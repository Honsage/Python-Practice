"""Валидаторы, общие для нескольких приложений."""
from urllib.parse import urlparse

from django.core.exceptions import ValidationError


def validate_github_url(value):
    """Проверяет, что ссылка валидна и ведёт на github.com."""
    if not value:
        return
    host = urlparse(value).netloc.lower()
    if host != "github.com" and not host.endswith(".github.com"):
        raise ValidationError("Ссылка должна вести на github.com")
