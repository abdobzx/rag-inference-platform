"""Multi-agent RAG (Corrective RAG / Self-RAG pattern) built on LangGraph.

Classic RAG has no way to notice when it went wrong: if retrieval returns
weak or irrelevant context, or the model's answer isn't actually grounded in
that context, a plain retrieve-then-generate pipeline ships the bad answer
anyway. This graph adds agents whose job is specifically to catch that:

  retrieve -> grade_documents -> [insufficient? -> transform_query -> retrieve again]
                               -> generate -> grade_generation (supervisor)
                                            -> [hallucinated? -> retry generate]
                                            -> [off-topic? -> transform_query, retry]
                                            -> [grounded + on-topic -> done]

grade_generation is the supervisor step: it checks the answer against the
retrieved facts (hallucination check) and against the original question
(relevance check), and routes accordingly instead of trusting the first
generation. Retries are capped (MAX_RETRIES) so a genuinely unanswerable
question terminates with an honest "insufficient information" result rather
than looping or eventually fabricating one.

Reuses the existing FAISS-backed Retriever/KnowledgeBase for retrieval -
this file only adds the agent layer on top of it.
"""

import logging
import os
from typing import List, Literal, TypedDict

from langchain_anthropic import ChatAnthropic
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field

from .retriever import Retriever

logger = logging.getLogger(__name__)

MAX_RETRIES = 2
MODEL_ID = os.getenv("ANTHROPIC_MODEL_ID", "claude-haiku-4-5-20251001")


# ---------------------------------------------------------------------------
# Structured grading schemas - each grader is a distinct agent with one job.
# ---------------------------------------------------------------------------

class DocumentGrade(BaseModel):
    binary_score: Literal["yes", "no"] = Field(
        description="Is this document relevant to answering the question? 'yes' or 'no'."
    )


class HallucinationGrade(BaseModel):
    binary_score: Literal["yes", "no"] = Field(
        description="Is the generated answer fully grounded in / supported by the provided facts? 'yes' or 'no'."
    )
    reasoning: str = Field(description="One sentence explaining the grading decision.")


class AnswerRelevanceGrade(BaseModel):
    binary_score: Literal["yes", "no"] = Field(
        description="Does the generated answer actually address the user's question? 'yes' or 'no'."
    )


class GraphState(TypedDict):
    question: str
    original_question: str
    generation: str
    documents: List[str]
    retries: int
    anomalies: List[str]  # supervisor's log of what it caught along the way


def _model(temperature: float = 0.0) -> ChatAnthropic:
    return ChatAnthropic(model=MODEL_ID, temperature=temperature)


# ---------------------------------------------------------------------------
# Nodes
# ---------------------------------------------------------------------------

def make_retrieve_node(retriever: Retriever, top_k: int = 4):
    def retrieve(state: GraphState) -> GraphState:
        results = retriever.search(state["question"], top_k=top_k)
        documents = [text for _distance, text in results]
        logger.info(f"[retrieve] query={state['question']!r} -> {len(documents)} chunks")
        return {**state, "documents": documents}

    return retrieve


def grade_documents(state: GraphState) -> GraphState:
    """Relevance-grading agent: filters out retrieved chunks that don't
    actually relate to the question, instead of trusting the raw FAISS
    nearest-neighbor result. This is what lets the graph *notice* a bad
    retrieval instead of generating from garbage context.
    """
    grader = _model().with_structured_output(DocumentGrade)
    relevant_docs: List[str] = []

    for doc in state["documents"]:
        prompt = (
            f"Question: {state['question']}\n\n"
            f"Retrieved fact: {doc}\n\n"
            "Is this fact relevant to answering the question? Answer strictly yes or no."
        )
        grade = grader.invoke(prompt)
        if grade.binary_score == "yes":
            relevant_docs.append(doc)

    logger.info(f"[grade_documents] {len(relevant_docs)}/{len(state['documents'])} chunks kept as relevant")
    anomalies = list(state["anomalies"])
    if not relevant_docs:
        anomalies.append(
            f"retry {state['retries']}: retrieval for {state['question']!r} returned no relevant context"
        )
    return {**state, "documents": relevant_docs, "anomalies": anomalies}


def transform_query(state: GraphState) -> GraphState:
    """Query-rewriting agent: only invoked when grading found the retrieved
    context insufficient. Reformulates the question to retrieve better on
    the next pass, rather than giving up or generating from nothing.
    """
    model = _model(temperature=0.3)
    prompt = (
        f"Original question: {state['original_question']}\n"
        f"Current phrasing that returned poor results: {state['question']}\n\n"
        "Rewrite this as a single, more specific search query likely to retrieve "
        "relevant facts from a pharmaceutical ingredient-handling knowledge base. "
        "Return only the rewritten query, nothing else."
    )
    new_question = model.invoke(prompt).content.strip()
    logger.info(f"[transform_query] {state['question']!r} -> {new_question!r}")
    return {**state, "question": new_question, "retries": state["retries"] + 1}


def generate(state: GraphState) -> GraphState:
    """Generator agent: answers using only the (already relevance-filtered)
    retrieved facts, explicitly instructed not to use outside knowledge -
    the hallucination grader downstream depends on this instruction holding.
    """
    model = _model()
    context = "\n".join(f"- {doc}" for doc in state["documents"]) or "(no relevant facts retrieved)"
    prompt = (
        f"Context (verified facts from the ingredient-handling knowledge base):\n{context}\n\n"
        f"Question: {state['original_question']}\n\n"
        "Answer using ONLY the facts above. If the facts don't contain enough information "
        "to answer confidently, say so explicitly rather than guessing."
    )
    answer = model.invoke(prompt).content.strip()
    logger.info(f"[generate] produced {len(answer)}-char answer from {len(state['documents'])} facts")
    return {**state, "generation": answer}


def insufficient_context(state: GraphState) -> GraphState:
    """Terminal node reached when retries are exhausted and no relevant
    context was ever found - an honest 'I don't know' instead of a forced
    generation from nothing.
    """
    anomalies = state["anomalies"] + [
        f"gave up after {state['retries']} retries: no relevant context found for "
        f"{state['original_question']!r}"
    ]
    answer = (
        "I don't have enough verified information in the knowledge base to answer this "
        "question confidently. This has been flagged for human review rather than guessed."
    )
    return {**state, "generation": answer, "anomalies": anomalies}


# ---------------------------------------------------------------------------
# Routing (the supervisor logic lives here, in the edges, not a plain node -
# it decides where the graph goes next based on what the graders found)
# ---------------------------------------------------------------------------

def decide_to_generate(state: GraphState) -> Literal["generate", "transform_query", "insufficient_context"]:
    if state["documents"]:
        return "generate"
    if state["retries"] < MAX_RETRIES:
        return "transform_query"
    return "insufficient_context"


def grade_generation_vs_documents_and_question(
    state: GraphState,
) -> Literal["useful", "not_grounded", "not_relevant", "give_up"]:
    """The supervisor step. Two independent checks against the generation:
    is it actually supported by the retrieved facts (not hallucinated), and
    does it actually answer the question that was asked. Either failing
    triggers a correction path instead of returning the answer as-is.
    """
    hallucination_grader = _model().with_structured_output(HallucinationGrade)
    context = "\n".join(f"- {doc}" for doc in state["documents"]) or "(no facts)"
    h_grade = hallucination_grader.invoke(
        f"Facts:\n{context}\n\nGenerated answer: {state['generation']}\n\n"
        "Is the generated answer fully grounded in and supported by these facts? "
        "Score 'no' if it states anything the facts don't support."
    )

    if h_grade.binary_score == "no":
        logger.warning(f"[supervisor] HALLUCINATION detected: {h_grade.reasoning}")
        state["anomalies"].append(f"retry {state['retries']}: hallucination detected - {h_grade.reasoning}")
        return "not_grounded" if state["retries"] < MAX_RETRIES else "give_up"

    answer_grader = _model().with_structured_output(AnswerRelevanceGrade)
    a_grade = answer_grader.invoke(
        f"Question: {state['original_question']}\n\nAnswer: {state['generation']}\n\n"
        "Does this answer actually address the question asked?"
    )
    if a_grade.binary_score == "no":
        logger.warning("[supervisor] answer grounded but does not address the question - retrying")
        state["anomalies"].append(f"retry {state['retries']}: answer grounded but off-topic for the question")
        return "not_relevant" if state["retries"] < MAX_RETRIES else "give_up"

    logger.info("[supervisor] generation passed both grounding and relevance checks")
    return "useful"


# ---------------------------------------------------------------------------
# Graph assembly
# ---------------------------------------------------------------------------

def build_agentic_rag_graph(retriever: Retriever):
    graph = StateGraph(GraphState)

    graph.add_node("retrieve", make_retrieve_node(retriever))
    graph.add_node("grade_documents", grade_documents)
    graph.add_node("transform_query", transform_query)
    graph.add_node("generate", generate)
    graph.add_node("insufficient_context", insufficient_context)

    graph.set_entry_point("retrieve")
    graph.add_edge("retrieve", "grade_documents")
    graph.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "generate": "generate",
            "transform_query": "transform_query",
            "insufficient_context": "insufficient_context",
        },
    )
    graph.add_edge("transform_query", "retrieve")
    graph.add_conditional_edges(
        "generate",
        grade_generation_vs_documents_and_question,
        {
            "useful": END,
            "not_grounded": "generate",
            "not_relevant": "transform_query",
            "give_up": END,
        },
    )
    graph.add_edge("insufficient_context", END)

    return graph.compile()


def run_agentic_rag(question: str, retriever: Retriever) -> GraphState:
    """Convenience entry point: builds and runs the graph for one question."""
    app = build_agentic_rag_graph(retriever)
    initial_state: GraphState = {
        "question": question,
        "original_question": question,
        "generation": "",
        "documents": [],
        "retries": 0,
        "anomalies": [],
    }
    return app.invoke(initial_state)
