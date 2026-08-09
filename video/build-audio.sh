#!/bin/bash
# ---------------------------------------------------------------------------
# build-audio.sh — narration + subtitles, from narration.tsv
#
# MUST run on macOS: it uses `say`, which does not exist on Linux.
# Renders one WAV per caption line, concatenates them with the declared gaps,
# and writes:
#     out/narration.wav   the voice track
#     out/captions.srt    subtitles whose timings are exact by construction
#     out/timing.txt      per-beat durations, so you know what to record against
#
# Usage:  ./build-audio.sh [voice] [wpm]
#         ./build-audio.sh                 # defaults below
#         ./build-audio.sh Ava 175
#         say -v '?' | grep en_            # list the English voices you have
#
# Voice note: Samantha and Alex ship by default and sound dated. Install a
# Premium voice first — System Settings > Accessibility > Spoken Content >
# System Voice > Manage Voices — and look for "Ava (Premium)", "Zoe (Premium)"
# or "Evan (Premium)". Those are the ones that do not sound like a robot.
# ---------------------------------------------------------------------------
set -euo pipefail

VOICE="${1:-Ava (Premium)}"
WPM="${2:-172}"

cd "$(dirname "$0")"
SRC="narration.tsv"
OUT="out"
CLIPS="$OUT/clips"

command -v say >/dev/null || { echo "ERROR: 'say' not found. Run this on macOS."; exit 1; }
command -v ffmpeg >/dev/null || { echo "ERROR: ffmpeg not found. brew install ffmpeg"; exit 1; }
[ -f "$SRC" ] || { echo "ERROR: $SRC not found."; exit 1; }

if ! say -v '?' | grep -qF "$VOICE"; then
  echo "ERROR: voice '$VOICE' is not installed."
  echo "Installed English voices:"
  say -v '?' | grep en_ || true
  echo "Install a Premium voice in System Settings > Accessibility > Spoken Content."
  exit 1
fi

rm -rf "$CLIPS" "$OUT/sil"; mkdir -p "$CLIPS"
echo "voice: $VOICE   rate: $WPM wpm"
echo

# --- 1. render one clip per line -------------------------------------------
python3 - "$SRC" > "$OUT/lines.tsv" <<'PY'
import sys
rows = []
for line in open(sys.argv[1]):
    line = line.rstrip("\n")
    if not line.strip() or line.lstrip().startswith("#"):
        continue
    parts = line.split("\t")
    if parts[0].strip() == "beat":
        continue
    while len(parts) < 4:
        parts.append("")
    beat, gap, caption, speak = (p.strip() for p in parts[:4])
    rows.append((beat, gap, caption, speak or caption))
for i, (beat, gap, caption, speak) in enumerate(rows):
    print(f"{i:03d}\t{beat}\t{gap}\t{caption}\t{speak}")
PY

n=0
while IFS=$'\t' read -r idx beat gap caption speak; do
  if [ -n "$caption" ]; then
    say -v "$VOICE" -r "$WPM" -o "$CLIPS/$idx.aiff" "$speak"
    ffmpeg -loglevel error -y -i "$CLIPS/$idx.aiff" \
      -af "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05,\
areverse,silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05,areverse,\
loudnorm=I=-18:TP=-2:LRA=11" \
      -ar 48000 -ac 1 "$CLIPS/$idx.wav"
    rm -f "$CLIPS/$idx.aiff"
    n=$((n+1))
  fi
done < "$OUT/lines.tsv"
echo "rendered $n clips"

# --- 2. concatenate with gaps, and emit the SRT ------------------------------
python3 - "$OUT/lines.tsv" "$CLIPS" "$OUT" <<'PY'
import subprocess, sys, os, collections

lines_tsv, clips, out = sys.argv[1], sys.argv[2], sys.argv[3]

def dur(path):
    r = subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                        "-of","default=nw=1:nk=1", path], capture_output=True, text=True)
    return float(r.stdout.strip())

def ts(t):
    h, rem = divmod(t, 3600); m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")

t = 0.0
srt, concat, beats, idx = [], [], collections.OrderedDict(), 1

for row in open(lines_tsv):
    i, beat, gap, caption, speak = row.rstrip("\n").split("\t")
    gap = float(gap)
    if gap > 0:
        concat.append(("silence", gap)); t += gap
    if not caption:
        beats.setdefault(beat, [t, t])[1] = t
        continue
    wav = os.path.join(clips, f"{i}.wav")
    d = dur(wav)
    # a caption must stay readable even if the voice is quick
    hold = max(d, 1.6, 0.35 * len(caption.split()) + 0.9)
    srt.append(f"{idx}\n{ts(t)} --> {ts(t + hold)}\n{caption}\n"); idx += 1
    concat.append((wav, d)); t += d
    if hold > d:                       # pad so audio never outruns its caption
        concat.append(("silence", hold - d)); t += hold - d
    beats.setdefault(beat, [t, t])
    beats[beat][1] = t

# Merge runs of silence, then render each one as its own exact-length file.
# (The concat demuxer's `outpoint` rounds up to a packet boundary — about 26 ms
# a time — which over ~70 gaps drifts the captions almost two seconds late.)
merged = []
for path, d in concat:
    if path == "silence" and merged and merged[-1][0] == "silence":
        merged[-1][1] += d
    else:
        merged.append([path, d])

sil_dir = os.path.join(out, "sil"); os.makedirs(sil_dir, exist_ok=True)
with open(os.path.join(out, "concat.txt"), "w") as f:
    for n, (path, d) in enumerate(merged):
        if path == "silence":
            p = os.path.join(sil_dir, f"{n:03d}.wav")
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi",
                            "-t", f"{d:.4f}", "-i", "anullsrc=r=48000:cl=mono",
                            "-c:a", "pcm_s16le", p], check=True)
            path = p
        f.write(f"file '{os.path.abspath(path)}'\n")

open(os.path.join(out, "captions.srt"), "w").write("\n".join(srt))

with open(os.path.join(out, "timing.txt"), "w") as f:
    f.write(f"{'beat':>6}  {'starts':>8}  {'ends':>8}  {'length':>7}\n")
    prev_end = 0.0
    for b, (start, end) in beats.items():
        f.write(f"{b:>6}  {prev_end:8.1f}  {end:8.1f}  {end - prev_end:7.1f}\n")
        prev_end = end
    f.write(f"\nTOTAL {t:.1f} s  =  {int(t // 60)}:{t % 60:04.1f}\n")
    f.write("HARD CAP 3:00 — " + ("OK\n" if t < 178 else "OVER — cut order is in demo-script.md\n"))
print(open(os.path.join(out, "timing.txt")).read())
PY

# --- 3. mux it into one wav --------------------------------------------------
ffmpeg -loglevel error -y -f concat -safe 0 -i "$OUT/concat.txt" -ar 48000 -ac 1 "$OUT/narration.wav"

python3 - "$OUT/narration.wav" "$OUT/captions.srt" <<'PY'
import subprocess, sys, re
d = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                          "-of","default=nw=1:nk=1", sys.argv[1]],
                         capture_output=True, text=True).stdout)
last = re.findall(r"--> (\d\d):(\d\d):(\d\d),(\d\d\d)", open(sys.argv[2]).read())[-1]
end = int(last[0])*3600 + int(last[1])*60 + int(last[2]) + int(last[3])/1000
drift = d - end
print(f"track {d:.3f} s, last caption ends {end:.3f} s, drift {drift:+.3f} s")
if abs(drift) > 0.25:
    print("WARNING: captions and audio have drifted apart. Do not ship this.")
    sys.exit(1)
PY

echo "wrote $OUT/narration.wav"
echo "wrote $OUT/captions.srt"
echo
echo "Listen to it end to end before you record anything:"
echo "  afplay $OUT/narration.wav"
