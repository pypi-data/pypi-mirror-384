# This file is placed in the Public Domain.


"clean namespace"


class Object:

    def __contains__(self, key):
        return key in dir(self)

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __str__(self):
        return str(self.__dict__)


def construct(obj, *args, **kwargs):
    if args:
        val = args[0]
        if isinstance(val, zip):
            update(obj, dict(val))
        elif isinstance(val, dict):
            update(obj, val)
        else:
            update(obj, vars(val))
    if kwargs:
        update(obj, kwargs)


def items(obj):
    if isinstance(obj, dict):
        return obj.items()
    return obj.__dict__.items()


def keys(obj):
    if isinstance(obj, dict):
        return obj.keys()
    return obj.__dict__.keys()


def update(obj, data, empty=True):
    for key, value in items(data):
        if not empty and not value:
            continue
        setattr(obj, key, value)


def values(obj):
    if isinstance(obj, dict):
        return obj.values()
    return obj.__dict__.values()


def __dir__():
    return (
        'Object',
        'construct',
        'items',
        'keys',
        'update',
        'values'
    )
