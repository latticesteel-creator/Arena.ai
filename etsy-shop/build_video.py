#!/usr/bin/env python3
"""Build Etsy listing videos (MP4) from the listing images.
Ken Burns zoom/pan + crossfades, rendered with a piped ffmpeg.
Outputs: 1080x1080 (Etsy square) and 1080x1920 (Reels / Pinterest vertical).
"""
import os, subprocess
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import imageio_ffmpeg

ROOT = "/home/user/Arena.ai/etsy-shop"
LIST = f"{ROOT}/listings"
OUT = f"{ROOT}/videos"
os.makedirs(OUT, exist_ok=True)

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FPS = 24
SCENE_DUR = 2.7      # seconds each scene is on screen
FADE = 0.35          # crossfade seconds
ZOOM_MAX = 1.075

SCENES = ["01_hero.jpg", "02_whats_inside.jpg", "03_benefits.jpg",
          "04_who_for.jpg", "05_how_it_works.jpg"]

_src = {}
def src(name):
    if name not in _src:
        _src[name] = Image.open(f"{LIST}/{name}").convert("RGB")
    return _src[name]

def ken_burns(img, t, out_size, zoom_in=True, pan=0.06):
    """t in 0..1 through the scene. Returns a rendered frame of out_size."""
    ow, oh = out_size
    z = 1.0 + (ZOOM_MAX - 1.0) * (t if zoom_in else (1 - t))
    # cover-crop base
    r = max(ow / img.width, oh / img.height) * z
    w, h = int(img.width * r), int(img.height * r)
    im = img.resize((w, h), Image.LANCZOS)
    # gentle horizontal drift
    dx = int((w - ow) * (0.5 + (t - 0.5) * pan * 2 * (1 if zoom_in else -1)))
    dy = int((h - oh) * 0.5)
    dx = max(0, min(w - ow, dx)); dy = max(0, min(h - oh, dy))
    return im.crop((dx, dy, dx + ow, dy + oh))

def frames_square(n_scenes, size=(1080, 1080)):
    scene_frames = int(SCENE_DUR * FPS)
    step = SCENE_DUR - FADE
    starts = [i * step for i in range(n_scenes)]
    total_t = starts[-1] + SCENE_DUR
    n_out = int(total_t * FPS)
    for f in range(n_out):
        t = f / FPS
        active = []
        for i, st in enumerate(starts):
            if st <= t < st + SCENE_DUR:
                local = (t - st) / SCENE_DUR
                active.append((i, local))
        if not active:
            active = [(n_scenes - 1, 0.999)]
        if len(active) == 1:
            i, local = active[0]
            yield ken_burns(src(SCENES[i]), local, size, zoom_in=(i % 2 == 0))
        else:
            (i1, l1), (i2, l2) = active[0], active[-1]
            a = ken_burns(src(SCENES[i1]), l1, size, zoom_in=(i1 % 2 == 0))
            b = ken_burns(src(SCENES[i2]), l2, size, zoom_in=(i2 % 2 == 0))
            # blend weight from crossfade progress
            k = min(1.0, max(0.0, (l2 * SCENE_DUR) / FADE))
            yield Image.blend(a, b, k)

def frames_vertical(size=(1080, 1920), blur_bg=True):
    """Square artwork centred on a soft background - safe for Reels/Pinterest."""
    ow, oh = size
    for sq in frames_square(len(SCENES), (1080, 1080)):
        if blur_bg:
            bg = sq.resize((ow, ow), Image.LANCZOS).crop((0, 0, ow, oh))
            bg = bg.resize((ow // 2, oh // 2)).filter(ImageFilter.GaussianBlur(28)).resize((ow, oh))
        else:
            bg = Image.new("RGB", size, (255, 250, 242))
        bg.paste(sq, (0, (oh - 1080) // 2))
        yield bg

def encode(gen, size, path):
    cmd = [FFMPEG, "-y", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{size[0]}x{size[1]}", "-r", str(FPS), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    n = 0
    for frame in gen:
        p.stdin.write(frame.tobytes())
        n += 1
    p.stdin.close()
    err = p.stderr.read().decode()
    p.wait()
    if p.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {err[:800]}")
    return n

if __name__ == "__main__":
    if not os.listdir(LIST):
        raise SystemExit("no listing images found")
    n = encode(frames_square(len(SCENES)), (1080, 1080), f"{OUT}/listing_video_square.mp4")
    print("square:", n, "frames ->", f"{n/FPS:.1f}s")
    n2 = encode(frames_vertical(), (1080, 1920), f"{OUT}/listing_video_vertical.mp4")
    print("vertical:", n2, "frames ->", f"{n2/FPS:.1f}s")
