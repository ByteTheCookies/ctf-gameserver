FROM debian:12-slim

ENV DEBIAN_FRONTEND=noninteractive
ENV DOCKER_TLS_CERTDIR=

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates curl iptables iproute2 uidmap tini docker.io openssh-server \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /run/sshd /etc/ssh/sshd_config.d /etc/vulnbox \
    && printf '%s\n' \
       'PasswordAuthentication yes' \
       'PermitRootLogin yes' \
       'ChallengeResponseAuthentication no' \
       'UsePAM yes' \
       > /etc/ssh/sshd_config.d/99-vulnbox.conf

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

VOLUME ["/var/lib/docker"]

ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
CMD ["bash"]
