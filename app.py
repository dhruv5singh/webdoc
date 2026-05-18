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

    # ---------------- PING ----------------

    ping_count = 1 if fast_mode else 3
    ping_wait = 1 if fast_mode else 2

    try:

        result = subprocess.run(
            ["ping", "-c", str(ping_count), "-W", str(ping_wait), site],
            capture_output=True,
            text=True
        )

        output = result.stdout

        ping_status = "UP" if result.returncode == 0 else "DOWN"

    except Exception:
        output = ""
        ping_status = "DOWN"

    # RESPONSE TIME

    time_match = re.findall(
        r"time=(\d+\.?\d*)",
        output
    )

    avg_time = (
        sum(map(float, time_match)) / len(time_match)
    ) if time_match else 0

    # PACKET LOSS

    loss_match = re.search(
        r"(\d+)% packet loss",
        output
    )

    if loss_match:
        packet_loss = float(loss_match.group(1))
    else:
        packet_loss = 100 if ping_status == "DOWN" else 0

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

    if http_status == "UP":
        final_status = "UP"

    elif ping_status == "UP":
        final_status = "NETWORK ISSUE"

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

    elif packet_loss > 30:
        alert = "CRITICAL"

    elif avg_time > 300:
        alert = "WARNING"

    elif ssl_days_left != -1 and ssl_days_left < 7:
        alert = "SSL EXPIRING"

    else:
        alert = "NORMAL"

    # ---------------- RETURN DATA ----------------

    return {
        "Timestamp": timestamp,
        "Website": website_display,
        "IP Address": ip_address,
        "Ping Status": ping_status,
        "HTTP Status": http_status,
        "Final Status": final_status,
        "Avg Response Time (ms)": round(avg_time, 2),
        "Load Time (ms)": round(load_time, 2),
        "Packet Loss %": round(packet_loss, 2),
        "DNS Time (ms)": round(dns_time, 2),
        "SSL Days Left": ssl_days_left,
        "Category": category,
        "Alert": alert
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
            "Ping",
            data["Ping Status"]
        )

        col2.metric(
            "HTTP",
            data["HTTP Status"]
        )

        col3.metric(
            "Response",
            f'{data["Avg Response Time (ms)"]} ms'
        )

        col4.metric(
            "Alert",
            data["Alert"]
        )

        # ---------------- TABLE ----------------

        st.subheader("Detailed Report")

        st.dataframe(
            df,
            use_container_width=True
        )

    else:

        st.warning("Please enter a website name.")