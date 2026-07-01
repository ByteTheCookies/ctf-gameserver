FROM python:3-slim

RUN apt update && apt install -y socat

WORKDIR /app
COPY server.py crypto.py fish.py .

RUN chmod +x /app/server.py

EXPOSE 2345

CMD ["socat", "-d", "TCP-LISTEN:2345,reuseaddr,fork", "EXEC:/app/server.py"]
