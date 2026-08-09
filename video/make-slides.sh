#!/bin/bash
# make-slides.sh — regenerate the two stills build-video.sh uses.
set -euo pipefail
cd "$(dirname "$0")"
FF=${FF:-/opt/homebrew/opt/ffmpeg@7/bin/ffmpeg}
B="fontfile='/System/Library/Fonts/Supplemental/Arial Bold.ttf'"
H="fontfile=/System/Library/Fonts/Helvetica.ttc"
mkdir -p out
bg() { "$FF" -y -v error -f lavfi -i color=c=0x0d1620:s=1920x1080 -frames:v 1 -vf "$1" "$2"; }

bg "drawtext=${B}:text='Hindsight':fontsize=170:fontcolor=0xeef4f7:x=(w-text_w)/2:y=300,\
drawtext=${H}:text='The on-call agent for your data platform':fontsize=52:fontcolor=0x9fb3bf:x=(w-text_w)/2:y=530,\
drawtext=${H}:text='Build with DataHub - The Agent Hackathon':fontsize=34:fontcolor=0x66798a:x=(w-text_w)/2:y=630,\
drawtext=${H}:text='github.com/gmassello/hindsight':fontsize=34:fontcolor=0x3b82a0:x=(w-text_w)/2:y=780" out/slide.png

bg "drawtext=${B}:text='Hindsight':fontsize=150:fontcolor=0xeef4f7:x=(w-text_w)/2:y=280,\
drawtext=${H}:text='demo - gmassello.github.io/hindsight':fontsize=42:fontcolor=0x3b82a0:x=(w-text_w)/2:y=530,\
drawtext=${H}:text='code - github.com/gmassello/hindsight':fontsize=42:fontcolor=0x3b82a0:x=(w-text_w)/2:y=610,\
drawtext=${H}:text='skill - datahub-project/datahub-skills PR 110':fontsize=42:fontcolor=0x3b82a0:x=(w-text_w)/2:y=690,\
drawtext=${H}:text='Build with DataHub - The Agent Hackathon':fontsize=32:fontcolor=0x66798a:x=(w-text_w)/2:y=820" out/slide-close.png
echo "wrote out/slide.png slide-close.png"
