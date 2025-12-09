class SettingsModel:
    def __init__(self):
        self.ai_server = ""
        self.model = ""
        self.api_key = ""
        self.auto_start = False

    def load_settings(self, settings_dict):
        self.ai_server = settings_dict.get("ai_server", self.ai_server)
        self.model = settings_dict.get("model", self.model)
        self.api_key = settings_dict.get("api_key", self.api_key)
        self.auto_start = settings_dict.get("auto_start", self.auto_start)

    def to_dict(self):
        return {
            "ai_server": self.ai_server,
            "model": self.model,
            "api_key": self.api_key,
            "auto_start": self.auto_start,
        }