# This file is placed in the Public Domain.


"json serializer"


from json import JSONEncoder
from json import dump as jdump
from json import dumps as jdumps
from json import load as load
from json import loads as loads


class Encoder(JSONEncoder):

    def default(self, o):
        if isinstance(o, dict):
            return o.items()
        if isinstance(o, list):
            return iter(o)
        try:
            return JSONEncoder.default(self, o)
        except TypeError:
            try:
                return vars(o)
            except TypeError:
                return repr(o)


def dump(obj, fp, *args, **kw):
    kw["cls"] = Encoder
    jdump(obj, fp, *args, **kw)


def dumps(obj, *args, **kw):
    kw["cls"] = Encoder
    return jdumps(obj, *args, **kw)


def __dir__():
    return (
        'dump',
        'dumps',
        'load',
        'loads'
    )
