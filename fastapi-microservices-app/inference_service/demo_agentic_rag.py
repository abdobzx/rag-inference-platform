#!/usr/bin/env python3
"""Live demo of the multi-agent RAG (src/rag/agentic_rag.py).

Runs two questions through the graph:
  1. An in-scope question the knowledge base actually covers - shows the
     retrieve -> grade -> generate -> supervisor-approves flow.
  2. An out-of-scope medical dosage question the knowledge base has nothing
     about - shows the supervisor correctly detecting the anomaly (no
     relevant context, even after query rewrites) and refusing to fabricate
     an answer instead of hallucinating a fake drug dosage.

Usage:
    export ANTHROPIC_API_KEY="your_key_here"
    python demo_agentic_rag.py
"""
import logging
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
logging.basicConfig(level=logging.INFO, format="%(message)s")

from src.rag.knowledge_base import KnowledgeBase
from src.rag.retriever import Retriever
from src.rag.agentic_rag import run_agentic_rag


def run_and_print(title: str, question: str, retriever: Retriever):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)
    print(f"Question: {question}\n")
    result = run_agentic_rag(question, retriever)
    print(f"\nFinal answer:\n{result['generation']}\n")
    print(f"Retries used: {result['retries']}")
    if result["anomalies"]:
        print("Anomalies the supervisor caught along the way:")
        for a in result["anomalies"]:
            print(f"  - {a}")
    else:
        print("No anomalies - clean pass on the first attempt.")


def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY is not set.")
        print("  export ANTHROPIC_API_KEY='your_key_here'")
        sys.exit(1)

    kb = KnowledgeBase()
    retriever = Retriever(knowledge_base=kb)

    run_and_print(
        "DEMO 1: in-scope question (expect a clean, grounded answer)",
        "What temperature should active pharmaceutical ingredients be stored at?",
        retriever,
    )

    run_and_print(
        "DEMO 2: out-of-scope question (expect a graceful refusal, not a hallucinated answer)",
        "What is the recommended dosage of ibuprofen for a 10-year-old child?",
        retriever,
    )


if __name__ == "__main__":
    main()
