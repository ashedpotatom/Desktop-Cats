# Desktop Cats

Desktop Cats는 화면 위를 돌아다니는 고양이 데스크톱 펫입니다.
고양이들은 걷고, 앉고, 눕고, 세수하고, 하품하고, 잠도 잡니다.
macOS에서는 메뉴바 아이콘으로 집, 성격, 창 레이어를 조절할 수 있습니다.

## 빠른 실행

macOS에서는 아래 파일을 더블클릭하세요.

```text
Run Desktop Cats.command
```

처음 실행할 때는 자동으로 다음 작업을 합니다.

- Python 3 확인
- 필요한 Python 패키지 설치
- 프로젝트 안에 `.venv` 실행 환경 생성
- 고양이 실행
- 실행 후 터미널 창 자동 최소화

Python 3가 없으면 다운로드 페이지를 열거나, Homebrew가 설치되어 있으면
`brew install python`을 시도합니다.

## 터미널에서 실행

```bash
./Run\ Desktop\ Cats.command
```

고양이 수를 바꾸고 싶다면 숫자를 붙입니다.

```bash
./Run\ Desktop\ Cats.command 5
```

터미널 창을 숨기지 않고 문제를 확인하고 싶다면:

```bash
DESKTOP_CATS_KEEP_TERMINAL=1 ./Run\ Desktop\ Cats.command
```

## 종료 방법

macOS에서는 메뉴바의 고양이 아이콘을 클릭한 뒤 `Quit`을 누르면 종료됩니다.

PyGame 미리보기 창으로 실행되는 환경에서는 `Esc` 또는 `Q`를 눌러 종료할 수
있습니다.

## 메뉴 기능

macOS 메뉴바 고양이 아이콘을 누르면 다음 메뉴가 나옵니다.

- `House`: 고양이 집을 보여주고, 고양이들이 집으로 가서 잡니다.
- `Mode > Lazy Cat`: 70% 정도는 쉬고, 30% 정도만 움직이는 느긋한 성격입니다.
- `Mode > Active Cat`: 70% 정도는 움직이고, 30% 정도만 쉬는 활발한 성격입니다.
- `Layer > Front`: 고양이를 다른 창보다 앞으로 올립니다.
- `Layer > Back`: 고양이를 일반 앱 창 뒤쪽으로 보냅니다.
- `Quit`: 앱을 종료합니다.

## 고양이 행동

- 단일 클릭: 현재 자세에 맞는 조용한 `meow` 애니메이션을 합니다. 앉아 있으면
  `sit meow`, 서 있거나 걷는 중이면 `stand meow`, 누워 있으면 `lie meow`가
  나옵니다.
- 드래그 앤 드롭: 고양이를 잡아서 원하는 위치로 옮길 수 있습니다.
- 많이 클릭하거나 3초 이상 잡고 있으면: `hiss` 행동을 합니다.
- 오래 돌아다니면: 하품합니다.
- 쉬는 중에는: 앉거나 웅크리거나 누워 있고, 가끔 세수합니다.
- 가끔 긁기, 장난치는 공격, 뒷발로 서기 행동도 합니다.
- 집 위에 놓으면: 그 위치에서 잠듭니다.

## 화면 동작

macOS에서는 여러 개의 연결된 디스플레이를 인식합니다.
고양이는 메인 화면뿐 아니라 확장된 화면까지 돌아다닐 수 있습니다.

기본 레이어는 `Back`입니다. 그래서 일반 앱 창이 고양이를 덮을 수 있고,
고양이는 창 위를 무조건 덮고 지나가지 않습니다. 항상 앞에 보이게 하고 싶다면
메뉴에서 `Layer > Front`를 선택하세요.

## 문제가 생겼을 때

### `Run Desktop Cats.command`가 열리지 않을 때

macOS 보안 설정 때문에 처음 실행이 막힐 수 있습니다.
그럴 때는 파일을 오른쪽 클릭한 뒤 `열기`를 선택하세요.

### Python이 없다고 나올 때

아래 페이지에서 Python 3를 설치한 뒤 다시 실행하세요.

```text
https://www.python.org/downloads/macos/
```

Homebrew를 쓰고 있다면 터미널에서 아래 명령으로 설치할 수도 있습니다.

```bash
brew install python
```

### 패키지 설치가 실패할 때

인터넷 연결을 확인한 뒤 다시 실행하세요.
계속 실패하면 터미널을 숨기지 않는 모드로 실행해서 오류 메시지를 확인합니다.

```bash
DESKTOP_CATS_KEEP_TERMINAL=1 ./Run\ Desktop\ Cats.command
```

### 고양이가 안 보일 때

- 메뉴바에 고양이 아이콘이 있는지 확인하세요.
- `Layer > Front`를 눌러 고양이를 앞으로 올려보세요.
- 여러 모니터를 쓰고 있다면 다른 화면에 있는지 확인하세요.

## 개발자용 실행

직접 개발하거나 코드를 수정할 때는 아래처럼 실행할 수 있습니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

고양이 수 지정:

```bash
python main.py --cats 5
```

## App Store 준비

Mac App Store 배포 준비 문서는 `packaging/` 폴더에 있습니다.

- `packaging/APP_STORE_RELEASE_PLAN_KO.md`
- `packaging/APP_STORE_RELEASE_CHECKLIST.md`

App Store에 올리려면 Apple Developer Program 가입, Bundle ID, 인증서, 서명,
패키징 과정이 추가로 필요합니다.

## 출처 및 라이선스

이 프로젝트는 오픈소스 데스크톱 펫 프로젝트와 공개 에셋을 참고해 만들었습니다.
자세한 출처와 에셋 정보는 `ASSET_CREDITS.md`에 정리되어 있습니다.

재배포 전에는 포함된 에셋의 라이선스와 표기 조건을 확인하세요.
