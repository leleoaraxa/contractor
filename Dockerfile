FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt pyproject.toml /app/
RUN pip install --no-cache-dir -U pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN pip install --no-cache-dir --no-deps -e .
