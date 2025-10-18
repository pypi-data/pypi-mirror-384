import logging

class AgentixLogger:
    def __init__(self, logger: logging.Logger, task_key: str = None):
        self.task_key = task_key
        self.logger = logger

    def set_task_key(self, task_key: str):
        self.task_key = task_key

    def _prefix(self, msg: str):
        return f"[{self.task_key}] | {msg}" if self.task_key else msg

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(self._prefix(msg), *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(self._prefix(msg), *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(self._prefix(msg), *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(self._prefix(msg), *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(self._prefix(msg), *args, **kwargs)

    def set_task_key(self, task_key: str):
        self.task_key = task_key