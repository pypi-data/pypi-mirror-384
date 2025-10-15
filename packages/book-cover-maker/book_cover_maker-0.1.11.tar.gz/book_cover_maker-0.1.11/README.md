# Book Cover Maker

책 표지를 자동으로 생성하는 Python 도구입니다. 배경 이미지에 제목, 저자, 판본 정보를 추가하여 전문적인 책 표지를 만들 수 있습니다.

## 주요 기능

- 🎨 **다양한 언어 지원**: 한국어, 일본어, 영어 폰트 자동 선택
- 📝 **자동 텍스트 래핑**: 긴 제목이 자동으로 줄바꿈되어 표시
- 🖼️ **커스터마이징**: 사용자 정의 폰트 및 배경 이미지 지원
- ⚖️ **균등한 여백**: 제목 영역의 좌우 여백이 자동으로 균등하게 조정
- 📦 **간편한 설치**: pip를 통한 쉬운 설치 및 사용

## 설치

```bash
pip install book-cover-maker
```

## 사용법

### 기본 사용법

```bash
book-cover-maker "책 제목" "저자명" "1ST EDITION"
```

### 언어 선택

```bash
# 한국어 (기본값)
book-cover-maker "책 제목" "저자명" "1ST EDITION" --lang kr

# 일본어
book-cover-maker "本のタイトル" "著者名" "1ST EDITION" --lang jp

# 영어
book-cover-maker "Book Title" "Author Name" "1ST EDITION" --lang en
```

### 커스텀 배경 이미지 사용

```bash
book-cover-maker "책 제목" "저자명" "1ST EDITION" background.jpg
```

### 출력 파일 지정

```bash
book-cover-maker "책 제목" "저자명" "1ST EDITION" --output my_cover.png
```

## 명령행 옵션

- `bg_image_path`: 배경 이미지 경로 (선택사항, 기본 배경 사용)
- `title`: 책 제목
- `author`: 저자명
- `edition`: 판본 라벨 (예: "1ST EDITION")
- `--lang`: 언어 선택 (`kr`, `jp`, `en`, 기본값: `kr`)
- `--output`, `-o`: 출력 파일 경로 (선택사항)

## 폰트 지원

프로젝트에는 다음 폰트들이 포함되어 있습니다:

- **한국어**: Noto Sans KR (Regular, Bold)
- **일본어**: Noto Sans JP (Variable Font)
- **영어**: Noto Sans (Regular, Bold)

## 출력 예시

생성된 책 표지는 다음과 같은 요소들을 포함합니다:

- 상단 우측: 판본 라벨 (어두운 파란색 배경)
- 하단 좌측: 제목 (흰색 텍스트, 자동 줄바꿈)
- 제목 하단: 수평선
- 수평선 하단: 저자명 (회색 텍스트)

## 개발자 정보

- **개발자**: David Cho
- **이메일**: csi00700@gmail.com
- **저장소**: [GitHub](https://github.com/hakunamta00700/book_cover_maker)

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.
