# DooService CLI

> Professional command-line tool for managing Odoo instances with Docker

DooService CLI provides a declarative, configuration-first approach to managing complex Odoo deployments. Define your entire infrastructure in YAML and manage everything from the command line.

## 🚀 Quick Start

```bash
# 1. Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install DooService CLI
uv tool install dooservice-cli

# 3. Check system dependencies
dooservice doctor

# 4. Initialize project
dooservice init

# 5. Edit configuration
nano dooservice.yml

# 6. Create and start instance
dooservice create production
```

## ✨ Key Features

- 🐳 **Docker-native** - Full Docker & Docker Compose integration
- 📝 **Configuration-first** - Define everything in YAML
- 🐍 **Python dependencies** - Auto-install packages in containers
- 🌐 **Cloudflare tunnels** - Automatic domain and DNS management
- 📦 **Git repositories** - Auto-sync custom addons
- 💾 **Backup & snapshots** - Database backup and restore
- 🔄 **Smart workflows** - Deploy, rebuild, destroy with data preservation
- 🪟 **Cross-platform** - Works on Windows, Linux, and macOS

## 📦 Installation

### Using uv (Recommended)

[uv](https://docs.astral.sh/uv/) is a fast, modern Python package manager. Install it first:

```bash
# On macOS and Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# On Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Then install DooService CLI:

```bash
uv tool install dooservice-cli
```

### Alternative: Using pipx

```bash
pipx install dooservice-cli
```

### Alternative: Using pip

```bash
pip install --user dooservice-cli
```

### Development Installation

```bash
git clone https://github.com/apiservicesac/dooservice-cli-py.git
cd dooservice-cli-py
uv tool install --editable .
```

## 🎯 Commands Reference

### System Commands

```bash
# Initialize configuration structure
dooservice init [-p|--path DIR] [--minimal] [-f|--force]

# Check system health and dependencies
dooservice doctor
```

### Instance Lifecycle

```bash
# Create instance (NAME is required)
dooservice create NAME [-c|--config FILE]

# Start instance (NAME optional, interactive selection if omitted)
dooservice start [NAME] [-c|--config FILE]

# Stop instance (NAME optional, interactive selection if omitted)
dooservice stop [NAME] [-c|--config FILE]

# Delete instance (NAME optional, interactive selection if omitted)
dooservice delete [NAME] [-c|--config FILE] [--force] [--keep-data] [--keep-domain]

# Restart instance
dooservice restart [NAME] [-c|--config FILE]

# List all instances
dooservice list [-c|--config FILE]

# Show instance status
dooservice status [NAME] [-c|--config FILE]

# View logs
dooservice logs [NAME] [--service SERVICE] [--follow] [--tail N] [-c|--config FILE]

# Execute command in container
dooservice exec NAME COMMAND [--user USER] [--workdir DIR] [-c|--config FILE]

# Sync repositories and configuration
dooservice sync NAME [-c|--config FILE] [--no-restart]

# Update Odoo modules
dooservice update-modules NAME -d|--database DATABASE [-m|--modules MODULE]... [-a|--all] [-p|--http-port PORT] [-c|--config FILE]
```

### Quick Aliases

```bash
# Shortcuts for common commands
dooservice ls [-c|--config FILE]        # Alias for 'list'
dooservice ps [-c|--config FILE]        # Alias for 'list'
dooservice up [NAME] [-c|--config FILE] # Alias for 'start'
dooservice down [NAME] [-c|--config FILE] # Alias for 'stop'
dooservice rm [NAME] [-c|--config FILE] [...] # Alias for 'delete'
```

### Workflow Commands

```bash
# Deploy: create + start + domain setup
dooservice deploy [NAME] [-c|--config FILE]

# Rebuild: stop + delete (keep data/domain) + create + start + domain sync
dooservice rebuild [NAME] [-c|--config FILE]

# Destroy: stop + delete
dooservice destroy [NAME] [-c|--config FILE] [--force]
```

### Repository Management

```bash
# List repositories for an instance
dooservice repo list INSTANCE_NAME [--repo-name NAME] [-c|--config FILE]

# Show detailed status of a repository
dooservice repo status INSTANCE_NAME REPO_NAME [-c|--config FILE]

# Synchronize repositories
dooservice repo sync INSTANCE_NAME [--repo-name NAME] [-q|--quiet] [--test] [-c|--config FILE]
```

### Backup Management

```bash
# Create backup
dooservice backup create INSTANCE_NAME [-d|--database NAME] [--format zip|dump] [-o|--output DIR] [-c|--config FILE] [-v|--verbose]

# Test backup connection
dooservice backup test INSTANCE_NAME [-d|--database NAME] [-c|--config FILE]

# List available databases
dooservice backup databases INSTANCE_NAME [-c|--config FILE]
```

### Tunnel Management

```bash
# Initialize Cloudflare tunnel from configuration
dooservice tunnel init [-c|--config FILE] [-v|--verbose] [--force]

# Delete tunnel and associated DNS records
dooservice tunnel delete [-c|--config FILE] [-v|--verbose]

# Check tunnel status
dooservice tunnel status [-c|--config FILE]

# Show tunnel logs
dooservice tunnel logs [-n|--tail N] [-f|--follow] [-c|--config FILE]

# Restart tunnel container
dooservice tunnel restart [-c|--config FILE]

# Stop tunnel container
dooservice tunnel stop [-c|--config FILE]
```

### Domain Management

```bash
# Enable domain (create DNS records and tunnel config)
dooservice domain enable NAME [-c|--config FILE] [-v|--verbose]

# Disable domain (remove DNS and disconnect tunnel)
dooservice domain disable NAME [-c|--config FILE] [-v|--verbose]

# Sync domain with instance (connect to tunnel network)
dooservice domain sync NAME [-c|--config FILE] [-v|--verbose]

# List configured domains
dooservice domain list [-c|--config FILE]

# Check domain status
dooservice domain status NAME [-c|--config FILE]

# Test domain connectivity and response
dooservice domain test NAME [-c|--config FILE]

# Show logs for domain's associated instance
dooservice domain logs NAME [-n|--tail N] [-f|--follow] [-c|--config FILE]
```

### Configuration Management

```bash
# Validate configuration file
dooservice config validate FILE

# Load and display configuration
dooservice config load FILE [--no-validate]

# Create new configuration
dooservice config create FILE [--no-validate]

# Convert configuration format
dooservice config convert INPUT [--output FILE]
```

## ⚙️ Configuration Guide

### Basic Structure

```yaml
version: '1.0'

# Optional: Import other configuration files
imports:
  - config/defaults.yml
  - config/domains.yml
  - config/repositories.yml

# Global defaults (optional)
defaults:
  instance:
    odoo_version: '19.0'
    db_version: '17'

# Cloudflare integration (optional)
domains:
  default_provider: 'cloudflare'
  providers:
    cloudflare:
      api_token: 'YOUR_TOKEN'
      account_id: 'YOUR_ACCOUNT_ID'
      tunnels:
        main-tunnel:
          zone_id: 'YOUR_ZONE_ID'
          domain: 'example.com'
  base_domains:
    app.example.com:
      instance: 'production'

# Backup configuration (optional)
backup:
  enabled: true
  output_dir: 'odoo-data/backups'
  format: 'zip'

# Snapshot configuration (optional)
snapshot:
  enabled: true
  default_storage_dir: 'odoo-data/snapshots'
  retention:
    days: 60
    max_snapshots: 100

# Repository definitions (optional)
repositories:
  custom-addons:
    source_type: 'git'
    type: 'github'
    url: 'https://github.com/your-org/odoo-addons.git'
    branch: 'main'

# Instance definitions (required)
instances:
  production:
    odoo_version: '19.0'
    data_dir: 'odoo-data/${name}'

    ports:
      http: 8069
      longpolling: 8072

    repositories:
      custom-addons: {}

    python_dependencies:
      - 'pandas>=1.5.0'
      - 'requests>=2.28.0'

    env_vars:
      DB_HOST: 'db_${name}'
      DB_USER: 'odoo'
      DB_PASSWORD: 'secure_password'
      ADMIN_PASSWORD: 'admin_password'
      WORKERS: 4

    deployment:
      type: 'docker'
      docker:
        web:
          image: 'odoo:${odoo_version}'
          container_name: 'web_${name}'
          restart_policy: 'unless-stopped'
        db:
          image: 'postgres:${db_version}'
          container_name: 'db_${name}'
          restart_policy: 'unless-stopped'
```

### Configuration Sections

#### 1. Global Defaults (`defaults`)

Define default values inherited by all instances:

```yaml
defaults:
  instance:
    # Versions
    odoo_version: '19.0'              # Odoo version
    db_version: '17'                  # PostgreSQL version

    # Directories
    data_dir: 'odoo-data/${name}'     # Data directory (relative path)

    # Auto Backup
    auto_backup:
      enabled: false
      db_name: '${name}_db'

    # Paths (inside data_dir)
    paths:
      config: '${data_dir}/etc/odoo.conf'
      addons: '${data_dir}/addons'
      logs: '${data_dir}/logs'
      filestore: '${data_dir}/filestore'

    # Default ports
    ports:
      http: 8069
      longpolling: 8072
      expose: []                      # Options: [], ['web'], ['db'], ['web', 'db']

    # Default repositories
    repositories: {}

    # Environment variables
    env_vars:
      # Network
      ODOO_HTTP_PORT: 8069
      ODOO_LONGPOLLING_PORT: 8072

      # Database
      DB_HOST: 'db_${name}'
      DB_PORT: 5432
      DB_USER: 'odoo'
      DB_PASSWORD: 'odoo'
      ADMIN_PASSWORD: 'admin'

      # Performance
      WORKERS: 2
      LIMIT_MEMORY_SOFT: 2147483648   # 2GB
      LIMIT_MEMORY_HARD: 2684354560   # 2.5GB
      LIMIT_REQUEST: 8192
      LIMIT_TIME_CPU: 60
      LIMIT_TIME_REAL: 120
      MAX_CRON_THREADS: 2

      # General
      PROXY_MODE: true
      LIST_DB: false
      TIMEZONE: 'America/Lima'

    # Python packages to auto-install
    python_dependencies: []

    # Snapshot settings
    snapshot:
      enabled: true
      storage_dir: '${data_dir}/snapshots'
      include_backup_by_default: true
      retention:
        days: 60
        max_snapshots: 20

    # Deployment configuration
    deployment:
      type: 'docker'
      docker:
        web:
          image: 'odoo:${odoo_version}'
          container_name: 'web_${name}'
          restart_policy: 'unless-stopped'
          user: 'root'
          volumes:
            - '${paths.addons}:/mnt/extra-addons'
            - '${paths.config}:/etc/odoo/odoo.conf'
            - '${paths.logs}:/var/log/odoo'
            - '${paths.filestore}:/var/lib/odoo'
          networks:
            - 'net_${name}'
          ports:
            - '${env_vars.ODOO_HTTP_PORT}:8069'
            - '${env_vars.ODOO_LONGPOLLING_PORT}:8072'
          depends_on:
            - 'db_${name}'
          environment:
            TZ: '${env_vars.TIMEZONE}'
          healthcheck:
            test: ["CMD", "curl", "-f", "http://localhost:8069/web/health"]
            interval: "30s"
            timeout: "10s"
            retries: 3
            start_period: "40s"

        db:
          image: 'postgres:${db_version}'
          container_name: 'db_${name}'
          restart_policy: 'unless-stopped'
          user: 'root'
          volumes:
            - '${data_dir}/postgresql:/var/lib/postgresql/data'
          networks:
            - 'net_${name}'
          ports:
            - '${env_vars.DB_PORT}:5432'
          environment:
            TZ: '${env_vars.TIMEZONE}'
            POSTGRES_USER: '${env_vars.DB_USER}'
            POSTGRES_PASSWORD: '${env_vars.DB_PASSWORD}'
            POSTGRES_DB: 'postgres'
          healthcheck:
            test: ["CMD-SHELL", "pg_isready -U ${env_vars.DB_USER}"]
            interval: "10s"
            timeout: "5s"
            retries: 5
            start_period: "10s"
```

#### 2. Domains Configuration (`domains`)

Configure Cloudflare tunnels and domain mappings:

```yaml
domains:
  # Global domain settings
  default_provider: 'cloudflare'      # Only cloudflare supported
  default_ssl: true                   # Enable SSL by default
  default_force_ssl: true             # Force HTTPS redirect
  default_redirect_www: true          # Redirect www to non-www
  default_hsts: true                  # Enable HSTS header

  # Cloudflare provider configuration
  providers:
    cloudflare:
      api_token: 'YOUR_API_TOKEN'     # Cloudflare API token (required)
      account_id: 'YOUR_ACCOUNT_ID'   # Cloudflare account ID (required)

      # Tunnel definitions
      tunnels:
        main-tunnel:
          zone_id: 'YOUR_ZONE_ID'     # Cloudflare zone ID
          domain: 'example.com'       # Root domain
          enabled: true               # Enable tunnel

  # Domain to instance mappings
  base_domains:
    app.example.com:
      instance: 'production'          # Instance name (required)

    dev.example.com:
      instance: 'development'

    test.example.com:
      instance: 'testing'
```

**Cloudflare Setup Requirements:**
1. Create API token with permissions: `Account:Cloudflare Tunnel:Edit`, `Zone:DNS:Edit`
2. Get Account ID from Cloudflare Dashboard
3. Get Zone ID from domain's Overview page

#### 3. Backup Configuration (`backup`)

Global backup settings:

```yaml
backup:
  enabled: true                       # Enable backup system
  output_dir: 'odoo-data/backups'     # Backup storage directory
  format: 'zip'                       # Format: 'zip' or 'dump'

  # Retention policy
  retention:
    days: 30                          # Keep backups for N days (0=unlimited)
    max_backups: 10                   # Max backup files (0=unlimited)

  # Automatic backups
  auto_backup:
    enabled: false                    # Enable scheduled backups
    format: 'zip'                     # Backup format
    schedule:
      frequency: 'daily'              # Options: daily, weekly, monthly
      time: '02:00'                   # Time in HH:MM format (24h)
```

#### 4. Snapshot Configuration (`snapshot`)

Global snapshot settings:

```yaml
snapshot:
  enabled: true                                    # Enable snapshot system
  default_storage_dir: 'odoo-data/snapshots'       # Snapshot storage

  # Retention policy
  retention:
    days: 60                                       # Keep for N days
    max_snapshots: 100                             # Max total snapshots
```

#### 5. Repositories (`repositories`)

Define Git repositories for Odoo addons:

```yaml
repositories:
  # Basic repository
  custom-addons:
    source_type: 'git'                # Type: git, zip, local, tar.gz
    type: 'github'                    # Provider: github, gitlab, git
    url: 'https://github.com/org/repo.git'
    branch: 'main'                    # Branch or tag
    submodules: false                 # Clone submodules

  # Private repository (SSH)
  private-addons:
    source_type: 'git'
    type: 'git'
    url: 'git@github.com:org/private.git'
    branch: 'main'

  # Specific commit
  stable-addons:
    source_type: 'git'
    type: 'github'
    url: 'https://github.com/org/addons.git'
    commit: 'abc123def'               # Use commit hash instead of branch
```

#### 6. Instances (`instances`)

Define Odoo instances (inherits from defaults):

```yaml
instances:
  production:
    # Override Odoo version
    odoo_version: '19.0'

    # Override data directory
    data_dir: 'odoo-data/${name}'

    # Override ports
    ports:
      http: 8069
      longpolling: 8072
      expose: []                      # Expose ports: [], ['web'], ['db'], ['web', 'db']

    # Attach repositories (reference from global repositories)
    repositories:
      custom-addons: {}               # Use default config
      private-addons:
        path: '/mnt/custom-addons'    # Override mount path

    # Python packages to auto-install
    python_dependencies:
      - 'pandas>=1.5.0'
      - 'requests>=2.28.0'
      - 'pillow>=9.0.0'

    # Environment variables (merged with defaults)
    env_vars:
      DB_HOST: 'db_${name}'
      DB_USER: 'odoo'
      DB_PASSWORD: 'secure_password_here'
      ADMIN_PASSWORD: 'admin_password_here'
      WORKERS: 4
      TIMEZONE: 'America/Lima'

    # Override deployment (optional, uses defaults if not specified)
    deployment:
      type: 'docker'
      docker:
        web:
          image: 'odoo:${odoo_version}'
          container_name: 'web_${name}'
          # ... full docker config
        db:
          image: 'postgres:${db_version}'
          container_name: 'db_${name}'
          # ... full docker config
```

### Variable Substitution

Variables are replaced automatically:

- `${name}` - Instance name
- `${odoo_version}` - Odoo version
- `${db_version}` - PostgreSQL version
- `${data_dir}` - Data directory
- `${paths.config}` - Config file path
- `${paths.addons}` - Addons directory path
- `${paths.logs}` - Logs directory path
- `${paths.filestore}` - Filestore directory path
- `${env_vars.VARIABLE}` - Any environment variable

### Modular Configuration

Split large configurations into multiple files:

```yaml
# dooservice.yml (main file)
version: '1.0'

imports:
  - config/defaults.yml
  - config/domains.yml
  - config/repositories.yml
  - config/backups.yml
```

```yaml
# config/defaults.yml
defaults:
  instance:
    odoo_version: '19.0'
    # ... other defaults
```

```yaml
# config/domains.yml
domains:
  providers:
    cloudflare:
      api_token: '${CLOUDFLARE_API_TOKEN}'
      # ... domain config
```

## 🐍 Python Dependencies

Automatically install Python packages during instance creation:

```yaml
instances:
  production:
    python_dependencies:
      - 'pandas>=1.5.0'
      - 'requests>=2.28.0'
      - 'pillow>=9.0.0'
```

**How it works:**
1. Create instance → containers created but stopped
2. Start web container temporarily
3. Install packages with `pip3` (uses `--break-system-packages` for Odoo 18+)
4. Stop web container
5. Instance ready with dependencies installed

**Features:**
- Auto-detects Odoo version for correct pip flags
- Executes as root user in container
- Progress tracking with spinners
- Continues even if some packages fail

## 🪟 Cross-Platform Support

Works on **Windows, Linux, and macOS**:

```yaml
# Configuration (same on all platforms)
data_dir: 'odoo-data/${name}'

# Windows result: odoo-data\production
# Linux/Mac result: odoo-data/production
```

**Requirements:**
- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Python 3.11+
- Git (for repository sync)

## 📚 Common Workflows

### Initial Setup

```bash
# 1. Check system
dooservice doctor

# 2. Initialize configuration
dooservice init

# 3. Edit configuration
nano dooservice.yml

# 4. Validate
dooservice config validate dooservice.yml

# 5. Create instance
dooservice create production
```

### Daily Operations

```bash
# Start instance
dooservice start production

# View logs
dooservice logs production --follow

# Check status
dooservice status production

# Stop instance
dooservice stop production
```

### Maintenance

```bash
# Sync repositories (update code)
dooservice sync production

# Rebuild instance (recreate containers, keep data)
dooservice rebuild production

# Create backup
dooservice backup create production --database production_db

# Update Odoo modules
dooservice update-modules production -d production_db --all
```

### Cloudflare Setup

```bash
# 1. Initialize tunnel from configuration
dooservice tunnel init

# 2. Enable a domain (connects to instance and creates DNS records)
dooservice domain enable app.example.com

# 3. Check domain status
dooservice domain status app.example.com

# 4. Test domain connectivity
dooservice domain test app.example.com

# 5. View instance logs for the domain
dooservice domain logs app.example.com --follow
```

## 🏗️ Architecture

Built with Clean Architecture principles:

```
dooservice/
├── core/              # Configuration management
├── instance/          # Instance lifecycle
├── backup/            # Backup operations
├── repository/        # Git repository management
├── domains/           # Cloudflare integration
└── shared/            # Common utilities
```

## 🤝 Contributing

Contributions welcome! Please see our [contributing guidelines](CONTRIBUTING.md).

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [GitHub Wiki](https://github.com/apiservicesac/dooservice-cli-py/wiki)
- **Issues**: [GitHub Issues](https://github.com/apiservicesac/dooservice-cli-py/issues)
- **Discussions**: [GitHub Discussions](https://github.com/apiservicesac/dooservice-cli-py/discussions)

---

**Made with ❤️ by API SERVICE SAC**
