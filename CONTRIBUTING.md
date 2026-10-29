# Contributing

## Workflow

- Branch from the latest `main` using `feat/<scope>`, `fix/<scope>`, `docs/<scope>` or `chore/<scope>`.
- Keep each pull request to one coherent change. Ask for review on modeling/encoding changes.
- Use a clear commit subject, for example `feat(maxsat): add binary peak model`.
- Do not commit `.venv`, benchmark downloads, license files, credentials, or unreproducible result dumps.

## Local checks

Install development tools once with `uv sync --locked --extra dev`, then run:

```powershell
uv run salb3pm smoke
uv run ruff format --check .
uv run ruff check .
```

Once the test suite has been added, run it with `uv run pytest` before opening a pull request. For a model change, the pull request should state the paper equation/page, model assumptions, instance/result schema impact, command used, observed status and limitations. Add or update focused tests and an independent validation where appropriate.
