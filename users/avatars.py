"""Генерация дефолтного аватара: первая буква имени на однотонном фоне."""

import random
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

# Спокойные фоновые цвета, на которых белая буква читается хорошо.
TEAL = "#3D7068"
SLATE = "#4F6D7A"
PLUM = "#7D6B91"
OLIVE = "#6B7B5E"
CLAY = "#8A6D62"
STEEL = "#5C6B73"
PALETTE = [TEAL, SLATE, PLUM, OLIVE, CLAY, STEEL]

TEXT_COLOR = "#FFFFFF"
AVATAR_SIZE = 256
LETTER_HEIGHT_RATIO = 0.5
FALLBACK_LETTER = "?"

FONT_PATH = (
    settings.BASE_DIR / "static" / "fonts" / "Neue_Haas_Grotesk_Display_Pro_75_Bold.otf"
)


def generate_avatar(name, size=AVATAR_SIZE):
    """Возвращает ContentFile с PNG-аватаром по первой букве имени."""
    letter = (name or FALLBACK_LETTER).strip()[:1].upper() or FALLBACK_LETTER
    image = Image.new("RGB", (size, size), random.choice(PALETTE))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype(str(FONT_PATH), size=int(size * LETTER_HEIGHT_RATIO))
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), letter, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = (
        (size - text_width) / 2 - bbox[0],
        (size - text_height) / 2 - bbox[1],
    )
    draw.text(position, letter, fill=TEXT_COLOR, font=font)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue())
