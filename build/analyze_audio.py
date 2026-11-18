#!/usr/bin/env python3
"""Measure a track before cutting to it: tempo, bar grid, section energy.

Usage:
    python3 build/analyze_audio.py ref.mp4          # 只打印
    python3 build/analyze_audio.py ref.mp4 --json   # 输出机器可读结构

剪辑点用 bars 里的时间，不要用估算的 BPM 均分。
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import librosa
import numpy as np


def load(path: Path, sr: int = 22050):
    if path.suffix.lower() == ".wav":
        return librosa.load(str(path), sr=sr, mono=True)[0], sr
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        wav = Path(tmp.name)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(path),
                    "-vn", "-ac", "1", "-ar", str(sr), str(wav)], check=True)
    y, _ = librosa.load(str(wav), sr=sr, mono=True)
    wav.unlink(missing_ok=True)
    return y, sr


def analyze(path: Path) -> dict:
    y, sr = load(path)
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, hop_length=512)
    beats = librosa.frames_to_time(beat_frames, sr=sr, hop_length=512)
    bpm = float(np.atleast_1d(tempo)[0])

    # 4/4：取前 8 拍里最像强拍的那一拍作为第一小节起点
    bar = beats[0] if len(beats) else 0.0
    bar_len = 60.0 / bpm * 4
    bars = [round(float(bar + i * bar_len), 3) for i in range(int((len(y) / sr - bar) // bar_len) + 1)]

    # 段落：按 0.5 秒窗口的能量与低频占比，找“质变点”
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=256))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)
    t = librosa.frames_to_time(np.arange(S.shape[1]), sr=sr, hop_length=256)
    low = S[freqs < 150].mean(0)
    rms = librosa.feature.rms(y=y, hop_length=256)[0]

    sections = []
    for start in np.arange(0, len(y) / sr, 0.5):
        m = (t >= start) & (t < start + 0.5)
        if not m.any():
            continue
        sections.append({
            "t": round(float(start), 2),
            "rms_db": round(float(20 * np.log10(rms[m].mean() + 1e-9)), 1),
            "low_db": round(float(20 * np.log10(low[m].mean() + 1e-9)), 1),
        })

    silent = [s["t"] for s in sections if s["rms_db"] < -40]
    end = round(float(len(y) / sr), 2)
    return {
        "file": str(path),
        "duration": end,
        "bpm": round(bpm, 2),
        "bar_length": round(bar_len, 4),
        "bars": bars,
        "silence_from": silent[0] if silent else None,
        "sections": sections,
    }


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    info = analyze(Path(sys.argv[1]))
    if "--json" in sys.argv:
        print(json.dumps(info, ensure_ascii=False, indent=2))
        return
    print(f"{info['file']}")
    print(f"  duration {info['duration']}s  bpm {info['bpm']}  bar {info['bar_length']}s")
    print(f"  bars: {info['bars'][:16]}")
    if info["silence_from"]:
        print(f"  silence from {info['silence_from']}s")
    print("  t     rms   low")
    for s in info["sections"][::2]:
        print(f"  {s['t']:5.1f} {s['rms_db']:6.1f} {s['low_db']:6.1f}")


if __name__ == "__main__":
    main()
