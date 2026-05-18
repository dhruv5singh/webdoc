FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Allow the PORT env var to be set by the runtime (Render uses $PORT)
ENV PORT=8501

EXPOSE ${PORT}

# Use shell form so environment variables like $PORT are expanded
CMD streamlit run app.py --server.port $PORT --server.address 0.0.0.0