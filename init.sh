#!/bin/sh
set -eu

TARGET_DIR="archos"
ARCHISO_TEMPLATE_SRC="/usr/share/archiso/configs/releng"


###############################################################################
# Install archiso
###############################################################################

if [ ! -d "$ARCHISO_TEMPLATE_SRC" ]; then

    echo "[-] Official archiso template not found."
    echo "[+] Installing archiso..."

    if sudo pacman -Sy --noconfirm archiso; then
        echo "[✓] archiso installed."
    else
        echo "[-] Failed to install archiso."
        exit 1
    fi

fi



###############################################################################
# Prepare workspace
###############################################################################

echo "[+] Preparing workspace..."

mkdir -p "$TARGET_DIR"


echo "[+] Copying releng template..."

cp -a \
    "$ARCHISO_TEMPLATE_SRC"/. \
    "$TARGET_DIR"/



###############################################################################
# Create Wayland directories
###############################################################################

echo "[+] Creating Wayland directories..."

mkdir -p \
"$TARGET_DIR/airootfs/usr/share/archos-wayland/configs"

mkdir -p \
"$TARGET_DIR/airootfs/etc/systemd/user"

mkdir -p \
"$TARGET_DIR/airootfs/etc/systemd/user/graphical-session.target.wants"



###############################################################################
# Create import script
###############################################################################

echo "[+] Creating import-wayland.sh"



cat > \
"$TARGET_DIR/airootfs/usr/share/archos-wayland/import-wayland.sh" <<'EOF'
#!/bin/bash

set -e


FLAG="$HOME/.config/.archos_wayland_imported"


if [ -f "$FLAG" ]; then
    exit 0
fi



SRC="/usr/share/archos-wayland/configs"



if [ ! -d "$SRC" ]; then
    exit 0
fi



mkdir -p "$HOME/.config"
mkdir -p "$HOME/.local/share"



###############################################################################
# Detect desktop
###############################################################################

SESSION=""



case "${XDG_CURRENT_DESKTOP:-}" in


    *Hyprland*|*HYPRLAND*)

        SESSION="hyprland"
        ;;


    *KDE*|*Plasma*|*kde*)

        SESSION="plasma"
        ;;


esac



# fallback

if [ -z "$SESSION" ]; then

    if [ -d "$SRC/hyprland" ]; then
        SESSION="hyprland"

    elif [ -d "$SRC/plasma" ]; then
        SESSION="plasma"

    fi

fi



if [ -z "$SESSION" ]; then
    echo "[archos] Unknown desktop"
    exit 0
fi



CONFIG="$SRC/$SESSION"



if [ ! -d "$CONFIG" ]; then
    exit 0
fi



echo "[archos] Importing $SESSION configuration..."



cp -a \
"$CONFIG"/. \
"$HOME"/



touch "$FLAG"



echo "[archos] $SESSION configuration imported."

EOF



chmod +x \
"$TARGET_DIR/airootfs/usr/share/archos-wayland/import-wayland.sh"




###############################################################################
# Create systemd user service
###############################################################################

echo "[+] Creating systemd service..."

cat > \
"$TARGET_DIR/airootfs/etc/systemd/user/import-wayland.service" <<'EOF'

[Unit]
Description=Import Archos Wayland configuration
After=graphical-session.target


[Service]
Type=oneshot
ExecStart=/usr/share/archos-wayland/import-wayland.sh


[Install]
WantedBy=graphical-session.target

EOF




###############################################################################
# Enable service
###############################################################################

ln -sf \
../import-wayland.service \
"$TARGET_DIR/airootfs/etc/systemd/user/graphical-session.target.wants/import-wayland.service"



###############################################################################
# Finished
###############################################################################

echo ""
echo "=================================================="
echo "[✓] archos workspace created"
echo "[✓] Wayland auto import installed"
echo ""
echo "Workspace:"
echo "  $(pwd)/$TARGET_DIR"
echo ""
echo "Next:"
echo "  sudo python3 getSystemConfig/syncDesktop.py"
echo "  sudo mkarchiso -v archos"
echo "=================================================="

