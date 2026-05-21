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
    /* Premium dark dashboard containers */
    .dashboard-title {
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 800;
        color: #ffffff;
        margin-bottom: 4px;
    }
    .dashboard-subtitle {
        color: #9aa6b2;
        margin-bottom: 24px;
        font-size: 16px;
    }
    /* Custom metric card system */
    .metric-container {
        display: flex;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 24px;
        flex-wrap: wrap;
        width: 100%;
    }
    .metric-card {
        background: linear-gradient(135deg, #141822 0%, #0e111a 100%);
        border: 1px solid #1f2638;
        border-radius: 12px;
        padding: 20px;
        flex: 1;
        min-width: 200px;
        box-shadow: 0 8px 16px rgba(0, 0, 0, 0.4);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #3b82f6;
    }
    .metric-title {
        font-size: 13px;
        color: #8a929e;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 8px;
        font-weight: 700;
    }
    .metric-value {
        font-size: 26px;
        font-weight: 800;
        color: #ffffff;
        font-family: 'Outfit', 'Inter', sans-serif;
    }
    .status-up {
        color: #10b981 !important; /* Emerald green */
    }
    .status-down {
        color: #ef4444 !important; /* Rose red */
    }
    .status-warning {
        color: #f59e0b !important; /* Amber yellow */
    }
    .status-ssl {
        color: #a78bfa !important; /* Lavender purple */
    }
    .status-info {
        color: #3b82f6 !important; /* Blue */
    }
    .diagnosis-box {
        background-color: #0e111a;
        border-left: 4px solid #3b82f6;
        padding: 16px;
        border-radius: 4px 12px 12px 4px;
        margin-top: 16px;
        margin-bottom: 24px;
        font-size: 15px;
        color: #e6eef6;
        border: 1px solid #1f2638;
        border-left: 4px solid #3b82f6;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown('<h1 class="dashboard-title">🌐 Live Network Monitoring Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="dashboard-subtitle">Monitor website health, latency, DNS, SSL, and HTTP status in real time without OS-level raw ping requirements.</p>', unsafe_allow_html=True)

# ---------------- INPUT ----------------

site = st.text_input(
    "Enter Website",
    placeholder="example: google.com or https://google.com"
)

fast_mode = st.checkbox("Fast Mode", value=True)

# ---------------- MONITOR FUNCTION ----------------


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
                    http_status = "WARNING"
                
                website_display = response.url
                break
            except Exception as e:
                diagnosis = f"HTTP request failed: {e}"
                continue

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
            alert = "WARNING"
            diagnosis = "Website reachable but high latency detected."
        else:
            alert = "NORMAL"
            diagnosis = "Application reachable and healthy."

    # ---------------- CATEGORY ----------------
    if avg_time == 0:
        category = "N/A"
    elif avg_time < 100:
        category = "Fast"
    elif avg_time < 250:
        category = "Moderate"
    else:
        category = "Slow"

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


# ---------------- BUTTON ----------------

if st.button("Monitor Website"):
    if site:
        with st.spinner("Monitoring website..."):
            data = monitor_website(site, fast_mode)

        if data:
            df = pd.DataFrame([data])

            # ---------------- METRICS ----------------
            st.success("Monitoring Complete")

            # Determine colors for HTML cards
            reach_class = "status-up" if data["Reachability Status"] == "UP" else "status-down"
            
            if data["HTTP Status"] == "UP":
                http_class = "status-up"
                http_val = f'UP ({data["HTTP Status Code"]})'
            elif data["HTTP Status"] == "WARNING":
                http_class = "status-warning"
                http_val = f'WARN ({data["HTTP Status Code"]})'
            else:
                http_class = "status-down"
                http_val = "DOWN"

            if data["Alert"] == "NORMAL":
                alert_class = "status-up"
            elif data["Alert"] == "WARNING":
                alert_class = "status-warning"
            elif data["Alert"] == "SSL EXPIRING":
                alert_class = "status-ssl"
            else:
                alert_class = "status-down"

            ssl_val = f'{data["SSL Days Left"]} days' if data["SSL Days Left"] >= 0 else "N/A"
            ssl_class = "status-ssl" if data["SSL Days Left"] >= 7 else ("status-down" if data["SSL Days Left"] >= 0 else "status-info")

            # Create clean custom metric cards in a responsive flex layout
            st.markdown(
                f"""
                <div class="metric-container">
                    <div class="metric-card">
                        <div class="metric-title">Reachability</div>
                        <div class="metric-value {reach_class}">{data["Reachability Status"]}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Response Time</div>
                        <div class="metric-value">{data["Avg Response Time (ms)"]} <span style="font-size:16px;color:#8a929e">ms</span></div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">HTTP Status</div>
                        <div class="metric-value {http_class}">{http_val}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">Alert Level</div>
                        <div class="metric-value {alert_class}">{data["Alert"]}</div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-title">SSL Certificate</div>
                        <div class="metric-value {ssl_class}">{ssl_val}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # ---------------- TABLE ----------------
            st.subheader("Detailed Report")
            st.dataframe(df, width="stretch")
            
            # Custom styled Diagnosis Box
            st.markdown(
                f"""
                <div class="diagnosis-box">
                    <strong>Diagnosis:</strong> {data['Diagnosis']}
                </div>
                """,
                unsafe_allow_html=True
            )
    else:
        st.warning("Please enter a website name.")