from __future__ import annotations

import os
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

from rag_engine import LegalRetriever, load_corpus, run_agent, source_summary
from trusted_sources import ingest_trusted_url

load_dotenv()
st.set_page_config(page_title="NyayaRoute | Legal Research Workspace", page_icon="⚖", layout="wide")

st.markdown("""
<style>
    .stApp { background: #f7f8fc; }
    .hero { padding: 1rem 0 .55rem; }
    .hero h1 { color: #132d5c; margin: 0; font-size: 2.15rem; }
    .sub { color: #526076; margin-top: .3rem; }
    .result-card { border: 1px solid #cad8ec; border-left: 6px solid #205cba; border-radius: 10px; background: #fff; padding: 1.1rem 1.25rem; margin: .65rem 0 1rem; }
    .warning-card { border-left-color: #c67a00; background: #fffbf1; }
    .route { border: 1px solid #dce2ef; border-radius: 10px; padding: .7rem; background: white; min-height: 82px; }
    .route strong { color: #1c3f77; }
    .tiny { color: #5d6880; font-size: .85rem; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Preparing legal retrieval workspace…")
def get_retriever() -> LegalRetriever:
    return LegalRetriever(load_corpus())


def reset_retriever() -> None:
    get_retriever.clear()


def render_source_links(actions: list[dict[str, str]]) -> None:
    for action in actions:
        st.markdown(f"- [{action['label']}]({action['url']}) — {action['why']}")


def memo(question: str, result: dict) -> str:
    sources = "\n".join(f"- [S{i}] {item['title']} — {item['url']}" for i, item in enumerate(result["evidence"], 1)) or "- No adequate source material was retrieved."
    outcome = result["answer"] or f"Insufficient evidence: {result['evidence_reason']}"
    return f"""# NyayaRoute Legal Research Memo

**Question:** {question}

**Research outcome**

{outcome}

## Sources consulted
{sources}

## Research audit
- Query quality: {result['quality_reason']}
- Search query: {result['query_used']}
- Retrieval route: {result['route']} — {result['route_reason']}
- Evidence decision: {result['evidence_reason']}
- Retry used: {'Yes' if result['retried'] else 'No'}

*This is legal research information, not legal advice. Verify the current primary text and seek qualified legal counsel for advice.*
"""


st.markdown("<div class='hero'><h1>NyayaRoute</h1><p class='sub'>An evidence-first workspace for Indian legal research — answers when the sources support it, and guides the next research step when they do not.</p></div>", unsafe_allow_html=True)

workspace_tab, library_tab, about_tab = st.tabs(["Research workspace", "Source library", "How to use this"])

with workspace_tab:
    corpus = load_corpus()
    source_options = sorted({item["source"] for item in corpus})
    with st.sidebar:
        st.header("Research settings")
        selected_sources = st.multiselect("Search these sources", source_options, default=source_options)
        st.caption("Use the source filter to focus statutory research or case-law research.")
        st.divider()
        st.metric("Local legal chunks", len(corpus))
        st.caption(f"{len(source_summary(corpus))} source page(s) indexed")
        if os.getenv("GROQ_API_KEY"):
            st.success(f"Groq ready · {os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')}")
        else:
            st.warning("Add GROQ_API_KEY to .env to generate grounded answers.")
        st.info("Not legal advice. Verify citations in their original source.")

    st.subheader("Start a research question")
    question = st.text_area("Question", placeholder="Example: What does Article 21 of the Constitution protect?", height=100, label_visibility="collapsed", key="research_input")
    samples = st.columns(3)
    sample_values = [
        "What does Article 21 of the Constitution protect?",
        "What is the latest amendment to the IT Act?",
        "Which Supreme Court cases discuss personal liberty?",
    ]
    for col, label, value in zip(samples, ["Try Article 21", "Try an amendment", "Try case law"], sample_values):
        if col.button(label, use_container_width=True):
            st.session_state["research_input"] = value
            st.rerun()

    investigate = st.button("Research this question", type="primary")
    if investigate:
        if not question.strip():
            st.warning("Enter a legal research question first.")
        elif not selected_sources:
            st.warning("Select at least one source to search.")
        else:
            with st.status("Checking query quality, routing retrieval, and evaluating evidence…", expanded=False) as status:
                result = run_agent(question.strip(), get_retriever(), set(selected_sources))
                status.update(label="Research decision complete", state="complete")
            st.session_state["research_result"] = result
            st.session_state["research_question"] = question.strip()

    result = st.session_state.get("research_result")
    research_question = st.session_state.get("research_question")
    if result and research_question:
        st.divider()
        if result["enough"] and result["answer"]:
            st.markdown("<div class='result-card'><b>RESEARCH ANSWER</b><br><span class='tiny'>Evidence gate passed — the answer below is constrained to the cited local sources.</span></div>", unsafe_allow_html=True)
            st.markdown(result["answer"])
        elif result["enough"]:
            st.markdown("<div class='result-card'><b>EVIDENCE FOUND</b><br><span class='tiny'>The evidence gate passed. Configure GROQ_API_KEY in .env to turn this evidence into a cited answer.</span></div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='result-card warning-card'><b>NO ANSWER YET — INSUFFICIENT EVIDENCE</b><br><span class='tiny'>The system did not find reliable material in the selected local library, so it will not guess.</span></div>", unsafe_allow_html=True)
            st.write(result["evidence_reason"])
            st.markdown("**Useful next steps**")
            render_source_links(result["actions"])
            st.caption("Open a relevant primary document, then add its specific URL in the Source library. Re-run this question after ingestion.")

        st.download_button("Download research memo (.md)", memo(research_question, result), file_name=f"nyayaroute-research-{datetime.now():%Y%m%d-%H%M}.md", mime="text/markdown")

        st.subheader("Authorities and citations")
        if not result["evidence"]:
            st.caption("No relevant chunks were retrieved from the selected local source library.")
        for index, item in enumerate(result["evidence"], 1):
            relevance = f"{item['relevance']:.0%} query-anchor match"
            with st.expander(f"[S{index}] {item['title']} · {item['source']} · {relevance}"):
                st.markdown(f"**Primary link:** [{item['url']}]({item['url']})")
                st.caption("Verify the full source text, date, court/bench, and later treatment before relying on it.")
                st.write(item["text"])

        with st.expander("Explain how this research outcome was reached"):
            cols = st.columns(4)
            quality = "Ready" if result["good_query"] else "Clarified"
            values = [("Query quality", quality, result["quality_reason"]), ("Retrieval route", result["route"], result["route_reason"]), ("Retry", "Used" if result["retried"] else "Not needed", f"{len(result['evidence'])} cited chunks retained"), ("Evidence gate", "Passed" if result["enough"] else "Not passed", result["evidence_reason"])]
            for col, (title, value, detail) in zip(cols, values):
                col.markdown(f"<div class='route'><small>{title}</small><br><strong>{value}</strong><br><small>{detail}</small></div>", unsafe_allow_html=True)
            st.caption(f"Research query used: {result['query_used']}")

with library_tab:
    st.subheader("Source library")
    st.write("The workspace only answers from this local collection. Add specific legal document pages, not broad landing pages or bulk crawls.")
    current_sources = source_summary(load_corpus())
    if current_sources:
        for item in current_sources:
            st.markdown(f"**{item['title']}**  ")
            st.markdown(f"{item['source']} · {item['chunks']} chunk(s) · [Open source]({item['url']})")
    else:
        st.info("No sources are indexed yet.")
    st.divider()
    st.subheader("Add a trusted source")
    st.caption("Allowed: India Code, Supreme Court of India, Indian Kanoon, and official High Court sites. The tool is deliberately page-by-page and does not bulk crawl.")
    with st.form("ingest_source", clear_on_submit=True):
        source_url = st.text_input("Specific document URL", placeholder="https://www.indiacode.nic.in/…")
        display_title = st.text_input("Optional label", placeholder="e.g., Information Technology Act, 2000")
        submit_source = st.form_submit_button("Add to source library")
    if submit_source:
        if not source_url.strip():
            st.warning("Enter a source URL.")
        else:
            try:
                with st.spinner("Fetching and indexing the trusted source page…"):
                    count, title = ingest_trusted_url(source_url.strip(), display_title.strip() or None)
                reset_retriever()
                if count:
                    st.success(f"Added {count} chunks from: {title}. Return to Research workspace and ask your question again.")
                else:
                    st.info("That page is already indexed; no new chunks were added.")
            except Exception as exc:
                st.error(f"Could not add this source: {exc}")

with about_tab:
    st.subheader("A safer way to use legal RAG")
    st.markdown("""
    1. Ask a focused legal research question.
    2. NyayaRoute checks whether the query needs clarification and selects BM25, vector, or hybrid retrieval.
    3. It reranks candidate chunks and tests whether a sufficiently relevant authority was retrieved.
    4. It either produces a cited, evidence-constrained research answer or says what is missing and directs you to trusted sources.

    For current amendments, always add the current statutory text or notification first. A language model being available does not make it a source of law.
    """)
