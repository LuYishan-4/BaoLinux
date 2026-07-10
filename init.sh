#!/bin/sh
set -eu

TARGET_DIR="archos"
ARCHISO_TEMPLATE_SRC="/usr/share/archiso/configs/releng"

if [ ! -d "$ARCHISO_TEMPLATE_SRC" ]; then
    echo "[-] Error: Official template directory not found: $ARCHISO_TEMPLATE_SRC"
    echo "[+] Attempting to install archiso..."
    if sudo pacman -S --noconfirm archiso; then
        echo "[✓] archiso installed successfully"
    else
        echo "[-] Error: Installation failed. Please run 'sudo pacman -S archiso' manually."
        exit 1
    fi
fi

echo "[+] Preparing the archos workspace..."
mkdir -p "$TARGET_DIR"

echo "[+] Copying archiso template contents into $TARGET_DIR..."
if cp -a "$ARCHISO_TEMPLATE_SRC"/. "$TARGET_DIR"/; then
    echo "[✓] Template copied into $TARGET_DIR"
else
    echo "[-] Error: Failed to copy archiso template into $TARGET_DIR"
    exit 1
fi

echo ""
echo "=================================================="
echo "[] archos is ready for sync and setup work"
echo "[] Workspace path: $(pwd)/$TARGET_DIR"
echo "--------------------------------------------------"
ls -F "$TARGET_DIR"
echo "=================================================="
echo "[*] All subsequent sync and setup steps will use $TARGET_DIR"