from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import subprocess
import sys
import shlex

app = Flask(__name__)
CORS(app)

# Simple token-based auth: set API_TOKEN env var on the host (Render: Environment > Add Secret)
API_TOKEN = os.environ.get('API_TOKEN')

PING_SCRIPT = 'ping_test.py'


def authorized(req):
    if not API_TOKEN:
        # if no token configured, allow by default (not recommended for public deployments)
        return True
    token = req.headers.get('X-API-Key') or req.args.get('api_key')
    return token == API_TOKEN


@app.route('/health')
def health():
    return 'ok'


@app.route('/api/run', methods=['POST'])
def run_check():
    if not authorized(request):
        return jsonify({'error': 'unauthorized'}), 401

    data = request.get_json(force=True, silent=True) or {}
    site = data.get('site')
    if not site:
        return jsonify({'error': 'missing site parameter'}), 400

    # sanitize site lightly
    site = site.strip()
    if len(site) > 256:
        return jsonify({'error': 'site parameter too long'}), 400

    # Run the monitor in fast mode for responsiveness
    args = [sys.executable, PING_SCRIPT, site, '--fast']
    try:
        cp = subprocess.run(args, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return jsonify({'status': 'timeout'}), 504
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    result = {
        'returncode': cp.returncode,
        'stdout': cp.stdout,
        'stderr': cp.stderr,
    }
    return jsonify(result)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    app.run(host='0.0.0.0', port=port)
