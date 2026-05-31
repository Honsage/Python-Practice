from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from utils.pagination import paginate

from .forms import ProjectForm
from .models import Project


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
            return redirect(f"/projects/{project.id}/")
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
def toggle_favorite(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if request.user.favorites.filter(pk=project.pk).exists():
        request.user.favorites.remove(project)
        favorited = False
    else:
        request.user.favorites.add(project)
        favorited = True
    return JsonResponse({"status": "ok", "favorited": favorited})


@require_POST
@login_required
def toggle_participate(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.participants.filter(pk=request.user.pk).exists():
        project.participants.remove(request.user)
        participant = False
    else:
        project.participants.add(request.user)
        participant = True
    return JsonResponse({"status": "ok", "participant": participant})


@require_POST
@login_required
def complete_project(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    if project.owner_id != request.user.id or project.status != "open":
        return JsonResponse({"status": "error"}, status=403)
    project.status = "closed"
    project.save(update_fields=["status"])
    return JsonResponse({"status": "ok", "project_status": "closed"})
