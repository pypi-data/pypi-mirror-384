# This file is placed in the Public Domain.


"utilities"


import hashlib
import importlib.util
import logging
import os
import sys
import time
import _thread


FORMATS = [
    "%Y-%M-%D %H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d-%m",
    "%m-%d",
]


LEVELS = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warning': logging.WARNING,
    'warn': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL,
}


class Formatter(logging.Formatter):

    def format(self, record):
        record.module = record.module.upper()
        return logging.Formatter.format(self, record)


def elapsed(seconds, short=True):
    txt = ""
    nsec = float(seconds)
    if nsec < 1:
        return f"{nsec:.2f}s"
    yea     = 365 * 24 * 60 * 60
    week    = 7 * 24 * 60 * 60
    nday    = 24 * 60 * 60
    hour    = 60 * 60
    minute  = 60
    yeas    = int(nsec / yea)
    nsec   -= yeas * yea
    weeks   = int(nsec / week)
    nsec   -= weeks * week
    nrdays  = int(nsec / nday)
    nsec   -= nrdays * nday
    hours   = int(nsec / hour)
    nsec   -= hours * hour
    minutes = int(nsec / minute)
    nsec   -= int(minute * minutes)
    sec     = int(nsec)
    if yeas:
        txt += f"{yeas}y"
    if weeks:
        nrdays += weeks * 7
    if nrdays:
        txt += f"{nrdays}d"
    if short and txt:
        return txt.strip()
    if hours:
        txt += f"{hours}h"
    if minutes:
        txt += f"{minutes}m"
    if sec:
        txt += f"{sec}s"
    txt = txt.strip()
    return txt


def extract_date(daystr):
    daystr = daystr.encode('utf-8', 'replace').decode("utf-8")
    res = time.time()
    for fmat in FORMATS:
        try:
            res = time.mktime(time.strptime(daystr, fmat))
            break
        except ValueError:
            pass
    return res


def fntime(daystr):
    datestr = " ".join(daystr.split(os.sep)[-2:])
    datestr = datestr.replace("_", " ")
    if "." in datestr:
        datestr, rest = datestr.rsplit(".", 1)
    else:
        rest = ""
    timed = time.mktime(time.strptime(datestr, "%Y-%m-%d %H:%M:%S"))
    if rest:
        timed += float("." + rest)
    return float(timed)


def importer(name, pth):
    if not os.path.exists(pth):
        return
    try:
        spec = importlib.util.spec_from_file_location(name, pth)
        if not spec or not spec.loader:
            return
        mod = importlib.util.module_from_spec(spec)
        if not mod:
            return
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        logging.info("load %s", pth)
        return mod
    except Exception as ex:
        logging.exception(ex)
        _thread.interrupt_main()


def level(loglevel="debug"):
    if loglevel != "none":
        datefmt = "%H:%M:%S"
        format_short = "%(module).3s %(message)-76s"
        ch = logging.StreamHandler()
        ch.setLevel(LEVELS.get(loglevel))
        formatter = Formatter(fmt=format_short, datefmt=datefmt)
        ch.setFormatter(formatter)
        logger = logging.getLogger()
        logger.addHandler(ch)


def md5sum(path):
    with open(path, "r", encoding="utf-8") as file:
        txt = file.read().encode("utf-8")
        return hashlib.md5(txt).hexdigest()


def spl(txt):
    try:
        result = txt.split(",")
    except (TypeError, ValueError):
        result = [
            txt,
        ]
    return [x for x in result if x]


def __dir__():
    return (
        'cdir',
        'elapsed',
        'extract_date',
        'fntime',
        'importer',
        'level',
        'md5sum',
        'spl'
    )
