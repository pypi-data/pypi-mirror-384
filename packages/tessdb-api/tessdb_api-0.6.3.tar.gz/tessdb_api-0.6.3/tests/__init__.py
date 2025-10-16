from enum import StrEnum
import logging
import shlex
import subprocess


log = logging.getLogger(__name__.split(".")[-1])

class DbSize(StrEnum):
    SMALL = "anew"
    MEDIUM = "medium"
    LARGE = "big"


def copy_file(src: str, dst: str):
    cmd = shlex.split(f"cp -f {src} {dst}")
    log.info("copying %s into %s", src, dst)
    subprocess.run(cmd)
