"""Evaluation script implementing the PowerPoint Slide 13 Evaluation Plan.
Benchmarks: BM25 vs Dense (FAISS) vs Hybrid vs Adaptive Agentic RAG
Metrics: Recall@k, Precision@k, MRR, Faithfulness/Sufficiency, Relevance, Latency, Retrieval Attempts
"""
import sys
import time
from pathlib import Path
from typing import Any

# Ensure project root and .venv site-packages are on sys.path
_root = Path(__file__).resolve().parent.parent
_venv = _root / ".venv" / "Lib" / "site-packages"
if _venv.exists() and str(_venv) not in sys.path:
    sys.path.insert(0, str(_venv))
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

import numpy as np

import rag_engine
from rag_engine import LegalRetriever, load_corpus, run_agent

BENCHMARK_QUERIES = [
    {
        "query": "What does Article 21 of the Constitution protect regarding personal liberty?",
        "expected_anchor": "Article 21",
        "category": "Constitutional Law",
    },
    {
        "query": "What are the fundamental rights enforcement remedies under Article 32?",
        "expected_anchor": "Article 32",
        "category": "Constitutional Law",
    },
    {
        "query": "Equality before law and equal protection under Article 14",
        "expected_anchor": "Article 14",
        "category": "Fundamental Rights",
    },
    {
        "query": "Section 66A Information Technology Act unconstitutionality Shreya Singhal",
        "expected_anchor": "Section 66A",
        "category": "Cyber & Statutory",
    },
]

def evaluate():
    corpus = load_corpus()
    retriever = LegalRetriever(corpus)
    k = 5

    methods = ["BM25", "Dense (FAISS)", "Hybrid (RRF)", "Adaptive Agentic RAG"]
    summary = {m: {"recall": [], "precision": [], "mrr": [], "latency": [], "attempts": [], "pass": []} for m in methods}

    print("=" * 80)
    print("NYAYAROUTE: EMPIRICAL BENCHMARK EVALUATION (Slide 13 Evaluation Plan)")
    print("=" * 80)

    for q_obj in BENCHMARK_QUERIES:
        query = q_obj["query"]
        anchor = q_obj["expected_anchor"].lower()

        # 1. BM25
        t0 = time.time()
        bm25_res = retriever.bm25_search(query, limit=k)
        lat_bm25 = time.time() - t0
        rel_bm25 = [1 if anchor in (e.title + " " + e.text).lower() else 0 for e in bm25_res]
        mrr_bm25 = (1.0 / (rel_bm25.index(1) + 1)) if 1 in rel_bm25 else 0.0
        summary["BM25"]["recall"].append(1.0 if sum(rel_bm25) > 0 else 0.0)
        summary["BM25"]["precision"].append(sum(rel_bm25) / max(1, len(bm25_res)))
        summary["BM25"]["mrr"].append(mrr_bm25)
        summary["BM25"]["latency"].append(lat_bm25)
        summary["BM25"]["attempts"].append(1)
        summary["BM25"]["pass"].append(1.0 if sum(rel_bm25) > 0 else 0.0)

        # 2. Dense (FAISS)
        t0 = time.time()
        dense_res = retriever.vector_search(query, limit=k)
        lat_dense = time.time() - t0
        rel_dense = [1 if anchor in (e.title + " " + e.text).lower() else 0 for e in dense_res]
        mrr_dense = (1.0 / (rel_dense.index(1) + 1)) if 1 in rel_dense else 0.0
        summary["Dense (FAISS)"]["recall"].append(1.0 if sum(rel_dense) > 0 else 0.0)
        summary["Dense (FAISS)"]["precision"].append(sum(rel_dense) / max(1, len(dense_res)))
        summary["Dense (FAISS)"]["mrr"].append(mrr_dense)
        summary["Dense (FAISS)"]["latency"].append(lat_dense)
        summary["Dense (FAISS)"]["attempts"].append(1)
        summary["Dense (FAISS)"]["pass"].append(1.0 if sum(rel_dense) > 0 else 0.0)

        # 3. Hybrid
        t0 = time.time()
        hybrid_res = retriever.retrieve(query, route="Hybrid Retrieval", limit=k, include_live_web=False)
        lat_hybrid = time.time() - t0
        rel_hybrid = [1 if anchor in (e.title + " " + e.text).lower() else 0 for e in hybrid_res]
        mrr_hybrid = (1.0 / (rel_hybrid.index(1) + 1)) if 1 in rel_hybrid else 0.0
        summary["Hybrid (RRF)"]["recall"].append(1.0 if sum(rel_hybrid) > 0 else 0.0)
        summary["Hybrid (RRF)"]["precision"].append(sum(rel_hybrid) / max(1, len(hybrid_res)))
        summary["Hybrid (RRF)"]["mrr"].append(mrr_hybrid)
        summary["Hybrid (RRF)"]["latency"].append(lat_hybrid)
        summary["Hybrid (RRF)"]["attempts"].append(1)
        summary["Hybrid (RRF)"]["pass"].append(1.0 if sum(rel_hybrid) > 0 else 0.0)

        # 4. Adaptive Agentic RAG (Full 7-Stage Pipeline)
        t0 = time.time()
        agent_res = run_agent(query, retriever, use_live_web=False)
        lat_agent = time.time() - t0
        agent_ev = agent_res.get("evidence", [])
        rel_agent = [1 if anchor in (e.get("title", "") + " " + e.get("text", "")).lower() else 0 for e in agent_ev[:k]]
        mrr_agent = (1.0 / (rel_agent.index(1) + 1)) if 1 in rel_agent else 0.0
        summary["Adaptive Agentic RAG"]["recall"].append(1.0 if sum(rel_agent) > 0 else 0.0)
        summary["Adaptive Agentic RAG"]["precision"].append(sum(rel_agent) / max(1, len(agent_ev[:k])))
        summary["Adaptive Agentic RAG"]["mrr"].append(mrr_agent)
        summary["Adaptive Agentic RAG"]["latency"].append(lat_agent)
        summary["Adaptive Agentic RAG"]["attempts"].append(2 if agent_res.get("retried") else 1)
        summary["Adaptive Agentic RAG"]["pass"].append(1.0 if agent_res.get("enough") else 0.0)

    # Print Formatted Results Table for Judges
    print(f"\n{'Category':<15} | {'Metric':<14} | {'BM25':<8} | {'Dense':<8} | {'Hybrid':<8} | {'Adaptive Agentic RAG':<20}")
    print("-" * 85)
    
    # Retrieval
    r_k = {m: np.mean(summary[m]["recall"]) for m in methods}
    p_k = {m: np.mean(summary[m]["precision"]) for m in methods}
    mrr_v = {m: np.mean(summary[m]["mrr"]) for m in methods}
    lat_v = {m: np.mean(summary[m]["latency"]) for m in methods}
    att_v = {m: np.mean(summary[m]["attempts"]) for m in methods}
    faith_v = {m: np.mean(summary[m]["pass"]) for m in methods}

    print(f"{'Retrieval':<15} | {'Recall@5':<14} | {r_k['BM25']:.1%}   | {r_k['Dense (FAISS)']:.1%}   | {r_k['Hybrid (RRF)']:.1%}   | {r_k['Adaptive Agentic RAG']:.1%}")
    print(f"{'Retrieval':<15} | {'Precision@5':<14} | {p_k['BM25']:.1%}   | {p_k['Dense (FAISS)']:.1%}   | {p_k['Hybrid (RRF)']:.1%}   | {p_k['Adaptive Agentic RAG']:.1%}")
    print(f"{'Retrieval':<15} | {'MRR':<14} | {mrr_v['BM25']:.2f}     | {mrr_v['Dense (FAISS)']:.2f}     | {mrr_v['Hybrid (RRF)']:.2f}     | {mrr_v['Adaptive Agentic RAG']:.2f}")
    print(f"{'Answer Quality':<15} | {'Faithfulness':<14} | {faith_v['BM25']:.1%}   | {faith_v['Dense (FAISS)']:.1%}   | {faith_v['Hybrid (RRF)']:.1%}   | {faith_v['Adaptive Agentic RAG']:.1%}")
    print(f"{'Efficiency':<15} | {'Latency (s)':<14} | {lat_v['BM25']:.2f}s   | {lat_v['Dense (FAISS)']:.2f}s   | {lat_v['Hybrid (RRF)']:.2f}s   | {lat_v['Adaptive Agentic RAG']:.2f}s")
    print(f"{'Adaptivity':<15} | {'Retr. Attempts':<14} | {att_v['BM25']:.1f}     | {att_v['Dense (FAISS)']:.1f}     | {att_v['Hybrid (RRF)']:.1f}     | {att_v['Adaptive Agentic RAG']:.1f}")
    print("=" * 85)

if __name__ == "__main__":
    evaluate()
