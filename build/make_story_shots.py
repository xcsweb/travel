#!/usr/bin/env python3
"""Narrative cut: shots land on the song's bar lines (136 BPM, 4/4)."""
import subprocess
from pathlib import Path

ROOT = Path("/workspace/travel")
SRC = ROOT / "assets" / "stock"
OUT = ROOT / "assets" / "story2"
OUT.mkdir(parents=True, exist_ok=True)

W, H, FPS = 1080, 1920, 30
# bar starts derived from beat tracking: 0.09 + 1.7655 * k
CUTS = [0.00, 1.86, 3.62, 5.39, 7.15, 8.92, 10.68, 12.45,
        14.21, 15.98, 17.75, 19.51, 20.05, 22.75]

# src file id, source in-point, speed  (duration comes from CUTS)
SHOTS = [
    ("s01", "49878", 2.0, 1.0),   # 夜街人群（路口）
    ("s02", "4231", 2.0, 1.0),    # 夜市人流（人群中）
    ("s03", "1606", 2.0, 1.0),    # 站台（决定离开）
    ("s04", "50267", 2.0, 1.0),   # 公路日落航拍（出发）
    ("s05", "4396", 1.5, 1.0),    # 雪山（副歌第一拍）
    ("s06", "2213", 2.0, 1.0),    # 瀑布
    ("s07", "5363", 2.0, 1.0),    # 湖上小船（孤身）
    ("s08", "51500", 2.0, 0.5),   # 海滩浪 慢放
    ("s09", "44496", 2.0, 1.0),   # 海滩航拍日落
    ("s10", "41574", 2.0, 1.0),   # 森林小路
    ("s11", "43150", 2.0, 1.0),   # 两个人的背影
    ("s12", "1191", 2.0, 0.35),   # 椰树日落 极慢
]


def build(name, src, ss, dur, speed):
    need = dur * speed
    vf = (
        f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={W}:{H},"
        "eq=contrast=1.09:saturation=0.94:gamma=1.01,"
        "colorbalance=rs=-0.018:gs=0.006:bs=0.032:rh=0.032:gh=0.0:bh=-0.022,"
        "unsharp=5:5:0.45:5:5:0.0,"
        "vignette=angle=PI/4.7,"
        "noise=alls=3:allf=t,"
        f"fps={FPS},format=yuv420p"
    )
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                    "-ss", f"{ss}", "-t", f"{need + 0.4:.3f}",
                    "-i", str(SRC / f"{src}.mp4"),
                    "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast",
                    "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS),
                    str(OUT / f"{name}.mp4")], check=True)


if __name__ == "__main__":
    for name, src, ss, speed in SHOTS:
        dur = CUTS[int(name[1:])] - CUTS[int(name[1:]) - 1]
        build(name, src, ss, dur, speed)
        print(f"{name} <- {src}  {dur:.2f}s @ {speed}x")
