FROM python:3.13.2-alpine3.21

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ /app/

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]