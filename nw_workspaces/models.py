from django.db import models
import os
import git
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
import re
import threading
import git
import subprocess
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.conf import settings

    
class Team(models.Model):
    name = models.CharField(max_length=50)
    users = models.ManyToManyField(User, related_name='teams')

    def __str__(self):
        return self.name

def get_env_file_path(instance, filename):
    # Create the directory path
    dir_path = os.path.join(settings.BASE_DIR, 'workspaces', instance.name)
    # Return the full path, including the specific filename 'base_env'
    return os.path.join(dir_path, 'base_env')


def upload_to_workspace(instance, filename):
    return f'workspaces/{instance.name}/{filename}'

class Workspace(models.Model):
    name = models.CharField(max_length=100)
    github_repo_url = models.CharField(max_length=200)
    github_ssh_key_file = models.FileField(upload_to=upload_to_workspace)
    app_port = models.IntegerField(null=True, blank=True)
    admin_username = models.CharField(max_length=50)
    env_file = models.FileField(upload_to=upload_to_workspace)
    cloudflare_bearer_token = models.CharField(max_length=200)
    cloudflare_zone_id = models.CharField(max_length=50)
    users = models.ManyToManyField(User, related_name='workspaces')
    docker_start_command = models.TextField(blank=True, null=True)  

    def __str__(self):
        return self.name


@receiver(post_save, sender=Workspace)
def create_workspace_folder(sender, instance, created, **kwargs):
    subprocess.run(['git', 'config', '--system', 'core.longpaths', 'true'])
    if created:
        print(os.getcwd())
        workspace_path = os.path.join(settings.BASE_DIR,'workspaces', instance.name)
        os.makedirs(workspace_path, exist_ok=True)

        # Path to the SSH key file within the workspace's directory
        ssh_key_path = os.path.join(workspace_path, 'ssh_key')
        env_file_path = os.path.join(workspace_path, 'base_env')

        # Read the SSH key from the file
        with open(instance.github_ssh_key_file.path, 'r') as ssh_key_file:
            ssh_key_content = ssh_key_file.read()
        os.remove(instance.github_ssh_key_file.path) 
        # Save the SSH key to the file
        with open(ssh_key_path, 'w') as ssh_key_file:
            ssh_key_file.write(ssh_key_content)

        # Read the env file
        with open(instance.env_file.path, 'r') as env_file_content:
            env_file_read_content = env_file_content.read()

        os.remove(instance.env_file.path) 
        # Save the base file
        with open(env_file_path, 'w') as env_file_content:
            env_file_content.write(env_file_read_content)
        # Make the SSH key file readable only by the owner

        os.chmod(ssh_key_path, 0o600)

        # Set up the Git environment to use the saved SSH key and disable StrictHostKeyChecking
        git_ssh_cmd = f'ssh -i {ssh_key_path} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'

        # Create a new thread and start the cloning process
        clone_thread = threading.Thread(target=clone_repository, args=(instance, workspace_path, git_ssh_cmd))
        clone_thread.start()



def clone_repository(instance, workspace_path, git_ssh_cmd):
    # Prepare the command to clone the repository
    clone_command = [
        'git', 'clone', '-v',
        instance.github_repo_url,
        os.path.join(workspace_path, 'base')
    ]

    # Define the environment variables including the custom GIT_SSH_COMMAND
    my_env = os.environ.copy()
    print(git_ssh_cmd)
    my_env['GIT_SSH_COMMAND'] = git_ssh_cmd

    # Run the command with the custom environment variables
    subprocess.run(clone_command, env=my_env)
# Create your models here.
