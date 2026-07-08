# Mac App Store 배포 순서 체크리스트

이 문서는 현재 Desktop Cats 프로젝트를 Mac App Store에 올리기 위한 순서입니다.
지금 프로젝트는 실행 스크립트 형태로 잘 동작하지만, App Store에는 `.app` 번들과
서명된 설치 패키지로 제출해야 합니다.

## 1. 먼저 결정할 것

- 앱 이름: 예시 `Desktop Cats`
- Bundle ID: 예시 `com.yourname.desktopcats`
- 버전: 예시 `1.0.0`
- 빌드 번호: 예시 `1`
- 배포 방식: Mac App Store
- 기본 레이어 정책: `Back` 기본값 유지 권장
- 개인정보 수집 여부: 현재 구조라면 `데이터 수집 없음`으로 유지 가능

## 2. 라이선스 확인

가장 먼저 해야 합니다. 심사보다도 먼저 정리하는 게 좋습니다.

- OpenGameArt 고양이/강아지 Free pack 원본 페이지에서 라이선스 확인
- 고양이 침대 이미지 라이선스 확인
- 메뉴바 아이콘 라이선스 또는 직접 제작 여부 확인
- 라이선스가 attribution을 요구하면 앱 설명이나 크레딧에 반영
- 원본 라이선스 텍스트를 프로젝트에 보관

주의: 현재 `ASSET_CREDITS.md`에는 출처만 있고, 원본 라이선스 텍스트는 없습니다.

## 3. Apple Developer 준비

- Apple Developer Program 가입
- App Store Connect 접속 가능 여부 확인
- `Certificates, Identifiers & Profiles`에서 macOS 앱용 Bundle ID 생성
- Keychain Access에서 서명 인증서 설치 확인
- 인증서 이름 확인:

```bash
security find-identity -v -p codesigning
```

필요할 수 있는 인증서 이름 예시는 다음과 같습니다.

```text
Apple Distribution: Your Name (TEAMID)
3rd Party Mac Developer Installer: Your Name (TEAMID)
```

실제 이름은 계정마다 다릅니다.

## 4. 로컬 빌드 준비

Xcode 또는 Xcode Command Line Tools가 필요합니다.

```bash
xcodebuild -version
codesign --version
xcrun --version
productbuild --version
```

현재 프로젝트에는 App Store용 준비 파일이 있습니다.

```text
setup_app.py
packaging/build_app_store.sh
packaging/entitlements.mas.plist
packaging/requirements-build.txt
```

## 5. 앱 번들 빌드

먼저 서명 없이 `.app` 번들이 만들어지는지 확인합니다.

```bash
cd /Users/pn020/Documents/Codex/2026-07-07/munucrafts-py-desktoppet-ducky-https-github/outputs/desktop-cat-pet

BUNDLE_ID="com.yourname.desktopcats" \
APP_NAME="Desktop Cats" \
APP_VERSION="1.0.0" \
BUILD_NUMBER="1" \
zsh packaging/build_app_store.sh
```

성공하면 다음 파일이 생깁니다.

```text
dist/Desktop Cats.app
```

## 6. 로컬에서 앱 테스트

앱 번들을 직접 실행해서 확인합니다.

```bash
open "dist/Desktop Cats.app"
```

확인할 것:

- 메뉴바 아이콘이 보이는지
- `House`가 작동하는지
- `Mode > Lazy Cat / Active Cat`이 작동하는지
- `Layer > Front / Back`이 작동하는지
- 메뉴를 열어도 고양이가 멈추지 않는지
- 앱 종료가 되는지
- 새 Mac 사용자 계정에서도 실행되는지

## 7. 서명 빌드

인증서 이름을 확인한 뒤 서명해서 빌드합니다.

```bash
cd /Users/pn020/Documents/Codex/2026-07-07/munucrafts-py-desktoppet-ducky-https-github/outputs/desktop-cat-pet

APP_SIGN_IDENTITY="Apple Distribution: Your Name (TEAMID)" \
INSTALLER_SIGN_IDENTITY="3rd Party Mac Developer Installer: Your Name (TEAMID)" \
BUNDLE_ID="com.yourname.desktopcats" \
APP_NAME="Desktop Cats" \
APP_VERSION="1.0.0" \
BUILD_NUMBER="1" \
zsh packaging/build_app_store.sh
```

성공하면 다음 파일이 생깁니다.

```text
dist/Desktop Cats-1.0.0-1.pkg
```

## 8. 서명 검증

```bash
codesign --verify --deep --strict --verbose=2 "dist/Desktop Cats.app"
codesign -d --entitlements :- "dist/Desktop Cats.app"
pkgutil --check-signature "dist/Desktop Cats-1.0.0-1.pkg"
```

확인할 것:

- 앱이 서명되어 있는지
- sandbox entitlement가 들어갔는지
- `.pkg` 서명이 정상인지

## 9. App Store Connect 앱 등록

App Store Connect에서 새 앱을 만듭니다.

- 플랫폼: macOS
- 이름: `Desktop Cats`
- Bundle ID: 위에서 만든 Bundle ID
- SKU: 자유롭게 정하되 고유해야 함
- 카테고리: Entertainment 또는 Utilities 후보

## 10. 메타데이터 준비

필요한 항목:

- 앱 설명
- 키워드
- 지원 URL
- 개인정보 처리방침 URL
- 스크린샷
- 앱 아이콘
- 연령 등급
- 저작권 문구
- 심사 노트

현재 기능 기준 심사 노트에 적으면 좋은 내용:

```text
Desktop Cats is a menu bar desktop pet app. It displays small animated cats on
the desktop. Users can choose House, Mode, and Layer from the menu bar icon.
Layer > Front intentionally keeps cats above other windows, and Layer > Back
returns them underneath normal app windows. Back is the default.
The app does not collect user data and does not use network features.
```

## 11. 개인정보 라벨

현재 앱 구조 기준:

- 계정 없음
- 네트워크 사용 없음
- 분석 도구 없음
- 광고 없음
- 사용자 데이터 수집 없음

따라서 App Privacy는 보통 `Data Not Collected` 방향으로 작성합니다.
추후 analytics나 crash reporting을 붙이면 다시 작성해야 합니다.

## 12. 빌드 업로드

Transporter 앱을 쓰는 방법이 가장 쉽습니다.

- Transporter 설치
- `dist/Desktop Cats-1.0.0-1.pkg` 업로드
- App Store Connect에서 빌드 처리 완료 대기
- 해당 빌드를 앱 버전에 연결

명령어로 올릴 수도 있습니다.

```bash
xcrun altool --upload-app \
  --type macos \
  --file "dist/Desktop Cats-1.0.0-1.pkg" \
  --username "APPLE_ID" \
  --password "APP_SPECIFIC_PASSWORD"
```

Apple 계정 설정에 따라 Transporter 사용을 권장합니다.

## 13. 제출 전 최종 QA

- 새로 부팅한 뒤 실행
- 여러 모니터에서 실행
- `Front`와 `Back` 전환
- 활성 창 뒤/앞 동작 확인
- 고양이 드래그 앤 드롭
- 집에 드롭하면 놓은 위치에서 잠드는지 확인
- 메뉴 열어도 고양이가 멈추지 않는지 확인
- 앱 종료 확인
- 인터넷이 없어도 실행되는지 확인
- `.venv`, `__pycache__`, 개발용 임시 파일이 앱 번들에 없는지 확인

## 14. 제출 후

- App Review 메시지 확인
- 거절되면 원인별로 수정
- 특히 `Layer > Front` 기능은 심사자가 오해할 수 있으므로, 필요하면 심사 노트에서 더 자세히 설명

## 추천 진행 순서 요약

1. 에셋 라이선스 확인
2. Apple Developer 계정과 Bundle ID 준비
3. 서명 없이 `.app` 빌드
4. 로컬 실행 테스트
5. 인증서로 앱과 패키지 서명
6. 서명 검증
7. App Store Connect 앱 등록
8. 스크린샷/설명/개인정보 라벨 작성
9. Transporter로 `.pkg` 업로드
10. TestFlight 또는 내부 테스트
11. App Review 제출
