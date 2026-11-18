#!/usr/bin/env python3
"""Cut real stock travel footage into graded 9:16 shots for the beat-cut cover."""
import subprocess
from pathlib import Path

ROOT = Path("/workspace/travel")
SRC = ROOT / "assets" / "stock"
OUT = ROOT / "assets" / "stock_v"
OUT.mkdir(parents=True, exist_ok=True)

W, H, FPS, KEEP = 1080, 1920, 30, 2.6

# contact-sheet index -> source file id
IDS = {
    1: "1170", 2: "1191", 3: "1564", 4: "1606", 5: "2168", 6: "2213",
    7: "2385", 8: "40657", 9: "4075", 10: "4119", 11: "4132", 12: "41574",
    13: "41576", 14: "4231", 15: "43150", 16: "4396", 17: "44496",
    18: "49845", 19: "49846", 20: "49878", 21: "50267", 22: "51500",
    23: "51585", 24: "51791", 25: "5363",
}

# index, in-point, vertical offset (-1..1 of slack), punch (crop factor)
SHOTS = {
    "v01": (22, 3.0, 0.00, 1.00),
    "v02": (4, 2.0, 0.00, 1.06),
    "v03": (12, 1.0, -0.05, 1.00),
    "v04": (17, 2.0, 0.00, 1.10),
    "v05": (6, 1.5, 0.00, 1.00),
    "v06": (13, 2.0, 0.00, 1.00),
    "v07": (23, 2.0, 0.00, 1.12),
    "v08": (9, 2.0, 0.00, 1.00),
    "v09": (19, 3.0, 0.00, 1.00),
    "v10": (11, 2.0, 0.00, 1.08),
    "v11": (2, 1.0, 0.00, 1.00),
    "v12": (5, 2.0, 0.00, 1.05),
    "v13": (21, 3.0, 0.00, 1.00),
}


def build(name, src, ss, off, punch):
    vf = (
        f"crop=iw/{punch if punch > 1 else 1}:ih/{punch if punch > 1 else 1},"
        f"scale={W}:{H}:force_original_aspect_ratio=increase:flags=lanczos,"
        f"crop={W}:{H}:(iw-{W})/2:(ih-{H})/2+({off})*(ih-{H})/2,"
        "eq=contrast=1.08:saturation=0.95:gamma=1.01,"
        "colorbalance=rs=-0.015:gs=0.006:bs=0.030:rh=0.030:gh=0.0:bh=-0.020,"
        "unsharp=5:5:0.45:5:5:0.0,"
        "vignette=angle=PI/4.6,"
        "noise=alls=3:allf=t,"
        f"fps={FPS},format=yuv420p"
    )
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-ss", str(ss), "-t", str(KEEP), "-i", str(SRC / f"{IDS[src]}.mp4"),
           "-vf", vf, "-an", "-c:v", "libx264", "-preset", "veryfast",
           "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS),
           str(OUT / f"{name}.mp4")]
    subprocess.run(cmd, check=True)


if __name__ == "__main__":
    for i, (name, args) in enumerate(SHOTS.items(), 1):
        build(name, *args)
        print(f"[{i:02d}/{len(SHOTS)}] {name} <- {args[0]}")
