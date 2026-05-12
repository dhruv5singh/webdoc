from flask import Flask, request, render_template, redirect, url_for
import csv
import subprocess
import time
import os

app = Flask(__name__)

SITE_CSV = "site.csv"
REPORT_CSV = "report.csv"
PING_SCRIPT = "ping_test.py"


def append_site_to_csv(site: str):
    site = site.strip()
    if not site:
        return
    existing = set()
    if os.path.exists(SITE_CSV):
        with open(SITE_CSV, newline='', encoding='utf-8') as sf:
            for i, line in enumerate(sf):
                if i == 0 and line.strip().lower() == 'site':
                    continue
                existing.add(line.strip().lower())
    need_header = not os.path.exists(SITE_CSV)
    if site.lower() not in existing:
        with open(SITE_CSV, 'a', newline='', encoding='utf-8') as f:
            if need_header:
                f.write('site\n')
            f.write(site + '\n')


def run_monitor_fast(site: str):
    # call ping_test with fast flag
    cp = subprocess.run(["python", PING_SCRIPT, site, "--fast"], capture_output=True, text=True)
    print(f"run_monitor_fast: site={site} rc={cp.returncode}")
    if cp.stdout:
        print(cp.stdout)
    if cp.stderr:
        print(cp.stderr)
    return cp


def latest_report_for(site: str):
    if not os.path.isfile(REPORT_CSV):
        return None
    with open(REPORT_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r.get("Website", "").strip().lower() == site.strip().lower()]
        return rows[-1] if rows else None


def clamp_percent(x, max_val):
    try:
        v = float(x)
    except Exception:
        return 0
    p = int(round((v / max_val) * 100))
    return max(0, min(100, p))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        site = request.form.get("site", "").strip()
        if site:
            # run fast monitor
            cp = run_monitor_fast(site)
            # wait briefly for report to be written (poll)
            row = None
            for _ in range(6):
                row = latest_report_for(site)
                if row:
                    break
                time.sleep(0.5)
            append_site_to_csv(site)
            return redirect(url_for("show_site", site=site))
    return render_template("index.html", report=None)


@app.route("/site")
def show_site():
    site = request.args.get("site", "")
    if not site:
        return redirect(url_for("index"))
    row = latest_report_for(site)
    if not row:
        return render_template("index.html", report=None, message="No data found for " + site)
    bars = {
        "Avg_Response_Time_ms": clamp_percent(row.get("Avg_Response_Time_ms", 0), 2000),
        "Packet_Loss_%": clamp_percent(row.get("Packet_Loss_%", 0), 100),
        "DNS_Time_ms": clamp_percent(row.get("DNS_Time_ms", 0), 1000),
        "Load_Time_ms": clamp_percent(row.get("Load_Time_ms", 0), 5000),
        "SSL_Days_Left": clamp_percent(row.get("SSL_Days_Left", 0), 365)
    }
    return render_template("index.html", report=row, bars=bars)


if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, request, render_template, redirect, url_for
import csv
import subprocess
import time
import os

app = Flask(__name__)

SITE_CSV = "site.csv"
REPORT_CSV = "report.csv"
PING_SCRIPT = "ping_test.py"


def append_site_to_csv(site: str):
    """Append a site to site.csv if not present (case-insensitive). Ensure header exists."""
    site = site.strip()
    if not site:
        return
    existing = set()
    if os.path.exists(SITE_CSV):
        with open(SITE_CSV, newline='', encoding='utf-8') as sf:
            for i, line in enumerate(sf):
                if i == 0 and line.strip().lower() == 'site':
                    continue
                existing.add(line.strip().lower())
    # add header if file missing
    need_header = not os.path.exists(SITE_CSV)
    if site.lower() not in existing:
        with open(SITE_CSV, 'a', newline='', encoding='utf-8') as f:
            if need_header:
                f.write('site\n')
            f.write(site + '\n')


def run_monitor_for(site: str):
    # Run the monitor script for a single site (blocking) and capture output
    cp = subprocess.run(["python", PING_SCRIPT, site], capture_output=True, text=True)
    # Log for debugging
    print(f"run_monitor_for: site={site} returncode={cp.returncode}")
    if cp.stdout:
        print("stdout:\n", cp.stdout)
    if cp.stderr:
        print("stderr:\n", cp.stderr)
    return cp


def latest_report_for(site: str):
    if not os.path.isfile(REPORT_CSV):
        return None
    with open(REPORT_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r.get("Website", "").strip().lower() == site.strip().lower()]
        return rows[-1] if rows else None


def clamp_percent(x, max_val):
    try:
        v = float(x)
    except Exception:
        return 0
    p = int(round((v / max_val) * 100))
    return max(0, min(100, p))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        site = request.form.get("site", "").strip()
        if site:
            # Run monitor first for the single site
            cp = run_monitor_for(site)
            # Wait briefly for report.csv to be updated and attempt to read the latest row
            row = None
            for _ in range(6):
                row = latest_report_for(site)
                if row:
                    break
                time.sleep(0.5)
            # If we got a row, append to site.csv (deduplicated). If not, still append to keep history
            try:
                append_site_to_csv(site)
            except Exception as e:
                print(f"append_site_to_csv failed: {e}")
            return redirect(url_for("show_site", site=site))
    return render_template("index.html", report=None)


@app.route("/site")
def show_site():
    site = request.args.get("site", "")
    if not site:
        return redirect(url_for("index"))
    row = latest_report_for(site)
    if not row:
        return render_template("index.html", report=None, message="No data found for " + site)
    bars = {
        "Avg_Response_Time_ms": clamp_percent(row.get("Avg_Response_Time_ms", 0), 2000),
        "Packet_Loss_%": clamp_percent(row.get("Packet_Loss_%", 0), 100),
        "DNS_Time_ms": clamp_percent(row.get("DNS_Time_ms", 0), 1000),
        "Load_Time_ms": clamp_percent(row.get("Load_Time_ms", 0), 5000),
        "SSL_Days_Left": clamp_percent(row.get("SSL_Days_Left", 0), 365)
    }
    return render_template("index.html", report=row, bars=bars)


if __name__ == "__main__":
    # Run dev server
    app.run(debug=True)
from flask import Flask, request, render_template, redirect, url_for
import csv
import subprocess
import time
import os

app = Flask(__name__)

SITE_CSV = "site.csv"
REPORT_CSV = "report.csv"
PING_SCRIPT = "ping_test.py"


def run_monitor_for(site):
    # Run the existing monitor script for a single site (faster)
    subprocess.run(["python", PING_SCRIPT, site], check=False)


def latest_report_for(site):
    if not os.path.isfile(REPORT_CSV):
        return None
    with open(REPORT_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r.get("Website", "").strip().lower() == site.strip().lower()]
        return rows[-1] if rows else None


def clamp_percent(x, max_val):
    try:
        v = float(x)
    except Exception:
        return 0
    p = int(round((v / max_val) * 100))
    return max(0, min(100, p))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        site = request.form.get("site", "").strip()
        if site:
            # run monitor only for this site in fast mode
            run_monitor_for(site + " --fast")
            # small delay to ensure report.csv updated
            time.sleep(0.5)
            return redirect(url_for("show_site", site=site))
    return render_template("index.html", report=None)


@app.route("/site")
def show_site():
    site = request.args.get("site", "")
    if not site:
        return redirect(url_for("index"))
    row = latest_report_for(site)
    if not row:
        return render_template("index.html", report=None, message="No data found for " + site)
    # compute bar percentages (scales can be tuned)
    bars = {
        "Avg_Response_Time_ms": clamp_percent(row.get("Avg_Response_Time_ms", 0), 2000),  # scale 0..2000ms
        "Packet_Loss_%": clamp_percent(row.get("Packet_Loss_%", 0), 100),               # 0..100%
        "DNS_Time_ms": clamp_percent(row.get("DNS_Time_ms", 0), 1000),
        "Load_Time_ms": clamp_percent(row.get("Load_Time_ms", 0), 5000),
        "SSL_Days_Left": clamp_percent(row.get("SSL_Days_Left", 0), 365)
    }
    return render_template("index.html", report=row, bars=bars)


if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, request, render_template, redirect, url_for
import csv
import subprocess
import time
import os

app = Flask(__name__)

SITE_CSV = "site.csv"
REPORT_CSV = "report.csv"
PING_SCRIPT = "ping_test.py"


def run_monitor():
    # Run the existing monitor script (blocks until completion)
    subprocess.run(["python", PING_SCRIPT], check=False)


def latest_report_for(site):
    if not os.path.isfile(REPORT_CSV):
        return None
    with open(REPORT_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r.get("Website", "").strip().lower() == site.strip().lower()]
        return rows[-1] if rows else None


from flask import Flask, request, render_template, redirect, url_for
import csv
import subprocess
import time
import os

app = Flask(__name__)

SITE_CSV = "site.csv"
REPORT_CSV = "report.csv"
PING_SCRIPT = "ping_test.py"


def run_monitor():
    # Run the existing monitor script (blocks until completion)
    subprocess.run(["python", PING_SCRIPT], check=False)


def latest_report_for(site):
    if not os.path.isfile(REPORT_CSV):
        return None
    with open(REPORT_CSV, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader if r.get("Website", "").strip().lower() == site.strip().lower()]
        return rows[-1] if rows else None


def clamp_percent(x, max_val):
    try:
        v = float(x)
    except Exception:
        return 0
    p = int(round((v / max_val) * 100))
    return max(0, min(100, p))


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        site = request.form.get("site", "").strip()
        if site:
            # append to site.csv so existing script picks it up
            # avoid duplicates
            existing = set()
            if os.path.exists(SITE_CSV):
                with open(SITE_CSV, newline='', encoding='utf-8') as sf:
                    for line in sf:
                        existing.add(line.strip().lower())
            if site.strip().lower() not in existing:
                prefix = "\n" if (os.path.exists(SITE_CSV) and os.path.getsize(SITE_CSV) > 0) else ""
                with open(SITE_CSV, "a", newline='', encoding='utf-8') as f:
                    f.write(prefix + site + "\n")
            # run monitor (may take several seconds)
            run_monitor()
            # small delay to ensure report.csv updated
            time.sleep(0.5)
            return redirect(url_for("show_site", site=site))
    return render_template("index.html", report=None)


@app.route("/site")
def show_site():
    site = request.args.get("site", "")
    if not site:
        return redirect(url_for("index"))
    row = latest_report_for(site)
    if not row:
        return render_template("index.html", report=None, message="No data found for " + site)
    # compute bar percentages (scales can be tuned)
    bars = {
        "Avg_Response_Time_ms": clamp_percent(row.get("Avg_Response_Time_ms", 0), 2000),  # scale 0..2000ms
        "Packet_Loss_%": clamp_percent(row.get("Packet_Loss_%", 0), 100),               # 0..100%
        "DNS_Time_ms": clamp_percent(row.get("DNS_Time_ms", 0), 1000),
        "Load_Time_ms": clamp_percent(row.get("Load_Time_ms", 0), 5000),
        "SSL_Days_Left": clamp_percent(row.get("SSL_Days_Left", 0), 365)
    }
    return render_template("index.html", report=row, bars=bars)


if __name__ == "__main__":
    # Run dev server
    app.run(debug=True)