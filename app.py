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


# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="WebDoc - Advanced Network Monitoring",
    page_icon="🌐",
    layout="wide"
)

init_db()


# ---------------- SESSION ----------------
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if 'page' not in st.session_state:
    st.session_state['page'] = 'intro'


# ---------------- SIDEBAR ----------------
with st.sidebar:
    st.markdown("# 🌐 WebDoc")
    st.markdown("### Advanced Monitoring")

    if not st.session_state['authenticated']:
        if st.button("Login"):
            st.session_state['page'] = 'login'
    else:
        st.success("Logged In")



        if st.button("History"):
            st.session_state['page'] = 'history'

        if st.button("Logout"):
            st.session_state['authenticated'] = False
            st.session_state['page'] = 'intro'
            st.rerun()


# ---------------- INTRO PAGE ----------------
if st.session_state['page'] == 'intro':

    st.markdown("""
    <style>
    .main {
        background-color: #0d1117;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("🌐 WebDoc")
    st.subheader("AI Inspired Network Monitoring Dashboard")

    st.write("Monitor latency, DNS, SSL, packet loss and website health in real time.")

    if st.button("Get Started"):
        st.session_state['page'] = 'login'
        st.rerun()

    st.stop()


# ---------------- LOGIN ----------------
if st.session_state['page'] == 'login':

    st.title("Login")

    email = st.text_input("Enter Email")

    if st.button("Continue"):
        st.session_state['authenticated'] = True
        st.session_state['user_email'] = email
        st.session_state['page'] = 'main'
        st.rerun()

    st.stop()


# ---------------- HISTORY ----------------
if st.session_state['page'] == 'history':

    st.title("📊 Monitoring History")
    if st.button("← Back"):
        st.session_state['page'] = 'main'
        st.rerun()

    history_df = get_history(st.session_state['user_email'])

    if not history_df.empty:
        st.dataframe(history_df, use_container_width=True)
    else:
        st.warning("No monitoring history found.")
    st.stop()


# ---------------- MONITOR FUNCTION ----------------
def generate_diagnosis(ip_address, reachability_status, status_code, url, avg_time):
    # (kept for backward compatibility – not used in final output)
    if ip_address == "DNS FAILED":
        return "DNS resolution failed – the domain could not be resolved."
    elif reachability_status == "DOWN":
        return "Website is unreachable via HTTP – no response received."
    elif status_code == 403:
        return f"Access to {url} is forbidden (HTTP 403). This often means the server blocks automated requests."
    elif status_code >= 400:
        return f"Received HTTP {status_code} from {url}."
    elif avg_time > 300:
        return "Website responded, but latency is high (>300 ms)."
    else:
        return f"Successfully reached {url} with status code {status_code}."
    if ip_address == "DNS FAILED":
        return "DNS resolution failed – the domain could not be resolved."
    elif reachability_status == "DOWN":
        return "Website is unreachable via HTTP – no response received."
    elif status_code == 403:
        return f"Access to {url} is forbidden (HTTP 403). This often means the server blocks automated requests."
    elif status_code >= 400:
        return f"Received HTTP {status_code} from {url}."
    elif avg_time > 300:
        return "Website responded, but latency is high (>300 ms)."
    else:
        return "Website is reachable and latency is within normal range."

def monitor_website(site_raw):
    """Monitor a website and return a dictionary of metrics.
    The function now also creates a user‑friendly, AI‑style diagnosis paragraph.
    """

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
    except:
        ip_address = "DNS FAILED"
        dns_time = 0

    # HTTP
    reachability_status = "DOWN"
    http_status = "DOWN"
    status_code = 0
    avg_time = 0
    packet_loss = 100
    diagnosis = ""

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

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

        with context.wrap_socket(socket.socket(), server_hostname=hostname) as s:
            s.settimeout(5)
            s.connect((hostname, 443))
            cert = s.getpeercert()

            expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')

            ssl_days_left = (
                expiry_date.replace(tzinfo=timezone.utc)
                - datetime.now(timezone.utc)
            ).days

    except:
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
                diagnosis = "Website responded, but latency is high (>300 ms)."
        else:
            alert = "NORMAL"
            if not diagnosis:
                diagnosis = "Website is reachable and latency is within normal range."
    
    # Category
    if avg_time < 120:
        category = "Fast"
    elif avg_time < 300:
        category = "Moderate"
    else:
        category = "Slow"

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


# ---------------- AI DIAGNOSIS HELPER ----------------

def compose_diagnosis(data: dict) -> str:
    """Create a natural‑language diagnosis for non‑technical users.
    Combines reachability, HTTP status, latency, DNS, and SSL information.
    """
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

    # Build paragraph
    parts = []
    # Reachability & DNS
    if reach == "DOWN" or ip == "DNS FAILED":
        parts.append(f"We could not reach {site}. {raw}")
    else:
        parts.append(f"{site} ({ip}) is reachable.")
        # HTTP status
        if http_status == "UP":
            parts.append(f"The HTTP request succeeded with status code {code}.")
        else:
            parts.append(f"The HTTP request returned a warning ({code}). {raw}")
        # Latency
        if latency is not None:
            if latency > 300:
                parts.append(f"Response time is {latency:.0f} ms, which is slower than usual.")
            else:
                parts.append(f"Response time is {latency:.0f} ms, which is fast.")
        # DNS
        if dns is not None:
            parts.append(f"DNS lookup took {dns:.0f} ms.")
        # SSL
        if ssl_days is not None:
            if ssl_days < 30:
                parts.append(f"The SSL certificate expires in {ssl_days} days – consider renewing soon.")
            else:
                parts.append(f"The SSL certificate is valid for another {ssl_days} days.")
        # Overall health
        if alert == "NORMAL":
            parts.append("Overall health looks good.")
        elif alert == "ACCEPTABLE":
            parts.append("Overall health is acceptable, but keep an eye on latency.")
        else:
            parts.append("Overall health is critical – please investigate the issues above.")
    return " ".join(parts)

# ---------------- MAIN DASHBOARD ----------------
st.markdown("""
<style>
.stApp {
    background-color: #0d1117;
    color: white;
}
[data-testid="metric-container"] {
    background: linear-gradient(145deg,#131a2a,#0f1725);
    border: 1px solid #1f2937;
    padding: 15px;
    border-radius: 18px;
}
/* Align monitor button with input */
.stButton > button {
    margin-top: -5px;
}
</style>
""", unsafe_allow_html=True)

st.title("🌐 LIVE NETWORK MONITORING")
st.caption("Real-time website health analytics")


# ---------------- INPUT ----------------
col1, col2 = st.columns([5,1])

with col1:
    site = st.text_input(
        "Website",
        placeholder="Enter website like google.com"
    )

with col2:
    monitor = st.button("Monitor")


# ---------------- MONITOR ----------------
if monitor and site:

    with st.spinner("Analyzing website..."):

        data = monitor_website(site)

        insert_record(
            st.session_state['user_email'],
            data
        )

        st.success("Monitoring Complete")


        # ---------------- METRIC ROW ----------------
        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Reachability",
            data['Reachability Status']
        )

        c2.metric(
            "HTTP",
            f"{data['HTTP Status']} ({data['HTTP Status Code']})"
        )

        c3.metric(
            "Response",
            f"{data['Avg Response Time (ms)']} ms"
        )

        c4.metric(
            "Alert",
            data['Alert']
        )


        # ---------------- WEBSITE HISTORY ----------------
        st.markdown("---")

        st.subheader(f"📈 Trend Analytics — {site}")

        history_df = get_website_history(
            st.session_state['user_email'],
            site
        )

        if len(history_df) > 1:
        # Show full diagnosis for each historic entry
        st.subheader("🧠 Diagnosis History")
        for _, row in history_df.iterrows():
            st.markdown(f"**{row['timestamp']} – {row['website']}**")
            st.write(row['diagnosis'])
        # Existing graphs follow

            history_df['timestamp'] = pd.to_datetime(history_df['timestamp'])


            # ---------------- LATENCY GRAPH ----------------
            # Simplified latency trend graph
            fig1 = px.line(
                history_df,
                x='timestamp',
                y='avg_response',
                title=f'{site} Response Time Trend'
            )
            fig1.update_layout(
                template='plotly_white',
                height=300,
                xaxis_title='Time',
                yaxis_title='Response (ms)'
            )
            st.plotly_chart(fig1, width='stretch')





            # Simplified DNS lookup trend bar chart
            fig3 = px.bar(
                history_df,
                x='timestamp',
                y='dns_time',
                title=f'{site} DNS Lookup Trend'
            )
            fig3.update_layout(
                template='plotly_white',
                height=300,
                xaxis_title='Time',
                yaxis_title='DNS Time (ms)'
            )
            st.plotly_chart(fig3, width='stretch')


        else:
            st.info(
                "This is the first scan for this website. More scans will automatically generate trend graphs."
            )


        # ---------------- DIAGNOSIS ----------------
        st.markdown("---")

        st.subheader("🧠 Diagnosis")

        st.write(data['Diagnosis'])


        # ---------------- RAW TABLE ----------------
        st.markdown("---")

        st.subheader("📋 Detailed Report")

        report_data = {k: v for k, v in data.items() if k != "Diagnosis"}
        df = pd.DataFrame([report_data])

        st.dataframe(df, width='stretch')
