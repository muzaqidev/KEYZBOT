FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create directories for runtime data
RUN mkdir -p data history memory plans

EXPOSE 8080

CMD ["python3", "web/server.py"]
