"""Agentic, evidence-constrained retrieval for Indian legal research."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
import re
from typing import Any

import numpy as np
from rank_bm25 import BM25Okapi

LEGAL_TERMS = {"act", "article", "section", "constitution", "code", "ipc", "bns", "crpc", "bnss", "judgment", "case", "court", "writ", "bail", "appeal", "petition", "precedent", "ruling", "amendment", "rules"}
PRIMARY_SOURCES = {"India Code", "Supreme Court of India"}


@dataclass
class Evidence:
    id: str
    title: str
    url: str
    source: str
    text: str
    score: float = 0.0
    relevance: float = 0.0


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def load_corpus() -> list[dict[str, Any]]:
    """Read the bundled sample and locally ingested source records."""
    rows: list[dict[str, Any]] = []
    for path in (Path("data/demo_legal_corpus.jsonl"), Path("data/legal_corpus.jsonl")):
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    rows.append(json.loads(line))
    return rows


def source_summary(corpus: list[dict[str, Any]]) -> list[dict[str, str | int]]:
    grouped: dict[str, dict[str, Any]] = {}
    for item in corpus:
        key = item["url"]
        grouped.setdefault(key, {"title": item["title"], "url": key, "source": item["source"], "chunks": 0})
        grouped[key]["chunks"] += 1
    return sorted(grouped.values(), key=lambda item: (str(item["source"]), str(item["title"])))


class LegalRetriever:
    def __init__(self, corpus: list[dict[str, Any]]):
        self.corpus = corpus
        self.tokenized = [_tokens(f"{d['title']} {d['text']}") for d in corpus]
        self.bm25 = BM25Okapi(self.tokenized) if corpus else None
        self.embedder = None
        self.embeddings = None
        self.reranker = None

    def _embeddings(self) -> np.ndarray:
        if self.embeddings is None:
            from sentence_transformers import SentenceTransformer
            self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
            self.embeddings = self.embedder.encode([f"{d['title']}\n{d['text']}" for d in self.corpus], normalize_embeddings=True, show_progress_bar=False)
        return self.embeddings

    def _evidence(self, index: int, score: float, query: str) -> Evidence:
        doc = self.corpus[index]
        query_terms = set(_tokens(query)) - {"what", "does", "the", "and", "for", "with", "under", "about", "latest"}
        document_terms = set(_tokens(f"{doc['title']} {doc['text']}"))
        relevance = len(query_terms & document_terms) / max(1, len(query_terms))
        return Evidence(**{key: doc[key] for key in ("id", "title", "url", "source", "text")}, score=score, relevance=relevance)

    def bm25_search(self, query: str, limit: int) -> list[Evidence]:
        if not self.bm25:
            return []
        scores = self.bm25.get_scores(_tokens(query))
        top = np.argsort(scores)[::-1][:limit]
        return [self._evidence(int(i), float(scores[i]), query) for i in top if scores[i] > 0]

    def vector_search(self, query: str, limit: int) -> list[Evidence]:
        if not self.corpus:
            return []
        try:
            vectors = self._embeddings()
            query_vector = self.embedder.encode([query], normalize_embeddings=True, show_progress_bar=False)[0]
            scores = vectors @ query_vector
            top = np.argsort(scores)[::-1][:limit]
            return [self._evidence(int(i), float(scores[i]), query) for i in top if scores[i] > 0.10]
        except Exception:
            return []

    def retrieve(self, query: str, route: str, limit: int = 12) -> list[Evidence]:
        if route == "BM25":
            candidates = self.bm25_search(query, limit)
        elif route == "Vector DB":
            candidates = self.vector_search(query, limit)
        else:
            combined: dict[str, Evidence] = {}
            for rank, item in enumerate(self.bm25_search(query, limit), 1):
                item.score = 1 / (60 + rank)
                combined[item.id] = item
            for rank, item in enumerate(self.vector_search(query, limit), 1):
                if item.id in combined:
                    combined[item.id].score += 1 / (60 + rank)
                else:
                    item.score = 1 / (60 + rank)
                    combined[item.id] = item
            candidates = sorted(combined.values(), key=lambda x: x.score, reverse=True)
        return self.rerank(query, candidates[:limit])

    def rerank(self, query: str, candidates: list[Evidence]) -> list[Evidence]:
        if not candidates:
            return []
        try:
            if self.reranker is None:
                from sentence_transformers import CrossEncoder
                self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
            scores = self.reranker.predict([(query, item.text) for item in candidates])
            for item, score in zip(candidates, scores):
                item.score = float(score)
            return sorted(candidates, key=lambda x: (x.relevance, x.score), reverse=True)
        except Exception:
            return sorted(candidates, key=lambda x: x.relevance, reverse=True)


def quality_check(question: str) -> tuple[bool, str]:
    tokens = _tokens(question)
    has_legal_signal = bool(set(tokens) & LEGAL_TERMS) or bool(re.search(r"\b\d+[A-Za-z]?\b", question))
    if len(tokens) < 5:
        return False, "Too short to identify the legal issue, jurisdiction, or authority requested."
    if not has_legal_signal:
        return False, "The question lacks clear legal anchors; the research query will be clarified before retrieval."
    return True, "Question contains enough legal anchors for first-pass retrieval."


def choose_route(query: str) -> tuple[str, str]:
    terms = set(_tokens(query))
    if terms & {"section", "article", "act", "code", "statute", "bare", "amendment", "notification"}:
        return "BM25", "Exact statutory terms, section references, and amendments favour lexical retrieval."
    if terms & {"judgment", "case", "precedent", "held", "ruling", "appeal"}:
        return "Hybrid", "Case-law research benefits from citation keywords and semantic similarity."
    return "Vector DB", "A conceptual fact pattern favours semantic retrieval."


def groq_chat(messages: list[dict[str, str]], temperature: float = 0.1) -> str:
    from groq import Groq
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not configured")
    response = Groq(api_key=key).chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"), messages=messages, temperature=temperature, max_tokens=1100
    )
    return response.choices[0].message.content or ""


def rewrite_query(question: str) -> str:
    prompt = "Rewrite this into a concise Indian legal-research query. Preserve facts. Do not invent a statute, judgment, or outcome. Return only the query.\n\nQuestion: " + question
    try:
        return groq_chat([{"role": "system", "content": "You are a precise legal-research query editor."}, {"role": "user", "content": prompt}])
    except Exception:
        return f"Indian law legal research: {question}"


def evidence_is_enough(items: list[Evidence]) -> tuple[bool, str]:
    if not items:
        return False, "No relevant chunks were found in the selected local source library."
    best = items[0]
    if best.relevance < 0.28:
        return False, "The closest retrieved material does not match enough of the legal issue to support an answer."
    if best.source in PRIMARY_SOURCES:
        return True, f"A primary-source chunk matched {best.relevance:.0%} of the legal anchors in the question."
    corroborating = [item for item in items[1:] if item.relevance >= 0.28]
    if corroborating:
        return True, "Multiple relevant legal-source chunks passed the evidence gate."
    return False, "Only a non-primary source matched; add the underlying statute or judgment before relying on an answer."


def generate_answer(question: str, evidence: list[Evidence]) -> str:
    supported = [item for item in evidence if item.relevance >= 0.28][:5]
    context = "\n\n".join(f"[S{i}] {item.title}\nSource: {item.source}\nURL: {item.url}\n{item.text}" for i, item in enumerate(supported, 1))
    system = """You are NyayaRoute, an Indian legal research assistant. Use only supplied sources. Do not give legal advice, invent authorities, or state that a source proves more than it says. Use exactly these headings: **Short answer**, **Relevant authority**, **What this means**, **Limits / next verification**. Cite each material proposition as [S1], [S2], etc. End with: 'This is legal research information, not legal advice.' If the sources do not answer the question, say so plainly."""
    return groq_chat([{"role": "system", "content": system}, {"role": "user", "content": f"Question: {question}\n\nSources:\n{context}"}])


def research_actions(question: str) -> list[dict[str, str]]:
    encoded = question.replace(" ", "+")
    return [
        {"label": "Search India Code", "url": f"https://www.indiacode.nic.in/search/?query={encoded}", "why": "Find the current statutory text, amendments, and linked rules."},
        {"label": "Search Supreme Court judgments", "url": "https://www.sci.gov.in/judgements/", "why": "Locate relevant Supreme Court decisions and verify the primary judgment."},
        {"label": "Search Indian Kanoon", "url": f"https://indiankanoon.org/search/?formInput={encoded}", "why": "Use for case-law discovery, then verify against the primary source."},
    ]


def run_agent(question: str, retriever: LegalRetriever, allowed_sources: set[str] | None = None) -> dict[str, Any]:
    good, quality_reason = quality_check(question)
    query = question if good else rewrite_query(question)
    route, route_reason = choose_route(query)
    first = retriever.retrieve(query, route)
    if allowed_sources:
        first = [item for item in first if item.source in allowed_sources]
    enough, evidence_reason = evidence_is_enough(first)
    retried = False
    if not enough:
        retried = True
        retry_query = rewrite_query(f"{question}. Find directly relevant Indian primary legal authorities.")
        retry_results = retriever.retrieve(retry_query, "Hybrid", limit=20)
        if allowed_sources:
            retry_results = [item for item in retry_results if item.source in allowed_sources]
        retry_enough, retry_reason = evidence_is_enough(retry_results)
        if retry_enough or (retry_results and retry_results[0].relevance > (first[0].relevance if first else 0)):
            first, enough, evidence_reason, query, route = retry_results, retry_enough, retry_reason, retry_query, "Hybrid"
    answer = generate_answer(question, first) if enough and os.getenv("GROQ_API_KEY") else None
    return {"good_query": good, "quality_reason": quality_reason, "query_used": query, "route": route, "route_reason": route_reason, "evidence": [asdict(x) for x in first[:5]], "enough": enough, "evidence_reason": evidence_reason, "retried": retried, "answer": answer, "actions": research_actions(question)}
