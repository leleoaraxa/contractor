FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt pyproject.toml /app/
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . /app
