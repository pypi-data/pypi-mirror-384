# This file is placed in the Public Domain.


"working directory"


import datetime
import os
import pathlib


j = os.path.join


class Workdir:

    name = __file__.rsplit(os.sep, maxsplit=2)[-2]
    wdr  = ""


def cdir(path):
    pth = pathlib.Path(path)
    pth.parent.mkdir(parents=True, exist_ok=True)


def fqn(obj):
    kin = str(type(obj)).split()[-1][1:-2]
    if kin == "type":
        kin = f"{obj.__module__}.{obj.__name__}"
    return kin


def getpath(obj):
    return store(ident(obj))


def ident(obj):
    return j(fqn(obj), *str(datetime.datetime.now()).split())


def long(name):
    split = name.split(".")[-1].lower()
    res = name
    for names in types():
        if split == names.split(".")[-1].lower():
            res = names
            break
    return res


def moddir():
    assert Workdir.wdr
    return j(Workdir.wdr, "mods")


def pidfile(filename):
    if os.path.exists(filename):
        os.unlink(filename)
    path2 = pathlib.Path(filename)
    path2.parent.mkdir(parents=True, exist_ok=True)
    with open(filename, "w", encoding="utf-8") as fds:
        fds.write(str(os.getpid()))


def pidname(name):
    assert Workdir.wdr
    return j(Workdir.wdr, f"{name}.pid")


def setwd(name, path=""):
    path = path or os.path.expanduser(f"~/.{name}")
    Workdir.wdr = Workdir.wdr or path
    skel()


def skel():
    result = ""
    if not os.path.exists(store()):
        pth = pathlib.Path(store())
        pth.mkdir(parents=True, exist_ok=True)
        pth = pathlib.Path(moddir())
        pth.mkdir(parents=True, exist_ok=True)
        result =  str(pth)
    return result


def store(pth=""):
    assert Workdir.wdr
    return j(Workdir.wdr, "store", pth)


def strip(pth, nmr=2):
    return j(pth.split(os.sep)[-nmr:])


def types():
    skel()
    return os.listdir(store())


def __dir__():
    return (
        'Workdir',
        'cdir',
        'fqn',
        'getpath',
        'ident',
        'j',
        'long',
        'moddir',
        'pidfile',
        'pidname',
        'setwd',
        'skel',
        'store',
        'strip',
        'types'
    )
