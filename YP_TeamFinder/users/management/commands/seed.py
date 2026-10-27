"""Наполняет базу демонстрационными пользователями и проектами.

Команда идемпотентна: повторный запуск не создаёт дубликатов.
Пароль всех демо-пользователей – `password`.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from projects.models import Project
from users.models import User

DEMO_PASSWORD = "password"

USERS = [
    {
        "email": "anna@example.com",
        "name": "Анна",
        "surname": "Смирнова",
        "phone": "+79990000001",
        "about": "Frontend-разработчик, люблю аккуратный UI.",
        "github_url": "https://github.com/anna",
    },
    {
        "email": "boris@example.com",
        "name": "Борис",
        "surname": "Ковалёв",
        "phone": "+79990000002",
        "about": "Backend на Python, интересуюсь распределёнными системами.",
        "github_url": "https://github.com/boris",
    },
    {
        "email": "vera@example.com",
        "name": "Вера",
        "surname": "Орлова",
        "phone": "+79990000003",
        "about": "Дизайнер продуктов и иллюстратор.",
        "github_url": "",
    },
    {
        "email": "dmitry@example.com",
        "name": "Дмитрий",
        "surname": "Соколов",
        "phone": "+79990000004",
        "about": "DevOps-инженер, автоматизирую всё подряд.",
        "github_url": "https://github.com/dmitry",
    },
]

# Проекты по email автора.
PROJECTS = [
    {
        "owner": "anna@example.com",
        "name": "Дизайн-система TeamFinder",
        "description": "Единая библиотека компонентов и стилей для платформы.",
        "status": "open",
        "github_url": "https://github.com/anna/design-system",
    },
    {
        "owner": "boris@example.com",
        "name": "Сервис уведомлений",
        "description": "Очередь и доставка уведомлений пользователям.",
        "status": "open",
        "github_url": "",
    },
    {
        "owner": "boris@example.com",
        "name": "API статистики",
        "description": "Сбор и агрегация метрик активности проектов.",
        "status": "closed",
        "github_url": "",
    },
    {
        "owner": "vera@example.com",
        "name": "Мобильное приложение",
        "description": "Прототип мобильной версии для поиска команды.",
        "status": "open",
        "github_url": "",
    },
    {
        "owner": "dmitry@example.com",
        "name": "Инфраструктура CI/CD",
        "description": "Пайплайны сборки, тестирования и деплоя.",
        "status": "open",
        "github_url": "https://github.com/dmitry/ci",
    },
]


class Command(BaseCommand):
    help = "Создаёт демонстрационных пользователей и проекты"

    @transaction.atomic
    def handle(self, *args, **options):
        users = self._create_users()
        projects = self._create_projects(users)
        self._link_demo_relations(users, projects)
        self.stdout.write(self.style.SUCCESS("Демо-данные готовы."))

    def _create_users(self):
        users = {}
        for data in USERS:
            user = User.objects.filter(email=data["email"]).first()
            if user is None:
                user = User.objects.create_user(password=DEMO_PASSWORD, **data)
                self.stdout.write(f"Пользователь создан: {user.email}")
            users[user.email] = user
        return users

    def _create_projects(self, users):
        projects = {}
        for data in PROJECTS:
            owner = users[data["owner"]]
            project, created = Project.objects.get_or_create(
                name=data["name"],
                owner=owner,
                defaults={
                    "description": data["description"],
                    "status": data["status"],
                    "github_url": data["github_url"],
                },
            )
            if created:
                project.participants.add(owner)
                self.stdout.write(f"Проект создан: {project.name}")
            projects[data["name"]] = project
        return projects

    def _link_demo_relations(self, users, projects):
        users["vera@example.com"].favorites.add(projects["Сервис уведомлений"])
        users["dmitry@example.com"].favorites.add(projects["Дизайн-система TeamFinder"])
        projects["Дизайн-система TeamFinder"].participants.add(
            users["boris@example.com"]
        )
        projects["Инфраструктура CI/CD"].participants.add(users["anna@example.com"])
