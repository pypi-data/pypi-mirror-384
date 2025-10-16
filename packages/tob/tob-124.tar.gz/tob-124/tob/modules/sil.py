# This file is placed in the Public Domain.


"enable silence mode"


from ..brokers import Fleet
 

def sil(event):
    bot = Fleet.get(event.orig)
    bot.silent = True
    event.reply("ok")


def lou(event):
    bot = Fleet.get(event.orig)
    bot.silent = False
    event.reply("ok")
