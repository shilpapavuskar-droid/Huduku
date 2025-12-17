# Use official Python image
FROM python:3.13.2-alpine3.21

# Set working directory
WORKDIR ./app

#Copy project files
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
