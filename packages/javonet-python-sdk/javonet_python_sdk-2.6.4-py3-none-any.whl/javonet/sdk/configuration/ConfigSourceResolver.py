import os
import json
from argparse import ArgumentError

from javonet.sdk.configuration.ConfigsDictionary import ConfigsDictionary
from javonet.sdk.configuration.configResolvers.JsonConfigResolver import JsonConfigResolver
from javonet.sdk.configuration.configResolvers.YamlConfigResolver import YamlConfigResolver
from javonet.sdk.configuration.configResolvers.ConnectionStringConfigResolver import ConnectionStringConfigResolver

class ConfigSourceResolver:
    @staticmethod
    def add_configs(priority, config_source):
        print(f"Adding config from source: {config_source} with priority '{priority}'")
        config_string = ConfigSourceResolver._get_config_source_as_string(config_source)
        ConfigSourceResolver._parse_configs_and_add_to_collection(priority, config_string)

    @staticmethod
    def get_config(config_name):
        print(f"Retrieving config {config_name}")
        return ConfigsDictionary.get_config(config_name)

    @staticmethod
    def clear_configs():
        ConfigsDictionary.clear_configs()

    @staticmethod
    def _get_config_source_as_string(config_source):
        if not config_source or config_source.strip() == "":
            raise ValueError("Config source cannot be null or whitespace.")
        env_value = os.environ.get(config_source)
        if env_value and env_value.strip() != "":
            config_source = env_value
        if os.path.isfile(config_source):
            with open(config_source, "r", encoding="utf-8") as f:
                config_source = f.read()
        return config_source.strip()

    @staticmethod
    def _parse_configs_and_add_to_collection(priority, config_string):
        # Try JSON
        try:
            json_object = json.loads(config_string)
            JsonConfigResolver.add_configs(priority, json_object)
            return
        except json.JSONDecodeError:
            pass
        except Exception as ex:
            print("Failed to parse config source as JSON: " + str(ex))

        # Try YAML
        try:
            YamlConfigResolver.add_configs(priority, config_string)
            return
        except ArgumentError:
            pass
        except Exception as ex:
            print("Failed to parse config source as YAML: " + str(ex))

        # Try connection string
        try:
            ConnectionStringConfigResolver.add_configs(priority, config_string)
            return
        except Exception as ex:
            print("Failed to parse config source as connection string: " + str(ex))

        raise ValueError("Config source is not valid JSON, YAML, or connection string format:\n" + config_string)

