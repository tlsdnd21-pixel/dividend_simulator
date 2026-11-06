# 맛집 쇼츠 자동 편집기

참고 영상(서울 최고가 부대찌개 쇼츠)의 스타일을 그대로 재현해요.

- 9:16 세로, 1080×1920
- **위쪽 고정 제목** 2줄 (둘째 줄은 노란색)
- 가운데 **팝업 자막**, 원하는 단어만 노란색으로 강조
- **AI 내레이션** (Edge TTS, 무료) + 내레이션 길이에 맞춰 컷 자동 조절
- 현장음 살짝 + 배경음악(선택)

## 준비 (처음 한 번)
```bash
# ffmpeg 설치 (Mac: brew install ffmpeg / Windows: winget install ffmpeg)
pip install pyyaml edge-tts
```
글꼴(Black Han Sans, 나눔고딕 ExtraBold)은 처음 실행할 때 자동으로 받아요.

## 사용 순서
1. 촬영한 영상을 폴더 하나에 넣기
2. `python make_short.py scan 폴더/`
   - 영상별 길이 출력
   - `폴더/_preview/`에 1초 간격 미리보기 이미지 생성 (몇 초에 뭐가 나오는지 확인용)
   - `폴더/project.yaml` 초안 생성
3. `project.yaml`에 제목, 쓸 구간, 할 말 적기 (`example/project.yaml` 참고)
4. `python make_short.py build 폴더/project.yaml` → 완성 mp4

## project.yaml 핵심
```yaml
title: |
  서울에서 가장 비싼
  부대찌개 맛집
cuts:
  # 장면 1개 + 문장 1개
  - {clip: IMG_001.MOV, start: 3.0, end: 4.5, say: "2인분에 무려 5만 원입니다", highlight: ["5만 원"]}
  # 문장 하나 동안 장면 여러 개를 빠르게 (참고 영상 스타일)
  - say: "와 서울에서 가장 비싼 부대찌개집에 다녀왔습니다"
    shots:
      - {clip: IMG_001.MOV, start: 0.0, end: 1.2}
      - {clip: IMG_002.MOV, start: 5.0, end: 6.0}
```

| 설정 | 기본값 | 설명 |
|---|---|---|
| `voice` | `ko-KR-SunHiNeural` | 여자 목소리. 남자: `ko-KR-InJoonNeural`, 끄기: `none` |
| `voice_rate` | `+15%` | 말 빠르기 |
| `original_audio_volume` | `0` | 현장음 크기 (0.2~0.3 추천) |
| `bgm` / `bgm_volume` | 없음 / `0.12` | 배경음악 파일 (저작권 없는 음원) |
| `title_size` / `sub_size` | `80` / `78` | 글자 크기 |
| `title_y` / `sub_y` | `0.14` / `0.58` | 화면 위에서부터의 위치 비율 |
| `text` (컷별) | `say`와 같음 | 자막을 내레이션과 다르게 쓰고 싶을 때 |

## 촬영 팁 (참고 영상 기준)
- 첫 장면은 **움직임이 있는 장면** (냄비 들고 오기, 끓는 모습)
- 꼭 찍을 것: 간판·입구, 메뉴판 가격, 재료 클로즈업, 국자로 뜨기, 면 집어 올리기, 영수증
- 장면마다 3~5초씩 넉넉히 찍기. 편집할 때 1~1.5초만 써요.
