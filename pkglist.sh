#!/bin/bash
SCRIPT_DIR=$(cd "$(dirname "$0")"; pwd)
TARGET_DIR="$SCRIPT_DIR/archos/airootfs/usr/share"


pacman -Qqme > "$TARGET_DIR/pkglist.txt"

echo "Done: $TARGET_DIR/pkglist.txt"
