# Minimal, pinned base for reproducibility.
FROM python:3.12-slim

# Avoid interactive prompts, ensure stdout is unbuffered for live logs.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install deps first for layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project.
COPY . .

# Default: run the smoke tests. Override in compose / CLI for the matrix run.
CMD ["pytest", "-q"]
