#!/usr/bin/env python3
import os
import shutil
import sys
import re


BASE_DIR = os.getcwd()
AIROOTFS_DIR = os.path.join(BASE_DIR, "archos", "airootfs")
SKEL_DIR = os.path.join(AIROOTFS_DIR, "etc", "skel")


def check_env():
    if os.geteuid() != 0:
        print("[-] Error: Please run this script with root privileges (sudo python3 ...)")
        sys.exit(1)
    if not os.path.exists(os.path.join(BASE_DIR, "archos")):
        print(f"[-] Error: 'archos' directory not found in {BASE_DIR}")
        sys.exit(1)


def fix_hardcoded_paths(target_dir, original_user):

    print("   -> fixing hardcoded paths in configuration files...")
    old_home = f"/home/{original_user}"

    text_extensions = {'.conf', '.json', '.yaml', '.yml', '.toml', '.sh', '.zsh', 'rc'}

    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if any(file.endswith(ext) or ext in file for ext in text_extensions):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    if old_home in content:
         
                        new_content = content.replace(old_home, "$HOME")
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                except Exception:
                    pass 


def sync_all_software_dotfiles():
    print("[+] Starting comprehensive synchronization of all software configurations on the host...")
    
    real_user = os.environ.get("SUDO_USER")
    if not real_user:
        print("[-] Error: Unable to detect the actual user who triggered sudo (SUDO_USER)")
        return

    user_home = os.path.expanduser(f"~{real_user}")
    os.makedirs(SKEL_DIR, exist_ok=True)
    
    
    all_dotfiles = [
        ".config",         
        ".local/share",   
        ".bashrc",   
        ".zshrc",  
        ".zsh",  
        ".p10k.zsh",   
        ".vimrc",  
        ".tmux.conf"
    ]

    def ultra_config_filter(path, names):
        ignored = []
        path_lower = path.lower()

        garbage_keywords = ["tmp", "temp", "crashreports", "minidumps", "logs", "history", "socket", "pid"]
        if any(kw in path_lower for kw in garbage_keywords):
            return names

        cache_keywords = [
            "cache", "cached", "code cache", "gpu-cache", "gpu cache", 
            "cachestorage", "service worker", "application cache"
        ]

     
        heavy_apps_garbage = [
            "google-chrome", "microsoft-edge", "chromium", "brave",
            "discord", "spotify", "slack", "yarn", "npm", "electron", 
            "jetbrains", "cursor", "vscode", "code", "insomnia"
        ]

        for name in names:
            name_lower = name.lower()
            

            if any(kw in name_lower for kw in garbage_keywords):
                ignored.append(name)
                continue

            if any(ck in name_lower for ck in cache_keywords) or any(app in name_lower for app in heavy_apps_garbage):

                whitelist = ["cookie", "login", "session", "extension", "secure", "key", "cert", "config", "preferences", "profile"]
                if not any(wl in name_lower for wl in whitelist):
                    ignored.append(name)
                    
        return ignored

    for item in all_dotfiles:
        src_path = os.path.join(user_home, item)
        dest_path = os.path.join(SKEL_DIR, item)
        
        if os.path.exists(src_path):
            print(f"   -> fix: ~/{item}")
            

            if os.path.exists(dest_path):
                if os.path.isdir(dest_path):
                    shutil.rmtree(dest_path)
                else:
                    os.remove(dest_path)
            
      
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            
   
            if os.path.isdir(src_path):
                shutil.copytree(src_path, dest_path, symlinks=True, ignore=ultra_config_filter)
          
                fix_hardcoded_paths(dest_path, real_user)
            else:
                shutil.copy2(src_path, dest_path)
                
 
    print("\n[] Done！")


if __name__ == "__main__":
    print(f"[i] now: {BASE_DIR}")
    print(f"[i] airootfs : {SKEL_DIR}")
    print("-" * 60)
    
    check_env()
    sync_all_software_dotfiles()