#!/usr/bin/env python3
import os
import shutil
import glob
import sys

BASE_DIR = os.getcwd()

AIROOTFS_DIR = os.path.join(
    BASE_DIR,
    "archos",
    "airootfs"
)

BACKUP_DIR = os.path.join(
    AIROOTFS_DIR,
    "usr",
    "share",
    "archos-wayland",
    "configs"
)

CONFIG_MAP = {
    "hyprland": [
        ".config/hypr",
        ".config/waybar",
        ".config/fuzzel",
        ".config/mako",
        ".config/waypaper",
        ".config/swayosd",
        ".config/wayvnc",
        ".config/fcitx5",
        ".config/gtk-3.0",
        ".config/gtk-4.0",
        ".config/QtProject.conf",
        ".config/kitty",
        ".config/yazi",
        ".config/starship.toml"
    ],

    "plasma": [
        ".config/plasma*",
        ".config/plasma-workspace",

        ".config/kde*",
        ".config/KDE",

        ".config/kdeglobals",
        ".config/kglobalshortcutsrc",

        ".config/kwinrc",
        ".config/kwinrulesrc",
        ".config/kwinoutputconfig.json",

        ".config/ksmserverrc",
        ".config/kxkbrc",
        ".config/kscreenlockerrc",

        ".config/plasma-org.kde.plasma.desktop-appletsrc",
        ".config/plasmashellrc",
        ".config/powerdevilrc",
        ".config/plasma-localerc",

        ".config/fcitx5",
        ".config/gtk-3.0",
        ".config/gtk-4.0",
        ".config/QtProject.conf",

        ".local/share/kscreen",
        ".local/share/plasma*"
    ]
}

def get_real_user():
    user = os.environ.get("SUDO_USER")
    if not user:
        print("[-] Please run with sudo")
        sys.exit(1)
    return user

def detect_desktops(home):
    desktops = []
    # Hyprland
    if os.path.exists(
        os.path.join(
            home,
            ".config",
            "hypr"
        )
    ):
        desktops.append("hyprland")
    # KDE Plasma
    if (
        os.path.exists(
            os.path.join(
                home,
                ".config",
                "plasma-workspace"
            )
        )
        or
        os.path.exists(
            os.path.join(
                home,
                ".config",
                "kdeglobals"
            )
        )
        or
        os.path.exists(
            os.path.join(
                home,
                ".config",
                "kwinrc"
            )
        )
    ):
        desktops.append("plasma")


    return desktops

def copy_item(src, dst):
    if os.path.isdir(src):
        shutil.copytree(
            src,
            dst,
            dirs_exist_ok=True,
            symlinks=True
        )
    else:
        os.makedirs(
            os.path.dirname(dst),
            exist_ok=True
        )
        shutil.copy2(
            src,
            dst
        )

def sync_desktop(home, desktop):
    print(
        f"[+] Syncing {desktop}"
    )
    desktop_backup = os.path.join(
        BACKUP_DIR,
        desktop
    )
    os.makedirs(
        desktop_backup,
        exist_ok=True
    )
    for item in CONFIG_MAP[desktop]:
        if "*" in item:
            paths = glob.glob(
                os.path.join(
                    home,
                    item
                )
            )
        else:
            paths = [
                os.path.join(
                    home,
                    item
                )
            ]
        for src in paths:


            if not os.path.exists(src):
                continue


            rel = os.path.relpath(
                src,
                home
            )


            dst = os.path.join(
                desktop_backup,
                rel
            )


            print(
                f"    -> {desktop}/{rel}"
            )


            try:

                copy_item(
                    src,
                    dst
                )

            except Exception as e:

                print(
                    f"       failed: {e}"
                )



def main():


    user = get_real_user()


    home = os.path.expanduser(
        f"~{user}"
    )


    if not os.path.exists(
        os.path.join(
            BASE_DIR,
            "archos"
        )
    ):

        print(
            "[-] archos directory not found"
        )

        sys.exit(1)



    # 清理舊備份
    if os.path.exists(BACKUP_DIR):

        print(
            "[+] Removing old Wayland backup"
        )

        shutil.rmtree(
            BACKUP_DIR
        )


    os.makedirs(
        BACKUP_DIR,
        exist_ok=True
    )



    desktops = detect_desktops(
        home
    )


    if not desktops:

        print(
            "[-] No Wayland desktop detected"
        )

        return



    print(
        "[+] Detected:"
    )

    for d in desktops:
        print(
            f"    {d}"
        )


    print()


    for d in desktops:

        sync_desktop(
            home,
            d
        )



    print()
    print(
        "[✓] Wayland configuration synchronized"
    )
    print(
        "[✓] Saved:"
    )
    print(
        f"    {BACKUP_DIR}"
    )

if __name__ == "__main__":
    main()
