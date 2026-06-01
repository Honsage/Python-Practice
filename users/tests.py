import shutil
import tempfile
from http import HTTPStatus

from django.test import TestCase, override_settings

from projects.models import Project
from users.models import User

TEMP_MEDIA = tempfile.mkdtemp()

REGISTER_URL = "/users/register/"
LOGIN_URL = "/users/login/"
LOGOUT_URL = "/users/logout/"
USERS_LIST_URL = "/users/list/"
EDIT_PROFILE_URL = "/users/edit-profile/"
CHANGE_PASSWORD_URL = "/users/change-password/"
PROJECTS_LIST_URL = "/projects/list/"

USER_EMAIL = "ivan@example.com"
PASSWORD = "secret123"
NEW_PASSWORD = "brandnew456"
LOGIN_ERROR = "Неверный email или пароль"

PHONE_PLUS7 = "+79991234567"
PHONE_EIGHT = "89991234567"
GITHUB_URL = "https://github.com/ivan"

FILTER_FAVORITE_OWNERS = "owners-of-favorite-projects"
FILTER_PARTICIPATING_OWNERS = "owners-of-participating-projects"
FILTER_INTERESTED = "interested-in-my-projects"
FILTER_PARTICIPANTS = "participants-of-my-projects"


def tearDownModule():
    shutil.rmtree(TEMP_MEDIA, ignore_errors=True)


def make_user(email, name="Иван", surname="Петров", password=PASSWORD, **extra):
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
        self.assertNotEqual(user.password, PASSWORD)
        self.assertTrue(user.check_password(PASSWORD))


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class RegistrationTests(TestCase):
    def test_get_renders_form(self):
        response = self.client.get(REGISTER_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertIn("form", response.context)

    def test_valid_post_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            REGISTER_URL,
            {
                "name": "Иван",
                "surname": "Петров",
                "email": USER_EMAIL,
                "password": PASSWORD,
            },
        )
        self.assertRedirects(response, LOGIN_URL, fetch_redirect_response=False)
        user = User.objects.get(email=USER_EMAIL)
        self.assertTrue(user.check_password(PASSWORD))
        self.assertIsNone(self.client.session.get("_auth_user_id"))

    def test_duplicate_email_is_rejected(self):
        make_user(USER_EMAIL)
        response = self.client.post(
            REGISTER_URL,
            {
                "name": "Иван",
                "surname": "Сидоров",
                "email": USER_EMAIL,
                "password": PASSWORD,
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(User.objects.filter(email=USER_EMAIL).count(), 1)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class LoginLogoutTests(TestCase):
    def setUp(self):
        self.user = make_user(USER_EMAIL, password=PASSWORD)

    def test_login_with_correct_credentials(self):
        response = self.client.post(
            LOGIN_URL,
            {"email": USER_EMAIL, "password": PASSWORD},
        )
        self.assertRedirects(
            response, PROJECTS_LIST_URL, fetch_redirect_response=False
        )
        self.assertEqual(self.client.session.get("_auth_user_id"), str(self.user.id))

    def test_login_with_wrong_password_shows_error(self):
        response = self.client.post(
            LOGIN_URL,
            {"email": USER_EMAIL, "password": "wrong"},
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertContains(response, LOGIN_ERROR)
        self.assertIsNone(self.client.session.get("_auth_user_id"))

    def test_logout_redirects_home(self):
        self.client.force_login(self.user)
        response = self.client.get(LOGOUT_URL)
        self.assertRedirects(
            response, PROJECTS_LIST_URL, fetch_redirect_response=False
        )
        self.assertIsNone(self.client.session.get("_auth_user_id"))


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class UserDetailsTests(TestCase):
    def test_details_page_renders_requested_user(self):
        user = make_user(USER_EMAIL, name="Иван")
        response = self.client.get(f"/users/{user.id}/")
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(response.context["user"], user)

    def test_unknown_user_returns_404(self):
        response = self.client.get("/users/999/")
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class UserListTests(TestCase):
    def test_list_is_ordered_newest_first(self):
        first = make_user("a@example.com")
        second = make_user("b@example.com")
        response = self.client.get(USERS_LIST_URL)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        ids = [u.id for u in response.context["page_obj"]]
        self.assertEqual(ids, sorted(ids, reverse=True))
        self.assertIn(first, response.context["page_obj"])
        self.assertIn(second, response.context["page_obj"])

    def test_pagination_twelve_per_page(self):
        for i in range(13):
            make_user(f"user{i}@example.com")
        response = self.client.get(USERS_LIST_URL)
        self.assertEqual(len(response.context["page_obj"]), 12)

    def test_anonymous_filter_is_ignored(self):
        make_user("a@example.com")
        response = self.client.get(f"{USERS_LIST_URL}?filter={FILTER_PARTICIPANTS}")
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
        response = self.client.get(f"{USERS_LIST_URL}?filter={FILTER_FAVORITE_OWNERS}")
        self.assertEqual(response.context["active_filter"], FILTER_FAVORITE_OWNERS)
        self.assertIn(self.author, response.context["page_obj"])
        self.assertNotIn(self.fan, response.context["page_obj"])

    def test_owners_of_participating_projects(self):
        project = Project.objects.create(name="P", owner=self.author)
        project.participants.add(self.me)
        response = self.client.get(
            f"{USERS_LIST_URL}?filter={FILTER_PARTICIPATING_OWNERS}"
        )
        self.assertIn(self.author, response.context["page_obj"])
        self.assertNotIn(self.fan, response.context["page_obj"])

    def test_interested_in_my_projects(self):
        my_project = Project.objects.create(name="Mine", owner=self.me)
        self.fan.favorites.add(my_project)
        response = self.client.get(f"{USERS_LIST_URL}?filter={FILTER_INTERESTED}")
        self.assertIn(self.fan, response.context["page_obj"])
        self.assertNotIn(self.author, response.context["page_obj"])

    def test_participants_of_my_projects(self):
        my_project = Project.objects.create(name="Mine", owner=self.me)
        my_project.participants.add(self.member)
        response = self.client.get(f"{USERS_LIST_URL}?filter={FILTER_PARTICIPANTS}")
        self.assertIn(self.member, response.context["page_obj"])
        self.assertNotIn(self.author, response.context["page_obj"])


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class EditProfileTests(TestCase):
    def setUp(self):
        self.user = make_user(USER_EMAIL)
        self.client.force_login(self.user)

    def _payload(self, **overrides):
        data = {
            "name": "Иван",
            "surname": "Петров",
            "about": "Обо мне",
            "phone": PHONE_PLUS7,
            "github_url": "",
        }
        data.update(overrides)
        return data

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(EDIT_PROFILE_URL)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_valid_update_redirects_to_profile(self):
        new_name = "Пётр"
        response = self.client.post(EDIT_PROFILE_URL, self._payload(name=new_name))
        self.assertRedirects(
            response, f"/users/{self.user.id}/", fetch_redirect_response=False
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, new_name)

    def test_phone_8_format_is_normalized_to_plus7(self):
        self.client.post(EDIT_PROFILE_URL, self._payload(phone=PHONE_EIGHT))
        self.user.refresh_from_db()
        self.assertEqual(self.user.phone, PHONE_PLUS7)

    def test_invalid_phone_format_is_rejected(self):
        response = self.client.post(EDIT_PROFILE_URL, self._payload(phone="12345"))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.phone)

    def test_duplicate_phone_across_formats_is_rejected(self):
        other = make_user("other@example.com")
        other.phone = PHONE_PLUS7
        other.save()
        response = self.client.post(EDIT_PROFILE_URL, self._payload(phone=PHONE_EIGHT))
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.phone)

    def test_non_github_url_is_rejected(self):
        response = self.client.post(
            EDIT_PROFILE_URL,
            self._payload(github_url="https://gitlab.com/ivan"),
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_valid_github_url_is_accepted(self):
        response = self.client.post(
            EDIT_PROFILE_URL,
            self._payload(github_url=GITHUB_URL),
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.user.refresh_from_db()
        self.assertEqual(self.user.github_url, GITHUB_URL)


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ChangePasswordTests(TestCase):
    def setUp(self):
        self.user = make_user(USER_EMAIL, password=PASSWORD)
        self.client.force_login(self.user)

    def test_requires_login(self):
        self.client.logout()
        response = self.client.get(CHANGE_PASSWORD_URL)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_successful_change(self):
        response = self.client.post(
            CHANGE_PASSWORD_URL,
            {
                "old_password": PASSWORD,
                "new_password1": NEW_PASSWORD,
                "new_password2": NEW_PASSWORD,
            },
        )
        self.assertRedirects(
            response, f"/users/{self.user.id}/", fetch_redirect_response=False
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))

    def test_wrong_old_password_is_rejected(self):
        response = self.client.post(
            CHANGE_PASSWORD_URL,
            {
                "old_password": "wrong",
                "new_password1": NEW_PASSWORD,
                "new_password2": NEW_PASSWORD,
            },
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(PASSWORD))
