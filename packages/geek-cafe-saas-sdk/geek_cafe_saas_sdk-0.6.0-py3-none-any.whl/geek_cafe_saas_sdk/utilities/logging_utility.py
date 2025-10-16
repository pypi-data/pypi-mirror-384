from aws_lambda_powertools import Logger
from geek_cafe_saas_sdk.utilities.environment_variables import (
    EnvironmentVariables,
)


LOG_LEVEL = EnvironmentVariables.get_logging_level()


class LoggingUtility:
    def __init__(self, service=None) -> None:
        self.logger: Logger
        self.logger = Logger(service=service)
        self.logger.setLevel(LOG_LEVEL)

    @staticmethod
    def get_logger(
        service: str | None = None, level: str | None | int = None
    ) -> Logger:
        if level is None:
            level = LOG_LEVEL
        logger = Logger(service=service)
        logger.setLevel(level)
        return logger

    @staticmethod
    def build_message(
        source: str,
        action: str,
        message: str | None = None,
        metric_filter: str | None = None,
    ) -> dict:
        """
        Build a formatted message for logging
        Args:
            source (str): _description_
            action (str): _description_
            message (str, optional): _description_. Defaults to None.
            metric_filter (str, optional): _description_. Defaults to None.

        Returns:
            dict: _description_
        """
        response = {
            "source": source,
            "action": action,
            "details": message,
            "metric_filter": metric_filter,
        }
        return response


class LogLevels:
    def __init__(self) -> None:
        pass

    CRITICAL = 50
    FATAL = CRITICAL
    ERROR = 40
    WARNING = 30
    WARN = WARNING
    INFO = 20
    DEBUG = 10
    NOTSET = 0
