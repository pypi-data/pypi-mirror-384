# This file is placed in the Public Domain.


"show modules"


from tob.package import modules


def mod(event):
    event.reply(",".join(modules()))
