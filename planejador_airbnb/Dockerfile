FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install -r requirements.txt

COPY .. .

RUN python manage.py collectstatic --no-input

CMD ["gunicorn", "planejador_airbnb.wsgi:application", "--bind", "0.0.0.0:8000"]