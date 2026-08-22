FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY ./src ./src
COPY ./alembic.ini .
COPY ./alembic ./alembic
# Apply migrations before serving. Base.metadata.create_all() in main.py's startup
# event stays as a safety net for tables migrations don't yet own, but the schema
# (indexes, constraints, the role column) is only correct if migrations actually run.
CMD alembic upgrade head && uvicorn src.main:app --host 0.0.0.0 --port 8000
