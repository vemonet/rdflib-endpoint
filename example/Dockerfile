FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8
# FROM python:3.8

COPY ./requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# cf. https://fastapi.tiangolo.com/deployment/docker/
COPY ./app /app

# EXPOSE 80
# ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]