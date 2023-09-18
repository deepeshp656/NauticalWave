from django import forms
from nw_workspaces.models import Workspace
from git import Repo
import os
from django.conf import settings





def get_git_branches(repo_path):
    repo = Repo(repo_path)
    local_branches = [str(b) for b in repo.branches]
    remote_branches = [str(r.remote_head) for r in repo.remotes.origin.refs]
    return local_branches + remote_branches

class DeploymentForm(forms.Form):
    workspace = forms.ModelChoiceField(queryset=Workspace.objects.none())
    env_file = forms.FileField(required=False)
    dockerfile_name = forms.CharField(required=False, initial='Dockerfile')
    dynamic_envs = forms.CharField(required=False, help_text='Enter key-value pairs separated by commas. E.g., KEY1=VALUE1,KEY2=VALUE2')
    git_branch = forms.ChoiceField(choices=[]) # Choices will be populated dynamically
    deployment_method = forms.ChoiceField(choices=[('dockerfile', 'Dockerfile'), ('dockercompose', 'Docker Compose')])

    def __init__(self, user, *args, **kwargs):
        super(DeploymentForm, self).__init__(*args, **kwargs)
        self.fields['workspace'].queryset = Workspace.objects.filter(users__in=[user])
        
        # Assuming workspace is selected, you may need to adjust this logic
        workspace = self.fields['workspace'].queryset.first()
        print(os.getcwd())
        git_path = os.path.join(settings.BASE_DIR, f"workspaces/{workspace.name}/base") # Using relative path
        git_branch_choices = get_git_branches(git_path)
        self.fields['git_branch'].choices = [(branch, branch) for branch in git_branch_choices]
