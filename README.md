A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python.

Built with FastAPI and RDFLib.

## Install and run

1. Install dependencies

```bash
pip install -r requirements.txt
```

2. Run the server on http://localhost:8000

```bash
uvicorn main:app --reload --app-dir app
```

## Or run with docker

```bash
docker-compose up -d --build
```

