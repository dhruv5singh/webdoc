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

# Compile dynamic nginx config from template
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
print(f'  PORT={port}, ADMIN_SLUG={slug}')
"

echo "Launching main Streamlit app on internal port 8501..."
streamlit run app.py \
    --server.port 8501 \
    --server.address 127.0.0.1 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false &

echo "Launching admin Streamlit app on internal port 8502..."
streamlit run admin_app.py \
    --server.port 8502 \
    --server.address 127.0.0.1 \
    --server.baseUrlPath "$ADMIN_SLUG" \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false &

# Wait until both Streamlit apps are ready before starting Nginx
echo "Waiting for Streamlit apps to be ready..."
MAX_WAIT=60
WAITED=0

until curl -sf http://127.0.0.1:8501/_stcore/health > /dev/null 2>&1; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo "ERROR: Main app (8501) did not start in ${MAX_WAIT}s. Proceeding anyway."
        break
    fi
    sleep 1
    WAITED=$((WAITED + 1))
done
echo "Main app is ready (waited ${WAITED}s)"

WAITED=0
until curl -sf http://127.0.0.1:8502/_stcore/health > /dev/null 2>&1; do
    if [ $WAITED -ge $MAX_WAIT ]; then
        echo "ERROR: Admin app (8502) did not start in ${MAX_WAIT}s. Proceeding anyway."
        break
    fi
    sleep 1
    WAITED=$((WAITED + 1))
done
echo "Admin app is ready (waited ${WAITED}s)"

echo "=== All services ready — Starting Nginx frontend proxy on port $PORT ==="
nginx -g "daemon off;"
