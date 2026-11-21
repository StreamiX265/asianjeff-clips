"""fetch.py PROJECT START END OUT.mp4
Download only the HLS segments of the VOD covering [START, END] seconds (no full download).
ffmpeg can't use the HTTPS proxy, so segments are fetched with requests and remuxed locally.
Writes OUT.mp4 and OUT.mp4.base (true start time of the first segment, in VOD seconds)."""
import sys, os, subprocess, requests, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(__file__)); from common import load
p = load(sys.argv[1]); s, e, out = float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
cache = os.path.join(p["work"], f"m3u8_{p['quality']}.txt")
if not os.path.exists(cache):
    u = subprocess.check_output(["yt-dlp", "-f", p["quality"], "-g", p["vod_url"]], stderr=subprocess.DEVNULL, text=True).strip()
    open(cache, "w").write(u)
url = open(cache).read().strip(); base = url.rsplit("/", 1)[0] + "/"
segs, t, dur = [], 0.0, None
for l in requests.get(url, timeout=60).text.splitlines():
    if l.startswith("#EXTINF:"): dur = float(l[8:].split(",")[0])
    elif l and not l.startswith("#"): segs.append((t, dur, l)); t += dur
pick = [x for x in segs if x[0] + x[1] > s and x[0] < e]
with cf.ThreadPoolExecutor(8) as ex: data = list(ex.map(lambda x: requests.get(base + x[2], timeout=120).content, pick))
tmp = out + ".ts"; open(tmp, "wb").write(b"".join(data))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-c", "copy", out], check=True)
os.remove(tmp); open(out + ".base", "w").write(str(pick[0][0])); print(out, "base", pick[0][0])
