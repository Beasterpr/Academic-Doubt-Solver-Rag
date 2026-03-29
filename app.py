import os
import shutil

import streamlit as st

from ui.components import render_status_indicator
from ui.kb_ui import render_kb_tab
from ui.chat_ui import render_chat_tab
from ui.report_ui import render_report_tab
from ui.mcq_ui import render_mcq_tab

# PAGE CONFIG

st.set_page_config(
    page_title="ScholarAI — Academic Intelligence",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# CSS

def load_css():
    with open("styles/styles.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# SESSION STATE

defaults = {
    "vectordb":     None,
    "total_pages":  0,
    "total_chunks": 0,
    "total_pdf":    0,
    "kb_ready":     False,
    "chat_rag":     [],
    "chat_web":     [],
    "mcq_phase":    "setup",
    "mcq_answers":  {},
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# SIDEBAR

with st.sidebar:
    st.markdown(
        '<div class="sidebar-logo">🎓 ScholarAI</div>'
        '<div class="sidebar-tagline">Academic Intelligence Platform</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    st.markdown('<div class="sidebar-section-title">Knowledge Base</div>', unsafe_allow_html=True)

    if st.session_state.kb_ready:
        st.markdown(render_status_indicator(active=True), unsafe_allow_html=True)

        stats = [
            ("Pages Loaded",   st.session_state.total_pages),
            ("Chunks Created", st.session_state.total_chunks),
            ("PDFs Indexed",   st.session_state.total_pdf),
        ]

        for label, val in stats:
            st.markdown(
                f'<div class="sidebar-stat-row">'
                f'<span class="sidebar-stat-label">{label}</span>'
                f'<span class="sidebar-stat-value">{val}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.markdown(render_status_indicator(active=False), unsafe_allow_html=True)
        st.caption("Upload PDFs or URLs in the Knowledge Base tab.")

    st.divider()

    st.markdown('<div class="sidebar-section-title">System Config</div>', unsafe_allow_html=True)

    config = [
        ("Model",      "Llama 3.1 8B"),
        ("Provider",   "Groq"),
        ("Embeddings", "MiniLM-L6-v2"),
        ("Vector DB",  "ChromaDB"),
        ("Chunk Size", "700 tokens"),
        ("Overlap",    "150 tokens"),
    ]

    rows = "".join(
        f'<div class="sidebar-config-row">'
        f'<span class="sidebar-config-key">{k}</span>'
        f'<span class="sidebar-config-val">{v}</span>'
        f'</div>'
        for k, v in config
    )

    st.markdown(f'<div class="config-container">{rows}</div>', unsafe_allow_html=True)

    st.divider()
    st.markdown('<div class="sidebar-section-title">Actions</div>', unsafe_allow_html=True)

    if st.button("🗑️ Reset Knowledge Base", use_container_width=True):
        if st.session_state.kb_ready:
            for key in ["vectordb", "total_pages", "total_chunks", "total_pdf", "kb_ready"]:
                st.session_state[key] = defaults[key]
            if os.path.exists("uploaded"):
                shutil.rmtree("uploaded")
            st.cache_resource.clear()
            st.success("Knowledge base cleared.")
            st.rerun()
        else:
            st.warning("Nothing to reset.")

    if st.button("💬 Clear Chat History", use_container_width=True):
        st.session_state.chat_rag = []
        st.session_state.chat_web = []
        st.session_state.mcq_phase   = "setup"
        st.session_state.mcq_answers = {}
        st.success("Chat history cleared.")
        st.rerun()

# MAIN HEADER

col_h, col_badge = st.columns([3, 1])

with col_h:
    st.markdown('''
    <div class="header-title-wrapper">
        <span class="header-title">Academic Intelligence</span>
        <span class="header-title-gradient">&nbsp;Platform</span>
    </div>
    <p class="header-subtitle">
        RAG-powered Q&amp;A &nbsp;·&nbsp; Intelligent Web Search &nbsp;·&nbsp; Auto Report Generation
    </p>
    ''', unsafe_allow_html=True)

with col_badge:
    if st.session_state.kb_ready:
        st.markdown(
            '<div class="badge-container">'
            '<span class="badge badge-success">● KB Active</span>'
            '</div>',
            unsafe_allow_html=True,
        )

st.markdown('<div class="spacer-xs"></div>', unsafe_allow_html=True)
st.divider()

# TABS

tab1, tab2, tab3, tab4 = st.tabs([
    "  📂  Knowledge Base  ",
    "  💬  Chat  ",
    "  📑  Report Generator  ",
    "  🧩  MCQ Generator  ",
])

with tab1:
    render_kb_tab(defaults)

with tab2:
    render_chat_tab()

with tab3:
    render_report_tab()

with tab4:
    render_mcq_tab()
