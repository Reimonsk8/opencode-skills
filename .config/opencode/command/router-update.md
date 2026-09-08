---
description: Check/update the LAN OpenRouter proxy (9router) and sync opencode proxy models.
agent: build
---

Follow the `router-update` skill: check if 9router is running on 192.168.1.74, update it if a newer version exists, restart it, and rewrite the `provider.proxy.models` in the opencode config with the models it currently offers.