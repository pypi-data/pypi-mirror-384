# Beta Release Checklist

Use this checklist to keep the beta launch tight and reproducible.

## ✅ Code + Tests
- [ ] `pytest tests/enhanced -q` passes.
- [ ] `mypy nocturnal_archive` (optional) is clean.
- [ ] Lint fast check: `flake8 nocturnal_archive tests`.
- [ ] No ad-hoc files under the project root (`git status` is clean).

## ✅ Packaging
- [ ] Update `setup.py` version and changelog entry.
- [ ] Regenerate bundled data files if required (`nocturnal_archive/data/company_tickers.json`).
- [ ] Run `python -m build` and inspect `dist/` contents.
- [ ] Smoke install the wheel: `pip install dist/nocturnal_archive-*.whl` in a fresh venv.

## ✅ Documentation & Go-To-Market
- [ ] Refresh `README.md` headline + quick start.
- [ ] Verify `docs/INSTALL.md` matches the current interface.
- [ ] Review `docs/playbooks/BETA_LAUNCH_PLAYBOOK.md` for messaging/alignment updates.
- [ ] Capture notable changes in `BETA_LAUNCH_READY.md` or release notes.

## ✅ Distribution
- [ ] Publish wheel/sdist via `twine upload dist/*` or internal artifact store.
- [ ] Announce new version with upgrade steps (`nocturnal-update --status`).
- [ ] Confirm no deprecated backend bundles creep back into the repo (legacy stack now only in Git history).

## ✅ Distribution Assets
- [ ] Bundle platform starter kits (macOS `.command`, Windows `.ps1`, quickstart PDF).
- [ ] Host download links on the landing page / release email.
- [ ] Validate `nocturnal --setup` onboarding flow end-to-end with new wrappers.

## ✅ Post-Launch Monitoring & Feedback
- [ ] Confirm Groq quota alarm thresholds.
- [ ] Enable beta telemetry upload pipeline (opt-in respected).
- [ ] Review telemetry dashboards for API health / CLI errors within 24 hours.
- [ ] Capture feedback tickets tagged `beta` in issue tracker.
