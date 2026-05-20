import streamlit as st
import pandas as pd
import subprocess
import requests
import socket
import ssl
import re
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Network Monitoring Dashboard",
    layout="wide"
)

st.title("🌐 Live Network Monitoring Dashboard")
st.write("Monitor website health, latency, DNS, SSL, and HTTP status in real time.")

# ---------------- INPUT ----------------

site = st.text_input(
    "Enter Website",
    placeholder="example: google.com"
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
    headers = {"User-Agent": "Mozilla/5.0"}
    http_timeout = 3 if fast_mode else 10
    response = None
    for url_try in http_urls:
        try:
            start = time.time()
            response = requests.get(url_try, headers=headers, timeout=http_timeout, allow_redirects=True)
            end = time.time()
            avg_time = (end - start) * 1000
            status_code = response.status_code
            if 200 <= status_code < 400:
                reachability_status = "UP"
                http_status = "UP"
                packet_loss = 0
                diagnosis = "Application reachable and healthy."
            else:
                reachability_status = "UP"
                http_status = "WARNING"
                packet_loss = 0
                diagnosis = "Website reachable but HTTP status is not OK."
            website_display = response.url
            break
        except Exception as e:
            diagnosis = f"HTTP request failed: {e}"
            continue

    if reachability_status == "DOWN":
        diagnosis = "Website unreachable via HTTP."

    # ---------------- HTTP CHECK ----------------

    # ---------------- HTTP CHECK ----------------
    load_time = 0
    status_code = 0
    http_status = "DOWN"
    headers = {"User-Agent": "Mozilla/5.0"}
    http_timeout = 3 if fast_mode else 10
    for url_try in http_urls:
        try:
            start = time.time()
            response = requests.get(url_try, headers=headers, timeout=http_timeout, allow_redirects=True)
            end = time.time()
            load_time = (end - start) * 1000
            status_code = response.status_code
            if response.history:
                # you can log response.history if needed
                pass
            if 200 <= status_code < 400:
                http_status = "UP"
            else:
                http_status = "WARNING"
            # prefer the first successful URL
            website_display = response.url
            break
        except Exception:
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

            ssl_days_left = (
                expiry_date - datetime.now(timezone.utc)
            ).days

    except Exception:

        ssl_days_left = -1


    # ---------------- FINAL STATUS ----------------
    if ip_address == "DNS FAILED":
        final_status = "DNS ISSUE"
        diagnosis = "DNS resolution failed."
    elif http_status == "UP":
        final_status = "UP"
        if avg_time > 300:
            diagnosis = "Website reachable but high latency detected."
    elif reachability_status == "DOWN":
        final_status = "DOWN"
        diagnosis = "Website unreachable via HTTP."
    else:
        final_status = "DOWN"


    # ---------------- CATEGORY ----------------
    if avg_time < 100:
        category = "Fast"
    elif avg_time < 250:
        category = "Moderate"
    else:
        category = "Slow"


    # ---------------- ALERT ----------------
    if final_status == "DOWN":
        alert = "CRITICAL"
    elif final_status == "DNS ISSUE":
        alert = "CRITICAL"
    elif avg_time > 300 and final_status == "UP":
        alert = "WARNING"
    elif ssl_days_left != -1 and ssl_days_left < 7:
        alert = "SSL EXPIRING"
        diagnosis = "SSL certificate nearing expiry."
    else:
        alert = "NORMAL"

    # ---------------- RETURN DATA ----------------

    return {
        "Timestamp": timestamp,
        "Website": website_display,
        "IP Address": ip_address,
        "Reachability Status": reachability_status,
        "HTTP Status": http_status,
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

        df = pd.DataFrame([data])

        # ---------------- METRICS ----------------

        st.success("Monitoring Complete")


        col1, col2, col3, col4 = st.columns(4)
        col1.metric(
            "Reachability",
            data["Reachability Status"]
        )
        col2.metric(
            "HTTP",
            data["HTTP Status"]
        )
        col3.metric(
            "Response Time",
            f'{data["Avg Response Time (ms)"]} ms'
        )
        col4.metric(
            "Alert",
            data["Alert"]
        )

        # ---------------- TABLE ----------------


        st.subheader("Detailed Report")
        st.dataframe(df, use_container_width=True)
        st.markdown(f"**Diagnosis:** {data['Diagnosis']}")

    else:

        st.warning("Please enter a website name.")