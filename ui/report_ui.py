import time

import streamlit as st

from core.models import llm_model
from loaders.document_loader import load_from_url, load_from_youtube, load_from_pdf
from services.report_service import generate_report
from ui.components import render_page_hero, render_report_steps


# REPORT TAB

def render_report_tab():

    st.markdown(
        render_page_hero(
            "Report Generator",
            "Feed any web article, YouTube video, or PDF and receive "
            "a structured professional report — executive summary, key findings, and conclusion."
        ),
        unsafe_allow_html=True,
    )

    r_left, r_right = st.columns([1, 1], gap="large")

    with r_left:
        st.markdown('<div class="section-title">📥 Source</div>', unsafe_allow_html=True)

        source_type = st.radio(
            "Source Type",
            ["🌐  Web URL", "▶️  YouTube", "📄  PDF"],
            horizontal=True,
            label_visibility="collapsed",
            key="report_source_type",
        )

        st.markdown('<div class="spacer-sm"></div>', unsafe_allow_html=True)

        url_input  = ""
        yt_input   = ""
        pdf_report = None

        if source_type == "🌐  Web URL":
            url_input = st.text_input(
                "URL",
                placeholder="https://en.wikipedia.org/wiki/Artificial_intelligence",
                key="report_url",
            )
        elif source_type == "▶️  YouTube":
            yt_input = st.text_input(
                "YouTube URL",
                placeholder="https://www.youtube.com/watch?v=...",
                key="report_yt",
            )
            st.caption("⚠️ Video must have captions/subtitles enabled.")
        elif source_type == "📄  PDF":
            pdf_report = st.file_uploader(
                "Upload PDF",
                type="pdf",
                accept_multiple_files=False,
                key="report_pdf",
            )

        label = url_input or yt_input or (pdf_report.name if pdf_report else "")

        if label:
            st.markdown(
                f'<div class="source-label">✓&nbsp;&nbsp;{label}</div>',
                unsafe_allow_html=True,
            )

    with r_right:
        st.markdown('<div class="section-title">⚙️ How It Works</div>', unsafe_allow_html=True)

        steps_info = [
            ("1", "Load & Parse",            "Content fetched and cleaned from your source."),
            ("2", "Smart Chunking",           "Split into up to 18 chunks (8K tokens) for rate-limit safety."),
            ("3", "Parallel Summarisation",   "4 threads process chunks simultaneously — ~4× faster."),
            ("4", "Report Synthesis",         "All summaries merged into a structured professional report."),
        ]

        st.markdown(render_report_steps(steps_info), unsafe_allow_html=True)

    st.markdown('<div class="spacer-md"></div>', unsafe_allow_html=True)

    if st.button("⚡ Generate Report", use_container_width=True, key="gen_btn"):
        has_input = (
            (source_type == "🌐  Web URL"  and url_input.strip()) or
            (source_type == "▶️  YouTube"  and yt_input.strip())  or
            (source_type == "📄  PDF"      and pdf_report is not None)
        )

        if not has_input:
            st.warning("⚠️ Please provide a source before generating.")
            st.stop()

        st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)

        step_ph  = st.empty()
        prog_bar = st.progress(0.0)
        prog_lbl = st.empty()

        STEPS = [
            ("📥", "Loading content"),
            ("✂️", "Splitting into chunks"),
            ("⚡", "Parallel summarisation"),
            ("📝", "Synthesising report"),
        ]

        def render_steps(current):
            rows = ""
            for i, (icon, step_label) in enumerate(STEPS, 1):
                if i < current:
                    dot, lc, sfx = "dot-done",   "step-label-done",   " ✓"
                elif i == current:
                    dot, lc, sfx = "dot-active",  "step-label-active", "…"
                else:
                    dot, lc, sfx = "dot-wait",    "step-label",        ""

                rows += (
                    f'<div class="step-row">'
                    f'<span class="step-dot {dot}"></span>'
                    f'<span style="font-size:14px;">{icon}</span>'
                    f'<span class="{lc}">{step_label}{sfx}</span>'
                    f'</div>'
                )
            step_ph.markdown(f'<div class="step-pipeline">{rows}</div>', unsafe_allow_html=True)

        # Step 1 — Load
        render_steps(1)
        prog_bar.progress(0.04)

        try:
            if source_type == "🌐  Web URL":
                report_docs = load_from_url(url_input.strip())
            elif source_type == "▶️  YouTube":
                report_docs = load_from_youtube(yt_input.strip())
            else:
                pdf_report.seek(0)
                report_docs = load_from_pdf(pdf_report)
        except Exception as e:
            st.error(f"❌ Failed to load: {e}")
            st.stop()

        # Step 2 — Chunk
        render_steps(2)
        prog_bar.progress(0.08)

        # Step 3 — Summarise
        render_steps(3)

        llm = llm_model()

        def on_chunk(done, total):
            prog_bar.progress(min(0.10 + 0.75 * (done / total), 0.85))
            prog_lbl.markdown(
                f'<p class="progress-label">Processing chunk '
                f'<b style="color:var(--accent-cyan)">{done}</b> / {total}</p>',
                unsafe_allow_html=True,
            )

        try:
            result = generate_report(report_docs, llm, on_chunk_done=on_chunk)
        except Exception as e:
            st.error(f"❌ Report generation failed: {e}")
            st.stop()

        # Step 4 — Done
        render_steps(4)
        prog_bar.progress(1.0)
        time.sleep(0.3)

        step_ph.empty()
        prog_lbl.empty()
        prog_bar.empty()

        # Metrics
        st.markdown('<div class="spacer-xs"></div>', unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("⏱ Time",          f"{result['elapsed']:.1f}s")
        m2.metric("📦 Total Chunks",  result["total_chunks"])
        m3.metric("✅ Chunks Used",   result["used_chunks"])
        m4.metric("🔋 Coverage",      f"{int(result['used_chunks'] / max(result['total_chunks'], 1) * 100)}%")

        if result["truncated"]:
            st.markdown(
                f'<div class="truncation-warning">⚡ Large document: used '
                f'<b>{result["used_chunks"]}</b> of <b>{result["total_chunks"]}</b> chunks '
                f'to stay within Groq free-tier limits.</div>',
                unsafe_allow_html=True,
            )

        # Report output
        st.markdown(f'<div class="report-card fade-in-up">{result["report"]}</div>', unsafe_allow_html=True)
        st.markdown('<div class="spacer-lg"></div>', unsafe_allow_html=True)

        # Download buttons
        d1, d2 = st.columns(2)

        with d1:
            st.download_button(
                "⬇️ Download as Markdown",
                data=result["report"],
                file_name="report.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with d2:
            st.download_button(
                "⬇️ Download as Text",
                data=result["report"],
                file_name="report.txt",
                mime="text/plain",
                use_container_width=True,
            )
