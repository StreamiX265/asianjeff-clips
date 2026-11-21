---
name: clip
description: The /clip command. Clip a stream VOD into viral vertical shorts and schedule them to TikTok, Instagram and YouTube via Buffer. Use when the user types /clip (optionally followed by a VOD link and notes) or says "clip this stream/video".
---

# /clip

Shortcut for the **clipper** skill, which holds the full workflow and scripts.

1. Load and follow the `clipper` skill (Skill tool, name `clipper`). If it isn't installed, tell the user to add the Clipper skill to their profile first.
2. Treat everything after `/clip` as the brief: VOD URL, streamer, number of clips, hashtags, focus, schedule start. Example: `/clip https://www.twitch.tv/videos/123 asianjeff 20 clips #asianjeff #gta6 #asianjeffclips`.
3. If no URL was given, ask for it. Use clipper's defaults for anything else unstated: 20 clips, ~30 s, the streamer's funniest reactions and quotes, all connected Buffer channels, starting at the next open slot today.
