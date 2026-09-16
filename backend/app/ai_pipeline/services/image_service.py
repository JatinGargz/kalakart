"""
Stage 4: AI image enhancement

Background removal via rembg (U^2-Net, runs locally, free) and lighting/
crop/resize via OpenCV. No paid vision API needed. Also fully offline-
capable after the rembg model weights are downloaded once.

Features:
1. Smart crop -- finds the actual product's bounding box (via alpha
   channel), then adds consistent padding, instead of centering the whole
   original frame.
2. Auto-straighten -- detects if the product is tilted (via the alpha
   mask's minimum-area bounding rectangle) and rotates it level before
   compositing, so crooked phone photos come out straight.
3. Auto-contrast background selection -- computes the product's average
   color and picks whichever background color (from BACKGROUND_COLORS)
   contrasts with it best, so light/white products don't disappear into a
   white background. An explicit background choice always overrides this.
4. Soft drop shadow -- a blurred ellipse beneath the product so it reads
   as a studio shot, not a flat cutout.
5. Sharpening -- a mild unsharp-mask pass so texture reads clearly.
6. Subtle vignette -- a barely-there edge darkening so the eye is drawn to
   the product, a common real product-photography finishing touch.
"""

import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from rembg import remove

from app.schemas.models import EnhancedImage

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "static", "enhanced_images"))
TARGET_SIZE = (1024, 1024)  # standard e-commerce square format
PADDING_RATIO = 0.14  # 14% breathing room around the product on each side

BACKGROUND_COLORS = {
    "white": (255, 255, 255),
    "light_gray": (240, 240, 240),
    "soft_beige": (245, 238, 224),
    "pastel_blue": (232, 240, 247),
}
DEFAULT_BACKGROUND = "auto"  # "auto" triggers contrast-based selection; any key above is respected as-is


def _correct_lighting(image: np.ndarray) -> np.ndarray:
    """CLAHE-based auto lighting correction -- handles dim/uneven phone-camera
    photos taken indoors without special equipment."""
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_channel = clahe.apply(l_channel)
    merged = cv2.merge((l_channel, a_channel, b_channel))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2BGR)


def _sharpen(image: np.ndarray) -> np.ndarray:
    """Mild unsharp mask -- subtle by design, too strong looks artificial."""
    blurred = cv2.GaussianBlur(image, (0, 0), sigmaX=3)
    return cv2.addWeighted(image, 1.5, blurred, -0.5, 0)


def _apply_vignette(image: np.ndarray, strength: float = 0.15) -> np.ndarray:
    """Very subtle radial darkening toward the edges -- draws the eye to the
    product without looking like an obvious filter. `strength` of 0.15 means
    corners darken by at most 15%, center is untouched."""
    h, w = image.shape[:2]
    y, x = np.ogrid[:h, :w]
    cx, cy = w / 2, h / 2
    max_dist = np.sqrt(cx**2 + cy**2)
    dist = np.sqrt((x - cx) ** 2 + (y - cy) ** 2) / max_dist  # 0 at center, 1 at corners
    mask = 1 - strength * (dist**2)
    mask = np.clip(mask, 1 - strength, 1.0)
    return (image.astype(np.float32) * mask[..., None]).clip(0, 255).astype(np.uint8)


def _get_content_bbox(rgba_image: Image.Image) -> tuple[int, int, int, int]:
    """Bounding box of the actual product using the alpha channel."""
    alpha = np.array(rgba_image.split()[-1])
    ys, xs = np.where(alpha > 10)
    if len(xs) == 0 or len(ys) == 0:
        return 0, 0, rgba_image.width, rgba_image.height
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())


def _straighten(rgba_image: Image.Image) -> Image.Image:
    """
    Detects if the product is tilted using the minimum-area bounding
    rectangle of its alpha mask, and rotates it level. Phone photos are
    often a few degrees off since people rarely hold the camera perfectly
    straight -- this fixes that before the product gets cropped/placed.
    """
    alpha = np.array(rgba_image.split()[-1])
    mask = (alpha > 10).astype(np.uint8) * 255
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return rgba_image

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < 100:  # too small to reliably estimate an angle
        return rgba_image

    rect = cv2.minAreaRect(largest)
    angle = rect[-1]

    # cv2.minAreaRect angle convention varies by OpenCV version; normalize
    # to a small rotation in [-45, 45] so we straighten rather than flip
    # the product onto its side.
    if angle < -45:
        angle = 90 + angle
    if angle > 45:
        angle = angle - 90

    # Skip rotation for negligible tilt -- avoids introducing blur/artifacts
    # on already-straight photos due to unnecessary resampling.
    if abs(angle) < 1.5:
        return rgba_image

    return rgba_image.rotate(-angle, resample=Image.BICUBIC, expand=True, fillcolor=(0, 0, 0, 0))


def _select_auto_background(product_rgba: Image.Image) -> str:
    """
    Picks whichever background color contrasts best with the product's
    average color, so light/white products don't blend into a white
    background. Falls back to 'white' if the product region is empty.
    """
    rgb = np.array(product_rgba.convert("RGB"))
    alpha = np.array(product_rgba.split()[-1])
    mask = alpha > 10
    if not mask.any():
        return "white"

    avg_color = rgb[mask].mean(axis=0)  # [R, G, B]

    best_key = "white"
    best_distance = -1.0
    for key, color in BACKGROUND_COLORS.items():
        distance = float(np.linalg.norm(avg_color - np.array(color)))
        if distance > best_distance:
            best_distance = distance
            best_key = key
    return best_key


def _add_drop_shadow(canvas: Image.Image, product_rgba: Image.Image, paste_pos: tuple[int, int]) -> None:
    """Soft blurred elliptical shadow beneath the product, drawn onto canvas
    BEFORE the product is pasted on top."""
    px, py = paste_pos
    shadow_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    shadow_alpha = np.array(product_rgba.split()[-1])
    ys, xs = np.where(shadow_alpha > 10)
    if len(xs) == 0:
        return

    shadow_w = int((xs.max() - xs.min()) * 0.8)
    shadow_h = max(int(shadow_w * 0.18), 10)
    shadow_cx = px + (xs.min() + xs.max()) // 2
    shadow_cy = py + ys.max() - int(shadow_h * 0.3)

    draw = ImageDraw.Draw(shadow_layer)
    draw.ellipse(
        [shadow_cx - shadow_w // 2, shadow_cy - shadow_h // 2, shadow_cx + shadow_w // 2, shadow_cy + shadow_h // 2],
        fill=(0, 0, 0, 90),
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=max(shadow_w * 0.06, 1)))
    canvas.alpha_composite(shadow_layer)


def enhance_image(input_path: str, background: str = DEFAULT_BACKGROUND) -> EnhancedImage:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filename = os.path.basename(input_path)

    # Background removal (rembg works directly on PIL images)
    with Image.open(input_path) as img:
        no_bg = remove(img.convert("RGBA"))  # RGBA with transparent background

    # --- Auto-straighten before cropping, so the crop box fits the level product ---
    no_bg = _straighten(no_bg)

    # --- Smart crop: find the actual product, not the whole frame ---
    x0, y0, x1, y1 = _get_content_bbox(no_bg)
    product = no_bg.crop((x0, y0, x1 + 1, y1 + 1))

    # --- Resolve background color: explicit choice wins, else auto-contrast ---
    if background == "auto" or background not in BACKGROUND_COLORS:
        resolved_key = _select_auto_background(product)
    else:
        resolved_key = background
    bg_color = BACKGROUND_COLORS[resolved_key]

    # --- Scale product to fit target canvas with consistent padding ---
    pad = int(min(TARGET_SIZE) * PADDING_RATIO)
    max_product_w = TARGET_SIZE[0] - 2 * pad
    max_product_h = TARGET_SIZE[1] - 2 * pad
    scale = min(max_product_w / product.width, max_product_h / product.height)
    new_size = (max(1, int(product.width * scale)), max(1, int(product.height * scale)))
    product = product.resize(new_size, Image.LANCZOS)

    # --- Build the background canvas ---
    canvas = Image.new("RGBA", TARGET_SIZE, (*bg_color, 255))
    paste_x = (TARGET_SIZE[0] - product.width) // 2
    paste_y = (TARGET_SIZE[1] - product.height) // 2

    # --- Drop shadow, drawn onto canvas BEFORE the product is pasted on top ---
    _add_drop_shadow(canvas, product, (paste_x, paste_y))

    # --- Paste the product using its own alpha as the mask ---
    canvas.paste(product, (paste_x, paste_y), product)
    composited = canvas.convert("RGB")

    # --- Lighting + sharpening via OpenCV ---
    cv_image = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2BGR)
    lit = _correct_lighting(cv_image)
    sharpened = _sharpen(lit)
    finished = _apply_vignette(sharpened)

    output_path = os.path.join(OUTPUT_DIR, f"enhanced_{filename}")
    cv2.imwrite(output_path, finished)

    return EnhancedImage(
        original_filename=filename,
        enhanced_image_path=output_path,
        background_removed=True,
        lighting_corrected=True,
        background_color=resolved_key,
        dimensions=f"{TARGET_SIZE[0]}x{TARGET_SIZE[1]}",
    )
