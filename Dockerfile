FROM python:3.8

WORKDIR /app

COPY requirements.txt /app

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT gunicorn -b 0.0.0.0:8080 -w 4 app:app
