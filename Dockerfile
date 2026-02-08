# Base Image
FROM python:3.9-slim

# Working Directory
WORKDIR /app

# System Dependencies (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy Requirements
COPY requirements.txt .

# Install Python Dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Application Code
COPY . .

# Environment Variables
ENV API_URL="http://127.0.0.1:8000"
# Revert to standard port for cloud (Render often sets PORT, handled in entrypoint)
ENV PORT=8501 

# Expose Streamlit Port
EXPOSE 8501

# Entrypoint Script
COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

# Run
CMD ["./entrypoint.sh"]
