"""posts.py PROJECT RAW_BASE_URL
Assemble final per-platform post text into OUT/captions.json (adds tiktok_full, instagram_full,
yt_title, yt_full, url) from the drafted fields (title, hook, tiktok, instagram, yt) and
project.json "hashtags" (required tags) / "extra_tags" per platform.
RAW_BASE_URL e.g. https://raw.githubusercontent.com/OWNER/REPO/main/clips"""
import sys, os, json, glob
sys.path.insert(0, os.path.dirname(__file__)); from common import load
p = load(sys.argv[1]); base = sys.argv[2].rstrip("/") if len(sys.argv) > 2 else ""
f = os.path.join(p["out"], "captions.json"); caps = json.load(open(f))
tags = " ".join(p.get("hashtags", [])); ex = p.get("extra_tags", {})
files = {os.path.basename(x)[:2]: os.path.basename(x) for x in glob.glob(os.path.join(p["out"], "[0-9][0-9]_*.mp4"))}
for c in caps:
    c["tiktok_full"] = f"{c['tiktok']} {tags} {ex.get('tiktok', '#fyp #gaming')}".strip()
    c["instagram_full"] = f"{c['instagram']}\n\n{tags} {ex.get('instagram', '#streamer #gaming #reels')}".strip()
    c["yt_title"] = (c["title"] + " #shorts")[:100]
    c["yt_full"] = f"{c['yt']}\n\n{tags} {ex.get('youtube', '#shorts #gaming')}".strip()
    fn = files.get(f"{c['id']:02d}")
    if base and fn: c["url"] = f"{base}/{fn}"
json.dump(caps, open(f, "w"), indent=1, ensure_ascii=False); print("updated", len(caps))
