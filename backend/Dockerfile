FROM python:3.12-slim

# The default image is production-shaped. Build with --build-arg
# INSTALL_EXTRAS=dev for the test-capable development image used by Compose.
ARG INSTALL_EXTRAS=

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY requirements.lock requirements-dev.lock ./
COPY apps ./apps
COPY config ./config
COPY manage.py ./
COPY tests ./tests

RUN if [ -n "$INSTALL_EXTRAS" ]; then \
      pip install --no-cache-dir --require-hashes -r "requirements-${INSTALL_EXTRAS}.lock"; \
    else \
      pip install --no-cache-dir --require-hashes -r requirements.lock; \
    fi

RUN addgroup --system app && adduser --system --ingroup app app \
    && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["sh", "-c", "exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --timeout 60 --access-logfile - --access-logformat '%(s)s %(L)s' --error-logfile -"]
