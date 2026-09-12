---
name: hermes
description: Use when the user runs /hermes or asks to set up, repair, update, check, or control Hermes Agent (NousResearch natively on Windows) so it can be reached from Telegram/Discord/WhatsApp/Slack/etc. on their phone and control this PC. Covers full 0-to-working install wizard, model/provider config (prefers Hermes' keyless opencode-free tier, else reuses the opencode zen/go account), a gateway platform menu (Telegram, Discord, WhatsApp, Slack, Matrix, …), Windows auto-start, and ongoing stability checks/fixes.
---

# Hermes Agent setup & maintenance (native Windows)

Hermes Agent (NousResearch) is a self-improving AI agent with a messaging gateway (Telegram, Discord, WhatsApp, Slack, Matrix, ~20 platforms). Goal: install it natively on this Windows PC, wire it to a model backend, let the user control the PC from the phone via their platform of choice, auto-start at login, and keep it stable.

## Key locations (native Windows)

- Install/runtime: `%LOCALAPPDATA%\hermes\hermes-agent\` (git checkout + venv)
- Data dir (`HERMES_HOME`): `%LOCALAPPDATA%\hermes\` — `config.yaml`, `.env`, `auth.json`, `logs\`, `sessions\`, `skills\` live here. **Survives reinstalls.**
- Launcher: `%LOCALAPPDATA%\hermes\bin\hermes.exe`. Existing terminals won't see `hermes` on PATH — call it directly:
  `& "$env:LOCALAPPDATA\hermes\bin\hermes.exe" ...`
- Shell-in bash: Hermes uses Git Bash internally (`HERMES_GIT_BASH_PATH`), no manual action needed.

Always run install/management via **PowerShell**: `powershell -NoProfile -Command "..."`.

## 0. Detect existing install & decide a path

```powershell
Test-Path "$env:LOCALAPPDATA\hermes\bin\hermes.exe"
& "$env:LOCALAPPDATA\hermes\bin\hermes.exe" --version
```

- `hermes --version` works → installed.
- **EVERY /hermes invocation MUST first report the live process status** (unless `$ARGUMENTS` is install/update/stop/uninstall):
  ```powershell
  & "$env:LOCALAPPDATA\hermes\bin\hermes.exe" gateway status          # running? PID + Startup/Scheduled entry
  & "$env:LOCALAPPDATA\hermes\bin\hermes.exe" config get model        # which provider/model is actually serving
  Get-Process -Id (Get-CimInstance Win32_Process -Filter "Name like 'python%'" | Where-Object { $_.CommandLine -match 'gateway run' }).ProcessId -ErrorAction SilentlyContinue | Select-Object Id,StartTime,CPU,WorkingSet
  Get-Content "$env:LOCALAPPDATA\hermes\logs\gateway.log" -Tail 6     # what it did most recently
  Get-Content "$env:LOCALAPPDATA\hermes\logs\agent.log" -Tail 6       # active turn? which tools running?
  ```
  Report in a compact block:
  - **Running**: `✓ gateway up (PID …) | model: <provider>/<model>` or `✗ down`.
  - **What it's doing**: last `gateway.log` line + last `agent.log` tool lines (`tool execute_code/terminal/computer_use completed`, `API call #N`, `response ready`). That tells the user if a turn is live, what tool it last ran, and whether the last reply was delivered.
  - Then offer the choice: **leave it running / restart / pause / stop** — and apply what they pick (pause = gateway pause, stops inbound turns but keeps the process; stop = process down; restart = clean reload). `$ARGUMENTS` sets the default (start/on/off/restart/status), but always state the live state + ask before mutating (unless the arg explicitly says to).
- Command intent from `$ARGUMENTS`:
  - `start` / `on` → ensure server + gateway are up
  - `stop` / `off` → ensure server + gateway are down
  - `restart` → restart the gateway
  - `status` / `check` → report state, do not change anything
  - `update` → update only
  - `setup` / `install` / empty & not installed → full wizard
  - `repair` → diagnose + fix (no reinstall unless required)
  - `uninstall` → uninstall
  - empty & already installed → show status, then **ask the user** open (on) or close (off) and apply

## 1. Install

### 1a. Official installer (fast path)

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

If that errors, fall back to:
```powershell
iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
```

- **Skip the interactive first-run wizard** so model/platform setup is done programmatically:
  `powershell -NoProfile -Command "& ([scriptblock]::Create((irm https://hermes-agent.nousresearch.com/install.ps1))) -SkipSetup"`
- Antivirus note: if Defender/Bitdefender quarantines `%LOCALAPPDATA%\hermes\bin\uv.exe`, it's a known false positive on Astral's `uv`; whitelist the `bin` folder (the hash changes every release).

### 1b. Manual install (if installer fails)

**Known failure on this PC:** the installer dies with `Environment variable name or value is too long` — the User PATH is already ~2500 chars (near the Windows limit) and the installer's PATH-prepend+migration step overflows. Fix the PATH only if you want; otherwise do the manual install:

```powershell
$env:HERMES_HOME = "$env:LOCALAPPDATA\hermes"
git clone https://github.com/NousResearch/hermes-agent.git "$env:HERMES_HOME\hermes-agent"
# Python 3.13 (project requires-python >=3.11,<3.14)
& "$env:HERMES_HOME\bin\uv.exe" venv "$env:HERMES_HOME\hermes-agent\.venv" --python 3.13
$env:VIRTUAL_ENV = "$env:HERMES_HOME\hermes-agent\.venv"
$env:PATH = "$env:HERMES_HOME\hermes-agent\.venv\Scripts;$env:PATH"
& "$env:HERMES_HOME\bin\uv.exe" pip install -e "$env:HERMES_HOME\hermes-agent[messaging]"
# Launcher shims live in the venv; copy them into bin\ so a single path works:
Copy-Item "$env:HERMES_HOME\hermes-agent\.venv\Scripts\hermes.exe"      "$env:HERMES_HOME\bin\hermes.exe"
Copy-Item "$env:HERMES_HOME\hermes-agent\.venv\Scripts\hermes-acp.exe" "$env:HERMES_HOME\bin\hermes-acp.exe" -ErrorAction SilentlyContinue
```

Verify: `& "$env:LOCALAPPDATA\hermes\bin\hermes.exe" --version`. (The installer still pre-creates `bin\uv.exe` before it dies — that's what step above reuses. If it didn't, install uv first via the official astral script.)

## 2. Model backend (prefer the free tier)

**Order of preference — try the keyless free tier FIRST; it costs nothing and needs no key:**

### 2a. `opencode-free` — keyless free tier (recommended, zero config)

Hermes ships a native provider that serves OpenCode's free-tier models anonymously (no key, no account). It points at `https://opencode.ai/zen/v1`. Set in `config.yaml`:

```yaml
model:
  provider: opencode-free
  default: nemotron-3-ultra-free
```

- **Default MUST be a tool-calling model.** Two verified tool-capable free defaults (pick by priority):
  - **Speed** → `ling-3.0-flash-fin-free` (Finnish flash model). API latency **~1.8s** vs nemotron's 18-24s; a simple terminal turn completes in ~6-7s (measured 2026-09-08). Verified tool-calling (calls `tool terminal`). **Caveat: bursty `503 Endpoint is unavailable` from upstream** — needs a reliable fallback (nemotron) or turns fail over.
  - **Reliability** → `nemotron-3-ultra-free` (1M ctx): executes terminal/file/browser tools consistently; slow (18-24s/API call).
  - `nemotron-3.5-lightning-free` (small) is *fallback only* — it often answers without calling any tool, so it tells the user "no puedo controlar tu PC" instead of doing it. If the bot ever replies to a control request without doing anything, the fix is the model, not the config.
- **Turn-name breakdown measured on this PC** (a 409s Telegram turn): 296s was `execute_code` real work (browser + Facebook + message — inherent, page loads dominate, no config fixes it), ~100s was model latency (5 × 18-24s on nemotron). Swapping to ling cut the model part ~15-20×; browser-heavy tasks stay minutes regardless.
- **CRITICAL — changing the default model does NOT touch live sessions.** A gateway DM session is created once (with the then-default model) and reused on every restart via "auto-resume" — it keeps its pinned model forever. Symptom: you switch `config.yaml` to `nemotron-3-ultra-free`, `hermes config get model` shows it, gateway restarts, but the bot STILL answers without tools in fast ~45s turns (= old small model). Fix after any model swap:
  ```powershell
  & "$env:LOCALAPPDATA\hermes\bin\hermes.exe" sessions list                 # find the telegram dm session id
  & "$env:LOCALAPPDATA\hermes\bin\hermes.exe" sessions delete --yes <session_id>
  # then remove its routing mirror entry from %LOCALAPPDATA%\hermes\sessions\sessions.json
  # (property agent:main:<platform>:dm:<chat_id>) and restart the gateway
  & "$env:LOCALAPPDATA\hermes\bin\hermes.exe" gateway restart
  ```
  The next phone message then starts a fresh session with the new default. (Tell the user to send a NEW message — a started turn can't be retargeted.)
- **Available free models** (suffix `-free`) rotate weekly; read the live anonymous catalog before trusting any list:
  ```powershell
  Invoke-RestMethod -Uri 'https://opencode.ai/zen/v1/models' | % { $_.data.id } | Where-Object { $_ -match '-free$' }
  ```
- **Known-good on this PC (verified):** `nemotron-3-ultra-free` (tool-calling ✓, reliable, slow), `ling-3.0-flash-fin-free` (tool-calling ✓, fast, bursty 503s), `nemotron-3.5-lightning-free` (chat-only, weak on tools). **`deepseek-v4-flash-free` = avoid:** hung silently >120s with no response (measured 2026-09-08), consistent with the earlier "Model is unavailable" day. Model availability changes daily — always smoke-test the chosen id (see §2c).
- **NEVER use `big-pickle` or `laguna-s-2.1-free` with Hermes** — both are UA-gate: the relay 429s/401s every client except the opencode CLI's own User-Agent. big-pickle is the model that runs opencode itself; it looks free but only works inside opencode's CLI.
- Free-tier quota: ~450-766 requests/day, resets at UTC midnight; when exhausted you get 429s until reset. Hermes retries automatically.
- Do NOT send an API key with this provider: the free relay `401`s any bearer it doesn't recognize.

### 2b. Reuse the opencode account key (fallback)

```powershell
type "$env:USERPROFILE\.local\share\opencode\auth.json"
```

If `opencode-go` (or `opencode-zen`) key present → write it to `%LOCALAPPDATA%\hermes\.env`:
```
OPENCODE_GO_API_KEY=<value>      # or OPENCODE_ZEN_API_KEY
```
Then set provider in `config.yaml`:
```yaml
model:
  provider: opencode-go      # or opencode-zen
  default: <model-id from the provider's own catalog>
```
Confirm the current model id against what the provider serves:
```powershell
$key = (Get-Content "$env:USERPROFILE\.local\share\opencode\auth.json" | ConvertFrom-Json).'opencode-go'.key
Invoke-RestMethod -Uri 'https://opencode.ai/zen/go/v1/models' -Headers @{Authorization="Bearer $key"} | % { $_.data.id } | Select-Object -First 40
```
**Gotcha:** `opencode-go` is the *subscription* tier. With no Go subscription the chat endpoint may return 429/401 while `/models` still answers. If that happens, drop back to §2a (opencode-free).

**Rate-limit diagnostic (canonical):** `hermes auth list` shows each credential's breaker state:
```
opencode-go (1 credentials):
  #1  OPENCODE_GO_API_KEY  api_key id=92e849 priority=0 env:OPENCODE_GO_API_KEY rate-limited GoUsageLimitError (429) (12h 7m left)
```
- `rate-limited GoUsageLimitError (429) (Nh left)` = the **Go monthly quota is exhausted**; resets in ~1 day or on top-up at opencode.ai/workspace. While flagged, `chat --provider opencode-go` returns `HTTP 401: Missing API key` (the breaker masks the 429) — the key IS fine, the subscription is capped.
- **While rate-limited, Go CANNOT serve as a fallback**: hermes falls down the chain and burns minutes retrying a dead endpoint. Move it to the END of `fallback_providers` (or remove it) until the quota resets.
- When quota is back, `deepseek-v4-flash` is the go-tier pick (fast, tool-capable, verified in the fallback chain).

Only if no opencode account at all → ask the user for an **OpenRouter** key (`sk-or-...`) → `OPENROUTER_API_KEY`, model like `openrouter/<model>`; or any first-class key in the table below.

| Provider | `.env` key | config `provider:` |
|---|---|---|
| OpenCode Free (keyless) | *(none)* | `opencode-free` |
| OpenCode Zen | `OPENCODE_ZEN_API_KEY` | `opencode-zen` |
| OpenCode Go | `OPENCODE_GO_API_KEY` | `opencode-go` |
| OpenRouter | `OPENROUTER_API_KEY` | `openrouter` |
| Anthropic | `ANTHROPIC_API_KEY` | `anthropic` |
| OpenAI | `OPENAI_API_KEY` | `openai-api` |

### 2c. Smoke-test tool-calling BEFORE wiring the gateway

The point is NOT "does the model reply" — it's "does the model actually call tools". A model that answers text but never invokes tools cannot control the PC. Force a real tool call:

```powershell
& "$env:LOCALAPPDATA\hermes\bin\hermes.exe" chat -q "Use the terminal tool to run: whoami" -m nemotron-3-ultra-free
```

- **Flag order matters:** `-m <model>` goes AFTER the `-q "<query>"` positional (argparse). `chat -q "..." -m nemotron-3-ultra-free` ✓; `chat -q -m nemotron... "..."` ✗.
- **PASS = output shows tool activity**, not just a reply: a `💻 $` terminal line, the printed result (`Oblivion`), and a `Messages: N (1 user, 2 tool calls)` summary. If the model answers prose with zero tool calls → wrong model, use `nemotron-3-ultra-free` (or another big tool-capable id).
- `chat -q` reaches the API and prints the result. The free models are slow — allow ~2min; patience.
- Do **NOT** use `hermes -c "..."` or plain `hermes chat` in this shell: they launch the TUI, which crashes here with `prompt_toolkit ... NoConsoleScreenBufferError: No Windows console found`. `-q` (fast chat) is the headless-friendly path.
- On `401 ... not supported` → model id wrong/delisted for this tier; pick another id from §2a.
- On `400 ... Model is unavailable` → model listed but down today; pick another.
- Never judge an id from a raw `Invoke-RestMethod` completion test — the relay rejects raw clients (400/401) for header reasons; only the Hermes-native call is authoritative.

### 2d. Automatic failover (fallback_providers) — configured

Set in `config.yaml` so the gateway never goes silent on upstream saturation / quota / rough patches. **Ordering is the hot path** — hermes tries fallbacks in order when the primary fails; a dead/rate-limited entry at the TOP of the chain burns minutes per turn. Current chain on this PC (speed primary → reliable backup → fastest paid once quota returns):
```yaml
fallback_providers:
  - provider: opencode-free
    model: nemotron-3-ultra-free
  - provider: opencode-go
    model: deepseek-v4-flash
```
- Tried in order when the primary fails (rate-limit 429, 5xx, connection errors, empty response) after its retries run out. `hermes fallback list` shows the chain; add/remove interactively via `hermes fallback add` (or write the YAML directly — the CLI picker is interactive/TUI).
- **Dead-end chain lesson (measured 2026-09-08):** the old chain had `opencode-go` as the ONLY fallback while it was rate-limited — a 503 on the primary routed straight into a dead 429 endpoint and the turn ate minutes. Ordering matters more than composer: reliable-slow backup first, rate-limited paid tier last.
- Caveat: `opencode-go` (paid Zen/Go tier) has its **own monthly usage limit**. When reached you get `GoUsageLimitError ... Resets in 1 day` in agent.log (see §2b `hermes auth list` diagnostic) — the fallback entry stays configured and starts working again when the quota resets (or the user tops up their workspace balance at opencode.ai/workspace). Free-tier `-free` alternates were tried as fallbacks and REJECTED: only `nemotron-3-ultra-free` (and now `ling-3.0-flash-fin-free`, verified 2026-09-08) actually call tools (0 tool calls = the "no puedo" bug), so do NOT add another `-free` model to the chain.
- The Nvidia 502s (`Upstream error from Nvidia: Service temporarily overloaded`) are bursty and auto-retried (attempt N/3); a turn can take 10+ min to land. Not an action item by itself.

## 3. Gateway platform — CONFIG MENU

Gateway config lives in `%LOCALAPPDATA%\hermes\.env` (secrets + allowlist) and `config.yaml` (`platforms.<name>.enabled: true`). The wizard (`hermes gateway setup`) is interactive; this skill writes the `.env` keys directly.

**Ask the user: "¿A través de qué aplicación quieres controlar este PC?"** then follow only that subsection. The first three are the practical phone options; the rest are supported but heavier. **Every option below gives full remote PC control** (terminal + files + browser + computer_use) — the platform only changes *where* the messages arrive; the capability is identical. Add as many platforms as the user wants (each is just another `.env` token + `enabled: true`; they coexist and all reach the same agent).

### 3.1 Telegram (recommended — simplest for phone)
Ask for:
1. **Bot token** — [@BotFather](https://t.me/BotFather) → `/newbot`, format `123456789:ABC...`. Validate instantly:
   ```powershell
   Invoke-RestMethod "https://api.telegram.org/bot<TOKEN>/getMe" | % { $_.result.username }
   ```
   (if it prints `@<name>` the token is good — expect exactly that username from the user)
2. **Numeric user ID** — [@userinfobot](https://t.me/userinfobot), from your phone, it returns your id.

Write to `.env`:
```
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_ALLOWED_USERS=<user-id>
```
Enable in `config.yaml`:
```yaml
platforms:
  telegram:
    enabled: true
```

### 3.2 Discord
Ask for:
1. **Bot token** — Discord Developer Portal → Application → Bot → token (long hex-ish string).
2. **User ID** — Discord → Settings → Advanced → Developer Mode → right-click your name → Copy User ID.
3. **Guild ID** (only if using a server) — right-click server name → Copy Server ID.

Write to `.env`:
```
DISCORD_BOT_TOKEN=<token>
DISCORD_ALLOWED_USERS=<user-id>
```
Enable `platforms.discord.enabled: true` in `config.yaml`. Verify via the gateway log for `[Discord] Connected` (no curl shortcut like Telegram).

### 3.3 WhatsApp (Baileys bridge — needs Node; works via Web pairing)
- No API key needed — you pair the agent's WhatsApp Web session by scanning a QR code on your phone.
- Activate with `WHATSAPP_ENABLED=true`, add your number to `WHATSAPP_ALLOWED_USERS` (E.164 format, e.g. `+521234567890`).
- **The native pairing wizard is BROKEN on this PC**: `hermes whatsapp` / the desktop app promise a QR in a "new terminal window" that never opens, so you get stuck with nothing to scan. **Do NOT run the interactive wizard.** Pair from opencode instead (below) — it renders the QR right here so the scan step completes.

**opencode QR pairing (workaround that works):**
1. **Present BOTH modes and let the user choose** (the native wizard does this — the opencode wizard must too):
   - **Separate bot number** (recommended for a bot): people message a dedicated number; needs a 2nd SIM / WhatsApp Business number.
   - **Personal number (self-chat)**: the user messages themselves to talk to the agent.
   Set the choice: `WHATSAPP_MODE=bot` or `WHATSAPP_MODE=self-chat` in `%LOCALAPPDATA%\hermes\.env`.
2. **Phone (allowlist): ask manually with an example** so it's entered correctly:
   - Prompt: `Phone number that controls the PC? Format: <country code><area><number>, no dashes/spaces — e.g. +521234567890 (Mexico).`
   - Validate: strip spaces/dashes, must start with `+` followed by 9-15 digits; if invalid, ask again.
   - Write `WHATSAPP_ALLOWED_USERS=<that number>` to `.env`. (In `bot` mode it's comma-separated numbers or `*`.)
3. **Render the QR inside opencode** (no new terminal, no TTY needed):
   ```
   powershell -NoProfile -Command "$env:WHATSAPP_PAIR_TTL='180'; & \"$env:LOCALAPPDATA\hermes\hermes-agent\.venv\Scripts\python.exe\" -X utf8 \"C:\Users\Oblivion\.config\opencode\skills\hermes\whatsapp_qr.py\""
   ```
   The script starts the bridge in `--pair-json` mode, prints a compact ASCII QR in the terminal, and waits (default 180s; `WHATSAPP_PAIR_TTL` overrides). Timeout can be raised for slow phones: `WHATSAPP_PAIR_TTL='600'`.
4. **User scans**: phone → WhatsApp → Settings → Linked Devices → **Link a Device**, then scan the QR rendered above. On success `creds.json` is saved and the script exits 0.
5. **Only now enable** (matches upstream: never leave `WHATSAPP_ENABLED=true` unpaired — every gateway start would burn 30s+ on a phantom bridge):
   - Append `WHATSAPP_ENABLED=true` to the `.env` (keep the `WHATSAPP_MODE` / `WHATSAPP_ALLOWED_USERS` lines from steps 1-2).
   - `hermes gateway restart`, then tail `bridge.log`: `%LOCALAPPDATA%\hermes\whatsapp\bridge.log` for `Bridge started on port 3000` and the gateway log for `[WhatsApp] Bridge ready (status: connected)`.
6. Troubleshooting: `creds.json` never appears → re-run step 3 with a fresh QR (QRs expire ~20s after display, but the bridge regenerates until TTL). Nothing printed at all → Node missing (`node -v`) or bridge deps missing (`%LOCALAPPDATA%\hermes\hermes-agent\scripts\whatsapp-bridge\node_modules`); the script installs deps on first run.

### 3.4 Slack (workspace, not phone-first)
`.env`: `SLACK_BOT_TOKEN=xoxb-...` and `SLACK_ALLOWED_USERS=<your-id>`. Enable `platforms.slack.enabled: true`. (App manifest needed in Slack; see hermes Gateway setup for the scopes.)

### 3.5 Matrix (self-hosted/Element)
`.env`: `MATRIX_HOMESERVER=https://<server>`, `MATRIX_USER_ID=@user:server`, `MATRIX_ACCESS_TOKEN=...`, `MATRIX_ALLOWED_USERS=@user:server`, plus `MATRIX_PASSWORD`/`MATRIX_DEVICE_ID` on first login. Enable `platforms.matrix.enabled: true`.

### 3.6 Other supported platforms
Adapter exact env keys live in `%LOCALAPPDATA%\hermes\hermes-agent\plugins\platforms\<name>\adapter.py` and `%LOCALAPPDATA%\hermes\hermes-agent\gateway\platforms\`. The available adapters are: `telegram, discord, whatsapp, slack, matrix, teams, wecom, feishu, dingtalk, google_chat, line, mattermost, irc, ntfy, simplex, sms, email, buzz, photon, raft, homeassistant, a2a`. To wire one: read its adapter for the `*_BOT_TOKEN` / `*_ALLOWED_USERS` / `*_HOMESERVER` keys, write them to `.env`, set `platforms.<name>.enabled: true`, restart the gateway, then check the log tail for the "Connected" line.

**Common rules for every platform**
- **Allowlist is mandatory & desired**: the gateway denies everyone not in `*_ALLOWED_USERS`. This is the security model — only the user controls the PC.
- After the gateway is up, ask the user to **send `/sethome` from their phone chat** so cron/status land in that DM.

## 4. PC control by default (no extra config)

Setting: the user wants to **control this PC from their phone** (open apps, save files, close windows, run commands, browse). This is the default stance — do NOT disable toolsets.

- **Every `hermes-<platform>` bundle ships the full core toolset** (terminal, process_manage, read_file, write_file, patch, browser, execute_code, delegate_task, computer_use, …) — see `toolsets.py` `_bundle()` / `_HERMES_CORE_TOOLS`. No per-platform tool config needed; a fresh platform already gets PC control.
- **Identical remote-control capability on every channel** — Telegram, Discord, WhatsApp, Slack, Matrix, … all expose the same core tools, so a message from any channel can drive this PC. Verify `hermes tools --summary` shows the desired toolsets `✓` for the platform you're wiring (result: terminal/file/browser/code/computer-use all `✓` for Telegram; other platforms inherit the same bundle).
- **For true desktop automation** (clicking menus, saving in an app, closing windows): make sure **Computer Use** (`computer_use` tool, cua-driver backend) is enabled for the platform toolset — `hermes computer-use` installs the driver once per machine. It does NOT steal the user's cursor; it drives the same desktop session the gateway runs in. Terminal alone covers most remote tasks; computer_use covers the rest (e.g. "save current Ableton project and close the windows" worked end-to-end via `execute_code` + `computer_use`).
- **`tools_search` / `tool` tool config**: leave defaults (`enabled: auto`). Terminal has safety checks (dangerous-command approval) but the user is the only allowed contact, so personal control flows.
- Terminal backend stays local (this PC):
  ```yaml
  terminal:
    backend: local
  ```
- **The only thing that breaks PC control is the model**, not the config: a chat-only model (`nemotron-3.5-lightning-free`) replies "no puedo" without calling tools. Pin the tool-capable default (§2a) and gate it via the tool-call smoke test (§2c).

## 5. Server + gateway: control, auto-start, status

```powershell
& "$env:LOCALAPPDATA\hermes\bin\hermes.exe" gateway install     # register auto-start + start now (once after setup)
& "$env:LOCALAPPDATA\hermes\bin\hermes.exe" gateway start       # open (on)
& "$env:LOCALAPPDATA\hermes\bin\hermes.exe" gateway stop        # close (off)
& "$env:LOCALAPPDATA\hermes\bin\hermes.exe" gateway restart
& "$env:LOCALAPPDATA\hermes\bin\hermes.exe" gateway status      # running? PID + task state
```

**`gateway install` is interactive in this shell.** It asks "Start the gateway now?" and "Start automatically with a Scheduled Task?" (say yes to both) then tries to raise a **UAC prompt** for the Scheduled Task. If UAC is declined it falls back to a Startup-folder shortcut automatically — which is fine and still auto-starts at login:
```
✓ Installed Windows login item: ...\Programs\Startup\Hermes_Gateway.vbs
```
To force the startup-folder path without any prompt: `$env:HERMES_GATEWAY_FORCE_STARTUP=1`.

`gateway status` merges the Scheduled Task + Startup-folder shortcut + live PID — the single source of truth, always report its output. Caveat to tell the user: **the gateway only runs after login** (logout/shutdown = phone can't reach the PC).

## 6. Verify end-to-end (don't skip)

1. **Migrate config first**: run `hermes doctor --fix` once at setup — this PC starts at `_config_version: 0` and needs migrating to the current version (v41+) before things behave.
2. **Config sanity**: `hermes config get model` shows the provider/model you set.
3. **Gateway + adapter up**: tail `%LOCALAPPDATA%\hermes\logs\gateway.log` and confirm lines like `[Telegram] Connected to Telegram (polling mode)` and `Gateway running with N platform(s)`. (The first `/start` may be logged as an ignored "platform ping" — that's normal.)
4. **Real message round-trip + real tool call**: ask the user to send a control request from their phone (e.g. `ejecuta whoami en la terminal`). Confirm in the log:
   ```
   inbound message: platform=telegram user=R chat=<id> msg='ejecuta whoami en la terminal'
   response ready: platform=telegram ... response=N chars  api_calls=N
   [Telegram] Sending response (N chars) to <id>
   ```
   **Bare `api_calls=1` with no intervening tool lines = the model answered without calling tools**. That is the "no puedo controlar tu PC" failure mode → swap to `nemotron-3-ultra-free` (reliable) or `ling-3.0-flash-fin-free` (fast), reset the DM session, and restart.
   **Success evidence in `agent.log`**: lines like `tool terminal_tool ... local environment ready`, `tool execute_code completed`, `tool computer_use completed` followed by a `response ready` in `gateway.log` = the bot actually acted on this PC (terminal ran, code executed, desktop auto-driven).
5. **If it doesn't reply or replies without acting**: check `gateway status`, the log's error lines (unauthorized user, bad token, model 429/401), fix, restart, retry.

## 7. Maintenance: `update`, `check`/`repair`

### update
```powershell
& "$env:LOCALAPPDATA\hermes\bin\hermes.exe" update
& "$env:LOCALAPPDATA\hermes\bin\hermes.exe" gateway restart
```

### check / repair — the stability pass (in order; fix and move on)
1. **Installed?** `hermes --version`. If not → §1a/§1b.
2. **Model configured, tool-capable & reachable?** `hermes config get model`; smoke-test tool-calling with `chat -q "Use the terminal tool to run: whoami" -m <id>` (§2c). If the provider 429s/401s with a set key: **run `hermes auth list` FIRST** — `rate-limited GoUsageLimitError (429)` means the Go quota is simply exhausted (see §2b), not a bad key. The narrow fix is **`opencode-free` + `nemotron-3-ultra-free`** (reliable) or **`ling-3.0-flash-fin-free`** (fast if latency is the complaint) (§2a), Go moved to the END of the fallback chain until it resets.
2b. **Fallback chain sane?** `hermes fallback list` — if the top fallback is a rate-limited/failing provider (e.g. `opencode-go` while capped), a flaky primary 503s straight into a dead endpoint and turns eat minutes. Put a reliable-slow `-free` model first, paid tier last (§2d).
3. **Platform token present & enabled?** `*_BOT_TOKEN` in `.env` and `platforms.<name>.enabled` not `false` in `config.yaml`. Telegram: verify with `getMe` (§3.1). Others: check the log for `Connected`.
4. **Allowlist right?** `*_ALLOWED_USERS` contains the user — if the bot is reachable-but-ignored, this is the usual cause.
5. **Gateway running & auto-start?** `gateway status` shows a live PID and the Startup/Scheduled entry. Re-run `gateway install` if missing.
6. **Log clean?** Tail `gateway.log`; resolve adapter errors (invalid token, `401`, `Model ... is unavailable/not supported` → swap model, circuit-breaker paused → restart).
7. **Models acting, not prose?** If any recent inbound control request produced `api_calls=1` with no tool call, the default model is the weak chat one — pin `nemotron-3-ultra-free` (§2a) or `ling-3.0-flash-fin-free` if it verifies tool-calling (§2c), **reset the DM session** (the live session keeps its pinned model; see the CRITICAL note in §2a), restart the gateway.
8. **Users complain about slow replies?** Measure the split first (tails of `gateway.log`/`agent.log`): `time=N s api_calls=N` vs the `tool X completed (Ns)` lines. If model latency dominates (18-24s per call ≈ nemotron), swap to `ling-3.0-flash-fin-free` (+ reset DM session). If a browser/`execute_code` tool eats the seconds, that's inherent page-load time — model swap won't help.

Fix each issue, then `hermes gateway restart` and re-verify with a real phone message. Prefer the narrowest fix (one env key, one config line) over reinstalling.

### uninstall (clean)
```powershell
& "$env:LOCALAPPDATA\hermes\bin\hermes.exe" uninstall   # removes task, shim, install dir; keeps data
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\hermes"  # optional, to nuke data too
```

## Common pitfalls (Windows)
- `hermes: command not found` → use `& "$env:LOCALAPPDATA\hermes\bin\hermes.exe"` directly.
- Installer: `Environment variable name or value is too long` → User PATH too long; use manual install §1b.
- `NoConsoleScreenBufferError` / TUI crash in this shell → use `chat -q`, never `hermes -c`/plain `chat`.
- WhatsApp QR never appears / wizard "opens a new terminal window" that never opens → the native pairing UI is broken here; use the opencode inline QR renderer (§3.3 step 3) instead of `hermes whatsapp`.
- `opencode-go` model returns 429/401 despite the key working in `/models` → **check `hermes auth list` for `rate-limited GoUsageLimitError (429) (Nh left)`** (quota exhausted, resets ~1 day) vs truly no subscription; either way switch to `opencode-free`.
- Slow replies → split the turn (log): model latency ≈ `API call #N ... latency=Xs`; tool latency ≈ `tool X completed (Ns)`. Model-dominated → `ling-3.0-flash-fin-free` + session reset; browser-dominated → inherent, no fix.
- `ling-3.0-flash-fin-free` gives `503 Endpoint is unavailable` → bursty upstream; auto-retried + falls back to nemotron. Fine if the fallback chain is sane (§2d).
- Bot replies "no puedo controlar tu PC" / answers prose without acting (log shows `api_calls=1`, 0 tool calls) → model is chat-only; pin `nemotron-3-ultra-free`, **reset the DM session** (see §2a CRITICAL), restart gateway.
- `big-pickle` / `laguna-s-2.1-free` 429 for non-opencode-CLI → UA-gated; never pick them for Hermes.
- Antivirus flags `uv.exe` → false positive, whitelist `%LOCALAPPDATA%\hermes\bin`.
- Never store API keys / bot tokens in chat or any log the skill writes — only in `%LOCALAPPDATA%\hermes\.env`.

## 8. Setup completo de control de PC (Browser + Visión + Computer Use)

Para que Hermes controle tu navegador, haga clicks, lea pantalla y actúe por Telegram/Discord/WhatsApp sin "tonterías":

1. **Modelo con Visión nativa por defecto**:
   En `config.yaml`:
   ```yaml
   model:
     provider: opencode-free
     default: nemotron-3-ultra-free
   ```
   *(No usar ling-3.0-flash-fin-free para tareas de navegador ya que no soporta visión nativa).*

2. **Computer Use (cua-driver)**:
   ```powershell
   & "$env:LOCALAPPDATA\hermes\bin\hermes.exe" computer-use install
   ```
   *(Permite capturar escritorio y hacer clicks/movimientos).*

3. **Browser Automation**:
   Los tools de navegador (`browser_navigate`, `browser_click`, `browser_snapshot`, `browser_vision`) se activan automáticamente vía `agent-browser` y Playwright Chromium.

4. **Habilitar todos los Toolsets clave**:
   ```powershell
   & "$env:LOCALAPPDATA\hermes\bin\hermes.exe" tools enable browser terminal file code_execution vision computer_use memory skills todo delegation cronjob session_search clarify search web tts image_gen
   ```

5. **Reiniciar y limpiar sesión DM**:
   Cada vez que cambies el modelo, borra la sesión antigua de Telegram para que coja las capacidades nuevas:
   ```powershell
   & "$env:LOCALAPPDATA\hermes\bin\hermes.exe" sessions delete --yes <session_id>
   & "$env:LOCALAPPDATA\hermes\bin\hermes.exe" gateway restart
   ```