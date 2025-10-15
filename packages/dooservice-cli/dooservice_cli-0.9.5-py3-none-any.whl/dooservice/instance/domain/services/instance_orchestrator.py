from typing import Dict

from dooservice.core.domain.entities.configuration import Instance
from dooservice.instance.domain.entities.instance_configuration import (
    InstanceEnvironment,
    InstancePaths,
)


class InstanceOrchestrator:
    """Service for orchestrating instance operations."""

    def prepare_instance_environment(
        self, name: str, instance_config: Instance
    ) -> InstanceEnvironment:
        """Prepare the environment configuration for an instance."""
        paths = InstancePaths.from_data_dir(instance_config.data_dir, name)

        env_vars = self._build_environment_variables(instance_config, paths)

        return InstanceEnvironment(name=name, env_vars=env_vars, paths=paths)

    def _build_environment_variables(
        self, instance_config: Instance, paths: InstancePaths
    ) -> Dict[str, str]:
        """Build environment variables from instance configuration."""
        env_vars = {}

        if instance_config.env_vars.ODOO_HTTP_PORT:
            env_vars["ODOO_HTTP_PORT"] = str(instance_config.env_vars.ODOO_HTTP_PORT)

        if instance_config.env_vars.ODOO_LONGPOLLING_PORT:
            env_vars["ODOO_LONGPOLLING_PORT"] = str(
                instance_config.env_vars.ODOO_LONGPOLLING_PORT
            )

        if instance_config.env_vars.DB_HOST:
            env_vars["DB_HOST"] = instance_config.env_vars.DB_HOST

        if instance_config.env_vars.DB_PORT:
            env_vars["DB_PORT"] = str(instance_config.env_vars.DB_PORT)

        if instance_config.env_vars.DB_USER:
            env_vars["DB_USER"] = instance_config.env_vars.DB_USER

        if instance_config.env_vars.DB_PASSWORD:
            env_vars["DB_PASSWORD"] = instance_config.env_vars.DB_PASSWORD

        if instance_config.env_vars.ADMIN_PASSWORD:
            env_vars["ADMIN_PASSWORD"] = instance_config.env_vars.ADMIN_PASSWORD

        if instance_config.env_vars.WORKERS:
            env_vars["WORKERS"] = str(instance_config.env_vars.WORKERS)

        env_vars["DATA_DIR"] = str(paths.data_dir)
        env_vars["ADDONS_PATH"] = str(paths.addons_dir)
        env_vars["LOGS_PATH"] = str(paths.logs_dir)

        return env_vars

    def generate_odoo_config(
        self, instance_env: InstanceEnvironment, instance_config: Instance
    ) -> str:
        """Generate odoo.conf content."""
        addons_paths = instance_env.get_addons_paths()
        addons_path_str = (
            ",".join(addons_paths) if addons_paths else "/mnt/extra-addons"
        )

        config_lines = [
            "[options]",
            f"addons_path = {addons_path_str}",
            "data_dir = /var/lib/odoo",
            "logfile = /var/log/odoo/odoo.log",
        ]

        if instance_config.env_vars.DB_HOST:
            config_lines.append(f"db_host = {instance_config.env_vars.DB_HOST}")

        if instance_config.env_vars.DB_PORT:
            config_lines.append(f"db_port = {instance_config.env_vars.DB_PORT}")

        if instance_config.env_vars.DB_USER:
            config_lines.append(f"db_user = {instance_config.env_vars.DB_USER}")

        if instance_config.env_vars.DB_PASSWORD:
            config_lines.append(f"db_password = {instance_config.env_vars.DB_PASSWORD}")

        if instance_config.env_vars.ADMIN_PASSWORD:
            config_lines.append(
                f"admin_passwd = {instance_config.env_vars.ADMIN_PASSWORD}"
            )

        if instance_config.env_vars.WORKERS:
            config_lines.append(f"workers = {instance_config.env_vars.WORKERS}")

        if instance_config.env_vars.LIMIT_MEMORY_SOFT:
            config_lines.append(
                f"limit_memory_soft = {instance_config.env_vars.LIMIT_MEMORY_SOFT}"
            )

        if instance_config.env_vars.LIMIT_MEMORY_HARD:
            config_lines.append(
                f"limit_memory_hard = {instance_config.env_vars.LIMIT_MEMORY_HARD}"
            )

        if instance_config.env_vars.LIMIT_REQUEST:
            config_lines.append(
                f"limit_request = {instance_config.env_vars.LIMIT_REQUEST}"
            )

        if instance_config.env_vars.LIMIT_TIME_CPU:
            config_lines.append(
                f"limit_time_cpu = {instance_config.env_vars.LIMIT_TIME_CPU}"
            )

        if instance_config.env_vars.LIMIT_TIME_REAL:
            config_lines.append(
                f"limit_time_real = {instance_config.env_vars.LIMIT_TIME_REAL}"
            )

        if instance_config.env_vars.MAX_CRON_THREADS:
            config_lines.append(
                f"max_cron_threads = {instance_config.env_vars.MAX_CRON_THREADS}"
            )

        if instance_config.env_vars.PROXY_MODE:
            config_lines.append(
                f"proxy_mode = {str(instance_config.env_vars.PROXY_MODE).lower()}"
            )

        if instance_config.env_vars.LIST_DB is not None:
            config_lines.append(
                f"list_db = {str(instance_config.env_vars.LIST_DB).lower()}"
            )

        return "\n".join(config_lines) + "\n"
