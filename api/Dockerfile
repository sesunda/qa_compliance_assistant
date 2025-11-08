FROM python:3.11-slim

WORKDIR /app

# Install system dependencies in one layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir --upgrade pip

# Copy ONLY requirements first (better caching - only rebuilds if requirements change)
COPY requirements.txt /app/requirements.txt

# Install dependencies (this layer will be cached if requirements.txt doesn't change)
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code LAST (changes most frequently)
COPY . /app/api/

# Copy startup script and ensure it's executable
COPY startup.sh /app/startup.sh
RUN chmod +x /app/startup.sh

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Lightweight health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application with automatic migrations
# Using exec form ensures signals are properly handled
ENTRYPOINT ["/bin/bash"]
CMD ["/app/startup.sh"]
