FROM debian:12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV DOCKER_TLS_CERTDIR=

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates curl iptables iproute2 uidmap tini docker.io openssh-server \
    && (apt-get install -y --no-install-recommends docker-compose-plugin || true) \
    && if ! docker compose version >/dev/null 2>&1; then \
         arch="$(dpkg --print-architecture)"; \
         case "$arch" in \
           amd64) compose_arch="x86_64" ;; \
           arm64) compose_arch="aarch64" ;; \
           *) echo "Unsupported architecture for compose plugin: $arch" >&2; exit 1 ;; \
         esac; \
         mkdir -p /usr/libexec/docker/cli-plugins; \
         curl -fsSL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-${compose_arch}" \
           -o /usr/libexec/docker/cli-plugins/docker-compose; \
         chmod +x /usr/libexec/docker/cli-plugins/docker-compose; \
       fi \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends tcpdump rsync python3 zip \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /run/sshd /etc/ssh/sshd_config.d /etc/vulnbox \
    && printf '%s\n' \
       'PasswordAuthentication yes' \
       'PermitRootLogin yes' \
       'ChallengeResponseAuthentication no' \
       'UsePAM yes' \
       > /etc/ssh/sshd_config.d/99-vulnbox.conf

COPY vm-dind/entrypoint.sh /usr/local/bin/entrypoint.sh
COPY services/CCForms /root/CCForms
COPY services/vulnify /root/vulnify

RUN chmod +x /usr/local/bin/entrypoint.sh
RUN chmod +x /root/CCForms/deploy.sh

VOLUME ["/var/lib/docker"]

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
CMD ["sleep", "infinity"]
