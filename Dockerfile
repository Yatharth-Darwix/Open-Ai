# Stage 1: Build Frontend
FROM node:18-slim as frontend-build
WORKDIR /app/frontend
COPY frontend/package.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Backend & Runtime
FROM python:3.9-slim
WORKDIR /app/backend

# Install system dependencies if any (usually none for this stack)
# RUN apt-get update && apt-get install -y ...

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy Backend Code
COPY backend/ ./

# Copy Frontend Build from Stage 1
COPY --from=frontend-build /app/frontend/build ../frontend/build

# Expose Port (FastAPI default is 8000, but Cloud Run expects $PORT or 8080)
ENV PORT=8080
EXPOSE 8080

# Command to run
# We use uvicorn to run the app, binding to 0.0.0.0 and the PORT env var
CMD sh -c "uvicorn main:app --host 0.0.0.0 --port $PORT"
