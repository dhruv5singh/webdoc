from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
import sys
import shlex
import logging
import csv

# Setup logging so we can see debug output in Render logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Simple token-based auth: set API_TOKEN env var on the host (Render: Environment > Add Secret)
API_TOKEN = os.environ.get('API_TOKEN')

PING_SCRIPT = 'ping_test.py'

logger.info(f"API_TOKEN configured: {bool(API_TOKEN)}")


def authorized(req):
    if not API_TOKEN:
        # if no token configured, allow by default (not recommended for public deployments)
        return True
    token = req.headers.get('X-API-Key') or req.args.get('api_key')
    return token == API_TOKEN


@app.route('/health')
def health():
    return 'ok'


@app.route('/api/report', methods=['GET'])
def get_report():
    """Return report.csv as JSON array of objects."""
    report_file = 'report.csv'
    if not os.path.isfile(report_file):
        logger.warning("report.csv not found")
        return jsonify([])
    
    try:
        rows = []
        with open(report_file, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(row)
        logger.info(f"Returning {len(rows)} rows from report.csv")
        return jsonify(rows)
    except Exception as e:
        logger.error(f"Error reading report.csv: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/run', methods=['POST'])
def run_check():
    if not authorized(request):
        logger.warning("Unauthorized API request (invalid token)")
        return jsonify({'error': 'unauthorized'}), 401

    data = request.get_json(force=True, silent=True) or {}
    site = data.get('site')
    if not site:
        logger.warning("API request missing site parameter")
        return jsonify({'error': 'missing site parameter'}), 400

    # sanitize site lightly
    site = site.strip()
    if len(site) > 256:
        logger.warning(f"Site parameter too long: {len(site)} chars")
        return jsonify({'error': 'site parameter too long'}), 400

    logger.info(f"Running monitor for site: {site}")
    
    # Run the monitor in fast mode for responsiveness
    args = [sys.executable, PING_SCRIPT, site, '--fast']
    logger.info(f"Subprocess args: {' '.join(args)}")
    
    try:
        cp = subprocess.run(args, capture_output=True, text=True, timeout=60)
        logger.info(f"Monitor completed. returncode={cp.returncode}, stdout_len={len(cp.stdout)}, stderr_len={len(cp.stderr)}")
        if cp.stdout:
            logger.info(f"stdout:\n{cp.stdout[:500]}")  # log first 500 chars
        if cp.stderr:
            logger.info(f"stderr:\n{cp.stderr[:500]}")
    except subprocess.TimeoutExpired:
        logger.error(f"Monitor timeout for {site}")
        return jsonify({'status': 'timeout'}), 504
    except Exception as e:
        logger.error(f"Monitor error for {site}: {e}")
        return jsonify({'error': str(e)}), 500

    result = {
        'returncode': cp.returncode,
        'stdout': cp.stdout,
        'stderr': cp.stderr,
        'site': site,
    }
    logger.info(f"Returning result: {result}")
    return jsonify(result)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    app.run(host='0.0.0.0', port=port)
