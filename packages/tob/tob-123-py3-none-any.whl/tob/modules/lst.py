# This file is been placed in the Public Domain.


"available types"


from ..workdir import types


def lst(event):
    tps = types()
    if tps:
        event.reply(",".join([x.split(".")[-1].lower() for x in tps]))
    else:
        event.reply("no data yet.")
