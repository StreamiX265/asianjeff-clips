"""qa.py PROJECT [SECOND=7]
Contact sheet of every rendered clip (one frame at SECOND) -> work/qa_sheet.png, numbered.
Check: face centred in the cam panel, no stray overlay in the crop, caption on the seam."""
import sys, os, subprocess, glob
sys.path.insert(0, os.path.dirname(__file__)); from common import load
p = load(sys.argv[1]); t = sys.argv[2] if len(sys.argv) > 2 else "7"
D = os.path.join(p["work"], "qa"); os.makedirs(D, exist_ok=True)
fs = sorted(glob.glob(os.path.join(p["out"], "[0-9][0-9]_*.mp4"))); th = []
for f in fs:
    n = os.path.basename(f)[:2]; o = os.path.join(D, f"{n}.png")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", t, "-i", f, "-frames:v", "1", "-vf",
                    f"scale=216:384,drawtext=text={n}:fontsize=28:fontcolor=yellow:borderw=2:x=6:y=6", o]); th.append(o)
cols = 10
args = sum([["-i", x] for x in th], [])
lay = "|".join(f"{(i%cols)*216}_{(i//cols)*384}" for i in range(len(th)))
out = os.path.join(p["work"], "qa_sheet.png")
if len(th) == 1: __import__("shutil").copy(th[0], out)
else: subprocess.run(["ffmpeg", "-v", "error", "-y", *args, "-filter_complex", f"xstack=inputs={len(th)}:layout={lay}:fill=black", out], check=True)
print(out)
