from django import forms

from team_finder.validators import validate_github_url

from .models import Project


class ProjectForm(forms.ModelForm):
    """Создание и редактирование проекта."""

    status = forms.ChoiceField(
        label="Статус",
        choices=[("open", "Открыт"), ("closed", "Закрыт")],
        widget=forms.Select,
    )

    class Meta:
        model = Project
        fields = ["name", "description", "github_url", "status"]
        labels = {
            "name": "Название проекта",
            "description": "Описание проекта",
            "github_url": "Ссылка на GitHub",
        }

    def clean_github_url(self):
        url = self.cleaned_data.get("github_url")
        validate_github_url(url)
        return url
