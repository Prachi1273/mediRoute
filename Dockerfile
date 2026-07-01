# MediRoute — Cloud Run deployment
# Day 1 + Day 5 concept: deployability via Cloud Run

FROM python:3.11-slim

WORKDIR /app

# Install system deps for pdfplumber
RUN apt-get update && apt-get install -y \
    libpoppler-cpp-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user (security best practice — Day 4)
RUN useradd -m -u 1000 mediRoute && chown -R mediRoute:mediRoute /app
USER mediRoute

# Cloud Run uses PORT env variable
ENV PORT=8080
EXPOSE 8080

CMD ["python", "server.py"]
