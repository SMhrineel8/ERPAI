# Use an official Python runtime
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy all files from your repo
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV PYTHONPATH="${PYTHONPATH}:/app"

# Expose port
EXPOSE 8000

# Run the app
CMD ["python", "main.py"]
