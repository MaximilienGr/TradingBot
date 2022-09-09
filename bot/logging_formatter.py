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


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def print_BOLD(message):
    print(f"{bcolors.BOLD} {message} {bcolors.ENDC}")


def print_OKBLUE(message):
    print(f"{bcolors.OKBLUE} {message} {bcolors.ENDC}")


def print_OKGREEN(message):
    print(f"{bcolors.OKGREEN} {message} {bcolors.ENDC}")


# print(f"{bcolors.HEADER}Warning: No active frommets remain. Continue?")
# print(f"{bcolors.OKBLUE}Warning: No active frommets remain. Continue?") #####
# print(f"{bcolors.OKCYAN}Warning: No active frommets remain. Continue?")
# print(f"{bcolors.OKGREEN}Warning: No active frommets remain. Continue?") #####
# print(f"{bcolors.WARNING}Warning: No active frommets remain. Continue?")
# print(f"{bcolors.FAIL}Warning: No active frommets remain. Continue?")
# print(f"{bcolors.ENDC}Warning: No active frommets remain. Continue?")
# print(f"{bcolors.BOLD}Warning: No active frommets remain. Continue?")
# print(f"{bcolors.UNDERLINE}Warning: No active frommets remain. Continue?")


logger = logging.getLogger("TradingBot")
setup_logger(logger)
