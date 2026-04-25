FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

EXPOSE 5100

CMD ["sh", "-c", "gunicorn --workers 2 --threads 4 --timeout 120 --bind 0.0.0.0:${PORT:-5100} app:application"]
