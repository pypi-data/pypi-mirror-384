import logging
from pathlib import Path


def is_gz_file(filepath):
    with open(filepath, 'rb') as test_f:
        return test_f.read(2) == b'\x1f\x8b'


def move_sub_dirs(src: Path, dst: Path):
    """
    Move all subdirectories of a source directory into the target directory
    """
    if not src.is_dir():
        logging.warning(f'Source does not exist or is not a directory: {src}')
        return

    if not dst.is_dir():
        logging.warning(f'Source does not exist or is not a directory: {src}')
        return

    subdir: Path
    for partition in src.iterdir():
        if partition.is_dir():
            partition.rename(dst / partition.name)


def get_file_ext(filename: str) -> str:
    return filename.split(".")[-1].lower()
