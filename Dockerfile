# Hosted demo of Nafas (synthetic personas only; no API key, so coach notes come from the offline template).
# State is held in process memory per browser session, so this must run as ONE process (threads are fine).
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn==23.0.0

COPY nafas ./nafas
COPY data ./data
COPY run.py LICENSE README.md ./

RUN useradd --create-home nafas
USER nafas

EXPOSE 8080
CMD ["gunicorn", "--workers", "1", "--threads", "8", "--timeout", "120", "--bind", "0.0.0.0:8080", "nafas.server:app"]
