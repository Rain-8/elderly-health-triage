FROM python:3.11-slim

WORKDIR /app

# Install curl first
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Download AlloyDB Auth Proxy
RUN curl -o /app/alloydb-auth-proxy https://dl.google.com/cloudsql/alloydb-auth-proxy.linux.x86_64 && \
    chmod +x /app/alloydb-auth-proxy

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

# Start auth proxy in background, then start the app
CMD ["sh", "-c", "/app/alloydb-auth-proxy projects/nice-tiger-439903-a8/locations/us-central1/clusters/elderly-health-cluster/instances/primary-instance &  sleep 2 && uvicorn main:app --host 0.0.0.0 --port 8080"]