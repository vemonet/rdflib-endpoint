# 🛠️ Contributing

This section is for if you want to run the package in development, and get involved by making a code contribution.

> Requirements: [`uv`](https://docs.astral.sh/uv/getting-started/installation/) to easily handle scripts and virtual environments.

## 📥️ Clone

Clone the repository:

```sh
git clone https://github.com/vemonet/rdflib-endpoint
cd rdflib-endpoint
```

## 🪝 Install pre-commit hooks

```sh
uv run --all-extras pre-commit install
```

## 🚀 Run example API

Run the example SPARQL endpoint with YASGUI on http://localhost:8000, it will be automatically reloaded when the code is changed:

```sh
./scripts/dev.sh
```

## ☑️ Run tests

Make sure the existing tests still work by running the test suite and linting checks. Note that any pull requests to the fairworkflows repository on github will automatically trigger running of the test suite:

```sh
uv run pytest
```

To display all `print()`:

```sh
uv run pytest -s
```

## 🧹 Code formatting

The code will be automatically formatted when you commit your changes using `pre-commit`. But you can also run the script to format the code yourself:

```sh
./scripts/fmt.sh
```

### ♻️ Reset the environment

Upgrade `uv`:

```sh
uv self update
```

Clean `uv` cache:

```sh
uv cache clean
```

## 🏷️ Release process

> [!IMPORTANT]
>
> Get a PyPI API token at [pypi.org/manage/account](https://pypi.org/manage/account).

Run the release script providing the version bump: `fix`, `minor`, or `major`

```sh
./scripts/release.sh fix
```

> [!NOTE]
>
> This will generate the changelog, commit the new version and changelog, create a tag and push the tag, which will trigger the creation of a new release on GitHub.
