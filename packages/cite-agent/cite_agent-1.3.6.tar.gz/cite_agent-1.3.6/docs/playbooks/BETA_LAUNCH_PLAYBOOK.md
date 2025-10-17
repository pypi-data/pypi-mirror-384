# Nocturnal Archive Beta Launch Playbook

This playbook walks through the public-facing launch, internal coordination, and telemetry plan for the Nocturnal Archive beta.

---

## 1. Launch Narrative & Positioning
- **Promise**: "Spin up finance and research insights in seconds with a safe, CLI-first copilot." Focus on shell safety, deterministic tooling, and built-in data citations.
- **Audience**: Technical analysts, research leads, staff engineers, and AI tooling teams.
- **Value props**: Pre-wired finance lookups, reproducible workspace interactions, and low-latency Groq-backed reasoning.

## 2. Timeline Snapshot (T-minus Checklist)
- **T-10 days** – Finish regression runs, freeze dependencies, smoke the wheel in clean VMs.
- **T-7 days** – Finalize onboarding assets (email copy, quickstart PDF, Loom walkthrough). Publish docs/INSTALL.md + this playbook.
- **T-5 days** – Provision monitoring pipeline, set up Slack/Teams beta channel, seed feedback form.
- **T-3 days** – Push release candidate to private PyPI index; generate signed installers for Windows `.ps1` and macOS `.command` wrappers.
- **T-1 day** – Send preload instructions to early testers, stage status page announcement.
- **T (Launch)** – Publish PyPI release, unveil landing page, send invite email, open support triage rotations.
- **T+1 week** – Collect metrics, publish beta health report, triage backlog.

## 3. User-Facing Onboarding

### 3.1 Landing Page & CTA
- Single CTA: **"Get the Beta"** → downloads a platform-specific starter kit (zip containing helper scripts + README).
- Secondary CTA: **"See it in action"** → 90-second Loom of CLI workflow.
- Trust signals: Security highlights, Groq-backed, MIT licensed, optional self-hosted APIs.

### 3.2 Starter Kit Contents
- `Start Nocturnal (macOS).command` – opens Terminal automatically, runs the bootstrap script, and launches the CLI.
- `Start Nocturnal (Windows).ps1` – PowerShell script that creates a venv, installs the wheel, and launches `nocturnal --setup`.
- `beta-quickstart.pdf` – polished version of docs/INSTALL.md, with screenshots and QR codes.
- `FEEDBACK.md` – link trio (feedback form, bug report board, office hours calendar).

> 👉 Action: wrap existing `nocturnal --setup` wizard with friendly wrappers; bundle generated scripts and README with the wheel upload.

### 3.3 Email Sequence (copy skeleton)
1. **Launch announcement**
   - Subject: "You're in: Nocturnal Archive Beta"
   - Body: Value proposition, bullet install steps, link to starter kit, mention support alias `beta@nocturnal.dev`.
2. **Day 2 check-in**
   - Quick tip (e.g., multi-ticker comparison), reminder about office hours.
3. **Day 5 "Unlock more"**
   - Highlight research synthesis workflow, ask for feedback form completion.

Include iCalendar invite to the weekly live Q&A.

### 3.4 In-product Welcome Flow
- On first launch, `nocturnal --setup` already captures the Groq key; extend it to:
  - Show a brief "Beta code of conduct" (privacy, no PII uploads).
  - Offer opt-in telemetry toggle (default off).
  - Print `nocturnal tips` command for contextual help.
- Add `nocturnal tips` command to rotate through pro tips and link to docs.

## 4. Support & Feedback Loop
- **Channel**: Create `#nocturnal-beta` Slack/Discord bridge plus `beta@nocturnal.dev` shared inbox.
- **Response SLAs**: <4h during launch week, <1 business day afterward.
- **Rotations**: Two engineers + one PM on beta duty per week. Publish on-call schedule in shared calendar.
- **Feedback Intake**: Embed Productboard/Jira form with auto-tagged "BETA" label. Quick triage fields (severity, repro steps, environment).

## 5. Telemetry & Monitoring

### 5.1 Client Instrumentation
- Extend `EnhancedNocturnalAgent` to emit JSON lines to `~/.nocturnal_archive/logs/beta-telemetry.jsonl` with:
  - hashed user ID, command path (`cli`, `api`, `shell_blocked`, etc.), latency, success flag.
  - allow disabling via `NOCTURNAL_TELEMETRY=0`.
- Ship a lightweight uploader (`nocturnal-report --sync`) that pushes logs to an S3 bucket or ingest API nightly.

### 5.2 Central Observability Stack
- **Metrics**: Grafana dashboards fed by Loki (logs) and VictoriaMetrics/Prometheus (aggregated counts).
- **Alerts**:
  - High failure rate (>20% shell_blocked / FinSight errors) over 15m window.
  - No telemetry heartbeat for >60m (agent down).
  - Update service failures from `nocturnal-update` (webhook into Opsgenie/PagerDuty).
- **Health checks**: Reuse `_check_backend_health` by exposing `/beta/readyz` endpoint and keep it on the status page.

### 5.3 Beta Scorecard (weekly)
- Installs activated
- DAU / WAU
- Avg. first response latency
- Finance success rate
- Research success rate
- Top 5 blockers (from feedback form + telemetry)

## 6. Release Engineering Workflow
- Automate GitHub Actions pipeline: lint + tests → build wheel → upload to private PyPI/simple index.
- Tag beta builds as `0.9.0bX`; promote to public PyPI after sign-off.
- Provide rollback script: `python -m pip install nocturnal-archive==<prev>` + `nocturnal --reset`.

## 7. Definition of Done for Beta Exit
- 90%+ testers keep the agent enabled after first week.
- P0/P1 bug queue cleared within 24h for one month.
- Finance + research flows meet SLA (<8s P95, <2% error rate).
- Telemetry opt-in rate ≥ 60% (opt-in prompt clarity).
- Documentation NPS ≥ 8/10.

## 8. Open TODOs (tracked items)
- [ ] Build installer scripts (`.command`, `.ps1`) wrapping `nocturnal --setup`.
- [ ] Implement opt-in telemetry emitter + sync command.
- [ ] Spin up Grafana/Loki stack (Terraform module or Render/Trainiac deployment).
- [ ] Draft landing page (Vercel/Next.js) with CTA + analytics (PostHog).
- [ ] Record Loom walkthrough and drop in `/docs/assets/`.

---

**Keeper:** Store updates to this playbook in the `docs/playbooks/` folder and link it from `docs/BETA_RELEASE_CHECKLIST.md` so every release manager picks up the latest guidance.
