#!/bin/zsh
set -euo pipefail

ROOT_DIR="${0:A:h}/.."
cd "$ROOT_DIR"

APP_NAME="${APP_NAME:-Desktop Cat}"
BUNDLE_ID="${BUNDLE_ID:-com.example.desktopcat}"
APP_VERSION="${APP_VERSION:-1.0.0}"
BUILD_NUMBER="${BUILD_NUMBER:-1}"
APP_PATH="dist/${APP_NAME}.app"
PKG_PATH="dist/${APP_NAME}-${APP_VERSION}-${BUILD_NUMBER}.pkg"
ENTITLEMENTS="packaging/entitlements.mas.plist"

echo "Building ${APP_NAME} (${BUNDLE_ID}) ${APP_VERSION} build ${BUILD_NUMBER}"
python3 -m pip install -r packaging/requirements-build.txt

rm -rf build dist
BUNDLE_ID="$BUNDLE_ID" \
APP_NAME="$APP_NAME" \
APP_VERSION="$APP_VERSION" \
BUILD_NUMBER="$BUILD_NUMBER" \
python3 setup_app.py py2app

if [[ -n "${APP_SIGN_IDENTITY:-}" ]]; then
  echo "Signing app with ${APP_SIGN_IDENTITY}"
  codesign --force --deep --timestamp \
    --entitlements "$ENTITLEMENTS" \
    --sign "$APP_SIGN_IDENTITY" \
    "$APP_PATH"
else
  echo "APP_SIGN_IDENTITY is not set, so the app bundle was not signed."
fi

if [[ -n "${INSTALLER_SIGN_IDENTITY:-}" ]]; then
  echo "Building signed installer package"
  productbuild --component "$APP_PATH" /Applications \
    --sign "$INSTALLER_SIGN_IDENTITY" \
    "$PKG_PATH"
  echo "Created $PKG_PATH"
else
  echo "INSTALLER_SIGN_IDENTITY is not set, so no .pkg was created."
fi

echo "Created $APP_PATH"
