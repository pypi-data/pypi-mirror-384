"""Server setup commands for Ubuntu servers."""

import paramiko


def setup_server(host, domain, app_name="app", port=3000, user="root", key_path=None):
    """
    Set up an Ubuntu server for hosting dbbasic-web apps.

    This installs:
    - Python 3.12
    - nginx
    - certbot for SSL
    - Creates app user and directories
    - Configures systemd service
    - Sets up nginx reverse proxy
    """
    print(f"Setting up server {host} for {domain}...")

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # Connect
    connect_kwargs = {"hostname": host, "username": user}
    if key_path:
        connect_kwargs["key_filename"] = key_path

    ssh.connect(**connect_kwargs)

    def run(command, description=None):
        """Run command and print output."""
        if description:
            print(f"  {description}...")
        stdin, stdout, stderr = ssh.exec_command(command)
        exit_status = stdout.channel.recv_exit_status()
        output = stdout.read().decode()
        error = stderr.read().decode()

        if exit_status != 0:
            print(f"    Error: {error}")
            raise Exception(f"Command failed: {command}")

        if output:
            print(f"    {output.strip()}")
        return output

    # Update system
    run("apt-get update", "Updating package lists")

    # Install Python 3.12
    run("apt-get install -y software-properties-common", "Installing prerequisites")
    run("add-apt-repository -y ppa:deadsnakes/ppa", "Adding Python PPA")
    run("apt-get update", "Updating package lists")
    run("apt-get install -y python3.12 python3.12-venv python3-pip", "Installing Python 3.12")

    # Install nginx and certbot
    run("apt-get install -y nginx certbot python3-certbot-nginx", "Installing nginx and certbot")

    # Create app user
    run(f"useradd -m -s /bin/bash {app_name} || true", f"Creating {app_name} user")

    # Create app directories
    run(f"mkdir -p /var/www/{app_name}", f"Creating /var/www/{app_name}")
    run(f"chown -R {app_name}:{app_name} /var/www/{app_name}", "Setting permissions")

    # Configure firewall
    run("ufw allow 'Nginx Full' || true", "Configuring firewall")
    run("ufw allow OpenSSH || true", "Allowing SSH")
    run("ufw --force enable || true", "Enabling firewall")

    # Create systemd service
    service_content = f"""[Unit]
Description={app_name} dbbasic-web application
After=network.target

[Service]
Type=simple
User={app_name}
WorkingDirectory=/var/www/{app_name}
Environment="PATH=/var/www/{app_name}/venv/bin"
ExecStart=/var/www/{app_name}/venv/bin/uvicorn dbbasic_web.asgi:app --host 127.0.0.1 --port {port} --workers 2
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""

    run(f"cat > /etc/systemd/system/{app_name}.service << 'EOF'\n{service_content}\nEOF",
        f"Creating systemd service")

    # Create nginx config
    nginx_content = f"""server {{
    listen 80;
    server_name {domain};

    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""

    run(f"cat > /etc/nginx/sites-available/{app_name} << 'EOF'\n{nginx_content}\nEOF",
        "Creating nginx config")

    run(f"ln -sf /etc/nginx/sites-available/{app_name} /etc/nginx/sites-enabled/{app_name}",
        "Enabling nginx site")

    run("nginx -t", "Testing nginx config")
    run("systemctl reload nginx", "Reloading nginx")

    print(f"\n✓ Server setup complete!")
    print(f"\nNext steps:")
    print(f"1. Deploy your app: dbbasic-deploy push --host {host} --domain {domain}")
    print(f"2. Set up SSL: ssh {user}@{host} 'certbot --nginx -d {domain}'")

    ssh.close()
