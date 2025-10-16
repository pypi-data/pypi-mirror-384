"""Command-line interface for dbbasic-deploy."""

import click
from .setup import setup_server
from .deploy import deploy_app


@click.group()
@click.version_option(version="0.1.0")
def main():
    """Simple SSH deployment tool for dbbasic-web apps to Ubuntu servers."""
    pass


@main.command()
@click.option("--host", required=True, help="Server hostname or IP")
@click.option("--domain", required=True, help="Domain name for the app")
@click.option("--app-name", default="app", help="Application name (default: app)")
@click.option("--port", default=3000, help="Port for uvicorn (default: 3000)")
@click.option("--user", default="root", help="SSH user (default: root)")
@click.option("--key", "key_path", help="Path to SSH private key")
def setup(host, domain, app_name, port, user, key_path):
    """
    Set up a fresh Ubuntu server for hosting dbbasic-web apps.

    This will install Python, nginx, certbot, and configure systemd service.

    Example:
        dbbasic-deploy setup --host myserver.com --domain demo.dbbasic.com
    """
    try:
        setup_server(host, domain, app_name, port, user, key_path)
    except Exception as e:
        click.echo(f"Error during setup: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option("--host", required=True, help="Server hostname or IP")
@click.option("--domain", required=True, help="Domain name for the app")
@click.option("--app-name", default="app", help="Application name (default: app)")
@click.option("--port", default=3000, help="Port for uvicorn (default: 3000)")
@click.option("--user", default="root", help="SSH user (default: root)")
@click.option("--key", "key_path", help="Path to SSH private key")
@click.option("--path", "local_path", default=".", help="Local path to deploy (default: .)")
def push(host, domain, app_name, port, user, key_path, local_path):
    """
    Deploy your app to the server.

    This will upload your code, install dependencies, and restart the service.

    Example:
        dbbasic-deploy push --host myserver.com --domain demo.dbbasic.com
    """
    try:
        deploy_app(host, domain, app_name, port, user, key_path, local_path)
    except Exception as e:
        click.echo(f"Error during deployment: {e}", err=True)
        raise click.Abort()


@main.command()
@click.option("--host", required=True, help="Server hostname or IP")
@click.option("--domain", required=True, help="Domain name for SSL certificate")
@click.option("--email", help="Email for Let's Encrypt notifications")
@click.option("--user", default="root", help="SSH user (default: root)")
@click.option("--key", "key_path", help="Path to SSH private key")
def ssl(host, domain, email, user, key_path):
    """
    Set up SSL certificate with Let's Encrypt.

    Example:
        dbbasic-deploy ssl --host myserver.com --domain demo.dbbasic.com --email you@example.com
    """
    import paramiko

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    connect_kwargs = {"hostname": host, "username": user}
    if key_path:
        connect_kwargs["key_filename"] = key_path

    ssh.connect(**connect_kwargs)

    email_flag = f"--email {email}" if email else "--register-unsafely-without-email"
    command = f"certbot --nginx -d {domain} {email_flag} --non-interactive --agree-tos"

    click.echo(f"Setting up SSL for {domain}...")
    stdin, stdout, stderr = ssh.exec_command(command)
    exit_status = stdout.channel.recv_exit_status()

    output = stdout.read().decode()
    error = stderr.read().decode()

    if exit_status == 0:
        click.echo(output)
        click.echo(f"\n✓ SSL certificate installed successfully!")
        click.echo(f"Your app is now available at: https://{domain}")
    else:
        click.echo(f"Error: {error}", err=True)
        raise click.Abort()

    ssh.close()


if __name__ == "__main__":
    main()
