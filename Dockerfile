FROM node:18-alpine

WORKDIR /app

# Install Python and dependencies
RUN apk add --no-cache python3 py3-pip py3-psycopg2

# Copy backend requirements
COPY backend/requirements.txt ./backend/

# Install Python dependencies (use --break-system-packages for Alpine)
RUN pip3 install --no-cache-dir --break-system-packages -r ./backend/requirements.txt

# Copy package files for Node
COPY package*.json ./

# Install Node dependencies
RUN npm install && npm install --save express http-proxy-middleware

# Copy entire application
COPY . .

# Build frontend
RUN npm run build

# Expose ports
EXPOSE 3000 8000

# Health check for frontend
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

# Start both backend and frontend
CMD sh -c 'python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 &' && node server.js
