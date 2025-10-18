# This file is placed in the Public Domain.


"main commands"


import json


from tob.command import Commands, scanner
from tob.package import NAME
from tob.utility import md5sum


def cmd(event):
    event.reply(",".join(sorted(Commands.names)))


def md5(event):
    tbl = getmod("tbl")
    if tbl:
        event.reply(md5sum(tbl.__file__))
    else:
        event.reply("table is not there.")


def srv(event):
    import getpass
    name = getpass.getuser()
    event.reply(TXT % (NAME.upper(), name, name, name, NAME))


def tbl(event):
    Commands.names = {}
    scanner()
    event.reply("# This file is placed in the Public Domain.")
    event.reply("")
    event.reply("")
    event.reply('"lookup tables"')
    event.reply("")
    event.reply("")
    event.reply(f"NAMES = {json.dumps(Commands.names, indent=4, sort_keys=True)}")
    event.reply("")
    event.reply("")
    event.reply("MD5 = {")
    for module in scanner():
        event.reply(f'    "{module.__name__.split(".")[-1]}": "{md5sum(module.__file__)}",')
    event.reply("}")


TXT = """[Unit]
Description=%s
After=network-online.target

[Service]
Type=simple
User=%s
Group=%s
ExecStart=/home/%s/.local/bin/%s -s

[Install]
WantedBy=multi-user.target"""
