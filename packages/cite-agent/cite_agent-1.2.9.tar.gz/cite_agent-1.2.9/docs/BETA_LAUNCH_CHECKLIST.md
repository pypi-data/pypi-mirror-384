# Nocturnal Archive Beta Launch Checklist

This checklist captures everything required to execute the private beta and pave the path to a public release. Use it as the master tracker across product, engineering, legal, support, and marketing.

---

## 1. Product & Strategy
- [ ] Finalize beta goals (activation, retention, qualitative feedback).
- [ ] Define success metrics (DAU, token usage, NPS, error rate targets).
- [ ] Finalize beta timeline (kickoff date, feedback cycles, exit criteria).
- [ ] Assign beta owner / response SLA.
- [ ] Create release note cadence (weekly/biweekly updates to testers).

## 2. Build Readiness
- [x] Regression suite green (CI + manual smoke on macOS/Windows/Linux).
- [x] TestPyPI package built and verified (`nocturnal-archive==0.9.0b1`).
- [ ] Production PyPI token ready (scoped per project for final release).
- [ ] Auto-updater smoke-tested (macOS LaunchAgent, Windows Scheduled Task, Linux systemd timer).
- [ ] Version pinning to prevent old clients from staying on unsupported builds.
- [ ] Feature flag system in place for experimental capabilities (optional but recommended).

## 3. Installer & Distribution
- [ ] macOS installer (`.pkg` or notarized `.app`).
- [ ] Windows installer (`.msi` via WiX or `.exe` via Inno Setup), signed.
- [ ] Linux installer (AppImage/Flatpak or `.deb`).
- [ ] Host installers (GitHub Releases / S3 with CDN / direct raw GitHub fallback).
- [ ] Generate checksums for installers and publish alongside links.
- [ ] Draft distribution email with OS-specific download buttons and instructions.
- [x] Provide fallback shell/PowerShell scripts for advanced users (already in `installers/`).

## 4. Onboarding & UX
- [x] First-run wizard with academic email login verification.
- [x] Collect Groq/API keys securely (OS keychain integration).
- [x] Telemetry disclosure explaining always-on streaming.
- [x] Display beta limitations (rate limits, command sandbox, expected latency).
- [x] Friendly CLI theming (rich prompts, quick tips, `nocturnal tips`).
- [x] Include in-app feedback command (`nocturnal --feedback`).
- [x] Document command sandbox behaviour (allowed vs. blocked commands).

## 5. Legal & Compliance
- [ ] Draft and share beta NDA / terms of use.
- [ ] Publish privacy disclosure outlining telemetry collection.
- [ ] Verify licensing of dependencies (ensure redistributions are compliant).
- [ ] Confirm data-handling compliance (PII, financial data retention policies).
- [ ] Provide export instructions for users who want to remove data/configs.

## 6. Security
- [ ] Sign installers (Apple Developer ID, Microsoft Authenticode).
- [x] Hash verification in installer scripts.
- [x] Academic domain gating for beta access.
- [x] Optionally obfuscate/distribute core agent via PyArmor/Nuitka bundles.
- [ ] Anti-tamper checks (hash of CLI, alerts if modified).
- [ ] License file per tester with server-side revocation.
- [ ] Rate limits & abuse detection on backend endpoints.
- [ ] Secrets storage guidance (Keychain, Windows Credential Manager, etc.).

## 7. Telemetry & Monitoring
- [ ] Extend `TelemetryManager` with HTTPS batching.
- [ ] Deploy ingestion API (FastAPI) with auth & rate limits.
- [ ] Store telemetry in managed DB (Postgres/ClickHouse) or logging service.
- [ ] Dashboard: installs, DAU, token usage per user, error rates, command mix.
- [ ] Alerts for crash spikes, API failures, or rate limit breaches.
- [ ] Monitor auto-update rollout success (percentage on latest build).

## 8. Support & Feedback
- [ ] Create dedicated support channel (Slack/Discord) with invite instructions.
- [ ] Set up support inbox (beta@nocturnal.dev) with auto-responder.
- [ ] Build feedback form (Notion/Typeform) linked from CLI/footer.
- [ ] Write troubleshooting guide and FAQ (include telemetry log location).
- [ ] Define escalation process for P0 issues.
- [ ] Schedule regular beta syncs (office hours, feedback review).

## 9. Communications
- [ ] Welcome email template (links, instructions, limitations, support info).
- [ ] Update cadence (weekly digest of fixes + upcoming features).
- [ ] Changelog location (docs/CHANGELOG.md or website section).
- [ ] Public status page (optional) or at least internal downtime playbook.
- [ ] Closing survey to collect final impressions before GA.

## 10. Backend & Infrastructure
- [ ] Health endpoint implemented (`/api/health`) and monitored.
- [ ] Rate limiting for API endpoints (per-user/per-IP).
- [ ] Graceful degradation if external APIs (Groq, OpenAlex) are down.
- [ ] Logging retention policy (rotate, scrub sensitive data).
- [ ] Backup/restore plan for config storage and telemetry DB.
- [ ] Incident response runbook (pager escalation, communication template).

## 11. Post-Beta Transition
- [ ] Criteria for promoting testers to paid/public tiers.
- [ ] Plan for migrating beta data to production accounts.
- [ ] Remove temporary feature flags / telemetry gating before GA.
- [ ] Update pricing/licensing messaging post-beta.
- [ ] Archive beta assets (installers, docs) and snapshot feedback insights.

---

**How to use this checklist:**
- Track ownership (assign initials next to each item) and due dates in a shared tracker.
- Hold weekly stand-ups to review progress.
- Update this document with notes/links as tasks complete.

When every section is checked off and acceptance criteria hit, you’re ready to flip the switch on the public launch.
