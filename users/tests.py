import shutil
import tempfile

from django.test import TestCase, override_settings

from projects.models import Project
from users.models import User

TEMP_MEDIA = tempfile.mkdtemp()


def tearDownModule():
    shutil.rmtree(TEMP_MEDIA, ignore_errors=True)


def make_user(email, name="Иван", surname="Петров", password="secret123", **extra):
    return User.objects.create_user(
        email=email, name=name, surname=surname, password=password, **extra
    )


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class UserModelTests(TestCase):
    def test_avatar_is_generated_on_create(self):
        user = make_user("a@example.com", name="Анна")
        self.assertTrue(user.avatar)
        self.assertTrue(user.avatar.name.endswith(".png"))

    def test_email_is_username_field(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_password_is_hashed(self):
        user = make_user("a@example.com")
        self.assertNotEqual(user.password, "secret123")
        self.assertTrue(user.check_password("secret123"))


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class RegistrationTests(TestCase):
    url = "/users/register/"

    def test_get_renders_form(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_valid_post_creates_user_and_authenticates(self):
        response = self.client.post(
            self.url,
            {
                "name": "Иван",
                "surname": "Петров",
                "email": "ivan@example.com",
                "password": "secret123",
            },
        )
        self.assertRedirects(
            response, "/projects/list/", fetch_redirect_response=False
        )
        user = User.objects.get(email="ivan@example.com")
        self.assertTrue(user.check_password("secret123"))
        self.assertEqual(self.client.session.get("_auth_user_id"), str(user.id))

    def test_duplicate_email_is_rejected(self):
        make_user("ivan@example.com")
        response = self.client.post(
            self.url,
            {
                "name": "Иван",
                "surname": "Сидоров",
                "email": "ivan@example.com",
                "password": "secret123",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(email="ivan@example.com").count(), 1)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = make_user("ivan@example.com", password="secret123")

    def test_login_with_correct_credentials(self):
        response = self.client.post(
            "/users/login/",
            {"email": "ivan@example.com", "password": "secret123"},
        )
        self.assertRedirects(
            response, "/projects/list/", fetch_redirect_response=False
        )
        self.assertEqual(self.client.session.get("_auth_user_id"), str(self.user.id))

    def test_login_with_wrong_password_shows_error(self):
        response = self.client.post(
            "/users/login/",
            {"email": "ivan@example.com", "password": "wrong"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Неверный email или пароль")
        self.assertIsNone(self.client.session.get("_auth_user_id"))

    def test_logout_redirects_home(self):
        self.client.force_login(self.user)
        response = self.client.get("/users/logout/")
        self.assertRedirects(
            response, "/projects/list/", fetch_redirect_response=False
        )
        self.assertIsNone(self.client.session.get("_auth_user_id"))


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class UserDetailsTests(TestCase):
    def test_details_page_renders_requested_user(self):
        user = make_user("ivan@example.com", name="Иван")
        response = self.client.get(f"/users/{user.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["user"], user)

    def test_unknown_user_returns_404(self):
        response = self.client.get("/users/999/")
        self.assertEqual(response.status_code, 404)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class UserListTests(TestCase):
    def test_list_is_ordered_by_id(self):
        first = make_user("a@example.com")
        second = make_user("b@example.com")
        response = self.client.get("/users/list/")
        self.assertEqual(response.status_code, 200)
        ids = [u.id for u in response.context["page_obj"]]
        self.assertEqual(ids, sorted(ids))
        self.assertIn(first, response.context["page_obj"])
        self.assertIn(second, response.context["page_obj"])

    def test_pagination_twelve_per_page(self):
        for i in range(13):
            make_user(f"user{i}@example.com")
        response = self.client.get("/users/list/")
        self.assertEqual(len(response.context["page_obj"]), 12)

    def test_anonymous_filter_is_ignored(self):
        make_user("a@example.com")
        response = self.client.get(
            "/users/list/?filter=participants-of-my-projects"
        )
        self.assertIsNone(response.context["active_filter"])
        self.assertEqual(len(response.context["page_obj"]), 1)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class UserFilterTests(TestCase):
    def setUp(self):
        self.me = make_user("me@example.com")
        self.author = make_user("author@example.com")
        self.fan = make_user("fan@example.com")
        self.member = make_user("member@example.com")
        self.client.force_login(self.me)

    def test_owners_of_favorite_projects(self):
        project = Project.objects.create(name="P", owner=self.author)
        self.me.favorites.add(project)
        response = self.client.get(
            "/users/list/?filter=owners-of-favorite-projects"
        )
        self.assertEqual(response.context["active_filter"], "owners-of-favorite-projects")
        self.assertIn(self.author, response.context["page_obj"])
        self.assertNotIn(self.fan, response.context["page_obj"])

    def test_owners_of_participating_projects(self):
        project = Project.objects.create(name="P", owner=self.author)
        project.participants.add(self.me)
        response = self.client.get(
            "/users/list/?filter=owners-of-participating-projects"
        )
        self.assertIn(self.author, response.context["page_obj"])
        self.assertNotIn(self.fan, response.context["page_obj"])

    def test_interested_in_my_projects(self):
        my_project = Project.objects.create(name="Mine", owner=self.me)
        self.fan.favorites.add(my_project)
        response = self.client.get(
            "/users/list/?filter=interested-in-my-projects"
        )
        self.assertIn(self.fan, response.context["page_obj"])
        self.assertNotIn(self.author, response.context["page_obj"])

    def test_participants_of_my_projects(self):
        my_project = Project.objects.create(name="Mine", owner=self.me)
        my_project.participants.add(self.member)
        response = self.client.get(
            "/users/list/?filter=participants-of-my-projects"
        )
        self.assertIn(self.member, response.context["page_obj"])
        self.assertNotIn(self.author, response.context["page_obj"])


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class EditProfileTests(TestCase):
    def setUp(self):
        self.user = make_user("ivan@example.com")
        self.client.force_login(self.user)

    def _payload(self, **overrides):
        data = {
            "name": "Иван",
            "surname": "Петров",
            "about": "Обо мне",
            "phone": "+79991234567",
            "github_url": "",
        }
        data.update(overrides)
        return data

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get("/users/edit-profile/")
        self.assertEqual(response.status_code, 302)

    def test_valid_update_redirects_to_profile(self):
        response = self.client.post("/users/edit-profile/", self._payload(name="Пётр"))
        self.assertRedirects(
            response, f"/users/{self.user.id}/", fetch_redirect_response=False
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, "Пётр")

    def test_phone_8_format_is_normalized_to_plus7(self):
        self.client.post("/users/edit-profile/", self._payload(phone="89991234567"))
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, "+79991234567")

    def test_invalid_phone_format_is_rejected(self):
        response = self.client.post("/users/edit-profile/", self._payload(phone="12345"))
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.phone)

    def test_duplicate_phone_across_formats_is_rejected(self):
        other = make_user("other@example.com")
        other.phone = "+79991234567"
        other.save()
        response = self.client.post(
            "/users/edit-profile/", self._payload(phone="89991234567")
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.phone)

    def test_non_github_url_is_rejected(self):
        response = self.client.post(
            "/users/edit-profile/",
            self._payload(github_url="https://gitlab.com/ivan"),
        )
        self.assertEqual(response.status_code, 200)

    def test_valid_github_url_is_accepted(self):
        response = self.client.post(
            "/users/edit-profile/",
            self._payload(github_url="https://github.com/ivan"),
        )
        self.assertEqual(response.status_code, 302)
        self.user.refresh_from_db()
        self.assertEqual(self.user.github_url, "https://github.com/ivan")


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ChangePasswordTests(TestCase):
    def setUp(self):
        self.user = make_user("ivan@example.com", password="secret123")
        self.client.force_login(self.user)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get("/users/change-password/")
        self.assertEqual(response.status_code, 302)

    def test_successful_change(self):
        response = self.client.post(
            "/users/change-password/",
            {
                "old_password": "secret123",
                "new_password1": "brandnew456",
                "new_password2": "brandnew456",
            },
        )
        self.assertRedirects(
            response, f"/users/{self.user.id}/", fetch_redirect_response=False
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("brandnew456"))

    def test_wrong_old_password_is_rejected(self):
        response = self.client.post(
            "/users/change-password/",
            {
                "old_password": "wrong",
                "new_password1": "brandnew456",
                "new_password2": "brandnew456",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("secret123"))
