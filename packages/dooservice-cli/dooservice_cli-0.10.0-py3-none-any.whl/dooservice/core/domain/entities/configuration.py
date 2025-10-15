from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union


class DeploymentType(Enum):
    SYSTEM = "system"
    DOCKER = "docker"


class SourceType(Enum):
    GIT = "git"
    ZIP = "zip"
    LOCAL = "local"
    TAR_GZ = "tar.gz"


class RepositoryType(Enum):
    GIT = "git"
    GITHUB = "github"
    GITLAB = "gitlab"


class SSLProvider(Enum):
    LETSENCRYPT = "letsencrypt"
    CLOUDFLARE = "cloudflare"
    ZEROSSL = "zerossl"
    OTHER = "other"


class BackupFormat(Enum):
    ZIP = "zip"
    DUMP = "dump"


class Frequency(Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


class RestartPolicy(Enum):
    NO = "no"
    ON_FAILURE = "on-failure"
    ALWAYS = "always"
    UNLESS_STOPPED = "unless-stopped"


@dataclass
class HealthCheck:
    test: List[str]
    interval: str = "30s"
    timeout: str = "30s"
    retries: int = 3
    start_period: str = "0s"


@dataclass
class DockerContainer:
    image: str
    container_name: str
    restart_policy: RestartPolicy = RestartPolicy.NO
    user: Optional[str] = None
    volumes: List[str] = field(default_factory=list)
    networks: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    ports: List[str] = field(default_factory=list)
    depends_on: List[str] = field(default_factory=list)
    healthcheck: Optional[HealthCheck] = None


@dataclass
class DockerDeployment:
    web: DockerContainer
    db: Optional[DockerContainer] = None


@dataclass
class Deployment:
    type: DeploymentType
    docker: Optional[DockerDeployment] = None


@dataclass
class Paths:
    config: str
    addons: str = ""
    logs: str = ""
    filestore: str = ""


@dataclass
class Ports:
    http: str
    longpolling: str
    expose: List[str] = field(default_factory=list)


@dataclass
class EnvVars:
    ODOO_HTTP_PORT: Optional[int] = None
    ODOO_LONGPOLLING_PORT: Optional[int] = None
    DB_HOST: Optional[str] = None
    DB_PORT: Optional[int] = None
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    ADMIN_PASSWORD: Optional[str] = None
    WORKERS: Optional[int] = None
    LIMIT_MEMORY_SOFT: Optional[int] = None
    LIMIT_MEMORY_HARD: Optional[int] = None
    LIMIT_REQUEST: Optional[int] = None
    LIMIT_TIME_CPU: Optional[int] = None
    LIMIT_TIME_REAL: Optional[int] = None
    MAX_CRON_THREADS: Optional[int] = None
    PROXY_MODE: Optional[bool] = None
    LIST_DB: Optional[bool] = None
    TIMEZONE: Optional[str] = None
    LETSENCRYPT_EMAIL: Optional[str] = None
    CLOUDFLARE_API_TOKEN: Optional[str] = None
    CLOUDFLARE_ZONE_ID: Optional[str] = None
    ZEROSSL_API_KEY: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    GITHUB_WEBHOOK_SECRET: Optional[str] = None


@dataclass
class Domain:
    base: str
    subdomain: str = ""
    use_root_domain: bool = False


@dataclass
class Retention:
    days: int = 30
    max_backups: int = 10


@dataclass
class Schedule:
    frequency: Frequency
    time: str = "02:00"


@dataclass
class AutoBackup:
    enabled: bool = False
    format: BackupFormat = BackupFormat.ZIP
    schedule: Optional[Schedule] = None


@dataclass
class Backup:
    enabled: bool = True
    output_dir: str = "/opt/dooservice/backups"
    format: BackupFormat = BackupFormat.ZIP
    retention: Retention = field(default_factory=Retention)
    auto_backup: AutoBackup = field(default_factory=AutoBackup)


@dataclass
class SnapshotRetention:
    days: int = 60
    max_snapshots: int = 100


@dataclass
class Snapshot:
    enabled: bool = True
    default_storage_dir: str = "/opt/dooservice/snapshots"
    retention: SnapshotRetention = field(default_factory=SnapshotRetention)


@dataclass
class GitHubWatcher:
    instance: str
    action: Union[str, List[str]]
    enabled: bool = True


@dataclass
class GitHubConfig:
    auto_watch: bool = True
    default_action: Union[str, List[str]] = "pull+restart"
    watchers: List[GitHubWatcher] = field(default_factory=list)
    exclude_instances: List[str] = field(default_factory=list)


@dataclass
class Repository:
    source_type: SourceType
    path: str
    type: RepositoryType
    url: str
    branch: str
    ssh_key_path: str = ""
    submodules: bool = False
    depth: int = 1  # Shallow clone depth (1=latest only, 0=full)
    github: Optional[GitHubConfig] = None


@dataclass
class CloudflareTunnel:
    name: str
    domain: str
    enabled: bool = True


@dataclass
class CloudflareProvider:
    api_token: str
    account_id: str
    zone_id: str
    tunnel: CloudflareTunnel


@dataclass
class SSLProviderConfig:
    email: Optional[str] = None
    api_token: Optional[str] = None
    zone_id: Optional[str] = None
    api_key: Optional[str] = None


@dataclass
class BaseDomain:
    name: str
    instance: str
    ssl_provider: Optional[SSLProvider] = None
    ssl: bool = True
    force_ssl: bool = True
    redirect_www: bool = False
    hsts: bool = True
    cname_target: Optional[str] = None
    dns_challenge: bool = False


@dataclass
class DomainsConfig:
    default_provider: SSLProvider = SSLProvider.LETSENCRYPT
    default_ssl: bool = True
    default_force_ssl: bool = True
    default_redirect_www: bool = False
    default_hsts: bool = True
    providers: Dict[str, SSLProviderConfig] = field(default_factory=dict)
    base_domains: Dict[str, BaseDomain] = field(default_factory=dict)
    cloudflare: Optional[CloudflareProvider] = None


@dataclass
class GitHubOAuth:
    client_id: str
    client_secret: str
    redirect_uri: str = "http://localhost:8080/auth/callback"
    scopes: List[str] = field(
        default_factory=lambda: ["repo", "read:user", "admin:public_key"]
    )


@dataclass
class GitHubWebhook:
    enabled: bool = True
    default_host: str = "localhost"
    default_port: int = 8080
    default_secret: str = ""
    auto_start: bool = False


@dataclass
class GitHubIntegration:
    enabled: bool = True
    oauth: GitHubOAuth = field(default_factory=GitHubOAuth)
    webhook: GitHubWebhook = field(default_factory=GitHubWebhook)


@dataclass
class InstanceSnapshot:
    enabled: bool = True
    storage_dir: str = ""
    include_backup_by_default: bool = True
    retention: SnapshotRetention = field(default_factory=SnapshotRetention)


@dataclass
class InstanceAutoBackup:
    enabled: bool = True
    db_name: str = ""


@dataclass
class Instance:
    odoo_version: str
    data_dir: str
    paths: Paths
    ports: Ports
    env_vars: EnvVars
    deployment: Deployment
    db_version: str = "17"  # Default PostgreSQL version
    auto_backup: InstanceAutoBackup = field(default_factory=InstanceAutoBackup)
    repositories: Dict[str, Repository] = field(default_factory=dict)
    python_dependencies: List[str] = field(default_factory=list)
    snapshot: InstanceSnapshot = field(default_factory=InstanceSnapshot)


@dataclass
class InstanceDefaults:
    """Default configuration values for instances."""

    odoo_version: str = "19.0"
    db_version: str = "17"
    auto_backup: Optional[InstanceAutoBackup] = None
    data_dir: str = "/opt/odoo-data/${name}"
    paths: Optional[Paths] = None
    ports: Optional[Ports] = None
    repositories: Dict[str, Repository] = field(default_factory=dict)
    env_vars: Optional[EnvVars] = None
    python_dependencies: List[str] = field(default_factory=list)
    snapshot: Optional[InstanceSnapshot] = None
    deployment: Optional[Deployment] = None


@dataclass
class Defaults:
    """Global defaults section."""

    instance: InstanceDefaults = field(default_factory=InstanceDefaults)


@dataclass
class ConfigurationImport:
    """Represents an import directive in configuration files."""

    path: str
    resolved_path: Optional[Path] = None


@dataclass
class DooServiceConfiguration:
    version: str = "1.0"
    imports: List[str] = field(default_factory=list)
    defaults: Defaults = field(default_factory=Defaults)
    domains: DomainsConfig = field(default_factory=DomainsConfig)
    backup: Backup = field(default_factory=Backup)
    snapshot: Snapshot = field(default_factory=Snapshot)
    github: GitHubIntegration = field(default_factory=GitHubIntegration)
    repositories: Dict[str, Repository] = field(default_factory=dict)
    instances: Dict[str, Instance] = field(default_factory=dict)
