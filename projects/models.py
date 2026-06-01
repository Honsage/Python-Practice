from django.conf import settings
from django.db import models

NAME_MAX_LENGTH = 200
STATUS_MAX_LENGTH = 6

STATUS_OPEN = "open"
STATUS_CLOSED = "closed"
STATUS_CHOICES = [
    (STATUS_OPEN, "Open"),
    (STATUS_CLOSED, "Closed"),
]


class Project(models.Model):
    """Проект, опубликованный пользователем."""

    name = models.CharField(max_length=NAME_MAX_LENGTH)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_projects",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    github_url = models.URLField(blank=True)
    status = models.CharField(
        max_length=STATUS_MAX_LENGTH,
        choices=STATUS_CHOICES,
        default=STATUS_OPEN,
    )
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="participated_projects",
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name
