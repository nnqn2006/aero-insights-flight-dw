# AERO INSIGHTS | Flight DW 2025 — snapshot-mode dashboard image (no database connection at runtime)
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8050 WEB_CONCURRENCY=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY 02_PYTHON_SOURCE/ 02_PYTHON_SOURCE/
COPY 03_EXPORT_DATA/ 03_EXPORT_DATA/
COPY 04_CSS/ 04_CSS/
RUN useradd --create-home appuser
USER appuser
EXPOSE 8050
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
  CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"8050\")}/health', timeout=4)" || exit 1
CMD ["sh", "-c", "gunicorn --chdir 02_PYTHON_SOURCE app:server --bind 0.0.0.0:${PORT} --workers ${WEB_CONCURRENCY} --threads 4 --timeout 120"]
