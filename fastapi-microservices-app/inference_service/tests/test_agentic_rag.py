"""Tests for the multi-agent RAG graph (src/rag/agentic_rag.py). All model
calls are mocked - no ANTHROPIC_API_KEY or real FAISS/torch stack needed -
so these verify the graph's routing logic (does it correctly retry on a
hallucination, does it give up gracefully when nothing relevant is found)
rather than actual LLM output quality, which was verified separately with
a real, live run against the real API (see the multi-agent RAG section in
the README for that transcript).
"""
import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key-not-used-model-is-mocked")

from src.rag import agentic_rag as rag  # noqa: E402


class FakeRetriever:
    """Stands in for the real FAISS-backed Retriever."""

    def __init__(self, results):
        self._results = results  # list[(distance, text)]

    def search(self, query, top_k=4):
        return self._results


def _fake_model_returning(*responses):
    """Builds a fake `_model()` replacement whose .invoke()/.with_structured_output().invoke()
    return the given responses in order, one per call, regardless of prompt content.
    """
    call_iter = iter(responses)

    class FakeInvokable:
        def invoke(self, _prompt):
            return next(call_iter)

    class FakeChatModel:
        def with_structured_output(self, _schema):
            return FakeInvokable()

        def invoke(self, _prompt):
            return next(call_iter)

    return lambda temperature=0.0: FakeChatModel()


class Content:
    """Mimics a plain-text ChatAnthropic response (has .content)."""

    def __init__(self, text):
        self.content = text


def test_grade_documents_keeps_only_relevant_chunks():
    state: rag.GraphState = {
        "question": "q", "original_question": "q", "generation": "",
        "documents": ["doc A", "doc B"], "retries": 0, "anomalies": [],
    }
    grades = [rag.DocumentGrade(binary_score="yes"), rag.DocumentGrade(binary_score="no")]
    with patch.object(rag, "_model", _fake_model_returning(*grades)):
        result = rag.grade_documents(state)
    assert result["documents"] == ["doc A"]


def test_grade_documents_logs_anomaly_when_nothing_relevant():
    state: rag.GraphState = {
        "question": "q", "original_question": "q", "generation": "",
        "documents": ["doc A"], "retries": 0, "anomalies": [],
    }
    with patch.object(rag, "_model", _fake_model_returning(rag.DocumentGrade(binary_score="no"))):
        result = rag.grade_documents(state)
    assert result["documents"] == []
    assert any("no relevant context" in a for a in result["anomalies"])


def test_decide_to_generate_routes_to_generate_when_docs_present():
    state: rag.GraphState = {
        "question": "q", "original_question": "q", "generation": "",
        "documents": ["some fact"], "retries": 0, "anomalies": [],
    }
    assert rag.decide_to_generate(state) == "generate"


def test_decide_to_generate_routes_to_rewrite_when_empty_and_retries_left():
    state: rag.GraphState = {
        "question": "q", "original_question": "q", "generation": "",
        "documents": [], "retries": 0, "anomalies": [],
    }
    assert rag.decide_to_generate(state) == "transform_query"


def test_decide_to_generate_gives_up_after_max_retries():
    state: rag.GraphState = {
        "question": "q", "original_question": "q", "generation": "",
        "documents": [], "retries": rag.MAX_RETRIES, "anomalies": [],
    }
    assert rag.decide_to_generate(state) == "insufficient_context"


def test_supervisor_flags_hallucination_and_retries_when_budget_remains():
    state: rag.GraphState = {
        "question": "q", "original_question": "q", "generation": "made up answer",
        "documents": ["fact"], "retries": 0, "anomalies": [],
    }
    with patch.object(
        rag, "_model",
        _fake_model_returning(rag.HallucinationGrade(binary_score="no", reasoning="not supported by facts")),
    ):
        route = rag.grade_generation_vs_documents_and_question(state)
    assert route == "not_grounded"
    assert any("hallucination detected" in a for a in state["anomalies"])


def test_supervisor_gives_up_on_hallucination_after_max_retries():
    state: rag.GraphState = {
        "question": "q", "original_question": "q", "generation": "made up answer",
        "documents": ["fact"], "retries": rag.MAX_RETRIES, "anomalies": [],
    }
    with patch.object(
        rag, "_model",
        _fake_model_returning(rag.HallucinationGrade(binary_score="no", reasoning="not supported")),
    ):
        route = rag.grade_generation_vs_documents_and_question(state)
    assert route == "give_up"


def test_supervisor_flags_off_topic_answer_even_if_grounded():
    state: rag.GraphState = {
        "question": "q", "original_question": "what temperature for storage?",
        "generation": "grounded but unrelated answer",
        "documents": ["fact"], "retries": 0, "anomalies": [],
    }
    with patch.object(
        rag, "_model",
        _fake_model_returning(
            rag.HallucinationGrade(binary_score="yes", reasoning="fully supported"),
            rag.AnswerRelevanceGrade(binary_score="no"),
        ),
    ):
        route = rag.grade_generation_vs_documents_and_question(state)
    assert route == "not_relevant"


def test_supervisor_passes_grounded_on_topic_answer():
    state: rag.GraphState = {
        "question": "q", "original_question": "what temperature for storage?",
        "generation": "a correct, grounded answer",
        "documents": ["fact"], "retries": 0, "anomalies": [],
    }
    with patch.object(
        rag, "_model",
        _fake_model_returning(
            rag.HallucinationGrade(binary_score="yes", reasoning="fully supported"),
            rag.AnswerRelevanceGrade(binary_score="yes"),
        ),
    ):
        route = rag.grade_generation_vs_documents_and_question(state)
    assert route == "useful"


def test_end_to_end_graph_gives_up_gracefully_when_nothing_is_ever_relevant():
    """Full graph run, everything mocked: retrieval always returns docs, but
    the grader always rejects them as irrelevant - the graph should retry
    up to MAX_RETRIES rewriting the query, then land on insufficient_context
    with an honest 'I don't know' rather than looping forever or fabricating
    an answer. This is the exact behavior verified live against the real API
    for an out-of-scope medical dosage question (see README).
    """
    retriever = FakeRetriever([(0.5, "an unrelated fact")])

    # (MAX_RETRIES + 1) grading rounds, one "no" verdict each, since the doc
    # never becomes relevant no matter how the query gets rewritten.
    grades = [rag.DocumentGrade(binary_score="no") for _ in range(rag.MAX_RETRIES + 1)]
    rewrites = [Content(f"rewritten query {i}") for i in range(rag.MAX_RETRIES)]

    responses = []
    for i in range(rag.MAX_RETRIES + 1):
        responses.append(grades[i])
        if i < rag.MAX_RETRIES:
            responses.append(rewrites[i])

    with patch.object(rag, "_model", _fake_model_returning(*responses)):
        result = rag.run_agentic_rag("an unanswerable question", retriever)

    assert "don't have enough" in result["generation"].lower()
    assert result["retries"] == rag.MAX_RETRIES
    # retries go 0 -> 1 -> MAX_RETRIES before the cap stops it, so that's
    # (MAX_RETRIES + 1) failed-retrieval rounds, plus the final give-up message.
    assert len(result["anomalies"]) == rag.MAX_RETRIES + 2
