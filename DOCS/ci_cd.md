## CI/CD Workflow Documentation

### What we built
- **Workflow file**: `.github/workflows/ci.yml`
- **Purpose**: Run Django test suite automatically on pushes/PRs and on-demand, using SQLite and no external credentials.

### Why we built it this way
- **No secrets required**: Uses SQLite (default in `settings.py` when `PG*` env vars are absent) and sets a harmless `OPENAI_API_KEY=dummy` to keep optional LLM imports from failing.
- **Fast installs**: Installs the slimmer set of dependencies from `resources/requirements.txt` to keep CI quick and deterministic.
- **Matches runtime**: Uses Python 3.10 per `runtime.txt`.

### How it works (high level)
- Triggers on `push`, `pull_request`, and manual `workflow_dispatch`.
- Runs on `ubuntu-latest`:
  1. Checkout repository
  2. Set up Python `3.10`
  3. Cache and install dependencies from `resources/requirements.txt`
  4. Execute Django tests via `python manage.py test -v 2 --noinput`
- Environment:
  - `OPENAI_API_KEY=dummy` (prevents client init errors; no real credentials)
  - No `PG*` envs → Django uses SQLite automatically

### What tests are run
- The default Django test discovery runs all `tests.py`/`tests/` in installed apps. In this repo, that includes (not exhaustive):
  - `twenty_one_tech_pocs/maintenance_assistant/tests.py`
  - `twenty_one_tech_pocs/service_manuals_assistant/tests.py`
  - `twenty_one_tech_pocs/safety_procedure_assistant/tests.py`

### How to run it locally
Prerequisites: Docker running and user can access Docker socket; `act` installed.

Commands (from repo root):
```bash
act                 # run default event locally
act -j tests        # run only the tests job
act push            # simulate a push event

# If the default image is unavailable, map ubuntu-latest to a compatible image
act -P ubuntu-latest=catthehacker/ubuntu:act-latest
```

If you see `permission denied` for Docker:
```bash
sudo systemctl start docker
sudo usermod -aG docker $USER
newgrp docker
docker ps
```

### File references
- Workflow: `.github/workflows/ci.yml`
- Python runtime: `runtime.txt`
- CI dependency set: `resources/requirements.txt`
- Django settings (SQLite fallback, no `PG*`): `twenty_one_tech_pocs/twenty_one_tech_pocs/settings.py`

### Extending the workflow (optional)
- Add linting (flake8/ruff) and formatting checks.
- Generate coverage (`coverage.py`) and upload as an artifact.
- Add a separate job to install the full `requirements.txt` if/when those heavier deps are needed in tests.
