---
name: jev-setup
description: Use when the user runs /jev-setup or asks to install, check status, turn on/off, update, or test JEV (TypeSafe Jev). Always reports current status first (skill present, API key, SDK, API ping), then asks what to do.
---

# JEV Setup

Jev is TypeSafe's System One model (`jev-latest`): POST state + typed questions (Choice/Score/Noul) to `https://api.typesafe.ai/v1/systemone`, get typed answers back. Our setup is three pieces: the `typesafe-ai` skill + the `TYPESAFE_API_KEY` env var + the `typesafe-sdk` pip package.

## 1. Status check (ALWAYS run first, then ask)

Run these checks, report the result as a table, then use the question tool to ask what the user wants to do. Change nothing before they pick.

```batch
if exist "%USERPROFILE%\.agents\skills\typesafe-ai\SKILL.md" (echo SKILL: PRESENT) else (echo SKILL: MISSING)
if defined TYPESAFE_API_KEY (echo KEY: SET) else (echo KEY: MISSING)
reg query HKCU\Environment /v TYPESAFE_API_KEY 2>nul || echo KEY-PERSISTENT: MISSING
pip show typesafe-sdk 2>nul | findstr /C:"Name" /C:"Version" || echo SDK: MISSING
```

If the key is SET, ping the API (valid key returns `answers`, `401` = bad key):

```batch
curl -s -X POST https://api.typesafe.ai/v1/systemone -H "Authorization: Bearer %TYPESAFE_API_KEY%" -H "Content-Type: application/json" -d "{\"state\":\"ping\",\"model\":\"jev-latest\",\"questions\":{\"ok\":{\"type\":\"noul\",\"instructions\":\"Is this a test?\"}}}"
```

Status meaning:

- NOT INSTALLED = skill file MISSING
- INSTALLED + ON = skill present + key SET + ping returns `answers`
- INSTALLED + OFF = skill present but key MISSING (or ping fails)
- SDK MISSING = `pip install` needed in any case

Also confirm opencode loads the skill: `C:\Users\Oblivion\.config\opencode\opencode.jsonc` → `skills.paths` must contain `C:\Users\Oblivion\.agents\skills`. If missing, add it.

Then ask via the question tool (options: Install / Turn on / Turn off / Update / Test / Nothing). Execute only the pick, then re-run the status check.

## 2. Actions

### Install (skill + SDK + key)

```batch
mkdir "%USERPROFILE%\.agents\skills\typesafe-ai"
curl -sL https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md -o "%USERPROFILE%\.agents\skills\typesafe-ai\SKILL.md"
pip install typesafe-sdk
```

Get a key at https://console.typesafe.ai/keys, then persist it:

```batch
setx TYPESAFE_API_KEY "paste-key-here"
```

Restart the shell and opencode after `setx`, then re-run the status check.

### Turn on

```batch
setx TYPESAFE_API_KEY "paste-key-here"
```

Restart shell/opencode. If the skill file is MISSING, do Install instead.

### Turn off

```batch
reg delete HKCU\Environment /v TYPESAFE_API_KEY /f
set TYPESAFE_API_KEY=
```

Skill + SDK stay installed; Jev calls fail until a key is set again. Restart opencode.

### Update

```batch
curl -sL https://raw.githubusercontent.com/typesafe-ai/skills/main/skills/typesafe-ai/SKILL.md -o "%USERPROFILE%\.agents\skills\typesafe-ai\SKILL.md"
pip install -U typesafe-sdk
```

### Test

Run the curl ping from section 1 plus:

```batch
python -c "from typesafe_sdk import TypeSafeClient; print('sdk ok')"
```

## Notes

- Never print or commit the key value. Report SET/MISSING + ping result only.
- Live docs are the source of truth: https://docs.typesafe.ai/llms.txt — check there if install steps or SDK usage changed.
- After any `setx`/key change, remind the user to restart opencode for it to take effect.
