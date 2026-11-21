---
name: clipper
description: Turn a long Twitch (or YouTube/Kick) stream VOD into viral vertical short-form clips and schedule them to TikTok, Instagram Reels and YouTube Shorts through Buffer. Finds the funniest reactions and most quotable lines, cuts 9:16 clips with the streamer's face cam on top and gameplay below, opens each clip on its best second, burns in word-by-word captions, writes per-platform post captions with required hashtags, shows a preview page for approval, hosts the files on a public GitHub repo and schedules them into the user's Buffer posting slots. Use this whenever the user says /clip, pastes a stream or VOD link and wants clips, shorts, reels or TikToks from it, asks to "clip" a streamer (e.g. AsianJeff), or wants stream highlights posted to social media on a schedule, even if they don't mention every step.
---

# Clipper

Stream VOD → N viral vertical clips → captions → user approval → public hosting → Buffer schedule.

This workflow was built clipping AsianJeff's GTA 6 stream (4h18m, 20 clips, TikTok + Instagram + YouTube via Buffer). The defaults below are what the user approved there; ask only about what the request leaves open.

## 0. Gather the brief

From the request (ask once, in one AskUserQuestion, only for what is missing):

- **VOD URL** (required).
- **Streamer name** and **focus**. Default: funny moments and memorable quotes from the streamer themselves, not chat or game NPCs.
- **Number of clips**. Default 20. **Length**: ~30 s each unless the user asks for a specific clip to run longer.
- **Required hashtags**, e.g. `#asianjeff #gta6 #asianjeffclips`. Default `#<streamer> #<game> #<streamer>clips`.
- **Platforms**. Default: every channel connected in Buffer.
- **Schedule start**. Default: the next slot that hasn't passed, today.

Create a project directory (e.g. `/home/user/<streamer>-<vodid>/`) with `project.json`:

```json
{"vod_url": "https://www.twitch.tv/videos/…", "title": "AsianJeff GTA 6 clips",
 "whisper_prompt": "AsianJeff streaming GTA 6. Quitting Fortnite. Yo chat, bro, Lucia, Jason.",
 "fixes": {"\\b(4A|4-9|fornite|foreign)\\b": "Fortnite"},
 "hashtags": ["#asianjeff", "#gta6", "#asianjeffclips"],
 "extra_tags": {"tiktok": "#fyp #gaming #gta6clips", "instagram": "#gta6clips #streamer #gaming #reels", "youtube": "#shorts #gaming"},
 "layouts": {}}
```

`whisper_prompt` primes the transcriber with names and slang; `fixes` are regex corrections for words it still mishears in captions.

All scripts live in `scripts/` next to this file and take the project dir as their first argument (`S=<this skill dir>/scripts`).

## 1. Environment (cloud container)

Read `references/environment.md` before starting. The short version:

- `pip install -q yt-dlp openai-whisper` (ffmpeg is usually present). Hugging Face is often blocked, so use **openai-whisper** (models from `openaipublic.azureedge.net`), not faster-whisper.
- Twitch video comes from a per-VOD CloudFront host (e.g. `d2nvs31859zcd8.cloudfront.net`). If yt-dlp gets `403 … no rule allows this host`, add that exact host with `update_environment`; the user approves it on a card.
- ffmpeg can't use the HTTPS proxy, so never let yt-dlp hand a URL to ffmpeg. `fetch.py` pulls HLS segments itself.
- Don't fetch Twitch chat replay with borrowed client IDs. The permission system blocks it. Pick moments from transcript + loudness.

## 2. Transcribe the whole VOD (background)

```bash
python3 $S/transcribe.py PROJ      # run_in_background; small.en ≈ 4× realtime on 4 CPUs
python3 $S/candidates.py PROJ 60   # after it finishes
```

While it runs, do the Buffer discovery (step 9) and the layout survey (step 4).

## 3. Pick the moments

Read `work/candidates.txt` (top loud/keyword windows) and grep `work/full.txt` for anything else promising. What made the cut and got approved:

- **The streamer's own reactions and lines**: panic ("we're cooked bro, what do I do"), self-owns ("it's the game, not me bro"), hot takes ("Fortnite is actually so much better"), getting curved ("chat, why does she not want me bro"), relatable bits ("12,000 steps today… another marathon").
- A clear setup → payoff inside ~30 s, understandable without stream context.
- Skip long silent stretches, menus, and quiet NPC dialogue unless the streamer is reacting over it.
- Leave out slurs, transphobic or otherwise demeaning lines even if loud. Start the clip after such a line, or pick another moment. They get channels reported.
- The user replaced opening/"just chatting" clips with funnier gameplay reactions. Prefer reactions to gameplay over pre-game talk.

Pick N plus 3–5 alternates and write `clips.json` in **stream order**, ids 1..N:

```json
[{"id": 1, "slug": "were_cooked_bro", "hook": [2985, 2990], "start": 2966, "end": 3020, "layout": "A"}]
```

Rough times from `full.txt` are fine here; step 5 makes them precise.

## 4. Face-cam layouts

Streams change overlay mid-stream (cam size and position moved three times in the AsianJeff VOD, and the opening was full-screen camera).

```bash
python3 $S/frames.py PROJ          # one frame per clip -> work/frames_sheet.png
```

Look at the sheet, group clips by layout, then measure each layout's cam box on a full-size frame (`work/frames/<id>.png`, crop + `drawgrid` helps). Add to `project.json`:

```json
"layouts": {"A": {"cam": [95, 315, 432, 336], "game": [600, 140, 875, 875]},
            "F": {"full": true}}
```

- `cam` = x, y, w, h in the 1920×1080 source, aspect ≈ 1.286 (it is scaled to 1080×840), centred on the face, inside the webcam border.
- `game` = square region (scaled to 1080×1080), right of the cam, below the chat overlay. ~875 px from y=140 worked.
- `F` = full-screen camera: a single 608×1080 crop; set per-clip `"fx"` so the face is centred.

Set each clip's `"layout"`.

## 5. Precise cut points

```bash
python3 $S/prep.py PROJ            # word-level timestamps per clip window -> work/tmp/NN_slug/words.txt
```

Each `words.txt` entry is `VODseconds[!]:word` (`!` = loud). For every clip set:

- **hook** = the best 1.5–4 s, i.e. the punchline or scream, said by the streamer. It plays first. It must start on sound: a silent first second loses the viewer.
- **start/end** = the setup through the payoff; usually start just after the hook's context begins. Hook + main ≈ 30 s (≤ 31). End on a finished sentence, not mid-word.
- The hook may repeat inside the main part. That's fine and common.

## 6. Render

```bash
python3 $S/render.py PROJ all      # ~80 s per clip; run_in_background with a Monitor on "OK|Error|Traceback"
python3 $S/qa.py PROJ              # contact sheet -> work/qa_sheet.png, look at it
```

Output: `clips/NN_slug.mp4`, 1080×1920, 30 fps, loudness −14 LUFS, yellow active-word captions on the cam/gameplay seam. Fix framing issues by editing the layout or `fx`, deleting `work/tmp/NN_slug/stack.mp4`, and re-rendering just that id.

## 7. Post captions

Write `clips/captions.json` yourself, one object per clip, in the streamer's voice and platform style:

```json
{"id": 1, "title": "\"We're COOKED Bro, What Do I Do?!\" 😭 AsianJeff GTA 6", "hook": "\"We're cooked bro\"",
 "tiktok": "first GTA 6 shootout on controller and he's fully panicking 😭🔫 'lock in!'",
 "instagram": "First GTA 6 shootout on a controller 😭 \"We're cooked bro, what do I do?!\" 🔫",
 "yt": "AsianJeff's first GTA 6 gunfight on controller turns into pure panic."}
```

TikTok: short, lowercase, meme tone. Instagram: quote the line plus emojis. YouTube: title ≤ 90 chars with the quote, plus a one-line description. Then `python3 $S/posts.py PROJ` adds the hashtags (once hosting is known, rerun with the raw base URL to add `url`).

## 8. Preview and approval loop

```bash
python3 $S/preview.py PROJ         # work/preview/index.html + v/NN.mp4
```

Publish with `claude-artifacts` `publish_files` (title from project.json, icon `video`): index.html + the first ~10 videos, then republish with slug/base_version for the rest (64 MiB per call). Then ask with AskUserQuestion: **All N are good** / **Some need changes** / **Redo the selection**.

Users often answer in chat instead ("replace 1 & 2 with something funnier", "let clip 20 run longer", "rearrange in order"). Apply the change, re-render only affected clips (renumber by moving files and tmp dirs, keeping stream order), rebuild the preview, republish changed files, and ask again. Don't move on until the user picks the approval option.

## 9. Hosting (public URLs for Buffer)

Buffer only accepts publicly downloadable direct URLs. Use a public GitHub repo the user owns:

1. The user connects GitHub at https://claude.ai/connect-github (installing the Claude GitHub App on the repo) and creates an empty **public** repo.
2. `add_repo` (access `push`), clone, then `git checkout -b main`, copy clips into `clips/`, commit, and push in batches of ~5 files (the proxy rejects huge pushes). End commit messages with the session's attribution lines.
3. Verify: `curl -o /dev/null -w "%{http_code}" https://raw.githubusercontent.com/OWNER/REPO/main/clips/<file>` is 200, and `api.github.com/repos/OWNER/REPO` shows `"private": false`.
4. Rerun `posts.py PROJ https://raw.githubusercontent.com/OWNER/REPO/main/clips`.

Tell the user to keep the repo public and the files in place until every post has gone out.

## 10. Schedule in Buffer

Read `references/buffer.md`: it has the exact call shapes and the plan limits that bit us. In outline:

1. `get_account` (org, timezone, currentTime), `list_channels`, `get_channel` per channel (postingSchedule).
2. Build the slot list from the schedule, starting at the first slot after `currentTime`.
3. Post clips **in order** with `mode: customScheduled` and explicit `dueAt` per slot. Parallel `addToQueue` calls land out of order. Test one post first.
4. When Buffer refuses for limits, save the rest with `saveToDraft: true`, then `send_later` a follow-up (after the next batch has gone out) to move drafts into freed slots, and say so.

## 11. Report

Finish with a short summary: what was scheduled where and when (a small table per day/channel), what was left as drafts and why, where the files live (repo + local `clips/`), the preview link, and a one-line reminder that clips are the streamer's content and channels can get copyright claims.
