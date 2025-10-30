FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . /app/mcp_server/

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8001

# Run the application
CMD ["uvicorn", "mcp_server.src.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
