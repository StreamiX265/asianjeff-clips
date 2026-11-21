"""render.py PROJECT ID [ID ...]   (or `all`)
Render clips to OUT/NN_slug.mp4: 1080x1920, 30fps, face cam on top (1080x840) + gameplay (1080x1080),
hook segment first then the main segment, loudness-normalised, word-by-word burned-in captions.

Clip spec (clips.json item): {"id","slug","hook":[s,e],"start","end","layout"}; optional "fx" (x offset
of the 608px-wide crop for full-screen-camera layouts), "fixes" (regex->text caption corrections).
Layouts come from project.json "layouts": {"A": {"cam":[x,y,w,h], "game":[x,y,w,h]}, "F": {"full":true}}.
Cam boxes should have aspect ~1.286 (1080/840) and game boxes 1:1, measured on the 1920x1080 source."""
import json, sys, os, subprocess, re
sys.path.insert(0, os.path.dirname(__file__)); from common import load, clips, tag
p = load(sys.argv[1]); allc = clips(p)
ids = [c["id"] for c in allc] if sys.argv[2:] == ["all"] else [int(x) for x in sys.argv[2:]]
import whisper, torch
torch.set_num_threads(os.cpu_count() or 4)
model = None
CAP_Y = {"stack": 880, "full": 1300}   # caption centre: on the cam/gameplay seam, or lower third

def ts(t):
    t = max(t, 0); return f"{int(t//3600)}:{int(t%3600//60):02d}:{t%60:05.2f}"

for spec in [c for c in allc if c["id"] in ids]:
    T = tag(spec); tmp = os.path.join(p["work"], "tmp", T); os.makedirs(tmp, exist_ok=True)
    L = p["layouts"][spec.get("layout", "B")]; full = L.get("full")
    hs, he = spec["hook"]; s, e = spec["start"], spec["end"]
    raw = os.path.join(tmp, "raw.mp4")
    need_lo, need_hi = min(hs, s), max(he, e)
    ok = os.path.exists(raw + ".base")
    if ok:
        b = float(open(raw + ".base").read())
        dur = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", raw]))
        ok = b <= need_lo and b + dur >= need_hi
    if not ok:
        subprocess.run(["python3", os.path.join(os.path.dirname(__file__), "fetch.py"), p["dir"], str(need_lo - 1), str(need_hi + 1), raw], check=True)
    lo = float(open(raw + ".base").read())
    def seg(a, b, i):
        return (f"[0:v]trim={a-lo:.3f}:{b-lo:.3f},setpts=PTS-STARTPTS,fps=30[v{i}];"
                f"[0:a]atrim={a-lo:.3f}:{b-lo:.3f},asetpts=PTS-STARTPTS[a{i}];")
    if full:
        v = f"[cv]crop=608:1080:{spec.get('fx', 656)}:0,scale=1080:1920:flags=lanczos,format=yuv420p[v];"
    else:
        cx, cy, cw, ch = L["cam"]; gx, gy, gw, gh = L["game"]
        v = ("[cv]split[c1][c2];"
             f"[c1]crop={cw}:{ch}:{cx}:{cy},scale=1080:840:flags=lanczos[cam];"
             f"[c2]crop={gw}:{gh}:{gx}:{gy},scale=1080:1080:flags=lanczos[game];"
             "[cam][game]vstack,format=yuv420p[v];")
    fc = seg(hs, he, 0) + seg(s, e, 1) + "[v0][a0][v1][a1]concat=n=2:v=1:a=1[cv][ca];" + v + "[ca]loudnorm=I=-14:TP=-1.5:LRA=11[a]"
    stack = os.path.join(tmp, "stack.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", stack], check=True)
    # captions are transcribed from the finished clip's own audio, so timing matches exactly
    model = model or whisper.load_model(p["whisper_model"], download_root=p["models"])
    r = model.transcribe(stack, language="en", fp16=False, word_timestamps=True, condition_on_previous_text=False,
                         initial_prompt=p["whisper_prompt"] or None)
    words = [w for sg in r["segments"] for w in sg.get("words", [])]
    fixes = {r"\bChad\b": "chat"}; fixes.update(p["fixes"]); fixes.update(spec.get("fixes", {}))
    for a_, b_ in fixes.items():
        for w in words: w["word"] = re.sub(a_, b_, w["word"], flags=re.I)
    json.dump(words, open(os.path.join(tmp, "words.json"), "w"))
    ass = ["[Script Info]", "ScriptType: v4.00+", "PlayResX: 1080", "PlayResY: 1920", "", "[V4+ Styles]",
           "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
           "Style: W,Inter ExtraBold,92,&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,100,100,0,0,1,7,3,5,60,60,0,1",
           "", "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text"]
    chunks, cur = [], []
    for w in words:   # <=3 words per caption; break at punctuation
        cur.append(w)
        if len(cur) == 3 or re.search(r"[.!?,]$", w["word"].strip()): chunks.append(cur); cur = []
    if cur: chunks.append(cur)
    y = CAP_Y["full" if full else "stack"]
    for ci, chk in enumerate(chunks):
        nxt = chunks[ci+1][0]["start"] if ci + 1 < len(chunks) else chk[-1]["end"] + 0.4
        for wi, w in enumerate(chk):
            st = w["start"]; en = chk[wi+1]["start"] if wi + 1 < len(chk) else min(nxt, chk[-1]["end"] + 0.6)
            if en <= st: continue
            parts = []
            for k, x in enumerate(chk):   # active word: yellow + slight pop
                t = x["word"].strip().upper().replace("{", "").replace("}", "")
                parts.append("{\\c&H00E5FF&\\fscx112\\fscy112}" + t + "{\\c&HFFFFFF&\\fscx100\\fscy100}" if k == wi else t)
            ass.append(f"Dialogue: 0,{ts(st)},{ts(en)},W,,0,0,0,,{{\\pos(540,{y})}}" + " ".join(parts))
    open(os.path.join(tmp, "caps.ass"), "w").write("\n".join(ass) + "\n")
    final = os.path.join(p["out"], f"{T}.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", stack, "-vf", f"ass={tmp}/caps.ass", "-c:v", "libx264", "-preset", "medium",
                    "-crf", "20", "-profile:v", "high", "-movflags", "+faststart", "-c:a", "copy", final], check=True)
    d = float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", final]))
    print(f"OK {final} {d:.1f}s words={len(words)}", flush=True)
