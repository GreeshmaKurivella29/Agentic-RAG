from __future__ import annotations

import base64
import os
from datetime import datetime
from pathlib import Path

import importlib
import streamlit as st
from dotenv import load_dotenv

import rag_engine
import live_web_searcher
importlib.reload(rag_engine)
importlib.reload(live_web_searcher)

from rag_engine import LegalRetriever, load_corpus, run_agent, source_summary
from trusted_sources import ingest_trusted_url
from pdf_ingestor import DuplicatePDFError, ingest_pdf, preview_pdf
from pdf_parser import PDFIngestionError
load_dotenv()

st.set_page_config(
    page_title="NyayaRoute | Institutional Intelligence",
    page_icon="⚖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Function to load and base64 encode the user's uploaded legal image
def get_image_b64() -> str:
    paths = [
        Path(r"C:\Users\Vybha\.gemini\antigravity-ide\brain\26493043-ee59-4102-beff-3c715ce5832a\media__1784889718562.png"),
        Path("legal_hero.png"),
    ]
    for p in paths:
        if p.exists():
            try:
                with open(p, "rb") as f:
                    return base64.b64encode(f.read()).decode("utf-8")
            except Exception:
                pass
    return ""

img_b64 = get_image_b64()
img_src = f"data:image/png;base64,{img_b64}" if img_b64 else "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=1200&q=80"

# ── Pure CSS Design Integration & Image Animations (NO JS SCRIPTS) ────────────
st.markdown(f"""
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;0,800;1,400&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,300,0,0" rel="stylesheet">

<style>
  /* Base background and typography */
  html, body, .stApp {{
    background-color: #faf9f7 !important;
    color: #1a1c1b !important;
    font-family: 'Inter', sans-serif !important;
  }}

  /* Hide default Streamlit menu and decoration while preserving sidebar controls */
  #MainMenu {{ visibility: hidden; }}
  footer {{ visibility: hidden; }}
  [data-testid="stToolbar"] {{ display: none !important; }}
  [data-testid="stDecoration"] {{ display: none !important; }}

  /* Ensure header and all sidebar collapse/expand controls are 100% clickable and visible */
  header[data-testid="stHeader"] {{
    background: transparent !important;
    pointer-events: auto !important;
    z-index: 99999 !important;
  }}

  /* Make sure the sidebar collapse and expand toggle is always accessible, prominent, and clickable */
  [data-testid="collapsedControl"],
  [data-testid="stSidebarCollapsedControl"],
  [data-testid="stSidebarCollapseButton"],
  button[data-testid="stSidebarCollapseButton"],
  button[aria-label="Expand sidebar"],
  button[aria-label="Close sidebar"] {{
    visibility: visible !important;
    display: flex !important;
    pointer-events: auto !important;
    opacity: 1 !important;
  }}

  [data-testid="collapsedControl"],
  [data-testid="stSidebarCollapsedControl"] {{
    background-color: #0c1b33 !important;
    color: #ffffff !important;
    border: 2px solid #735a3a !important;
    border-radius: 6px !important;
    top: 0.6rem !important;
    left: 0.6rem !important;
    z-index: 9999999 !important;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.35) !important;
    padding: 4px 8px !important;
  }}
  [data-testid="collapsedControl"] button,
  [data-testid="stSidebarCollapsedControl"] button,
  [data-testid="stSidebarCollapseButton"] button {{
    color: #ffffff !important;
  }}
  [data-testid="collapsedControl"] svg,
  [data-testid="stSidebarCollapsedControl"] svg,
  [data-testid="stSidebarCollapseButton"] svg {{
    fill: #ffffff !important;
    stroke: #ffffff !important;
  }}

  .block-container {{
    padding-top: 1rem !important;
    padding-bottom: 2rem !important;
    max-width: 1240px !important;
  }}

  /* Fonts for headings */
  h1, h2, h3, h4, h5, h6,
  [data-testid="stMarkdownContainer"] h1,
  [data-testid="stMarkdownContainer"] h2,
  [data-testid="stMarkdownContainer"] h3 {{
    font-family: 'Playfair Display', serif !important;
    color: #1a1c1b !important;
    letter-spacing: -0.01em;
  }}

  /* Body text color enforcement */
  p, span, label, li, div, [data-testid="stMarkdownContainer"] p {{
    color: #1a1c1b;
    font-family: 'Inter', sans-serif;
  }}

  /* Sidebar styling */
  [data-testid="stSidebar"] {{
    background-color: #f4f3f1 !important;
    border-right: 1px solid #c5c6ce !important;
  }}
  [data-testid="stSidebar"] * {{
    color: #1a1c1b !important;
  }}

  /* Tabs styling */
  button[data-baseweb="tab"] p {{
    font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: #44474d !important;
  }}
  button[aria-selected="true"][data-baseweb="tab"] p {{
    color: #000000 !important;
  }}
  button[aria-selected="true"][data-baseweb="tab"] {{
    border-bottom: 2px solid #735a3a !important;
  }}

  /* Text area styling */
  .stTextArea textarea {{
    background-color: #ffffff !important;
    border: 1px solid #c5c6ce !important;
    border-radius: 4px !important;
    font-family: 'Playfair Display', serif !important;
    font-style: italic !important;
    font-size: 1.05rem !important;
    color: #1a1c1b !important;
    padding: 0.85rem !important;
  }}
  .stTextArea textarea:focus {{
    border-color: #735a3a !important;
    box-shadow: 0 0 0 1px #735a3a !important;
  }}

  /* Buttons styling */
  .stButton button {{
    background-color: #ffffff !important;
    color: #1a1c1b !important;
    border: 1px solid #c5c6ce !important;
    border-radius: 4px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
    padding: 0.6rem 1rem !important;
    transition: all 0.2s ease !important;
  }}
  .stButton button:hover {{
    background-color: #efeeec !important;
    border-color: #735a3a !important;
  }}
  .stButton button[kind="primary"] {{
    background-color: #000000 !important;
    color: #ffffff !important;
    border: none !important;
  }}
  .stButton button[kind="primary"] p {{
    color: #ffffff !important;
  }}

  /* Download Button */
  .stDownloadButton button {{
    background-color: transparent !important;
    color: #b9c7e6 !important;
    border: 1px solid #b9c7e6 !important;
    border-radius: 4px !important;
    width: 100% !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    font-weight: 600 !important;
    padding: 0.7rem !important;
  }}
  .stDownloadButton button p {{
    color: #b9c7e6 !important;
  }}

  /* Expanders */
  [data-testid="stExpander"] {{
    background-color: #ffffff !important;
    border: 1px solid #c5c6ce !important;
    border-radius: 4px !important;
    margin-bottom: 0.75rem !important;
  }}
  [data-testid="stExpander"] summary span p {{
    font-family: 'Playfair Display', serif !important;
    font-weight: 600 !important;
    color: #1a1c1b !important;
  }}

  /* Material Symbols styling */
  .material-symbols-outlined {{
    font-family: 'Material Symbols Outlined' !important;
    font-weight: normal;
    font-style: normal;
    display: inline-block;
    line-height: 1;
    text-transform: none;
    letter-spacing: normal;
    word-wrap: normal;
    white-space: nowrap;
    direction: ltr;
  }}

  /* ── IMAGE ANIMATIONS ── */
  @keyframes heroFloat {{
    0% {{
      transform: translateY(0px);
      box-shadow: 0 15px 35px rgba(12, 27, 51, 0.16), 0 0 0 1px rgba(115, 90, 58, 0.3);
    }}
    50% {{
      transform: translateY(-12px);
      box-shadow: 0 28px 50px rgba(115, 90, 58, 0.28), 0 0 0 1px rgba(115, 90, 58, 0.7);
    }}
    100% {{
      transform: translateY(0px);
      box-shadow: 0 15px 35px rgba(12, 27, 51, 0.16), 0 0 0 1px rgba(115, 90, 58, 0.3);
    }}
  }}

  @keyframes kenBurnsZoom {{
    0% {{ transform: scale(1.0); }}
    50% {{ transform: scale(1.07); }}
    100% {{ transform: scale(1.0); }}
  }}

  @keyframes shimmerGlow {{
    0% {{ opacity: 0.4; }}
    50% {{ opacity: 0.95; }}
    100% {{ opacity: 0.4; }}
  }}

  .animated-hero-card {{
    animation: heroFloat 7s ease-in-out infinite;
    border-radius: 8px;
    overflow: hidden;
    position: relative;
    background: #0c1b33;
    transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  }}

  .animated-hero-card:hover {{
    transform: translateY(-16px) scale(1.01);
  }}

  .animated-hero-img {{
    animation: kenBurnsZoom 14s ease-in-out infinite;
    width: 100%;
    height: 330px;
    object-fit: cover;
    display: block;
  }}

  .hero-img-badge {{
    animation: shimmerGlow 3s ease-in-out infinite;
  }}
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Preparing legal retrieval workspace…")
def _init_legal_retriever(_corpus: list[dict], cache_token: str = "v4_live") -> LegalRetriever:
    return LegalRetriever(_corpus)


def get_retriever() -> LegalRetriever:
    corpus = load_corpus()
    retriever = _init_legal_retriever(corpus, cache_token="v4_live")
    if not hasattr(retriever, "live_web_search"):
        _init_legal_retriever.clear()
        retriever = LegalRetriever(corpus)
    return retriever


def reset_retriever() -> None:
    _init_legal_retriever.clear()


def render_source_links(actions: list[dict]) -> None:
    for action in actions:
        st.markdown(f"- [{action['label']}]({action['url']}) — {action['why']}")


def memo(question: str, result: dict) -> str:
    sources = "\n".join(
        f"- [S{i}] {item['title']} — {item['url']} (Cross-Encoder: {item.get('cross_encoder_prob', 0):.1%})"
        for i, item in enumerate(result["evidence"], 1)
    ) or "- No adequate source material was retrieved."
    outcome = result["answer"] or f"Insufficient evidence: {result['evidence_reason']}"
    reformulate_note = f" (Reformulated from original inquiry: '{result.get('reformulate_reason', '')}')" if result.get('was_reformulated') else " (Original query verified specific)"
    retry_note = f"\n- Stage 6 Retry Query: {result.get('retry_query')}" if result.get('retried') else ""
    return f"""# NyayaRoute Legal Research Memo

**Original Question:** {question}
**Reformulated Search Query:** {result['query_used']}{reformulate_note}

**Research outcome**

{outcome}

## Sources consulted
{sources}

## 7-Stage Pipeline Audit Trail
- Stage 1 Query Analysis: {result.get('quality_reason', '')}
- Stage 2 Reformulated Query: {result['query_used']} (Was Reformulated: {'Yes' if result.get('was_reformulated') else 'No'})
- Stage 3 Retrieval Route: {result['route']} — {result['route_reason']}
- Stage 4 Neural Reranker: ms-marco-MiniLM evaluated {result.get('candidate_count', 0)} passages ({result.get('live_web_count', 0)} live judicial precedents)
- Stage 5 Evidence Sufficiency Gate: {'Passed' if result['enough'] else 'Not Passed'} — {result['evidence_reason']}
- Stage 6 Retry Executed: {'Yes' if result['retried'] else 'No'}{retry_note}
- Stage 7 Guardrail Status: {'Authoritative Answer' if not result.get('is_insufficient_evidence_response') else 'Explicit Refusal to Hallucinate'}
- Live Web Retrieval: {'Active (Real-time Judicial Precedents)' if result.get('use_live_web') else 'Disabled'}

*This is legal research information, not legal advice. Verify the current primary text and seek qualified legal counsel for advice.*
"""


# ── Top Navigation Bar ────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid rgba(197,198,206,0.5); padding:0.6rem 0 1rem; margin-bottom:1.5rem;">
  <div style="display:flex; align-items:center; gap:2rem;">
    <span style="font-family:'Playfair Display',serif; font-size:1.35rem; font-weight:700; text-transform:uppercase; letter-spacing:0.15em; color:#000;">NYAYAROUTE</span>
    <div style="display:flex; gap:1.5rem; align-items:center;">
      <span style="font-family:'Inter',sans-serif; font-size:0.82rem; font-weight:600; color:#000; border-bottom:1.5px solid #000; padding-bottom:2px;">Research</span>
      <span style="font-family:'Inter',sans-serif; font-size:0.82rem; color:#44474d;">Precedents</span>
      <span style="font-family:'Inter',sans-serif; font-size:0.82rem; color:#44474d;">Library</span>
      <span style="font-family:'Inter',sans-serif; font-size:0.82rem; color:#44474d;">Archive</span>
    </div>
  </div>
  <div style="display:flex; align-items:center; gap:1.25rem;">
    <span class="material-symbols-outlined" style="color:#44474d; font-size:22px; cursor:pointer;">account_balance</span>
    <span class="material-symbols-outlined" style="color:#44474d; font-size:22px; cursor:pointer;">settings</span>
    <div style="background:#0c1b33; color:#ffffff; font-family:'Inter',sans-serif; font-size:0.72rem; font-weight:600; text-transform:uppercase; letter-spacing:0.1em; padding:0.5rem 1.25rem; border-radius:2px;">
      Institutional Access
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Hero Section with Animated Legal Picture Showcase ─────────────────────────
st.markdown(f"""
<div style="padding:1rem 0 2rem; border-bottom:1px solid rgba(197,198,206,0.3); margin-bottom:2rem; display:grid; grid-template-columns: 1.1fr 0.9fr; gap:2.5rem; align-items:center;">
  <div>
    <span style="font-family:'Inter',sans-serif; font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.3em; color:#735a3a; display:block; margin-bottom:0.75rem;">
      Legacy of Intelligence
    </span>
    <h1 style="font-family:'Playfair Display',serif; font-size:2.8rem; font-weight:700; line-height:1.1; color:#000; margin:0 0 1rem; letter-spacing:-0.02em;">
      Institutional <span style="font-style:italic;">Authority</span> in Legal Jurisprudence.
    </h1>
    <p style="font-family:'Inter',sans-serif; font-size:0.95rem; line-height:1.75; color:#44474d; margin:0 0 1.5rem;">
      NyayaRoute delivers sovereign-grade insights, synthesizing centuries of precedents with the computational precision of modern legal technology.
    </p>
    <div style="display:flex; gap:1rem;">
      <span style="background:#000000; color:#ffffff; font-family:'Inter',sans-serif; font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.1em; padding:0.75rem 1.75rem; border-radius:3px; display:inline-block; cursor:pointer;">Begin Inquiry</span>
      <span style="border:1px solid #75777e; color:#1a1c1b; font-family:'Inter',sans-serif; font-size:0.75rem; font-weight:600; text-transform:uppercase; letter-spacing:0.1em; padding:0.75rem 1.75rem; border-radius:3px; display:inline-block; cursor:pointer;">White Papers</span>
    </div>
  </div>

  <!-- Animated Legal Picture Card -->
  <div class="animated-hero-card">
    <div style="position:relative; overflow:hidden;">
      <img src="{img_src}" alt="Scales of Justice and Gavel" class="animated-hero-img" />
      <div style="position:absolute; inset:0; background:linear-gradient(to top, rgba(12,27,51,0.85) 0%, transparent 60%); pointer-events:none;"></div>
      <div style="position:absolute; bottom:1.25rem; left:1.25rem; right:1.25rem; z-index:2; display:flex; justify-content:space-between; align-items:flex-end;">
        <div>
          <span class="hero-img-badge" style="background:#735a3a; color:#ffffff; font-family:'Inter',sans-serif; font-size:0.6rem; font-weight:700; text-transform:uppercase; letter-spacing:0.12em; padding:3px 8px; border-radius:2px; display:inline-block; margin-bottom:0.4rem;">
            Sovereign Jurisprudence
          </span>
          <h4 style="font-family:'Playfair Display',serif; font-size:1.15rem; font-weight:600; color:#ffffff; margin:0;">
            Scales of Justice &amp; Precedent Archive
          </h4>
        </div>
        <span class="material-symbols-outlined" style="color:#d7e3ff; font-size:24px;">gavel</span>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Global Sidebar ─────────────────────────────────────────────────────────────
corpus = load_corpus()
source_options = sorted({item["source"] for item in corpus})

if "use_live_web" not in st.session_state:
    st.session_state["use_live_web"] = True
if "selected_sources" not in st.session_state:
    st.session_state["selected_sources"] = source_options

with st.sidebar:
    st.markdown("<h3 style='font-family:\"Playfair Display\",serif; font-size:1.3rem; font-weight:700; margin-bottom:0.75rem; color:#0c1b33;'>⚖ Research Settings</h3>", unsafe_allow_html=True)
    
    use_live_web_sb = st.toggle(
        "🌐 Real-Time Precedent Search",
        value=st.session_state["use_live_web"],
        key="sb_toggle_live_web",
        help="When enabled, retrieves live Supreme Court and High Court judgments and precedents in real-time."
    )
    st.session_state["use_live_web"] = use_live_web_sb
    if use_live_web_sb:
        st.caption("🟢 Live Retrieval Active: Real-time judicial precedents will be retrieved, neural re-ranked, and cited.")
    else:
        st.caption("⚪ Local Mode: Limited to indexed local corpus chunks.")

    selected_sources_sb = st.multiselect(
        "Search these sources",
        source_options,
        default=st.session_state["selected_sources"],
        key="sb_multiselect_sources",
    )
    st.session_state["selected_sources"] = selected_sources_sb
    st.caption("Use the source filter to focus statutory research or case-law research.")
    
    st.divider()
    st.metric("Local Legal Chunks", len(corpus))
    st.caption(f"{len(source_summary(corpus))} source page(s) indexed")
    
    with st.expander("AI Synthesis Mode", expanded=not bool(os.getenv("GROQ_API_KEY"))):
        api_key_input = st.text_input(
            "Groq API Key (Optional)",
            value=os.getenv("GROQ_API_KEY", ""),
            type="password",
            help="Enter your Groq key for generative synthesis with Groq LLMs. If omitted, local extractive legal synthesis is used automatically."
        )
        if api_key_input and api_key_input != os.getenv("GROQ_API_KEY"):
            os.environ["GROQ_API_KEY"] = api_key_input
            st.rerun()

    if os.getenv("GROQ_API_KEY"):
        st.success(f"Generative LLM Active · {os.getenv('GROQ_MODEL', 'qwen/qwen3.8-27b')}")
    else:
        st.info("Local Extractive Synthesis Active. (Add Groq key for generative reasoning).")
    st.info("Not legal advice. Verify citations in their original source.")


workspace_tab, library_tab, kb_tab, about_tab = st.tabs(
    ["Research workspace", "Source library", "Knowledge Base", "How to use this"]
)
# ──────────────────────────────────────────────────────────────────────────────
with workspace_tab:
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None

    # ── Institutional Access Search Banner ───────────────────────────────────
    st.markdown("""
    <div style="background:#0c1b33; border-radius:6px; padding:2rem; margin-bottom:1.5rem; color:#ffffff;">
      <div style="display:flex; justify-content:space-between; align-items:flex-end; margin-bottom:1.25rem; flex-wrap:wrap; gap:1rem;">
        <div>
          <h2 style="font-family:'Playfair Display',serif; font-size:1.6rem; font-weight:600; color:#ffffff; margin:0 0 0.3rem;">Institutional Access</h2>
          <p style="font-family:'Inter',sans-serif; font-size:0.85rem; color:#7684a1; margin:0; max-width:520px;">
            Execute complex thematic searches across the unified codebase of federal and state statutes.
          </p>
        </div>
        <span style="font-family:'Inter',sans-serif; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.12em; color:#7684a1;">
          System Status: Optimal
        </span>
      </div>
      <div style="display:flex; flex-wrap:wrap; gap:1rem; align-items:center; margin-top:0.75rem; border-top:1px solid rgba(255,255,255,0.1); padding-top:1rem;">
        <span style="font-family:'Inter',sans-serif; font-size:0.7rem; text-transform:uppercase; color:#7684a1;">Trending Queries:</span>
        <span style="font-family:'Inter',sans-serif; font-size:0.7rem; color:#ffffff; text-decoration:underline; text-underline-offset:3px;">Digital Privacy Act 2024</span>
        <span style="font-family:'Inter',sans-serif; font-size:0.7rem; color:#ffffff; text-decoration:underline; text-underline-offset:3px;">Land Reform Precedents</span>
        <span style="font-family:'Inter',sans-serif; font-size:0.7rem; color:#ffffff; text-decoration:underline; text-underline-offset:3px;">Maritime Jurisdiction</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Question text area
    default_val = st.session_state.get("pending_question") or ""
    question = st.text_area(
        "Your legal research question",
        value=default_val,
        placeholder="Query the Code: fundamental rights under environmental distress...",
        height=110,
        label_visibility="collapsed",
    )

    # Sample query buttons
    samples = st.columns(3)
    sample_items = [
        ("Fundamental Rights (Art 21)", "What does Article 21 of the Constitution protect?"),
        ("IT Act Amendments", "What is the latest amendment to the IT Act?"),
        ("Writ & Liberty Cases", "Which Supreme Court cases discuss personal liberty?"),
    ]
    for col, (label, val) in zip(samples, sample_items):
        if col.button(label, use_container_width=True):
            st.session_state.pending_question = val
            st.rerun()

    st.markdown("<div style='margin-top:1.25rem;'></div>", unsafe_allow_html=True)
    investigate = st.button("Research this question", type="primary")

    if investigate:
        active_sources = st.session_state.get("selected_sources") or source_options
        active_live_web = st.session_state.get("use_live_web", True)
        if not question.strip():
            st.warning("Please enter a legal research question first.")
        elif not active_sources:
            st.warning("Select at least one source to search.")
        else:
            with st.status("Executing 7-Stage Legal Intelligence Pipeline…", expanded=True) as status:
                result = run_agent(question.strip(), get_retriever(), set(active_sources), use_live_web=active_live_web)
                
                # Dynamic visual reporting of the 7 stages from the PPT
                analysis = result.get("analysis", {})
                terms_display = ", ".join(result.get("legal_terms", [])) if result.get("legal_terms") else "None detected"
                cits_display = ", ".join(result.get("citations", [])) if result.get("citations") else "None detected"
                st.write(f"✓ **Stage 1 (Query Analysis):** Legal terms: [{terms_display}] · Citations: [{cits_display}] · Ambiguity: {'Flagged' if analysis.get('is_ambiguous') else 'Clean/Specific'}.")
                
                if result.get("was_reformulated"):
                    st.write(f"✓ **Stage 2 (Reformulation):** Reformulated weak/ambiguous query to: *\"{result['query_used']}\"* ({result['reformulate_reason']})")
                else:
                    st.write("✓ **Stage 2 (Query Validation):** Query sufficiently grounded; proceeding with original query.")
                
                st.write(f"✓ **Stage 3 (Routing):** Routed to **{result['route']}** ({result.get('candidate_count', 0)} candidates).")
                
                if result.get("use_live_web"):
                    st.write(f"✓ **Stage 4 (Neural Cross-Encoder):** Evaluated {result.get('candidate_count', 0)} candidate authorities ({result.get('live_web_count', 0)} live judicial precedents) using ms-marco-MiniLM.")
                else:
                    st.write(f"✓ **Stage 4 (Cross-Encoder Re-Ranking):** Scored candidate passages using ms-marco-MiniLM neural relevance model.")
                
                if result.get("enough"):
                    st.write(f"✓ **Stage 5 (Evidence Sufficiency Gate):** **PASSED** ({result['evidence_reason']})")
                    st.write("✓ **Stage 6 (Retry Assessment):** Bypassed (first-pass evidence passed sufficiency gate).")
                    st.write("✓ **Stage 7 (Answer Synthesis):** Grounded legal brief synthesized with source citations.")
                    status.update(label="✓ 7-Stage Pipeline Complete: Verified Authority Grounded", state="complete")
                else:
                    st.write(f"⚠ **Stage 5 (Evidence Sufficiency Gate):** **INSUFFICIENT** ({result['evidence_reason']})")
                    if result.get("retried"):
                        st.write(f"✓ **Stage 6 (Targeted Retry):** Reformulated query retry escalated to {result.get('retry_route', 'Hybrid Retrieval')}.")
                    st.write("✓ **Stage 7 (Safe Refusal):** Explicit Insufficient-Evidence Declaration returned (hallucination prevented).")
                    status.update(label="⚠ 7-Stage Pipeline Complete: Insufficient Evidence Safeguard", state="complete")

            st.session_state["research_result"] = result
            st.session_state["research_question"] = question.strip()

    result = st.session_state.get("research_result")
    research_question = st.session_state.get("research_question")

    if result and research_question:
        # Active Workspace Header & Metrics
        st.markdown(f"""<div style="display:flex; align-items:center; justify-content:space-between; border-bottom:2px solid #000; padding-bottom:0.6rem; margin:2.5rem 0 1.5rem;">
<div style="display:flex; align-items:center; gap:0.75rem;">
<h3 style="font-family:'Playfair Display',serif; font-size:1.4rem; font-weight:700; color:#000; margin:0;">Active Workspace</h3>
<span style="background:{'#d1fae5' if result['enough'] else '#fef3c7'}; color:{'#065f46' if result['enough'] else '#92400e'}; font-family:'Inter',sans-serif; font-size:0.65rem; font-weight:700; text-transform:uppercase; padding:3px 10px; letter-spacing:0.05em; border-radius:3px;">
{'Verified Grounded' if result['enough'] else 'Insufficient Evidence Refusal'}
</span>
</div>
<div style="display:flex; gap:0.75rem;">
<div style="background:#fff; border:1px solid #c5c6ce; padding:0.5rem 0.9rem; text-align:center; border-radius:4px;">
<span style="font-family:'Playfair Display',serif; font-size:0.95rem; font-weight:700; color:#000; display:block;">{len(corpus)}</span>
<span style="font-family:'Inter',sans-serif; font-size:0.6rem; text-transform:uppercase; color:#44474d; letter-spacing:0.05em;">Legal Chunks</span>
</div>
<div style="background:#fff; border:1px solid #c5c6ce; padding:0.5rem 0.9rem; text-align:center; border-radius:4px;">
<span style="font-family:'Playfair Display',serif; font-size:0.95rem; font-weight:700; color:#000; display:block;">{result.get('latency_seconds', 0.28):.2f}s</span>
<span style="font-family:'Inter',sans-serif; font-size:0.6rem; text-transform:uppercase; color:#44474d; letter-spacing:0.05em;">Latency</span>
</div>
</div>
</div>""", unsafe_allow_html=True)

        left_col, right_col = st.columns([2, 1], gap="large")

        with left_col:
            query_used = result.get('query_used', research_question)
            was_reformulated = result.get('was_reformulated', False)
            reformulate_reason = result.get('reformulate_reason', '')
            retried = result.get('retried', False)
            retry_query = result.get('retry_query', '')

            # Core Authority Card (or Explicit Insufficient-Evidence Declaration)
            if result["enough"] and result.get("answer"):
                badge_bg = '#d1fae5' if was_reformulated else '#e0f2fe'
                badge_color = '#065f46' if was_reformulated else '#0369a1'
                badge_text = '✓ Reformulated for Precision' if was_reformulated else '✓ Specific Query Retained'

                retry_badge_html = f'<div style="margin-top:6px; padding-top:6px; border-top:1px dashed #cbd5e1;"><span style="font-weight:700; color:#b45309; font-size:0.75rem; text-transform:uppercase;">Stage 6 Retry Query: </span><code style="background:#fffbeb; color:#b45309; padding:2px 6px; border-radius:3px; font-weight:600; border:1px solid #fde68a;">{retry_query}</code></div>' if retried and retry_query else ''

                rationale_html = f'<div style="margin-top:4px; font-size:0.75rem; color:#475569;"><em>Rationale:</em> {reformulate_reason}</div>' if reformulate_reason and was_reformulated else ''

                header_html = f"""<div style="background:#ffffff; border:1px solid #c5c6ce; border-radius:6px; padding:1.5rem 1.75rem 1.25rem; margin-bottom:1.25rem;">
<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.75rem;">
<div>
<span style="font-family:'Inter',sans-serif; font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; color:#735a3a;">
Core Authority &amp; Synthesis (7-Stage Pipeline Output)
</span>
<h4 style="font-family:'Playfair Display',serif; font-size:1.3rem; font-weight:600; color:#1a1c1b; margin:0.3rem 0 0;">
{research_question}
</h4>
</div>
<span class="material-symbols-outlined" style="color:#735a3a; font-size:22px;">verified</span>
</div>
<div style="height:1px; background:#c5c6ce; opacity:0.5; margin:0.75rem 0 1rem;"></div>
<div style="background:#f8f9fa; border:1px solid #e2e8f0; border-left:4px solid #735a3a; border-radius:4px; padding:0.85rem 1rem; margin-bottom:0.25rem;">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
<span style="font-family:'Inter',sans-serif; font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:#735a3a;">Stage 2 Search Query Transformation</span>
<span style="font-family:'Inter',sans-serif; font-size:0.65rem; font-weight:700; background:{badge_bg}; color:{badge_color}; padding:2px 8px; border-radius:3px;">{badge_text}</span>
</div>
<div style="font-family:'Inter',sans-serif; font-size:0.85rem; line-height:1.5; color:#1a1c1b;">
<div style="margin-bottom:0.35rem;"><span style="font-weight:600; color:#64748b; font-size:0.75rem; text-transform:uppercase;">Original Inquiry: </span><span style="color:#334155; font-style:italic;">"{research_question}"</span></div>
<div><span style="font-weight:700; color:#0c1b33; font-size:0.75rem; text-transform:uppercase;">Reformulated Search Query: </span><code style="background:#ffffff; border:1px solid #cbd5e1; color:#0c1b33; font-weight:600; font-size:0.83rem; padding:2px 8px; border-radius:3px;">{query_used}</code></div>
{rationale_html}
{retry_badge_html}
</div>
</div>
</div>"""
                st.markdown(header_html, unsafe_allow_html=True)
                st.markdown(result["answer"])

                metrics_html = f"""<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:0.75rem; margin:1.25rem 0 1.5rem;">
<div style="background:#f4f3f1; border-radius:4px; padding:0.85rem; border:1px solid #e2e8f0;">
<p style="font-size:0.62rem; text-transform:uppercase; letter-spacing:0.05em; color:#44474d; margin-bottom:0.2rem;">Retrieval Route</p>
<p style="font-weight:700; font-size:0.85rem; color:#1a1c1b; margin:0;">{result['route']}</p>
</div>
<div style="background:#f4f3f1; border-radius:4px; padding:0.85rem; border:1px solid #e2e8f0;">
<p style="font-size:0.62rem; text-transform:uppercase; letter-spacing:0.05em; color:#44474d; margin-bottom:0.2rem;">Citations</p>
<p style="font-weight:700; font-size:0.85rem; color:#1a1c1b; margin:0;">{len(result['evidence'])} Authorities</p>
</div>
<div style="background:#f4f3f1; border-radius:4px; padding:0.85rem; border:1px solid #e2e8f0;">
<p style="font-size:0.62rem; text-transform:uppercase; letter-spacing:0.05em; color:#44474d; margin-bottom:0.2rem;">Gate Status</p>
<p style="font-weight:700; font-size:0.85rem; color:#047857; margin:0;">Evidence Passed</p>
</div>
</div>"""
                st.markdown(metrics_html, unsafe_allow_html=True)

            else:
                badge_bg = '#fef3c7' if was_reformulated else '#e0f2fe'
                badge_color = '#92400e' if was_reformulated else '#0369a1'
                badge_text = '✓ Reformulated' if was_reformulated else '✓ Evaluated Query'

                retry_badge_html = f'<div style="margin-top:6px; padding-top:6px; border-top:1px dashed #fed7aa;"><span style="font-weight:700; color:#b45309; font-size:0.75rem; text-transform:uppercase;">Stage 6 Retry Attempted: </span><code style="background:#fffbeb; color:#b45309; padding:2px 6px; border-radius:3px; font-weight:600; border:1px solid #fde68a;">{retry_query}</code></div>' if retried and retry_query else ''

                rationale_html = f'<div style="margin-top:4px; font-size:0.75rem; color:#92400e;"><em>Rationale:</em> {reformulate_reason}</div>' if reformulate_reason and was_reformulated else ''

                refusal_header_html = f"""<div style="background:#fffbf1; border:1px solid #fddab2; border-left:4px solid #b45309; border-radius:6px; padding:1.5rem 1.75rem 1.25rem; margin-bottom:1.25rem;">
<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:0.75rem;">
<div>
<span style="font-family:'Inter',sans-serif; font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; color:#b45309;">
Explicit Insufficient Evidence Declaration (Refusal to Hallucinate)
</span>
<h4 style="font-family:'Playfair Display',serif; font-size:1.25rem; font-weight:600; color:#1a1c1b; margin:0.3rem 0 0;">
{research_question}
</h4>
</div>
<span class="material-symbols-outlined" style="color:#b45309; font-size:22px;">shield</span>
</div>
<div style="height:1px; background:#fddab2; opacity:0.8; margin:0.75rem 0 1rem;"></div>
<div style="background:#fff7ed; border:1px solid #fed7aa; border-left:4px solid #b45309; border-radius:4px; padding:0.85rem 1rem; margin-bottom:0.25rem;">
<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.4rem;">
<span style="font-family:'Inter',sans-serif; font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; color:#b45309;">Stage 2 Search Query Transformation</span>
<span style="font-family:'Inter',sans-serif; font-size:0.65rem; font-weight:700; background:{badge_bg}; color:{badge_color}; padding:2px 8px; border-radius:3px;">{badge_text}</span>
</div>
<div style="font-family:'Inter',sans-serif; font-size:0.85rem; line-height:1.5; color:#1a1c1b;">
<div style="margin-bottom:0.35rem;"><span style="font-weight:600; color:#9a3412; font-size:0.75rem; text-transform:uppercase;">Original Inquiry: </span><span style="color:#431407; font-style:italic;">"{research_question}"</span></div>
<div><span style="font-weight:700; color:#7c2d12; font-size:0.75rem; text-transform:uppercase;">Evaluated Search Query: </span><code style="background:#ffffff; border:1px solid #fed7aa; color:#7c2d12; font-weight:600; font-size:0.83rem; padding:2px 8px; border-radius:3px;">{query_used}</code></div>
{rationale_html}
{retry_badge_html}
</div>
</div>
</div>"""
                st.markdown(refusal_header_html, unsafe_allow_html=True)
                st.markdown(result.get('answer', result.get('evidence_reason')))
                st.markdown("**Recommended Primary Legal Portals**")
                render_source_links(result["actions"])
                st.caption("Verify against official primary databases or ingest the relevant Bare Act / Judgment PDF into the Source Library.")

            # Live 3-Card Snapshot
            snapshot_html = f"""<div style="display:grid; grid-template-columns:repeat(3,1fr); gap:0.75rem; margin-bottom:1.5rem;">
<div style="background:#ffffff; border:1px solid #c5c6ce; border-left:4px solid #735a3a; padding:1.1rem; border-radius:4px;">
<span style="font-family:'Inter',sans-serif; font-size:0.62rem; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; color:#735a3a; display:block; margin-bottom:0.5rem;">Evidence Gate</span>
<p style="font-family:'Inter',sans-serif; font-size:0.8rem; color:#1a1c1b; margin-bottom:0.5rem; line-height:1.4;">{result['evidence_reason']}</p>
<span style="font-family:'Inter',sans-serif; font-size:0.65rem; color:#44474d;">Status: {'Passed' if result['enough'] else 'Insufficient'}</span>
</div>
<div style="background:#ffffff; border:1px solid #c5c6ce; border-left:4px solid #0c1b33; padding:1.1rem; border-radius:4px;">
<span style="font-family:'Inter',sans-serif; font-size:0.62rem; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; color:#0c1b33; display:block; margin-bottom:0.5rem;">Routing Decision</span>
<p style="font-family:'Inter',sans-serif; font-size:0.8rem; color:#1a1c1b; margin-bottom:0.5rem; line-height:1.4;">Route: <strong>{result['route']}</strong>. {result['route_reason'][:90]}...</p>
<span style="font-family:'Inter',sans-serif; font-size:0.65rem; color:#44474d;">Reranker: ms-marco-MiniLM</span>
</div>
<div style="background:#ffffff; border:1px solid #c5c6ce; border-left:4px solid #047857; padding:1.1rem; border-radius:4px;">
<span style="font-family:'Inter',sans-serif; font-size:0.62rem; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; color:#047857; display:block; margin-bottom:0.5rem;">Corpus Coverage</span>
<p style="font-family:'Inter',sans-serif; font-size:0.8rem; color:#1a1c1b; margin-bottom:0.5rem; line-height:1.4;">FAISS Vector Index &amp; BM25 active ({len(corpus)} local legal chunks).</p>
<span style="font-family:'Inter',sans-serif; font-size:0.65rem; color:#44474d;">Cross-Encoder Neural Reranking</span>
</div>
</div>"""
            st.markdown(snapshot_html, unsafe_allow_html=True)

            # Authorities & Citations with Neural Re-Ranking Scores
            st.markdown("<h4 style='font-family:\"Playfair Display\",serif; font-size:1.25rem; font-weight:700; font-style:italic; margin-bottom:1rem;'>Authorities and citations</h4>", unsafe_allow_html=True)
            if not result["evidence"]:
                st.caption("No relevant chunks were retrieved from the selected local source library.")

            for index, item in enumerate(result["evidence"], 1):
                ce_prob = item.get("cross_encoder_prob", item.get("relevance", 0))
                ce_score = item.get("cross_encoder_score", item.get("score", 0))
                anchor_match = item.get("relevance", 0)
                is_live = item.get("source") == "Indian Kanoon" and str(item.get("id", "")).startswith("live_")
                source_tag = "🌐 Judicial Precedent" if is_live else item['source']
                with st.expander(f"[S{index}] {item['title']} · {source_tag} · Neural Confidence: {ce_prob:.1%} (Score: {ce_score:.2f}) · {anchor_match:.0%} anchor match"):
                    if is_live:
                        st.markdown(f"**Live Judicial Precedent:** [{item['url']}]({item['url']}) · [View Full Judgment ↗]({item['url']})")
                    else:
                        st.markdown(f"**Primary link:** [{item['url']}]({item['url']})")
                    st.caption("Verify the full source text, date, court/bench, and later treatment before judicial reliance.")
                    st.write(item["text"])

            # Comprehensive 7-Stage Pipeline Audit Trail
            with st.expander("7-Stage Legal Intelligence Audit Trail (PPT Pipeline Specification)", expanded=True):
                st.markdown("##### Stage-by-Stage Verification Breakdown")
                
                s_cols1 = st.columns(3)
                with s_cols1[0]:
                    st.markdown("""<div style="border:1px solid #c5c6ce; border-radius:4px; padding:0.85rem; background:#fff; height:100%;">
<small style="color:#735a3a; font-weight:700; text-transform:uppercase; font-size:0.65rem;">Stage 1: Query Analysis</small><br>
<strong style="color:#1a1c1b; font-size:0.88rem;">Terms, Entities &amp; Citations</strong><br>
</div>""", unsafe_allow_html=True)
                    st.caption(f"**Legal terms:** {', '.join(result.get('legal_terms', [])) or 'None'}")
                    st.caption(f"**Citations:** {', '.join(result.get('citations', [])) or 'None'}")
                    st.caption(f"**Entities:** {', '.join(result.get('entities', [])) or 'None'}")
                    st.caption(f"**Ambiguity:** {'Flagged' if result.get('analysis', {}).get('is_ambiguous') else 'Clean/Specific'}")

                with s_cols1[1]:
                    st.markdown("""<div style="border:1px solid #c5c6ce; border-radius:4px; padding:0.85rem; background:#fff; height:100%;">
<small style="color:#735a3a; font-weight:700; text-transform:uppercase; font-size:0.65rem;">Stage 2: Reformulation</small><br>
<strong style="color:#1a1c1b; font-size:0.88rem;">Weak/Ambiguous Resolution</strong><br>
</div>""", unsafe_allow_html=True)
                    st.caption(f"**Was Reformulated:** {'Yes' if result.get('was_reformulated') else 'No'}")
                    st.caption(f"**Effective Query:** {result.get('query_used', '')}")
                    st.caption(f"**Rationale:** {result.get('reformulate_reason', 'Query already specific.')}")

                with s_cols1[2]:
                    st.markdown("""<div style="border:1px solid #c5c6ce; border-radius:4px; padding:0.85rem; background:#fff; height:100%;">
<small style="color:#735a3a; font-weight:700; text-transform:uppercase; font-size:0.65rem;">Stage 3: Retrieval Route</small><br>
<strong style="color:#1a1c1b; font-size:0.88rem;">BM25 / Dense / Hybrid</strong><br>
</div>""", unsafe_allow_html=True)
                    st.caption(f"**Selected Route:** {result.get('route', '')}")
                    st.caption(f"**Rationale:** {result.get('route_reason', '')}")
                    st.caption(f"**Candidates Retrieved:** {result.get('candidate_count', len(result.get('evidence', [])))}")

                top_match_display = f"{result['evidence'][0].get('cross_encoder_prob', 0):.1%}" if result.get("evidence") else "N/A"
                s_cols2 = st.columns(4)
                with s_cols2[0]:
                    st.markdown(f"""<div style="border:1px solid #c5c6ce; border-radius:4px; padding:0.85rem; background:#fff; margin-top:0.75rem;">
<small style="color:#735a3a; font-weight:700; text-transform:uppercase; font-size:0.65rem;">Stage 4: Re-Ranking</small><br>
<strong style="color:#1a1c1b; font-size:0.85rem;">Cross-Encoder</strong><br>
<small style="color:#44474d; font-size:0.72rem;">Model: ms-marco-MiniLM-L-6-v2<br>Top Neural Match: {top_match_display}</small>
</div>""", unsafe_allow_html=True)

                with s_cols2[1]:
                    st.markdown(f"""<div style="border:1px solid #c5c6ce; border-radius:4px; padding:0.85rem; background:#fff; margin-top:0.75rem;">
<small style="color:#735a3a; font-weight:700; text-transform:uppercase; font-size:0.65rem;">Stage 5: Sufficiency Gate</small><br>
<strong style="color:{'#047857' if result['enough'] else '#b45309'}; font-size:0.85rem;">{'Passed' if result['enough'] else 'Insufficient'}</strong><br>
<small style="color:#44474d; font-size:0.72rem;">{result.get('evidence_reason', '')[:65]}...</small>
</div>""", unsafe_allow_html=True)

                with s_cols2[2]:
                    st.markdown(f"""<div style="border:1px solid #c5c6ce; border-radius:4px; padding:0.85rem; background:#fff; margin-top:0.75rem;">
<small style="color:#735a3a; font-weight:700; text-transform:uppercase; font-size:0.65rem;">Stage 6: Retry</small><br>
<strong style="color:#1a1c1b; font-size:0.85rem;">{'Invoked' if result['retried'] else 'Bypassed'}</strong><br>
<small style="color:#44474d; font-size:0.72rem;">{'Escalated to Hybrid search' if result['retried'] else 'First-pass passed'}</small>
</div>""", unsafe_allow_html=True)

                with s_cols2[3]:
                    st.markdown(f"""<div style="border:1px solid #c5c6ce; border-radius:4px; padding:0.85rem; background:#fff; margin-top:0.75rem;">
<small style="color:#735a3a; font-weight:700; text-transform:uppercase; font-size:0.65rem;">Stage 7: Output Guardrail</small><br>
<strong style="color:#1a1c1b; font-size:0.85rem;">{'Synthesis' if not result.get('is_insufficient_evidence_response') else 'Refusal'}</strong><br>
<small style="color:#44474d; font-size:0.72rem;">{'Grounded with citations' if not result.get('is_insufficient_evidence_response') else 'Hallucination prevented'}</small>
</div>""", unsafe_allow_html=True)

        with right_col:
            # Intelligence Summary Panel
            st.markdown(f"""<div style="background:#0c1b33; color:#ffffff; border-radius:6px; padding:1.75rem; margin-bottom:1.25rem;">
<h4 style="font-family:'Playfair Display',serif; font-size:1.2rem; font-weight:600; color:#b9c7e6; margin:0 0 1.25rem;">Intelligence Summary</h4>
<div style="font-family:'Inter',sans-serif; font-size:0.82rem; display:flex; flex-direction:column; gap:0.65rem;">
<div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.15); padding-bottom:0.6rem;">
<span style="color:rgba(255,255,255,0.85);">Query Analysis</span>
<span style="font-weight:700; color:#ffffff;">{'Clear' if result['good_query'] else 'Reformulated'}</span>
</div>
<div style="display:flex; flex-direction:column; gap:0.25rem; border-bottom:1px solid rgba(255,255,255,0.15); padding-bottom:0.6rem;">
<div style="display:flex; justify-content:space-between;">
<span style="color:rgba(255,255,255,0.85);">Stage 2 Search Query</span>
<span style="font-weight:700; color:{'#34d399' if result.get('was_reformulated') else '#93c5fd'};">{'Reformulated' if result.get('was_reformulated') else 'Retained'}</span>
</div>
<span style="font-size:0.72rem; color:#e2e8f0; font-family:monospace; background:rgba(255,255,255,0.08); padding:3px 6px; border-radius:3px; word-break:break-word;">
{result.get('query_used', research_question)}
</span>
</div>
<div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.15); padding-bottom:0.6rem;">
<span style="color:rgba(255,255,255,0.85);">Retrieval Route</span>
<span style="font-weight:700; color:#ffffff;">{result['route']}</span>
</div>
<div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.15); padding-bottom:0.6rem;">
<span style="color:rgba(255,255,255,0.85);">Neural Reranker</span>
<span style="font-weight:700; color:#ffffff;">ms-marco-MiniLM</span>
</div>
<div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.15); padding-bottom:0.6rem;">
<span style="color:rgba(255,255,255,0.85);">Real-Time Precedents</span>
<span style="font-weight:700; color:{'#34d399' if result.get('use_live_web') else '#94a3b8'};">{'Active' if result.get('use_live_web') else 'Disabled'}</span>
</div>
<div style="display:flex; justify-content:space-between; border-bottom:1px solid rgba(255,255,255,0.15); padding-bottom:0.6rem;">
<span style="color:rgba(255,255,255,0.85);">Retry Attempted</span>
<span style="font-weight:700; color:{'#fbbf24' if result['retried'] else '#34d399'};">{'Yes' if result['retried'] else 'No'}</span>
</div>
<div style="display:flex; justify-content:space-between;">
<span style="color:rgba(255,255,255,0.85);">Gate Verdict</span>
<span style="font-weight:700; color:{'#34d399' if result['enough'] else '#fbbf24'};">{'Passed' if result['enough'] else 'Insufficient'}</span>
</div>
</div>
</div>""", unsafe_allow_html=True)

            st.download_button(
                "Export Brief (.md)",
                memo(research_question, result),
                file_name=f"nyayaroute-{datetime.now():%Y%m%d-%H%M}.md",
                mime="text/markdown",
                use_container_width=True,
            )

            # Precedent Heatmap dynamically rendered
            evidence_scores = [ev.get("relevance", 0.0) for ev in result.get("evidence", [])]
            score_bars = ""
            for score in evidence_scores[:5]:
                score_bars += f'<div style="flex:{score+0.2:.2f}; height:35px; background:rgba(115,90,58,{max(0.25, score):.2f}); border-radius:2px;" title="{score:.0%} relevance"></div>'
            if not score_bars:
                score_bars = '<div style="flex:1; height:35px; background:rgba(115,90,58,0.2); border-radius:2px;"></div>'

            st.markdown(f"""<div style="background:#ffffff; border:1px solid #c5c6ce; border-radius:6px; overflow:hidden; margin-top:1.25rem;">
<div style="background:#f4f3f1; border-bottom:1px solid #c5c6ce; padding:0.75rem 1rem;">
<span style="font-family:'Inter',sans-serif; font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; color:#000000;">Precedent Heatmap</span>
</div>
<div style="padding:1rem; display:flex; flex-direction:column; gap:0.5rem;">
<div style="display:flex; gap:0.35rem; align-items:center;">
{score_bars}
</div>
<p style="font-family:'Inter',sans-serif; font-size:0.65rem; color:#44474d; margin:0;">
Relevance density across top {len(evidence_scores)} retrieved legal authorities.
</p>
</div>
</div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
with library_tab:
    st.markdown("<h3 style='font-family:\"Playfair Display\",serif; font-size:1.35rem; font-weight:700; margin-bottom:0.5rem;'>Source Library</h3>", unsafe_allow_html=True)
    st.write(
        "The workspace only answers from this local collection. "
        "Add specific legal document pages, not broad landing pages or bulk crawls."
    )
    current_sources = source_summary(load_corpus())
    if current_sources:
        for item in current_sources:
            st.markdown(
                f"**{item['title']}**  \n"
                f"{item['source']} · {item['chunks']} chunk(s) · [Open source]({item['url']})"
            )
    else:
        st.info("No sources are indexed yet. Use the form below to add a trusted source.")

    st.divider()
    st.markdown("<h3 style='font-family:\"Playfair Display\",serif; font-size:1.35rem; font-weight:700; margin-bottom:0.5rem;'>Add a Trusted Source</h3>", unsafe_allow_html=True)
    st.caption(
        "Allowed: India Code, Supreme Court of India, and official High Court portals. "
        "The tool is deliberately page-by-page and does not bulk crawl."
    )

    with st.form("ingest_source", clear_on_submit=True):
        source_url = st.text_input(
            "Specific document URL",
            placeholder="https://www.indiacode.nic.in/…",
        )
        display_title = st.text_input(
            "Optional label",
            placeholder="e.g., Information Technology Act, 2000",
        )
        submit_source = st.form_submit_button("Add to source library")

    if submit_source:
        if not source_url.strip():
            st.warning("Enter a source URL.")
        else:
            try:
                with st.spinner("Fetching and indexing the trusted source page…"):
                    count, title = ingest_trusted_url(
                        source_url.strip(), display_title.strip() or None
                    )
                reset_retriever()
                if count:
                    st.success(
                        f"Added {count} chunks from: {title}. "
                        "Return to Research workspace and ask your question again."
                    )
                else:
                    st.info("That page is already indexed; no new chunks were added.")
            except Exception as exc:
                st.error(f"Could not add this source: {exc}")

# ──────────────────────────────────────────────────────────────────────────────
# ──────────────────────────────────────────────────────────────────────────────
# KNOWLEDGE BASE — PDF INGESTION
with kb_tab:
    st.markdown(
        "<h2 style='font-family:\"Playfair Display\",serif;'>Knowledge Base</h2>",
        unsafe_allow_html=True,
    )

    st.markdown(
        "Upload official legal PDFs to expand NyayaRoute's searchable knowledge base."
    )

    uploaded_files = st.file_uploader(
        "Upload legal PDF(s)",
        type=["pdf"],
        accept_multiple_files=True,
        help="Acts, Constitution, judgments, Gazette notifications, Law Commission reports, etc.",
    )

    if uploaded_files:

        for uploaded_file in uploaded_files:

            st.markdown("---")
            st.markdown(f"### {uploaded_file.name}")

            file_bytes = uploaded_file.getvalue()

            # ── Preview ──────────────────────────────────────────────────────
            try:
                parsed, profile, structure_kind, chunks = preview_pdf(
                    file_bytes,
                    uploaded_file.name,
                )

                st.success("PDF successfully parsed.")

                # Document metadata
                st.markdown("#### Detected metadata")

                metadata_col1, metadata_col2 = st.columns(2)

                with metadata_col1:
                    st.write(f"**Document kind:** {profile.kind}")
                    st.write(f"**Act:** {profile.act}")
                    st.write(f"**Year:** {profile.year}")

                with metadata_col2:
                    st.write(f"**Source:** {profile.source}")
                    st.write(f"**Court:** {profile.court}")
                    st.write(f"**Structure:** {structure_kind}")

                # PDF statistics
                stat1, stat2, stat3 = st.columns(3)

                with stat1:
                    st.metric("Pages", parsed.num_pages_total)

                with stat2:
                    st.metric("Pages used", parsed.num_pages_used)

                with stat3:
                    st.metric("Chunks", len(chunks))

                # ── Metadata preview ─────────────────────────────────────────
                with st.expander("Preview extracted chunks"):

                    for i, chunk in enumerate(chunks[:5], start=1):

                        st.markdown(f"**Chunk {i}**")

                        st.write(
                            f"Structure: {chunk.structure_kind}"
                        )

                        if chunk.part:
                            st.write(f"Part: {chunk.part}")

                        if chunk.chapter:
                            st.write(f"Chapter: {chunk.chapter}")

                        if chunk.article:
                            st.write(f"Article: {chunk.article}")

                        if chunk.section:
                            st.write(f"Section: {chunk.section}")

                        if chunk.heading:
                            st.write(f"Heading: {chunk.heading}")

                        st.text_area(
                            "Text",
                            chunk.text,
                            height=150,
                            key=f"preview_{uploaded_file.name}_{i}",
                        )

                        st.markdown("---")

                # ── Classification override ─────────────────────────────────
                with st.expander("Override detected classification (optional)"):

                    source_override = st.text_input(
                        "Source",
                        value=profile.source,
                        key=f"source_{uploaded_file.name}",
                    )

                    act_override = st.text_input(
                        "Act / document name",
                        value=profile.act,
                        key=f"act_{uploaded_file.name}",
                    )

                # ── Index button ────────────────────────────────────────────
                if st.button(
                    f"Index {uploaded_file.name}",
                    type="primary",
                    key=f"index_{uploaded_file.name}",
                ):

                    try:

                        progress = st.progress(0)

                        progress.progress(20)

                        result = ingest_pdf(
                            file_bytes,
                            uploaded_file.name,
                            source_override=source_override or None,
                            act_override=act_override or None,
                        )

                        progress.progress(100)

                        st.success(
                            f"Successfully indexed {result.filename}: "
                            f"{result.chunks_created} chunks created."
                        )

                        # Results
                        result_col1, result_col2, result_col3 = st.columns(3)

                        with result_col1:
                            st.metric(
                                "Chunks created",
                                result.chunks_created,
                            )

                        with result_col2:
                            st.metric(
                                "Duplicates skipped",
                                result.chunks_skipped_duplicate,
                            )

                        with result_col3:
                            st.metric(
                                "Pages used",
                                result.pages_used,
                            )

                        if result.chunks_created == 0:

                            st.info(
                                "That PDF was already indexed; no new chunks were added."
                            )

                    except DuplicatePDFError:

                        st.warning(
                            "This PDF has already been indexed."
                        )

                    except PDFIngestionError as exc:

                        st.error(
                            f"Could not process this PDF: {exc}"
                        )

                    except Exception as exc:

                        st.error(
                            f"Unexpected indexing error: {exc}"
                        )

            except PDFIngestionError as exc:

                st.error(
                    f"Could not read {uploaded_file.name}: {exc}"
                )

            except Exception as exc:

                st.error(
                    f"Could not preview {uploaded_file.name}: {exc}"
                )

# ──────────────────────────────────────────────────────────────────────────────
with about_tab:
    st.markdown("<h3 style='font-family:\"Playfair Display\",serif; font-size:1.35rem; font-weight:700; margin-bottom:0.5rem;'>A Safer Way to Use Legal RAG</h3>", unsafe_allow_html=True)
    st.markdown("""
    1. Ask a focused legal research question.
    2. **NyayaRoute** checks whether the query needs clarification and selects BM25, vector, or hybrid retrieval.
    3. It reranks candidate chunks and tests whether a sufficiently relevant authority was retrieved.
    4. It either produces a cited, evidence-constrained research answer — or says what is missing and directs you to trusted sources.

    For current amendments, always add the current statutory text or notification first.  
    **A language model being available does not make it a source of law.**
    """)

# ── Institutional Footer ──────────────────────────────────────────────────────
st.markdown("""
<div style="border-top:1px solid #c5c6ce; margin-top:3rem; padding:1.5rem 0; display:flex; flex-wrap:wrap; justify-content:space-between; align-items:center; gap:1rem;">
  <span style="font-family:'Inter',sans-serif; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.1em; color:#44474d;">
    © 2026 NYAYAROUTE INTERNATIONAL. ALL RIGHTS RESERVED.
  </span>
  <div style="display:flex; gap:1.5rem; flex-wrap:wrap;">
    <a href="#" style="font-family:'Inter',sans-serif; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em; color:#44474d; text-decoration:underline; text-underline-offset:4px;">
      Terms of Service
    </a>
    <a href="#" style="font-family:'Inter',sans-serif; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em; color:#44474d; text-decoration:underline; text-underline-offset:4px;">
      Privacy Protocol
    </a>
    <a href="#" style="font-family:'Inter',sans-serif; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em; color:#44474d; text-decoration:underline; text-underline-offset:4px;">
      Compliance
    </a>
    <a href="#" style="font-family:'Inter',sans-serif; font-size:0.68rem; text-transform:uppercase; letter-spacing:0.08em; color:#44474d; text-decoration:underline; text-underline-offset:4px;">
      Institutional Contact
    </a>
  </div>
</div>
""", unsafe_allow_html=True)
