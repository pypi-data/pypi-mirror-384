import os
import pathlib

from loguru import logger

def make_unique_path(path: pathlib.Path):
    path = pathlib.Path(path)
    counter = 1
    new_path = path

    while new_path.exists():
        new_path = path.with_stem(f"{path.stem}_{counter}")
        counter += 1

    return new_path


def file_is_writable(output_file: pathlib.Path) -> bool:
    if not output_file.is_file():
        # If the parent directory is writable we should be good to go
        return os.access(output_file.parent, os.W_OK)

    access = os.access(output_file, os.W_OK)
    if not access:
        logger.error(f'Permission denied: {output_file}. The file is not writable.')
        return False

    # It is not enough to check that the file is writable in Windows. We must also check that it is possible to open
    # the file
    try:
        with output_file.open('a'):
            pass
    except PermissionError as ex:
        # Unable to open a file that is reported as writable by the operating system. In that case it is a good chance
        # that the file is already open. Error log our assumption and return False
        logger.error(str(ex) + '. Is the file already open?')
        return False
    return True