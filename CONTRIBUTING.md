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
./scripts/install.sh
```

## 🚀 Run example API

The API will be automatically reloaded when the code is changed:

```sh
./scripts/dev.sh
```

Access the YASGUI interface at http://localhost:8000

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

## 🏷️ New release process

The deployment of new releases is done automatically by a GitHub Action workflow when a new release is created on GitHub. To release a new version:

1. Make sure the `PYPI_TOKEN` secret has been defined in the GitHub repository (in Settings > Secrets > Actions). You can get an API token from PyPI at [pypi.org/manage/account](https://pypi.org/manage/account).

2. Increment the `version` number following semantic versioning, select between `fix`, `minor`, or `major`:

   ```sh
   uvx hatch version fix
   ```

3. Commit the new version, and **create a new release on GitHub**, which will automatically trigger the workflow to publish the new release to [PyPI](https://pypi.org/project/rdflib-endpoint/).

You can also manually trigger the workflow from the Actions tab in your GitHub repository webpage if needed.
