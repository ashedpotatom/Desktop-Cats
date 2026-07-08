# Mac App Store Release Checklist

This project currently runs as a Python desktop pet. For Mac App Store release,
ship it as a signed and sandboxed `.app` bundle rather than a script that
creates a virtual environment at launch.

## Required Account Setup

- Join the Apple Developer Program.
- Create an App Store Connect app record for macOS.
- Choose a final bundle ID, for example `com.yourcompany.desktopcat`.
- Create or download the signing certificates required by your account.

## Local Build

Install build tooling and create the app bundle:

```bash
cd work/source
BUNDLE_ID="com.yourcompany.desktopcat" \
APP_NAME="Desktop Cat" \
APP_VERSION="1.0.0" \
BUILD_NUMBER="1" \
zsh packaging/build_app_store.sh
```

To create a signed package, provide signing identities:

```bash
APP_SIGN_IDENTITY="Apple Distribution: Your Name (TEAMID)" \
INSTALLER_SIGN_IDENTITY="3rd Party Mac Developer Installer: Your Name (TEAMID)" \
BUNDLE_ID="com.yourcompany.desktopcat" \
zsh packaging/build_app_store.sh
```

Certificate names vary by Apple account setup. Check Keychain Access and use
the exact signing identity names installed on your Mac.

## App Store Review Risks

- `Layer > Front` pins cats above other windows. Keep `Back` as the default and
  explain this feature in App Review notes so reviewers understand it is
  user-controlled.
- The app is sandboxed and does not need network, camera, microphone, contacts,
  or file-access entitlements.
- The current runtime creates temporary sprite frames. This should remain inside
  the app sandbox container or system temporary directory.
- Do not submit a build that installs packages at launch. Dependencies must be
  bundled inside the `.app`.

## Assets And Legal

- Confirm the license for the OpenGameArt cat/dog pack and keep a copy of the
  license text in the app record or project.
- Confirm the license/ownership for the cat bed and menu bar icon.
- Include accurate credits if the license requires attribution.

## App Store Connect Metadata

- App name and subtitle.
- Description and keywords.
- Support URL.
- Privacy policy URL, even if the app collects no data.
- Screenshots for macOS.
- Age rating.
- Privacy nutrition label. This app should be “data not collected” if no
  telemetry, accounts, network calls, or analytics are added.
- Review notes explaining the menu bar app, desktop pet behavior, House, Mode,
  and Layer controls.

## Upload

After building a signed `.pkg`, upload it with Transporter or App Store Connect
tools, then attach the processed build to the macOS app version and submit for
review.
