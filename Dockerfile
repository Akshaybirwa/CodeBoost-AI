# syntax=docker/dockerfile:1
FROM node:20-alpine

WORKDIR /app

# Install dependencies first for better caching
COPY package.json package-lock.json ./
RUN npm ci

# Copy application source
COPY . .

# Expose Vite dev server port
EXPOSE 8080

# Run Vite dev server; host/port overridden via flags
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "8080"]