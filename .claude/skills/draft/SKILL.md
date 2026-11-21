---
name: draft
description: The /draft command. Move the user's Buffer drafts (e.g. leftover clips from /clip) into open posting-schedule slots on TikTok, Instagram, YouTube or any connected channel, in clip order, within Buffer's plan limits. Use when the user types /draft, or asks to post, schedule, queue or "push out" their Buffer drafts.
---

# /draft: schedule Buffer drafts into open slots

Text after `/draft` narrows the job: channel names (`tiktok`, `youtube`, `instagram`), a count (`5`), a start time (`from tomorrow 9am`), or `now` (publish the next draft immediately on each channel; confirm before doing that, since it posts publicly at once). With nothing after it, fill every open slot on every channel, starting at the next slot that hasn't passed.

Load the Buffer tools with ToolSearch (`get_account`, `list_channels`, `get_channel`, `list_posts`, `edit_post`), plus `send_later` if it's available.

## Steps

1. **Account and time.** Call `get_account`. Use its `currentTime` and timezone offset for every `dueAt`. Say which organization you're using by name.
2. **Channels and schedules.** Call `list_channels`, then `get_channel` for each in-scope channel to read `postingSchedule` (per-day `times`, channel timezone).
3. **What's there.** For each channel, call `list_posts` with `channelIds:[id]`, `status:["draft"]`, then again with `status:["scheduled"]` (use `first:100` and page through). Also check `status:["error"]` and report any failed posts.
4. **Order the drafts.** Put clips in clip order using the `NN_` number in `assets[].source` (e.g. `.../clips/12_disappointed_in_gta6.mp4`). Drafts without a number go after them, oldest `createdAt` first.
5. **Free capacity per channel.**
   - The plan's scheduled-post cap comes from `get_account` → `organizations[].limits.scheduledPosts` (10 on the free plan). It applies **per channel**. Free = cap − scheduled count.
   - **YouTube allows at most 2 posts per calendar day.** Count posts already scheduled on each day, and only use slots on days with fewer than 2.
6. **Pick slots.** Walk the posting schedule forward from `currentTime` (or the requested start). Skip slots already taken by a scheduled post on that channel (same `dueAt` minute) and YouTube days that are full. Take as many as free capacity allows.
7. **Schedule.** For each draft → slot, call `edit_post {postId, mode:"customScheduled", dueAt:"YYYY-MM-DDTHH:MM:00±HH:MM"}` and send nothing else, so text, video and metadata stay as they are. Do them **one channel at a time, in order**. If a call fails with a limit error, stop that channel and keep the rest as drafts. If it fails because a time is in the past, move to the next slot.
8. **Leftovers.** If drafts remain, schedule a `send_later` (initiation `own_followup`, or `human_request` if the user asked for it) for shortly after the next batch of this channel's posts will have gone out. Typically the day after the last scheduled post, at midday, so capacity has freed up. Write its message so it says to run `/draft` again for those channels and to report what was scheduled. Tell the user when it's set for.
9. **Report.** Give one table per day: channel → clip number/title → time. Then list what's still in drafts and why (cap reached, YouTube 2/day), and when the follow-up runs. Keep it short.

## Notes
- Never create new posts or change captions here. This command only moves existing drafts. If the user wants caption edits, do them as a separate, explicit step.
- Drafts don't count toward the cap. Scheduled posts do.
- Buffer's API rate limit is about 150 calls per 15 minutes, shared across all calls. That's plenty for a few dozen edits. If a response shows `remaining` near 0, wait for `resetSeconds`.
