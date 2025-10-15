# GitHub Actions Workflows

This repository includes several GitHub Actions workflows to ensure code quality and automate releases.

## Workflows

### 1. CI (`ci.yml`)
**Triggers:** Push to `main` branch, Pull requests to `main` branch

**What it does:**
- Runs tests on Python versions 3.8, 3.9, 3.10, 3.11, and 3.12
- Installs development dependencies
- Runs linting with flake8
- Runs type checking with mypy
- Runs tests with pytest and coverage
- Uploads coverage reports to Codecov
- Builds the package and validates it with twine

### 2. Pre-commit (`pre-commit.yml`)
**Triggers:** Push to `main` branch, Pull requests to `main` branch

**What it does:**
- Runs pre-commit hooks to ensure code formatting and quality
- Checks for trailing whitespace, end-of-file issues, YAML syntax, etc.
- Runs Black code formatting
- Runs flake8 linting
- Runs mypy type checking

### 3. Publish (`publish.yml`)
**Triggers:** When a new release is published

**What it does:**
- Builds the package
- Validates the package with twine
- Publishes to PyPI using the `PYPI_TOKEN` secret

## Setup Instructions

### For Repository Owners

1. **Add PyPI Token Secret:**
   - Go to your repository settings
   - Navigate to "Secrets and variables" → "Actions"
   - Add a new repository secret named `PYPI_TOKEN`
   - Set the value to your PyPI API token

2. **Enable Codecov (Optional):**
   - Connect your repository to Codecov
   - The workflow will automatically upload coverage reports

### For Contributors

1. **Install pre-commit hooks locally:**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

2. **Run tests locally:**
   ```bash
   make test
   ```

3. **Run linting locally:**
   ```bash
   make lint
   ```

## Workflow Status

You can view the status of all workflows in the "Actions" tab of your GitHub repository.

## Manual Workflow Triggers

You can also trigger workflows manually:
- Go to the "Actions" tab
- Select the workflow you want to run
- Click "Run workflow"

## Troubleshooting

### Common Issues

1. **Tests failing on specific Python versions:**
   - Check if your code is compatible with all supported Python versions
   - Update the `python-version` matrix in `ci.yml` if needed

2. **Pre-commit hooks failing:**
   - Run `pre-commit run --all-files` locally to fix issues
   - Commit the changes

3. **Publishing fails:**
   - Ensure `PYPI_TOKEN` secret is correctly set
   - Check that the token has the necessary permissions
   - Verify the package name is available on PyPI

### Getting Help

If you encounter issues with the workflows:
1. Check the workflow logs in the "Actions" tab
2. Ensure all dependencies are properly specified in `requirements-dev.txt`
3. Verify that your code follows the project's coding standards
