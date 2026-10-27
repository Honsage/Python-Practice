import shutil
import tempfile
from http import HTTPStatus

from django.test import TestCase, override_settings

from projects.models import STATUS_CLOSED, STATUS_OPEN, Project
from users.models import User

TEMP_MEDIA = tempfile.mkdtemp()

ROOT_URL = "/"
LIST_URL = "/projects/list/"
FAVORITES_URL = "/projects/favorites/"
CREATE_URL = "/projects/create-project/"

OWNER_EMAIL = "owner@example.com"
USER_EMAIL = "ivan@example.com"
STRANGER_EMAIL = "stranger@example.com"


def tearDownModule():
    shutil.rmtree(TEMP_MEDIA, ignore_errors=True)


def make_user(email, name="Иван", surname="Петров", password="secret123"):
    return User.objects.create_user(
        email=email, name=name, surname=surname, password=password
    )


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class RootRedirectTests(TestCase):
    def test_root_redirects_to_project_list(self):
        response = self.client.get(ROOT_URL)
        self.assertRedirects(response, LIST_URL, fetch_redirect_response=False)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ProjectListTests(TestCase):
    def setUp(self):
        self.owner = make_user(OWNER_EMAIL)

    def test_newest_projects_first(self):
        old = Project.objects.create(name="Old", owner=self.owner)
        new = Project.objects.create(name="New", owner=self.owner)
        response = self.client.get(LIST_URL)
        page = list(response.context["page_obj"])
        self.assertLess(page.index(new), page.index(old))

    def test_pagination_twelve_per_page(self):
        for i in range(13):
            Project.objects.create(name=f"P{i}", owner=self.owner)
        response = self.client.get(LIST_URL)
        self.assertEqual(len(response.context["page_obj"]), 12)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ProjectDetailsTests(TestCase):
    def test_details_render_project(self):
        owner = make_user(OWNER_EMAIL)
        project = Project.objects.create(name="P", owner=owner)
        response = self.client.get(f"/projects/{project.id}/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["project"], project)

    def test_unknown_project_returns_404(self):
        response = self.client.get("/projects/999/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class CreateProjectTests(TestCase):
    def setUp(self):
        self.user = make_user(USER_EMAIL)

    def test_requires_login(self):
        response = self.client.get(CREATE_URL)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_create_sets_owner_and_adds_owner_as_participant(self):
        self.client.force_login(self.user)
        name = "Новый проект"
        response = self.client.post(
            CREATE_URL,
            {
                "name": name,
                "description": "Описание",
                "github_url": "",
                "status": STATUS_OPEN,
            },
        )
        project = Project.objects.get(name=name)
        self.assertRedirects(
            response, f"/projects/{project.id}/", fetch_redirect_response=False
        )
        self.assertEqual(project.owner, self.user)
        self.assertIn(self.user, project.participants.all())

    def test_non_github_url_is_rejected(self):
        self.client.force_login(self.user)
        name = "Проект"
        response = self.client.post(
            CREATE_URL,
            {
                "name": name,
                "description": "",
                "github_url": "https://gitlab.com/x",
                "status": STATUS_OPEN,
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(Project.objects.filter(name=name).exists())


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class EditProjectTests(TestCase):
    def setUp(self):
        self.owner = make_user(OWNER_EMAIL)
        self.stranger = make_user(STRANGER_EMAIL)
        self.project = Project.objects.create(name="P", owner=self.owner)

    def test_owner_can_edit(self):
        self.client.force_login(self.owner)
        new_name = "Изменён"
        response = self.client.post(
            f"/projects/{self.project.id}/edit/",
            {
                "name": new_name,
                "description": "",
                "github_url": "",
                "status": STATUS_OPEN,
            },
        )
        self.assertRedirects(
            response, f"/projects/{self.project.id}/", fetch_redirect_response=False
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, new_name)

    def test_stranger_cannot_edit(self):
        self.client.force_login(self.stranger)
        original_name = self.project.name
        response = self.client.post(
            f"/projects/{self.project.id}/edit/",
            {
                "name": "Взломщик",
                "description": "",
                "github_url": "",
                "status": STATUS_OPEN,
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.project.refresh_from_db()
        self.assertEqual(self.project.name, original_name)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class FavoritesPageTests(TestCase):
    def setUp(self):
        self.user = make_user(USER_EMAIL)
        self.owner = make_user(OWNER_EMAIL)
        self.fav = Project.objects.create(name="Fav", owner=self.owner)
        self.other = Project.objects.create(name="Other", owner=self.owner)
        self.user.favorites.add(self.fav)

    def test_requires_login(self):
        response = self.client.get(FAVORITES_URL)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_shows_only_user_favorites(self):
        self.client.force_login(self.user)
        response = self.client.get(FAVORITES_URL)
        projects = list(response.context["projects"])
        self.assertIn(self.fav, projects)
        self.assertNotIn(self.other, projects)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ToggleFavoriteTests(TestCase):
    def setUp(self):
        self.user = make_user(USER_EMAIL)
        self.project = Project.objects.create(name="P", owner=self.user)
        self.url = f"/projects/{self.project.id}/toggle-favorite/"

    def test_anonymous_cannot_favorite(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(self.project.interested_users.count(), 0)

    def test_toggle_adds_then_removes(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.json(), {"status": "ok", "favorited": True})
        self.assertIn(self.project, self.user.favorites.all())

        response = self.client.post(self.url)
        self.assertEqual(response.json(), {"status": "ok", "favorited": False})
        self.assertNotIn(self.project, self.user.favorites.all())

    def test_get_not_allowed(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTPStatus.METHOD_NOT_ALLOWED)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ToggleParticipateTests(TestCase):
    def setUp(self):
        self.owner = make_user(OWNER_EMAIL)
        self.user = make_user(USER_EMAIL)
        self.project = Project.objects.create(name="P", owner=self.owner)
        self.url = f"/projects/{self.project.id}/toggle-participate/"

    def test_toggle_join_then_leave(self):
        self.client.force_login(self.user)

        response = self.client.post(self.url)
        self.assertEqual(response.json(), {"status": "ok", "participant": True})
        self.assertIn(self.user, self.project.participants.all())

        response = self.client.post(self.url)
        self.assertEqual(response.json(), {"status": "ok", "participant": False})
        self.assertNotIn(self.user, self.project.participants.all())

    def test_anonymous_cannot_participate(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(self.project.participants.count(), 0)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class CompleteProjectTests(TestCase):
    def setUp(self):
        self.owner = make_user(OWNER_EMAIL)
        self.stranger = make_user(STRANGER_EMAIL)
        self.project = Project.objects.create(
            name="P", owner=self.owner, status=STATUS_OPEN
        )
        self.url = f"/projects/{self.project.id}/complete/"

    def test_owner_completes_open_project(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(
            response.json(), {"status": "ok", "project_status": STATUS_CLOSED}
        )
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, STATUS_CLOSED)

    def test_stranger_cannot_complete(self):
        self.client.force_login(self.stranger)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.project.refresh_from_db()
        self.assertEqual(self.project.status, STATUS_OPEN)

    def test_already_closed_is_rejected(self):
        self.project.status = STATUS_CLOSED
        self.project.save()
        self.client.force_login(self.owner)
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
