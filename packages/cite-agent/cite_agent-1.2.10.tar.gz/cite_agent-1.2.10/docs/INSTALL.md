# Installing the Nocturnal Archive Beta Agent

This guide keeps the beta footprint lean while giving operators a repeatable install flow.

## 1. Prerequisites

- Python 3.9 – 3.12 (CPython).
- A Groq API key with access to the llama-3 series models.
- Optional: FinSight and Archive service endpoints if you are running the private APIs.

## 2. Create an isolated environment

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## 3. Install the package

The beta release ships as a standard Python package. Install from the project root:

```bash
pip install .
```

For development or CI usage install the additional tooling:

```bash
pip install -r requirements-dev.txt
```

## 4. Configure credentials

Run the setup wizard to sign in with your academic account:

```bash
nocturnal --setup
```

The wizard verifies your institution-issued email, provisions credentials from the control plane, and stores them under `~/.nocturnal_archive/`. Manual Groq API keys are no longer required. For headless environments set `NOCTURNAL_ACCOUNT_EMAIL`, `NOCTURNAL_AUTH_TOKEN`, and `GROQ_API_KEY` as environment variables before launching.

## 5. Launch the CLI

Interactive mode:

```bash
nocturnal
```

Run a single query:

```bash
nocturnal "Summarise Apple Q2 earnings"
```

Setup wizard:

```bash
nocturnal --setup
```

## 6. Upgrading

```bash
python -m pip install --upgrade nocturnal-archive
nocturnal-update --status
```

The updater checks PyPI for signed releases and applies them in-place.

## 7. Running the regression suite

```bash
pytest tests/enhanced -q
```

The test module includes shell-safety, finance, and concurrency guards required for beta sign-off.

## 8. Shipping the wheel

```bash
python -m build  # requires `pip install build`
ls dist/
```

Publish with Twine or your artifact store once the release candidate passes validation.
