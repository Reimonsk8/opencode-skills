---
name: router-update
description: Use when the user asks to update the LAN router/OpenRouter proxy, sync model lists, or runs /router-update. Checks if 9router is running on 192.168.1.74, starts/updates it over SSH, and rewrites the provider.proxy models in the opencode config to match what the router currently serves.
---

# Router Update

The router is **9router** — a node binary installed globally via npm on `192.168.1.74`, serving an OpenAI-compatible API at `http://192.168.1.74:20128/v1`. opencode connects to it through the `proxy` provider in `C:\Users\Oblivion\.config\opencode\opencode.jsonc` (`baseURL` port `20128`).

All SSH commands run passwordless: `ssh root@192.168.1.74 "..."`.

## Steps

### 1. Check if the router is running

```bash
ssh root@192.168.1.74 "ss -tlnp | grep -q ':20128' && echo UP || echo DOWN"
```

### 2. Check if an update is available

```bash
ssh root@192.168.1.74 "npm ls -g 9router 2>&1 | grep 9router | sed 's/.*@//'"
ssh root@192.168.1.74 "npm view 9router version"
```

Compare the two. If equal → no update needed. If different → update.

### 3. Update (only if versions differ)

```bash
ssh root@192.168.1.74 "npm install -g 9router@latest"
```

Then restart the router to load the new version (also do this whenever the router is NOT running):

```bash
ssh root@192.168.1.74 "pkill -f 'node /usr/bin/9router'; sleep 1; nohup node /usr/bin/9router -n --skip-update >> /root/9router.log 2>&1 &"
```

`--skip-update` is kept because this skill manages updates explicitly. If the router was already running and current, skip this step.

Wait for startup: `ssh root@192.168.1.74 "sleep 2; ss -tlnp | grep -q ':20128' && echo UP || echo DOWN"`.

### 4. Sync the model list into the opencode config

Fetch the current models the router offers:

```bash
ssh root@192.168.1.74 "curl -s http://127.0.0.1:20128/v1/models"
```

Parse `data[].id` from the response. Then edit `C:\Users\Oblivion\.config\opencode\opencode.jsonc`:

- Replace the entire `provider.proxy.models` object with one entry per model id, matching the existing shape:
  ```json
  "models": {
    "<model-id>": { "name": "<model-id>" },
    ...
  }
  ```
- Do not touch `baseURL`, `apiKey`, `name`, or any other top-level keys.

## Notes

- The router responds on `127.0.0.1:20128` from the server itself; no auth key needed for the models endpoint.
- After editing the config, remind the user to restart opencode for the new model list to load.