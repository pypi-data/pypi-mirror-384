import re
from javonet.sdk.configuration.Config import Config
from javonet.sdk.configuration.ConfigsDictionary import ConfigsDictionary
from javonet.sdk.configuration.ConfigPriority import ConfigPriority
from javonet.sdk.configuration.configResolvers.ConfigResolver import ConfigResolver
from javonet.sdk.tools.ActivationHelper import ActivationHelper

class ConnectionStringConfigResolver(ConfigResolver):
    @staticmethod
    def add_configs(priority, connection_string_source):
        if not connection_string_source or connection_string_source.strip() == "":
            raise ValueError("Connection string source cannot be null or empty.")

        normalized = connection_string_source.replace("\r\n", "\n").replace("\r", "\n")
        lines = [line.strip() for line in normalized.split("\n") if line.strip()]

        for line in lines:
            if line.startswith("#") or line.startswith("//"):
                continue
            if line.lower().startswith("licensekey"):
                ConnectionStringConfigResolver._set_license_key(line)
                continue
            try:
                key_values = ConnectionStringConfigResolver._parse_key_values(line)
                config_name = key_values.get("name")
                runtime_value = key_values.get("runtime")

                if not config_name or config_name.strip() == "":
                    raise ValueError("Missing or empty config name.")
                if not runtime_value or runtime_value.strip() == "":
                    raise ValueError("Missing or empty runtime.")

                runtime_name = ConfigResolver.try_parse_runtime(runtime_value)
                host_value = key_values.get("host")
                connection_data = ConfigResolver.build_connection_data(host_value)
                plugins = key_values.get("plugins", "")
                modules = key_values.get("modules", "")

                config = Config(runtime_name, connection_data, plugins, modules)
                ConfigsDictionary.add_config(config_name, priority, config)
            except Exception as ex:
                print(f"Failed to parse config line: '{line}'. Reason: {ex}")
                raise

    @staticmethod
    def _set_license_key(line):
        eq = line.find("=")
        if 0 < eq < len(line) - 1:
            value_portion = line[eq + 1:].strip()
            semicolon = value_portion.find(";")
            if semicolon >= 0:
                value_portion = value_portion[:semicolon].strip()
            hash_idx = value_portion.find("#")
            if hash_idx >= 0:
                value_portion = value_portion[:hash_idx].strip()
            slashes = value_portion.find("//")
            if slashes >= 0:
                value_portion = value_portion[:slashes].strip()
            ActivationHelper.TemporaryLicenseKey = value_portion

    @staticmethod
    def _parse_key_values(line):
        result = {}
        segments = [seg.strip() for seg in line.split(";") if seg.strip()]
        for segment in segments:
            eq = segment.find("=")
            if eq <= 0 or eq == len(segment) - 1:
                print(f"Ignoring malformed token '{segment}' in line: {line}")
                continue
            key = segment[:eq].strip().lower()
            value = segment[eq + 1:].strip()
            if key:
                result[key] = value
        return result
