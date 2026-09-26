#!/bin/bash

set -e

cd "$(dirname "$0")"

PYINSTALLER=".venv/bin/pyinstaller"

echo "================================"
echo "Building MacTap"
echo "================================"

echo
echo "Cleaning..."
rm -rf build dist
rm -f MacTap.spec MacTapDetector.spec

echo
echo "Building detector..."
"$PYINSTALLER" \
    --noconfirm \
    --clean \
    --onefile \
    --console \
    --name MacTapDetector \
    --collect-all macimu \
    detector.py

echo
echo "Building MacTap.app..."
"$PYINSTALLER" \
    --noconfirm \
    --clean \
    --onedir \
    --windowed \
    --name MacTap \
    --icon assets/MacTap.icns \
    --osx-bundle-identifier com.mohammadrezal.mactap \
    --collect-all rumps \
    app.py

APP="dist/MacTap.app"

echo
echo "Adding detector..."
cp dist/MacTapDetector \
    "$APP/Contents/MacOS/MacTapDetector"

chmod +x \
    "$APP/Contents/MacOS/MacTapDetector"

echo
echo "Adding resources..."
mkdir -p "$APP/Contents/Resources"

cp config.json \
    "$APP/Contents/Resources/config.json"

cp sounds/triple_tap.mp3 \
    "$APP/Contents/Resources/triple_tap.mp3"

echo
echo "Adding application icon..."
cp assets/MacTap.icns \
    "$APP/Contents/Resources/MacTap.icns"

echo
echo "Configuring Info.plist..."

python3 - <<'PY'
import plistlib
from pathlib import Path

plist_path = Path(
    "dist/MacTap.app/Contents/Info.plist"
)

with plist_path.open("rb") as f:
    plist = plistlib.load(f)

plist["LSUIElement"] = True
plist["CFBundleIconFile"] = "MacTap.icns"
plist["CFBundleIconName"] = "MacTap"
plist["CFBundleIdentifier"] = "com.mohammadrezal.mactap"
plist["CFBundleDisplayName"] = "MacTap"
plist["CFBundleName"] = "MacTap"
plist["CFBundleShortVersionString"] = "1.0"
plist["CFBundleVersion"] = "1.0.0"

with plist_path.open("wb") as f:
    plistlib.dump(plist, f)

print("✅ Icon configured")
PY

echo
echo "Installing..."
rm -rf /Applications/MacTap.app
cp -R "$APP" /Applications/MacTap.app

echo
echo "Removing quarantine..."
xattr -dr com.apple.quarantine \
    /Applications/MacTap.app \
    2>/dev/null || true

echo
echo "✅ MacTap.app built and installed."
