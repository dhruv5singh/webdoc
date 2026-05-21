import streamlit as st
import pandas as pd
import requests
import socket
import ssl
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Network Monitoring Dashboard",
    layout="wide"
)

# Premium dark theme and custom styled elements
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
    
    /* App-wide reset */
    .stApp {
        background-color: #0b0f19 !important;
        color: #e2e8f0 !important;
    }
    
    /* Custom premium header */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 20px 24px;
        background: linear-gradient(135deg, #111625 0%, #0d121f 100%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
    }
    .header-left {
        display: flex;
        align-items: center;
        gap: 20px;
    }
    .sphere-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        width: 64px;
        height: 64px;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%);
        border-radius: 50%;
    }
    .rotating-sphere {
        animation: spin-sphere 25s linear infinite;
        filter: drop-shadow(0 0 10px rgba(59, 130, 246, 0.5));
    }
    @keyframes spin-sphere {
        from { transform: rotate(0deg); }
        to { transform: rotate(360deg); }
    }
    .dashboard-title {
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 800;
        font-size: 26px;
        color: #ffffff;
        letter-spacing: 0.5px;
        margin: 0;
        text-transform: uppercase;
    }
    .dashboard-subtitle {
        font-family: 'Inter', sans-serif;
        color: #8f9cae;
        font-size: 14px;
        margin: 4px 0 0 0;
    }
    .header-right {
        display: flex;
        align-items: center;
        gap: 16px;
    }
    .avatar-wrapper {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        overflow: hidden;
        border: 2px solid rgba(255, 255, 255, 0.15);
    }
    .avatar-wrapper img {
        width: 100%;
        height: 100%;
        object-fit: cover;
    }
    .settings-gear {
        color: #8f9cae;
        cursor: pointer;
        transition: color 0.2s ease, transform 0.2s ease;
    }
    .settings-gear:hover {
        color: #ffffff;
        transform: rotate(45deg);
    }

    /* Cohesive Input Form Container */
    .form-box {
        background-color: #111625;
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 24px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }
    
    /* Styled Input labels & descriptions */
    .form-label {
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        font-size: 14px;
        color: #8f9cae;
        margin-bottom: 8px;
    }

    /* Custom metric card system */
    .metric-container {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin-bottom: 28px;
        width: 100%;
    }
    .metric-card {
        background: linear-gradient(135deg, #121826 0%, #0d121f 100%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 22px;
        position: relative;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.35);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        overflow: hidden;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(59, 130, 246, 0.4);
        box-shadow: 0 12px 30px rgba(59, 130, 246, 0.15);
    }
    .metric-card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
    }
    .metric-icon-wrap {
        color: #8f9cae;
        display: flex;
        align-items: center;
        justify-content: center;
        background: rgba(255, 255, 255, 0.03);
        padding: 8px;
        border-radius: 10px;
    }
    .metric-badge-wrap {
        display: flex;
        align-items: center;
    }
    .metric-title {
        font-size: 11px;
        color: #8f9cae;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 8px;
        font-weight: 700;
        font-family: 'Outfit', sans-serif;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 800;
        color: #ffffff;
        font-family: 'Outfit', 'Inter', sans-serif;
        display: flex;
        align-items: baseline;
        gap: 6px;
    }
    .metric-subpill {
        font-size: 11px;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.08);
        color: #a0aec0;
        font-family: 'Inter', sans-serif;
    }
    .status-up {
        color: #10b981 !important; /* Emerald green */
    }
    .status-down {
        color: #f43f5e !important; /* Rose red */
    }
    .status-warning {
        color: #3b82f6 !important; /* Blue */
    }
    .status-ssl {
        color: #a78bfa !important; /* Lavender purple */
    }
    .status-info {
        color: #3b82f6 !important; /* Blue */
    }
    .diagnosis-box {
        background: linear-gradient(135deg, #111625 0%, #0d121f 100%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-left: 4px solid #3b82f6;
        padding: 20px;
        border-radius: 4px 16px 16px 4px;
        margin-top: 24px;
        margin-bottom: 24px;
        font-size: 15px;
        color: #e2e8f0;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
        font-family: 'Inter', sans-serif;
    }
    
    /* Clean alert bar styling */
    .alert-box {
        border: 1px solid #10b981;
        background: rgba(16, 185, 129, 0.06);
        color: #10b981;
        padding: 12px 18px;
        border-radius: 8px;
        margin-bottom: 24px;
        font-family: 'Inter', sans-serif;
        font-size: 14px;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Overwrite Streamlit widgets with deep dark style */
    div[data-baseweb="input"] {
        background-color: #161c2d !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="input"] input {
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
    }
    
    /* Premium Button Styling */
    div.stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 700 !important;
        font-family: 'Outfit', sans-serif !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
        transition: all 0.2s ease !important;
        text-transform: uppercase !important;
        font-size: 14px !important;
        margin-top: 14px !important;
    }
    div.stButton > button:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 16px rgba(59, 130, 246, 0.45) !important;
    }

    /* Modern tables styling */
    .report-section {
        background: linear-gradient(135deg, #121826 0%, #0d121f 100%);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 10px 25px rgba(0, 0, 0, 0.35);
        margin-top: 24px;
        margin-bottom: 24px;
    }
    
    .report-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        flex-wrap: wrap;
        gap: 16px;
    }
    
    .report-header h3 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        font-size: 18px;
        letter-spacing: 0.5px;
        color: #ffffff;
        text-transform: uppercase;
        margin: 0;
    }
    
    .table-controls {
        display: flex;
        gap: 12px;
        align-items: center;
    }

    .toolbar-icon-btn {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 8px;
        width: 36px;
        height: 36px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #8f9cae;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .toolbar-icon-btn:hover {
        background: rgba(59, 130, 246, 0.15);
        color: #ffffff;
        border-color: rgba(59, 130, 246, 0.4);
    }
    
    .table-wrap {
        width: 100%;
        overflow-x: auto;
        border-radius: 8px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .report-table {
        width: 100%;
        border-collapse: collapse;
        background-color: rgba(17, 22, 37, 0.6);
        color: #e2e8f0;
        font-size: 13px;
        font-family: 'Inter', sans-serif;
    }
    
    .report-table th {
        background-color: rgba(22, 28, 45, 0.9);
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        color: #8f9cae;
        text-transform: uppercase;
        font-size: 11px;
        letter-spacing: 0.8px;
        padding: 14px 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        text-align: left;
        white-space: nowrap;
    }
    
    .report-table td {
        padding: 14px 16px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        vertical-align: middle;
        white-space: nowrap;
    }
    
    .report-table tbody tr:hover {
        background-color: rgba(255, 255, 255, 0.02);
    }
    
    /* Table Badges rendering style */
    .tag-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
    }
    
    .tag-badge-up {
        background-color: rgba(16, 185, 129, 0.1);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    
    .tag-badge-down {
        background-color: rgba(244, 63, 94, 0.1);
        color: #f43f5e;
        border: 1px solid rgba(244, 63, 94, 0.2);
    }
    
    .tag-badge-warn {
        background-color: rgba(251, 146, 60, 0.1);
        color: #fb923c;
        border: 1px solid rgba(251, 146, 60, 0.2);
    }
    
    .tag-badge-ssl {
        background-color: rgba(167, 139, 250, 0.1);
        color: #a78bfa;
        border: 1px solid rgba(167, 139, 250, 0.2);
    }
    
    /* Circle progress indicator */
    .progress-ring-wrap {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        position: relative;
        width: 32px;
        height: 32px;
    }
    
    .progress-ring-text {
        position: absolute;
        font-size: 9px;
        font-weight: 800;
        color: #ffffff;
        font-family: 'Outfit', sans-serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Custom Premium Header
st.markdown(
    """
    <div class="header-container">
        <div class="header-left">
            <div class="sphere-wrapper">
                <svg class="rotating-sphere" width="50" height="50" viewBox="0 0 100 100">
                    <circle cx="50" cy="50" r="45" fill="none" stroke="rgba(59, 130, 246, 0.2)" stroke-width="1.2" />
                    <circle cx="50" cy="50" r="35" fill="none" stroke="rgba(59, 130, 246, 0.15)" stroke-width="0.8" />
                    <!-- Coordinates curves -->
                    <ellipse cx="50" cy="50" rx="45" ry="15" fill="none" stroke="rgba(59, 130, 246, 0.4)" stroke-width="1.2" />
                    <ellipse cx="50" cy="50" rx="15" ry="45" fill="none" stroke="rgba(59, 130, 246, 0.4)" stroke-width="1.2" />
                    <ellipse cx="50" cy="50" rx="45" ry="30" fill="none" stroke="rgba(59, 130, 246, 0.25)" stroke-width="0.8" />
                    <ellipse cx="50" cy="50" rx="30" ry="45" fill="none" stroke="rgba(59, 130, 246, 0.25)" stroke-width="0.8" />
                    <!-- Network nodes -->
                    <circle cx="50" cy="5" r="3.5" fill="#60a5fa" />
                    <circle cx="50" cy="95" r="3.5" fill="#60a5fa" />
                    <circle cx="5" cy="50" r="3.5" fill="#60a5fa" />
                    <circle cx="95" cy="50" r="3.5" fill="#60a5fa" />
                    <circle cx="18" cy="18" r="3" fill="#93c5fd" />
                    <circle cx="82" cy="18" r="3" fill="#93c5fd" />
                    <circle cx="18" cy="82" r="3" fill="#93c5fd" />
                    <circle cx="82" cy="82" r="3" fill="#93c5fd" />
                    <circle cx="50" cy="50" r="4.5" fill="#3b82f6" />
                    <!-- Connectors -->
                    <line x1="50" y1="5" x2="18" y2="18" stroke="rgba(96, 165, 250, 0.35)" stroke-width="0.8" />
                    <line x1="50" y1="5" x2="82" y2="18" stroke="rgba(96, 165, 250, 0.35)" stroke-width="0.8" />
                    <line x1="5" y1="50" x2="18" y2="18" stroke="rgba(96, 165, 250, 0.35)" stroke-width="0.8" />
                    <line x1="5" y1="50" x2="18" y2="82" stroke="rgba(96, 165, 250, 0.35)" stroke-width="0.8" />
                    <line x1="95" y1="50" x2="82" y2="18" stroke="rgba(96, 165, 250, 0.35)" stroke-width="0.8" />
                    <line x1="95" y1="50" x2="82" y2="82" stroke="rgba(96, 165, 250, 0.35)" stroke-width="0.8" />
                    <line x1="50" y1="95" x2="18" y2="82" stroke="rgba(96, 165, 250, 0.35)" stroke-width="0.8" />
                    <line x1="50" y1="95" x2="82" y2="82" stroke="rgba(96, 165, 250, 0.35)" stroke-width="0.8" />
                    <line x1="50" y1="50" x2="50" y2="5" stroke="rgba(96, 165, 250, 0.25)" stroke-width="0.6" />
                    <line x1="50" y1="50" x2="50" y2="95" stroke="rgba(96, 165, 250, 0.25)" stroke-width="0.6" />
                </svg>
            </div>
            <div>
                <h1 class="dashboard-title">LIVE NETWORK MONITORING</h1>
                <p class="dashboard-subtitle">Real-time health insights for your websites.</p>
            </div>
        </div>
        
    </div>
    """,
    unsafe_allow_html=True
)

# ---------------- INPUT FORM ----------------

col1, col2, col3 = st.columns([3.5, 1.2, 1.3])

with col1:
    st.markdown('<div class="form-label">Website to monitor</div>', unsafe_allow_html=True)
    site = st.text_input(
        "Website to monitor",
        placeholder="example: google.com or https://google.com",
        label_visibility="collapsed"
    )

with col2:
    st.markdown('<div class="form-label" style="margin-bottom: 22px;">&nbsp;</div>', unsafe_allow_html=True)
    fast_mode = st.toggle("Fast Mode", value=True)

with col3:
    st.markdown('<div style="height: 4px;"></div>', unsafe_allow_html=True)
    # The button st.button takes full container width to match "MONITOR NOW" block
    monitor_clicked = st.button("MONITOR NOW", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

def monitor_website(site_raw, fast_mode=True):
    timestamp = datetime.now()

    # normalize input: accept full URLs or bare hostnames
    s = (site_raw or '').strip()
    if not s:
        return None
    if s.startswith('http://') or s.startswith('https://'):
        parsed = urlparse(s)
        hostname = parsed.hostname
        path = parsed.path or ''
        if parsed.query:
            path += '?' + parsed.query
        http_urls = [s.rstrip('/')]
        website_display = s.rstrip('/')
    else:
        parsed = urlparse('//' + s)
        hostname = parsed.hostname or s
        path = parsed.path or ''
        if parsed.query:
            path += '?' + parsed.query
        http_urls = [f'https://{hostname}{path}', f'http://{hostname}{path}']
        website_display = hostname

    site = hostname

    # ---------------- DNS CHECK ----------------

    try:
        dns_start = time.time()
        ip_address = socket.gethostbyname(site)
        dns_end = time.time()
        dns_time = (dns_end - dns_start) * 1000
    except Exception:
        ip_address = "DNS FAILED"
        dns_time = 0

    # ---------------- HTTP REACHABILITY & LATENCY ----------------
    reachability_status = "DOWN"
    avg_time = 0
    packet_loss = 100
    status_code = 0
    http_status = "DOWN"
    load_time = 0
    diagnosis = ""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }
    http_timeout = 3 if fast_mode else 10

    # Run HTTP checks only if DNS succeeded
    if ip_address != "DNS FAILED":
        for url_try in http_urls:
            try:
                start = time.time()
                response = requests.get(url_try, headers=headers, timeout=http_timeout, allow_redirects=True)
                end = time.time()
                avg_time = (end - start) * 1000
                load_time = avg_time
                status_code = response.status_code
                
                # If we get a response, the website is reachable
                reachability_status = "UP"
                packet_loss = 0
                
                if 200 <= status_code < 400:
                    http_status = "UP"
                else:
                    http_status = "Acceptable"
                
                website_display = response.url
                break
            except Exception as e:
                diagnosis = f"HTTP request failed: {e}"
                continue

    if reachability_status == "DOWN":
        diagnosis = "Website unreachable via HTTP."

    # ---------------- SSL CHECK ----------------

    try:
        context = ssl.create_default_context()
        with context.wrap_socket(
            socket.socket(),
            server_hostname=site
        ) as s:
            s.settimeout(5)
            s.connect((site, 443))
            cert = s.getpeercert()
            expiry_date = datetime.strptime(
                cert['notAfter'],
                '%b %d %H:%M:%S %Y %Z'
            )
            ssl_days_left = (expiry_date.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).days
    except Exception:
        ssl_days_left = -1

    # ---------------- FINAL STATUS & DIAGNOSIS ----------------
    if ip_address == "DNS FAILED":
        final_status = "DNS ISSUE"
        diagnosis = "DNS resolution failed."
        alert = "CRITICAL"
    elif reachability_status == "DOWN":
        final_status = "DOWN"
        diagnosis = "Website unreachable via HTTP."
        alert = "CRITICAL"
    else:
        final_status = "UP"
        if ssl_days_left != -1 and ssl_days_left < 7:
            alert = "SSL EXPIRING"
            diagnosis = "SSL certificate nearing expiry."
        elif avg_time > 300:
            alert = "Acceptable"
            diagnosis = "Website reachable but high latency detected."
        else:
            alert = "NORMAL"
            diagnosis = "Application reachable and healthy."

    # ---------------- CATEGORY ----------------
    if avg_time == 0:
        category = "N/A"
        perf_pill = "DOWN"
    elif avg_time < 120:
        category = "Fast"
        perf_pill = "Fast"
    elif avg_time < 280:
        category = "Moderate"
        perf_pill = "Acceptable"
    else:
        category = "Slow"
        perf_pill = "Slow"

    # ---------------- RETURN DATA ----------------

    return {
        "Timestamp": timestamp,
        "Website": website_display,
        "IP Address": ip_address,
        "Reachability Status": reachability_status,
        "HTTP Status": http_status,
        "HTTP Status Code": status_code,
        "Final Status": final_status,
        "Avg Response Time (ms)": round(avg_time, 2),
        "Load Time (ms)": round(load_time, 2),
        "Packet Loss %": round(packet_loss, 2),
        "DNS Time (ms)": round(dns_time, 2),
        "SSL Days Left": ssl_days_left,
        "Category": category,
        "Alert": alert,
        "Diagnosis": diagnosis
    }


# ---------------- METRICS AND TRIGGER ----------------

if monitor_clicked:
    if site:
        with st.spinner("Monitoring website..."):
            data = monitor_website(site, fast_mode)

        if data:
            df = pd.DataFrame([data])

            # Beautiful Custom Green Alert Box
            st.markdown(
                """
                <div class="alert-box">
                    <svg width="20" height="20" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                    </svg>
                    <span>Scan completed. Results are current.</span>
                </div>
                """,
                unsafe_allow_html=True
            )

            # Determine colors and badges for HTML cards
            # 1. Reachability
            if data["Reachability Status"] == "UP":
                reach_class = "status-up"
                reach_badge = """<svg width="18" height="18" fill="none" stroke="#10b981" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4"></path><circle cx="12" cy="12" r="10" stroke="#10b981" stroke-width="2"></circle></svg>"""
            else:
                reach_class = "status-down"
                reach_badge = """<svg width="18" height="18" fill="none" stroke="#f43f5e" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>"""

            # 2. Response Time Performance badge
            resp_time = data["Avg Response Time (ms)"]
            if resp_time == 0:
                perf_pill = "DOWN"
                resp_badge = """<svg width="18" height="18" fill="none" stroke="#f43f5e" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>"""
            elif resp_time < 120:
                perf_pill = "Performance"
                resp_badge = """<svg width="18" height="18" fill="none" stroke="#10b981" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4"></path><circle cx="12" cy="12" r="10" stroke="#10b981" stroke-width="2"></circle></svg>"""
            elif resp_time < 280:
                perf_pill = "Moderate"
                resp_badge = """<svg width="18" height="18" fill="none" stroke="#fb923c" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01"></path><circle cx="12" cy="12" r="10" stroke="#fb923c" stroke-width="2"></circle></svg>"""
            else:
                perf_pill = "Slow"
                resp_badge = """<svg width="18" height="18" fill="none" stroke="#f43f5e" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01"></path><circle cx="12" cy="12" r="10" stroke="#f43f5e" stroke-width="2"></circle></svg>"""

            # 3. HTTP Status
            if data["HTTP Status"] == "UP":
                http_class = "status-up"
                http_val = f'UP'
                http_sub = f'{data["HTTP Status Code"]}'
                http_badge = """<svg width="18" height="18" fill="none" stroke="#10b981" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4"></path><circle cx="12" cy="12" r="10" stroke="#10b981" stroke-width="2"></circle></svg>"""
            elif data["HTTP Status"] == "WARNING":
                http_class = "status-warning"
                http_val = f'WARN'
                http_sub = f'{data["HTTP Status Code"]}'
                http_badge = """<svg width="18" height="18" fill="none" stroke="#fb923c" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01"></path><circle cx="12" cy="12" r="10" stroke="#fb923c" stroke-width="2"></circle></svg>"""
            else:
                http_class = "status-down"
                http_val = "DOWN"
                http_sub = "ERR"
                http_badge = """<svg width="18" height="18" fill="none" stroke="#f43f5e" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>"""

            # 4. Alert Level
            if data["Alert"] == "NORMAL":
                alert_class = "status-up"
                alert_badge = """<svg width="18" height="18" fill="none" stroke="#10b981" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4"></path><circle cx="12" cy="12" r="10" stroke="#10b981" stroke-width="2"></circle></svg>"""
            elif data["Alert"] == "WARNING":
                alert_class = "status-warning"
                alert_badge = """<svg width="18" height="18" fill="none" stroke="#fb923c" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01"></path><circle cx="12" cy="12" r="10" stroke="#fb923c" stroke-width="2"></circle></svg>"""
            elif data["Alert"] == "SSL EXPIRING":
                alert_class = "status-ssl"
                alert_badge = """<svg width="18" height="18" fill="none" stroke="#a78bfa" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01"></path><circle cx="12" cy="12" r="10" stroke="#a78bfa" stroke-width="2"></circle></svg>"""
            else:
                alert_class = "status-down"
                alert_badge = """<svg width="18" height="18" fill="none" stroke="#f43f5e" stroke-width="3.2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>"""

            # 5. SSL Days Left
            ssl_days = data["SSL Days Left"]
            ssl_val = f'{ssl_days} days' if ssl_days >= 0 else "N/A"
            if ssl_days >= 30:
                ssl_class = "status-ssl"
                ssl_badge = """<svg width="18" height="18" fill="none" stroke="#a78bfa" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4"></path><circle cx="12" cy="12" r="10" stroke="#a78bfa" stroke-width="2"></circle></svg>"""
            elif ssl_days >= 0:
                ssl_class = "status-warning"
                ssl_badge = """<svg width="18" height="18" fill="none" stroke="#fb923c" stroke-width="3" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01"></path><circle cx="12" cy="12" r="10" stroke="#fb923c" stroke-width="2"></circle></svg>"""
            else:
                ssl_class = "status-down"
                ssl_badge = """<svg width="18" height="18" fill="none" stroke="#f43f5e" stroke-width="3.2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"></path></svg>"""

            # Render Cohesive Premium Metric Cards Grid
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-card">
                        <div class="metric-card-header">
                            <div class="metric-icon-wrap">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M5 12.55a11 11 0 0 1 14.08 0M1.42 9a16 16 0 0 1 21.16 0M8.53 16.11a6 6 0 0 1 6.95 0M12 20h.01" stroke-linecap="round" stroke-linejoin="round"/></svg>
                            </div>
                            <div class="metric-badge-wrap">{reach_badge}</div>
                        </div>
                        <div class="metric-title">REACHABILITY</div>
                        <div class="metric-value {reach_class}">{data["Reachability Status"]}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-card-header">
                            <div class="metric-icon-wrap">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke-linecap="round" stroke-linejoin="round"/></svg>
                            </div>
                            <div class="metric-badge-wrap">{http_badge}</div>
                        </div>
                        <div class="metric-title">HTTP STATUS</div>
                        <div class="metric-value {http_class}">
                            {http_val}
                            <span class="metric-subpill">{http_sub}</span>
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-card-header">
                            <div class="metric-icon-wrap">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2a10 10 0 0 0-10 10 10 10 0 0 0 13.29 9.5M12 6V12l4 2M22 12A10 10 0 0 0 12 2m0 20v-2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="12" cy="12" r="1"/></svg>
                            </div>
                            <div class="metric-badge-wrap">{resp_badge}</div>
                        </div>
                        <div class="metric-title">AVG RESPONSE</div>
                        <div class="metric-value">
                            {data["Avg Response Time (ms)"]}<span style="font-size:16px;color:#8f9cae;font-weight:500;">ms</span>
                            <span class="metric-subpill">{perf_pill}</span>
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-card-header">
                            <div class="metric-icon-wrap">
                                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" stroke-linecap="round" stroke-linejoin="round"/></svg>
                            </div>
                            <div class="metric-badge-wrap">{alert_badge}</div>
                        </div>
                        <div class="metric-title">ALERT STATUS</div>
                        <div class="metric-value {alert_class}">{data["Alert"]}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # ---------------- TABLE ----------------
            # Format row data fields nicely for the custom premium table
            timestamp_str = data["Timestamp"].strftime("%Y-%m-%d %H:%M:%S")
            website_str = data["Website"]
            ip_str = data["IP Address"]
            
            # Reachability Status tag
            reach_status = data["Reachability Status"]
            if reach_status == "UP":
                reach_badge_html = '<span class="tag-badge tag-badge-up">UP</span>'
            else:
                reach_badge_html = f'<span class="tag-badge tag-badge-down">{reach_status}</span>'
                
            # HTTP Status tag
            http_status_val = data["HTTP Status"]
            if http_status_val == "UP":
                http_badge_html = '<span class="tag-badge tag-badge-up">UP</span>'
            elif http_status_val == "WARNING":
                http_badge_html = '<span class="tag-badge tag-badge-warn">WARN</span>'
            else:
                http_badge_html = f'<span class="tag-badge tag-badge-down">{http_status_val}</span>'
                
            # HTTP Status Code
            status_code_val = data["HTTP Status Code"]
            status_code_str = str(status_code_val) if status_code_val != 0 else "N/A"
            
            # Final Status tag
            final_status_val = data["Final Status"]
            if final_status_val == "UP":
                final_badge_html = '<span class="tag-badge tag-badge-up">UP</span>'
            elif final_status_val == "DNS ISSUE" or final_status_val == "DOWN":
                final_badge_html = f'<span class="tag-badge tag-badge-down">{final_status_val}</span>'
            else:
                final_badge_html = f'<span class="tag-badge tag-badge-warn">{final_status_val}</span>'
                
            # Avg Response Time
            avg_resp_val = data["Avg Response Time (ms)"]
            avg_resp_str = f"{avg_resp_val:.1f} ms" if avg_resp_val > 0 else "0 ms"
            
            # Load Time
            load_time_val = data["Load Time (ms)"]
            load_time_str = f"{load_time_val:.1f} ms" if load_time_val > 0 else "0 ms"
            
            # Packet Loss circular progress ring SVG
            loss_val = data["Packet Loss %"]
            stroke_color = "#f43f5e" if loss_val > 0 else "#10b981"
            packet_loss_html = f"""
            <div class="progress-ring-wrap">
              <svg width="32" height="32" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.915" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="3"></circle>
                <circle cx="18" cy="18" r="15.915" fill="none" stroke="{stroke_color}" stroke-width="3.2" stroke-dasharray="{loss_val}, 100" stroke-dashoffset="0" stroke-linecap="round"></circle>
              </svg>
              <span class="progress-ring-text">{int(loss_val)}%</span>
            </div>
            """
            
            # DNS Time
            dns_time_val = data["DNS Time (ms)"]
            dns_time_str = f"{dns_time_val:.1f} ms" if dns_time_val > 0 else "0 ms"
            
            # SSL Days Left
            ssl_days_val = data["SSL Days Left"]
            if ssl_days_val == -1:
                ssl_days_html = '<span style="color:#f43f5e;font-weight:700;">Expired/NA</span>'
            elif ssl_days_val < 10:
                ssl_days_html = f'<span style="color:#f43f5e;font-weight:700;">{ssl_days_val} days</span>'
            elif ssl_days_val < 30:
                ssl_days_html = f'<span style="color:#fb923c;font-weight:600;">{ssl_days_val} days</span>'
            else:
                ssl_days_html = f'<span style="color:#a78bfa;font-weight:500;">{ssl_days_val} days</span>'

            # Table HTML
            table_html = f"""
            <div class="report-section">
                <div class="report-header">
                    <h3>Detailed Report</h3>
                    <div class="table-controls">
                        <!-- Search Icon -->
                        <div class="toolbar-icon-btn" title="Search">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>
                            </svg>
                        </div>
                        <!-- Refresh Icon -->
                        <div class="toolbar-icon-btn" title="Refresh">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"></path>
                            </svg>
                        </div>
                        <!-- Options Icon -->
                        <div class="toolbar-icon-btn" title="More Options">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                                <circle cx="12" cy="12" r="1"></circle><circle cx="12" cy="5" r="1"></circle><circle cx="12" cy="19" r="1"></circle>
                            </svg>
                        </div>
                    </div>
                </div>
                <div class="table-wrap">
                    <table class="report-table">
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Website</th>
                                <th>IP Address</th>
                                <th>Reachability Status</th>
                                <th>HTTP Status</th>
                                <th>HTTP Status Code</th>
                                <th>Final Status</th>
                                <th>Avg Response Time</th>
                                <th>Load Time</th>
                                <th>Packet Loss %</th>
                                <th>DNS Time</th>
                                <th>SSL Days Left</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>{timestamp_str}</td>
                                <td><span style="color:#ffffff;font-weight:500;">{website_str}</span></td>
                                <td>{ip_str}</td>
                                <td>{reach_badge_html}</td>
                                <td>{http_badge_html}</td>
                                <td><span style="font-weight:600;color:#ffffff;">{status_code_str}</span></td>
                                <td>{final_badge_html}</td>
                                <td>{avg_resp_str}</td>
                                <td>{load_time_str}</td>
                                <td>{packet_loss_html}</td>
                                <td>{dns_time_str}</td>
                                <td>{ssl_days_html}</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
            """
            st.markdown(table_html, unsafe_allow_html=True)
            
            # Custom styled Diagnosis Box
            st.markdown(
                f"""
                <div class="diagnosis-box">
                    <strong style="color:#ffffff;font-family:\'Outfit\',sans-serif;font-size:15px;letter-spacing:0.5px;">DIAGNOSIS:</strong> {data['Diagnosis']}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.warning("Please enter a website name.")
