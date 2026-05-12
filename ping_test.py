#!/usr/bin/env python3
import sys
import time
import subprocess
import requests
import csv
import re
from datetime import datetime
import os
import socket
import ssl


# Simple network monitor that writes to report.csv
# Usage:
#  python ping_test.py            # runs for all sites listed in site.csv
#  python ping_test.py example.com  # runs only for example.com
#  python ping_test.py example.com --fast  # faster checks for UI


def parse_args():
    site = None
    fast = False
    args = sys.argv[1:]
    if args:
        site = args[0]
    if len(args) > 1:
        if args[1].lower() in ("--fast", "fast"):
            fast = True
    return site, fast


def load_sites(target_site):
    if target_site:
        return [{"site": target_site}]
    with open("site.csv") as f:
        reader = csv.DictReader(f)
        return list(reader)


def run_monitor(target_site=None, fast_mode=False):
    file_exists = os.path.isfile("report.csv")
    sites = load_sites(target_site)

    with open("report.csv", "a", newline="", encoding="utf-8") as report:
        writer = csv.writer(report)

        if not file_exists:
            writer.writerow([
                "Timestamp",
                "Website",
                "Ping_Status",
                "Avg_Response_Time_ms",
                "Packet_Loss_%",
                "Hop_Count",
                "DNS_Time_ms",
                "HTTP_Status",
                "HTTP_Status_Code",
                "Load_Time_ms",
                "SSL_Days_Left",
                "Final_Status",
                "Category",
                "Alert",
            ])

        for row in sites:
            site = row.get("site")
            timestamp = datetime.now()

            # DNS
            try:
                dns_start = time.time()
                ip_address = socket.gethostbyname(site)
                dns_end = time.time()
                dns_time = (dns_end - dns_start) * 1000
            except Exception:
                ip_address = "DNS FAILED"
                dns_time = 0

            # PING
            ping_count = 1 if fast_mode else 3
            ping_wait = 500 if fast_mode else 1000
            try:
                result = subprocess.run(["ping", "-n", str(ping_count), "-w", str(ping_wait), site], capture_output=True, text=True)
                output = result.stdout
                ping_status = "UP" if result.returncode == 0 else "DOWN"
            except Exception:
                output = ""
                ping_status = "DOWN"

            time_match = re.findall(r"time[=<](\d+)", output)
            avg_time = (sum(map(int, time_match)) / len(time_match)) if time_match else 0
            loss_match = re.search(r"Lost = (\d+)", output)
            sent_match = re.search(r"Sent = (\d+)", output)
            if loss_match and sent_match:
                lost = int(loss_match.group(1))
                sent = int(sent_match.group(1))
                packet_loss = (lost / sent) * 100
            else:
                packet_loss = 0

            # TRACEROUTE (skip in fast mode)
            hop_count = 0
            if not fast_mode:
                try:
                    tracert = subprocess.run(["tracert", "-h", "15", site], capture_output=True, text=True)
                    hop_lines = re.findall(r"^\s*\d+\s+", tracert.stdout, re.MULTILINE)
                    hop_count = len(hop_lines)
                except Exception:
                    hop_count = 0

            # HTTP - use a session, follow redirects, record history; try HTTPS then HTTP
            status_code = 0
            http_status = "DOWN"
            load_time = 0
            final_url = ""
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
            }
            session = requests.Session()
            session.headers.update(headers)
            http_timeout = 3 if fast_mode else 10
            for scheme in ("https://", "http://"):
                try:
                    start = time.time()
                    resp = session.get(scheme + site, timeout=http_timeout, allow_redirects=True)
                    end = time.time()
                    load_time = (end - start) * 1000
                    status_code = resp.status_code
                    final_url = resp.url
                    # log redirect chain for debugging
                    if resp.history:
                        chain = " -> ".join(h.headers.get('Location', str(h.status_code)) for h in resp.history)
                        print(f"HTTP redirect chain for {site}: {chain} -> {final_url} (final {status_code})")
                    else:
                        print(f"HTTP final URL for {site}: {final_url} (status {status_code})")
                    # treat 2xx and 3xx as UP
                    if 200 <= status_code < 400:
                        http_status = "UP"
                    else:
                        http_status = "WARNING"
                    break
                except Exception as e:
                    print(f"HTTP request for {scheme+site} failed: {e}")
                    continue

            # SSL
            ssl_timeout = 3 if fast_mode else 5
            try:
                context = ssl.create_default_context()
                with context.wrap_socket(socket.socket(), server_hostname=site) as s:
                    s.settimeout(ssl_timeout)
                    s.connect((site, 443))
                    cert = s.getpeercert()
                    expiry_date = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    ssl_days_left = (expiry_date - datetime.utcnow()).days
            except Exception:
                ssl_days_left = -1

            # FINAL STATUS
            if http_status == "UP":
                final_status = "UP"
            elif ping_status == "UP":
                final_status = "NETWORK ISSUE"
            else:
                final_status = "DOWN"

            # CATEGORY
            if avg_time < 100:
                category = "Fast"
            elif avg_time < 250:
                category = "Moderate"
            else:
                category = "Slow"

            # ALERT
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

            writer.writerow([
                timestamp,
                site,
                ping_status,
                round(avg_time, 2),
                round(packet_loss, 2),
                hop_count,
                round(dns_time, 2),
                http_status,
                status_code,
                round(load_time, 2),
                ssl_days_left,
                final_status,
                category,
                alert,
            ])


if __name__ == '__main__':
    target, fast = parse_args()
    run_monitor(target_site=target, fast_mode=fast)