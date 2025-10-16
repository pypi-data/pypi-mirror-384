from argparse import ArgumentError

import yaml
from javonet.sdk.configuration.Config import Config
from javonet.sdk.configuration.ConfigsDictionary import ConfigsDictionary
from javonet.sdk.configuration.configResolvers.ConfigResolver import ConfigResolver
from javonet.sdk.tools.ActivationHelper import ActivationHelper

class YamlConfigResolver(ConfigResolver):
    @staticmethod
    def add_configs(priority, yaml_string):
        if not yaml_string or yaml_string.strip() == "":
            raise ValueError("YAML string cannot be null or empty.")

        try:
            data = yaml.safe_load(yaml_string)
        except Exception as ex:
            raise ValueError(f"Failed to parse YAML: {ex}")

        if not isinstance(data, dict):
            raise ArgumentError("Root YAML node must be a mapping.")


        license_key = data.get("licenseKey")
        if isinstance(license_key, str):
            ActivationHelper.TemporaryLicenseKey = license_key.strip()

        configs = data.get("configurations")
        if not isinstance(configs, dict):
            raise ArgumentError("YAML must contain 'configurations' mapping.")

        for config_name, cfg in configs.items():
            if not isinstance(config_name, str) or not config_name.strip():
                print("Skipping entry with empty config name.")
                continue
            if not isinstance(cfg, dict):
                print(f"Skipping '{config_name}': value is not a mapping.")
                continue
            try:
                runtime_value = YamlConfigResolver._get_required_string(cfg, "runtime")
                runtime_name = ConfigResolver.try_parse_runtime(runtime_value)

                host = YamlConfigResolver._get_optional_string(cfg, "host")
                connection_data = ConfigResolver.build_connection_data(host)

                plugins = YamlConfigResolver._get_optional_string(cfg, "plugins")
                modules = YamlConfigResolver._get_optional_string(cfg, "modules")

                config = Config(runtime_name, connection_data, plugins, modules)
                ConfigsDictionary.add_config(config_name, priority, config)
            except Exception as ex:
                print(f"Failed to add config '{config_name}': {ex}")

    @staticmethod
    def _get_required_string(mapping, key):
        value = mapping.get(key)
        if not isinstance(value, str) or value.strip() == "":
            raise ValueError(f"Missing or invalid '{key}' property.")
        return value.strip()

    @staticmethod
    def _get_optional_string(mapping, key):
        value = mapping.get(key)
        if isinstance(value, str):
            return value
        return ""