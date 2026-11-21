"""Shared helpers. Every script takes the project dir (holding project.json) as its first argument."""
import json, os, sys
def load(project_dir):
    p = json.load(open(os.path.join(project_dir, "project.json")))
    p.setdefault("work", os.path.join(project_dir, "work"))
    p.setdefault("out", os.path.join(project_dir, "clips"))
    p.setdefault("models", os.path.expanduser("~/whisper-models"))
    p.setdefault("whisper_model", "small.en")
    p.setdefault("quality", "1080p60")
    p.setdefault("whisper_prompt", "")
    p.setdefault("fixes", {})
    p.setdefault("layouts", {})
    for d in (p["work"], p["out"], p["models"]): os.makedirs(d, exist_ok=True)
    p["dir"] = project_dir
    return p
def clips(p):
    f = os.path.join(p["dir"], "clips.json")
    return json.load(open(f)) if os.path.exists(f) else []
def tag(c): return f"{c['id']:02d}_{c['slug']}"
