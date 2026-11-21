"""transcribe.py PROJECT
Full-VOD pass: downloads the audio-only rendition, transcribes it (segment-level) and computes
per-second loudness. Outputs work/transcript.json, work/full.txt, work/loud.npy.
small.en runs ~4x realtime on 4 CPUs (a 4h stream takes ~1h): run it in the background."""
import sys, os, json, subprocess, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from common import load
p = load(sys.argv[1]); W = p["work"]
aud = os.path.join(W, "audio.mp4"); wav = os.path.join(W, "audio16k.wav")
if not os.path.exists(aud):
    subprocess.run(["yt-dlp", "-f", "Audio_Only/bestaudio", "-N", "8", "--no-progress", "-o", aud, p["vod_url"]], check=True)
if not os.path.exists(wav):
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", aud, "-ac", "1", "-ar", "16000", wav], check=True)
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", wav, "-f", "s16le", "-ac", "1", "-ar", "8000", "-"], capture_output=True).stdout
a = np.frombuffer(raw, np.int16).astype(np.float32) / 32768; n = len(a) // 8000
np.save(os.path.join(W, "loud.npy"), 20 * np.log10(np.sqrt((a[:n*8000].reshape(n, 8000) ** 2).mean(1)) + 1e-9))
import whisper, torch
torch.set_num_threads(os.cpu_count() or 4)
m = whisper.load_model(p["whisper_model"], download_root=p["models"])
r = m.transcribe(wav, language="en", fp16=False, verbose=False, condition_on_previous_text=False,
                 initial_prompt=p["whisper_prompt"] or None)
T = [{"s": round(s["start"], 2), "e": round(s["end"], 2), "t": s["text"].strip()} for s in r["segments"]]
json.dump(T, open(os.path.join(W, "transcript.json"), "w"))
open(os.path.join(W, "full.txt"), "w").write("".join(f"{int(s['s'])} {s['t']}\n" for s in T))
print("done", len(T), "segments")
