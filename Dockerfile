FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    STORY_DATA_DIR=/tmp/aioclips-stories

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg fontconfig fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend/app /app/app
RUN mkdir -p /tmp/aioclips-stories \
    && useradd -u 10001 -m studio \
    && chown -R studio:studio /tmp/aioclips-stories /app
USER studio

EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app.original_api:app --host 0.0.0.0 --port ${PORT:-8000}"]
