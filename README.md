A SPARQL endpoint to serve machine learning models, or any other logic implemented in Python.

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the server from your terminal:

```bash
uvicorn main:app --reload
```

Run with docker:

```bash
docker-compose up -d --build
```

