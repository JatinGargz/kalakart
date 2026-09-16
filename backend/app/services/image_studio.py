import io
import os
from PIL import Image, ImageEnhance

def enhance_craft_image(image_bytes: bytes, prod_id: str, static_dir: str) -> str:
    try:
        raw = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    except Exception:
        raw = Image.new("RGBA", (800, 800), (200, 100, 50, 255))
    
    try:
        from rembg import remove
        nobg = remove(raw)
    except Exception:
        nobg = raw

    try:
        nobg = ImageEnhance.Color(nobg).enhance(1.18)
        nobg = ImageEnhance.Contrast(nobg).enhance(1.08)
    except Exception:
        pass

    canvas = Image.new("RGBA", (1080, 1080), (255, 255, 255, 255))
    nobg.thumbnail((860, 860), Image.Resampling.LANCZOS)
    x = (1080 - nobg.width) // 2
    y = (1080 - nobg.height) // 2
    canvas.paste(nobg, (x, y), nobg)
    
    # Stamp official MoSJE Authenticity & GI Tag Seal on the corner
    try:
        from PIL import ImageDraw
        draw = ImageDraw.Draw(canvas)
        draw.rounded_rectangle([560, 985, 1050, 1055], radius=16, fill=(28, 25, 23, 240), outline=(212, 175, 55, 255), width=2)
        draw.text((580, 996), "★ MoSJE CERTIFIED ETHICAL HANDCRAFT", fill=(212, 175, 55, 255))
        draw.text((580, 1022), f"ARTISAN ID: {prod_id.upper()} • PM VISHWAKARMA", fill=(245, 245, 245, 230))
    except Exception as e:
        pass

    filename = f"studio_{prod_id}.jpg"
    out_dir = os.path.join(static_dir, "studio")
    os.makedirs(out_dir, exist_ok=True)
    filepath = os.path.join(out_dir, filename)
    canvas.convert("RGB").save(filepath, format="JPEG", quality=92)
    return f"/static/studio/{filename}"
