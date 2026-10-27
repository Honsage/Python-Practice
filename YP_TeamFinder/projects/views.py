from functools import wraps
from http import HTTPStatus

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from utils.pagination import paginate

from .forms import ProjectForm
from .models import STATUS_CLOSED, STATUS_OPEN, Project


def _with_project(view):
    """Передаёт во view найденный проект или отдаёт статус 404 для AJAX."""

    @wraps(view)
    def wrapper(request, project_id, *args, **kwargs):
        project = Project.objects.filter(pk=project_id).first()
        if project is None:
            return JsonResponse(
                {"status": "error", "message": "Проект не найден"},
                status=HTTPStatus.NOT_FOUND,
            )
        return view(request, project, *args, **kwargs)

    return wrapper


def project_list(request):
    projects = Project.objects.all()
    page_obj = paginate(request, projects)
    return render(
        request,
        "projects/project_list.html",
        {"projects": projects, "page_obj": page_obj, "query_prefix": ""},
    )


@login_required
def favorites(request):
    projects = request.user.favorites.all().order_by("-created_at")
    return render(request, "projects/favorite_projects.html", {"projects": projects})


def project_details(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    return render(request, "projects/project-details.html", {"project": project})


def _project_form_view(request, instance, is_edit):
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=instance)
        if form.is_valid():
            project = form.save(commit=False)
            if not is_edit:
                project.owner = request.user
            project.save()
            if not is_edit:
                project.participants.add(request.user)
            return redirect("projects:details", project_id=project.id)
    else:
        form = ProjectForm(instance=instance)
    return render(
        request,
        "projects/create-project.html",
        {"form": form, "is_edit": is_edit},
    )


@login_required
def create_project(request):
    return _project_form_view(request, instance=None, is_edit=False)


@login_required
def edit_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.id:
        return HttpResponseForbidden("Недостаточно прав")
    return _project_form_view(request, instance=project, is_edit=True)


@require_POST
@login_required
@_with_project
def toggle_favorite(request, project):
    favorites = request.user.favorites
    is_favorited = favorites.filter(pk=project.pk).exists()
    if is_favorited:
        favorites.remove(project)
    else:
        favorites.add(project)
    return JsonResponse({"status": "ok", "favorited": not is_favorited})


@require_POST
@login_required
@_with_project
def toggle_participate(request, project):
    participants = project.participants
    is_participant = participants.filter(pk=request.user.pk).exists()
    if is_participant:
        participants.remove(request.user)
    else:
        participants.add(request.user)
    return JsonResponse({"status": "ok", "participant": not is_participant})


@require_POST
@login_required
@_with_project
def complete_project(request, project):
    if project.owner_id != request.user.id or project.status != STATUS_OPEN:
        return JsonResponse({"status": "error"}, status=HTTPStatus.FORBIDDEN)
    project.status = STATUS_CLOSED
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": STATUS_CLOSED})
