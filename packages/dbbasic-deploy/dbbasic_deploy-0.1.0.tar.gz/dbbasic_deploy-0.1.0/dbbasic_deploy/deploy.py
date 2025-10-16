"""Deployment commands for dbbasic-web apps."""

import os
import paramiko
from paramiko import SFTPClient


def deploy_app(host, domain, app_name="app", port=3000, user="root", key_path=None, local_path="."):
    """
    Deploy a dbbasic-web app to Ubuntu server.

    Steps:
    1. Copy code to server
    2. Install dependencies
    3. Restart service
    4. Check health
    """
    print(f"Deploying to {host}...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Connect
    connect_kwargs = {"hostname": host, "username": user}
    if key_path:
        connect_kwargs["key_filename"] = key_path

    ssh.connect(**connect_kwargs)

    def run(command, description=None, check=True):
        """Run command and print output."""
        if description:
            print(f"  {description}...")
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        error = stderr.read().decode()

        if check and exit_status != 0:
            print(f"    Error: {error}")
            raise Exception(f"Command failed: {command}")

        if output:
            for line in output.strip().split('\n'):
                print(f"    {line}")
        return output, exit_status

    # Create temp directory for upload
    temp_dir = f"/tmp/{app_name}-deploy"
    run(f"rm -rf {temp_dir} && mkdir -p {temp_dir}", "Preparing temp directory")

    # Upload files via SFTP
    print("  Uploading files...")
    sftp = ssh.open_sftp()

    def upload_directory(local_dir, remote_dir):
        """Recursively upload directory."""
        for item in os.listdir(local_dir):
            local_item = os.path.join(local_dir, item)
            remote_item = f"{remote_dir}/{item}"

            # Skip common directories to ignore
            if item in ['__pycache__', '.git', 'venv', 'node_modules', '.DS_Store', 'var']:
                continue

            if os.path.isfile(local_item):
                sftp.put(local_item, remote_item)
                print(f"    Uploaded {item}")
            elif os.path.isdir(local_item):
                try:
                    sftp.mkdir(remote_item)
                except IOError:
                    pass  # Directory might already exist
                upload_directory(local_item, remote_item)

    upload_directory(local_path, temp_dir)
    sftp.close()

    # Move to app directory
    app_dir = f"/var/www/{app_name}"
    run(f"sudo -u {app_name} rm -rf {app_dir}/*", "Clearing app directory")
    run(f"sudo -u {app_name} cp -r {temp_dir}/* {app_dir}/", "Moving files to app directory")
    run(f"rm -rf {temp_dir}", "Cleaning up")

    # Create venv if it doesn't exist
    output, status = run(f"sudo -u {app_name} test -d {app_dir}/venv", check=False)
    if status != 0:
        run(f"sudo -u {app_name} python3.12 -m venv {app_dir}/venv", "Creating virtual environment")

    # Install dependencies
    run(f"sudo -u {app_name} {app_dir}/venv/bin/pip install --upgrade pip", "Upgrading pip")
    run(f"sudo -u {app_name} {app_dir}/venv/bin/pip install -r {app_dir}/requirements.txt",
        "Installing dependencies")

    # Restart service
    run(f"systemctl restart {app_name}", "Restarting service")
    run(f"systemctl enable {app_name}", "Enabling service")

    # Check status
    output, status = run(f"systemctl is-active {app_name}", "Checking service status", check=False)
    if status == 0:
        print(f"\n✓ Deployment successful!")
        print(f"\nYour app is running at:")
        print(f"  http://{domain}")
        print(f"\nTo check logs:")
        print(f"  ssh {user}@{host} 'journalctl -u {app_name} -f'")
    else:
        print(f"\n✗ Service failed to start")
        print(f"\nCheck logs:")
        print(f"  ssh {user}@{host} 'journalctl -u {app_name} -n 50'")

    ssh.close()
