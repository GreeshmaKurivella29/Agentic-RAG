# NyayaRoute — Agentic Legal Research Workspace

A legal-domain RAG demonstrator for Indian law. Unlike a fixed retrieve-then-answer system, NyayaRoute evaluates query quality, routes retrieval, reranks evidence, retries weak searches, and can decline to answer when the evidence is thin.

## Workspace features

- **Answer-first outcome:** cited research answer when evidence passes; a clear, useful no-answer outcome when it does not.
- **Source library:** view every indexed page and add a specific trusted legal-document URL from the UI.
- **Guided next steps:** an evidence failure includes direct India Code, Supreme Court, and Indian Kanoon discovery links.
- **Research controls:** limit retrieval to selected sources.
- **Authority cards:** open the primary source, inspect each retrieved excerpt, and see its query-anchor match.
- **Audit trail:** query quality, retrieval route, retry decision, and evidence decision are available under an expandable explanation.
- **Downloadable memo:** export the answer, sources, and research audit as Markdown.

> **Not legal advice.** The system provides research assistance only. Always verify citations against the original legal text and consult a qualified advocate for advice.

## What it does

```text
Question → quality check → query rewrite (if needed) → BM25 / Vector / Hybrid
         → candidate chunks → cross-encoder rerank → evidence check
         → answer with citations  OR  retry → insufficient evidence
```

## Trusted-source policy

The ingestor accepts only the following sources by default:

- `indiacode.nic.in` — Government legislation
- `sci.gov.in` and `main.sci.gov.in` — Supreme Court of India
- `indiankanoon.org` — Indian case-law/legal search service
- Official High Court domains ending in `.hc.gov.in`, plus the common `highcourt*.gov.in` pattern

Use `--allow-domain` only after independently confirming that the domain is an official court/government source. Respect each site’s terms, robots policy, rate limits, and copyright conditions. Ingestion is deliberately URL-by-URL; it does not bulk crawl legal repositories.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# add GROQ_API_KEY to .env
streamlit run app.py
```

The app works in **demo corpus** mode without a Groq key (retrieval trace only). With a key, it produces evidence-constrained answers.

## Add vetted legal material

```powershell
python ingest.py "https://www.indiacode.nic.in/handle/123456789/1362"
python ingest.py "https://www.sci.gov.in/judgements/" --title "Supreme Court judgment index"
```

This stores chunks in `data/legal_corpus.jsonl`, which is intentionally git-ignored. Re-run the Streamlit app after ingesting material.

You can also use the **Source library** tab in the app. For a hands-on test with the Information Technology Act, use the official India Code document page:

```text
https://www.indiacode.nic.in/handle/123456789/15442?locale=en
```

Add it from the Source library, then re-run your question. The ingestor intentionally accepts one page at a time and rejects untrusted domains.

## Test scenarios

1. **Supported answer:** ask `What does Article 21 of the Constitution protect?` The bundled India Code sample should produce a Groq-cited answer with an Article 21 authority card.
2. **Safe no-answer:** ask `What is the latest amendment to the IT Act?` before adding IT Act material. You should see **No answer yet — insufficient evidence** plus research links, not a hallucinated answer.
3. **Ingestion flow:** add the IT Act URL above in Source library. Confirm the source appears in the list, return to the workspace, and ask `What is the short title and scope of the Information Technology Act, 2000?`.
4. **Source filter:** choose only `India Code` in the sidebar and ask the Article 21 question. The citations should be limited to India Code material.
5. **Research audit:** expand **Explain how this research outcome was reached** after any query and confirm that query quality, route, retry, and evidence decision are shown.

## Architecture choices

- **Quality gate:** flags vague or underspecified questions and uses Groq to form a concise legal-research query.
- **Router:** legislation-oriented questions use BM25; fact/semantic questions use vector search; citations/case-law questions use hybrid retrieval.
- **Reranker:** `cross-encoder/ms-marco-MiniLM-L-6-v2` scores the top candidate chunks.
- **Evidence gate:** requires multiple relevant chunks and a minimum reranker score before generation; the retry path expands the query and search depth.
- **Grounded answer:** the model is instructed to use only supplied context and cite each material proposition as `[S1]`, `[S2]`, etc.

## Project layout

- `app.py` — Streamlit research interface and routing visualisation
- `rag_engine.py` — agentic orchestration, retrieval, reranking, evidence gate, Groq answer generation
- `ingest.py` — guarded single-page ingestion tool
- `trusted_sources.py` — source allowlist and document extraction/chunking
- `data/demo_legal_corpus.jsonl` — small illustrative seed corpus; replace/augment with vetted primary material
 