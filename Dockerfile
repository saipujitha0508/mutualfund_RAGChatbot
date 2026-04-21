FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements-deploy.txt .
RUN pip install --no-cache-dir -r requirements-deploy.txt

# Copy application files
COPY runtime/ ./runtime/
COPY data/sources.csv ./data/

# Create necessary directories
RUN mkdir -p data/chroma data/raw data/normalized data/chunked data/embedded data/structured

# Expose port
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Set environment variables
ENV PORT=7860
ENV API_HOST=0.0.0.0

# Run the application
CMD ["python", "-m", "runtime.phase_9_api"]
