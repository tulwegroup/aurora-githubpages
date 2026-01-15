# Simple, bulletproof Python backend for Railway
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend ./backend
COPY app_wrapper.py ./main.py
COPY config.py .
COPY constants.ts .
COPY types.ts .
COPY models.py .

# Unbuffered logging
ENV PYTHONUNBUFFERED=1

# Port
EXPOSE 8000

# Start - dead simple
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
