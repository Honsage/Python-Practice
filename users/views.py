from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from utils.pagination import paginate

from .forms import ChangePasswordForm, EditProfileForm, LoginForm, RegisterForm
from .models import User

USER_FILTERS = {
    "owners-of-favorite-projects": lambda me: User.objects.filter(
        owned_projects__in=me.favorites.all()
    ),
    "owners-of-participating-projects": lambda me: User.objects.filter(
        owned_projects__participants=me
    ),
    "interested-in-my-projects": lambda me: User.objects.filter(favorites__owner=me),
    "participants-of-my-projects": lambda me: User.objects.filter(
        participated_projects__owner=me
    ),
}


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("/users/login/")
    else:
        form = RegisterForm()
    return render(request, "users/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data["email"],
                password=form.cleaned_data["password"],
            )
            if user is not None:
                login(request, user)
                return redirect("/projects/list/")
            form.add_error(None, "Неверный email или пароль")
    else:
        form = LoginForm()
    return render(request, "users/login.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("/projects/list/")


def user_list(request):
    queryset = User.objects.all()
    active_filter = request.GET.get("filter")
    if request.user.is_authenticated and active_filter in USER_FILTERS:
        queryset = USER_FILTERS[active_filter](request.user).distinct()
    else:
        active_filter = None

    query_prefix = f"filter={active_filter}&" if active_filter else ""
    page_obj = paginate(request, queryset)
    return render(
        request,
        "users/participants.html",
        {
            "participants": page_obj,
            "page_obj": page_obj,
            "active_filter": active_filter,
            "query_prefix": query_prefix,
        },
    )


def user_details(request, user_id):
    profile = get_object_or_404(User, pk=user_id)
    return render(request, "users/user-details.html", {"user": profile})


@login_required
def edit_profile(request):
    if request.method == "POST":
        form = EditProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect(f"/users/{request.user.id}/")
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, "users/edit_profile.html", {"form": form})


@login_required
def change_password(request):
    if request.method == "POST":
        form = ChangePasswordForm(user=request.user, data=request.POST)
        if form.is_valid():
            form.save()
            update_session_auth_hash(request, form.user)
            return redirect(f"/users/{request.user.id}/")
    else:
        form = ChangePasswordForm(user=request.user)
    return render(request, "users/change_password.html", {"form": form})
