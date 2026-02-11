# Example Dockerfile for GeoHealth LGA Project
FROM python:3.11-slim-bullseye

WORKDIR /app

# Security: update/upgrade system packages
RUN apt-get update && apt-get upgrade -y && apt-get clean

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
