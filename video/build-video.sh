#!/bin/bash
# ---------------------------------------------------------------------------
# build-video.sh — assemble the deliverable
#
# Takes the raw muted screen recording, the narration track and the SRT, and
# produces out/hindsight-demo.mp4: 1920x1080, voice mixed, subtitles burned in.
#
# Run build-audio.sh FIRST. The audio is authoritative; the video is fitted to
# it.
#
#   ./build-video.sh raw.mov
#   START=3.5 ./build-video.sh raw.mov          # drop the first 3.5 s
#   START=3.5 END=152 ./build-video.sh raw.mov  # and cut at 2:32
#   BED=bed.m4a ./build-video.sh raw.mov        # add a music bed under the voice
#
# Env knobs:
#   START, END   trim the recording, in seconds (END is absolute, not duration)
#   BED          background music file, mixed at 6 %
#   FONTSIZE     subtitle size, default 14. These are ASS script units, not
#                pixels: libass renders an SRT on a 384x288 canvas and scales
#                it up, so 14 lands at roughly 52 px tall on the 1080p output.
#                12 is discreet, 16 is shouting. 14 fits every caption on one
#                line and is legible on a phone.
#   NOFIT=1      do not rubber-band the video speed to match the audio
# ---------------------------------------------------------------------------
set -euo pipefail

# The default homebrew ffmpeg 8 bottle ships without libass, so it has no
# subtitles filter; the ffmpeg@7 keg does. Prefer it when present.
[ -d /opt/homebrew/opt/ffmpeg@7/bin ] && PATH="/opt/homebrew/opt/ffmpeg@7/bin:$PATH"

RAW="${1:-raw.mov}"
cd "$(dirname "$0")"
OUT="out"
SRT="$OUT/captions.srt"
VOICE="$OUT/narration.wav"
FINAL="$OUT/hindsight-demo.mp4"
FONTSIZE="${FONTSIZE:-14}"

[ -f "$RAW"   ] || { echo "ERROR: recording '$RAW' not found."; exit 1; }
[ -f "$VOICE" ] || { echo "ERROR: $VOICE not found. Run ./build-audio.sh first."; exit 1; }
[ -f "$SRT"   ] || { echo "ERROR: $SRT not found. Run ./build-audio.sh first."; exit 1; }

probe() { ffprobe -v error -show_entries format=duration -of default=nw=1:nk=1 "$1"; }

A=$(probe "$VOICE")
START="${START:-0}"
END="${END:-$(probe "$RAW")}"
V=$(python3 -c "print(max(0.001, $END - $START))")

# --- optional title slide over the first beat --------------------------------
# SLIDE=out/slide.png shows a still for the first SLIDE_DUR seconds — the
# length of beat 1 in out/timing.txt — and the recording covers the rest.
# Pair it with a fit that skipped beat 1 (fit-to-audio --timing without it).
SLIDE="${SLIDE:-}"
if [ -n "$SLIDE" ]; then
  [ -f "$SLIDE" ] || { echo "ERROR: SLIDE '$SLIDE' not found."; exit 1; }
  SLIDE_DUR="${SLIDE_DUR:?set it to the length of beat 1, from out/timing.txt}"
fi
SLIDE_DUR="${SLIDE_DUR:-0}"

# --- optional outro slides ----------------------------------------------------
# OUTRO="img:dur,img:dur,..." appends stills after the recording. The first
# OUTRO_REPLACE seconds of them cover the tail of the narration (use it to put
# tech slides over the closing beat); anything beyond extends the video with
# padded silence. Trim the recording accordingly with END=.
OUTRO="${OUTRO:-}"
OUTRO_REPLACE="${OUTRO_REPLACE:-0}"

# --- fit the video to the audio ---------------------------------------------
SLIDE_PART=$([ -n "$SLIDE" ] && echo "$SLIDE_DUR" || echo 0)
RATIO=$(python3 -c "print(f'{$V/($A-$SLIDE_PART-$OUTRO_REPLACE):.6f}')")
if [ "${NOFIT:-0}" = "1" ]; then
  RATIO=1.0
  echo "NOFIT=1 — leaving the video speed alone"
else
  python3 - "$RATIO" <<'PY'
import sys
r = float(sys.argv[1])
if not 0.75 <= r <= 1.30:
    print(f"\nERROR: the recording is {r:.2f}x the length of the narration.")
    print("That is too far off to hide with a speed change. Re-record, or trim")
    print("with START= / END=, or pass NOFIT=1 and fix it by hand.\n")
    sys.exit(1)
print(f"fitting video at {r:.3f}x (imperceptible on a screencast)")
PY
fi

printf 'narration %.1f s   recording %.1f s   output %.1f s\n' "$A" "$V" "$A"
python3 - "$A" <<'PY'
import sys
t = float(sys.argv[1])
print(f"final length {int(t//60)}:{t%60:04.1f}", "— OK" if t < 179 else "— OVER 3:00, CUT SOMETHING")
PY

# --- audio: voice, optionally over a bed -------------------------------------
if [ -n "${BED:-}" ] && [ -f "$BED" ]; then
  echo "mixing music bed: $BED"
  ffmpeg -loglevel error -y -i "$VOICE" -stream_loop -1 -i "$BED" \
    -filter_complex "[1:a]volume=0.06,afade=t=in:st=0:d=2,afade=t=out:st=$(python3 -c "print($A-3)"):d=3[bed];\
[0:a][bed]amix=inputs=2:duration=first:dropout_transition=0,loudnorm=I=-16:TP=-1.5:LRA=11[a]" \
    -map "[a]" -ar 48000 -ac 2 "$OUT/mixed.wav"
  TRACK="$OUT/mixed.wav"
else
  TRACK="$VOICE"
fi

# --- video: trim, fit, scale to 1080p, burn the subtitles --------------------
# The newer ffmpeg filtergraph parser chokes on nested quotes: protect the
# commas inside force_style with backslashes instead, and use a font name
# without spaces.
STYLE="FontName=Helvetica,Fontsize=${FONTSIZE},Bold=1,PrimaryColour=&H00FFFFFF,\
BorderStyle=4,BackColour=&H33000000,Outline=0,Shadow=0,Alignment=2,MarginV=22"
STYLE_ESC=${STYLE//,/\\,}

FIT="scale=1920:1080:force_original_aspect_ratio=decrease,\
pad=1920:1080:(ow-iw)/2:(oh-ih)/2:color=black,setsar=1"

INPUTS=(-ss "$START" -to "$END" -i "$RAW" -i "$TRACK")
IDX=2 N=0 PRE="" CHAIN="" OUTRO_TOTAL=0

if [ -n "$SLIDE" ]; then
  INPUTS+=(-loop 1 -t "$SLIDE_DUR" -i "$SLIDE")
  PRE+="[${IDX}:v]${FIT},fps=30[sl];"
  CHAIN+="[sl]"; N=$((N+1)); IDX=$((IDX+1))
fi

PRE+="[0:v]setpts=PTS/${RATIO},fps=30,${FIT}[rec];"
CHAIN+="[rec]"; N=$((N+1))

if [ -n "$OUTRO" ]; then
  i=0
  for spec in ${OUTRO//,/ }; do
    IMG="${spec%%:*}"; DUR="${spec##*:}"
    [ -f "$IMG" ] || { echo "ERROR: OUTRO image '$IMG' not found."; exit 1; }
    INPUTS+=(-loop 1 -t "$DUR" -i "$IMG")
    PRE+="[${IDX}:v]${FIT},fps=30[o${i}];"
    CHAIN+="[o${i}]"; N=$((N+1)); IDX=$((IDX+1)); i=$((i+1))
    OUTRO_TOTAL=$(python3 -c "print($OUTRO_TOTAL + $DUR)")
  done
fi

TOTAL=$(python3 -c "print($A + max(0.0, $OUTRO_TOTAL - $OUTRO_REPLACE))")
printf 'output runs %.1f s including the outro\n' "$TOTAL"

ffmpeg -y "${INPUTS[@]}" \
  -filter_complex "${PRE}${CHAIN}concat=n=${N}:v=1:a=0,\
subtitles=filename=${SRT}:force_style=${STYLE_ESC}[v];[1:a]apad[a]" \
  -map "[v]" -map "[a]" -t "$TOTAL" \
  -c:v libx264 -preset medium -crf 20 -pix_fmt yuv420p -movflags +faststart \
  -c:a aac -b:a 192k \
  "$FINAL"

cp "$SRT" "$OUT/hindsight-demo.en.srt"
echo
echo "wrote $FINAL"
echo "wrote $OUT/hindsight-demo.en.srt   (upload this as the YouTube caption track too)"
ffprobe -v error -show_entries format=duration:stream=width,height -of default=nw=1 "$FINAL"
