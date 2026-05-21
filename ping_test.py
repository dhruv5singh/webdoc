#!/usr/bin/env python3
import sys
import time
import subprocess
import requests
import csv
import re
from datetime import datetime, timezone
import os
import socket
import ssl
from urllib.parse import urlparse


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
    # Ensure CSV headers are aligned and updated
    if os.path.isfile("report.csv"):
        try:
            with open("report.csv", "r", encoding="utf-8") as f:
                lines = f.readlines()
            if lines:
                header = lines[0].strip().split(",")
                needs_update = False
                if "Ping_Status" in header:
                    header = ["Reachability_Status" if h == "Ping_Status" else h for h in header]
                    needs_update = True
                if "Diagnosis" not in header:
                    header.append("Diagnosis")
                    needs_update = True
                
                if needs_update:
                    lines[0] = ",".join(header) + "\n"
                    # For historical rows, pad them to match the new headers
                    expected_len = len(header)
                    for i in range(1, len(lines)):
                        row = lines[i].strip().split(",")
                        if len(row) < expected_len:
                            row.extend([""] * (expected_len - len(row)))
                            lines[i] = ",".join(row) + "\n"
                    
                    with open("report.csv", "w", encoding="utf-8", newline="") as f:
                        f.writelines(lines)
        except Exception as e:
            print(f"Error repairing report.csv headers: {e}")

    file_exists = os.path.isfile("report.csv")
    sites = load_sites(target_site)

    with open("report.csv", "a", newline="", encoding="utf-8") as report:
        writer = csv.writer(report)
        if not file_exists:
            writer.writerow([
                "Timestamp",
                "Website",
                "Reachability_Status",
                "Avg_Response_Time_ms",
                "Packet_Loss_%",
                "DNS_Time_ms",
                "HTTP_Status",
                "HTTP_Status_Code",
                "Load_Time_ms",
                "SSL_Days_Left",
                "Final_Status",
                "Category",
                "Alert",
                "Diagnosis",
            ])

        for row in sites:
            site_raw = row.get("site")
            if not site_raw:
                continue
            # normalize input: accept full URLs or bare hostnames
            s = site_raw.strip()
            if s.startswith('http://') or s.startswith('https://'):
                parsed = urlparse(s)
                hostname = parsed.hostname
                path = parsed.path or ''
                if parsed.query:
                    path += '?' + parsed.query
                http_urls = [s.rstrip('/')]
            else:
                parsed = urlparse('//' + s)
                hostname = parsed.hostname or s
                path = parsed.path or ''
                if parsed.query:
                    path += '?' + parsed.query
                http_urls = [f'https://{hostname}{path}', f'http://{hostname}{path}']

            site = hostname
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
                        
                        # Reachability is UP if we get a response
                        reachability_status = "UP"
                        packet_loss = 0
                        
                        if 200 <= status_code < 400:
                            http_status = "UP"
                        else:
                            http_status = "WARNING"
                        
                        break
                    except Exception as e:
                        diagnosis = f"HTTP request failed: {e}"
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
                    ssl_days_left = (expiry_date.replace(tzinfo=timezone.utc) - datetime.now(timezone.utc)).days
            except Exception:
                ssl_days_left = -1

            # FINAL STATUS & DIAGNOSIS
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

            # CATEGORY
            if avg_time == 0:
                category = "N/A"
            elif avg_time < 100:
                category = "Fast"
            elif avg_time < 250:
                category = "Moderate"
            else:
                category = "Slow"

            writer.writerow([
                timestamp,
                site,
                reachability_status,
                round(avg_time, 2),
                round(packet_loss, 2),
                round(dns_time, 2),
                http_status,
                status_code,
                round(load_time, 2),
                ssl_days_left,
                final_status,
                category,
                alert,
                diagnosis,
            ])


if __name__ == '__main__':
    target, fast = parse_args()
    run_monitor(target_site=target, fast_mode=fast)