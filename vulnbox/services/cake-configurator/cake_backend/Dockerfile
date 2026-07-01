FROM cake_backend_deps


WORKDIR /app
COPY src/ .
RUN chmod +x ./gixfix.py
RUN make

CMD ["socat", "TCP6-LISTEN:4321,reuseaddr,fork", "EXEC:env LINES=24 COLUMNS=80 /app/CAKECONF,pty,raw,echo=0"]
