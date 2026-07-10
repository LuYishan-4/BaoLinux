#!/usr/bin/env python3
import os
import subprocess
import shutil
import sys

# === Set to relative path (archos/packages.x86_64 under current working directory) ===
BASE_DIR = os.getcwd()
ARCHISO_PACKAGES_FILE = os.path.join(BASE_DIR, "archos", "packages.x86_64")


def get_installed_packages():
    """Fetch explicitly installed packages from both pacman and yay (AUR)"""
    print("[+] Scanning locally installed packages...")
    all_packages = set()

    # 1. Fetch pacman official repository packages
    try:
        res_pacman = subprocess.run(
            ["pacman", "-Qeq"], capture_output=True, text=True, check=True
        )
        pacman_pkgs = res_pacman.stdout.strip().split("\n")
        all_packages.update(p for p in pacman_pkgs if p)
        print(f"   -> Found official repo packages: {len(pacman_pkgs)}")
    except subprocess.CalledProcessError:
        print("[-] Failed to read pacman package list")
        sys.exit(1)

    # 2. Try to fetch yay (AUR) packages (foreign packages only: -Qm)
    if os.path.exists("/usr/bin/yay"):
        try:
            res_yay = subprocess.run(
                ["yay", "-Qmq"], capture_output=True, text=True, check=True
            )
            yay_pkgs = res_yay.stdout.strip().split("\n")
            all_packages.update(p for p in yay_pkgs if p)
            print(f"   -> Found AUR (yay) packages: {len(yay_pkgs)}")
        except subprocess.CalledProcessError:
            print("[!] Error occurred while reading yay packages, skipping AUR section.")
    else:
        print("[!] yay is not installed, syncing official repo packages only.")

    return all_packages


def sync_to_archiso(packages):
    """Merge the package list with the original Archiso list and write to target"""
    if not os.path.exists(ARCHISO_PACKAGES_FILE):
        print(f"[-] Target build file not found: {ARCHISO_PACKAGES_FILE}")
        print(f"[*] Please verify if 'archos' folder and 'packages.x86_64' exist under ({BASE_DIR}).")
        sys.exit(1)

    print(f"[+] Reading original template: {ARCHISO_PACKAGES_FILE} ...")
    template_packages = set()

    with open(ARCHISO_PACKAGES_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                template_packages.add(line)

    final_list = template_packages.union(packages)

    print(f"[+] Writing a total of {len(final_list)} packages to build configuration...")
    with open(ARCHISO_PACKAGES_FILE, "w") as f:
        f.write("# ==========================================\n")
        f.write("# Package list auto-synced from local + template\n")
        f.write("# ==========================================\n\n")
        for pkg in sorted(final_list):
            f.write(f"{pkg}\n")
    print("[] Package list sync and copy completed successfully!")


if __name__ == "__main__":
    # Display current paths for debugging purposes
    print(f"[i] Current Working Directory: {BASE_DIR}")
    print(f"[i] Target File Path: {ARCHISO_PACKAGES_FILE}")
    print("-" * 50)
    
    sync_to_archiso(get_installed_packages())