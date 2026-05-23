import streamlit as st
import pandas as pd
import requests
import socket
import ssl
import time
import plotly.express as px
import plotly.graph_objects as go

from datetime import datetime, timezone
from urllib.parse import urlparse

from db import init_db, insert_record, get_history, get_website_history
from feedback_db import init_feedback_db, insert_bug_report, insert_feature_request


# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="WebDoc - Advanced Network Monitoring",
    page_icon="🌐",
    layout="wide"
)

init_db()
init_feedback_db()


# ---------------- SESSION ----------------
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if 'page' not in st.session_state:
    st.session_state['page'] = 'intro'


# ================================================================
# GLOBAL CSS
# ================================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, .stApp, .stMarkdown, .stButton, .stTextInput, .stSelectbox, [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {
    font-family: 'Inter', sans-serif !important;
}

#MainMenu, footer { visibility: hidden; }
header { background: transparent !important; }
[data-testid="stHeaderActionElements"] { display: none !important; }

/* Sidebar toggle buttons — always visible, clean look */
[data-testid="stSidebarCollapseButton"] button,
button[data-testid="collapsedSidebar"] {
    background: linear-gradient(135deg, #1a1f35, #111827) !important;
    border: 1px solid #2d3a55 !important;
    color: #a78bfa !important;
    border-radius: 50% !important;
    width: 32px !important;
    height: 32px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    box-shadow: 0 2px 12px rgba(124, 58, 237, 0.25), 0 0 0 1px rgba(124,58,237,0.1) !important;
    transition: all 0.2s ease !important;
    font-size: 14px !important;
}
[data-testid="stSidebarCollapseButton"] button:hover,
button[data-testid="collapsedSidebar"]:hover {
    background: linear-gradient(135deg, #7c3aed, #4f46e5) !important;
    border-color: #7c3aed !important;
    color: #ffffff !important;
    box-shadow: 0 4px 20px rgba(124, 58, 237, 0.5) !important;
    transform: scale(1.1) !important;
}
/* Make collapsed sidebar button always visible at screen edge */
button[data-testid="collapsedSidebar"] {
    position: fixed !important;
    left: 12px !important;
    top: 12px !important;
    z-index: 999999 !important;
}

.stApp {
    background-color: #0b0f1a !important;
    color: #e2e8f0 !important;
}

[data-testid="stSidebar"] {
    background: #0d1321 !important;
    border-right: 1px solid #1f2d45 !important;
    min-width: 220px !important;
}

/* Sidebar nav buttons — flat ghost style, NOT purple gradient */
[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #64748b !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 500 !important;
    padding: 0.45rem 0.75rem !important;
    text-align: left !important;
    box-shadow: none !important;
    transition: all 0.18s ease !important;
    font-size: 13px !important;
    justify-content: flex-start !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,255,255,0.05) !important;
    color: #e2e8f0 !important;
    transform: none !important;
    box-shadow: none !important;
    border: none !important;
}
/* Logout button — subtle red tint */
[data-testid="stSidebar"] .stButton > button[kind="secondary"]:last-of-type,
[data-testid="stSidebar"] .stButton:last-child > button {
    color: #94a3b8 !important;
}
[data-testid="stSidebar"] .stButton:last-child > button:hover {
    color: #f87171 !important;
    background: rgba(239,68,68,0.08) !important;
}

.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #6d28d9) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.2rem !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3) !important;
    font-size: 13px !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(124, 58, 237, 0.5) !important;
    background: linear-gradient(135deg, #8b5cf6, #7c3aed) !important;
}

.stTextInput > div > div > input {
    background: #111827 !important;
    border: 1px solid #1f2d45 !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
    font-size: 14px !important;
    padding: 0.6rem 1rem !important;
}
.stTextInput > div > div > input:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 3px rgba(124,58,237,0.2) !important;
}
.stTextInput > label { color: #94a3b8 !important; font-size: 13px !important; }

[data-testid="metric-container"] {
    background: linear-gradient(145deg, #111827, #0f172a) !important;
    border: 1px solid #1f2d45 !important;
    border-radius: 16px !important;
    padding: 1rem !important;
}

.stSelectbox > div > div {
    background: #111827 !important;
    border: 1px solid #1f2d45 !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}
.stSelectbox label { color: #94a3b8 !important; font-size: 13px !important; }

details {
    background: #111827 !important;
    border: 1px solid #1f2d45 !important;
    border-radius: 10px !important;
    color: #e2e8f0 !important;
}
details summary { color: #a78bfa !important; font-size: 13px !important; cursor: pointer; }

.stAlert { border-radius: 10px !important; }

.stSpinner > div { border-top-color: #7c3aed !important; }

::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #0b0f1a; }
::-webkit-scrollbar-thumb { background: #2d3748; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #4a5568; }

hr { border-color: #1f2d45 !important; margin: 1.5rem 0 !important; }

.block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }
</style>
""", unsafe_allow_html=True)


# ================================================================
# HELPERS
# ================================================================
def compose_diagnosis(data: dict) -> str:
    site = data.get("Website", "the site")
    ip = data.get("IP Address", "unknown IP")
    reach = data.get("Reachability Status", "unknown")
    http_status = data.get("HTTP Status", "unknown")
    code = data.get("HTTP Status Code", "?")
    latency = data.get("Avg Response Time (ms)", None)
    dns = data.get("DNS Time (ms)", None)
    ssl_days = data.get("SSL Days Left", None)
    alert = data.get("Alert", "")
    raw = data.get("Raw Diagnosis", "")

    parts = []
    if reach == "DOWN" or ip == "DNS FAILED":
        parts.append(f"We could not reach {site}. {raw}")
    else:
        parts.append(f"{site} ({ip}) is reachable.")
        if http_status == "UP":
            parts.append(f"The HTTP request succeeded with status code {code}.")
        else:
            parts.append(f"The HTTP request returned a warning ({code}). {raw}")
        if latency is not None:
            if latency > 300:
                parts.append(f"Response time is {latency:.0f} ms, which is slower than usual.")
            else:
                parts.append(f"Response time is {latency:.0f} ms, which is fast.")
        if dns is not None:
            parts.append(f"DNS lookup took {dns:.0f} ms.")
        if ssl_days is not None:
            if ssl_days < 0:
                parts.append("SSL certificate could not be verified.")
            elif ssl_days < 30:
                parts.append(f"The SSL certificate expires in {ssl_days} days – consider renewing soon.")
            else:
                parts.append(f"The SSL certificate is valid for another {ssl_days} days.")
        if alert == "NORMAL":
            parts.append("Overall health looks good.")
        elif alert == "ACCEPTABLE":
            parts.append("Overall health is acceptable, but keep an eye on latency.")
        else:
            parts.append("Overall health is critical – please investigate the issues above.")
    return " ".join(parts)


def monitor_website(site_raw):
    """Monitor a website and return a dictionary of metrics."""
    timestamp = datetime.now()
    s = (site_raw or '').strip()
    if not s:
        return None

    if s.startswith('http://') or s.startswith('https://'):
        parsed = urlparse(s)
        hostname = parsed.hostname
        http_urls = [s]
    else:
        hostname = s
        http_urls = [f'https://{hostname}', f'http://{hostname}']

    # DNS
    try:
        dns_start = time.time()
        ip_address = socket.gethostbyname(hostname)
        dns_end = time.time()
        dns_time = (dns_end - dns_start) * 1000
    except Exception:
        ip_address = "DNS FAILED"
        dns_time = 0

    # HTTP
    reachability_status = "DOWN"
    http_status = "DOWN"
    status_code = 0
    avg_time = 0
    packet_loss = 100
    diagnosis = ""
    headers = {"User-Agent": "Mozilla/5.0"}

    for url in http_urls:
        try:
            start = time.time()
            response = requests.get(url, headers=headers, timeout=5)
            end = time.time()
            avg_time = (end - start) * 1000
            status_code = response.status_code
            reachability_status = "UP"
            packet_loss = 0
            if status_code < 400:
                http_status = "UP"
                diagnosis = f"Successfully reached {url} with status code {status_code}."
            elif status_code == 403:
                http_status = "WARNING"
                diagnosis = f"Access to {url} is forbidden (HTTP 403). This often means the server blocks automated requests."
            else:
                http_status = "WARNING"
                diagnosis = f"Received HTTP {status_code} from {url}."
            break
        except Exception as e:
            diagnosis = f"Failed to connect to {url}: {e}"

    # SSL
    try:
        context = ssl.create_default_context()
        with context.wrap_socket(socket.socket(), server_hostname=hostname) as sock:
            sock.settimeout(5)
            sock.connect((hostname, 443))
            cert = sock.getpeercert()
            expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
            ssl_days_left = (
                expiry_date.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)
            ).days
    except Exception:
        ssl_days_left = -1

    # Final Status
    if ip_address == "DNS FAILED":
        final_status = "DNS ISSUE"
        alert = "CRITICAL"
        if not diagnosis:
            diagnosis = "DNS resolution failed – the domain could not be resolved."
    elif reachability_status == "DOWN":
        final_status = "DOWN"
        alert = "CRITICAL"
        if not diagnosis:
            diagnosis = "Website is unreachable via HTTP – no response received."
    else:
        final_status = "UP"
        if avg_time > 300:
            alert = "ACCEPTABLE"
            if not diagnosis:
                diagnosis = "Website responded, but latency is high (>300 ms)."
        else:
            alert = "NORMAL"
            if not diagnosis:
                diagnosis = "Website is reachable and latency is within normal range."

    category = "Fast" if avg_time < 120 else ("Moderate" if avg_time < 300 else "Slow")

    return {
        "Timestamp": timestamp,
        "Website": hostname,
        "IP Address": ip_address,
        "Reachability Status": reachability_status,
        "HTTP Status": http_status,
        "HTTP Status Code": status_code,
        "Final Status": final_status,
        "Avg Response Time (ms)": round(avg_time, 2),
        "Load Time (ms)": round(avg_time, 2),
        "Packet Loss %": packet_loss,
        "DNS Time (ms)": round(dns_time, 2),
        "SSL Days Left": ssl_days_left,
        "Category": category,
        "Alert": alert,
        "Diagnosis": compose_diagnosis({
            "Website": hostname,
            "IP Address": ip_address,
            "Reachability Status": reachability_status,
            "HTTP Status": http_status,
            "HTTP Status Code": status_code,
            "Avg Response Time (ms)": round(avg_time, 2),
            "Packet Loss %": packet_loss,
            "DNS Time (ms)": round(dns_time, 2),
            "SSL Days Left": ssl_days_left,
            "Category": category,
            "Alert": alert,
            "Raw Diagnosis": diagnosis,
        }),
    }


def health_score(data):
    score = 100
    if data.get('Reachability Status') == "DOWN":
        score -= 50
    if data.get('IP Address') == "DNS FAILED":
        score -= 30
    if data.get('Alert') == "CRITICAL":
        score -= 20
    elif data.get('Alert') == "ACCEPTABLE":
        score -= 10
    if data.get('Avg Response Time (ms)', 0) > 500:
        score -= 15
    elif data.get('Avg Response Time (ms)', 0) > 300:
        score -= 5
    if data.get('SSL Days Left', 0) < 0:
        score -= 10
    elif data.get('SSL Days Left', 100) < 30:
        score -= 5
    return max(0, min(100, score))


def status_badge(status):
    colors = {
        "UP":       ("#10b981", "#064e3b"),
        "DOWN":     ("#ef4444", "#450a0a"),
        "WARNING":  ("#f59e0b", "#451a03"),
        "NORMAL":   ("#10b981", "#064e3b"),
        "CRITICAL": ("#ef4444", "#450a0a"),
        "ACCEPTABLE": ("#f59e0b", "#451a03"),
        "DNS ISSUE":  ("#f59e0b", "#451a03"),
        "FAST":     ("#10b981", "#064e3b"),
        "MODERATE": ("#f59e0b", "#451a03"),
        "SLOW":     ("#ef4444", "#450a0a"),
    }
    fg, bg = colors.get(status.upper(), ("#94a3b8", "#1e293b"))
    return (
        f'<span style="background:{bg}; color:{fg}; border:1px solid {fg}55; '
        f'border-radius:20px; padding:3px 10px; font-size:11px; font-weight:700; '
        f'white-space:nowrap;">{status}</span>'
    )


DARK_CHART = dict(
    paper_bgcolor='#111827',
    plot_bgcolor='#111827',
    font_color='#94a3b8',
    margin=dict(l=10, r=10, t=40, b=10),
)
AXIS_STYLE = dict(showgrid=False, color='#4b5563', linecolor='#1f2d45')
GRID_AXIS  = dict(showgrid=True, gridcolor='#1f2d45', color='#4b5563', linecolor='#1f2d45')


# ================================================================
# SIDEBAR
# ================================================================
with st.sidebar:
    st.markdown("""
    <div style="padding:1rem 0.5rem 1.4rem; border-bottom:1px solid #1f2d45; margin-bottom:1rem;">
        <div style="display:flex; align-items:center; gap:10px; margin-bottom:4px;">
            <div style="background:linear-gradient(135deg,#7c3aed,#4f46e5);
                        width:36px; height:36px; border-radius:10px;
                        display:flex; align-items:center; justify-content:center;
                        font-size:18px; box-shadow:0 0 20px rgba(124,58,237,0.4);">🌐</div>
            <span style="font-size:20px; font-weight:800; color:#ffffff;">WebDoc</span>
        </div>
        <span style="font-size:11px; color:#4b5563; padding-left:46px;">Advanced Monitoring</span>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state.get('authenticated') and st.session_state.get('user_email'):
        email = st.session_state['user_email']
        initials = email[0].upper()
        st.markdown(f"""
        <div style="background:#111827; border:1px solid #1f2d45; border-radius:12px;
                    padding:10px 12px; display:flex; align-items:center; gap:10px;
                    margin-bottom:1.4rem;">
            <div style="background:linear-gradient(135deg,#7c3aed,#ec4899); width:32px; height:32px;
                        border-radius:50%; display:flex; align-items:center; justify-content:center;
                        font-weight:700; font-size:14px; color:white; flex-shrink:0;">{initials}</div>
            <div style="min-width:0;">
                <div style="font-size:11px; color:#4b5563;">Logged in as</div>
                <div style="font-size:12px; color:#e2e8f0; font-weight:600;
                            overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{email}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    if st.session_state.get('authenticated'):
        def section_label(text):
            st.markdown(
                f'<div style="font-size:9px; font-weight:800; color:#2d3a55; '
                f'letter-spacing:2px; text-transform:uppercase; padding:0 0.4rem; margin:14px 0 5px;">{text}</div>',
                unsafe_allow_html=True
            )

        current_page = st.session_state.get('page', 'main')

        def nav_btn(label, icon, page_name):
            is_active = current_page == page_name
            if is_active:
                st.markdown(f"""
                <div style="background:rgba(124,58,237,0.15); border-left:3px solid #7c3aed;
                            border-radius:10px; padding:9px 12px; margin-bottom:4px;
                            display:flex; align-items:center; gap:9px;">
                    <span style="font-size:15px; line-height:1;">{icon}</span>
                    <span style="color:#a78bfa; font-weight:700; font-size:13px;">{label}</span>
                </div>
                """, unsafe_allow_html=True)
            else:
                if st.button(f"{icon}  {label}", key=f"nav_{page_name}",
                             use_container_width=True):
                    st.session_state['page'] = page_name
                    st.rerun()

        section_label("GENERAL")
        nav_btn("Overview", "🏠", "main")

        section_label("REPORTS")
        nav_btn("History", "📊", "history")

        section_label("SETTINGS")
        nav_btn("Help & Support", "❓", "help")
        nav_btn("Settings", "⚙️", "settings_page")

        st.markdown('<hr style="border-color:#1f2d45; margin:0.5rem 0;">', unsafe_allow_html=True)
        if st.button("🔓  Log Out", use_container_width=True, key="logout_btn"):
            st.session_state['authenticated'] = False
            st.session_state['page'] = 'intro'
            if 'active_scan_data' in st.session_state:
                del st.session_state['active_scan_data']
            if 'active_site' in st.session_state:
                del st.session_state['active_site']
            st.rerun()

    else:
        st.markdown(
            '<div style="font-size:10px; font-weight:700; color:#374151; '
            'letter-spacing:1.5px; padding:0 0.3rem; margin-bottom:6px;">GENERAL</div>',
            unsafe_allow_html=True
        )
        if st.button("🔑  Login", use_container_width=True, key="nav_login"):
            st.session_state['page'] = 'login'
            st.rerun()


# ================================================================
# PAGE — INTRO
# ================================================================
if st.session_state['page'] == 'intro':

    # Add top padding via CSS for vertical centering feel
    st.markdown("""
    <style>
    .intro-center { text-align: center; }
    </style>
    <div style="height: 4vh;"></div>
    """, unsafe_allow_html=True)

    # Logo orb — centered via columns
    _, logo_col, _ = st.columns([2, 1, 2])
    with logo_col:
        st.markdown("""
        <div style="text-align:center;">
            <div style="width:80px; height:80px;
                        background:linear-gradient(135deg,#7c3aed,#4f46e5);
                        border-radius:24px;
                        display:inline-flex; align-items:center; justify-content:center;
                        font-size:38px;
                        box-shadow:0 0 60px rgba(124,58,237,0.55);">🌐</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:1.2rem;'></div>", unsafe_allow_html=True)

    # Title + subtitle — centered via a wide center column
    _, title_col, _ = st.columns([1, 4, 1])
    with title_col:
        st.markdown("""
        <div style="text-align:center;">
            <h1 style="font-size:3.2rem; font-weight:800; color:#ffffff;
                       margin:0 0 0.4rem; line-height:1.1;">WebDoc</h1>
            <p style="font-size:1.1rem; color:#6366f1; font-weight:600; margin:0 0 0.8rem;">
                AI-Powered Network Monitoring
            </p>
            <p style="color:#4b5563; font-size:0.95rem; line-height:1.8; margin-bottom:1.8rem;">
                Monitor latency, DNS resolution, SSL certificates, packet loss
                and real-time website health — all in one beautiful dashboard.
            </p>
        </div>
        """, unsafe_allow_html=True)

    # Feature pills — centered via a wide center column
    _, pills_col, _ = st.columns([1, 4, 1])
    with pills_col:
        st.markdown("""
        <div style="text-align:center; margin-bottom:2rem;">
            <span style="display:inline-block; background:#111827; border:1px solid #1f2d45;
                         border-radius:20px; padding:6px 14px; font-size:12px;
                         color:#a78bfa; font-weight:500; margin:4px;">⚡ Real-time Latency</span>
            <span style="display:inline-block; background:#111827; border:1px solid #1f2d45;
                         border-radius:20px; padding:6px 14px; font-size:12px;
                         color:#34d399; font-weight:500; margin:4px;">🔒 SSL Monitoring</span>
            <span style="display:inline-block; background:#111827; border:1px solid #1f2d45;
                         border-radius:20px; padding:6px 14px; font-size:12px;
                         color:#60a5fa; font-weight:500; margin:4px;">🧠 AI Diagnosis</span>
            <span style="display:inline-block; background:#111827; border:1px solid #1f2d45;
                         border-radius:20px; padding:6px 14px; font-size:12px;
                         color:#f472b6; font-weight:500; margin:4px;">📊 Trend Analytics</span>
        </div>
        """, unsafe_allow_html=True)

    # CTA button — centered
    _, btn_col, _ = st.columns([2, 1, 2])
    with btn_col:
        if st.button("Get Started →", use_container_width=True, key="btn_intro_get_started"):
            st.session_state['page'] = 'login'
            st.rerun()

    st.markdown("""
    <div style="text-align:center; color:#374151; font-size:12px; margin-top:1rem;">
        Trusted network monitoring for developers &amp; teams
    </div>
    """, unsafe_allow_html=True)

    st.stop()


# ================================================================
# PAGE — LOGIN
# ================================================================
if st.session_state['page'] == 'login':

    c1, c2, c3 = st.columns([1, 1.4, 1])
    with c2:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#111827,#0f172a);
                    border:1px solid #1f2d45; border-radius:22px; padding:2rem 1.8rem 1.5rem;
                    margin-top:4rem; box-shadow:0 12px 40px rgba(0,0,0,0.6);">
            <div style="text-align:center; margin-bottom:1.5rem;">
                <div style="width:58px; height:58px;
                            background:linear-gradient(135deg,#7c3aed,#4f46e5);
                            border-radius:18px; display:flex; align-items:center;
                            justify-content:center; font-size:28px; margin:0 auto 1rem;
                            box-shadow:0 0 30px rgba(124,58,237,0.45);">🌐</div>
                <h2 style="color:#ffffff; font-weight:700; margin:0 0 5px; font-size:1.3rem;">
                    Welcome to WebDoc
                </h2>
                <p style="color:#4b5563; font-size:13px; margin:0;">
                    Enter your email to start monitoring
                </p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        email = st.text_input("Email Address", placeholder="you@example.com",
                              label_visibility="collapsed")

        if st.button("Continue →", use_container_width=True, key="btn_login_continue"):
            if email and "@" in email:
                st.session_state['authenticated'] = True
                st.session_state['user_email'] = email
                st.session_state['page'] = 'main'
                st.rerun()
            else:
                st.error("Please enter a valid email address.")

        st.markdown("""
        <div style="text-align:center; color:#374151; font-size:11px; margin-top:0.8rem;">
            🔒 Your data is stored locally and privately.
        </div>
        """, unsafe_allow_html=True)

    st.stop()


# ================================================================
# PAGE — DOCS
# ================================================================
if st.session_state.get('page') == 'docs':
    if st.button("← Back to Help", key="btn_docs_back"):
        st.session_state['page'] = 'help'
        st.rerun()

    st.markdown("""
    <h1 style="color:#fff; font-weight:800; margin-bottom:4px;">📖 Documentation</h1>
    <p style="color:#4b5563; margin-bottom:2rem;">Everything you need to know about how WebDoc works.</p>
    """, unsafe_allow_html=True)

    def doc_section(icon, title, color, body_html):
        import textwrap
        clean_body = textwrap.dedent(body_html).strip()
        html_content = (
            f"<div style='background:linear-gradient(145deg,#111827,#0f172a); border:1px solid #1f2d45; "
            f"border-left:4px solid {color}; border-radius:16px; padding:1.5rem 1.6rem; margin-bottom:1.2rem; "
            f"box-shadow:0 4px 20px rgba(0,0,0,0.3);'>"
            f"<div style='font-size:16px; font-weight:800; color:{color}; margin-bottom:0.8rem;'>"
            f"{icon} {title}"
            f"</div>"
            f"<div style='color:#94a3b8; font-size:13px; line-height:1.9;'>"
            f"{clean_body}"
            f"</div>"
            f"</div>"
        )
        st.markdown(html_content, unsafe_allow_html=True)

    doc_section("🌐", "What is WebDoc?", "#7c3aed", """
        WebDoc is an <span style='color:#e2e8f0;font-weight:700;'>AI-powered network monitoring tool</span> that lets you
        check the real-time health of any website or domain. It runs a full diagnostic scan covering:
        DNS resolution, HTTP reachability, SSL certificate validity, response latency, and packet loss —
        all within seconds.
    """)

    doc_section("🔍", "How Scanning Works", "#3b82f6", """
        When you enter a domain and click <span style='color:#e2e8f0;font-weight:700;'>⚡ Monitor</span>, WebDoc runs the following pipeline:<br><br>
        <span style='color:#e2e8f0;font-weight:700;'>1. DNS Resolution</span> — Resolves the domain to its IP address using
        <span style='background:#1f2d45;padding:1px 6px;border-radius:4px;color:#a78bfa;'>socket.gethostbyname()</span>.
        Records the DNS lookup time in milliseconds.<br><br>
        <span style='color:#e2e8f0;font-weight:700;'>2. HTTP Request</span> — Attempts an HTTPS connection first, then falls back to HTTP.
        Captures the HTTP status code and response time.<br><br>
        <span style='color:#e2e8f0;font-weight:700;'>3. SSL Certificate Check</span> — Connects to port 443 and reads the certificate expiry date. Reports how many days until expiry.<br><br>
        <span style='color:#e2e8f0;font-weight:700;'>4. Health Score</span> — A 0–100 score computed from all metrics:
        reachability, response speed, SSL status, and packet loss.<br><br>
        <span style='color:#e2e8f0;font-weight:700;'>5. AI Diagnosis</span> — A human-readable summary generated from all the collected
        data, explaining what is working and what needs attention.
    """)

    doc_section("📊", "Metrics Explained", "#10b981", """
        <span style='color:#e2e8f0;font-weight:700;'>Reachability Status</span> — Whether the server responded to any HTTP request (UP / DOWN).<br><br>
        <span style='color:#e2e8f0;font-weight:700;'>HTTP Status Code</span> — The server response code. 200 = OK, 403 = Forbidden, 5xx = Server Error.<br><br>
        <span style='color:#e2e8f0;font-weight:700;'>Response Time (ms)</span> — Time from request sent to first byte received. Under 200ms is fast; over 500ms is slow.<br><br>
        <span style='color:#e2e8f0;font-weight:700;'>DNS Time (ms)</span> — How long it took to resolve the domain name to an IP address.<br><br>
        <span style='color:#e2e8f0;font-weight:700;'>SSL Days Left</span> — Days until the SSL/TLS certificate expires. Under 30 days triggers a warning.<br><br>
        <span style='color:#e2e8f0;font-weight:700;'>Packet Loss %</span> — Percentage of HTTP requests that failed. 0% is healthy; 100% means fully unreachable.<br><br>
        <span style='color:#e2e8f0;font-weight:700;'>Alert Level</span> — NORMAL (everything fine), ACCEPTABLE (minor issues), CRITICAL (site down or major problems).
    """)

    doc_section("🎯", "Health Score Calculation", "#f59e0b", """
        The Health Score (0–100) deducts points for issues found:<br><br>
        &nbsp;&nbsp;• <span style='color:#e2e8f0;font-weight:700;'>Site is DOWN</span> → −50 pts<br>
        &nbsp;&nbsp;• <span style='color:#e2e8f0;font-weight:700;'>DNS FAILED</span> → −30 pts<br>
        &nbsp;&nbsp;• <span style='color:#e2e8f0;font-weight:700;'>CRITICAL alert</span> → −20 pts<br>
        &nbsp;&nbsp;• <span style='color:#e2e8f0;font-weight:700;'>ACCEPTABLE alert</span> → −10 pts<br>
        &nbsp;&nbsp;• <span style='color:#e2e8f0;font-weight:700;'>Response over 500ms</span> → −15 pts<br>
        &nbsp;&nbsp;• <span style='color:#e2e8f0;font-weight:700;'>Response over 300ms</span> → −5 pts<br>
        &nbsp;&nbsp;• <span style='color:#e2e8f0;font-weight:700;'>SSL expired</span> → −10 pts<br>
        &nbsp;&nbsp;• <span style='color:#e2e8f0;font-weight:700;'>SSL under 30 days</span> → −5 pts<br><br>
        A score of <span style='color:#10b981;font-weight:700;'>70–100 = Good</span>,
        <span style='color:#f59e0b;font-weight:700;'>40–69 = Fair</span>,
        <span style='color:#ef4444;font-weight:700;'>0–39 = Critical</span>.
    """)

    doc_section("📋", "History and Analytics", "#ec4899", """
        Every scan is automatically saved to a local SQLite database tied to your login email.
        Visit the <span style='color:#e2e8f0;font-weight:700;'>📊 History</span> page to:<br><br>
        &nbsp;&nbsp;• Browse all past scans with full details<br>
        &nbsp;&nbsp;• Filter by website or alert level<br>
        &nbsp;&nbsp;• View response time trends over time<br>
        &nbsp;&nbsp;• See alert level distribution charts<br>
        &nbsp;&nbsp;• Read AI diagnosis logs for each scan
    """)

    doc_section("🔒", "Privacy and Data Storage", "#64748b", """
        All monitoring data is stored <span style='color:#e2e8f0;font-weight:700;'>securely and privately under your profile</span>.
        No data is shared with external third parties. Your email is used only as a local identifier to
        separate scan histories between different users.
    """)

    st.stop()


# ================================================================
# PAGE — HELP
# ================================================================
if st.session_state.get('page') == 'help':
    st.markdown("""
    <h1 style="color:#fff; font-weight:800; margin-bottom:4px;">❓ Help &amp; Support</h1>
    <p style="color:#4b5563; margin-bottom:1.5rem;">Documentation, bug reports, and support resources.</p>
    """, unsafe_allow_html=True)

    user_email = st.session_state.get('user_email', '')

    # ── Row 1: Documentation + Community ──────────────────────────
    dc1, dc2 = st.columns(2)

    with dc1:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#111827,#0f172a); border:1px solid #1f2d45;
                    border-left:4px solid #3b82f6; border-radius:16px; padding:1.4rem;
                    margin-bottom:1.2rem;">
            <div style="font-size:15px; font-weight:800; color:#3b82f6; margin-bottom:6px;">
                📖 Documentation
            </div>
            <div style="color:#64748b; font-size:13px; line-height:1.7; margin-bottom:1rem;">
                Learn how WebDoc monitors websites — from DNS resolution and SSL checks
                to health scoring and AI diagnosis.
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("📖  Read Documentation", key="btn_help_docs", use_container_width=True):
            st.session_state['page'] = 'docs'
            st.rerun()

    with dc2:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#111827,#0f172a); border:1px solid #1f2d45;
                    border-left:4px solid #8b5cf6; border-radius:16px; padding:1.4rem;
                    margin-bottom:1.2rem;">
            <div style="font-size:15px; font-weight:800; color:#8b5cf6; margin-bottom:6px;">
                💬 Community
            </div>
            <div style="color:#64748b; font-size:13px; line-height:1.7;">
                Join other users in our community forum.
            </div>
            <div style="margin-top:1rem; display:inline-block; background:#1f2d45;
                        border-radius:20px; padding:5px 14px; font-size:12px;
                        color:#8b5cf6; font-weight:700; letter-spacing:0.5px;">
                🚧 Coming Soon
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    # ── Row 2: Bug Report + Feature Request (compact forms) ───────
    fc1, fc2 = st.columns(2)

    with fc1:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#111827,#0f172a); border:1px solid #1f2d45;
                    border-left:4px solid #ef4444; border-radius:16px; padding:1.4rem;
                    margin-bottom:1rem;">
            <div style="font-size:15px; font-weight:800; color:#ef4444; margin-bottom:4px;">
                🐛 Report a Bug
            </div>
            <div style="color:#64748b; font-size:13px; margin-bottom:0.5rem;">
                Found an issue? Help us fix it.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)

        with st.form("form_bug_report", clear_on_submit=True):
            bug_title = st.text_input("Bug Title", placeholder="Short description of the issue", key="bug_title")
            bug_desc  = st.text_area("Description", placeholder="What went wrong? Include steps to reproduce if possible.", height=90, key="bug_desc")
            bug_sev   = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"], key="bug_sev")
            submitted_bug = st.form_submit_button("🐛  Submit Bug Report", use_container_width=True)

        if submitted_bug:
            if bug_title.strip() and bug_desc.strip():
                insert_bug_report(
                    email=user_email, name="",
                    title=bug_title.strip(), description=bug_desc.strip(),
                    steps="", severity=bug_sev
                )
                st.success("✅ Bug report submitted! Thank you.")
            else:
                st.error("Please fill in at least the Bug Title and Description.")

    with fc2:
        st.markdown("""
        <div style="background:linear-gradient(145deg,#111827,#0f172a); border:1px solid #1f2d45;
                    border-left:4px solid #10b981; border-radius:16px; padding:1.4rem;
                    margin-bottom:1rem;">
            <div style="font-size:15px; font-weight:800; color:#10b981; margin-bottom:4px;">
                💡 Feature Request
            </div>
            <div style="color:#64748b; font-size:13px; margin-bottom:0.5rem;">
                Have an idea? We'd love to hear it.
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)

        with st.form("form_feature_request", clear_on_submit=True):
            fr_title = st.text_input("Feature Title", placeholder="One-line summary of your idea", key="fr_title")
            fr_desc  = st.text_area("Description", placeholder="Describe the feature and how you'd use it.", height=90, key="fr_desc")
            fr_pri   = st.selectbox("Priority", ["Nice to have", "Important", "Critical"], key="fr_pri")
            submitted_fr = st.form_submit_button("💡  Submit Feature Request", use_container_width=True)

        if submitted_fr:
            if fr_title.strip() and fr_desc.strip():
                insert_feature_request(
                    email=user_email, name="",
                    title=fr_title.strip(), description=fr_desc.strip(),
                    use_case="", priority=fr_pri
                )
                st.success("✅ Feature request submitted! We'll review it soon.")
            else:
                st.error("Please fill in at least the Feature Title and Description.")

    st.stop()


# ================================================================
# PAGE — SETTINGS
# ================================================================
if st.session_state.get('page') == 'settings_page':
    st.markdown("""
    <h1 style="color:#fff; font-weight:800; margin-bottom:4px;">⚙️ Settings</h1>
    <p style="color:#4b5563; margin-bottom:1.5rem;">Configure your monitoring preferences.</p>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#111827; border:1px solid #1f2d45; border-radius:16px;
                padding:1.5rem; max-width:600px; margin-bottom:1rem;">
        <div style="font-size:14px; font-weight:700; color:#e2e8f0; margin-bottom:4px;
                    border-bottom:1px solid #1f2d45; padding-bottom:10px;">
            🔔 Notification Preferences
        </div>
        <div style="color:#4b5563; font-size:13px; margin-top:10px; line-height:1.6;">
            Coming soon — configure alert thresholds and email notifications.
        </div>
    </div>

    <div style="background:#111827; border:1px solid #1f2d45; border-radius:16px;
                padding:1.5rem; max-width:600px;">
        <div style="font-size:14px; font-weight:700; color:#e2e8f0; margin-bottom:4px;
                    border-bottom:1px solid #1f2d45; padding-bottom:10px;">
            🕐 Scan Interval
        </div>
        <div style="color:#4b5563; font-size:13px; margin-top:10px; line-height:1.6;">
            Coming soon — schedule automatic recurring scans.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ================================================================
# PAGE — HISTORY
# ================================================================
if st.session_state['page'] == 'history':

    hcol1, hcol2 = st.columns([4, 1])
    with hcol1:
        st.markdown("""
        <h1 style="color:#fff; font-weight:800; margin:0;">📊 Monitoring History</h1>
        <p style="color:#4b5563; margin-top:4px; font-size:14px;">Full audit log of all website scans</p>
        """, unsafe_allow_html=True)
    with hcol2:
        if st.button("← Dashboard", key="btn_history_back_dashboard"):
            st.session_state['page'] = 'main'
            st.rerun()

    history_df = get_history(st.session_state['user_email'])

    if history_df.empty:
        st.markdown("""
        <div style="background:#111827; border:1px solid #1f2d45; border-radius:16px;
                    padding:3rem; text-align:center; margin-top:2rem;">
            <div style="font-size:3rem; margin-bottom:1rem;">📭</div>
            <div style="color:#4b5563; font-size:1rem;">
                No monitoring history found. Run your first scan to see results here.
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.stop()

    # Summary chips
    total_scans = len(history_df)
    unique_sites = history_df['website'].nunique() if 'website' in history_df.columns else "–"

    # Last scan relative time
    last_scan_label = "–"
    if 'timestamp' in history_df.columns:
        try:
            last_ts = pd.to_datetime(history_df['timestamp']).max()
            delta = datetime.now() - last_ts.replace(tzinfo=None)
            total_secs = int(delta.total_seconds())
            if total_secs < 60:
                last_scan_label = f"{total_secs}s ago"
            elif total_secs < 3600:
                last_scan_label = f"{total_secs // 60}m ago"
            elif total_secs < 86400:
                last_scan_label = f"{total_secs // 3600}h ago"
            else:
                last_scan_label = f"{total_secs // 86400}d ago"
        except Exception:
            last_scan_label = "–"

    st.markdown(f"""
    <div style="display:flex; gap:10px; margin:1rem 0 1.5rem; flex-wrap:wrap;">
        <span style="background:#111827; border:1px solid #1f2d45; border-radius:20px;
                     padding:5px 14px; font-size:12px; color:#a78bfa; font-weight:600;">
            📋 Total Scans: {total_scans}
        </span>
        <span style="background:#111827; border:1px solid #1f2d45; border-radius:20px;
                     padding:5px 14px; font-size:12px; color:#34d399; font-weight:600;">
            🌐 Unique Sites: {unique_sites}
        </span>
        <span style="background:#111827; border:1px solid #1f2d45; border-radius:20px;
                     padding:5px 14px; font-size:12px; color:#60a5fa; font-weight:600;">
            🕐 Last Scan: {last_scan_label}
        </span>
    </div>
    """, unsafe_allow_html=True)


    # Filters
    fc1, fc2 = st.columns(2)
    with fc1:
        if 'website' in history_df.columns:
            sites = ["All Sites"] + sorted(history_df['website'].dropna().unique().tolist())
            site_filter = st.selectbox("Filter by Website", sites)
        else:
            site_filter = "All Sites"
    with fc2:
        alert_filter = st.selectbox("Filter by Alert Level",
                                    ["All Levels", "NORMAL", "ACCEPTABLE", "CRITICAL"])

    filtered_df = history_df.copy()
    if site_filter != "All Sites" and 'website' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['website'] == site_filter]
    if alert_filter != "All Levels" and 'alert' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['alert'] == alert_filter]

    # Reset pagination offsets if filters change
    if 'last_site_filter' not in st.session_state or st.session_state['last_site_filter'] != site_filter:
        st.session_state['last_site_filter'] = site_filter
        st.session_state['history_log_offset'] = 0
        st.session_state['history_diag_offset'] = 0

    if 'last_alert_filter' not in st.session_state or st.session_state['last_alert_filter'] != alert_filter:
        st.session_state['last_alert_filter'] = alert_filter
        st.session_state['history_log_offset'] = 0
        st.session_state['history_diag_offset'] = 0

    # Mini analytics
    if len(history_df) > 1:
        st.markdown("""
        <div style="margin:1.5rem 0 0.5rem;">
            <span style="color:#e2e8f0; font-weight:700; font-size:15px;">📈 Quick Analytics</span>
        </div>
        """, unsafe_allow_html=True)

        ac1, ac2 = st.columns(2)

        with ac1:
            if 'avg_response' in history_df.columns and 'timestamp' in history_df.columns:
                hdf_sorted = history_df.sort_values('timestamp')
                fig_mini = go.Figure()
                fig_mini.add_trace(go.Scatter(
                    x=hdf_sorted['timestamp'], y=hdf_sorted['avg_response'],
                    mode='lines', line=dict(color='#7c3aed', width=2),
                    fill='tozeroy', fillcolor='rgba(124,58,237,0.12)',
                ))
                fig_mini.update_layout(
                    **DARK_CHART, height=220,
                    title=dict(text='Response Time Over Time',
                               font=dict(color='#94a3b8', size=12)),
                    showlegend=False,
                    xaxis=AXIS_STYLE, yaxis=GRID_AXIS,
                )
                st.markdown('<div style="background:#111827; border:1px solid #1f2d45; border-radius:14px; overflow:hidden;">', unsafe_allow_html=True)
                st.plotly_chart(fig_mini, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

        with ac2:
            if 'alert' in history_df.columns:
                alert_counts = history_df['alert'].value_counts().reset_index()
                alert_counts.columns = ['alert', 'count']
                cmap = {'NORMAL': '#10b981', 'ACCEPTABLE': '#f59e0b', 'CRITICAL': '#ef4444'}
                fig_bar = px.bar(alert_counts, x='alert', y='count',
                                 color='alert', color_discrete_map=cmap)
                fig_bar.update_layout(
                    **DARK_CHART, height=220,
                    title=dict(text='Alert Level Distribution',
                               font=dict(color='#94a3b8', size=12)),
                    showlegend=False, bargap=0.35,
                    xaxis=AXIS_STYLE, yaxis=GRID_AXIS,
                )
                st.markdown('<div style="background:#111827; border:1px solid #1f2d45; border-radius:14px; overflow:hidden;">', unsafe_allow_html=True)
                st.plotly_chart(fig_bar, use_container_width=True)
                st.markdown('</div>', unsafe_allow_html=True)

    # Styled scan log table
    st.markdown("""
    <div style="margin:1.5rem 0 0.5rem;">
        <span style="color:#e2e8f0; font-weight:700; font-size:15px;">📋 Scan Log</span>
    </div>
    """, unsafe_allow_html=True)

    if not filtered_df.empty:
        col_map = {
            'timestamp':   'Timestamp',
            'website':     'Website',
            'ip_address':  'IP Address',
            'avg_response':'Response (ms)',
            'dns_time':    'DNS (ms)',
            'ssl_days':    'SSL Days',
            'final_status':'Status',
            'alert':       'Alert',
        }
        display_cols = [c for c in col_map if c in filtered_df.columns]

        badge_cols = {'alert', 'final_status'}
        headers_html = "".join(
            f"<th style='padding:10px 16px; text-align:left; color:#4b5563; "
            f"font-size:11px; font-weight:700; letter-spacing:1px; text-transform:uppercase;'>"
            f"{col_map[c]}</th>"
            for c in display_cols
        )

        # Initialize pagination offset for log
        if 'history_log_offset' not in st.session_state:
            st.session_state['history_log_offset'] = 0
        
        log_offset = st.session_state['history_log_offset']
        visible_log_df = filtered_df.iloc[log_offset : log_offset + 5]

        rows_html = ""
        for _, row in visible_log_df.iterrows():
            cells = ""
            for col in display_cols:
                val = str(row[col])
                if col in badge_cols:
                    cells += f"<td style='padding:10px 16px;'>{status_badge(val)}</td>"
                else:
                    cells += (
                        f"<td style='padding:10px 16px; color:#94a3b8; "
                        f"font-size:13px; white-space:nowrap;'>{val}</td>"
                    )
            rows_html += f"<tr style='border-bottom:1px solid #1f2d45;'>{cells}</tr>"

        st.markdown(f"""
        <div style="background:#111827; border:1px solid #1f2d45; border-radius:16px;
                    overflow-x:auto; margin-bottom:1.5rem;">
            <table style="width:100%; border-collapse:collapse; min-width:600px;">
                <thead style="background:#0d1321; border-bottom:1px solid #1f2d45;">
                    <tr>{headers_html}</tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)

        if len(filtered_df) > 5:
            lpcol1, lpcol2 = st.columns(2)
            with lpcol1:
                if log_offset > 0:
                    if st.button("⬅️ Previous 5 Logs", key="btn_prev_history_log"):
                        st.session_state['history_log_offset'] = max(0, log_offset - 5)
                        st.rerun()
            with lpcol2:
                if log_offset + 5 < len(filtered_df):
                    if st.button("Next 5 Logs ➡️", key="btn_next_history_log"):
                        st.session_state['history_log_offset'] = log_offset + 5
                        st.rerun()

        # Expandable diagnosis log
        if 'diagnosis' in filtered_df.columns:
            st.markdown("""
            <div style="margin:1.5rem 0 0.5rem;">
                <span style="color:#e2e8f0; font-weight:700; font-size:15px;">🧠 Diagnosis Log</span>
            </div>
            """, unsafe_allow_html=True)

            # Initialize pagination offset for diagnosis log
            if 'history_diag_offset' not in st.session_state:
                st.session_state['history_diag_offset'] = 0
            
            diag_offset = st.session_state['history_diag_offset']
            visible_diag_df = filtered_df.iloc[diag_offset : diag_offset + 5]

            for _, row in visible_diag_df.iterrows():
                label = f"{row.get('website','?')} — {row.get('timestamp','?')}"
                with st.expander(f"🔍 {label}"):
                    st.markdown(
                        f"<div style='color:#94a3b8; font-size:13px; line-height:1.7;'>"
                        f"{row.get('diagnosis','No diagnosis available.')}</div>",
                        unsafe_allow_html=True
                    )

            if len(filtered_df) > 5:
                dpcol1, dpcol2 = st.columns(2)
                with dpcol1:
                    if diag_offset > 0:
                        if st.button("⬅️ Previous 5 Diagnoses", key="btn_prev_history_diag"):
                            st.session_state['history_diag_offset'] = max(0, diag_offset - 5)
                            st.rerun()
                with dpcol2:
                    if diag_offset + 5 < len(filtered_df):
                        if st.button("Next 5 Diagnoses ➡️", key="btn_next_history_diag"):
                            st.session_state['history_diag_offset'] = diag_offset + 5
                            st.rerun()
    else:
        st.markdown("""
        <div style="background:#111827; border:1px solid #1f2d45; border-radius:12px;
                    padding:1.5rem; color:#4b5563; font-size:13px; text-align:center;">
            No records match your filter criteria.
        </div>
        """, unsafe_allow_html=True)

    st.stop()


# ================================================================
# PAGE — MAIN DASHBOARD
# ================================================================
st.markdown("""
<div style="margin-bottom:1.5rem;">
    <h1 style="color:#ffffff; font-weight:800; font-size:1.8rem; margin:0;">
        🌐 Live Network Monitoring
    </h1>
    <p style="color:#4b5563; margin-top:4px; font-size:14px;">Real-time website health analytics</p>
</div>
""", unsafe_allow_html=True)

# Search bar
s_col1, s_col2 = st.columns([5, 1])
with s_col1:
    site = st.text_input(
        "Website", label_visibility="collapsed",
        placeholder="🔍  Enter a domain like google.com or https://example.com"
    )
with s_col2:
    monitor = st.button("⚡ Monitor", use_container_width=True, key="btn_dashboard_monitor")


# ================================================================
# MONITOR ACTION
# ================================================================
if monitor and site:
    with st.spinner("🔍 Scanning website…"):
        data = monitor_website(site)

    if data is None:
        st.error("Please enter a valid website.")
        st.stop()

    st.session_state['active_site'] = data['Website']
    st.session_state['active_scan_data'] = data
    st.session_state['overview_diag_offset'] = 0
    insert_record(st.session_state['user_email'], data)
    st.rerun()

if 'active_scan_data' not in st.session_state:
    st.stop()

data = st.session_state['active_scan_data']
site = st.session_state['active_site']
score = health_score(data)

# Banner
alert_palette = {
    "NORMAL":     ("#10b981", "#064e3b"),
    "ACCEPTABLE": ("#f59e0b", "#451a03"),
    "CRITICAL":   ("#ef4444", "#450a0a"),
}
a_fg, a_bg = alert_palette.get(data['Alert'], ("#94a3b8", "#1e293b"))
st.markdown(f"""
<div style="background:{a_bg}; border:1px solid {a_fg}55; border-radius:12px;
            padding:12px 18px; margin:1rem 0; display:flex; align-items:center; gap:10px;">
    <span style="font-size:18px;">✅</span>
    <span style="color:{a_fg}; font-weight:600; font-size:14px;">
        Scan complete for <strong>{data['Website']}</strong> — Alert: {data['Alert']}
    </span>
</div>
""", unsafe_allow_html=True)

# ── METRIC CARDS + GAUGE ──────────────────────────────────────
st.markdown("""
<div style="margin:1.2rem 0 0.6rem;">
    <span style="color:#e2e8f0; font-weight:700; font-size:15px;">Current Status</span>
</div>
""", unsafe_allow_html=True)

main_col, gauge_col = st.columns([3, 1])

with main_col:
    ssl_val  = str(data['SSL Days Left']) if data['SSL Days Left'] >= 0 else "N/A"
    ssl_col  = "#ec4899" if data['SSL Days Left'] < 30 else "#34d399"
    ssl_bg   = "#3b0764" if data['SSL Days Left'] < 30 else "#064e3b"

    card_data = [
        ("🟢", "#10b981", "#064e3b", "Reachability",    data['Reachability Status']),
        ("🔵", "#3b82f6", "#1e3a5f", "HTTP Status",     f"{data['HTTP Status']} ({data['HTTP Status Code']})"),
        ("🟣", "#8b5cf6", "#2e1065", "Response Time",   f"{data['Avg Response Time (ms)']} ms"),
        ("🟠", "#f59e0b", "#451a03", "Packet Loss",     f"{data['Packet Loss %']}%"),
        ("🔒", ssl_col,   ssl_bg,    "SSL Days Left",   ssl_val),
    ]
    cols5 = st.columns(5)
    for col, (icon, color, bg, label, value) in zip(cols5, card_data):
        with col:
            st.markdown(f"""
            <div style="background:linear-gradient(145deg,#111827,#0f172a);
                        border:1px solid #1f2d45; border-radius:16px; padding:1rem;
                        height:100%; box-shadow:0 4px 16px rgba(0,0,0,0.3);">
                <div style="width:36px; height:36px; background:{bg};
                            border:1px solid {color}44; border-radius:10px;
                            display:flex; align-items:center; justify-content:center;
                            font-size:18px; margin-bottom:0.7rem;">{icon}</div>
                <div style="font-size:1rem; font-weight:800; color:{color};
                            word-break:break-word;">{value}</div>
                <div style="font-size:11px; color:#4b5563; margin-top:3px;
                            font-weight:500;">{label}</div>
            </div>
            """, unsafe_allow_html=True)

with gauge_col:
    g_color = "#10b981" if score >= 70 else ("#f59e0b" if score >= 40 else "#ef4444")
    g_label = "Good" if score >= 70 else ("Fair" if score >= 40 else "Critical")
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={'text': "Health Score", 'font': {'color': '#64748b', 'size': 12, 'family': 'Inter'}},
        number={'font': {'color': '#ffffff', 'size': 30, 'family': 'Inter'}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': '#374151',
                     'tickfont': {'color': '#374151', 'size': 9}},
            'bar': {'color': g_color, 'thickness': 0.28},
            'bgcolor': '#0d1321',
            'bordercolor': '#1f2d45',
            'steps': [
                {'range': [0,  40], 'color': '#1f0909'},
                {'range': [40, 70], 'color': '#1c1200'},
                {'range': [70, 100],'color': '#021f10'},
            ],
        }
    ))
    fig_gauge.add_annotation(
        text=g_label, x=0.5, y=0.22, showarrow=False,
        font=dict(color=g_color, size=12, family='Inter'), xanchor='center'
    )
    fig_gauge.update_layout(
        paper_bgcolor='#111827', font_color='#94a3b8',
        height=210, margin=dict(l=10, r=10, t=35, b=5),
    )
    st.markdown('<div style="background:#111827; border:1px solid #1f2d45; border-radius:16px; overflow:hidden;">', unsafe_allow_html=True)
    st.plotly_chart(fig_gauge, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ── TREND ANALYTICS ──────────────────────────────────────────
st.markdown('<hr>', unsafe_allow_html=True)
st.markdown(f"""
<div style="margin-bottom:0.6rem;">
    <span style="color:#e2e8f0; font-weight:700; font-size:15px;">📈 Trend Analytics — {site}</span>
</div>
""", unsafe_allow_html=True)

history_df = get_website_history(st.session_state['user_email'], site)

if len(history_df) > 1:
    history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])

    chart_c1, chart_c2 = st.columns(2)

    with chart_c1:
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=history_df['timestamp'], y=history_df['avg_response'],
            mode='lines', line=dict(color='#7c3aed', width=2.5),
            fill='tozeroy', fillcolor='rgba(124,58,237,0.14)',
        ))
        fig1.update_layout(
            **DARK_CHART, height=260,
            title=dict(text='Response Time (ms)',
                       font=dict(color='#94a3b8', size=13, family='Inter')),
            showlegend=False,
            xaxis=AXIS_STYLE, yaxis=GRID_AXIS,
        )
        st.markdown('<div style="background:#111827; border:1px solid #1f2d45; border-radius:16px; overflow:hidden;">', unsafe_allow_html=True)
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with chart_c2:
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=history_df['timestamp'], y=history_df['dns_time'],
            marker_color='#3b82f6', marker_line_width=0,
        ))
        fig3.update_layout(
            **DARK_CHART, height=260,
            title=dict(text='DNS Lookup Time (ms)',
                       font=dict(color='#94a3b8', size=13, family='Inter')),
            showlegend=False, bargap=0.3,
            xaxis=AXIS_STYLE, yaxis=GRID_AXIS,
        )
        st.markdown('<div style="background:#111827; border:1px solid #1f2d45; border-radius:16px; overflow:hidden;">', unsafe_allow_html=True)
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Donut + Diagnosis history
    donut_col, diag_col = st.columns([1, 2])

    with donut_col:
        if 'final_status' in history_df.columns:
            sc = history_df['final_status'].value_counts()
            d_colors = {'UP': '#10b981', 'DOWN': '#ef4444',
                        'DNS ISSUE': '#f59e0b', 'WARNING': '#f59e0b'}
            fig_donut = go.Figure(go.Pie(
                labels=sc.index.tolist(), values=sc.values.tolist(),
                hole=0.62,
                marker_colors=[d_colors.get(s, '#6b7280') for s in sc.index],
                textinfo='none',
            ))
            fig_donut.add_annotation(
                text=f"<b>{len(history_df)}</b><br><span>Total</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(color='#ffffff', size=15, family='Inter'), xanchor='center'
            )
            fig_donut.update_layout(
                **DARK_CHART, height=260,
                title=dict(text='Status Distribution',
                           font=dict(color='#94a3b8', size=13, family='Inter')),
                legend=dict(font=dict(color='#64748b', size=11), bgcolor='rgba(0,0,0,0)'),
            )
            st.markdown('<div style="background:#111827; border:1px solid #1f2d45; border-radius:16px; overflow:hidden;">', unsafe_allow_html=True)
            st.plotly_chart(fig_donut, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

    with diag_col:
        st.markdown("""
        <div style="margin-bottom:0.5rem;">
            <span style="color:#e2e8f0; font-weight:700; font-size:13px;">🧠 Diagnosis History</span>
        </div>
        """, unsafe_allow_html=True)
        if 'diagnosis' in history_df.columns:
            # Sort descending (latest first) for display
            diag_df = history_df.sort_values(by='timestamp', ascending=False)
            
            # Initialize offset state
            if 'overview_diag_offset' not in st.session_state:
                st.session_state['overview_diag_offset'] = 0
            
            offset = st.session_state['overview_diag_offset']
            visible_df = diag_df.iloc[offset : offset + 5]
            
            for _, row in visible_df.iterrows():
                ts  = str(row.get('timestamp', '?'))[:19]
                web = row.get('website', '?')
                with st.expander(f"{ts} — {web}"):
                    st.markdown(
                        f"<div style='color:#94a3b8; font-size:13px; line-height:1.7;'>"
                        f"{row.get('diagnosis', '')}</div>",
                        unsafe_allow_html=True
                    )
            
            # Pagination controls
            if len(diag_df) > 5:
                pcol1, pcol2 = st.columns(2)
                with pcol1:
                    if offset > 0:
                        if st.button("⬅️ Previous 5", key="btn_prev_overview_diag"):
                            st.session_state['overview_diag_offset'] = max(0, offset - 5)
                            st.rerun()
                with pcol2:
                    if offset + 5 < len(diag_df):
                        if st.button("Next 5 ➡️", key="btn_next_overview_diag"):
                            st.session_state['overview_diag_offset'] = offset + 5
                            st.rerun()
else:
    st.markdown("""
    <div style="background:#111827; border:1px solid #1f2d45; border-radius:12px;
                padding:1.5rem; color:#4b5563; font-size:13px; margin:1rem 0;">
        📊 This is the first scan for this website.
        Run more scans to see trend graphs and status distribution.
    </div>
    """, unsafe_allow_html=True)

# ── AI DIAGNOSIS CARD ─────────────────────────────────────────
st.markdown('<hr>', unsafe_allow_html=True)
st.markdown(f"""
<div style="background:linear-gradient(145deg,#111827,#0f172a);
            border:1px solid #1f2d45; border-left:4px solid {a_fg};
            border-radius:16px; padding:1.5rem; margin-bottom:1.5rem;
            box-shadow:0 4px 20px rgba(0,0,0,0.3);">
    <div style="display:flex; align-items:center; justify-content:space-between;
                margin-bottom:0.8rem; flex-wrap:wrap; gap:8px;">
        <span style="color:#e2e8f0; font-weight:700; font-size:15px;">🧠 AI Diagnosis</span>
        {status_badge(data['Alert'])}
    </div>
    <p style="color:#94a3b8; line-height:1.9; font-size:14px; margin:0;">
        {data['Diagnosis']}
    </p>
</div>
""", unsafe_allow_html=True)

# ── DETAILED REPORT TABLE ─────────────────────────────────────
st.markdown("""
<div style="margin-bottom:0.6rem;">
    <span style="color:#e2e8f0; font-weight:700; font-size:15px;">📋 Detailed Report</span>
</div>
""", unsafe_allow_html=True)

report_rows = [
    ("Timestamp",    str(data['Timestamp'])[:19]),
    ("Website",      data['Website']),
    ("IP Address",   data['IP Address']),
    ("Response",     f"{data['Avg Response Time (ms)']} ms"),
    ("DNS Time",     f"{data['DNS Time (ms)']} ms"),
    ("SSL Days",     ssl_val),
    ("Packet Loss",  f"{data['Packet Loss %']}%"),
    ("Category",     data['Category']),
    ("Final Status", data['Final Status']),
    ("Alert",        data['Alert']),
]

badge_labels = {"Final Status", "Alert"}
rows_html = ""
for label, value in report_rows:
    if label in badge_labels:
        val_html = status_badge(str(value))
    else:
        val_html = f"<span style='color:#94a3b8; font-size:13px;'>{value}</span>"
    rows_html += (
        f'<tr style="border-bottom:1px solid #1f2d45;">'
        f'<td style="padding:10px 18px; color:#4b5563; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; white-space:nowrap; width:160px;">{label}</td>'
        f'<td style="padding:10px 18px;">{val_html}</td>'
        f'</tr>'
    )

table_html = (
    f'<div style="background:#111827; border:1px solid #1f2d45; border-radius:16px; overflow:hidden; margin-bottom:2rem;">'
    f'<table style="width:100%; border-collapse:collapse;">'
    f'<thead style="background:#0d1321; border-bottom:1px solid #1f2d45;">'
    f'<tr>'
    f'<th style="padding:10px 18px; text-align:left; color:#4b5563; font-size:11px; font-weight:700; letter-spacing:1px; text-transform:uppercase;">Metric</th>'
    f'<th style="padding:10px 18px; text-align:left; color:#4b5563; font-size:11px; font-weight:700; letter-spacing:1px; text-transform:uppercase;">Value</th>'
    f'</tr>'
    f'</thead>'
    f'<tbody>{rows_html}</tbody>'
    f'</table>'
    f'</div>'
)
st.markdown(table_html, unsafe_allow_html=True)
