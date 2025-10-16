class Config:
    def __init__(self, runtime, connection_data, plugins="", modules=""):
        self.runtime = runtime
        self.connection_data = connection_data
        self.plugins = plugins
        self.modules = modules

    def __str__(self):
        parts = []
        parts.append(f"Runtime: {self.runtime}")

        if self.connection_data is not None:
            parts.append(f"Host: {self.connection_data}")

        if self.plugins.strip():
            parts.append(f"Plugins: {self.plugins}")

        if self.modules.strip():
            parts.append(f"Modules: {self.modules}")

        return ", ".join(parts)
