from typing import Any, Dict, List

from dooservice.core.domain.entities.configuration import (
    DooServiceConfiguration,
    Instance,
)


class ConfigurationValidator:
    def __init__(self):
        self._validation_errors: List[str] = []

    def validate(self, configuration: DooServiceConfiguration) -> bool:
        self._validation_errors.clear()

        self._validate_version(configuration.version)
        self._validate_instances(configuration.instances)
        self._validate_repositories(configuration.repositories)
        self._validate_domains(configuration.domains)

        return len(self._validation_errors) == 0

    def get_validation_errors(self) -> List[str]:
        return self._validation_errors.copy()

    def _validate_version(self, version: str) -> None:
        if not version:
            self._validation_errors.append("Version is required")
        elif version not in ["1.0"]:
            self._validation_errors.append(f"Unsupported version: {version}")

    def _validate_instances(self, instances: Dict[str, Instance]) -> None:
        if not instances:
            self._validation_errors.append("At least one instance must be defined")
            return

        for name, instance in instances.items():
            self._validate_instance(name, instance)

    def _validate_instance(self, name: str, instance: Instance) -> None:
        if not instance.odoo_version:
            self._validation_errors.append(
                f"Instance '{name}': odoo_version is required"
            )
        elif instance.odoo_version not in [
            "14.0",
            "14",
            "15.0",
            "15",
            "16.0",
            "16",
            "17.0",
            "17",
            "18.0",
            "18",
            "19",
            "19.0",
        ]:
            self._validation_errors.append(
                f"Instance '{name}': Unsupported Odoo version: {instance.odoo_version}"
            )

        if not instance.data_dir:
            self._validation_errors.append(f"Instance '{name}': data_dir is required")

        if not instance.paths.config:
            self._validation_errors.append(
                f"Instance '{name}': paths.config is required"
            )

        self._validate_instance_ports(name, instance)
        self._validate_instance_deployment(name, instance)

    def _validate_instance_ports(self, name: str, instance: Instance) -> None:
        if not instance.ports.http:
            self._validation_errors.append(f"Instance '{name}': ports.http is required")

        if not instance.ports.longpolling:
            self._validation_errors.append(
                f"Instance '{name}': ports.longpolling is required"
            )

    def _validate_instance_deployment(self, name: str, instance: Instance) -> None:
        if not instance.deployment:
            self._validation_errors.append(
                f"Instance '{name}': deployment configuration is required"
            )
            return

        if instance.deployment.type.value == "docker":
            if not instance.deployment.docker:
                self._validation_errors.append(
                    f"Instance '{name}': docker configuration is required "
                    f"when deployment type is 'docker'"
                )
            elif not instance.deployment.docker.web:
                self._validation_errors.append(
                    f"Instance '{name}': docker.web configuration is required"
                )

    def _validate_repositories(self, repositories: Dict[str, Any]) -> None:
        for name, repository in repositories.items():
            if not hasattr(repository, "url") or not repository.url:
                self._validation_errors.append(f"Repository '{name}': url is required")

            if not hasattr(repository, "branch") or not repository.branch:
                self._validation_errors.append(
                    f"Repository '{name}': branch is required"
                )

    def _validate_domains(self, domains: Any) -> None:
        if hasattr(domains, "base_domains") and domains.base_domains:
            for domain_name, domain in domains.base_domains.items():
                if not hasattr(domain, "name") or not domain.name:
                    self._validation_errors.append(
                        f"Domain '{domain_name}': name is required for base domains"
                    )
                if not hasattr(domain, "instance") or not domain.instance:
                    self._validation_errors.append(
                        f"Domain '{domain_name}': instance is required for base domains"
                    )
