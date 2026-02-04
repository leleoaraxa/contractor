FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
  && rm -rf /var/lib/apt/lists/*

# Offline wheelhouse (no network). Populate vendor/wheels/ in the repo.
ENV PIP_NO_INDEX=1 \
    PIP_FIND_LINKS=/app/vendor/wheels

# Copy project metadata AND package sources before editable install
COPY pyproject.toml /app/pyproject.toml
COPY app /app/app
COPY vendor /app/vendor

# Install deps from local wheelhouse only.
# Note: runtime extras are required for /execute FastAPI tests.
RUN pip install --upgrade pip \
  && pip install --no-index --find-links /app/vendor/wheels "setuptools>=68" wheel \
  && pip install --no-index --find-links /app/vendor/wheels -e ".[dev,runtime]"

# Copy tests and configs
COPY tests /app/tests
COPY pytest.ini /app/pytest.ini

CMD ["pytest", "-q"]
