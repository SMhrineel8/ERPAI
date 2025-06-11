# Use Python 3.11 (more stable than 3.12)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies first
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies with verbose output
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy entire application code into /app
COPY . .

# ✅ Fix PYTHONPATH so that 'ai_erp_copilot' is on Python’s import path
ENV PYTHONPATH="/app"

# Set unbuffered mode for logs
ENV PYTHONUNBUFFERED=1

# Expose the FastAPI port
EXPOSE 8000

# Health check (optional)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ✅ Run uvicorn pointing to the correct module path
#    'ai_erp_copilot.main:app' means:
#       look in /app/ai_erp_copilot/main.py for FastAPI app.
CMD ["uvicorn", "ai_erp_copilot.main:app", "--host", "0.0.0.0", "--port", "8000"]
