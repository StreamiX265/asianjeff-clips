"""prep.py PROJECT [ID ...]
For each clip in clips.json: fetch a raw window (+-12s around hook/start/end), transcribe it with
word timestamps, and write work/tmp/NN_slug/words.txt as `VODsec[!]:word` (! = loud). Read these to
set precise hook/start/end times: Whisper segment times are too coarse for cutting."""
import sys, os, json, subprocess, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from common import load, clips, tag
p = load(sys.argv[1]); ids = [int(x) for x in sys.argv[2:]]
import whisper, torch
torch.set_num_threads(os.cpu_count() or 4)
m = whisper.load_model(p["whisper_model"], download_root=p["models"])
for c in clips(p):
    if ids and c["id"] not in ids: continue
    tmp = os.path.join(p["work"], "tmp", tag(c)); os.makedirs(tmp, exist_ok=True)
    lo = min(c["hook"][0], c["start"]) - 12; hi = max(c["hook"][1], c["end"]) + 12; raw = os.path.join(tmp, "raw.mp4")
    subprocess.run(["python3", os.path.join(os.path.dirname(__file__), "fetch.py"), p["dir"], str(lo), str(hi), raw], check=True, capture_output=True)
    base = float(open(raw + ".base").read())
    r = m.transcribe(raw, language="en", fp16=False, word_timestamps=True, condition_on_previous_text=False,
                     initial_prompt=p["whisper_prompt"] or None)
    words = [(round(w["start"] + base, 2), w["word"].strip()) for s in r["segments"] for w in s["words"]]
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", raw, "-f", "s16le", "-ac", "1", "-ar", "8000", "-"], capture_output=True).stdout
    a = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768; n = len(a) // 4000
    db = 20 * np.log10(np.sqrt((a[:n*4000].reshape(n, 4000) ** 2).mean(1)) + 1e-9)
    out = [f"{t:.1f}{'!' if int((t-base)*2) < len(db) and db[int((t-base)*2)] > -14 else ''}:{w}" for t, w in words]
    open(os.path.join(tmp, "words.txt"), "w").write(" ".join(out)); print(tag(c), "done", flush=True)
