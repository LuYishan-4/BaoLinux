#!/usr/bin/env bash

# =====================================================================
# 1. Base Paths and Settings
# =====================================================================
BASE_DIR=$(pwd)
ARCHOS_DIR="$BASE_DIR/archos"
PACKAGES_FILE="$ARCHOS_DIR/packages.x86_64"
AIROOTFS_DIR="$ARCHOS_DIR/airootfs"
SYNC_SCRIPT="$BASE_DIR/sync_all_configs.py" # Calls your previous Python sync script

# Ensure the script is run with root/sudo privileges to modify systemd links and global files
if [ "$EUID" -ne 0 ]; then
    echo "[-] Error: This script requires administrative privileges. Please run with sudo:"
    echo "    sudo ./switch_de_and_sync.sh"
    exit 1
fi

# Ensure the project directory structure is correct
if [ ! -d "$ARCHOS_DIR" ]; then
    echo "[-] Error: Cannot find '$ARCHOS_DIR' directory. Please run this script from the project root."
    exit 1
fi

echo "[+] Initializing BaoLinux Environment Management Wizard..."

# =====================================================================
# 2. Prompt to Change/Switch Current Desktop Environment (DE)
# =====================================================================
if whiptail --title "BaoLinux Desktop Environment Management" --yesno "Do you want to switch or configure the Desktop Environment (DE) for this ISO?\n\n(Choosing 'No' will skip directly to the configuration sync stage)" 12 60; then
    
    # Allow the user to choose from mainstream DEs/WMs in Arch Linux
    DE_CHOICE=$(whiptail --title "Select Arch Linux Desktop Environment" --menu "Please choose which desktop environment to enable in the ISO:" 18 65 8 \
        "XFCE" "Lightweight, stable, highly customizable classic desktop" \
        "KDE_Plasma" "Modern, gorgeous, feature-rich flagship desktop" \
        "GNOME" "Minimalist, elegant desktop optimized for laptop gestures" \
        "Cinnamon" "Traditional Windows-like layout, modern and user-friendly" \
        "MATE" "Lightweight and efficient, continuing the classic GNOME 2 legacy" \
        "I3wm" "Geek preference: Tiling Window Manager (Tiling WM)" \
        "Hyprland" "Wayland-based, modern tiling window manager with top-tier effects" 3>&1 1>&2 2>&3)

    if [ -z "$DE_CHOICE" ]; then
        echo "[i] User cancelled the desktop selection."
    else
        echo "[+] Selected Desktop Environment: $DE_CHOICE"
        echo "[+] Automatically configuring core packages and distro settings for $DE_CHOICE..."

        # Initialize variables
        DE_PACKAGES=""
        DM_SERVICE=""

        # Assign corresponding Arch packages and Display Managers based on selection
        case $DE_CHOICE in
            XFCE)
                DE_PACKAGES="xfce4 xfce4-goodies lightdm lightdm-gtk-greeter"
                DM_SERVICE="lightdm.service"
                ;;
            KDE_Plasma)
                DE_PACKAGES="plasma-desktop sddm khotkeys sddm-kcm plasma-nm"
                DM_SERVICE="sddm.service"
                ;;
            GNOME)
                DE_PACKAGES="gnome gnome-extra gdm"
                DM_SERVICE="gdm.service"
                ;;
            Cinnamon)
                DE_PACKAGES="cinnamon lightdm lightdm-gtk-greeter"
                DM_SERVICE="lightdm.service"
                ;;
            MATE)
                DE_PACKAGES="mate mate-extra lightdm lightdm-gtk-greeter"
                DM_SERVICE="lightdm.service"
                ;;
            I3wm)
                DE_PACKAGES="i3-wm i3status i3lock dmenu lightdm lightdm-gtk-greeter alacritty"
                DM_SERVICE="lightdm.service"
                ;;
            Hyprland)
                DE_PACKAGES="hyprland waybar rofi-wayland kitty sddm qt6-wayland"
                DM_SERVICE="sddm.service"
                ;;
        esac

        # ---- Automatically Update packages.x86_64 ----
        if [ -f "$PACKAGES_FILE" ]; then
            echo "   -> Writing to package list: $PACKAGES_FILE"
            # Remove old desktop markers if they exist to prevent duplication
            sed -i '/# === BaoLinux DE Packages ===/,/# === End DE Packages ===/d' "$PACKAGES_FILE"
            
            # Append packages for the newly selected desktop
            echo -e "\n# === BaoLinux DE Packages ===\n# Selected: $DE_CHOICE" >> "$PACKAGES_FILE"
            for pkg in $DE_PACKAGES; do
                echo "$pkg" >> "$PACKAGES_FILE"
                echo "      + Added package: $pkg"
            done
            echo "# === End DE Packages ===" >> "$PACKAGES_FILE"
        else
            echo "[!] Warning: Cannot find $PACKAGES_FILE, skipping package injection."
        fi

        # ---- Automatically Configure the Login Manager (Display Manager) ----
        if [ ! -z "$DM_SERVICE" ]; then
            echo "   -> Setting up default login display manager ($DM_SERVICE)..."
            DM_TARGET_DIR="$AIROOTFS_DIR/etc/systemd/system"
            mkdir -p "$DM_TARGET_DIR"
            
            # Delete old display manager symbolic links
            rm -f "$DM_TARGET_DIR/display-manager.service"
            
            # Create a symbolic link to force the Archiso to boot into the corresponding login screen
            ln -sf "/usr/lib/systemd/system/$DM_SERVICE" "$DM_TARGET_DIR/display-manager.service"
            echo "      [✓] Successfully enabled $DM_SERVICE as the default display service."
        fi
        
        whiptail --title "Done" --msgbox "Core packages and boot services for [$DE_CHOICE] have been configured successfully!\n\nProceeding automatically to the configuration sync stage." 12 60
    fi
else
    echo "[i] Skipping desktop environment switch, moving directly to configuration sync."
fi

# =====================================================================
# 3. Main Synchronization: Invoke the Python Sync Utility
# =====================================================================
echo "--------------------------------------------------"
echo "[+] Triggering back-end Python script for configurations, cookies, and environment sync..."
echo "--------------------------------------------------"

if [ -f "$SYNC_SCRIPT" ]; then
    # Execute the Python script while preserving the SUDO_USER environment variable
    SUDO_USER=$SUDO_USER /usr/bin/python3 "$SYNC_SCRIPT"
else
    echo "[-] Error: Sync script '$SYNC_SCRIPT' not found in $BASE_DIR!"
    echo "    Please ensure the Python file is named correctly and located in the same directory."
    exit 1
fi

echo "=================================================="
echo "[] Success! BaoLinux desktop environment and software configuration sync completed!"
echo "=================================================="