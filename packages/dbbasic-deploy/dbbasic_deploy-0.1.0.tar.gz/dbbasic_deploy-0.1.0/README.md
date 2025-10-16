# dbbasic-deploy

Simple SSH deployment tool for [dbbasic-web](https://github.com/askrobots/dbbasic-web) apps to Ubuntu servers.

No Docker, no Ansible, no complexity. Just Python, SSH, nginx, and systemd.

## Features

- ✅ Deploys to Ubuntu 22.04/24.04 LTS
- ✅ Automatic nginx reverse proxy setup
- ✅ Let's Encrypt SSL certificates
- ✅ systemd service management
- ✅ Python 3.12 virtual environments
- ✅ Zero-downtime deployments via systemd restart

## Requirements

**Local machine:**
- Python 3.10+
- SSH access to your server

**Remote server:**
- Ubuntu 22.04 or 24.04 LTS
- Root access (or sudo user)
- Domain pointing to server IP

## Installation

### macOS

```bash
# Install Python 3 (if not already installed)
brew install python3

# Install dbbasic-deploy
pip3 install dbbasic-deploy
```

### Windows 11

```powershell
# Install Python from python.org or use winget
winget install Python.Python.3.12

# Install dbbasic-deploy
pip install dbbasic-deploy
```

**Note:** On Windows, you'll also need an SSH client. Windows 11 includes OpenSSH by default, but you may need to enable it:
```powershell
# Enable OpenSSH (run as Administrator)
Add-WindowsCapability -Online -Name OpenSSH.Client
```

### Ubuntu/Debian

```bash
# Install Python and pip
sudo apt update
sudo apt install python3 python3-pip

# Install dbbasic-deploy
pip3 install dbbasic-deploy
```

### Install from source

```bash
git clone https://github.com/askrobots/dbbasic-deploy
cd dbbasic-deploy
pip install -e .
```

## Quick Start

### 1. Set up a fresh server

```bash
dbbasic-deploy setup \
  --host myserver.com \
  --domain demo.dbbasic.com
```

This will:
- Install Python 3.12, nginx, certbot
- Create systemd service
- Configure nginx reverse proxy
- Set up firewall (ufw)

### 2. Deploy your app

```bash
cd your-dbbasic-web-app
dbbasic-deploy push \
  --host myserver.com \
  --domain demo.dbbasic.com
```

This will:
- Upload your code
- Install dependencies from requirements.txt
- Restart the service
- Verify it's running

### 3. Enable HTTPS

```bash
dbbasic-deploy ssl \
  --host myserver.com \
  --domain demo.dbbasic.com \
  --email you@example.com
```

This will:
- Get Let's Encrypt certificate
- Configure nginx for SSL
- Set up auto-renewal

Done! Your app is live at `https://demo.dbbasic.com`

## Usage

### Setup a new server

```bash
dbbasic-deploy setup --host SERVER --domain DOMAIN [OPTIONS]

Options:
  --host TEXT       Server hostname or IP (required)
  --domain TEXT     Domain name for the app (required)
  --app-name TEXT   Application name (default: app)
  --port INTEGER    Port for uvicorn (default: 3000)
  --user TEXT       SSH user (default: root)
  --key TEXT        Path to SSH private key
```

### Deploy/update your app

```bash
dbbasic-deploy push --host SERVER --domain DOMAIN [OPTIONS]

Options:
  --host TEXT       Server hostname or IP (required)
  --domain TEXT     Domain name for the app (required)
  --app-name TEXT   Application name (default: app)
  --port INTEGER    Port for uvicorn (default: 3000)
  --user TEXT       SSH user (default: root)
  --key TEXT        Path to SSH private key
  --path TEXT       Local path to deploy (default: .)
```

### Set up SSL

```bash
dbbasic-deploy ssl --host SERVER --domain DOMAIN [OPTIONS]

Options:
  --host TEXT       Server hostname or IP (required)
  --domain TEXT     Domain name for SSL certificate (required)
  --email TEXT      Email for Let's Encrypt notifications
  --user TEXT       SSH user (default: root)
  --key TEXT        Path to SSH private key
```

## Multiple Apps on One Server

You can host multiple apps by using different `--app-name` and `--port` values:

```bash
# App 1
dbbasic-deploy setup --host myserver.com --domain app1.com --app-name app1 --port 3001
dbbasic-deploy push --host myserver.com --domain app1.com --app-name app1 --port 3001

# App 2
dbbasic-deploy setup --host myserver.com --domain app2.com --app-name app2 --port 3002
dbbasic-deploy push --host myserver.com --domain app2.com --app-name app2 --port 3002
```

## File Structure on Server

```
/var/www/app/              # App directory
├── venv/                   # Python virtual environment
├── requirements.txt        # Dependencies
├── api.py                  # Your app code
└── data/                   # Persistent data

/etc/systemd/system/app.service    # systemd service
/etc/nginx/sites-available/app     # nginx config
```

## Debugging

Check service status:
```bash
ssh user@server 'systemctl status app'
```

View logs:
```bash
ssh user@server 'journalctl -u app -f'
```

Check nginx:
```bash
ssh user@server 'nginx -t'
ssh user@server 'systemctl status nginx'
```

## How It Works

1. **Setup** creates a systemd service that runs uvicorn
2. **Push** uploads code via SFTP and restarts the service
3. **SSL** runs certbot to get Let's Encrypt certificate
4. nginx acts as reverse proxy (handles SSL, proxies to uvicorn on port 3000)

## Comparison

| Feature | dbbasic-deploy | Docker/Coolify | Ansible | Capistrano |
|---------|----------------|----------------|---------|------------|
| Complexity | Low | Medium | High | Medium |
| Setup time | 2 min | 10 min | 30 min | 15 min |
| Multi-distro | No (Ubuntu) | Yes | Yes | Yes |
| Learning curve | Minimal | Medium | Steep | Medium |
| Dependencies | Python | Docker | Many | Ruby |

## Limitations

- **Ubuntu only** - Tested on 22.04 and 24.04 LTS
- **Single server** - Not for clusters or load balancing
- **Simple deploys** - No blue-green, canary, or complex strategies
- **SSH access required** - Need root or sudo access

For production apps with complex requirements, consider Docker/Kubernetes or proper configuration management tools.

## Contributing

Issues and PRs welcome at https://github.com/askrobots/dbbasic-deploy

## License

MIT
