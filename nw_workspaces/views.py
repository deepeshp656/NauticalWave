from django.shortcuts import render
from .models import Team
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from nw_workspaces.models import Workspace
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def home_view(request):
    user_workspaces = Workspace.objects.filter(users__id=request.user.id)
    context = {'user_workspaces': user_workspaces}
    return render(request, 'home.html', context)

# def workspace(request, team_id):
#     team = get_object_or_404(Team, pk=team_id)
#     if request.user not in team.users.all():
#         return HttpResponseForbidden("You don't have access to this workspace.")
#     # Render the workspace template for the selected team
#     user_workspaces = Workspace.objects.filter(users__id=request.user.id)
#     context = {'user_workspaces': user_workspaces}
#     return render(request, 'user_authentication/workspace.html', {'team': team}, context)

@login_required
def workspace(request, team_id):
    workspace = Workspace.objects.get(pk=team_id)
    return render(request, 'workspace.html', {'workspace': workspace})