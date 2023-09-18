from django.contrib import admin
from nw_workspaces.models import Workspace

@admin.register(Workspace)
class WorkspaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'github_repo_url', 'admin_username')

# Register your models here.
