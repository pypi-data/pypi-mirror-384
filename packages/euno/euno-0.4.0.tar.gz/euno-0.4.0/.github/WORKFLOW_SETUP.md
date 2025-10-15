# GitHub Actions Workflow Status

You can add these badges to your README.md to show the current status of your workflows:

```markdown
![CI](https://github.com/euno-ai/euno-sdk/workflows/CI/badge.svg)
![Pre-commit](https://github.com/euno-ai/euno-sdk/workflows/Pre-commit/badge.svg)
![Publish](https://github.com/euno-ai/euno-sdk/workflows/Publish%20to%20PyPI/badge.svg)
```

## Workflow Files Created

1. **`.github/workflows/ci.yml`** - Main CI workflow
2. **`.github/workflows/pre-commit.yml`** - Pre-commit checks
3. **`.github/workflows/publish.yml`** - PyPI publishing
4. **`.github/ISSUE_TEMPLATE/bug_report.md`** - Bug report template
5. **`.github/ISSUE_TEMPLATE/feature_request.md`** - Feature request template
6. **`.github/pull_request_template.md`** - Pull request template

## Next Steps

1. **Add PyPI Token Secret:**
   - Go to repository Settings → Secrets and variables → Actions
   - Add `PYPI_TOKEN` with your PyPI API token

2. **Enable Codecov (Optional):**
   - Connect your repository to Codecov for coverage reports

3. **Test the Workflows:**
   - Create a test pull request to verify the CI workflow
   - Check that all checks pass

4. **Add Status Badges:**
   - Add the workflow status badges to your README.md
