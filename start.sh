#!/bin/bash

# Configuration environment variables defaults
export PORT=${PORT:-10000}
export ADMIN_SLUG=${ADMIN_SLUG:-/admin-panel-control}

# Ensure ADMIN_SLUG starts with a slash
if [[ ! "$ADMIN_SLUG" =~ ^/ ]]; then
    export ADMIN_SLUG="/$ADMIN_SLUG"
fi

echo "=== System Booting ==="
echo "Port: $PORT"
echo "Admin Slug: $ADMIN_SLUG"

# Compile dynamic nginx config
python -c "
import os
port = os.getenv('PORT')
slug = os.getenv('ADMIN_SLUG')
with open('nginx.conf.template', 'r') as f:
    content = f.read()
content = content.replace('\${PORT}', port).replace('\${ADMIN_SLUG}', slug)
with open('/etc/nginx/nginx.conf', 'w') as f:
    f.write(content)
print('Dynamic Nginx configuration written successfully!')
"

echo "Launching main Streamlit app on internal port 8501..."
streamlit run app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true --server.enableCORS false --server.enableXsrfProtection false &

echo "Launching admin Streamlit app on internal port 8502 with baseUrlPath $ADMIN_SLUG..."
streamlit run admin_app.py --server.port 8502 --server.address 127.0.0.1 --server.baseUrlPath "$ADMIN_SLUG" --server.headless true --server.enableCORS false --server.enableXsrfProtection false &

echo "Starting Nginx frontend proxy..."
nginx -g "daemon off;"
