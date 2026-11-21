# Buffer scheduling reference

Learned on the StreamiX account (free plan). Tool names are the `mcp__Buffer__*` tools; load them with ToolSearch first.

## Limits that matter
- **10 scheduled posts per channel** (`organizations[].limits.scheduledPosts`). It's per channel, not per org: TikTok being full did not block YouTube. Error text: `Scheduled posts limit reached. You have 10 scheduled posts out of 10 allowed.`
- **YouTube: max 2 posts per day.** Error: `maximum number of posts YouTube allows in a day (2)`. Spread YouTube 2/day using that day's first two slots, in clip order.
- **Drafts do not count** toward the 10. Save overflow with `saveToDraft: true` (no mode/dueAt).
- API rate limit ~150 requests / 15 min, shared across all Buffer calls. 60–90 posts fit comfortably.

## Call shapes that worked
Common to all: `schedulingType: "automatic"`, `mode: "customScheduled"`, `dueAt: "YYYY-MM-DDTHH:MM:00+02:00"` (offset from the account timezone; never UTC by assumption; must be after `currentTime`).

TikTok:
```json
{"channelId": "...", "text": "<caption + hashtags>", "assets": [{"video": {"url": "<raw github url>"}}]}
```
Instagram (Reel):
```json
{"channelId": "...", "text": "...", "assets": [{"video": {"url": "..."}}],
 "metadata": {"instagram": {"type": "reel", "shouldShareToFeed": true}}}
```
YouTube (Short; Gaming = categoryId "20"):
```json
{"channelId": "...", "text": "<description + hashtags>", "assets": [{"video": {"url": "..."}}],
 "metadata": {"youtube": {"title": "<≤100 chars, ends #shorts>", "categoryId": "20", "privacy": "public", "madeForKids": false}}}
```
Buffer reads the video's duration from the URL on create (`durationMs` in the response). If that is missing or the call errors on the asset, the URL is not publicly fetchable.

## Ordering
`addToQueue` works for a single post, but several parallel calls race for slots. Compute the slot list yourself from `get_channel().postingSchedule` (per-day `times` in the channel timezone) and give each clip its own `dueAt`.

## Moving things later
- Reschedule: `edit_post {postId, mode: "customScheduled", dueAt}` (send only those fields).
- Draft → scheduled: `edit_post {postId, mode: "customScheduled", dueAt}` on the draft id (or `addToQueue`).
- Find posts: `list_posts {organizationId, channelIds:[...], status:["draft"|"scheduled"|"sent"|"error"], sort:[{field:"dueAt",direction:"asc"}]}`; identify clips by the `NN_` filename in `assets[].source`.

## Follow-up pattern
When drafts remain, `send_later` (initiation `human_request` if the user asked for it) at a time after enough scheduled posts have gone out. Put the channel IDs, timezone, slot list, limits and the exact steps in the message, because the future turn starts from that text.
