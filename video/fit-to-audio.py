#!/usr/bin/env python3
"""
fit-to-audio.py — squeeze a screen recording onto the narration, without the
mouse looking like it is on fast-forward.

build-video.sh rubber-bands the whole recording by one constant factor. That
only works when the recording is close to the audio. It is not: driving the
browser through a run spends most of the wall clock waiting — for a panel to
paint, for a page to load — and none of that waiting is worth screen time. A constant
1.9x makes every click twice as fast; what you actually want is the clicks at
normal speed and the waiting at 6x.

So: find the moments where the screen actually changes, keep those at 1x with
enough dwell to read them, and compress everything in between by whatever
factor makes the total land on the narration length.

    ./fit-to-audio.py raw.mov                     # fits to out/narration.wav
    ./fit-to-audio.py raw.mov --start 40 --end 345
    ./fit-to-audio.py raw.mov --dwell 3.0         # linger longer on each change
    ./fit-to-audio.py raw.mov --dry-run           # print the plan, render nothing

Writes out/raw-fitted.mov. Then:

    ./build-video.sh out/raw-fitted.mov

which will now find a recording the same length as the audio and leave the
speed alone.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"

SAMPLE_FPS = 4
SAMPLE_W, SAMPLE_H = 192, 108


def duration(path: Path) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(r.stdout.strip())


def activity(path: Path, start: float, end: float) -> list[float]:
    """Mean absolute frame-to-frame difference, one value per sample step."""
    cmd = [
        "ffmpeg", "-v", "error", "-ss", f"{start}", "-to", f"{end}", "-i", str(path),
        "-vf", f"fps={SAMPLE_FPS},scale={SAMPLE_W}:{SAMPLE_H},format=gray",
        "-f", "rawvideo", "-",
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    frame_bytes = SAMPLE_W * SAMPLE_H
    diffs, prev = [], None
    assert proc.stdout is not None
    while True:
        buf = proc.stdout.read(frame_bytes)
        if len(buf) < frame_bytes:
            break
        if prev is not None:
            diffs.append(sum(abs(a - b) for a, b in zip(buf, prev)) / frame_bytes)
        prev = buf
    proc.wait()
    return diffs


def keep_windows(diffs: list[float], thr: float, pre: float, dwell: float,
                 span: float) -> list[tuple[float, float]]:
    """Turn change events into merged [start, end] windows worth showing at 1x."""
    step = 1 / SAMPLE_FPS
    windows = []
    for i, d in enumerate(diffs):
        if d > thr:
            t = (i + 1) * step
            windows.append((max(0.0, t - pre), min(span, t + dwell)))
    if not windows:
        return []
    merged = [list(windows[0])]
    for a, b in windows[1:]:
        if a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return [(a, b) for a, b in merged]


def plan(keep: list[tuple[float, float]], span: float) -> list[tuple[float, float, bool]]:
    """Interleave keep windows with the gaps between them."""
    segs, cursor = [], 0.0
    for a, b in keep:
        if a > cursor:
            segs.append((cursor, a, False))
        segs.append((a, b, True))
        cursor = b
    if cursor < span:
        segs.append((cursor, span, False))
    return [s for s in segs if s[1] - s[0] > 0.05]


def dimly(s: str) -> str:
    return f"\033[2m{s}\033[0m"


def read_timing(path: Path) -> list[tuple[str, float]]:
    """(label, length) per beat, from the table build-audio.sh writes."""
    if not path.exists():
        sys.exit(f"not found: {path} — run ./build-audio.sh first")
    out = []
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) == 4 and parts[0] != "beat":
            try:
                out.append((parts[0], float(parts[3])))
            except ValueError:
                continue
    return out


def fit_chunk(diffs, cs, ce, budget, a, index):
    """Keep the interesting moments of [cs, ce] at 1x, squeeze the rest into `budget`."""
    step = 1 / SAMPLE_FPS
    lo, hi = int(cs / step), int(ce / step)
    local = diffs[lo:hi]
    dwell = a.dwell
    while True:
        keep = keep_windows(local, a.thr, a.pre, dwell, ce - cs)
        kept = sum(b - x for x, b in keep)
        gaps = (ce - cs) - kept
        room = budget - kept
        if room > 0.3 and gaps / room <= a.max_speed:
            speed = gaps / room
            break
        if dwell <= 0.6:
            # Everything is "interesting" and it still does not fit: give up on
            # dwell and speed the whole beat uniformly.
            speed = (ce - cs) / budget
            if speed > a.max_speed:
                print(f"\n  beat {index + 1} needs {speed:.1f}x — too much to hide.")
                print("  Re-trim with --start/--end, or shift that beat's mark in --beats.\n")
                return None
            return [(cs, ce, speed)], speed, 0.0, 0.0
        dwell -= 0.2

    segs = []
    for s, e, is_keep in plan(keep, ce - cs):
        segs.append((cs + s, cs + e, 1.0 if is_keep else speed))
    return segs, speed, kept, dwell


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("recording")
    p.add_argument("--audio", default=str(OUT / "narration.wav"))
    p.add_argument("--start", type=float, default=0.0)
    p.add_argument("--end", type=float, default=None)
    p.add_argument("--thr", type=float, default=0.5,
                   help="frame-difference threshold for 'something happened' (default 0.5)")
    p.add_argument("--pre", type=float, default=0.4, help="seconds kept before each change")
    p.add_argument("--dwell", type=float, default=2.2, help="seconds kept after each change")
    p.add_argument("--max-speed", type=float, default=8.0, help="cap on the gap speed-up")
    p.add_argument("--beats", default=None,
                   help="comma-separated recording timestamps where each beat starts, e.g. "
                        "'38,52,71,86,104,140,175,205,240,300'. Fits each beat to its own "
                        "slot in out/timing.txt so the narration never drifts off the picture. "
                        "Without this the total length is right but the beats slide.")
    p.add_argument("--timing", default=str(OUT / "timing.txt"))
    p.add_argument("--dry-run", action="store_true")
    a = p.parse_args()

    rec, audio = Path(a.recording), Path(a.audio)
    for f in (rec, audio):
        if not f.exists():
            sys.exit(f"not found: {f}")

    end = a.end if a.end is not None else duration(rec)
    span = end - a.start
    target = duration(audio)
    print(f"\n  recording  {span:7.1f} s  ({a.start:.1f} -> {end:.1f})")
    print(f"  narration  {target:7.1f} s")
    print(f"  need to lose {span - target:.1f} s\n")

    if span <= target:
        print("  the recording is already shorter than the audio — use build-video.sh directly.\n")
        return 0

    diffs = activity(rec, a.start, end)

    # Chunks of (recording start, recording end, audio budget). One chunk per beat
    # when --beats is given, otherwise the whole thing as a single chunk.
    if a.beats:
        marks = [float(x) - a.start for x in a.beats.split(",")]
        slots = read_timing(Path(a.timing))
        if len(marks) != len(slots):
            sys.exit(f"--beats has {len(marks)} marks but {a.timing} has {len(slots)} beats.")
        bounds = marks + [span]
        chunks = [(bounds[i], bounds[i + 1], slots[i][1]) for i in range(len(marks))]
        if marks[0] > 0.5:
            print(f"  {dimly(f'dropping the first {marks[0]:.1f} s before beat 1')}")
        print(f"  fitting {len(chunks)} beats individually — narration stays locked\n")
    else:
        chunks = [(0.0, span, target)]
        print("  no --beats: fitting as one block. Total length will be right, but the\n"
              "  narration will drift against the picture. Pass --beats to lock them.\n")

    segs, speeds = [], []
    for ci, (cs, ce, budget) in enumerate(chunks):
        got = fit_chunk(diffs, cs, ce, budget, a, ci)
        if got is None:
            return 1
        chunk_segs, speed, kept, dwell = got
        segs += chunk_segs
        speeds.append(speed)
        if a.beats:
            print(f"    beat {ci + 1:>2}  {ce - cs:6.1f}s -> {budget:5.1f}s   "
                  f"{kept:5.1f}s at 1x, rest at {speed:.1f}x"
                  + (f"  (dwell {dwell:.1f})" if abs(dwell - a.dwell) > 1e-9 else ""))
    print()

    parts, labels = [], []
    for i, (s, e, sp) in enumerate(segs):
        pts = "PTS-STARTPTS" if sp == 1.0 else f"(PTS-STARTPTS)/{sp:.6f}"
        parts.append(f"[0:v]trim={s:.3f}:{e:.3f},setpts={pts}[v{i}]")
        labels.append(f"[v{i}]")
    graph = ";".join(parts) + ";" + "".join(labels) + f"concat=n={len(segs)}:v=1:a=0[out]"

    if a.dry_run:
        for s, e, sp in segs[:16]:
            print(f"    {s:7.1f} -> {e:7.1f}  {'keep' if sp == 1.0 else f'{sp:.1f}x'}")
        if len(segs) > 16:
            print(f"    ... {len(segs) - 16} more ({len(segs)} segments total)")
        print()
        return 0

    OUT.mkdir(exist_ok=True)
    script = OUT / "_fit.filter"
    script.write_text(graph)
    dest = OUT / "raw-fitted.mov"
    print(f"  rendering {dest} ...")
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-stats", "-ss", str(a.start), "-to", str(end),
         "-i", str(rec), "-filter_complex_script", str(script),
         "-map", "[out]", "-an", "-c:v", "libx264", "-preset", "veryfast",
         "-crf", "16", "-pix_fmt", "yuv420p", str(dest)],
        check=True,
    )
    got = duration(dest)
    print(f"\n  {dest.name}  {got:.1f} s  (audio {target:.1f} s, off by {got - target:+.1f} s)")
    print(f"\n  next:  ./build-video.sh {dest}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
