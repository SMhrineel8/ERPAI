# Use an official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy files
COPY backend/ ./backend/

# Set env
ENV PYTHONPATH="${PYTHONPATH}:/app/backend"

# Install dependencies
RUN pip install --no-cache-dir -r backend/requirements.txt

# Expose port
EXPOSE 8000

# Run the app
CMD ["uvicorn", "backend.ai.main:app", "--host", "0.0.0.0", "--port", "8000"]
