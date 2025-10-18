# dodoenv

Env 설정을 도와주는 라이브러리입니다.

[![Python Version](https://img.shields.io/pypi/pyversions/dodoenv.svg)](https://pypi.org/project/dodoenv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 설치

```bash
pip install dodoenv
```

## 소개

다음과 같은 목적으로 제작되었습니다.

1. 오타방지

   ```python
   EXAMPLE_VALUE = os.environ.get("EXAMPLE_VALEU") # 오탈자 발생
   ```
2. Type 힌트

   ```python
   EXAMPLE_VALUE = os.environ.get("EXAMPLE_VALUE") # 없을 시 None
   assert EXAMPLE_VALUE # assert하지 않으면 Pylance가 조용히 하지 않음
   ```
3. Type 변환

   ```python
   EXAMPLE_VALUE = int(os.environ.get("EXAMPLE_VALUE", 0)) # 안멋짐
   ```

## 사용법

```python
from dodoenv import Env, load_dotenv

load_dotenv(".env")  # .env 파일에서 환경변수 로드

class Config:
    EXAMPLE_VALUE = Env[str]()
    EXAMPLE_INT_VALUE = Env[int](func=int)
    EXAMPLE_DEFAULT_VALUE = Env[str](default="default_value")
```

## 개발 환경 설정

```bash
# 저장소 클론
git clone https://github.com/byundojin/dodoenv.git
cd dodoenv

# 개발 의존성 설치
pip install -e ".[dev]"

# 테스트 실행
python -m tests.run
```

## 빌드 및 배포

```bash
# 빌드
python setup.py sdist bdist_wheel

# PyPI 업로드
pip install twine
twine upload dist/*
```

## 라이선스

MIT License - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.
