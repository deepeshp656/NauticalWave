from django.contrib import admin
from django.urls import path
from django.contrib.auth.decorators import login_required
from user_authentication.views import user_login, landing_page, logout_view
from nw_workspaces.views import workspace, home_view
from docker_management.views import container_names, start_container, get_git_branches_for_workspace, stop_container, delete_container, deploy



urlpatterns = [
    path('login/', user_login, name='login'),
    path('admin/', admin.site.urls),
    path('containers/', login_required(container_names), name='containers'),
    path('landing_page/', login_required(landing_page), name='landing_page'),
    path('workspace/<int:team_id>/', login_required(workspace), name='workspace'),
    path('workspaces/', login_required(workspace), name='workspaces_list'),    
    path('home/', login_required(home_view), name='home'),
    path('logout/', logout_view, name='logout'),
    path('start_container/', login_required(start_container), name='start_container'),
    path('stop_container/', login_required(stop_container), name='stop_container'),
    path('delete_container/', login_required(delete_container), name='delete_container'),
    path('deploy/', deploy, name='deploy'),
    path('get_git_branches/<int:workspace_id>/', get_git_branches_for_workspace, name='get_git_branches'),
    
    # Remove or comment out the line that includes 'user_authentication.urls'
]
