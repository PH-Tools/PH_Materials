from django.contrib.auth.decorators import login_required
from django.core.handlers.wsgi import WSGIRequest
from django.http import HttpResponse
from django.shortcuts import render
from django.template import Context
from django.views.decorators.http import require_POST
from render_block import render_block_to_string

from webportal.models import Team, User
from webportal.views._types import get_user

# ---------------------------------------------------------------------------------------
# -- User / Team Management Views


@login_required
def account_settings(request: WSGIRequest) -> HttpResponse:
    print(">> account_settings")

    user = get_user(request)
    context = {
        "user": user,
        "team": user.team,
        "team_members": user.team_members,
    }
    return render(request, "webportal/account_settings.html", context)


@require_POST
@login_required
def update_team_name(request: WSGIRequest) -> HttpResponse:
    print(">> update_team_name")

    locked_names = {"PUBLIC", "ADMIN"}
    user = get_user(request)

    if not user.team or user.team.name in locked_names:
        return HttpResponse(user.team.name if user.team else "PUBLIC")

    new_team_name = request.POST.get("team_name")
    if new_team_name and new_team_name not in locked_names:
        user.team.update_name(new_team_name)
        return HttpResponse(new_team_name)

    return HttpResponse(user.team.name)


@require_POST
@login_required
def update_first_name(request: WSGIRequest) -> HttpResponse:
    print(">> update_first_name")

    user = get_user(request)
    if new_first_name := request.POST.get("first_name"):
        user.first_name = new_first_name
        user.save()
        return HttpResponse(new_first_name)
    return HttpResponse(user.first_name)


@require_POST
@login_required
def update_last_name(request: WSGIRequest) -> HttpResponse:
    print(">> update_last_name")

    user = get_user(request)
    if new_last_name := request.POST.get("last_name"):
        user.last_name = new_last_name
        user.save()
        return HttpResponse(new_last_name)
    return HttpResponse(user.last_name)


@require_POST
@login_required
def update_email(request: WSGIRequest) -> HttpResponse:
    print(">> update_email")

    user = get_user(request)
    if new_email := request.POST.get("email"):
        user.email = new_email
        user.save()
        return HttpResponse(new_email)
    return HttpResponse(user.email)


@require_POST
@login_required
def invite_user_to_team(request: WSGIRequest) -> HttpResponse:
    print(">> invite_user_to_team")

    user = get_user(request)
    if not user.team:
        return HttpResponse("No Team to invite to")

    if email := request.POST.get("user_email"):
        if invited_user := User.objects.get(email=email):
            invited_user.invite_to_team(user)
            invited_user.save()
            return HttpResponse(f"Invited User '{email}' to Team '{user.team.name}'")
        return HttpResponse(f"Error: User '{email}' not found?")
    return HttpResponse("Invite User to Team")


@require_POST
@login_required
def accept_team_invite(request: WSGIRequest) -> HttpResponse:
    print(">> accept_team_invite")

    user = get_user(request)
    if not user.team_invite:
        return HttpResponse("No Team Invite to accept")
    if team := Team.objects.get(id=user.team_invite.pk):
        user.team = team
        user.team_invite = None
        user.save()
        return HttpResponse(f"Joined Team '{team.name}'")
    return HttpResponse("Accepted Team Invite")


@require_POST
@login_required
def decline_team_invite(request: WSGIRequest) -> HttpResponse:
    print(">> decline_team_invite")

    user = get_user(request)
    if not user.team_invite:
        return HttpResponse("No Team Invite to accept")
    if team := Team.objects.get(id=user.team_invite.pk):
        user.team_invite = None
        user.save()
        return HttpResponse(f"Declined Team Invite to join '{team.name}'")
    return HttpResponse("Declined Team Invite")


@require_POST
@login_required
def leave_team(request: WSGIRequest) -> HttpResponse:
    print(">> leave_team")

    user = get_user(request)
    user.team, created = Team.objects.get_or_create(name=user.username, created_by=user)
    user.team_invite = None
    user.save()

    block_html = render_block_to_string(
        "webportal/partials/account_settings/settings.html",
        block_name="teams",
        context=Context(
            {
                "user": user,
                "team": user.team,
                "team_members": user.team_members,
            }
        ),
        request=request,
    )
    return HttpResponse(block_html, content_type="text/html")
