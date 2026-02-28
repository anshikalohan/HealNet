FROM python:3.11-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
# Filter out macos specific requirements for linux container
RUN grep -v "tensorflow-macos" requirements.txt | grep -v "tensorflow-metal" > req_linux.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r req_linux.txt

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "run.py"]
