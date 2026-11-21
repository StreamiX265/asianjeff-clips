# Cloud container notes

- **Network**: Twitch API hosts `gql.twitch.tv` and `usher.ttvnw.net` are needed for yt-dlp metadata, plus the VOD's CloudFront host, which differs per VOD. Find it with `yt-dlp -f Audio_Only -g URL | sed -E 's#(https://[^/]+/).*#\1#'`, test with curl, and if the proxy refuses (`CONNECT tunnel failed, response 403`) call `get_environment` then `update_environment add_allowed_hosts:[<host>]`. Hugging Face is typically blocked; `openaipublic.azureedge.net` (openai-whisper weights) is allowed.
- **Proxy + ffmpeg**: ffmpeg's HLS client fails through the proxy (`Input/output error`). yt-dlp `--download-sections` therefore fails; use `scripts/fetch.py`, which downloads segments with python-requests and keeps whole segments plus a `.base` start time, so trims are frame-accurate (stream-copy cuts snap to keyframes and shift timing).
- **CPU only**: whisper `small.en` ≈ 4× realtime on 4 cores (`base.en` ≈ 7× but noticeably worse on slang). Full pass in the background; word-level passes only on short clip windows.
- **Fonts**: captions use `Inter ExtraBold` (present at /usr/share/fonts/opentype/inter). If missing, fall back to `DejaVu Sans Bold` in render.py's style line.
- **Disk**: the audio track of a 4h VOD is ~300 MB; each clip's raw 1080p60 window is ~30–60 MB. Don't download the whole video (14 GB).
- **Sessions are ephemeral**: anything worth keeping (clips, captions) goes to the user's GitHub repo; the preview lives on the artifact page.
- **Things not to do**: fetch Twitch chat via borrowed web client IDs (blocked as unauthorized access); disable TLS verification; publish clips anywhere other than where the user asked.
