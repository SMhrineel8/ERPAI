# Use Python 3.11 (more stable than 3.12)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies first
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Python dependencies with verbose output
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# ✅ Fix PYTHONPATH so that 'ai' inside backend is accessible
ENV PYTHONPATH="/app"

# Set unbuffered mode for logging
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check (optional for Render)
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ✅ RUN THE CORRECT ENTRYPOINT
CMD ["uvicorn", "ai.erp.copilot.main:app", "--host", "0.0.0.0", "--port", "8000"]
