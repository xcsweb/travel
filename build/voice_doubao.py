#!/usr/bin/env python3
"""Doubao (Volcengine) cloned-voice TTS.

Synthesize a line with a speaker cloned in the Doubao console
(https://console.volcengine.com/speech/new). Credentials live outside the repo:

    export VOLC_API_KEY=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    export VOLC_SPEAKER=S_xxxxxxxx

    python3 build/voice_doubao.py --text "璧山秀湖夜色美" --out assets/tts/demo.mp3

Or keep them in a local env file (KEY=VALUE, never commit it):

    python3 build/voice_doubao.py --env-file ~/.volc_local/cred.env --text "..."

Notes:
- X-Api-Key takes the API key value (UUID format in the new console),
  not the key display name shown next to it in the console.
- Voices cloned with model 2.0 need X-Api-Resource-Id: seed-icl-2.0.
- The response is a stream of JSON lines; audio chunks are base64 in "data".
"""
import argparse
import base64
import json
import os
import sys
import uuid

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://openspeech.bytedance.com/api/v3/tts/unidirectional"
DEFAULT_ENV_FILE = os.path.expanduser("~/.volc_local/cred.env")


def load_env_file(path):
    values = {}
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def resolve_credentials(args):
    values = dict(os.environ)
    if args.env_file:
        values.update(load_env_file(os.path.expanduser(args.env_file)))
    elif os.path.exists(DEFAULT_ENV_FILE):
        values.update(load_env_file(DEFAULT_ENV_FILE))
    api_key = args.api_key or values.get("VOLC_API_KEY")
    speaker = args.speaker or values.get("VOLC_SPEAKER")
    if not api_key or not speaker:
        sys.exit("missing credentials: set VOLC_API_KEY / VOLC_SPEAKER, or pass --env-file")
    return api_key, speaker


def read_text(args):
    if args.text:
        return args.text
    if args.text_file:
        with open(args.text_file, encoding="utf-8") as fh:
            return " ".join(line.strip() for line in fh if line.strip())
    sys.exit("either --text or --text-file is required")


def synthesize(api_key, speaker, text, out, resource_id, fmt, sample_rate):
    headers = {
        "Content-Type": "application/json",
        "X-Api-Key": api_key,
        "X-Api-Request-Id": str(uuid.uuid4()),
        "X-Api-Resource-Id": resource_id,
    }
    body = {
        "user": {"uid": "travel-local"},
        "req_params": {
            "text": text,
            "speaker": speaker,
            "audio_params": {"format": fmt, "sample_rate": sample_rate},
        },
    }
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    written = 0
    final_message = None
    with requests.post(URL, headers=headers, json=body, stream=True, timeout=180) as resp:
        if resp.status_code != 200:
            detail = resp.text[:300].replace("\n", " ")
            sys.exit(f"TTS failed: HTTP {resp.status_code} {detail}")
        with open(out, "wb") as fh:
            for raw in resp.iter_lines(decode_unicode=False):
                if not raw:
                    continue
                line = raw.decode("utf-8", "replace").strip()
                if line.startswith("data:"):
                    line = line[5:].strip()
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                code = obj.get("code")
                data = obj.get("data")
                if isinstance(data, str) and data:
                    chunk = base64.b64decode(data)
                    fh.write(chunk)
                    written += len(chunk)
                if code == 20000000:
                    final_message = obj.get("message") or "OK"
                elif code not in (0, None):
                    sys.exit(f"TTS failed: {code} {obj.get('message', '')}")
    if written == 0:
        sys.exit("TTS returned no audio")
    return written, final_message or "OK"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--text", help="text to synthesize")
    ap.add_argument("--text-file", help="read text from a UTF-8 file")
    ap.add_argument("--out", default=os.path.join(ROOT, "assets", "tts", "doubao.mp3"))
    ap.add_argument("--speaker", help="cloned speaker id, default $VOLC_SPEAKER")
    ap.add_argument("--api-key", help="API key value, default $VOLC_API_KEY")
    ap.add_argument("--env-file", help=f"KEY=VALUE credentials file, default {DEFAULT_ENV_FILE}")
    ap.add_argument("--resource-id", default="seed-icl-2.0",
                    help="seed-icl-2.0 for clone 2.0 (default)")
    ap.add_argument("--format", default="mp3", choices=["mp3", "wav", "pcm", "ogg", "aac"])
    ap.add_argument("--sample-rate", type=int, default=24000)
    args = ap.parse_args()

    api_key, speaker = resolve_credentials(args)
    text = read_text(args)
    written, message = synthesize(api_key, speaker, text, args.out,
                                  args.resource_id, args.format, args.sample_rate)
    print(f"{len(text)} chars -> {written} bytes, {args.format}, {message}")
    print(f"speaker {speaker}  -> {args.out}")


if __name__ == "__main__":
    main()
