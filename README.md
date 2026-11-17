# testnidenaikagoshima-assets

Images and the daily posting queue for Instagram @testnidenaikagoshima.

- `img/` — post images (`YYYYMMDD_1.jpg` close-up, `_2.jpg` full page)
- `queue.json` — one entry per post: date (JST), images, caption
- `posted.json` — ids already published
- `.github/workflows/instagram.yml` — runs daily at 18:41 JST and posts every due item

Setup: add the repository secret `IG_TOKEN` (Instagram API with Instagram Login, long-lived token).
