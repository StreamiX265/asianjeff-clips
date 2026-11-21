"""preview.py PROJECT
Build work/preview/index.html + v/NN.mp4 (540x960 ~1.1Mbps copies) from OUT clips and captions.json,
ready for claude-artifacts publish_files (<=20 MiB/file, 64 MiB per call: publish in 2 batches)."""
import sys, os, json, html, subprocess, glob
sys.path.insert(0, os.path.dirname(__file__)); from common import load, clips
p = load(sys.argv[1]); P = os.path.join(p["work"], "preview"); V = os.path.join(P, "v"); os.makedirs(V, exist_ok=True)
caps = json.load(open(os.path.join(p["out"], "captions.json"))); cl = {c["id"]: c for c in clips(p)}
for f in sorted(glob.glob(os.path.join(p["out"], "[0-9][0-9]_*.mp4"))):
    n = os.path.basename(f)[:2]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f, "-vf", "scale=540:960", "-c:v", "libx264", "-preset", "veryfast",
                    "-b:v", "1100k", "-maxrate", "1400k", "-bufsize", "2800k", "-c:a", "aac", "-b:a", "96k", "-movflags", "+faststart",
                    os.path.join(V, f"{n}.mp4")], check=True)
def fmt(t): t = int(t); return f"{t//3600}:{t%3600//60:02d}:{t%60:02d}"
e = html.escape; cards = []
for c in caps:
    k = cl.get(c["id"], {})
    cards.append(f'''<article class="card"><div class="num">#{c['id']:02d}</div>
<video src="v/{c['id']:02d}.mp4" controls preload="metadata" playsinline></video>
<h2>{e(c['title'])}</h2><p class="meta">Stream {fmt(k.get('start', 0))} · hook {e(c.get('hook', ''))}</p>
<details><summary>Post captions</summary><p><b>TikTok</b> {e(c['tiktok_full'])}</p>
<p><b>Instagram</b> {e(c['instagram_full'])}</p><p><b>YouTube</b> <i>{e(c['yt_title'])}</i><br>{e(c['yt_full'])}</p></details></article>''')
title = e(p.get("title", "Clip preview"))
page = f'''<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><style>
:root{{color-scheme:light dark;--bg:#f6f6f4;--fg:#1b1b1b;--mut:#6b6b6b;--card:#fff;--line:#e4e4e0;--acc:#b8860b}}
@media (prefers-color-scheme:dark){{:root{{--bg:#141414;--fg:#ededed;--mut:#9a9a9a;--card:#1e1e1e;--line:#2c2c2c;--acc:#f2c94c}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,sans-serif}}
header{{padding:28px 24px 8px;max-width:1400px;margin:auto}} h1{{font-size:24px;margin:0 0 6px}} header p{{color:var(--mut);margin:0;max-width:70ch}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px;padding:20px 24px 48px;max-width:1400px;margin:auto}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px;position:relative}}
.num{{position:absolute;top:18px;left:18px;background:rgba(0,0,0,.65);color:#fff;font-weight:700;padding:2px 8px;border-radius:6px;z-index:1;font-size:13px}}
video{{width:100%;aspect-ratio:9/16;background:#000;border-radius:8px;display:block}} h2{{font-size:15px;margin:10px 0 4px}}
.meta{{color:var(--mut);font-size:13px;margin:0 0 6px}} details{{font-size:13px}} summary{{cursor:pointer;color:var(--acc);font-weight:600}} details p{{margin:8px 0}}
</style></head><body><header><h1>{title}</h1>
<p>Clips are in stream order. Each opens on its payoff second, then cuts back to the setup. 540×960 preview copies; uploads are 1080×1920. Tell Claude in chat which clips are good or need changes.</p></header>
<main>{"".join(cards)}</main></body></html>'''
open(os.path.join(P, "index.html"), "w").write(page); print(P)
