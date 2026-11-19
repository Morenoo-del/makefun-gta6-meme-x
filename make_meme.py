#!/usr/bin/env python3
"""Build meme.png for the gta6-meme-x-01 entry.

Inputs (same directory as this script):
  scene.png       - AI-generated living-room scene, no text, no ghost
  ghost-mark.png  - official make.fun press-kit mark (mark-1024.png)

Output:
  meme.png        - 1024x1024 PNG: scene on top, black caption band below,
                    the make.fun ghost cut out of the official mark and
                    seated on the couch next to the waiting gamer, holding
                    its magenta star coin.

Captions are drawn with PIL (DejaVu Sans Bold) so the spelling is exact
and the letters stay sharp when the judge shrinks the picture to 480x480.
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SIZE = 1024
BAND_TOP = 683  # scene occupies y 0..683, caption band y 683..1024
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
MAGENTA = (196, 28, 131)  # sampled from the official mark's disc


def star_points(cx, cy, r_outer, r_inner, points=5, rotation=-90):
    pts = []
    for i in range(points * 2):
        r = r_outer if i % 2 == 0 else r_inner
        angle = math.radians(rotation + i * 180 / points)
        pts.append((cx + r * math.cos(angle), cy + r * math.sin(angle)))
    return pts


def extract_ghost(mark_path):
    """Cut the white ghost (with its black outline) out of the mark.

    The mark is a magenta disc; the ghost is the only white/black content
    in it, so selecting near-white or near-black pixels isolates the ghost.
    The white star of the coin comes along too and lands back on the coin
    we redraw underneath, so the ghost keeps holding its star coin.
    """
    mark = Image.open(mark_path).convert("RGBA")
    arr = np.asarray(mark).astype(np.int16)
    rgb = arr[:, :, :3]
    white = (rgb.min(axis=2) > 200)
    black = (rgb.max(axis=2) < 70)
    mask = white | black
    # Drop the mark's thick black outer ring (a circle around the disc):
    # it is logo furniture, not part of the ghost.
    yy, xx = np.mgrid[0:mark.height, 0:mark.width]
    ring = (xx - 512) ** 2 + (yy - 512) ** 2 > 400 ** 2
    mask = mask & ~ring
    # Drop the coin's white star: it is redrawn with the coin below, so
    # the ghost keeps holding exactly one star. The star fills the coin
    # disc, so exclude the whole disc — except the ghost's round hand,
    # which overlaps the disc's lower edge and must survive.
    coin_disc = (xx - 730) ** 2 + (yy - 440) ** 2 < 108 ** 2
    hand = (xx - 655) ** 2 + (yy - 545) ** 2 < 50 ** 2
    mask = mask & ~(coin_disc & ~hand)
    alpha = np.where(mask, 255, 0).astype(np.uint8)
    alpha_img = Image.fromarray(alpha, mode="L").filter(
        ImageFilter.GaussianBlur(1.2)
    )
    ghost = Image.new("RGBA", mark.size, (0, 0, 0, 0))
    ghost.paste(mark, (0, 0), alpha_img)
    return ghost


def build_ghost_layer(mark_path, height):
    """Ghost + redrawn star coin, scaled to the target height."""
    ghost = extract_ghost(mark_path)
    # Redraw the magenta star coin under the ghost's hand, at the same
    # spot it sits in the original mark (centre ~ (730, 440), r ~ 108).
    layer = Image.new("RGBA", ghost.size, (0, 0, 0, 0))
    coin = Image.new("RGBA", ghost.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(coin)
    d.ellipse([730 - 118, 440 - 118, 730 + 118, 440 + 118],
              fill=(0, 0, 0, 255))
    d.ellipse([730 - 108, 440 - 108, 730 + 108, 440 + 108],
              fill=MAGENTA + (255,))
    d.polygon(star_points(724, 452, 95, 38), fill=(255, 255, 255, 255))
    layer = Image.alpha_composite(layer, coin)
    layer = Image.alpha_composite(layer, ghost)
    bbox = layer.getbbox()
    layer = layer.crop(bbox)
    scale = height / layer.height
    layer = layer.resize(
        (round(layer.width * scale), height), Image.LANCZOS
    )
    return layer


def fit_font(draw, text, start_size, max_width):
    size = start_size
    while size > 20:
        font = ImageFont.truetype(FONT_PATH, size)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 2
    return ImageFont.truetype(FONT_PATH, 20)


def main():
    scene = Image.open(os.path.join(HERE, "scene.png")).convert("RGB")
    scene = scene.resize((SIZE, BAND_TOP), Image.LANCZOS)

    meme = Image.new("RGB", (SIZE, SIZE), (0, 0, 0))
    meme.paste(scene, (0, 0))
    draw = ImageDraw.Draw(meme, "RGBA")

    # --- ghost seated on the couch, right of the gamer -------------------
    ghost = build_ghost_layer(os.path.join(HERE, "ghost-mark.png"), 280)
    gx, gy = 430, 250  # ghost's top-left; its base lands on the seat
    shadow = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.ellipse([gx - 10, gy + 248, gx + ghost.width + 10, gy + 288],
               fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(10))
    meme.paste(Image.alpha_composite(meme.convert("RGBA"), shadow)
               .convert("RGB"), (0, 0))
    meme.paste(ghost, (gx, gy), ghost)

    # --- top caption ------------------------------------------------------
    draw = ImageDraw.Draw(meme, "RGBA")
    top_font = fit_font(draw, "WAITED 13 YEARS FOR GTA 6", 62, SIZE - 60)
    draw.text((SIZE // 2, 30), "WAITED 13 YEARS FOR GTA 6",
              font=top_font, fill=(255, 255, 255, 255),
              stroke_width=5, stroke_fill=(0, 0, 0, 255), anchor="ma")

    # --- bottom caption band ----------------------------------------------
    draw.rectangle([0, BAND_TOP, SIZE, SIZE], fill=(0, 0, 0, 255))
    line1 = "MY AGENT GOT PAID."
    f1 = fit_font(draw, line1, 100, SIZE - 60)
    draw.text((SIZE // 2, BAND_TOP + 50), line1, font=f1,
              fill=(255, 255, 255, 255), anchor="ma")
    line2 = "winning real money on make.fun"
    f2 = fit_font(draw, line2, 46, SIZE - 60)
    draw.text((SIZE // 2, BAND_TOP + 205), line2, font=f2,
              fill=MAGENTA + (255,), anchor="ma")

    meme.save(os.path.join(HERE, "meme.png"), "PNG")
    print("wrote meme.png", meme.size)


if __name__ == "__main__":
    main()
