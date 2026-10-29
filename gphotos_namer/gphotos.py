#!/usr/bin/env python3
"""Download a shared Google Photos video, extract frames to review, rename by content.

Usage:
  gphotos.py download <share-url> [-o DIR]    -> prints path of downloaded video
  gphotos.py frames <video> [-n 8] [-o DIR]   -> prints paths of extracted frame JPEGs
  gphotos.py rename <video> "<new title>"     -> renames file, keeping extension
"""
import argparse
import html
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    return urllib.request.urlopen(req, timeout=60)


def find_video_url(page):
    # The share page exposes a thumbnail on lh3.googleusercontent.com; "=dv" on the
    # same base URL serves the original video stream.
    m = re.search(r'<meta property="og:image" content="([^"]+)"', page)
    if m:
        base = html.unescape(m.group(1)).split("=")[0]
    else:
        m = re.search(r'https://lh3\.googleusercontent\.com/pw/[\w\-]+', page)
        if not m:
            sys.exit("Could not find media URL on the share page (is the link public?)")
        base = m.group(0)
    return base + "=dv"


def cmd_download(a):
    resp = fetch(a.url)
    page = resp.read().decode("utf-8", "replace")
    title = re.search(r'<meta property="og:title" content="([^"]*)"', page)
    name = re.sub(r'[\\/:*?"<>|]', "_", html.unescape(title.group(1))).strip() if title else ""
    name = name if name and name.lower() != "google photos" else "video"
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / (name if Path(name).suffix else name + ".mp4")
    with fetch(find_video_url(page)) as r, open(dest, "wb") as f:
        ctype = r.headers.get("Content-Type", "")
        if not ctype.startswith("video/"):
            sys.exit(f"Expected a video, got {ctype!r}. The item may not be a video or not public.")
        while chunk := r.read(1 << 20):
            f.write(chunk)
    print(dest)


def duration(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(video)], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def cmd_frames(a):
    video = Path(a.video)
    out = Path(a.out or video.with_suffix("").as_posix() + "_frames")
    out.mkdir(parents=True, exist_ok=True)
    dur = duration(video)
    for i in range(a.n):
        t = dur * (i + 0.5) / a.n
        dest = out / f"frame_{i:02d}.jpg"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video),
                        "-frames:v", "1", "-vf", "scale=768:-2", str(dest)], check=True)
        print(dest)


def cmd_rename(a):
    video = Path(a.video)
    safe = re.sub(r'[\\/:*?"<>|]', "", a.title).strip()
    if not safe:
        sys.exit("Empty title")
    dest = video.with_name(safe + video.suffix)
    if dest.exists():
        sys.exit(f"{dest} already exists")
    video.rename(dest)
    print(dest)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest="cmd", required=True)
    d = s.add_parser("download"); d.add_argument("url"); d.add_argument("-o", "--out", default="downloads"); d.set_defaults(f=cmd_download)
    f = s.add_parser("frames"); f.add_argument("video"); f.add_argument("-n", type=int, default=8); f.add_argument("-o", "--out"); f.set_defaults(f=cmd_frames)
    r = s.add_parser("rename"); r.add_argument("video"); r.add_argument("title"); r.set_defaults(f=cmd_rename)
    a = p.parse_args()
    a.f(a)


if __name__ == "__main__":
    main()
