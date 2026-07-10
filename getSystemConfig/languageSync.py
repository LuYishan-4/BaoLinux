#!/usr/bin/env python3
import os
import shutil
import sys
import subprocess


class BaseLanguageSync:

    def __init__(self, user_home, airootfs_dir, skel_dir):
        self.user_home = user_home
        self.airootfs_dir = airootfs_dir
        self.skel_dir = skel_dir

    def get_required_fonts(self):

        return []

    def get_input_method_configs(self):

        return []

    def get_environment_variables(self):

        return {}


class TraditionalChineseSync(BaseLanguageSync):

    def get_required_fonts(self):
        return [
            "/usr/share/fonts/TTF",
            "/usr/share/fonts/noto-cjk",
            "/usr/share/fonts/opentype"
        ]

    def get_input_method_configs(self):
        return [".config/fcitx5", ".local/share/fcitx5"]

    def get_environment_variables(self):
        return {
            "GTK_IM_MODULE": "fcitx",
            "QT_IM_MODULE": "fcitx",
            "XMODIFIERS": "@im=fcitx",
            "SDL_IM_MODULE": "fcitx",
            "GLFW_IM_MODULE": "ibus"
        }


class EnglishSync(BaseLanguageSync):
    def get_required_fonts(self):
        return ["/usr/share/fonts/TTF"]

    def get_input_method_configs(self):
        return []

    def get_environment_variables(self):
        return {
            "LANG": "en_US.UTF-8",
            "LC_ALL": "en_US.UTF-8"
        }



class BaoLinuxEnvInitializer:


    LANGUAGE_MAPPING = {
        "zh_TW": TraditionalChineseSync,
        "en_US": EnglishSync
    }

    def __init__(self, language_code="zh_TW"):

        self.base_dir = os.getcwd()
        self.airootfs_dir = os.path.join(self.base_dir, "archos", "airootfs")
        self.skel_dir = os.path.join(self.airootfs_dir, "etc", "skel")
        

        self._check_privileges()
        self.real_user = os.environ.get("SUDO_USER")
        self.user_home = os.path.expanduser(f"~{self.real_user}")


        if language_code not in self.LANGUAGE_MAPPING:
            print(f"[!] Unsupported language: {language_code}. Fallback to 'zh_TW'.")
            language_code = "zh_TW"
        
        self.language_code = language_code

        self.language_handler = self.LANGUAGE_MAPPING[language_code](
            self.user_home, self.airootfs_dir, self.skel_dir
        )

    def _check_privileges(self):

        if os.geteuid() != 0:
            print("[-] Error: Please run this script with root privileges (sudo python3 ...)")
            sys.exit(1)
        if not os.path.exists(os.path.join(self.base_dir, "archos")):
            print(f"[-] Error: 'archos' directory not found in {self.base_dir}")
            sys.exit(1)

    def sync_fonts(self):
        print(f"[+] [{self.language_code}] Syncing specified fonts...")
        iso_font_dir = os.path.join(self.airootfs_dir, "usr", "share", "fonts", "BaoFonts")
        
        if os.path.exists(iso_font_dir):
            shutil.rmtree(iso_font_dir)
            
        font_paths = self.language_handler.get_required_fonts()
        copied = False

        for path in font_paths:
            if os.path.exists(path):
                folder_name = os.path.basename(path)
                target = os.path.join(iso_font_dir, folder_name)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                shutil.copytree(path, target, symlinks=True)
                print(f"   -> Copied: {path}")
                copied = True
                
        if not copied:
            print("   i> No fonts required or found for this profile.")

    def sync_input_methods(self):
        print(f"[+] [{self.language_code}] Syncing input method configurations...")
        configs = self.language_handler.get_input_method_configs()
        
        for rel_path in configs:
            src_full = os.path.join(self.user_home, rel_path)
            dest_full = os.path.join(self.skel_dir, rel_path)

            if os.path.exists(src_full):
                if os.path.exists(dest_full):
                    shutil.rmtree(dest_full)
                os.makedirs(os.path.dirname(dest_full), exist_ok=True)
                shutil.copytree(src_full, dest_full, symlinks=True, 
                                ignore=shutil.ignore_patterns("*.log", "socket", "pid"))
                print(f"   -> Synced config: {rel_path} -> /etc/skel/{rel_path}")
            else:
                print(f"   i> Skipped: ~/{rel_path} not found.")

    def inject_environment_variables(self):
        print(f"[+] [{self.language_code}] Injecting environment variables to /etc/environment...")
        etc_env_path = os.path.join(self.airootfs_dir, "etc", "environment")
        os.makedirs(os.path.dirname(etc_env_path), exist_ok=True)

        env_dict = self.language_handler.get_environment_variables()
        if not env_dict:
            print("   i> No environment variables to inject.")
            return

        existing_content = ""
        if os.path.exists(etc_env_path):
            with open(etc_env_path, "r") as f:
                existing_content = f.read()

        with open(etc_env_path, "a") as f:
            if not existing_content.endswith("\n") and existing_content != "":
                f.write("\n")
            for key, val in env_dict.items():
                line = f"{key}={val}"
                if key not in existing_content:
                    f.write(f"{line}\n")
                    print(f"   -> Added: {line}")

    def run_all(self):
        print(f"=== Starting BaoLinux Env Sync [Profile: {self.language_code}] ===")
        self.sync_fonts()
        self.sync_input_methods()
        self.inject_environment_variables()
        print(f"[] Env Sync for {self.language_code} completed successfully!\n")


if __name__ == "__main__":
    initializer = BaoLinuxEnvInitializer(language_code="zh_TW")
    initializer.run_all()