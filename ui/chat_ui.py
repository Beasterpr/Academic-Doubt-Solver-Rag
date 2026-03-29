import os
import time

import streamlit as st

from core.models import llm_model
from chains.rag_chain import build_rag_chain
from services.web_service import run_web_search
from ui.components import (
    render_page_hero,
    render_warning_box,
    render_chat_user_message,
    render_chat_ai_message,
    render_chat_empty,
)


# CHAT TAB

def render_chat_tab():

    top_l, top_r = st.columns([2, 1])

    with top_l:
        st.markdown(
            render_page_hero(
                "Chat",
                "Ask questions from indexed documents (RAG) or search the web in real-time (WEB)."
            ),
            unsafe_allow_html=True,
        )

    with top_r:
        mode = st.radio("Mode", ["RAG", "WEB"], horizontal=True, key="chat_mode_radio")

    if mode == "RAG":
        st.markdown('<span class="chat-mode-pill mode-rag">🧠 RAG — Document Q&amp;A</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="chat-mode-pill mode-web">🌐 WEB — Live Search</span>', unsafe_allow_html=True)

    if mode == "RAG" and not st.session_state.kb_ready:
        st.markdown(
            render_warning_box(
                "No Knowledge Base",
                "Go to the Knowledge Base tab and index documents first."
            ),
            unsafe_allow_html=True,
        )

    history = st.session_state.chat_rag if mode == "RAG" else st.session_state.chat_web

    chat_box = st.container(height=520, border=False)

    with chat_box:
        if not history:
            if mode == "RAG":
                st.markdown(
                    render_chat_empty(
                        "🧠",
                        "Ready to Answer",
                        "Ask anything about your indexed documents. I'll search through them and cite my sources."
                    ),
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    render_chat_empty(
                        "🌐",
                        "Live Web Search",
                        "Ask any question — I'll route it to Wikipedia, Arxiv, or DuckDuckGo automatically."
                    ),
                    unsafe_allow_html=True,
                )
        else:
            for msg in history:
                ts = msg.get("ts", "")

                if msg["role"] == "user":
                    st.markdown(
                        render_chat_user_message(msg["content"], ts),
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        render_chat_ai_message(
                            msg["content"],
                            ts,
                            sources=msg.get("sources"),
                            web_mode=msg.get("web_mode", False),
                        ),
                        unsafe_allow_html=True,
                    )

    query = st.chat_input("Ask a question…" if mode == "RAG" else "Search the web…")

    if query:
        ts = time.strftime("%H:%M")
        history.append({"role": "user", "content": query, "ts": ts})

        llm = llm_model()

        if mode == "RAG":
            if not st.session_state.kb_ready:
                history.append({
                    "role": "assistant",
                    "content": "⚠️ No knowledge base. Please index documents first.",
                    "ts": ts,
                })
            else:
                with st.spinner("Searching knowledge base…"):
                    chain = build_rag_chain(st.session_state.vectordb, llm)
                    response = chain.invoke({"input": query})
                    answer = response["answer"]

                    sources = []
                    if "i cannot find the answer in the provided document" not in answer.lower():
                        seen = set()
                        for doc in response["context"]:
                            src = doc.metadata.get("source", "Unknown")
                            if src.startswith("http"):
                                key = src
                            else:
                                key = f"{os.path.basename(src)} — Page {doc.metadata.get('page', 0) + 1}"
                            if key not in seen:
                                seen.add(key)
                                sources.append(key)

                    history.append({
                        "role": "assistant",
                        "content": answer,
                        "sources": sources,
                        "ts": ts,
                    })
        else:
            with st.spinner("Searching the web…"):
                answer = run_web_search(query, llm)

                history.append({
                    "role": "assistant",
                    "content": answer,
                    "web_mode": True,
                    "ts": ts,
                })

        if mode == "RAG":
            st.session_state.chat_rag = history
        else:
            st.session_state.chat_web = history

        st.rerun()
