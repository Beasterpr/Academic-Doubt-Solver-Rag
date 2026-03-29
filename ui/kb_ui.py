import os
import time

import streamlit as st

from services.rag_service import preprocessing
from ui.components import (
    render_page_hero,
    render_kb_stats_grid,
    render_empty_state,
    render_info_box,
)


# KNOWLEDGE BASE TAB

def render_kb_tab(defaults: dict):

    st.markdown(
        render_page_hero(
            "Knowledge Base",
            "Upload PDFs and web URLs to build a searchable knowledge base. "
            "Once indexed, ask questions in RAG mode from the Chat tab."
        ),
        unsafe_allow_html=True,
    )

    col_up, col_status = st.columns([1.1, 0.9], gap="large")

    with col_up:
        st.markdown('<div class="section-title">📄 PDF Documents</div>', unsafe_allow_html=True)

        pdf_files = st.file_uploader("Upload PDF files", type="pdf", accept_multiple_files=True)

        if pdf_files:
            pills = "".join(
                f'<span class="file-pill">📄 {f.name} '
                f'<span class="file-size">({f.size // 1024}KB)</span></span>'
                for f in pdf_files
            )
            st.markdown(f'<div class="file-pills-container">{pills}</div>', unsafe_allow_html=True)

        st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">🌐 Web URLs</div>', unsafe_allow_html=True)

        url_text = st.text_area(
            "Web URLs (one per line)",
            placeholder="https://en.wikipedia.org/wiki/Machine_learning\nhttps://arxiv.org/abs/...",
            height=120,
        )

    with col_status:
        st.markdown('<div class="section-title">⚡ Status</div>', unsafe_allow_html=True)

        if st.session_state.kb_ready:
            stats_grid = render_kb_stats_grid(
                st.session_state.total_pages,
                st.session_state.total_chunks,
                st.session_state.total_pdf,
                "✓ Ready",
            )
            st.markdown(
                f'<div class="kb-card fade-in-up">'
                f'<div class="kb-card-title">✅ Knowledge Base Active</div>'
                f'{stats_grid}'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                render_empty_state(
                    "📭",
                    "No Knowledge Base",
                    "Upload PDFs or enter URLs, then click Index."
                ),
                unsafe_allow_html=True,
            )

        st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)
        st.markdown(
            render_info_box(
                "How it works",
                '1️⃣&nbsp; Upload PDFs and / or paste URLs<br>'
                '2️⃣&nbsp; Click <b>Index Knowledge Base</b><br>'
                '3️⃣&nbsp; Switch to <b>Chat</b> tab<br>'
                '4️⃣&nbsp; Ask questions in <b style="color:var(--accent-cyan)">RAG mode</b>',
            ),
            unsafe_allow_html=True,
        )

    st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)

    if st.button("⚡ Index Knowledge Base", use_container_width=True):
        files = []

        if pdf_files:
            os.makedirs("uploaded/pdf", exist_ok=True)
            for f in pdf_files:
                path = os.path.join("uploaded/pdf", f.name)
                with open(path, "wb") as w:
                    w.write(f.read())
                files.append(path)

        if not files and not url_text.strip():
            st.warning("⚠️ Please upload at least one PDF or enter a URL.")
        else:
            with st.status("Building knowledge base…", expanded=True) as status:
                st.write("🔍 Loading and parsing documents…")
                db, p, c = preprocessing(files, url_text)
                st.write(f"✂️ Created {c} chunks from {p} pages")
                st.write("🧠 Embedding and indexing into ChromaDB…")
                time.sleep(0.3)
                st.session_state.vectordb    = db
                st.session_state.total_pages = p
                st.session_state.total_chunks = c
                st.session_state.total_pdf   = len(files)
                st.session_state.kb_ready    = True
                status.update(label="✅ Knowledge base ready!", state="complete")

            st.balloons()
            st.rerun()
