"""FLUX.1 schnell (Cloudflare Workers AI) -> one picture per scene, composed into a 1080x1920 frame."""
import base64
import io
import time

import requests
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

import characters as cast
import config

MODEL = "@cf/black-forest-labs/flux-1-schnell"
URL = "https://api.cloudflare.com/client/v4/accounts/{acc}/ai/run/" + MODEL


class CloudflareAuthError(RuntimeError):
    pass


# ------------------------------------------------------------------ prompt building
def build_prompt(scene, attire, location, safe=False):
    """action first (FLUX reads the start of the prompt most closely), then the fixed look of each character."""
    looks = "; ".join(cast.describe(k, attire) for k in scene.get("characters", []))
    parts = [] if safe else [scene.get("image_prompt", "").rstrip(". ")]
    parts += [looks, f"Setting: {location}" if location else "", cast.ART_STYLE]
    prompt = ". ".join(p for p in parts if p)
    return prompt[:1400]


# ------------------------------------------------------------------ composition
def _fade_mask(size, fade):
    w, h = size
    mask = Image.new("L", size, 255)
    px = mask.load()
    for y in range(fade):
        v = int(255 * y / fade)
        for x in range(w):
            px[x, y] = v
            px[x, h - 1 - y] = v
    return mask


def compose(img):
    """Square FLUX picture -> 9:16 frame: blurred, darkened copy as backdrop + the sharp picture with soft edges."""
    W, H = config.WIDTH, config.HEIGHT
    img = ImageEnhance.Color(img.convert("RGB")).enhance(1.08)
    # backdrop
    s = max(W / img.width, H / img.height)
    bg = img.resize((int(img.width * s) + 1, int(img.height * s) + 1), Image.LANCZOS)
    l, t = (bg.width - W) // 2, (bg.height - H) // 2
    bg = bg.crop((l, t, l + W, t + H)).filter(ImageFilter.GaussianBlur(34))
    bg = ImageEnhance.Brightness(bg).enhance(0.45)
    # foreground: scale to FOREGROUND_H tall, centre-crop to the frame width (loses ~5% each side)
    fh = config.FOREGROUND_H
    scale = fh / img.height
    fw = int(img.width * scale)
    fg = img.resize((fw, fh), Image.LANCZOS)
    if fw > W:
        l = (fw - W) // 2
        fg = fg.crop((l, 0, l + W, fh))
    elif fw < W:
        fg = fg.resize((W, int(fh * W / fw)), Image.LANCZOS)
    bg.paste(fg, ((W - fg.width) // 2, config.FOREGROUND_TOP), _fade_mask(fg.size, 36))
    return bg


def compose_portrait(path=config.PORTRAIT):
    """The Rama portrait is already 9:16: fill the frame and darken the bottom so captions stay readable."""
    img = ImageOps.fit(Image.open(path).convert("RGB"), (config.WIDTH, config.HEIGHT), Image.LANCZOS)
    shade = Image.new("L", img.size, 0)
    px = shade.load()
    start = int(config.HEIGHT * 0.58)
    for y in range(start, config.HEIGHT):
        v = int(170 * (y - start) / (config.HEIGHT - start))
        for x in range(config.WIDTH):
            px[x, y] = v
    return Image.composite(Image.new("RGB", img.size, (0, 0, 0)), img, shade)


# ------------------------------------------------------------------ generation
def _request(prompt, seed):
    r = requests.post(URL.format(acc=config.CF_ACCOUNT_ID),
                      headers={"Authorization": f"Bearer {config.CF_API_TOKEN}"},
                      json={"prompt": prompt, "steps": 8}, timeout=180)   # NOTE: the REST API rejects "seed" (HTTP 400), so none is sent
    if r.status_code in (401, 403):
        raise CloudflareAuthError(f"Cloudflare rejected the token/account ({r.status_code}): {r.text[:300]}\n"
                                  "Check the CF_ACCOUNT_ID and CF_API_TOKEN secrets (token needs Workers AI permission).")
    if r.status_code != 200:
        raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
    b64 = (r.json().get("result") or {}).get("image")
    if not b64:
        raise RuntimeError(f"no image in response: {r.text[:200]}")
    img = Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
    if min(img.size) < 512:
        raise RuntimeError(f"image too small {img.size}")
    return img


def make_image(scene, attire, location, path, seed):
    """Returns True if a fresh picture was saved. Tries the full prompt twice, then a 'safe' prompt without the action
    (in case Cloudflare's content filter rejected it), each with a new seed."""
    plan = [(False, 0), (False, 1), (True, 2), (True, 3)]
    last = "unknown"
    for n, (safe, bump) in enumerate(plan, 1):
        prompt = build_prompt(scene, attire, location, safe=safe)
        try:
            compose(_request(prompt, seed + bump * 7919)).save(path, "JPEG", quality=93)
            return True
        except CloudflareAuthError:
            raise
        except Exception as e:  # noqa: BLE001
            last = str(e)
            print(f"   image attempt {n}/{len(plan)} failed: {last[:200]}")
            time.sleep(4 * n)
    print(f"   image FAILED after retries ({last[:120]})")
    return False


def save_portrait(path):
    compose_portrait().save(path, "JPEG", quality=93)
