# Publishing Nocturnal Archive to PyPI

Use this runbook to push the package to either TestPyPI or the public index.

## 1. Accounts & API tokens
1. Create a PyPI account at [pypi.org](https://pypi.org/account/register/).
2. Verify email + enable 2FA (mandatory for uploads).
3. Create a PyPI **API token** with scope `Entire account` (or project-specific once the name exists).
   - Copy the token; it starts with `pypi-`.
4. Optional: repeat the same steps on [TestPyPI](https://test.pypi.org/account/register/) to dry-run releases.

## 2. Local configuration
Populate `~/.pypirc` so build tooling knows where to upload:

```
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
  username = __token__
  password = pypi-XXXXXXXXXXXXXXXXXXXX

[testpypi]
  username = __token__
  password = pypi-XXXXXXXXXXXXXXXXXXXX
```

Alternatively, export the credentials per shell session:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-XXXXXXXXXXXXXXXXXXXX
```

## 3. Build artifacts
From the repo root:

```bash
python -m pip install --upgrade pip build twine
python -m build   # creates dist/*.whl and dist/*.tar.gz
```

Sanity check the wheel contents:

```bash
unzip -l dist/nocturnal_archive-*.whl
```

## 4. Test upload
Push to TestPyPI first:

```bash
twine upload --repository testpypi dist/*
```

Verify install in a clean venv:

```bash
python -m venv /tmp/nocturnal-test
source /tmp/nocturnal-test/bin/activate
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple nocturnal-archive
nocturnal --version
```

## 5. Production release
When satisfied, upload to the main index:

```bash
twine upload dist/*
```

Tag the release in git and publish release notes.

## 6. Post-release checks
- Confirm `pip install nocturnal-archive` finds the new version.
- Run the installer script (`curl https://get.nocturnal.dev/install.sh | bash`) to ensure it resolves the published wheel.
- Update any documentation badges or version references (`README.md`, `setup.py`, `docs/BETA_RELEASE_CHECKLIST.md`).

## 7. Automating releases (optional)
- Create a GitHub Actions workflow that runs tests, builds, and uploads on tagged commits using `pypa/gh-action-pypi-publish`.
- Store the API token in the repository secrets (`PYPI_API_TOKEN`).
- Gate promotion to the `stable` channel via manual approval if desired.

Happy shipping! 🦉
