from typing import ClassVar, Any

from pydantic_settings import BaseSettings, PydanticBaseSettingsSource, YamlConfigSettingsSource, EnvSettingsSource, CliSettingsSource

from fmtr.tools.data_modelling_tools import CliRunMixin
from fmtr.tools.path_tools import PackagePaths, Path


class YamlScriptConfigSettingsSource(YamlConfigSettingsSource):
    """

    Customer source for reading YAML *Script* (as opposed to plain YAML) configuration files.

    """

    def _read_file(self, file_path: Path) -> dict[str, Any]:
        """

        Use our own Path class to read YAML Script.

        """
        data = Path(file_path).read_yaml() or {}
        return data


class Base(BaseSettings, CliRunMixin):
    """

    Base class for settings configuration using Pydantic BaseSettings.
    Provides functionality for setting up and customizing sources for retrieving configuration values.
    Defines sources for configuration through environment variables, CLI arguments, YAML files.

    """

    paths: ClassVar = PackagePaths()

    @classmethod
    def settings_customise_sources(
            cls,
            settings_cls: type[BaseSettings],
            init_settings: PydanticBaseSettingsSource,
            env_settings: PydanticBaseSettingsSource,
            dotenv_settings: PydanticBaseSettingsSource,
            file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """

        Define priority and additional sources. Note: the earlier items have higher priority.

        """

        sources = (
            init_settings,
            CliSettingsSource(settings_cls, cli_parse_args=True),
            EnvSettingsSource(settings_cls, env_prefix=cls.get_env_prefix()),
            YamlScriptConfigSettingsSource(settings_cls, yaml_file=cls.paths.settings),
        )

        return sources

    @classmethod
    def get_env_prefix(cls):
        """

        Get environment variable prefix, which depends on whether the package is a namespace/singleton.

        """
        if cls.paths.is_namespace:
            stem = f'{cls.paths.org}_{cls.paths.name}'
        else:
            stem = f'{cls.paths.name}'

        prefix = f'{stem}_'.upper()
        return prefix

    @property
    def version(self):
        """

        Read in version file.

        """
        from fmtr.tools import version
        return version.read_path(self.paths.version)
