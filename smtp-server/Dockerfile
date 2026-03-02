FROM python:3.11-slim

WORKDIR /app

# Generate a self-signed cert for STARTTLS during build.
# The cert never leaves the container and is only used for in-Docker TLS.
RUN apt-get update && apt-get install -y --no-install-recommends openssl && \
    openssl req -x509 -newkey rsa:2048 \
        -keyout /app/key.pem -out /app/cert.pem \
        -days 3650 -nodes \
        -subj "/CN=smtp-server/O=Sharp Printer Emulator" 2>/dev/null && \
    apt-get remove -y openssl && apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

EXPOSE 587

CMD ["python", "server.py"]
