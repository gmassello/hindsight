# Demo video — shot list

What is **on screen**, beat by beat. The words live in [`narration.tsv`](narration.tsv) and only
there; the measured length of each beat is printed by `./build-audio.sh` into `out/timing.txt`. How
to build and record it is in [`README.md`](README.md).

Record against **https://gmassello.github.io/hindsight/**, not localhost: the rules ask for the
project running, and a Pages URL in the address bar proves it is deployed.

## The story

The same incident, twice. The first time the agent walks the lineage from scratch and files the
postmortem *inside DataHub*; the second time it finds that postmortem and gets there in fewer calls.
Then the catalog itself, showing what it left behind. Both runs are on record in `examples/`.

## Shot list

Dwell ≈4 s wherever a beat is marked 📌.

| Beat | On screen |
|---|---|
| 1 | Slide: intro (`out/slide.png`) |
| 2 | The scenario picker on the Pages demo |
| 3 | **Cold run** — timeline painting, the resolved asset with the ambiguity it called out, 📌 blast radius, 📌 ranked hypotheses |
| 4 | 📌 The approval gate with the dry-run plan, then **Approve** through to `✓ committed via mcp` |
| 5 | **Warm run** — 📌 the memory panel with the retrieved postmortem, then the tool-call count |
| 6 | The DataHub UI, full screen: 📌 `datahub-tag.png`, 📌 `datahub-banner.png`, 📌 `datahub-postmortem.png` — served raw from GitHub so the take needs no local quickstart. This beat is what fulfils the golden rule in `SUBMISSION.md` |
| 7 | Slide: closing (`out/slide-close.png`) — demo URL, repo, the Skill PR |

Beat 6 comes **after** the warm run on purpose: the video has to end on the DataHub UI showing
something the agent wrote, with only the closing card after it.

If an edit pushes the total over 3:00 — `build-audio.sh` says so — cut beat 2 first, then trim beat
3.

## What not to overclaim

- **The demo is a replay and the page says so on screen.** Say "replayed exactly as captured", never
  "watch it investigate live". The runs are real; the browser is not calling a model.
- **Memory bought speed and cost coverage** — see [§ Honest limits](../README.md#honest-limits). The
  narration claims fewer calls, not a better investigation.
- **Do not claim every write verified.** `verify` caught an overwritten incident banner; the real
  numbers are in the `verify.txt` of each run.
