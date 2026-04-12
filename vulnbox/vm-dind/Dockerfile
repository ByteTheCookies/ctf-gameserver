FROM debian:12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV DOCKER_TLS_CERTDIR=

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates curl iptables iproute2 uidmap tini docker.io docker-compose openssh-server \
    && mkdir -p /usr/local/lib/docker/cli-plugins \
    && printf '%s\n' '#!/bin/sh' 'exec /usr/bin/docker-compose "$@"' > /usr/local/lib/docker/cli-plugins/docker-compose \
    && chmod +x /usr/local/lib/docker/cli-plugins/docker-compose \
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
RUN chmod +x /usr/local/bin/entrypoint.sh
RUN chmod +x /root/CCForms/deploy.sh
RUN docker compose version >/dev/null

VOLUME ["/var/lib/docker"]

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
CMD ["sleep", "infinity"]
