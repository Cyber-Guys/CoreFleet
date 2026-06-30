FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir eclipse-zenoh

COPY subscriber.py /app/subscriber.py

ENTRYPOINT ["python", "/app/subscriber.py"]