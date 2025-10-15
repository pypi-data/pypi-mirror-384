# Release Process

이 문서는 Playfast의 릴리스 프로세스를 설명합니다.

## 사전 준비 (한 번만 설정)

### 1. PyPI 계정 설정

1. **PyPI 계정 생성**: <https://pypi.org/account/register/>
1. **Test PyPI 계정 생성** (선택사항): <https://test.pypi.org/account/register/>

### 2. PyPI API Token 생성

1. PyPI 로그인
1. Account Settings → API tokens → **Add API token**
1. Token name: `playfast-github-actions`
1. Scope: **"Entire account"** (또는 프로젝트가 이미 있다면 "playfast" 선택)
1. 생성된 토큰 복사 (한 번만 보임!): `pypi-AgEIcHlwaS5vcmc...`

### 3. GitHub Secrets 설정

1. GitHub 저장소로 이동
1. **Settings** → **Secrets and variables** → **Actions**
1. **New repository secret** 클릭
1. 다음 시크릿 추가:

| Name                  | Value         | 설명                      |
| --------------------- | ------------- | ------------------------- |
| `PYPI_API_TOKEN`      | `pypi-AgE...` | PyPI 업로드용 토큰        |
| `TEST_PYPI_API_TOKEN` | `pypi-AgE...` | Test PyPI 토큰 (선택사항) |

### 4. PyPI Trusted Publishing 설정 (추천, 토큰 없이 배포)

PyPI Trusted Publishing을 사용하면 API 토큰 없이도 GitHub Actions에서 안전하게 배포할 수 있습니다.

1. PyPI 로그인
1. Account Settings → **Publishing** → **Add a new pending publisher**
1. 다음 정보 입력:
   - **PyPI Project Name**: `playfast`
   - **Owner**: `mixL1nk` (GitHub username)
   - **Repository name**: `playfast`
   - **Workflow name**: `release.yml`
   - **Environment name**: `pypi`

설정 완료 후 `.github/workflows/release.yml`에서 `password:` 라인을 제거하면 됩니다.

## 릴리스 프로세스

### 자동 릴리스 (semantic-release 사용)

Conventional Commits를 사용하면 자동으로 버전이 증가하고 릴리스됩니다:

```bash
# 1. 커밋 (conventional commits 형식)
git commit -m "feat: add new feature"
git commit -m "fix: fix bug"

# 2. 자동 릴리스 (버전 증가 + 태그 생성 + 푸시)
poe release

# 3. GitHub Actions가 자동으로:
#    - 모든 플랫폼용 wheel 빌드
#    - PyPI에 업로드
#    - GitHub Release 생성
```

### 수동 릴리스

```bash
# 1. 버전 업데이트
# pyproject.toml의 version을 수정: 0.1.0 → 0.2.0

# 2. CHANGELOG 생성
poe changelog

# 3. 커밋
git add pyproject.toml CHANGELOG.md
git commit -m "chore(release): 0.2.0"

# 4. 태그 생성 및 푸시
git tag v0.2.0
git push origin main --tags

# 5. GitHub Actions가 자동 실행됨
```

## 빌드되는 플랫폼

GitHub Actions는 다음 플랫폼용 wheel을 빌드합니다:

| Platform    | Architecture    | Wheel Name                           |
| ----------- | --------------- | ------------------------------------ |
| **Linux**   | x86_64          | `playfast-*-manylinux_*_x86_64.whl`  |
| **Linux**   | aarch64 (ARM)   | `playfast-*-manylinux_*_aarch64.whl` |
| **macOS**   | x86_64 (Intel)  | `playfast-*-macosx_*_x86_64.whl`     |
| **macOS**   | aarch64 (M1/M2) | `playfast-*-macosx_*_arm64.whl`      |
| **Windows** | x86_64          | `playfast-*-win_amd64.whl`           |

추가로 **source distribution** (sdist)도 빌드됩니다: `playfast-*.tar.gz`

## 로컬 빌드 테스트

릴리스 전에 로컬에서 빌드를 테스트할 수 있습니다:

```bash
# 현재 플랫폼용 wheel 빌드
uv run maturin build --release

# 특정 플랫폼용 빌드 (크로스 컴파일)
uv run maturin build --release --target x86_64-unknown-linux-gnu

# sdist 빌드
uv run maturin sdist

# 빌드된 파일 확인
ls -lh target/wheels/
```

## 문제 해결

### PyPI 업로드 실패

**에러**: `403 Forbidden: The credential associated with user '...' isn't allowed to upload to project 'playfast'`

**해결**:

1. PyPI에서 프로젝트 이름이 사용 가능한지 확인
1. API 토큰의 Scope가 올바른지 확인
1. Trusted Publishing 설정이 올바른지 확인

### Wheel 빌드 실패

**에러**: `error: failed to compile`

**해결**:

1. 로컬에서 `uv run maturin build --release` 테스트
1. Rust 코드에 컴파일 에러가 없는지 확인
1. `Cargo.toml` 및 `pyproject.toml` 설정 확인

### GitHub Actions 권한 에러

**에러**: `Resource not accessible by integration`

**해결**:

1. Settings → Actions → General → Workflow permissions
1. **"Read and write permissions"** 선택
1. **"Allow GitHub Actions to create and approve pull requests"** 체크

## 참고 자료

- [Maturin Documentation](https://www.maturin.rs/)
- [GitHub Actions - Maturin Action](https://github.com/PyO3/maturin-action)
- [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
