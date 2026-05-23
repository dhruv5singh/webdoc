FROM python:3.11-slim

# Install nginx (reverse proxy) and curl (used by start.sh health checks)
RUN apt-get update && apt-get install -y nginx curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Render assigns a dynamic $PORT — Nginx listens on it and proxies internally
EXPOSE 10000

# Use start.sh as the entrypoint — it compiles nginx config, starts both
# Streamlit apps (port 8501 = user, 8502 = admin), then runs Nginx in foreground
ENTRYPOINT ["bash", "start.sh"]