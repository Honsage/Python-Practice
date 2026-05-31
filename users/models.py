import uuid

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models

from .avatars import generate_avatar


class UserManager(BaseUserManager):
    """Менеджер пользователей с идентификацией по email."""

    use_in_migrations = True

    def create_user(self, email, name, surname, password=None, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, surname=surname, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, surname, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True")
        return self.create_user(email, name, surname, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Пользователь платформы. Вход по email."""

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=124)
    surname = models.CharField(max_length=124)
    avatar = models.ImageField(upload_to="avatars/")
    phone = models.CharField(max_length=12, unique=True, null=True, blank=True)
    github_url = models.URLField(blank=True)
    about = models.TextField(max_length=256, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    favorites = models.ManyToManyField(
        "projects.Project",
        related_name="interested_users",
        blank=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.name} {self.surname}"

    def save(self, *args, **kwargs):
        if not self.avatar:
            self.avatar.save(
                f"avatar_{uuid.uuid4()}.png",
                generate_avatar(self.name),
                save=False,
            )
        super().save(*args, **kwargs)
