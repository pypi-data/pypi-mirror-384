import os
import pathlib
import sys
from datetime import datetime

from dotenv import find_dotenv, load_dotenv
from loguru import logger


def load_environment_from_dotenv() -> None:
    """
    Load environment variables from a .env file located in the current working directory.

    If a .env file is found, its contents are loaded into the environment.
    """
    env_file = pathlib.Path(find_dotenv(usecwd=True))
    if env_file.is_file():
        logger.trace('Loading environment from {env_file}', env_file=env_file)
        load_dotenv(env_file)
    else:
        logger.trace(f'.env not found in {env_file}', env_file=env_file.absolute())


def configure_json_log(log_directory: str|bool=False) -> None:
    """
    Configure JSON logging using the `loguru` logger.

    This function sets up structured JSON logging to a file, with the log file path
    determined by the `LOG_DIRECTORY` environment variable or the provided `log_directory` argument.
    If `LOG_DIRECTORY` is set to 'TRUE', the default directory 'log' is used.
    If it is set to 'FALSE', logging is skipped.

    Parameters
    ----------
    log_directory : str or bool, optional
        The directory where the log file should be saved. If set to `False`, logging is disabled
        unless overridden by the `LOG_DIRECTORY` environment variable.

    Environment Variables
    ---------------------
    LOG_DIRECTORY : str
        Overrides the `log_directory` argument when set. Special values:
        - 'TRUE': uses default directory 'log'
        - 'FALSE': disables logging

    Notes
    -----
    - The log file is named using the current timestamp in ISO format (without colons).
    - The log file is serialized in JSON format.
    - The directory is created if it does not exist.

    Examples
    --------
    >>> configure_json_log("logs")
    >>> os.environ["LOG_DIRECTORY"] = "TRUE"

    >>> configure_json_log(False)

    """
    if not log_directory:
        return

    script_name = pathlib.Path(pathlib.Path(sys.argv[0]))
    file_stem = script_name.stem if script_name.stem!='__main__' else script_name.parent.name + script_name.stem
    if 'PYTEST_CURRENT_TEST' in os.environ and os.environ.get('PYTEST_CURRENT_TEST'):
        pytest_current_test = os.environ.get('PYTEST_CURRENT_TEST').split('::')
        file_stem = pathlib.Path(pytest_current_test[0]).stem + pytest_current_test[1].replace('(call)', '').strip()

    env_log_directory = os.environ.get('LOG_DIRECTORY', log_directory)
    if isinstance(env_log_directory, bool):
        env_log_directory = pathlib.Path.cwd() / 'log'
    log_to_json = str(env_log_directory).upper().strip()!='FALSE'
    env_log_directory = env_log_directory if log_to_json and str(env_log_directory).upper().strip() != 'TRUE' else 'log'

    if log_to_json:
        log_directory = pathlib.Path(env_log_directory if env_log_directory else log_directory)
        if log_directory.is_file():
            logger.warning(f'LOG_DIRECTORY={log_directory} is a file. Skipping json logging')
            return
        log_directory.mkdir(exist_ok=True)

        log_start = datetime.now()
        timestamp = log_start.isoformat(timespec='seconds').replace(':', '')
        log_filename = log_directory / f'{file_stem}-{timestamp}.json'
        if log_filename.is_file():
            log_start_milliseconds = log_start.isoformat(timespec='milliseconds').replace(':', '')
            log_filename = log_filename.with_stem(f'{file_stem}-{log_start_milliseconds}')

        logger.debug(f'Logging json to {log_filename}')
        logger.add(log_filename, level=os.environ.get('LOG_LEVEL_JSON', 'TRACE'), serialize=True)
        if len(sys.argv) > 1:
            logger.info(f'argv={sys.argv[1:]}')
    else:
        logger.debug('Skipping json log. LOG_DIRECTORY is undefined.')


def configure_loglevel(log_format: str | None = None, level: str = 'INFO') -> None:
    """
    Configure the loguru logger with a specified log level and format.

    By default, sets the log level to INFO unless either:
    - The '--debug' flag is present in the command-line arguments (`sys.argv`), or
    - The environment variable DEBUG is set to 'TRUE' (case-insensitive).

    If debug mode is enabled, the log level is set to DEBUG and a filter is applied
    to suppress DEBUG logs from the 'ebm.model.file_handler' logger.

    Parameters
    ----------
    log_format : str, optional
        Custom format string for log messages. If not provided, the default format is used.
    level : str, optional
        Default log level to use when debug mode is not active. Defaults to 'INFO'.

    Returns
    -------
    None

    """
    logger.remove()
    options = {'level': level}
    if log_format:
        options['format'] = log_format

    # Accessing sys.argv directly since we want to figure out the log level before loading arguments with arg_parser.
    # Debug level may also be conveyed through environment variables, so read that from environ as well.
    if '--debug' in sys.argv or os.environ.get('DEBUG', '').upper() == 'TRUE':
        options['level'] = 'DEBUG'

    logger.add(sys.stderr,
               filter=lambda f: not (f['name'] == 'ebm.model.file_handler' and f['level'].name == 'DEBUG'),
               **options)


