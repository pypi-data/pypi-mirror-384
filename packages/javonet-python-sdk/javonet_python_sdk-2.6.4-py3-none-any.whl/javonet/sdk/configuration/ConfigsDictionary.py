from collections import defaultdict

class ConfigsDictionary:
    _configurations_collection = defaultdict(dict)

    @staticmethod
    def add_config(name, priority, config):
        if not name or name.strip() == "":
            print("Config name cannot be null or whitespace. Skipping add.")
            return
        if config is None:
            print("Config instance is null. Skipping add.")
            return

        per_priority = ConfigsDictionary._configurations_collection[name]

        if priority in per_priority:
            print(f"Config with name `{name}` and priority `{priority}` already exists. It will not be added or updated.")
            return

        per_priority[priority] = config
        print(f"Added configuration `{name}` with priority `{priority}` and parameters {config}")

    @staticmethod
    def get_config(name):
        if not name or name.strip() == "":
            raise ValueError("Config name cannot be null or whitespace")

        per_priority = ConfigsDictionary._configurations_collection.get(name)
        if per_priority is None or len(per_priority) == 0:
            raise ValueError(f"Configuration {name} not found")

        selected_priority = min(per_priority.keys(), key=lambda k: k.value)
        config = per_priority[selected_priority]
        print(f"Retrieved configuration `{name}` with priority `{selected_priority}` and parameters {config}")
        return config

    @staticmethod
    def clear_configs():
        ConfigsDictionary._configurations_collection.clear()
