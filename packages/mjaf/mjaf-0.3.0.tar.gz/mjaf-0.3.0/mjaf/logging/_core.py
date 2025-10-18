import logging
import logging.handlers
import pathlib
import sys
from typing import Annotated

import rich
import rich.traceback

from mjaf._utils.constants import LOG_LEVEL

log = logging.getLogger(__name__)

traceback_console = rich.console.Console(stderr=True)


# TODO: add options to use this
class PrintLogger:
    """
    https://stackoverflow.com/questions/14906764/how-to-redirect-stdout-to-both-file-and-console-with-scripting
    Writes the output from the print function to logs while still printing it to terminal
    """  # noqa E501

    def __init__(self, logger):
        self.terminal = sys.stdout
        self.log = logger
        # self.log = open(file, 'w')

    def write(self, message):
        self.terminal.write(message)
        # don't log extra extra newline from print statement
        if message != '\n':
            self.log.debug(message)

    def close(self):
        self.log.close()
        sys.stdout = open('/dev/stdout', 'w')

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        pass


class CustomFormatter(logging.Formatter):
    def __init__(self, *args, do_color=False, **kwargs):
        self.do_color = do_color

        super().__init__(*args, **kwargs)

    COLORS_BY_LEVEL = {
        logging.DEBUG: '34',  # Green
        logging.INFO: '26',  # Blue
        logging.WARNING: '220',  # Yellow
        logging.ERROR: '208',  # Orange
        logging.CRITICAL: '124',  # Red
    }

    def color_format(self, start_escape_code, end_escape_code):
        return (
            f"|0| %(asctime)s"
            f" |1| {start_escape_code}%(levelname)-8s{end_escape_code}"
            f" |2| %(name)s"
            f" |3| %(module)s:%(lineno)s %(funcName)s :: %(message)s"
        )

    def format(self, record: logging.LogRecord) -> str:
        start_escape_code = ''
        end_escape_code = ''

        if self.do_color:
            start_escape_code += (
                '\033[1;38;5;'
                + self.COLORS_BY_LEVEL[record.levelno]
                + 'm'
            )
            end_escape_code = '\033[m'

        formatter = logging.Formatter(
            self.color_format(
                start_escape_code,
                end_escape_code,
            ),
        )
        return formatter.format(record)


def set_handlers(
    logger_name: str = '',
    level: str | None = None,
    path: pathlib.Path | str | None = None,
    rotation_size: Annotated[int, 'MB'] = 10,
    rotations: int = 5,
    log_print_statements=False,
) -> None:

    level = level or LOG_LEVEL

    logger = logging.getLogger(logger_name)
    logger.propagate = False

    if path is not None:
        path = pathlib.Path(path).resolve()

        file_handler = logging.handlers.RotatingFileHandler(
            path,
            maxBytes=1000**2 * rotation_size,
            backupCount=rotations,
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(
            CustomFormatter(do_color=False),
        )

        logger.addHandler(file_handler)

    # >>> Prints to terminal
    # StreamHandler defaults to stderr
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(
        CustomFormatter(do_color=True),
    )
    # <<<

    logger.addHandler(stream_handler)

    # "specifies the lowest-severity log message a logger will handle"
    logger.setLevel(level)

    log.info('Logging configured successfully')
    log.info(f'{level=}')
    if path is not None:
        log.info(f'Logging to {path}')

    if log_print_statements:
        if isinstance(sys.stdout, PrintLogger):
            log.warning(
                'You already set log_print_statements=True'
                ', you probably don\'t want to do that twice',
            )
        sys.stdout = PrintLogger(logger)

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        logger.critical(
            'Uncaught exception',
            exc_info=(exc_type, exc_value, exc_traceback),
        )

        exception_traceback = rich.traceback.Traceback.from_exception(
            exc_type,
            exc_value,
            exc_traceback,
        )
        traceback_console.print(exception_traceback)

    sys.excepthook = handle_exception


if __name__ == '__main__':
    import mjaf
    mjaf.logging.set_handlers(
        __name__,
        level='DEBUG',
        log_print_statements=True,
    )
    mjaf.logging.set_handlers(
        'root',
        level='DEBUG',
        log_print_statements=True,
    )
    logging.getLogger(__name__).warning('test')
