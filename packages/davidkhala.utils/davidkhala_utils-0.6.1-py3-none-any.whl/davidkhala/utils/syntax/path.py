import os
from pathlib import Path
from typing import Optional


def join(*path_tokens):
    return os.path.join(path_tokens[0], *path_tokens[1:])

def resolve(__file__, relative_path:Optional[str]=""):
    return (Path(__file__) / relative_path).resolve()
def homedir():
    return os.path.expanduser('~')


HOME = homedir()


def dirname(file):
    return os.path.dirname(file)


def home_resolve(*path_tokens):
    return join(HOME, *path_tokens)


def delete(_path):
    Path(_path).unlink(True)
