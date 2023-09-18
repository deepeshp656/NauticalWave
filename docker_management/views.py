from django.shortcuts import render
import docker
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .forms import DeploymentForm
import os
import subprocess
from django.conf import settings
import shutil
from git import InvalidGitRepositoryError
from django.http import JsonResponse
from git import Repo
from nw_workspaces.models import Workspace
import socket

def find_free_port(start=3000, end=8000):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    raise Exception("No free port found")

def get_git_branches_for_workspace(request, workspace_id):
    try:
        workspace = Workspace.objects.get(pk=workspace_id)
        git_path = f"workspaces/{workspace.name}/base"
        repo = Repo(git_path)
        local_branches = [str(b) for b in repo.branches]
        remote_branches = [str(r.remote_head) for r in repo.remotes.origin.refs]
        branches = local_branches + remote_branches
        return JsonResponse({'branches': branches})
    except Workspace.DoesNotExist:
        return JsonResponse({'error': 'Workspace not found'}, status=404)

def convert_to_docker_tag(branch_name):
    # Replace illegal characters with underscores
    # Docker tags should only contain lowercase and uppercase letters, digits, underscores, periods, and dashes.
    # Git branch names can contain additional characters like '/', which are not allowed in Docker tags.
    illegal_chars = ['/']
    for char in illegal_chars:
        branch_name = branch_name.replace(char, '_')
    
    # Convert to lowercase to maintain consistency
    return branch_name.lower()



@login_required
def deploy(request):
    if request.method == 'POST':
        form = DeploymentForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            workspace = form.cleaned_data['workspace']
            env_file = form.cleaned_data['env_file']
            git_branch = form.cleaned_data['git_branch']
            deployment_method = form.cleaned_data['deployment_method']
            branch_folder_name = convert_to_docker_tag(git_branch)
            

            
            # Define paths
            base_path = os.path.join(settings.BASE_DIR, 'workspaces', workspace.name, 'base')
            branch_path = os.path.join(settings.BASE_DIR, 'workspaces', workspace.name, branch_folder_name)
            print(os.getcwd())
            print(base_path)

            # Clone the Git Repository and Checkout the Branch
            
            try:
                # Copy base folder to new branch folder
                shutil.copytree(base_path, branch_path)
                ssh_key_path = os.path.join(settings.BASE_DIR, "workspaces", workspace.name, "ssh_key")
                # Open the existing repository and checkout the branch

                git_ssh_identity_file = os.path.expanduser(ssh_key_path)
                git_ssh_cmd = f'ssh -i {git_ssh_identity_file}'

                with Repo(branch_path) as repo:
                    with repo.git.custom_environment(GIT_SSH_COMMAND=git_ssh_cmd):
                        repo.git.pull()
                        repo.git.checkout(git_branch)

            except InvalidGitRepositoryError:
                # Print paths for debugging
                print(f"Base path: {base_path}")
                print(f"Branch path: {branch_path}")

                # Optionally, return an error message to the user
                return render(request, 'error_page.html', {'message': 'Invalid Git repository'})

            docker_start_command = workspace.docker_start_command
            free_port = find_free_port()
            print(free_port)
            print(docker_start_command)
            print(workspace.app_port)
            # Deploy using Docker
            client = docker.from_env()
            if deployment_method == 'dockerfile':
                # Build and run Dockerfile
                print(f"Building image with path: {branch_path}, tag: {git_branch}")
                image, build_log = client.images.build(path=branch_path, tag=branch_folder_name)
                print("running build for the branch selected")
                container = client.containers.run(
                    image=image, 
                    ports={workspace.app_port: free_port}, 
                    command=docker_start_command,  # Use the command here
                    env_file=env_file, 
                    detach=True
                )
            elif deployment_method == 'dockercompose':
                # Run Docker Compose
                subprocess.run(['docker-compose', 'up', '-d'], cwd=branch_path)

            # Update the Workspace Model with the App Port
            # Assuming the Workspace model has an app_port field
            workspace.app_port = container.ports[workspace.app_port][0]['HostPort']
            workspace.save()

            return redirect('success_url') # Redirect to a success page
        
    else:
        form = DeploymentForm(request.user)

    return render(request, 'docker_management/deployment_page.html', {'form': form})





@login_required
def container_names(request):
    client = docker.from_env()
    containers = client.containers.list(all=True)  # Fetch all containers (running and stopped)

    container_info = []
    for container in containers:
        container_ports = container.ports
        mapped_ports = [port[0]['HostPort'] for port in container_ports.values() if port is not None]
        container_labels = container.labels
        status = container.status  # 'running', 'paused', or 'stopped'
        container_info.append({
            'name': container.name,
            'ports': mapped_ports,
            'labels': container_labels,
            'status': status
        })

    return render(request, 'docker_management/container_names.html', {'containers': container_info})


@login_required
def start_container(request):
    if request.method == 'POST':
        container_name = request.POST['container_name']
        client = docker.from_env()
        container = client.containers.get(container_name)
        container.start()
        # Redirect to the container list page (change the URL as needed)
        return redirect('containers')
    
@login_required    
def stop_container(request):
    if request.method == 'POST':
        container_name = request.POST['container_name']
        client = docker.from_env()
        container = client.containers.get(container_name)
        container.stop()
        # Redirect to the container list page (change the URL as needed)
        return redirect('containers')

@login_required   
def delete_container(request):
    if request.method == 'POST':
        container_name = request.POST['container_name']
        client = docker.from_env()
        container = client.containers.get(container_name)
        
        # Stop and remove the container
        container.stop()
        container.remove()
        
        # Redirect to the container list page (change the URL as needed)
        return redirect('containers')
