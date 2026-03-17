FROM python:3.13-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml uv.lock* ./
COPY src/ ./src/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv && \
    uv pip install --system -e .

# Expose port
EXPOSE 8000

# Run FastAPI application
CMD ["python", "-m", "uvicorn", "frcm.web:app", "--host", "0.0.0.0", "--port", "8000"]
