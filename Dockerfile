FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create directories for runtime data
RUN mkdir -p data history memory plans

# Run as non-root user
RUN useradd -m -r keyzbot && chown -R keyzbot:keyzbot /app
USER keyzbot

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/api/config')" || exit 1

CMD ["python3", "web/server.py"]
