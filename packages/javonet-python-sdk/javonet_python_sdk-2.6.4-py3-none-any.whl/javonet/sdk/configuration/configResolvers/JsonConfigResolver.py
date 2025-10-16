import json
from javonet.sdk.configuration.Config import Config
from javonet.sdk.configuration.ConfigsDictionary import ConfigsDictionary
from javonet.sdk.configuration.ConfigPriority import ConfigPriority
from javonet.sdk.configuration.configResolvers.ConfigResolver import ConfigResolver
from javonet.sdk.tools.ActivationHelper import ActivationHelper

class JsonConfigResolver(ConfigResolver):
    @staticmethod
    def add_configs(priority, json_object):
        if json_object is None:
            raise ValueError("json_object cannot be None")
        if not isinstance(json_object, dict):
            raise ValueError("Root JSON element must be a dict/object.")

        license_key = json_object.get("licenseKey")
        if isinstance(license_key, str):
            ActivationHelper.TemporaryLicenseKey = license_key.strip()

        configs = json_object.get("configurations")
        if not isinstance(configs, dict):
            raise ValueError("JSON must contain 'configurations' object.")

        for config_name, cfg in configs.items():
            try:
                if not isinstance(cfg, dict):
                    raise ValueError("Configuration value must be an object/dict.")

                runtime_value = JsonConfigResolver._get_required_string(cfg, "runtime")
                runtime_name = ConfigResolver.try_parse_runtime(runtime_value)

                host = JsonConfigResolver._get_optional_string(cfg, "host")
                connection_data = ConfigResolver.build_connection_data(host)

                plugins = JsonConfigResolver._get_optional_string(cfg, "plugins")
                modules = JsonConfigResolver._get_optional_string(cfg, "modules")

                config = Config(runtime_name, connection_data, plugins, modules)
                ConfigsDictionary.add_config(config_name, priority, config)
            except Exception as ex:
                print(f"Failed to add config '{config_name}': {ex}")

    @staticmethod
    def _get_required_string(obj, property):
        value = obj.get(property)
        if not isinstance(value, str) or value.strip() == "":
            raise ValueError(f"Missing or invalid '{property}' property.")
        return value.strip()

    @staticmethod
    def _get_optional_string(obj, property):
        value = obj.get(property)
        if isinstance(value, str):
            return value
        return ""