#!/usr/bin/env python3
import os
import subprocess
import shutil
import sys

# === Set to relative path (archos/airootfs under current working directory) ===
BASE_DIR = os.getcwd()
AIROOTFS_DIR = os.path.join(BASE_DIR, "archos", "airootfs")


def check_env():
    """Ensure the script is run with root privileges for copying system configs"""
    if os.geteuid() != 0:
        print("[-] Error: Please run this script with root privileges (sudo python3 ...)")
        sys.exit(1)
    if not os.path.exists(os.path.join(BASE_DIR, "archos")):
        print(f"[-] Error: 'archos' directory not found in {BASE_DIR}")
        sys.exit(1)


def sync_system_configs():
    """Copy critical global system configuration files"""
    print("[+] Syncing global system configurations...")
    
    # Map of source configuration files to their relative destination in airootfs
    config_map = {
        "/etc/vconsole.conf": "etc/vconsole.conf",
        "/etc/locale.conf": "etc/locale.conf",
        "/etc/bash.bashrc": "etc/bash.bashrc",
        "/etc/environment": "etc/environment",
    }

    for src, rel_dest in config_map.items():
        if os.path.exists(src):
            dest = os.path.join(AIROOTFS_DIR, rel_dest)
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(src, dest)
            print(f"   -> Copied: {src} -> {rel_dest}")
        else:
            print(f"   i> Skipped (Not Found): {src}")


def sync_user_dotfiles():
    """Copy current user's desktop configs & dotfiles to /etc/skel (with ignore rules)"""
    print("[+] Syncing user desktop configurations (Dotfiles)...")
    
    # Get the actual user who invoked sudo
    real_user = os.environ.get("SUDO_USER")
    if not real_user:
        print("[-] Warning: Could not detect the actual user (SUDO_USER). Skipping dotfiles.")
        return

    user_home = os.path.expanduser(f"~{real_user}")
    skel_dir = os.path.join(AIROOTFS_DIR, "etc/skel")
    os.makedirs(skel_dir, exist_ok=True)
    
    dotfiles_to_sync = [
        ".config",      # Main target (contains themes, DE/WM configs)
        ".bashrc",      # Shell configs
        ".zshrc", 
        ".zsh", 
        ".p10k.zsh"     # Powerlevel10k theme if used
    ]

    # Filter function to avoid copying massive cache/session data
    def ignore_patterns(path, names):
        ignored = []
        path_lower = path.lower()
        
        # General garbage / temporary keywords
        keywords = ["cache", "cached", "tmp", "temp", "session", "storage", "history", "logs"]
        
        # If the directory path itself matches keywords, skip everything inside it
        if any(kw in path_lower for kw in keywords):
            return names

        # Specific heavy application directories inside .config to exclude or filter heavily
        specific_heavy_apps = [
            "google-chrome", "microsoft-edge", "chromium", 
            "discord", "spotify", "slack", "slack-desktop",
            "yarn", "npm", "electron", "jetbrains", "code", "insomnia"
        ]

        for name in names:
            name_lower = name.lower()
            if any(kw in name_lower for kw in keywords) or any(app in name_lower for app in specific_heavy_apps):
                ignored.append(name)
        return ignored

    for item in dotfiles_to_sync:
        src_path = os.path.join(user_home, item)
        if os.path.exists(src_path):
            dest_path = os.path.join(skel_dir, item)
            
            # Clean up destination if it already exists to avoid conflict
            if os.path.exists(dest_path):
                if os.path.isdir(dest_path):
                    shutil.rmtree(dest_path)
                else:
                    os.remove(dest_path)
                    
            if os.path.isdir(src_path):
                # Using copytree with filter to avoid freezing
                shutil.copytree(src_path, dest_path, symlinks=True, ignore=ignore_patterns)
            else:
                shutil.copy2(src_path, dest_path)
            print(f"   -> Synced dotfile: {item} to /etc/skel/{item}")


def sync_systemd_services():
    """Enable currently active crucial systemd services in the live environment"""
    print("[+] Syncing Systemd services...")
    
    # Common services that are usually required to auto-start in a desktop distro
    essential_services = [
        "NetworkManager.service", 
        "bluetooth.service",
        "lightdm.service", 
        "gdm.service", 
        "sddm.service",
        "ly.service"
    ]
    
    for service in essential_services:
        # Check if the service is currently enabled on the host machine
        result = subprocess.run(["systemctl", "is-enabled", service], capture_output=True, text=True)
        if result.stdout.strip() == "enabled":
            
            # Determine the correct systemd target directory
            if service in ["lightdm.service", "gdm.service", "sddm.service", "ly.service"]:
                # Display managers usually go to display-manager.service link
                wants_dir = os.path.join(AIROOTFS_DIR, "etc/systemd/system")
                link_name = os.path.join(wants_dir, "display-manager.service")
            else:
                # Standard multi-user services
                wants_dir = os.path.join(AIROOTFS_DIR, "etc/systemd/system/multi-user.target.wants")
                link_name = os.path.join(wants_dir, service)
                
            os.makedirs(wants_dir, exist_ok=True)
            target_path = f"/usr/lib/systemd/system/{service}"
            
            if os.path.exists(link_name) or os.path.islink(link_name):
                os.remove(link_name)
                
            os.symlink(target_path, link_name)
            print(f"   -> Enabled Service: {service}")


if __name__ == "__main__":
    print(f"[i] Current Working Directory: {BASE_DIR}")
    print(f"[i] Target airootfs Directory: {AIROOTFS_DIR}")
    print("-" * 50)
    
    check_env()
    sync_system_configs()
    sync_user_dotfiles()
    sync_systemd_services()
    
    print("\n[] Desktop configurations and environment sync completed successfully!")