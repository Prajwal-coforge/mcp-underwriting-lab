FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY pyproject.toml ./
COPY src ./src
COPY tests ./tests
COPY corpus ./corpus
COPY scripts ./scripts
COPY docs ./docs

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

CMD ["pytest", "-q"]
