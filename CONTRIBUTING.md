# 🛠️ Contributing

This section is for if you want to run the package in development, and get involved by making a code contribution.

## 📥️ Clone

Clone the repository:

```bash
git clone https://github.com/vemonet/rdflib-endpoint
cd rdflib-endpoint
```

## 🐣 Install dependencies

Install [Hatch](https://hatch.pypa.io), this will automatically handle virtual environments and make sure all dependencies are installed when you run a script in the project:

```bash
pipx install hatch
```

Install the dependencies in a local virtual environment (running this command is optional as `hatch` will automatically install and synchronize dependencies each time you run a script with `hatch run`):

```bash
hatch -v env create
```

## 🚀 Run example API

The API will be automatically reloaded when the code is changed:

```bash
hatch run dev
```

Access the YASGUI interface at http://localhost:8000

## ☑️ Run tests

Make sure the existing tests still work by running the test suite and linting checks. Note that any pull requests to the fairworkflows repository on github will automatically trigger running of the test suite:

```bash
hatch run test
```

To display all `print()`:

```bash
hatch run test -s
```

You can also run the tests on multiple python versions:

```bash
hatch run all:test
```

## 🧹 Code formatting

The code will be automatically formatted when you commit your changes using `pre-commit`. But you can also run the script to format the code yourself:

```
hatch run fmt
```

## ♻️ Reset the environment

In case you are facing issues with dependencies not updating properly you can easily reset the virtual environment with:

```bash
hatch env prune
```

## 🏷️ New release process

The deployment of new releases is done automatically by a GitHub Action workflow when a new release is created on GitHub. To release a new version:

1. Make sure the `PYPI_TOKEN` secret has been defined in the GitHub repository (in Settings > Secrets > Actions). You can get an API token from PyPI at [pypi.org/manage/account](https://pypi.org/manage/account).

2. Increment the `version` number following semantic versioning, select between `fix`, `minor`, or `major`:

   ```bash
   hatch version fix
   ```

3. Commit the new version, and **create a new release on GitHub**, which will automatically trigger the workflow to publish the new release to [PyPI](https://pypi.org/project/rdflib-endpoint/).

You can also manually trigger the workflow from the Actions tab in your GitHub repository webpage if needed.
