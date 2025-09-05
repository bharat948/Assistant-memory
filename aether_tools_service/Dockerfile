FROM python:3.11-slim

WORKDIR /app

COPY ./aether_tools_service/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY ./aether_tools_service/app /app/aether_tools_service/app
COPY ./aether_agent/agent/examples /app/aether_agent/agent/examples

ENV PYTHONPATH=/app

CMD ["uvicorn", "aether_tools_service.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
