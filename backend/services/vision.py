"""VISION STUDIO — rembg background removal + 1080p canvas + MoSJE seal."""
import io
from PIL import Image, ImageDraw, ImageFont, ImageOps

CANVAS = 1080

import os
# rembg downloads a ~170MB u2net model on first use and hangs offline —
# so it is OPT-IN only: set SHILP_REMBG=1 to enable true AI cutout.
_USE_REMBG = os.getenv("SHILP_REMBG", "0") == "1"
try:
    if _USE_REMBG:
        from rembg import remove as rembg_remove
        HAS_REMBG = True
    else:
        raise ImportError("rembg disabled (set SHILP_REMBG=1 to enable)")
except Exception:
    HAS_REMBG = False
    rembg_remove = None


def _load_font(size: int):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def remove_background(img: Image.Image) -> tuple[Image.Image, str]:
    """Returns (rgba_image, engine_used)."""
    if HAS_REMBG:
        try:
            out = rembg_remove(img.convert("RGBA"))
            if isinstance(out, Image.Image):
                return out, "rembg-u2net"
            out_img = Image.open(io.BytesIO(bytes(out))).convert("RGBA")
            return out_img, "rembg-u2net"
        except Exception:
            pass
    return img.convert("RGBA"), "passthrough-fallback"


def build_1080_canvas(fg: Image.Image, bg_color=(255, 248, 236)) -> Image.Image:
    """Fit foreground onto 1080x1080 studio canvas, centred, with soft border."""
    canvas = Image.new("RGB", (CANVAS, CANVAS), bg_color)
    # Fit with padding (90px)
    max_side = CANVAS - 180
    fg_copy = fg.copy()
    fg_copy.thumbnail((max_side, max_side), Image.LANCZOS)
    x = (CANVAS - fg_copy.size[0]) // 2
    y = (CANVAS - fg_copy.size[1]) // 2 - 20
    if fg_copy.mode == "RGBA":
        canvas.paste(fg_copy, (x, y), fg_copy)
    else:
        canvas.paste(fg_copy, (x, y))
    draw = ImageDraw.Draw(canvas)
    # thin studio border
    draw.rounded_rectangle([8, 8, CANVAS - 8, CANVAS - 8], radius=36,
                           outline=(201, 154, 43), width=6)
    return canvas


def add_mosje_seal(canvas: Image.Image, artisan: str = "Verified Artisan",
                   craft: str = "Handmade in India") -> Image.Image:
    """Stamp a MoSJE-style authenticity seal bottom-right + top badge."""
    img = canvas.copy()
    draw = ImageDraw.Draw(img, "RGBA")
    f_small = _load_font(30)
    f_bold = _load_font(38)

    # Top-left badge: SHILP AI • Vision Studio
    draw.rounded_rectangle([36, 30, 560, 100], radius=18, fill=(109, 15, 22, 255))
    draw.text((58, 48), "❖ SHILP AI • Vision Studio 1080p", font=f_small,
              fill=(255, 233, 201))

    # Bottom seal bar
    draw.rounded_rectangle([36, CANVAS - 150, CANVAS - 36, CANVAS - 36],
                           radius=22, fill=(18, 30, 60, 235))
    draw.text((62, CANVAS - 130), "🇮🇳 MoSJE Seal of Authenticity",
              font=f_bold, fill=(245, 158, 11))
    draw.text((62, CANVAS - 82), f"{artisan} • {craft}",
              font=f_small, fill=(255, 255, 255))
    # Tricolour tick on right
    for i, col in enumerate([(255, 153, 51), (255, 255, 255), (19, 136, 8)]):
        draw.rectangle([CANVAS - 130, CANVAS - 125 + i * 26,
                        CANVAS - 60, CANVAS - 105 + i * 26], fill=col)
    return img


def process_raw_image(raw_bytes: bytes, artisan: str = "Verified Artisan",
                      craft: str = "Handmade in India") -> tuple[bytes, dict]:
    """Full pipeline: load → bg-remove → 1080 canvas → seal → JPEG bytes + meta."""
    src = Image.open(io.BytesIO(raw_bytes))
    src = ImageOps.exif_transpose(src)
    fg, engine = remove_background(src)
    canvas = build_1080_canvas(fg)
    sealed = add_mosje_seal(canvas, artisan=artisan, craft=craft)
    buf = io.BytesIO()
    sealed.save(buf, format="JPEG", quality=88)
    meta = {
        "engine": engine,
        "canvas": f"{CANVAS}x{CANVAS}",
        "seal": "MoSJE-Seal-v1",
        "has_rembg": HAS_REMBG,
    }
    return buf.getvalue(), meta
