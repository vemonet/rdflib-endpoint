FROM python:3.8

# cf. https://fastapi.tiangolo.com/deployment/docker/
COPY . /app/

RUN pip install -r /app/requirements.txt

EXPOSE 8000

ENTRYPOINT ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]