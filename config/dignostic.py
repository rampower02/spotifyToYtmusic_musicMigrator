# diagnostics_check_auth.py
import json, os
from pathlib import Path

CONFIG_DIR = "config"
auth_file = Path(CONFIG_DIR) / "ytmusic_auth.json"

if not auth_file.exists():
    print("File non trovato:", auth_file)
    raise SystemExit(1)

with auth_file.open("r", encoding="utf-8-sig") as f:
    try:
        data = json.load(f)
    except Exception as e:
        print("JSON invalido:", e)
        raise SystemExit(1)

print("Top-level keys:", list(data.keys()))
if "installed" in data:
    print("Found 'installed' keys:", list(data["installed"].keys()))
    print("client_id:", data["installed"].get("client_id"))
    print("client_secret:", data["installed"].get("client_secret"))
elif "web" in data:
    print("Found 'web' keys:", list(data["web"].keys()))
    print("client_id:", data["web"].get("client_id"))
    print("client_secret:", data["web"].get("client_secret"))
else:
    print("File JSON non contiene 'installed' o 'web'. Top-level looks like:", list(data.keys()))
    print("Try to read client_id/client_secret at top-level:")
    print("client_id:", data.get("client_id"))
    print("client_secret:", data.get("client_secret"))
