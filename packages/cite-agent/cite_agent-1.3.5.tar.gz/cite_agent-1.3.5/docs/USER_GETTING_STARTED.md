# Nocturnal Archive – Getting Started for Beta Testers

Welcome to the beta! This short guide shows you how to get the agent running without wrestling with developer tooling.

---

## 1. Install in one command (curl / PowerShell)
Grab the installer straight from your invite email or paste the command below. It downloads a tiny bootstrap script that handles everything for you.

**macOS / Linux**

```bash
curl -fsSL https://raw.githubusercontent.com/Spectating101/nocturnal-archive/overnight-backup-20251003/installers/nocturnal-install.sh | bash
```

**Windows (PowerShell)**

```powershell
irm https://raw.githubusercontent.com/Spectating101/nocturnal-archive/overnight-backup-20251003/installers/nocturnal-install.ps1 | iex
```

What happens next:
- A private virtual environment is created under `~/.nocturnal_archive/`.
- The latest beta build from the `nocturnal-archive` package is pulled down (pre-release channel by default).
- The CLI auto-launches with a warm welcome: “Hey, Nocturnal here, quick sign-in for the beta please.”

Prefer to adjust the package channel or pass additional setup flags? Set `NOCTURNAL_PACKAGE_SPEC`, `NOCTURNAL_CHANNEL`, `NOCTURNAL_SETUP_FLAGS`, or the new `NOCTURNAL_PACKAGE_SHA256` before running the command. When the SHA-256 is provided the installer downloads the wheel/source into a temp directory, verifies the hash, and only proceeds if it matches. (Generate the hash locally with `shasum -a 256 file.whl` or `Get-FileHash -Algorithm SHA256 file.whl`.)

### Installing the TestPyPI beta build
For the 
`0.9.0b1` dry run we just published to TestPyPI, share this command instead:

```bash
NOCTURNAL_PACKAGE_SPEC="nocturnal-archive==0.9.0b1" \
NOCTURNAL_EXTRA_INDEX_URL="https://test.pypi.org/simple/" \
NOCTURNAL_PACKAGE_SHA256="<sha256>" \
curl -fsSL https://raw.githubusercontent.com/Spectating101/nocturnal-archive/overnight-backup-20251003/installers/nocturnal-install.sh | bash
```

On Windows PowerShell:

```powershell
$env:NOCTURNAL_PACKAGE_SPEC="nocturnal-archive==0.9.0b1";
$env:NOCTURNAL_EXTRA_INDEX_URL="https://test.pypi.org/simple/";
$env:NOCTURNAL_PACKAGE_SHA256="<sha256>";
irm https://raw.githubusercontent.com/Spectating101/nocturnal-archive/overnight-backup-20251003/installers/nocturnal-install.ps1 | iex
```

Those environment variables tell the installer to pull the exact beta build from TestPyPI while still falling back to the public index for dependencies.

Replace `<sha256>` with the published checksum from the release announcement. If you skip the line the installer behaves like before but without tamper detection.

> **Offline or air-gapped?** Download the same scripts from the starter kit ZIP (see below) and run them locally.

## 2. Starter kit (double-click option)
If you’d rather keep everything offline or avoid curl, download the starter kit from the invite email and unzip it. Inside you’ll find:

- `Start Nocturnal (macOS).command` – double-click to launch the installer window.
- `Start Nocturnal (Windows).ps1` – right-click → “Run with PowerShell”.
- `beta-quickstart.pdf` – screenshots of the CLI, walkthrough, and QR code for office hours.
- `FEEDBACK.md` – links to the beta feedback form and support inbox.

These scripts wrap the same logic as the online installer—create the environment, fetch dependencies, and launch the welcome flow.

---

## 3. First‑run sign-in
When the CLI launches for the first time it keeps things simple:
1. **Academic email** – sign in with your institution-issued address (for now we accept `.edu`, `.ac.uk`, and similar academic domains). We’ll validate it before proceeding.
2. **Password** – enter your existing beta password or create a new one. The CLI provisions your account and pulls the required API keys from the control plane automatically—no manual key pasting.
3. **Tips command** – the wizard reminds you that `nocturnal tips` rotates through handy shortcuts once you’re inside the shell.

After the account handshake completes you’ll land in the interactive prompt. Type `help` to see available commands or `exit` to quit.

> The Groq key retrieved for your account is stored in your OS keychain (Keychain Access on macOS, Credential Manager on Windows, Secret Service on Linux). If the keychain isn’t available we fall back to `config.env` and call it out in the logs.

> Daily usage is capped at **25 queries** per tester. The CLI tracks this automatically and resets the count every UTC midnight. The limit is sealed to your beta build—environment tweaks are ignored, so reach out if you need a higher allowance for testing.

> Telemetry is always on. Events stream to the control plane in real-time and a replay log is written to `~/.nocturnal_archive/logs/beta-telemetry.jsonl` for transparency.

---

## 4. Everyday commands
| Task | Try this |
|------|----------|
| Open interactive chat | `nocturnal` |
| One-off question | `nocturnal "Summarize Microsoft’s Q2 earnings"` |
| Configure keys again | `nocturnal --setup` |
| View workspace files | Ask: "Show me the files in the project root" |
| Compare tickers | Ask: "Compare AAPL and MSFT net income" |
| Share feedback quickly | `nocturnal --feedback` |

Need inspiration? Run `nocturnal tips` inside the CLI.

---

## 5. Command sandbox (what works, what doesn’t)
The CLI can execute a tiny whitelist of shell utilities to keep testers (and our infra) safe. Prefix commands with `!` inside the chat to run them.

**Allowed commands**

- `ls`, `pwd`, `stat`, `whoami`
- `cat`, `head`, `tail`, `wc`
- `echo` with optional safe redirects inside the workspace
- `cd <subdir>` and `export VAR=value`
- `rm file.txt` (single files inside the workspace only)
- `python -c "print('hello')"` style one-liners that avoid OS/system modules

**Blocked actions**

- Pipes or chained commands (`|`, `;`, `&&`, `||`)
- Multi-line scripts or background jobs
- Writing outside the project tree (except `/tmp` for scratch files)
- Destructive wildcards (`rm -rf`, `*`, `?`), package managers, or network utilities
- Arbitrary Python snippets that import `os`, `sys`, `subprocess`, `socket`, etc.

> Tip: ask the agent to run SQL workflows instead of shelling out. The finance/filings adapters are tuned for that path.

---

## 6. Updating to the latest beta
The CLI enforces updates automatically every time you launch it. If you need to force a refresh manually (e.g., on an air-gapped machine), run:

```bash
python -m pip install --upgrade nocturnal-archive
nocturnal-update --status
```

Manual commands are optional—the agent already checks, installs, and restarts itself before each session.

---

## 7. Custom ticker names (optional)
The agent ships with a starter list of company nicknames so requests like “What’s Nvidia’s latest revenue?” resolve to the right ticker. You can add your own nicknames without modifying the code:

1. Create the folder `~/.nocturnal_archive/` if it doesn’t exist.
2. Add a file named `tickers.json` with entries like this:
   ```json
   [
     {"name": "acme corp", "symbol": "ACME"},
     {"name": "globex", "symbol": "GBX"}
   ]
   ```
3. Restart the CLI. Your nicknames now map to the correct symbols.

Prefer a different location? Set the environment variable `NOCTURNAL_TICKER_MAP=/path/to/my_tickers.json` before launching the agent.

---

## 8. Getting help
- **Live chat:** join the `#nocturnal-beta` Slack/Discord channel from your invite.
- **Email:** beta@nocturnal.dev (we reply within one business day).
- **Bug or feedback:** fill out the link in the starter kit or run `nocturnal --feedback`.

Happy exploring! 🦉✨
