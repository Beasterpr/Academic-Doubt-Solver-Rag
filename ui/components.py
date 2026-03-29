# UI COMPONENTS
# Pure HTML render helpers — no Streamlit state or logic here.


def render_status_indicator(active=True):
    """Render knowledge base status indicator."""
    if active:
        return '''
        <div class="status-indicator">
            <span class="status-dot status-dot-active"></span>
            <span class="status-text status-text-active">Active</span>
        </div>
        '''
    else:
        return '''
        <div class="status-indicator-simple">
            <span class="status-dot status-dot-inactive"></span>
            <span class="status-text status-text-inactive">No source loaded</span>
        </div>
        '''


def render_page_hero(title, subtitle):
    """Render page hero section."""
    return f'''
    <div class="page-hero">
        <div class="page-hero-title">{title}</div>
        <div class="page-hero-sub">{subtitle}</div>
    </div>
    '''


def render_kb_stats_grid(pages, chunks, pdfs, status):
    """Render knowledge base statistics grid."""
    stats = [
        ("Pages",  pages,  "var(--accent-cyan)"),
        ("Chunks", chunks, "var(--accent-indigo)"),
        ("PDFs",   pdfs,   "#34D399"),
        ("Status", status, "#FCD34D"),
    ]

    cells = "".join(
        f'<div class="kb-stat-cell">'
        f'<div class="kb-stat-value" style="color:{color};">{value}</div>'
        f'<div class="kb-stat-label">{label}</div>'
        f'</div>'
        for label, value, color in stats
    )

    return f'<div class="kb-stats-grid">{cells}</div>'


def render_empty_state(icon, title, text):
    """Render empty state component."""
    return f'''
    <div class="empty-state">
        <div class="empty-state-icon">{icon}</div>
        <div class="empty-state-title">{title}</div>
        <div class="empty-state-text">{text}</div>
    </div>
    '''


def render_info_box(title, content):
    """Render info box component."""
    return f'''
    <div class="info-box">
        <div class="info-box-title">{title}</div>
        <div class="info-box-content">{content}</div>
    </div>
    '''


def render_warning_box(message, details):
    """Render warning box component."""
    return f'''
    <div class="warning-box">
        <span class="warning-icon">⚠️</span>
        <div>
            <div class="warning-title">{message}</div>
            <div class="warning-text">{details}</div>
        </div>
    </div>
    '''


def render_report_steps(steps):
    """Render report generation steps."""
    cards = "".join(
        f'<div class="report-step-card">'
        f'<div class="report-step-number">{number}</div>'
        f'<div>'
        f'<div class="report-step-title">{title}</div>'
        f'<div class="report-step-desc">{desc}</div>'
        f'</div></div>'
        for number, title, desc in steps
    )

    return f'''
    <div class="steps-container">
        <div class="steps-list">{cards}</div>
    </div>
    '''


def render_chat_user_message(content, timestamp):
    """Render user chat message."""
    return f'''
    <div class="chat-user-msg">
        <div>
            <div class="chat-user-bubble">{content}</div>
            <div class="msg-time">{timestamp}</div>
        </div>
    </div>
    '''


def render_chat_ai_message(content, timestamp, sources=None, web_mode=False):
    """Render AI chat message with optional sources."""
    sources_html = ""

    if sources:
        items = "".join(
            f'<div class="source-item">'
            f'<span>{"🔗" if s.startswith("http") else "📄"}</span>'
            f'<span>{s}</span>'
            f'</div>'
            for s in sources
        )
        sources_html = (
            f'<div class="source-section">'
            f'<div class="source-section-title">Sources</div>'
            f'{items}'
            f'</div>'
        )

    web_hdr = '<div class="web-result-header">Web Search Result</div>' if web_mode else ""

    return f'''
    <div class="chat-ai-msg">
        <div class="chat-ai-avatar">🎓</div>
        <div>
            <div class="chat-ai-bubble">
                {web_hdr}{content}{sources_html}
            </div>
            <div class="msg-time-left">{timestamp}</div>
        </div>
    </div>
    '''


def render_chat_empty(icon, title, subtitle):
    """Render empty chat state."""
    return f'''
    <div class="chat-empty">
        <div class="chat-empty-icon">{icon}</div>
        <div class="chat-empty-title">{title}</div>
        <div class="chat-empty-sub">{subtitle}</div>
    </div>
    '''
