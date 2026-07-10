import json
import os
import subprocess
import sys
from pathlib import Path

BASE_DIR = Path.cwd().resolve()
ARCHOS_DIR = BASE_DIR / "archos"
CONFIG_FILE = ARCHOS_DIR / "global_config.json"


def load_config(payload: str | None = None):
    if payload:
        data = json.loads(payload)
    elif len(sys.argv) > 1:
        data = json.loads(sys.argv[1])
    else:
        data = {}

    return {
        "resolution": data.get("resolution", "1920x1080"),
        "kernel_params": data.get("kernel_params", "quiet splash"),
        "timeout": data.get("timeout", "5"),
        "theme_name": data.get("theme_name", "BaoLinux-Theme"),
        "root_password": data.get("root_password", ""),
    }


def write_config(config: dict):
    ARCHOS_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    print(f"[+] Saved merged config to {CONFIG_FILE}")


def run_python_script(script_name: str):
    script_path = BASE_DIR / script_name
    if not script_path.exists():
        print(f"[i] Skipped missing helper: {script_name}")
        return

    print(f"[+] Running {script_name}...")
    result = subprocess.run([sys.executable, str(script_path)], cwd=BASE_DIR, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.returncode != 0:
        print(f"[-] {script_name} exited with code {result.returncode}")
        if result.stderr:
            print(result.stderr.strip())


def main():
    print("[+] BaoLinux Python sync helper started")
    config = load_config(sys.argv[1] if len(sys.argv) > 1 else None)
    write_config(config)

    run_python_script("getSystemConfig/syncDesktop.py")
    run_python_script("getSystemConfig/syncSoftwareConfig.py")

    print("[] BaoLinux sync helper finished")


if __name__ == "__main__":
    main()
