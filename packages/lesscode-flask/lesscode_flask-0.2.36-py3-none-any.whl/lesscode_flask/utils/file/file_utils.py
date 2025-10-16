import os
from os.path import dirname


def check_or_create_dir(path):
    if not os.path.exists(dirname(path)):
        os.makedirs(dirname(path))
    return path
