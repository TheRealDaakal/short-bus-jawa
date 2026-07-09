"""
Renders the /raid spin wheel-spin animation as a GIF: the wheel rotates
several full turns and eases to a stop with the chosen operation's slice
under the fixed pointer at the top.
"""

import io
import random
from pathlib import Path

from PIL import Image

from utils.wheel_render import build_wheel_face
from utils.swtor_content import all_operations
from utils.easing import ease_out_quart

ASSET_DIR = Path("assets") / "wheel"
CANVAS_SIZE = 480


def _load(name: str) -> Image.Image:
    return Image.open(ASSET_DIR / name).convert("RGBA")


def _paste_centered(base: Image.Image, overlay: Image.Image, size: tuple[int, int] | None = None, y_offset: int = 0):
    if size:
        overlay = overlay.resize(size, Image.LANCZOS)

    x = (base.width - overlay.width) // 2
    y = (base.height - overlay.height) // 2 + y_offset
    base.alpha_composite(overlay, (x, y))


def landing_rotation(operation: str) -> float:
    """
    The rotation (degrees, PIL's rotate() convention) that puts the given
    operation's slice under the fixed pointer at the top of the wheel.
    """

    operations = all_operations()
    index = operations.index(operation)
    slice_angle = 360 / len(operations)

    return (index + 0.5) * slice_angle


def _build_frame(
    wheel_face: Image.Image,
    angle: float,
    holotable: Image.Image,
    emblem: Image.Image,
    pointer: Image.Image,
) -> Image.Image:
    canvas = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (5, 8, 16, 255))

    holotable_w = 435
    holotable_h = int(holotable_w * holotable.height / holotable.width)
    _paste_centered(canvas, holotable, size=(holotable_w, holotable_h))

    wheel_scaled = wheel_face.resize((390, 390), Image.LANCZOS)
    wheel_rotated = wheel_scaled.rotate(angle, resample=Image.BICUBIC, expand=False)
    _paste_centered(canvas, wheel_rotated)

    _paste_centered(canvas, emblem, size=(98, 98))
    _paste_centered(canvas, pointer, size=(51, 44), y_offset=-193)

    return canvas


def build_spin_frames(operation: str, num_frames: int = 28) -> list[Image.Image]:
    wheel_face = build_wheel_face()
    holotable = _load("holotable_bg.png")
    emblem = _load("center_emblem.png")
    pointer = _load("pointer.png")

    extra_spins = random.randint(4, 6)
    final_angle = 360 * extra_spins + landing_rotation(operation)

    frames = []
    for f in range(num_frames + 1):
        t = f / num_frames
        angle = final_angle * ease_out_quart(t)
        frame = _build_frame(wheel_face, angle, holotable, emblem, pointer)
        frames.append(frame.convert("RGB"))

    return frames


def build_spin_gif(operation: str, num_frames: int = 28, frame_duration_ms: int = 45) -> io.BytesIO:
    frames = build_spin_frames(operation, num_frames=num_frames)

    # Quantize every frame against one shared palette (built from the
    # landing frame, which has the widest settled color variety) instead
    # of letting each frame pick its own - much smaller file and no
    # flickering between frames from mismatched palettes.
    palette_frame = frames[-1].quantize(colors=256, method=Image.MEDIANCUT)
    quantized = [f.quantize(palette=palette_frame, dither=Image.FLOYDSTEINBERG) for f in frames]

    buf = io.BytesIO()
    quantized[0].save(
        buf,
        format="GIF",
        save_all=True,
        append_images=quantized[1:],
        duration=frame_duration_ms,
        loop=0,
        optimize=True,
    )
    buf.seek(0)

    return buf
