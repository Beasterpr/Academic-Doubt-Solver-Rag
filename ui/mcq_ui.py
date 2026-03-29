import re
import streamlit as st

from core.models import llm_model
from services.mcq_service import generate_mcqs_from_kb, generate_mcqs_from_topic


# ─────────────────────────────────────────────────────────────────────────────
# MCQ TAB  — entry point
# ─────────────────────────────────────────────────────────────────────────────

def render_mcq_tab():
    # Phase router
    phase = st.session_state.get("mcq_phase", "setup")   # setup | quiz | result

    if phase == "setup":
        _render_setup()
    elif phase == "quiz":
        _render_quiz()
    elif phase == "result":
        _render_result()


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 1 — SETUP
# ─────────────────────────────────────────────────────────────────────────────

def _render_setup():
    st.markdown(
        """
        <div style="margin-bottom:24px;">
            <div style="font-size:22px;font-weight:700;color:var(--text-primary);margin-bottom:4px;">
                🧩 MCQ Quiz Generator
            </div>
            <div style="font-size:14px;color:var(--text-secondary);">
                Configure your quiz below, then generate and attempt the questions.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Source mode ──────────────────────────────────────────────────────
    st.markdown('<p style="font-size:13px;font-weight:600;color:var(--text-secondary);margin-bottom:6px;">SOURCE</p>', unsafe_allow_html=True)

    source_mode = st.radio(
        "source_mode",
        ["📚  From Knowledge Base", "💡  From Topic (General Knowledge)"],
        label_visibility="collapsed",
        horizontal=True,
        key="mcq_source_mode",
    )

    kb_mode = source_mode.startswith("📚")

    if kb_mode and not st.session_state.get("kb_ready"):
        st.markdown(
            """
            <div style="display:flex;align-items:center;gap:10px;padding:12px 16px;
            background:rgba(251,191,36,0.08);border:1px solid rgba(251,191,36,0.3);
            border-radius:8px;margin:10px 0;">
                <span style="font-size:16px;">⚠️</span>
                <div>
                    <div style="font-size:13px;font-weight:600;color:#FCD34D;">Knowledge Base not loaded</div>
                    <div style="font-size:12px;color:var(--text-secondary);">Go to the Knowledge Base tab and index documents first, or use General Knowledge mode.</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div style="height:16px;"></div>', unsafe_allow_html=True)

    # ── Config row ───────────────────────────────────────────────────────
    col_topic, col_num, col_diff = st.columns([3, 1, 1], gap="medium")

    with col_topic:
        st.markdown('<p style="font-size:13px;font-weight:600;color:var(--text-secondary);margin-bottom:6px;">TOPIC</p>', unsafe_allow_html=True)
        topic = st.text_input(
            "topic",
            placeholder="e.g. Photosynthesis, Machine Learning, World War II …",
            label_visibility="collapsed",
            key="mcq_topic_input",
        )

    with col_num:
        st.markdown('<p style="font-size:13px;font-weight:600;color:var(--text-secondary);margin-bottom:6px;">QUESTIONS</p>', unsafe_allow_html=True)
        num_q = st.selectbox(
            "num_q",
            [5, 10, 15, 20],
            index=0,
            label_visibility="collapsed",
            key="mcq_num_q",
        )

    with col_diff:
        st.markdown('<p style="font-size:13px;font-weight:600;color:var(--text-secondary);margin-bottom:6px;">DIFFICULTY</p>', unsafe_allow_html=True)
        difficulty = st.selectbox(
            "difficulty",
            ["Easy", "Medium", "Hard", "Mixed"],
            index=3,
            label_visibility="collapsed",
            key="mcq_difficulty",
        )

    st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    # ── Generate button ──────────────────────────────────────────────────
    can_generate = bool(topic.strip()) and (not kb_mode or st.session_state.get("kb_ready"))

    if st.button("⚡  Generate Quiz", use_container_width=True, disabled=not can_generate, key="mcq_generate_btn"):
        with st.spinner(f"Generating {num_q} {difficulty.lower()} questions about **{topic.strip()}** …"):
            try:
                llm = llm_model()
                if kb_mode:
                    raw = generate_mcqs_from_kb(
                        st.session_state.vectordb, llm,
                        topic=topic.strip(), num_questions=num_q, difficulty=difficulty,
                    )
                else:
                    raw = generate_mcqs_from_topic(
                        llm,
                        topic=topic.strip(), num_questions=num_q, difficulty=difficulty,
                    )

                questions = _parse_questions(raw)

                if not questions:
                    st.error("❌ Could not parse questions from the response. Please try again.")
                    return

                # Store quiz state
                st.session_state["mcq_raw"]           = raw
                st.session_state["mcq_questions"]     = questions
                st.session_state["mcq_topic_used"]    = topic.strip()
                st.session_state["mcq_difficulty_used"] = difficulty
                st.session_state["mcq_source_label"]  = "Knowledge Base" if kb_mode else "General Knowledge"
                st.session_state["mcq_answers"]     = {}   # {q_num: selected_letter}
                st.session_state["mcq_phase"]       = "quiz"
                st.rerun()

            except Exception as e:
                st.error(f"❌ Generation failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 2 — QUIZ
# ─────────────────────────────────────────────────────────────────────────────

def _render_quiz():
    questions   = st.session_state.get("mcq_questions", [])
    topic       = st.session_state.get("mcq_topic_used", "")
    difficulty  = st.session_state.get("mcq_difficulty_used", "")
    source_lbl  = st.session_state.get("mcq_source_label", "")
    answers     = st.session_state.get("mcq_answers", {})

    # ── Header ───────────────────────────────────────────────────────────
    h_left, h_right = st.columns([3, 1])
    with h_left:
        st.markdown(
            f"""
            <div style="margin-bottom:4px;">
                <span style="font-size:20px;font-weight:700;color:var(--text-primary);">🧩 {topic}</span>
            </div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px;">
                <span style="font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;
                background:rgba(99,102,241,0.15);color:var(--accent-indigo);">{source_lbl}</span>
                <span style="font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;
                background:rgba(56,189,248,0.12);color:var(--accent-cyan);">{difficulty}</span>
                <span style="font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;
                background:rgba(255,255,255,0.06);color:var(--text-secondary);">{len(questions)} Questions</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with h_right:
        if st.button("↩ New Quiz", use_container_width=True, key="mcq_back_setup"):
            _reset_quiz()
            st.rerun()

    st.divider()

    # ── Questions ─────────────────────────────────────────────────────────
    for q in questions:
        num      = q["num"]
        answered = answers.get(num)

        st.markdown(
            f"""
            <div style="margin-bottom:4px;">
                <span style="font-size:11px;font-weight:700;color:var(--accent-cyan);
                letter-spacing:0.5px;">QUESTION {num}</span>
            </div>
            <div style="font-size:15px;font-weight:600;color:var(--text-primary);
            margin-bottom:12px;line-height:1.5;">{q["question"]}</div>
            """,
            unsafe_allow_html=True,
        )

        letters = [l for l in ["A", "B", "C", "D"] if l in q["options"]]
        col1, col2 = st.columns(2, gap="small")

        for i, letter in enumerate(letters):
            text = q["options"][letter]
            is_selected = answered == letter

            border = "border:1.5px solid var(--accent-indigo);" if is_selected else "border:1px solid var(--border);"
            bg     = "background:rgba(99,102,241,0.18);" if is_selected else "background:rgba(255,255,255,0.03);"
            fw     = "font-weight:600;" if is_selected else ""

            col = col1 if i % 2 == 0 else col2
            with col:
                if st.button(
                    f"{letter})  {text}",
                    key=f"mcq_q{num}_{letter}",
                    use_container_width=True,
                ):
                    st.session_state["mcq_answers"][num] = letter
                    st.rerun()

        st.markdown('<div style="height:20px;"></div>', unsafe_allow_html=True)

    st.divider()

    # ── Progress & Submit ─────────────────────────────────────────────────
    answered_count = len(answers)
    total          = len(questions)
    all_answered   = answered_count == total

    st.markdown(
        f"""
        <div style="display:flex;align-items:center;justify-content:space-between;
        margin-bottom:12px;">
            <span style="font-size:13px;color:var(--text-secondary);">
                {answered_count} of {total} answered
            </span>
            <span style="font-size:13px;color:{'#34D399' if all_answered else 'var(--accent-cyan)'};">
                {"✓ All answered — ready to submit!" if all_answered else f"{total - answered_count} remaining"}
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not all_answered:
        st.progress(answered_count / total)

    if st.button(
        "📊  Submit & See Results",
        use_container_width=True,
        disabled=not all_answered,
        key="mcq_submit_btn",
    ):
        st.session_state["mcq_phase"] = "result"
        st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# PHASE 3 — RESULT
# ─────────────────────────────────────────────────────────────────────────────

def _render_result():
    questions  = st.session_state.get("mcq_questions", [])
    answers    = st.session_state.get("mcq_answers", {})
    topic      = st.session_state.get("mcq_topic_used", "")
    difficulty = st.session_state.get("mcq_difficulty_used", "")
    raw        = st.session_state.get("mcq_raw", "")

    total   = len(questions)
    correct = sum(1 for q in questions if answers.get(q["num"]) == q["answer"])
    wrong   = total - correct
    pct     = int(correct / total * 100) if total else 0

    # ── Score card ────────────────────────────────────────────────────────
    if pct >= 80:
        score_color, grade, emoji = "#34D399", "Excellent", "🏆"
    elif pct >= 60:
        score_color, grade, emoji = "#60A5FA", "Good", "👍"
    elif pct >= 40:
        score_color, grade, emoji = "#FBBF24", "Fair", "📖"
    else:
        score_color, grade, emoji = "#F87171", "Needs Work", "💪"

    st.markdown(
        f"""
        <div style="text-align:center;padding:32px 24px;
        background:rgba(255,255,255,0.03);border:1px solid var(--border);
        border-radius:12px;margin-bottom:28px;">
            <div style="font-size:48px;margin-bottom:8px;">{emoji}</div>
            <div style="font-size:40px;font-weight:800;color:{score_color};margin-bottom:4px;">{pct}%</div>
            <div style="font-size:18px;font-weight:700;color:var(--text-primary);margin-bottom:12px;">{grade}</div>
            <div style="font-size:13px;color:var(--text-secondary);">{topic} · {difficulty}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Metrics row ───────────────────────────────────────────────────────
    m1, m2, m3 = st.columns(3)
    m1.metric("✅ Correct",  correct)
    m2.metric("❌ Incorrect", wrong)
    m3.metric("📋 Total",    total)

    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="font-size:13px;font-weight:600;color:var(--text-secondary);'
        'letter-spacing:0.5px;margin-bottom:12px;">QUESTION REVIEW</p>',
        unsafe_allow_html=True,
    )

    # ── Per-question review ───────────────────────────────────────────────
    for q in questions:
        num        = q["num"]
        user_ans   = answers.get(num, "")
        correct_ans = q["answer"]
        is_correct = user_ans == correct_ans

        status_color = "#34D399" if is_correct else "#F87171"
        status_icon  = "✅" if is_correct else "❌"
        border_color = "rgba(52,211,153,0.3)" if is_correct else "rgba(248,113,113,0.3)"
        bg_color     = "rgba(52,211,153,0.05)" if is_correct else "rgba(248,113,113,0.05)"

        st.markdown(
            f"""
            <div style="border:1px solid {border_color};background:{bg_color};
            border-radius:10px;padding:16px 20px;margin-bottom:12px;">
                <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;">
                    <div style="font-size:15px;font-weight:600;color:var(--text-primary);
                    line-height:1.5;flex:1;">
                        <span style="font-size:11px;font-weight:700;color:var(--accent-cyan);
                        display:block;margin-bottom:4px;">Q{num}</span>
                        {q["question"]}
                    </div>
                    <span style="font-size:20px;flex-shrink:0;">{status_icon}</span>
                </div>
            """,
            unsafe_allow_html=True,
        )

        # Options
        for letter in ["A", "B", "C", "D"]:
            if letter not in q["options"]:
                continue
            text = q["options"][letter]

            if letter == correct_ans:
                opt_style = "color:#34D399;font-weight:700;"
                tag = " ✓"
            elif letter == user_ans and not is_correct:
                opt_style = "color:#F87171;font-weight:600;text-decoration:line-through;"
                tag = " ✗ (your answer)"
            else:
                opt_style = "color:var(--text-secondary);"
                tag = ""

            st.markdown(
                f'<div style="font-size:13px;{opt_style}margin-top:6px;padding-left:4px;">'
                f'{letter}) {text}{tag}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div style="height:24px;"></div>', unsafe_allow_html=True)

    # ── Action buttons ────────────────────────────────────────────────────
    b1, b2 = st.columns(2)
    with b1:
        if st.button("🔁  Retake Same Quiz", use_container_width=True, key="mcq_retake"):
            st.session_state["mcq_answers"] = {}
            st.session_state["mcq_phase"]   = "quiz"
            st.rerun()
    with b2:
        if st.button("➕  New Quiz", use_container_width=True, key="mcq_new"):
            _reset_quiz()
            st.rerun()

    st.markdown('<div style="height:12px;"></div>', unsafe_allow_html=True)

    st.download_button(
        "⬇️  Download Questions as Text",
        data=raw,
        file_name=f"mcqs_{topic.replace(' ', '_')}.txt",
        mime="text/plain",
        use_container_width=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _reset_quiz():
    for key in ["mcq_phase", "mcq_questions", "mcq_raw", "mcq_answers",
                "mcq_topic_used", "mcq_difficulty_used", "mcq_source_label"]:
        st.session_state.pop(key, None)


def _parse_questions(raw: str) -> list[dict]:
    """Parse LLM output into list of {num, question, options, answer} dicts."""
    blocks = re.split(r"\n(?=Q\d+\.)", raw.strip())
    parsed = []

    for block in blocks:
        lines = [l.rstrip() for l in block.strip().splitlines() if l.strip()]
        if not lines:
            continue

        q_match = re.match(r"Q(\d+)\.\s*(.*)", lines[0])
        if not q_match:
            continue

        num      = q_match.group(1)
        question = q_match.group(2).strip()
        options  = {}
        answer   = ""

        for line in lines[1:]:
            opt = re.match(r"^([A-D])\)\s*(.*)", line)
            if opt:
                options[opt.group(1)] = opt.group(2).strip()
                continue
            ans = re.match(r"^Answer:\s*([A-D])", line, re.IGNORECASE)
            if ans:
                answer = ans.group(1).upper()

        if question and len(options) >= 2:
            parsed.append({"num": num, "question": question, "options": options, "answer": answer})

    return parsed
