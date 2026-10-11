FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY backend/requirements.lock backend/requirements-dev.lock ./
COPY backend/apps ./apps
COPY backend/config ./config
COPY backend/manage.py ./

RUN pip install --no-cache-dir --require-hashes -r requirements.lock \
    && addgroup --system app \
    && adduser --system --ingroup app app \
    && chown -R app:app /app

USER app
EXPOSE 8000
CMD ["sh", "-c", "exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-2} --timeout 60 --access-logfile - --error-logfile -"]
