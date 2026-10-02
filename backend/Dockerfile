FROM python:3.12-slim

# The default image is production-shaped: only [project].dependencies are
# installed. Build with --build-arg INSTALL_EXTRAS=dev for the test-capable
# development image used by Compose, for example:
#   docker build --build-arg INSTALL_EXTRAS=dev -t htf-backend-dev .
ARG INSTALL_EXTRAS=

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml ./
COPY apps ./apps
COPY config ./config
COPY manage.py ./
COPY tests ./tests

RUN pip install --upgrade pip \
    && if [ -n "$INSTALL_EXTRAS" ]; then \
         pip install -e ".[$INSTALL_EXTRAS]"; \
       else \
         pip install -e .; \
       fi

RUN addgroup --system app && adduser --system --ingroup app app \
    && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
