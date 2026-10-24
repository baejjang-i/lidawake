#!/bin/sh
# 맥에서 실행: sh build.sh  (Xcode Command Line Tools 필요: xcode-select --install)
# DMG까지 만들려면: sh build.sh dmg
set -e
cd "$(dirname "$0")"
APP=LidAwake.app
rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"
cp Info.plist "$APP/Contents/"
iconutil -c icns icon/AppIcon.iconset -o "$APP/Contents/Resources/AppIcon.icns"
cp icon/Lid*Template*.png "$APP/Contents/Resources/"
# Apple Silicon + Intel 겸용(universal) 바이너리
swiftc -Osize -Xlinker -dead_strip -target arm64-apple-macos11 main.swift -o /tmp/lidawake-arm64
swiftc -Osize -Xlinker -dead_strip -target x86_64-apple-macos11 main.swift -o /tmp/lidawake-x86_64
lipo -create /tmp/lidawake-arm64 /tmp/lidawake-x86_64 -output "$APP/Contents/MacOS/LidAwake"
strip -x "$APP/Contents/MacOS/LidAwake"
codesign --force --sign - "$APP"

if [ "$1" = "dmg" ]; then
  STAGE=$(mktemp -d)
  cp -R "$APP" "$STAGE/"
  ln -s /Applications "$STAGE/Applications"
  hdiutil create -volname LidAwake -srcfolder "$STAGE" -ov -format UDZO LidAwake.dmg
  echo "완료: LidAwake.dmg"
else
  echo "완료: open $APP  (또는 /Applications 로 옮긴 뒤 실행)"
fi
