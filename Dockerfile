FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    ca-certificates \
    curl \
    iputils-ping \
    libpq-dev \
    unzip \
 && rm -rf /var/lib/apt/lists/*

COPY LICENSE.txt README.md pyproject.toml /app/
COPY scripts /app/scripts
COPY src /app/src
COPY examples /app/examples

RUN curl -fsSL https://raw.githubusercontent.com/datasets/country-list/master/data.csv \
    -o /app/src/ctf_gameserver/web/registration/countries.csv
RUN mkdir -p /app/src/ctf_gameserver/web/static/ext \
 && curl -fsSL https://code.jquery.com/jquery-3.6.0.min.js \
    -o /app/src/ctf_gameserver/web/static/ext/jquery.min.js \
 && curl -fsSL https://github.com/twbs/bootstrap/releases/download/v5.3.7/bootstrap-5.3.7-dist.zip \
    -o /tmp/bootstrap.zip \
 && unzip -q /tmp/bootstrap.zip -d /tmp \
 && mv /tmp/bootstrap-5.3.7-dist /app/src/ctf_gameserver/web/static/ext/bootstrap \
 && curl -fsSL https://use.fontawesome.com/releases/v7.0.0/fontawesome-free-7.0.0-web.zip \
    -o /tmp/fontawesome-free.zip \
 && unzip -q /tmp/fontawesome-free.zip -d /tmp \
 && mv /tmp/fontawesome-free-7.0.0-web /app/src/ctf_gameserver/web/static/ext/fontawesome-free \
 && rm -rf /tmp/bootstrap.zip /tmp/fontawesome-free.zip /tmp/bootstrap-5.3.7-dist \
    /tmp/fontawesome-free-7.0.0-web

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -e . \
 && pip install --no-cache-dir gunicorn psycopg2-binary

COPY docker/web-settings /app/docker/web-settings
