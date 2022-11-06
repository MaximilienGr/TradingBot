import logging


def setup_logger(logger):
    logger.setLevel(logging.DEBUG)

    sh = logging.StreamHandler()
    LOG_FORMAT = "%(asctime)s - %(message)s"
    formatter = logging.Formatter(LOG_FORMAT)
    sh.setFormatter(formatter)

    def decorate_emit(fn):
        # add methods we need to the class
        def new(*args):
            levelno = args[0].levelno
            if levelno >= logging.CRITICAL:
                color = "\x1b[31;1m"
            elif levelno >= logging.ERROR:
                color = "\x1b[31;1m"
            elif levelno >= logging.WARNING:
                color = "\x1b[33;1m"
            elif levelno >= logging.INFO:
                color = "\x1b[32;1m"
            elif levelno >= logging.DEBUG:
                color = "\x1b[35;1m"
            else:
                color = "\x1b[0m"
            # add colored *** in the beginning of the message
            args[0].msg = "{0}{1}\x1b[0m".format(color, args[0].msg)
            return fn(*args)

        return new

    sh.emit = decorate_emit(sh.emit)
    logger.addHandler(sh)


logger = logging.getLogger("TradingBot")
setup_logger(logger)
