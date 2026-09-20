#!/bin/bash

set -e

cd "$(dirname "$0")"

echo "Cleaning old build..."
rm -rf build dist MacTap.spec

echo "Building MacTap.app..."
.venv/bin/pyinstaller \
    --noconfirm \
    --clean \
    --windowed \
    --onedir \
    --name MacTap \
    --osx-bundle-identifier com.mohammadrezal.mactap \
    app.py

echo "Setting menu-bar mode..."
python3 - <<'PY'
import plistlib
from pathlib import Path

plist = Path("dist/MacTap.app/Contents/Info.plist")

with plist.open("rb") as f:
    data = plistlib.load(f)

data["LSUIElement"] = True

with plist.open("wb") as f:
    plistlib.dump(data, f)

print("LSUIElement = True")
PY

echo "Installing to /Applications..."
rm -rf /Applications/MacTap.app
cp -R dist/MacTap.app /Applications/MacTap.app

xattr -dr com.apple.quarantine /Applications/MacTap.app 2>/dev/null || true

echo
echo "✅ MacTap.app successfully built and installed."
chmod +x build_app.sh
