FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY graph_rag_api/requirements.txt ./graph_rag_api/
RUN pip install --no-cache-dir -r graph_rag_api/requirements.txt

# Copy application code and data
COPY graph_rag_api/ ./graph_rag_api/
COPY complete_graph.json ./
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY graph/ ./graph/

# Expose API port
EXPOSE 8000

# Run the API
WORKDIR /app/graph_rag_api
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

