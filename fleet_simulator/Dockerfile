# Build context = repo root (see docker-compose.yaml) so the shared `corefleet`
# package can be copied alongside the simulator.
FROM python:3.13-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY corefleet /app/corefleet
COPY fleet_simulator /app/fleet_simulator

ENTRYPOINT ["python", "-m", "fleet_simulator"]
