FROM python:3.13.2-alpine3.21

# Set working directory inside container
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code (including manage.py, core, huduku_ui, etc.)
COPY . .

# Run Django on port 8000 (matches docker-compose 8002:8000)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]