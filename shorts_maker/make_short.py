#!/usr/bin/env python3
"""맛집 쇼츠 자동 편집기.

project.yaml 하나에 "어느 영상의 몇 초부터 + 할 말"만 적으면
9:16 컷 편집 + 위쪽 고정 제목 + 팝업 자막 + AI 내레이션 + 배경음악까지 넣은
완성 mp4를 만든다.

사용법
  python make_short.py scan  영상폴더/           # 영상 목록·길이 확인 + 1초 간격 미리보기 + project.yaml 초안
  python make_short.py build project.yaml        # 완성 영상 만들기
"""
import argparse
import asyncio
import json
import os
import re
import ssl
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import yaml

W, H, FPS = 1080, 1920, 30
HERE = Path(__file__).resolve().parent
FONT_DIR = HERE / "fonts"
FONTS = {
    "Black Han Sans": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/blackhansans/BlackHanSans-Regular.ttf",
    "NanumGothic ExtraBold": "https://cdn.jsdelivr.net/gh/google/fonts@main/ofl/nanumgothic/NanumGothic-ExtraBold.ttf",
}
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".avi", ".webm"}

DEFAULTS = {
    "output": "output.mp4",
    "title": "",
    "voice": "ko-KR-SunHiNeural",   # 남자 목소리: ko-KR-InJoonNeural / 끄기: none
    "voice_rate": "+15%",
    "original_audio_volume": 0.0,     # 원본 현장음 (0 = 끔, 0.3 정도면 은은하게)
    "bgm": None,
    "bgm_volume": 0.12,
    "title_font": "Black Han Sans",
    "title_size": 80,
    "title_y": 0.14,                  # 화면 위에서부터 비율
    "sub_font": "Black Han Sans",
    "sub_size": 78,
    "sub_y": 0.58,                    # 자막 세로 위치 (참고 영상 50~60%)
    "highlight_color": "#FFE400",
    "pop": True,                      # 자막 팝업 애니메이션
    "gap": 0.12,                      # 문장 사이 여유(초)
}


# ---------------------------------------------------------------- utils
def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"명령 실패: {' '.join(map(str, cmd))}\n{r.stderr[-2000:]}")
    return r.stdout


def probe(path):
    out = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
               "-of", "json", str(path)])
    j = json.loads(out)
    v = next((s for s in j["streams"] if s["codec_type"] == "video"), {})
    return {
        "duration": float(j["format"].get("duration", 0)),
        "has_audio": any(s["codec_type"] == "audio" for s in j["streams"]),
        "size": f"{v.get('width')}x{v.get('height')}",
    }


def ensure_fonts():
    FONT_DIR.mkdir(exist_ok=True)
    for name, url in FONTS.items():
        dst = FONT_DIR / url.rsplit("/", 1)[1]
        if not dst.exists():
            print(f"글꼴 다운로드: {name}")
            urllib.request.urlretrieve(url, dst)


def ass_color(hex_rgb, alpha="00"):
    h = hex_rgb.lstrip("#")
    return f"&H{alpha}{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def ass_time(t):
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ass_escape(s):
    return s.replace("\\", "\\\\").replace("{", "(").replace("}", ")").strip().replace("\n", "\\N")


# ---------------------------------------------------------------- TTS
def tts(text, voice, rate, out_path):
    import edge_tts
    import edge_tts.communicate as comm
    ca = os.environ.get("SSL_CERT_FILE")
    if ca and Path(ca).exists():  # 사내 프록시 등 인증서 환경 대응
        comm._SSL_CTX = ssl.create_default_context(cafile=ca)
    asyncio.run(edge_tts.Communicate(text, voice, rate=rate).save(str(out_path)))


# ---------------------------------------------------------------- scan
def cmd_scan(folder):
    folder = Path(folder)
    clips = sorted(p for p in folder.iterdir() if p.suffix.lower() in VIDEO_EXT)
    if not clips:
        sys.exit("영상 파일이 없습니다.")
    sheet_dir = folder / "_preview"
    sheet_dir.mkdir(exist_ok=True)
    cuts = []
    for c in clips:
        info = probe(c)
        print(f"{c.name:40s} {info['duration']:6.1f}초  {info['size']}  소리:{'O' if info['has_audio'] else 'X'}")
        # 1초 간격 썸네일을 한 장에 (초 표시 포함)
        sheet = sheet_dir / f"{c.stem}.jpg"
        cols = 6
        rows = max(1, -(-int(info["duration"]) // cols))
        run(["ffmpeg", "-y", "-v", "error", "-i", str(c), "-vf",
             f"fps=1,scale=240:-2,drawtext=text='%{{pts\\:hms}}':x=6:y=6:fontsize=22:fontcolor=yellow:box=1:boxcolor=black@0.6,"
             f"tile={cols}x{rows}", "-frames:v", "1", "-q:v", "4", str(sheet)])
        cuts.append({"clip": c.name, "start": 0.0, "end": round(min(info["duration"], 2.0), 1),
                     "say": "여기에 내레이션 문장"})
    draft = folder / "project.yaml"
    if not draft.exists():
        cfg = {"title": "서울에서 가장 ___한\n___ 맛집", "bgm": None, "cuts": cuts}
        draft.write_text(yaml.safe_dump(cfg, allow_unicode=True, sort_keys=False), encoding="utf-8")
        print(f"\n초안 생성: {draft}")
    print(f"미리보기 시트: {sheet_dir}/")


# ---------------------------------------------------------------- build
def build_ass(cfg, events, total):
    hl = ass_color(cfg["highlight_color"])
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Title,{cfg['title_font']},{cfg['title_size']},&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,7,4,8,60,60,{int(H * cfg['title_y'])},1
Style: Sub,{cfg['sub_font']},{cfg['sub_size']},&H00FFFFFF,&H00FFFFFF,&H00000000,&H96000000,0,0,0,0,100,100,0,0,1,6,3,5,80,80,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    lines = []
    if cfg["title"]:
        title = ass_escape(cfg["title"])
        # 두 번째 줄부터는 강조색 (참고 영상처럼 2줄 제목)
        parts = title.split("\\N", 1)
        if len(parts) == 2:
            title = f"{parts[0]}\\N{{\\c{hl}}}{parts[1]}"
        lines.append(f"Dialogue: 1,{ass_time(0)},{ass_time(total)},Title,,0,0,0,,{title}")
    y = int(H * cfg["sub_y"])
    for start, end, text, highlights in events:
        t = ass_escape(text)
        for word in highlights or []:
            t = t.replace(word, f"{{\\c{hl}}}{word}{{\\c&H00FFFFFF&}}")
        pop = "\\fscx70\\fscy70\\t(0,90,\\fscx108\\fscy108)\\t(90,160,\\fscx100\\fscy100)" if cfg["pop"] else ""
        lines.append(f"Dialogue: 0,{ass_time(start)},{ass_time(end)},Sub,,0,0,0,,{{\\pos({W // 2},{y}){pop}}}{t}")
    return head + "\n".join(lines) + "\n"


def cmd_build(project):
    project = Path(project).resolve()
    base = project.parent
    cfg = {**DEFAULTS, **yaml.safe_load(project.read_text(encoding="utf-8"))}
    cuts = cfg.get("cuts") or sys.exit("cuts 가 비어 있습니다.")
    ensure_fonts()
    use_voice = str(cfg["voice"]).lower() not in ("none", "false", "")
    tmp = Path(tempfile.mkdtemp(prefix="short_"))
    seg_files, events, t = [], [], 0.0

    for i, c in enumerate(cuts, 1):
        shots = c.get("shots") or [c]  # 한 문장 동안 여러 장면을 빠르게 넘길 때 shots 사용
        for s in shots:
            s["_path"] = base / s["clip"]
            if not s["_path"].exists():
                sys.exit(f"{i}번 컷: 영상 파일 없음 → {s['_path']}")
            s["_info"] = probe(s["_path"])
            s["_start"] = float(s.get("start", 0))
            s["_end"] = float(s.get("end", min(s["_info"]["duration"], s["_start"] + 1.5)))
            s["_len"] = max(s["_end"] - s["_start"], 0.1)
        src_total = sum(s["_len"] for s in shots)
        say = (c.get("say") or "").strip()
        text = c.get("text", say)

        voice_file = None
        if use_voice and say:
            voice_file = tmp / f"v{i:02d}.mp3"
            tts(say, c.get("voice", cfg["voice"]), cfg["voice_rate"], voice_file)
            dur = max(probe(voice_file)["duration"] + cfg["gap"], 0.6)
        else:
            dur = src_total

        ins, vchains, achains = [], [], []
        ov = float(c.get("original_audio_volume", cfg["original_audio_volume"]))
        for k, s in enumerate(shots):
            d = dur * s["_len"] / src_total  # 내레이션 길이를 장면 길이 비율로 나눔
            # 영상 구간이 짧으면 살짝 느리게 (최대 1.6배), 그래도 모자라면 마지막 프레임 유지
            slow = min(max(d / s["_len"], 1.0), 1.6)
            ins += ["-ss", f"{s['_start']:.3f}", "-t", f"{s['_len']:.3f}", "-i", str(s["_path"])]
            vchains.append(f"[{k}:v]setpts={slow:.4f}*(PTS-STARTPTS),scale={W}:{H}:force_original_aspect_ratio=increase,"
                           f"crop={W}:{H},setsar=1,fps={FPS},tpad=stop_mode=clone:stop_duration={d:.3f},"
                           f"trim=0:{d:.3f},setpts=PTS-STARTPTS[v{k}]")
            if ov > 0 and s["_info"]["has_audio"]:
                achains.append(f"[{k}:a]atempo={1 / slow:.4f},aresample=48000,aformat=channel_layouts=stereo,"
                               f"volume={ov},apad,atrim=0:{d:.3f},asetpts=PTS-STARTPTS[o{k}]")
            else:
                achains.append(f"anullsrc=r=48000:cl=stereo,atrim=0:{d:.3f}[o{k}]")
        n = len(shots)
        vf = ";".join(vchains) + ";" + "".join(f"[v{k}]" for k in range(n)) + f"concat=n={n}:v=1:a=0[v]"
        af = achains + ["".join(f"[o{k}]" for k in range(n)) + f"concat=n={n}:v=0:a=1[oa]"]
        mix = ["[oa]"]
        if voice_file:
            ins += ["-i", str(voice_file)]
            af.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo[na]")
            mix.append("[na]")
        af.append(f"{''.join(mix)}amix=inputs={len(mix)}:duration=longest:normalize=0,apad,atrim=0:{dur:.3f}[a]")
        seg = tmp / f"s{i:02d}.mp4"
        run(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex", ";".join([vf, *af]),
             "-map", "[v]", "-map", "[a]", "-t", f"{dur:.3f}", "-c:v", "libx264", "-preset", "veryfast",
             "-crf", "18", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(seg)])
        seg_files.append(seg)
        if text:
            events.append((t, t + dur, str(text), c.get("highlight")))
        print(f"[{i:2d}/{len(cuts)}] 장면 {n}개 → {dur:.2f}s  {say[:30]}")
        t += dur

    lst = tmp / "list.txt"
    lst.write_text("".join(f"file '{s}'\n" for s in seg_files))
    joined = tmp / "joined.mp4"
    run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(joined)])

    ass = tmp / "subs.ass"
    ass.write_text(build_ass(cfg, events, t), encoding="utf-8")
    out = (base / cfg["output"]).resolve()
    sub_filter = f"ass={ass}:fontsdir={FONT_DIR}"
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(joined)]
    if cfg["bgm"]:
        cmd += ["-stream_loop", "-1", "-i", str(base / cfg["bgm"]),
                "-filter_complex",
                f"[0:v]{sub_filter}[v];[1:a]volume={cfg['bgm_volume']},afade=t=out:st={max(t - 1, 0):.2f}:d=1[b];"
                f"[0:a][b]amix=inputs=2:duration=first:normalize=0[a]",
                "-map", "[v]", "-map", "[a]"]
    else:
        cmd += ["-vf", sub_filter, "-map", "0:v", "-map", "0:a"]
    cmd += ["-t", f"{t:.3f}", "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out)]
    run(cmd)
    print(f"\n완성: {out}  ({t:.1f}초, 컷 {len(cuts)}개)")


def main():
    ap = argparse.ArgumentParser(description="맛집 쇼츠 자동 편집기")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("scan").add_argument("folder")
    sub.add_parser("build").add_argument("project")
    a = ap.parse_args()
    cmd_scan(a.folder) if a.cmd == "scan" else cmd_build(a.project)


if __name__ == "__main__":
    main()
