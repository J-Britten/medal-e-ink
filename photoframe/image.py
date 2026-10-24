"""Turn an arbitrary photo into a frame buffer for the Spectra 6 panel."""

import numpy as np
from PIL import Image, ImageEnhance, ImageOps

from . import epd

# Palette used for dithering, paired with the panel's color code for each entry.
PALETTE = [
    ((0, 0, 0), epd.BLACK),
    ((255, 255, 255), epd.WHITE),
    ((255, 255, 0), epd.YELLOW),
    ((255, 0, 0), epd.RED),
    ((0, 0, 255), epd.BLUE),
    ((0, 255, 0), epd.GREEN),
]

# Palette index -> panel code. Unused indices fall back to white.
_CODE_LUT = np.full(256, epd.WHITE, dtype=np.uint8)
_CODE_LUT[: len(PALETTE)] = [code for _, code in PALETTE]


def _palette_image():
    flat = [c for rgb, _ in PALETTE for c in rgb]
    pal = Image.new("P", (1, 1))
    # Pad by repeating the first color so padding never adds a new color.
    pal.putpalette(flat + flat[:3] * (256 - len(PALETTE)))
    return pal


def prepare(
    img,
    *,
    rotate=0,
    fit="cover",
    background=(255, 255, 255),
    saturation=1.2,
    contrast=1.0,
    dither=True,
):
    """Return a palettised image of exactly panel size (800x480).

    rotate: how the panel is mounted, in degrees clockwise (0, 90, 180, 270).
            With 90/270 the picture is composed as 480x800 portrait.
    fit:    "cover" crops to fill the screen, "contain" letterboxes.
    """
    if rotate not in (0, 90, 180, 270):
        raise ValueError("rotate must be 0, 90, 180 or 270")

    img = ImageOps.exif_transpose(img).convert("RGB")

    size = (epd.WIDTH, epd.HEIGHT)
    if rotate in (90, 270):
        size = (epd.HEIGHT, epd.WIDTH)

    if fit == "cover":
        img = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
    elif fit == "contain":
        img = ImageOps.pad(img, size, Image.Resampling.LANCZOS, color=background)
    else:
        raise ValueError("fit must be 'cover' or 'contain'")

    # The panel's inks are much less vivid than sRGB primaries; a little boost helps.
    if saturation != 1.0:
        img = ImageEnhance.Color(img).enhance(saturation)
    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)

    if rotate:
        # PIL rotates counter-clockwise; undo the clockwise mounting rotation.
        img = img.rotate(rotate, expand=True)

    mode = Image.Dither.FLOYDSTEINBERG if dither else Image.Dither.NONE
    return img.quantize(palette=_palette_image(), dither=mode)


def pack(pimg):
    """Pack a prepared image into the panel's 4-bit-per-pixel buffer."""
    if pimg.size != (epd.WIDTH, epd.HEIGHT) or pimg.mode != "P":
        raise ValueError("expected a palettised 800x480 image from prepare()")
    codes = _CODE_LUT[np.frombuffer(pimg.tobytes(), dtype=np.uint8)]
    return ((codes[0::2] << 4) | codes[1::2]).tobytes()


def preview(pimg):
    """RGB rendering of exactly what will be sent to the panel."""
    return pimg.convert("RGB")
