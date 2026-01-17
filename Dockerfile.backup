# Simple, bulletproof Python backend for Railway
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code only
COPY backend ./backend
COPY app_wrapper.py ./main.py

# Unbuffered logging
ENV PYTHONUNBUFFERED=1

# Port - default to 8000 if PORT env var not set
ENV PORT=8000
EXPOSE 8000

# Start with PORT environment variable
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
