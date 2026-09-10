# ---- Production image for SecureStock (waitress WSGI) ----
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim

RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/install/bin:$PATH" \
    PYTHONPATH="/app"

COPY --from=builder /install /install

# Copy application code (excluding secrets, tests and docs)
COPY app ./app
COPY migrations ./migrations
COPY config.py run.py seed.py serve.py wsgi.py ./
COPY requirements.txt ./

# Non-root, least-privilege runtime
RUN mkdir -p /app/instance /app/uploads && chown -R appuser:appuser /app
USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5000/login')" || exit 1

CMD ["python", "serve.py"]