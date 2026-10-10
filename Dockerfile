#
# Dockerfile
# zifnab06/zifb.in
#

# Base Image
FROM python:3.15-rc-slim

# Environment setup
WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt

# Application installation
COPY . /app

# Runtime
EXPOSE 8080/tcp
ENTRYPOINT gunicorn -b 0.0.0.0:8080 -w 4 app:app
