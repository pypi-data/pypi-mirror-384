import os


def dropbox():
    path = os.path.expanduser("~/Dropbox/")
    if not os.path.isdir(path):
        path = "/Dropbox/"
    return path
