from django.shortcuts import render
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect
from nw_workspaces.models import Team, Workspace
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required



def user_login(request):
    error_message = ""
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('landing_page')
        else:
            error_message = "Login failed. Invalid username or password."

    return render(request, 'user_authentication/login.html', {'error_message': error_message})


@login_required
def landing_page(request):
    user = request.user
    workspaces = Workspace.objects.filter(users=user) # Adjust this query based on your model structure

    context = {
        'workspaces': workspaces,
    }

    return render(request, 'landing_page.html', context)



def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('login')) 




