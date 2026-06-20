FROM python:3.12-slim

# Don't buffer stdout/stderr; don't write .pyc files.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install dependencies first so the layer is cached across code changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code.
COPY . .

# Pastes are written to /app/pastes (the create_app default, relative to WORKDIR).
# Mount a volume here to persist them across container restarts.
EXPOSE 5000

# Serve with gunicorn; `app` is the module-level Flask instance in index.py.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "index:app"]
