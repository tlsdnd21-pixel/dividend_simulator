# 맛집 쇼츠 자동 편집기

참고 영상(서울 최고가 부대찌개 쇼츠)의 스타일을 그대로 재현해요.

- 9:16 세로, 1080×1920
- **위쪽 고정 제목** 2줄 (둘째 줄은 노란색)
- 가운데 **팝업 자막**, 원하는 단어만 노란색으로 강조
- **AI 내레이션** (Edge TTS, 무료) + 내레이션 길이에 맞춰 컷 자동 조절
- 현장음 살짝 + 배경음악(선택)

## 컴퓨터에 설치하기 (처음 한 번)

### Windows
1. **파이썬 설치:** https://www.python.org/downloads/ 에서 받아 설치해요. 설치 첫 화면에서 **"Add python.exe to PATH"를 꼭 체크**하세요.
2. **ffmpeg 설치:** 시작 메뉴에서 "PowerShell"을 열고 `winget install Gyan.FFmpeg`를 입력해요.
3. **PowerShell을 껐다가 다시 열고** `pip install pyyaml edge-tts`를 입력해요.
4. 확인: `python --version`, `ffmpeg -version`이 둘 다 버전을 출력하면 준비 끝이에요.

### Mac
1. 터미널을 열고 Homebrew(https://brew.sh) 안내대로 설치해요.
2. `brew install python ffmpeg`
3. `pip3 install pyyaml edge-tts` (Mac에서는 아래 명령의 `python`을 `python3`로 바꿔 쓰세요.)

글꼴(Black Han Sans, 나눔고딕 ExtraBold)은 처음 실행할 때 자동으로 받아요. 인터넷 연결이 필요해요(AI 내레이션도 인터넷 필요).

## 사용 순서
예: 바탕화면에 `shorts_maker` 폴더를 두고, 그 안에 `부대찌개` 폴더를 만들어 찍은 영상을 넣은 경우

```
cd Desktop\shorts_maker                     (Mac: cd ~/Desktop/shorts_maker)
python make_short.py scan 부대찌개
```
1. `부대찌개/_preview/`의 미리보기 이미지를 보고, 쓸 장면이 각 영상의 몇 초에 있는지 확인해요.
2. `부대찌개/project.yaml`을 메모장(또는 VS Code)으로 열어 제목, 구간, 할 말을 적고 저장해요. `example/project.yaml`을 참고하세요.
3. `python make_short.py build 부대찌개/project.yaml`
4. `부대찌개` 폴더에 완성본 mp4와 `..._편집용` 폴더가 생겨요.

## 캡컷에서 수정하기 (`..._편집용` 폴더)
| 파일 | 캡컷에 넣는 방법 |
|---|---|
| `1_영상_자막없음.mp4` | 메인 트랙 0초에 놓기 (소리 없음) |
| `2_내레이션.wav` | 오디오 트랙 0초에 놓기 |
| `3_현장음.wav` | 오디오 트랙 0초에 놓기 (`original_audio_volume`을 0보다 크게 했을 때만 소리 있음) |
| `4_배경음악.wav` | 오디오 트랙 0초 (`bgm`을 넣었을 때만 생김) |
| `5_자막.srt` | 텍스트 → 로컬 자막 → 가져오기. 글꼴·색은 캡컷에서 지정 |
| `6_제목.png` | 오버레이(PIP)로 올리고 영상 끝까지 늘리기. 투명 배경이라 그대로 겹쳐져요 |
| `컷별영상/`, `컷별내레이션/` | 순서를 바꾸거나 한 컷만 교체할 때 같은 번호끼리 짝지어 쓰기 |
| `내레이션_대본.txt` | 컷 번호, 길이, 문장 목록 |

모든 트랙은 길이가 같아서 **전부 0초에 맞춰 놓으면 싱크가 맞아요.**
`5_자막_스타일포함.ass`에는 노란 강조색과 팝업 효과가 들어 있어요. 캡컷은 이 효과를 그대로 불러오지 못해서, 강조는 캡컷에서 다시 해야 해요.

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
