"""Генерация дефолтного аватара: первая буква имени на однотонном фоне."""
import random
from io import BytesIO

from django.conf import settings
from django.core.files.base import ContentFile
from PIL import Image, ImageDraw, ImageFont

_PALETTE = [
    "#5B8C85", "#3D7068", "#6C7A89", "#7D6B91", "#8E6C88",
    "#4F6D7A", "#5C6B73", "#7A6C5D", "#6B7B5E", "#8A6D62",
    "#5D737E", "#646E78", "#7E6B8F", "#4C7273", "#866A6A",
]

_FONT_PATH = settings.BASE_DIR / "static" / "fonts" / "Neue_Haas_Grotesk_Display_Pro_75_Bold.otf"


def generate_avatar(name, size=256):
    """Возвращает ContentFile с PNG-аватаром по первой букве имени."""
    letter = (name or "?").strip()[:1].upper() or "?"
    image = Image.new("RGB", (size, size), random.choice(_PALETTE))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype(str(_FONT_PATH), size=int(size * 0.5))
    except OSError:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), letter, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    position = (
        (size - text_width) / 2 - bbox[0],
        (size - text_height) / 2 - bbox[1],
    )
    draw.text(position, letter, fill="#FFFFFF", font=font)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue())
