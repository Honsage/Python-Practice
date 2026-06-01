import re

from django import forms

from utils.validators import validate_github_url

from .models import User

_PHONE_FULL = re.compile(r"\+7\d{10}")
_PHONE_EIGHT = re.compile(r"8\d{10}")


class RegisterForm(forms.ModelForm):
    """Регистрация: имя, фамилия, email и пароль."""

    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ["name", "surname", "email", "password"]
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "email": "Email",
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Вход по email и паролю."""

    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)


class EditProfileForm(forms.ModelForm):
    """Редактирование личной информации пользователя."""

    class Meta:
        model = User
        fields = ["name", "surname", "avatar", "about", "phone", "github_url"]
        labels = {
            "name": "Имя",
            "surname": "Фамилия",
            "avatar": "Аватар",
            "about": "О себе",
            "phone": "Телефон",
            "github_url": "Ссылка на GitHub",
        }

    def clean_phone(self):
        phone = (self.cleaned_data.get("phone") or "").strip()
        if not phone:
            raise forms.ValidationError("Укажите номер телефона")
        if _PHONE_EIGHT.fullmatch(phone):
            phone = "+7" + phone[1:]
        elif not _PHONE_FULL.fullmatch(phone):
            raise forms.ValidationError("Формат: 8XXXXXXXXXX или +7XXXXXXXXXX")
        duplicate = User.objects.filter(phone=phone).exclude(pk=self.instance.pk)
        if duplicate.exists():
            raise forms.ValidationError("Этот номер телефона уже используется")
        return phone

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        validate_github_url(url)
        return url
