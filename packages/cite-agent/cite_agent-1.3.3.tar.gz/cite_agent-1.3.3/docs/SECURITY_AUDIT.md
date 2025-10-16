# Security Audit – Exposed Secrets (October 2025)

During repository triage we discovered multiple API keys and secrets committed in historical files. **All of the secrets listed below must be rotated immediately** and the corresponding commit history should be purged or rendered harmless.

| Secret / Provider | Location (now sanitized) | Recommended Action |
|-------------------|--------------------------|--------------------|
| `GROQ_API_KEY`, `GROQ_API_KEY_1` (Groq) | `.env.local` (now replaced with placeholders) | Rotate keys in Groq dashboard. Update deployment environments with newly issued values. |
| `MISTRAL_API_KEY` (Mistral) | `.env.local` | Rotate key; delete the compromised one. |
| `CEREBRAS_API_KEY` (Cerebras) | `.env.local` | Rotate key. |
| `COHERE_API_KEY` (Cohere) | `.env.local` | Rotate key. |
| `CORE_API_KEY` (CORE API) | `.env.local` | Rotate key. |
| `SEMANTIC_SCHOLAR_API_KEY` | `.env.local` | Rotate key. |
| `GOOGLE_SEARCH_API_KEY`, `GOOGLE_SEARCH_ENGINE_ID` | `.env.local` | Rotate key and search engine ID if compromised. |
| `UNPAYWALL_EMAIL` | `.env.local` | Review the email usage and replace with a service account address. |
| Database URLs (`MONGODB_URL`) | `.env.local` | Review access logs, rotate credentials, and update deployments. |

Additional findings:

1. `JWT_SECRET_KEY` is now enforced to come from the environment (see `nocturnal-archive-api/src/auth/security.py`). Ensure the production value is set and not committed.
2. Development helper scripts still contain placeholder values (e.g., `unified-platform/src/services/real_integration_service.py`). These are safe but should be double-checked before enabling production code paths.
3. `.env.local` has been sanitized with placeholders and remains ignored via `.gitignore`. Do **not** recommit real secrets.

## Recommended next steps

1. Rotate every secret listed above at the provider level.
2. Commit the sanitized `.env.local` file only if required for onboarding; otherwise keep it untracked locally.
3. Consider using `git filter-repo` or the GitHub secret scanning remediation utilities to purge exposed values from history if the repository is public.
4. Store production credentials in a secrets manager (e.g., AWS Secrets Manager, GCP Secret Manager, Doppler) and inject them via CI/CD.
5. Run the new `scripts/security_audit.py` tool (see below) before deploying to ensure no placeholder values remain.
