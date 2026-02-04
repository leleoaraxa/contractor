FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Copy project metadata AND package sources before editable install
COPY pyproject.toml /app/pyproject.toml
COPY app /app/app

RUN pip install --upgrade pip \
  && pip install -e ".[dev]"

# Copy tests and configs
COPY tests /app/tests
COPY pytest.ini /app/pytest.ini

CMD ["pytest", "-q"]
