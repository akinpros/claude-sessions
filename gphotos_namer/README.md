# gphotos_namer

Download a shared Google Photos video, review its content, and rename it descriptively.

Workflow (with Claude in-session):
1. `python3 gphotos.py download "<share link>"`
2. `python3 gphotos.py frames downloads/<file>` — Claude views the frames
3. `python3 gphotos.py rename downloads/<file> "<title>"`

Requires `ffmpeg`/`ffprobe`. Link must be a public share link to a single video.
