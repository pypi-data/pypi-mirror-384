from google_services_client_api.src.utils.logger import LoggerSingleton

class Config:
    ENABLE_LOGS = True

    @classmethod
    def update_configs(cls, configs: dict[str, any]):
        cls.ENABLE_LOGS = configs.get('enable_logs', cls.ENABLE_LOGS)
        
        LoggerSingleton.set_logger_state(cls.ENABLE_LOGS)