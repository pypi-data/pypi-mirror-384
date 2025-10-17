# KITECH Manufacturing Data Repository CLI

KITECH 제조 데이터 리포지토리를 위한 Python CLI 도구 및 라이브러리입니다.

## 기능

- 🖥️ **대화형 파일 관리자 (TUI)** - Textual 프레임워크 기반 현대적인 TUI
  - 리포지토리 선택 화면 (페이지네이션 지원)
  - 듀얼 패널 파일 관리자 (로컬 ↔ 원격)
  - 향상된 포커스 관리 (시각적 표시기)
  - 실시간 진행률 추적 (업로드/다운로드)
  - 배치 작업 지원 (여러 파일 동시 처리)
- 🔐 API Token 기반 인증 (시스템 키링에 안전 저장)
- ⬇️ 파일/폴더 다운로드 (SHA-256 무결성 검증)
- ⬆️ 파일/폴더 업로드 (MD5 무결성 검증)
- 📊 실시간 진행률 표시 (배치 작업 지원)
- 🐍 Python Library API (프로그래밍 방식 사용 가능)

## 요구 사항

- Python 3.10 ~ 3.13
- pip 또는 pipx

## 설치

### 권장 방법: pipx (CLI 도구용)

```bash
# pipx 설치 (한 번만)
brew install pipx
pipx ensurepath

# kitech-repository 설치
pipx install kitech-repository
```

### 대안: pip (라이브러리로 사용 시)

```bash
# 가상환경에서 설치
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install kitech-repository

# 또는 사용자 설치 (--user)
pip install --user kitech-repository
```

## 사용법

### 1. 초기 설정 (간단 버전)

단 한 번의 명령으로 서버 설정 + 로그인을 완료할 수 있습니다:

```bash
# 대화형으로 설정 (서버 URL과 Token을 순서대로 입력)
kitech login

# 또는 직접 지정
kitech login https://your-server.com
```

이 명령은 서버 주소를 설정하고 API Token 로그인까지 한 번에 처리합니다.

### 2. 파일 관리자 시작

```bash
kitech start
```

실행하면 리포지토리 선택 화면이 먼저 나타납니다:

**1단계: \
리포지토리 선택 화면**
- 모든 접근 가능한 리포지토리 목록 표시 (페이지네이션 지원)
- `↑/↓` 키로 리포지토리 선택
- `Enter` 키를 눌러 해당 리포지토리의 파일 관리자로 진입

**2단계: 듀얼 패널 파일 관리자**
- **왼쪽 패널 (원격)**: 선택한 리포지토리의 파일
- **오른쪽 패널 (로컬)**: 로컬 파일 시스템
- **하단 패널**: 파일 전송 진행률 표시

### 기본 사용 흐름

1. **파일 탐색**
   - `↑/↓` 키로 파일/폴더 선택
   - `Enter` 키로 폴더 열기 또는 파일 다운로드
   - `..` 항목을 선택하고 `Enter`를 눌러 상위 디렉토리로 이동
   - `Tab` 키로 왼쪽/오른쪽 패널 전환

2. **다운로드** (원격 → 로컬)
   - 왼쪽 패널(원격)에서 다운로드할 파일/폴더 선택
   - `Enter` 키 또는 `F2` 키로 선택한 파일 다운로드
   - `F1` 키로 현재 디렉토리의 모든 파일 다운로드
   - `~/Downloads` 폴더에 다운로드됨
   - 실시간 진행률이 하단에 표시됨

3. **업로드** (로컬 → 원격)
   - 오른쪽 패널(로컬)에서 업로드할 파일/폴더 선택
   - `F4` 키로 선택한 파일 업로드
   - `F3` 키로 현재 디렉토리의 모든 파일 업로드
   - 왼쪽 패널의 현재 경로에 업로드됨
   - 실시간 진행률이 하단에 표시됨

4. **종료**
   - `Ctrl+C` 또는 `Ctrl+Q` 키로 프로그램 종료
   - 터미널에서 `kitech logout`으로 로그아웃

### 키보드 단축키

#### 전역 단축키

| 키 | 기능 |
|---|---|
| `Tab` | 왼쪽/오른쪽 패널 전환 |
| `Ctrl+C` / `Ctrl+Q` | 프로그램 종료 |

#### 원격 패널 (왼쪽)

| 키 | 기능 |
|---|---|
| `↑/↓` | 파일/폴더 선택 |
| `Enter` | 폴더 열기 또는 파일 다운로드 |
| `F1` | 현재 디렉토리의 모든 파일 다운로드 |
| `F2` | 선택한 파일 다운로드 |
| `F5` | 파일 목록 새로고침 |
| `Backspace` | 상위 디렉토리로 이동 |

#### 로컬 패널 (오른쪽)

| 키 | 기능 |
|---|---|
| `↑/↓` | 파일/폴더 선택 |
| `Enter` | 폴더 열기 |
| `F3` | 현재 디렉토리의 모든 파일 업로드 |
| `F4` | 선택한 파일 업로드 |
| `F5` | 파일 목록 새로고침 |
| `Backspace` | 상위 디렉토리로 이동 |

## 명령어 참조

### 주요 명령어

```bash
# 로그인 (서버 설정 + 인증 한번에)
kitech login [SERVER_URL]

# 파일 관리자 시작
kitech start [REPO_ID]

# 연결 상태 확인
kitech status

# 로그아웃
kitech logout

# 버전 확인
kitech version
```

### 고급 명령어

```bash
# 서버 URL 변경
kitech server [NEW_URL]

# 현재 설정 확인
kitech config

# 설정 초기화
kitech config reset
```

### 저장 위치

- **설정 파일**: `~/.kitech/config.json` - 서버 URL, 청크 크기
- **인증 메타데이터**: `~/.kitech/auth_metadata.json` - 사용자 정보, 만료일
- **API 키**: 시스템 키링에 안전하게 암호화되어 저장 (macOS Keychain, Windows Credential Manager 등)

### 환경 변수 (선택사항)

명령어 대신 환경 변수로도 설정할 수 있습니다:

```bash
# 환경 변수로 설정
export KITECH_API_BASE_URL=https://your-api-server.com

# 또는 .env 파일에 작성
echo "KITECH_API_BASE_URL=https://your-api-server.com" > .env
```

**주의**: 베이스 URL만 입력하세요. API 버전(`/v1`)은 클라이언트가 런타임에 자동으로 추가합니다.

---

## 개발자를 위한 Library API

Python 프로그램에서 직접 사용할 수 있습니다:

### 기본 사용법

```python
from kitech_repository import KitechClient

# 기본 사용 (v1 API)
client = KitechClient(token="kt_xxx")

# 리포지토리 목록
repos = client.list_repositories()
for repo in repos:
    print(f"{repo.id}: {repo.name}")

# 파일 목록
files = client.list_files(repository_id=123)

# 파일 다운로드
client.download_file(
    repository_id=123,
    path="/data/file.csv",
    output_dir="./downloads"
)

# 파일 업로드
client.upload_file(
    repository_id=123,
    file_path="local.csv",
    remote_path="/data/uploaded.csv"
)

# Context manager 사용 (권장)
with KitechClient(token="kt_xxx") as client:
    repos = client.list_repositories()
```

### 배치 작업

```python
# 여러 파일 동시 다운로드 (비동기)
import asyncio
from kitech_repository import KitechClient

async def download_multiple():
    async with KitechClient(token="kt_xxx") as client:
        result = await client.download_batch(
            repository_id=123,
            paths=["/data/file1.csv", "/data/file2.csv"],
            output_dir="./downloads"
        )
        print(f"Success: {len(result.successful)}")
        print(f"Failed: {len(result.failed)}")

asyncio.run(download_multiple())
```

### 편의 함수

```python
from kitech_repository import download, upload, list_repositories

# 간단한 다운로드
download(repository_id=123, path="/data/file.csv")

# 간단한 업로드
upload(repository_id=123, file_path="local.csv", remote_path="/data/")

# 리포지토리 목록
repos = list_repositories(app_key="kt_xxx")
```

### API 버전 관리

```python
# 다른 API 버전 사용
client_v2 = KitechClient(token="kt_xxx", api_version="v2")

# API 버전 없이 사용
client_no_version = KitechClient(token="kt_xxx", api_version="")

# 기본값은 "v1"
client_default = KitechClient(token="kt_xxx")  # api_version="v1"
```

**중요**:
- Config 파일에는 베이스 URL만 저장되며, API 버전은 클라이언트 생성 시 지정합니다
- 이를 통해 동일한 애플리케이션에서 여러 API 버전을 동시에 사용할 수 있습니다

### 인증 관리

```python
from kitech_repository import AuthManager

# 인증 관리자 사용
auth = AuthManager()

# 로그인 정보 저장
auth.login(
    app_key="kt_xxx",
    user_id="user@example.com",
    expires_at="2026-01-01T00:00:00"
)

# 인증 확인
if auth.is_authenticated():
    print(f"Logged in as: {auth.get_metadata()['user_id']}")

# API 헤더 가져오기
headers = auth.headers  # {"X-App-Key": "kt_xxx"}

# 로그아웃
auth.logout()
```

### 설정 관리

```python
from kitech_repository import Config

# 설정 로드
config = Config.load()
print(f"API URL: {config.api_base_url}")
print(f"Chunk Size: {config.chunk_size}")

# 설정 변경 및 저장
config.api_base_url = "https://new-server.com"
config.save()

# 환경 변수로 설정
# KITECH_API_BASE_URL=https://server.com python script.py
```

## 개발

### 개발 환경 설정

```bash
# 저장소 클론
git clone https://github.com/WIM-Corporation/kitech-repository-CLI.git
cd kitech-repository-CLI

# uv로 설치 (권장)
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"

# 또는 pip로 설치
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 코드 품질

```bash
# 포맷팅
ruff format .

# 린트
ruff check .

# 자동 수정
ruff check . --fix
```

### 테스트

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함
pytest --cov

# 특정 테스트 파일
pytest tests/unit/test_auth.py

# 특정 테스트 함수
pytest tests/unit/test_auth.py::test_function_name
```

### TUI 개발

```bash
# 개발 모드로 TUI 실행 (라이브 리로드)
textual run --dev kitech_repository.tui.app:KitechTUI

# Textual 콘솔로 디버깅 (별도 터미널에서)
textual console

# Textual 내장 도구
textual borders  # 테두리 스타일 미리보기
textual colors   # 색상 팔레트 미리보기
textual keys     # 키 바인딩 참조
```

## 아키텍처

### 프로젝트 구조

```
kitech_repository/
├── cli/              # CLI 명령어 구현 (Typer)
│   ├── main.py      # 진입점
│   └── commands/    # 개별 명령어 모듈
├── core/            # 핵심 기능
│   ├── client.py    # HTTP 클라이언트
│   ├── auth.py      # 인증 관리
│   ├── config.py    # 설정 관리
│   └── exceptions.py # 예외 계층
├── models/          # 데이터 모델 (Pydantic)
│   ├── repository.py
│   ├── file.py
│   └── batch.py
├── tui/             # TUI 애플리케이션 (Textual)
│   ├── app.py       # 메인 앱
│   ├── screens/     # 화면 컴포넌트
│   ├── widgets/     # 위젯 컴포넌트
│   └── messages.py  # 커스텀 메시지
└── __init__.py      # 공개 API
```

### 핵심 설계 원칙

1. **이중 인터페이스 아키텍처**
   - CLI: 사용자 친화적인 명령어 인터페이스
   - Library: 프로그래밍 방식의 Python API

2. **보안**
   - 시스템 키링을 통한 안전한 자격증명 저장
   - 민감하지 않은 메타데이터만 파일에 저장
   - Presigned URL을 통한 직접 S3 액세스

3. **성능**
   - 비동기 배치 작업 (5-10개 동시 처리)
   - 청크 스트리밍 (기본 8KB)
   - 병렬 다운로드/업로드

4. **사용성**
   - 직관적인 TUI (Textual)
   - 명확한 진행률 표시
   - 도움말 메시지 및 오류 안내

## 라이센스

MIT License

## 기여

이슈 및 풀 리퀘스트를 환영합니다!

## 링크

- **PyPI**: https://pypi.org/project/kitech-repository/
- **GitHub**: https://github.com/WIM-Corporation/kitech-repository-CLI
- **Issues**: https://github.com/WIM-Corporation/kitech-repository-CLI/issues
