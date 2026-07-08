#!/bin/zsh
set -u

APP_NAME="Desktop Cats"
SCRIPT_DIR="${0:A:h}"
APP_DIR="$SCRIPT_DIR"
CAT_COUNT="${1:-${DESKTOP_CAT_COUNT:-3}}"
VENV_DIR="$APP_DIR/.venv"

pause_before_exit() {
  echo
  echo "창을 닫으려면 아무 키나 누르세요."
  read -k 1 -s
}

fail() {
  echo
  echo "실행할 수 없습니다: $1"
  echo
  echo "도움말:"
  echo "- macOS라면 Python 3 설치가 필요할 수 있습니다."
  echo "- Python 다운로드: https://www.python.org/downloads/macos/"
  echo "- Homebrew가 있다면 터미널에서 brew install python 도 가능합니다."
  pause_before_exit
  exit 1
}

find_python3() {
  if command -v python3 >/dev/null 2>&1; then
    command -v python3
    return 0
  fi

  if [[ -x "/usr/bin/python3" ]]; then
    echo "/usr/bin/python3"
    return 0
  fi

  return 1
}

install_python_if_possible() {
  if command -v brew >/dev/null 2>&1; then
    echo "Python 3가 없어 Homebrew로 설치를 시도합니다."
    brew install python || return 1
    rehash
    return 0
  fi

  echo "Python 3가 설치되어 있지 않습니다."
  echo "Python 다운로드 페이지를 열겠습니다."
  open "https://www.python.org/downloads/macos/" >/dev/null 2>&1 || true
  return 1
}

check_python_version() {
  "$1" - <<'PY'
import sys
raise SystemExit(0 if sys.version_info >= (3, 9) else 1)
PY
}

check_required_modules() {
  python - <<'PY'
import platform
import pygame

if platform.system() == "Darwin":
    import AppKit
    import Quartz
PY
}

cd "$APP_DIR" || fail "앱 폴더로 이동할 수 없습니다."

if [[ ! -f "main.py" || ! -f "requirements.txt" ]]; then
  fail "main.py 또는 requirements.txt를 찾을 수 없습니다. 압축을 풀어 전체 폴더 안에서 실행해 주세요."
fi

PYTHON_BIN="$(find_python3 || true)"
if [[ -z "$PYTHON_BIN" ]]; then
  install_python_if_possible || fail "Python 3 설치가 필요합니다."
  PYTHON_BIN="$(find_python3 || true)"
fi

if [[ -z "$PYTHON_BIN" ]]; then
  fail "Python 3를 찾을 수 없습니다."
fi

if ! check_python_version "$PYTHON_BIN"; then
  fail "Python 3.9 이상이 필요합니다. 현재 Python을 업데이트해 주세요."
fi

echo "$APP_NAME 실행 준비 중입니다."
echo "사용할 Python: $PYTHON_BIN"

if [[ -d "$VENV_DIR" ]]; then
  if ! "$VENV_DIR/bin/python" - <<'PY' >/dev/null 2>&1
import sys
raise SystemExit(0 if sys.version_info >= (3, 9) else 1)
PY
  then
    mv "$VENV_DIR" "$VENV_DIR.old.$(date +%Y%m%d%H%M%S)"
  fi
fi

if [[ ! -d "$VENV_DIR" ]]; then
  echo "처음 실행 준비를 합니다. 시간이 조금 걸릴 수 있습니다."
  "$PYTHON_BIN" -m venv --system-site-packages "$VENV_DIR" || fail "가상환경을 만들 수 없습니다."
fi

source "$VENV_DIR/bin/activate"

if ! check_required_modules >/dev/null 2>&1; then
  echo "필요한 프로그램 구성요소를 설치합니다."
  python -m pip install --upgrade pip setuptools wheel || fail "pip 업데이트에 실패했습니다."
  python -m pip install -r requirements.txt || fail "필요한 Python 패키지 설치에 실패했습니다."
fi

if ! check_required_modules >/dev/null 2>&1; then
  fail "필수 패키지를 불러올 수 없습니다. 인터넷 연결과 Python 설치 상태를 확인해 주세요."
fi

echo "고양이 ${CAT_COUNT}마리를 실행합니다."
echo "종료하려면 메뉴바 고양이 아이콘에서 Quit을 누르거나 이 터미널 창을 닫으세요."
python main.py --cats "$CAT_COUNT"
