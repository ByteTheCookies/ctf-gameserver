FROM debian:bookworm-slim

RUN apt update && apt install -y socat

WORKDIR /app
COPY vulnify .

RUN mkdir data
RUN chmod +x ./vulnify

EXPOSE 1337

CMD ["socat", "-d", "TCP-LISTEN:1337,reuseaddr,fork", "EXEC:/app/vulnify"]
