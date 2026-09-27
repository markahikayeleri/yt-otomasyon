"""AJAN 7: Prodüksiyon. Ücretsiz araçlarla görsel + seslendirme + FFmpeg montajı."""
import asyncio
import glob
import os
import random
import subprocess
import time
import urllib.parse

import edge_tts
import requests
from PIL import Image, ImageDraw, ImageFont

FPS = 30
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def run(cmd):
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def duration(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "default=nw=1:nk=1", path])
    return float(out.strip())


# ---------- Görsel (Pollinations: ücretsiz, anahtarsız) ----------
def image(prompt, w, h, path):
    url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt[:900]) +
           f"?width={w}&height={h}&nologo=true&seed={random.randint(1, 10**6)}")
    for attempt in range(4):
        try:
            r = requests.get(url, timeout=180)
            if r.ok and r.headers.get("content-type", "").startswith("image"):
                with open(path, "wb") as f:
                    f.write(r.content)
                Image.open(path).convert("RGB").resize((w, h)).save(path, "JPEG", quality=92)
                time.sleep(3)  # ücretsiz servisi yormamak için
                return path
        except Exception:
            pass
        time.sleep(10 * (attempt + 1))
    # Yedek: servis çökerse düz renkli kare (video yine de tamamlanır)
    Image.new("RGB", (w, h), (20, 24, 40)).save(path, "JPEG")
    return path


# ---------- Seslendirme (Edge-TTS: ücretsiz) ----------
def tts(text, path, voice, rate):
    asyncio.run(edge_tts.Communicate(text, voice, rate=rate).save(path))
    return path


# ---------- Tek görselden hafif yakınlaşan klip ----------
def ken_burns(img, seconds, w, h, out):
    frames = max(1, int(seconds * FPS))
    zin = random.choice([True, False])
    z = "min(zoom+0.0007,1.12)" if zin else "if(eq(on,0),1.12,max(zoom-0.0007,1.0))"
    vf = (f"scale={w*2}:{h*2},zoompan=z='{z}':d={frames}:x='iw/2-(iw/zoom/2)':"
          f"y='ih/2-(ih/zoom/2)':s={w}x{h}:fps={FPS},format=yuv420p")
    run(["ffmpeg", "-y", "-loop", "1", "-i", img, "-vf", vf, "-frames:v", str(frames),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", out])


def concat(files, out, extra=None):
    lst = out + ".txt"
    with open(lst, "w") as f:
        f.writelines(f"file '{os.path.abspath(p)}'\n" for p in files)
    run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", lst] + (extra or ["-c", "copy"]) + [out])


def render(sections, cfg, size, workdir, out_path):
    """sections: [{'narration': str, 'images': [prompt,...]}]"""
    os.makedirs(workdir, exist_ok=True)
    w, h = size
    clips, audios = [], []
    for i, s in enumerate(sections):
        a = tts(s["narration"], f"{workdir}/a{i}.mp3", cfg["voice"], cfg["voice_rate"])
        audios.append(a)
        d = duration(a)
        per = d / len(s["images"])
        for j, p in enumerate(s["images"]):
            img = image(p, w, h, f"{workdir}/i{i}_{j}.jpg")
            c = f"{workdir}/c{i}_{j}.mp4"
            ken_burns(img, per, w, h, c)
            clips.append(c)
    concat(clips, f"{workdir}/video.mp4")
    concat(audios, f"{workdir}/voice.m4a", ["-c:a", "aac", "-b:a", "160k"])

    music = glob.glob("assets/music/*.mp3")
    if music:
        run(["ffmpeg", "-y", "-i", f"{workdir}/video.mp4", "-i", f"{workdir}/voice.m4a",
             "-stream_loop", "-1", "-i", random.choice(music), "-filter_complex",
             "[2:a]volume=0.10[m];[1:a][m]amix=inputs=2:duration=first:normalize=0[a]",
             "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-shortest", out_path])
    else:
        run(["ffmpeg", "-y", "-i", f"{workdir}/video.mp4", "-i", f"{workdir}/voice.m4a",
             "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-shortest", out_path])
    return out_path


def thumbnail(prompt, text, out):
    image(prompt, 1280, 720, out)
    im = Image.open(out).convert("RGB")
    d = ImageDraw.Draw(im)
    text = text.upper()
    size = 120
    while True:  # yazı kapağa sığana kadar küçült
        try:
            font = ImageFont.truetype(FONT, size)
        except OSError:
            font = ImageFont.load_default()
            break
        box = d.textbbox((0, 0), text, font=font)
        if box[2] <= 1140 or size <= 50:
            break
        size -= 8
    box = d.textbbox((0, 0), text, font=font)
    x, y = 60, 720 - (box[3] - box[1]) - 80
    d.rectangle([x - 25, y - 20, x + box[2] + 25, y + box[3] + 30], fill=(0, 0, 0))
    d.text((x, y), text, font=font, fill=(255, 215, 0))
    im.save(out, "JPEG", quality=92)
    return out
