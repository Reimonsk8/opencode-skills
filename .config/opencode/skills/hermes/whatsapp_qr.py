# WhatsApp pairing QR for opencode: runs the Hermes Baileys bridge in
# --pair-json mode (no TTY needed), captures the QR string, renders it as an
# ASCII QR in the terminal, polls until creds.json appears, then exits.
# Run with the Hermes venv python (has the qrcode package):
#   %LOCALAPPDATA%\hermes\hermes-agent\.venv\Scripts\python.exe whatsapp_qr.py
import json, os, subprocess, sys, time
from pathlib import Path

HERMES_HOME = Path(os.environ.get("LOCALAPPDATA")) / "hermes"
SESSION = HERMES_HOME / "whatsapp" / "session"
BRIDGE = HERMES_HOME / "hermes-agent" / "scripts" / "whatsapp-bridge"
LOG = HERMES_HOME / "whatsapp" / "bridge_pair.log"
TTL = float(os.environ.get("WHATSAPP_PAIR_TTL", "180"))

def qr_to_ascii(data: str) -> str:
    # Half-block render: two modules per char row, one char per module column.
    # ~half the width and height of a "██"-per-module render, same contrast
    # (dark = block glyphs, light = spaces) so it scans on the same terminals.
    import qrcode
    q = qrcode.QRCode(border=1, box_size=1)
    q.add_data(data)
    q.make(fit=True)
    rows = q.get_matrix()
    if len(rows) % 2:
        rows = rows + [[False] * len(rows[0])]
    lines = []
    for i in range(0, len(rows), 2):
        top, bot = rows[i], rows[i + 1]
        lines.append("".join(
            "\u2588" if t and b else
            "\u2580" if t else
            "\u2584" if b else " "
            for t, b in zip(top, bot)))
    return "\n".join(lines)

def main() -> int:
    SESSION.mkdir(parents=True, exist_ok=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    if not BRIDGE.exists():
        print(f"bridge.js not found: {BRIDGE}")
        return 1
    if not (BRIDGE / "node_modules").exists():
        print("Installing bridge deps (npm install)...")
        r = subprocess.run(["npm", "install", "--no-fund", "--no-audit", "--progress=false"],
                           cwd=BRIDGE, capture_output=True, text=True,
                           encoding="utf-8", errors="replace")
        if r.returncode:
            print("npm install failed:", r.stderr[-2000:])
            return 1
    node = os.environ.get("HERMES_NODE") or "node"
    f = open(LOG, "w", encoding="utf-8", errors="replace")
    try:
        proc = subprocess.Popen(
            [node, str(BRIDGE / "bridge.js"), "--pair-only", "--pair-json",
             "--session", str(SESSION)],
            cwd=BRIDGE, stdout=f, stderr=subprocess.STDOUT, env=os.environ,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    except FileNotFoundError:
        print("node not found on PATH")
        return 1
    print("Waiting for WhatsApp QR (phone: WhatsApp > Linked Devices > Link a Device)...")
    shown = False
    start = time.time()
    while time.time() - start < TTL:
        if (SESSION / "creds.json").exists():
            print("\nPaired. creds.json saved.")
            return 0
        if not shown:
            try:
                for line in LOG.read_text(encoding="utf-8", errors="replace").splitlines():
                    try:
                        evt = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if evt.get("event") == "qr" and evt.get("qr"):
                        print("\n================= SCAN THIS QR =================")
                        print(qr_to_ascii(evt["qr"]))
                        print("================================================")
                        shown = True
                        break
            except FileNotFoundError:
                pass
        if proc.poll() is not None and proc.returncode != 0:
            tail = LOG.read_text(encoding="utf-8", errors="replace")[-1500:]
            print("Bridge exited", proc.returncode, ":", tail)
            return 1
        time.sleep(1)
    print(f"Timed out after {TTL:.0f}s, no scan. Exiting.")
    proc.kill()
    return 1

if __name__ == "__main__":
    sys.exit(main())