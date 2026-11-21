"""candidates.py PROJECT [N=60]
Score every 30s window by loudness peaks + reaction keywords, keep the top N non-overlapping
windows and write work/candidates.txt (timestamped transcript around each) for Claude to read."""
import sys, os, json, re, numpy as np
sys.path.insert(0, os.path.dirname(__file__)); from common import load
p = load(sys.argv[1]); W = p["work"]; N = int(sys.argv[2]) if len(sys.argv) > 2 else 60
T = json.load(open(os.path.join(W, "transcript.json"))); db = np.load(os.path.join(W, "loud.npy"))
KW = r"\b(oh my god|what the|bro|no way|yo+|wtf|hell|bruh|holy|dude|let'?s go|chat|crazy|insane|why|stop|wait|fuck|shit|dead|nah|lmao|haha|clip|cooked|help)\b"
rows = []
for st in range(0, len(db) - 30, 10):
    txt = " ".join(s["t"] for s in T if s["s"] < st + 30 and s["e"] > st)
    rows.append((st, np.sort(db[st:st+30])[-5:].mean(), len(re.findall(KW, txt.lower()))))
L = np.array([r[1] for r in rows]); K = np.array([r[2] for r in rows], float)
score = (L - L.mean()) / (L.std() + 1e-9) + 0.6 * (K - K.mean()) / (K.std() + 1e-9)
picked = []
for i in np.argsort(-score):
    if all(abs(rows[i][0] - q) >= 60 for q in picked): picked.append(rows[i][0])
    if len(picked) >= N: break
with open(os.path.join(W, "candidates.txt"), "w") as f:
    for st in sorted(picked):
        f.write(f"\n### {st//3600}:{st%3600//60:02d}:{st%60:02d} ({st}s) score={score[st//10]:.2f}\n")
        f.write(" | ".join(f"[{int(s['s'])}] {s['t']}" for s in T if s["s"] < st + 45 and s["e"] > st - 15) + "\n")
print("wrote", len(picked), "candidates")
