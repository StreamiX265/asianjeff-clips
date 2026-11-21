"""frames.py PROJECT [T1 T2 ...]
Grab one 1080p frame per clip in clips.json (3s after start), or at the given VOD times, and tile
them into work/frames_sheet.png (numbered) so Claude can see which face-cam layout each clip uses.
Also saves full-size frames as work/frames/<label>.png for measuring cam boxes."""
import sys, os, subprocess
sys.path.insert(0, os.path.dirname(__file__)); from common import load, clips
p = load(sys.argv[1]); W = p["work"]; D = os.path.join(W, "frames"); os.makedirs(D, exist_ok=True)
pts = [(str(c["id"]), int(c["start"]) + 3) for c in clips(p)] if len(sys.argv) < 3 else [(a, int(float(a))) for a in sys.argv[2:]]
fetch = os.path.join(os.path.dirname(__file__), "fetch.py"); thumbs = []
for label, t in pts:
    mp4 = os.path.join(D, f"{label}.mp4"); png = os.path.join(D, f"{label}.png"); th = os.path.join(D, f"t_{label}.png")
    subprocess.run(["python3", fetch, p["dir"], str(t), str(t + 1), mp4], capture_output=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-frames:v", "1", png])
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", png, "-vf",
                    f"scale=480:270,drawtext=text='{label}':fontsize=40:fontcolor=yellow:borderw=2:x=8:y=8", th])
    if os.path.exists(th): thumbs.append(th)
cols = 4; rows = (len(thumbs) + cols - 1) // cols
args = sum([["-i", t] for t in thumbs], [])
subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex",
                f"{''.join(f'[{i}]' for i in range(len(thumbs)))}xstack=inputs={len(thumbs)}:layout=" +
                "|".join(f"{(i%cols)*480}_{(i//cols)*270}" for i in range(len(thumbs))) + ":fill=black",
                os.path.join(W, "frames_sheet.png")] if len(thumbs) > 1 else ["true"])
print("sheet:", os.path.join(W, "frames_sheet.png"), len(thumbs), "frames")
