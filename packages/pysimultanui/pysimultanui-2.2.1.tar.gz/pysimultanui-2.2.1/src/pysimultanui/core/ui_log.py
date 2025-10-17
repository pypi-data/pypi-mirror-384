import logging
from nicegui import ui, app
from .. import user_manager


class LogElementHandler(logging.Handler):
    """A logging handler that emits messages to a log element."""

    def __init__(self, element: ui.log, level: int = logging.NOTSET) -> None:
        self.element = element
        super().__init__(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.setFormatter(formatter)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            self.element.push(msg)
        except Exception:
            self.handleError(record)


class UILog:
    def __init__(self):
        self.log = None
        self.handler = None
        self.logger = logging.getLogger(self.user.name)

    @property
    def user(self):
        return user_manager.users[app.storage.user['username']]

    def ui_content(self):
        self.log = ui.log(max_lines=100).classes('w-full h-full')
        # self.log.style = "font-family: monospace; white-space: pre-wrap;"
        self.handler = LogElementHandler(self.log)

        loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]

        for logger in loggers:
            if logger.name.startswith(('pkg_resources', 'concurrent', 'asyncio', 'websockets', 'websockets.protocol',
                                       'urllib3', 'requests', 'httpx', 'httpcore', 'aiohttp', 'fastapi', 'nicegui', 'http',
                                       'uvicorn', 'starlette', 'sqlalchemy', 'uvicorn', 'socket', 'engineio', 'charset',
                                       'markdown')):
                continue
            else:
                logger.addHandler(self.handler)

        self.logger = logging.getLogger(self.user.name)
        self.logger.addHandler(self.handler)
        self.logger.setLevel(logging.DEBUG)

    def __del__(self):
        self.logger.removeHandler(self.handler)
        for logger in logging.root.manager.loggerDict.values():
            try:
                logger.removeHandler(self.handler)
            except:
                pass

    def clear(self):
        self.log.clear()
