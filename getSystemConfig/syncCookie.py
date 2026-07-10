#!/usr/bin/env python3
import os
import shutil
import sys

# === Set to relative path (archos/airootfs under current working directory) ===
BASE_DIR = os.getcwd()
AIROOTFS_DIR = os.path.join(BASE_DIR, "archos", "airootfs")
SKEL_DIR = os.path.join(AIROOTFS_DIR, "etc", "skel")


def check_env():
    """Ensure the workspace exists before running"""
    if not os.path.exists(os.path.join(BASE_DIR, "archos")):
        print(f"[-] Error: 'archos' directory not found in {BASE_DIR}")
        print("[*] Please run this script from your project root directory.")
        sys.exit(1)
    
    # Ensuring root or appropriate write permissions
    if os.geteuid() != 0:
        print("[-] Error: Please run this script with root privileges (sudo python3 ...)")
        print("[*] Root is required to ensure proper file permissions in /etc/skel.")
        sys.exit(1)


def sync_browser_cookies():
    """Extract and sync only login states, cookies, and profiles from active browsers"""
    print("[+] Extracting and syncing browser cookies and sessions...")
    
    # Detect the actual non-root user who ran sudo
    real_user = os.environ.get("SUDO_USER")
    if not real_user:
        print("[-] Error: Could not detect the actual user (SUDO_USER).")
        sys.exit(1)

    user_home = os.path.expanduser(f"~{real_user}")
    os.makedirs(SKEL_DIR, exist_ok=True)

    # Browser paths: (Source Path Relative to Home -> Destination Path Relative to Skel)
    browser_targets = {
        # 1. Firefox (100% working natively in ISO)
        ".mozilla/firefox": ".mozilla/firefox",
        
        # 2. Chromium-based Browsers (Configs & Local Storage)
        ".config/google-chrome": ".config/google-chrome",
        ".config/microsoft-edge": ".config/microsoft-edge",
        ".config/chromium": ".config/chromium",
        ".config/BraveSoftware": ".config/BraveSoftware"
    }

    # Intelligent filter to capture cookies/sessions but completely drop heavy caches
    def cookie_only_filter(path, names):
        ignored = []
        path_lower = path.lower()
        
        # 1. Absolute junk directories to bypass immediately
        junk_keywords = ["tmp", "temp", "crashreports", "minidumps", "logs", "history"]
        if any(kw in path_lower for kw in junk_keywords):
            return names

        # 2. Heavy caching directories holding web images/assets (We want to skip these)
        cache_keywords = ["cache", "cached", "code cache", "gpu-cache", "gpu cache", "cachestorage"]

        for name in names:
            name_lower = name.lower()
            
            # Skip explicit junk filenames
            if any(kw in name_lower for kw in junk_keywords):
                ignored.append(name)
                continue
                
            # If it's a caching mechanism, inspect closer
            if any(ck in name_lower for ck in cache_keywords):
                # CRITICAL: DO NOT ignore if it contains authentication or extension keywords
                # Chromium uses 'Cookies', 'Login Data'; Firefox uses 'cookies.sqlite', 'sessionstore'
                whitelist = ["cookie", "login", "session", "extension", "secure", "key", "cert"]
                if not any(wl in name_lower for wl in whitelist):
                    ignored.append(name)
                    
        return ignored

    synced_count = 0
    for src_rel, dest_rel in browser_targets.items():
        src_full = os.path.join(user_home, src_rel)
        dest_full = os.path.join(SKEL_DIR, dest_rel)

        if os.path.exists(src_full):
            print(f"   -> Processing browser profile: ~/{src_rel}")
            
            # Clean target destination directory if it already exists
            if os.path.exists(dest_full):
                shutil.rmtree(dest_full)
                
            # Ensure the parent directory structure exists in skel
            os.makedirs(os.path.dirname(dest_full), exist_ok=True)
            
            # Perform copy with the fine-tuned filtering mechanism
            shutil.copytree(src_full, dest_full, symlinks=True, ignore=cookie_only_filter)
            print(f"      [✓] Successfully synced to /etc/skel/{dest_rel}")
            synced_count += 1
        else:
            # Silent skip if the user doesn't use this specific browser
            pass

    if synced_count == 0:
        print("[!] Warning: No browser directories found on your host machine.")
    else:
        print(f"\n[] Done! Successfully backed up {synced_count} browser profile(s).")
        print(f"[i] All session templates are safely stored at: {SKEL_DIR}")


if __name__ == "__main__":
    print(f"[i] Current Working Directory: {BASE_DIR}")
    print(f"[i] Targeting Directory: {SKEL_DIR}")
    print("-" * 50)
    
    check_env()
    sync_browser_cookies()