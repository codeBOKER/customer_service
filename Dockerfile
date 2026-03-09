# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables for Hugging Face Spaces (can be overridden for local development)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    HF_HOME=/app/cache \
    TRANSFORMERS_CACHE=/app/cache

# Install system dependencies including curl for health check
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all application code
COPY . .

# Create cache directory for Hugging Face models
RUN mkdir -p /app/cache && chmod 777 /app/cache

# Expose port (default 8000 for local, can be set to 7860 for Hugging Face Spaces)
EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/ || exit 1

# Run the application (uses PORT environment variable)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${PORT}"]
