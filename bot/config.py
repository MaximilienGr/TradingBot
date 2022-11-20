import logging

from bot.helpers.utils import _ansi_style


class Config:
    @classmethod
    def setup_config(self):

        streamHandler = logging.StreamHandler()
        streamHandler.addFilter(ContextFilter())
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
            handlers=[streamHandler],
        )


class ContextFilter(logging.Filter):
    def filter(self, record):
        if "indicators" in record.name:
            record.msg = _ansi_style(record.msg, "yellow")
            record.name = record.name.split(".")[-1]
        elif record.name == "root":
            record.msg = _ansi_style(record.msg, "bold")
        return record
