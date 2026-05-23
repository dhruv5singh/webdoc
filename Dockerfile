FROM python:3.11-slim

RUN apt-get update && apt-get install -y nginx apache2-utils && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Allow selection of service mode: 'api' (gunicorn) or 'ui' (streamlit)
ENV SERVICE=api

# Expose both ports. API runs on 5000 by default; Streamlit uses 8501
EXPOSE 5000 8501

# Entrypoint: choose service based on SERVICE env var
CMD if [ "$SERVICE" = "ui" ]; then \
			streamlit run app.py --server.port ${PORT} --server.address 0.0.0.0; \
		else \
			exec gunicorn --bind 0.0.0.0:${PORT:-5000} api:app; \
		fi