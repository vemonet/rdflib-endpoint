uv run --all-extras pytest --cov-report html
# python -c 'import webbrowser; webbrowser.open(\"http://0.0.0.0:3000\")'
uv run python -m http.server 3000 --directory ./htmlcov
