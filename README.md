# 世界走不完 — 旅行情绪短片

52 秒竖屏短片（1080×1920 / 30fps），13 个 AI 画面镜头 + 原创钢琴 BGM + 中文旁白 + 字幕。

## 目录

```
build/      旁白、混音、运镜与自研渲染脚本
config/     文案、时间轴（52s）
edit/       codecut 工程（project.json / ops.json）与字幕字体
assets/ai/  13 张原始竖屏画面
```

## 依赖

- Python 3：`numpy` `scipy` `Pillow` `sherpa-onnx`
- FFmpeg / ffprobe
- [codecut](https://github.com/xcsweb/codecut)（渲染用）

离线 TTS 模型不入库，首次运行前下载：

```bash
mkdir -p assets/models && cd assets/models
curl -LO https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/matcha-icefall-zh-baker.tar.bz2
tar xf matcha-icefall-zh-baker.tar.bz2
curl -LO https://github.com/k2-fsa/sherpa-onnx/releases/download/vocoder-models/vocos-22khz-univ.onnx
```

## 生成顺序

```bash
python3 build/voice.py        # 10 句旁白 -> assets/vo
python3 build/audio.py        # BGM + 混音 -> assets/audio/mix.wav
python3 build/make_motion.py  # Ken Burns 运镜 -> assets/motion
cd ../codecut && npm ci && npm run build
node dist/cli.js render --project ../travel/edit
```

成片、字体缓存、jobs 诊断与中间音频/视频均不入库；成片走 Release。
