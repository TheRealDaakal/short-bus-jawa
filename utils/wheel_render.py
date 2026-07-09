"""
Procedurally draws the operations wheel face - one pie slice per SWTOR
operation, each showing that operation's existing banner art (which
already has the operation's title baked in). Built in code rather than
generated as one flat image so it can't go stale or get garbled text
when the operations list changes - just re-run this module.
"""

import math

from PIL import Image, ImageDraw, ImageFont

from utils.swtor_content import all_operations
from utils.banners import get_banner_path

WHEEL_SIZE = 900
CENTER = WHEEL_SIZE // 2
OUTER_RADIUS = WHEEL_SIZE // 2 - 10

FONT_PATH = r"C:\Windows\Fonts\arialbd.ttf"

# Dark tinted fill per slice, cycled if there are more operations than colors.
_SLICE_COLORS = [
    (10, 40, 60), (30, 15, 50), (55, 25, 10), (10, 40, 20),
    (10, 15, 55), (45, 10, 15), (35, 10, 45), (25, 10, 45),
    (15, 35, 15), (10, 30, 45), (35, 30, 10), (45, 30, 10),
]


def _fit_crop(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    src_ratio = img.width / img.height
    target_ratio = target_w / target_h

    if src_ratio > target_ratio:
        new_h = img.height
        new_w = int(new_h * target_ratio)
        x0 = (img.width - new_w) // 2
        img = img.crop((x0, 0, x0 + new_w, new_h))
    else:
        new_w = img.width
        new_h = int(new_w / target_ratio)
        y0 = (img.height - new_h) // 2
        img = img.crop((0, y0, new_w, y0 + new_h))

    return img.resize((target_w, target_h), Image.LANCZOS)


def _build_thumbnail_layer(operation: str, thumb_w: int, thumb_h: int) -> Image.Image:
    pad = 6
    layer = Image.new("RGBA", (thumb_w + pad * 2, thumb_h + pad * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)

    banner_path = get_banner_path(operation)
    if banner_path:
        thumb = Image.open(banner_path).convert("RGBA")
        thumb = _fit_crop(thumb, thumb_w, thumb_h)
        layer.paste(thumb, (pad, pad), thumb)
    else:
        # No banner art yet for this operation - fall back to a plain
        # text label instead of leaving an empty box on the wheel.
        try:
            font = ImageFont.truetype(FONT_PATH, 16)
        except OSError:
            font = ImageFont.load_default()

        words = operation.upper().split()
        lines, current = [], ""
        for word in words:
            test = (current + " " + word).strip()
            bbox = draw.textbbox((0, 0), test, font=font)
            if bbox[2] - bbox[0] <= thumb_w - 10 or not current:
                current = test
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)

        total_h = len(lines) * 20
        ty = pad + (thumb_h - total_h) // 2
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            tx = pad + (thumb_w - tw) // 2
            draw.text((tx, ty), line, font=font, fill=(255, 255, 255, 255))
            ty += 20

    draw.rectangle([pad, pad, pad + thumb_w, pad + thumb_h], outline=(120, 200, 255, 255), width=2)

    return layer


def _paste_rotated(canvas: Image.Image, layer: Image.Image, angle_deg: float, rotation: float, radius: float):
    angle_rad = math.radians(angle_deg)
    px = CENTER + radius * math.cos(angle_rad)
    py = CENTER + radius * math.sin(angle_rad)

    rotated = layer.rotate(rotation, expand=True, resample=Image.BICUBIC)
    paste_x = int(px - rotated.width / 2)
    paste_y = int(py - rotated.height / 2)
    canvas.alpha_composite(rotated, (paste_x, paste_y))


def build_wheel_face() -> Image.Image:
    operations = all_operations()
    count = len(operations)
    slice_angle = 360 / count

    canvas = Image.new("RGBA", (WHEEL_SIZE, WHEEL_SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(canvas)

    bbox = [
        CENTER - OUTER_RADIUS, CENTER - OUTER_RADIUS,
        CENTER + OUTER_RADIUS, CENTER + OUTER_RADIUS,
    ]

    for i in range(count):
        start = -90 + i * slice_angle
        end = start + slice_angle
        color = _SLICE_COLORS[i % len(_SLICE_COLORS)]
        draw.pieslice(bbox, start, end, fill=(*color, 235))

    for i in range(count):
        angle_rad = math.radians(-90 + i * slice_angle)
        x = CENTER + OUTER_RADIUS * math.cos(angle_rad)
        y = CENTER + OUTER_RADIUS * math.sin(angle_rad)
        draw.line([(CENTER, CENTER), (x, y)], fill=(80, 180, 255, 120), width=6)
        draw.line([(CENTER, CENTER), (x, y)], fill=(160, 220, 255, 220), width=2)

    draw.ellipse(bbox, outline=(120, 200, 255, 255), width=4)

    for i, operation in enumerate(operations):
        center_angle_deg = -90 + (i + 0.5) * slice_angle
        rotation = -(center_angle_deg + 90)

        # Banner art already has the operation's title baked in, so there's
        # no separate text label to place - just the thumbnail itself.
        thumbnail = _build_thumbnail_layer(operation, thumb_w=145, thumb_h=76)
        _paste_rotated(canvas, thumbnail, center_angle_deg, rotation, radius=OUTER_RADIUS * 0.63)

    return canvas


if __name__ == "__main__":
    build_wheel_face().save("assets/wheel/wheel_face.png")
    print("saved assets/wheel/wheel_face.png")
