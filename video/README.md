# Building the demo video

The *what* to show lives in [`demo-script.md`](demo-script.md). This is the *how*.

Synthetic voice-over plus subtitles burned into the picture, both in English. **The audio is
authoritative and gets built first**: voice-over is impossible to stretch convincingly, screen
recording is the opposite. So build the track, read the per-beat timings it produces, then record
the screen against those.

Subtitles are burned in, not only shipped as an `.srt`. A judge who hits play on a muted phone and
never touches CC still gets every word.

## Requirements

macOS (`say`), `ffmpeg`, and `ffmpeg@7` for the `subtitles` filter — brew's ffmpeg 8 has no libass,
and `build-video.sh` prefers `/opt/homebrew/opt/ffmpeg@7/bin` automatically. The voice is
**Ava (Premium)**: System Settings → Accessibility → Spoken Content → Manage Voices.

## The pipeline

```bash
./build-audio.sh                                   # out/narration.wav, captions.srt, timing.txt
./make-slides.sh                                   # out/slide.png, out/slide-close.png
# record the screen → video/raw.mov (Cmd+Shift+5, window mode, mic off)
awk 'NR==1 || ($1 != "1" && $1 != "7")' out/timing.txt > out/timing-fit.txt
./fit-to-audio.py raw.mov --beats <5 marks> --timing out/timing-fit.txt
SLIDE=out/slide.png SLIDE_DUR=$B1 OUTRO="out/slide-close.png:$B7" OUTRO_REPLACE=$B7 \
  ./build-video.sh out/raw-fitted.mov
```

- `narration.tsv` is one caption per line, so the `.srt` timings are exact by construction. Keep
  captions under ~10 words.
- `$B1` and `$B7` are the lengths of beats 1 and 7 in `out/timing.txt` — read them there rather than
  writing them down anywhere, they move with every narration edit.
- Beats 1 and 7 are slides, not footage, so the fit runs against a timing file without those two
  rows and takes one mark per remaining beat — five, starting at beat 2. That is what the `awk`
  line produces; `fit-to-audio.py` aborts if the count does not match.
- Find the marks by contact-sheeting the recording (`fps=1/12` tiled, with the timestamp drawn on
  each frame) and then probing single frames around each candidate boundary. The marks that shipped
  were `0,35,104,180,264` for a 356 s take.
- `fit-to-audio.py` reports `off by -Xs` against the full narration: that is expected, X is beat 1
  plus beat 7, the two the slides cover.
- `build-audio.sh` re-renders every clip, so a narration edit also invalidates `out/raw-fitted.mov`.
  The slides survive it.
- `fit-to-audio.py` finds the moments where the screen changes, keeps them at 1x with a readable
  dwell, and compresses the dead waiting onto the narration length. Record at a natural pace.

## Recording

Chrome incognito, 1280×800, zoom 110 % (`Cmd +` once — zoom shortcuts do not work through the
extension), no bookmarks bar. Window-mode capture records only the Chrome window, so the terminal
never appears on camera.

Nothing to reset between takes: the demo is a deterministic replay of the runs in `examples/` — no
DataHub, no API key, no model in the loop, so a take cannot die on a quota or an indexing lag. Delete
the old `raw.mov` before recording over it.

Two destinations, one tab (the tab strip is browser chrome and cannot be clicked through the
extension): the demo for beats 2–5, and the three `docs/media/datahub-*.png` served raw from GitHub
for beat 6.

## Afterwards

Under 3:00, readable muted on a phone, the Pages URL visible in the address bar. Upload **public** to
YouTube with the `.srt` attached, then paste the link into `README.md` and `SUBMISSION.md` — not
before, so no link in the repo ever points at something that does not exist yet.

What shipped: https://youtu.be/y04gl1faens — 2:33, marks `0,45,112,188,295` on a 358 s take.
