T O B
=====


**NAME**

|
| ``tob`` - bot in reverse !
|

**SYNOPSIS**

|
| ``tob <cmd> [key=val] [key==val]``
| ``tob -cvaw [init=mod1,mod2]``
| ``tob -d``
| ``tob -s``
|


**DESCRIPTION**


``TOB`` has all you need to program a unix cli program, such as disk perisistence for configuration files, event handler to handle the client/server connection, easy programming of your own commands, etc.

``TOB`` contains python3 code to program objects in a functional way. it provides an “clean namespace” Object class that only has dunder methods, so the namespace is not cluttered with method names. This makes storing and reading to/from json possible.

``TOB`` is a python3 IRC bot, it can connect to IRC, fetch and display RSS feeds, take todo notes, keep a shopping list and log text. You can run it under systemd for 24/7 presence in a IRC channel.

``TOB`` is Public Domain.

|

**INSTALL**


installation is done with pipx

|
| ``$ pipx install tob``
| ``$ pipx ensurepath``
|
| <new terminal>
|
| ``$ tob srv > tob.service``
| ``$ sudo mv tob.service /etc/systemd/system/``
| ``$ sudo systemctl enable tob --now``
|
| joins ``#tob`` on localhost
|

**USAGE**

use ``tob`` to control the program, default it does nothing

|
| ``$ tob``
| ``$``
|

see list of commands

|
| ``$ tob cmd``
| ``cfg,dpl,exp,imp,mre,nme,pwd,rem,res,rss,syn``
|


**CONFIGURATION**

irc

|
| ``$ tob cfg server=<server>``
| ``$ tob cfg channel=<channel>``
| ``$ tob cfg nick=<nick>``
|

sasl

|
| ``$ tob pwd <nsvnick> <nspass>``
| ``$ tob cfg password=<frompwd>``
|

rss

|
| ``$ tob rss <url>``
| ``$ tob dpl <url> <item1,item2>``
| ``$ tob rem <url>``
| ``$ tob nme <url> <name>``
|

opml

|
| ``$ tob exp``
| ``$ tob imp <filename>``
|


**COMMANDS**

|
| ``cfg`` - irc configuration
| ``cmd`` - commands
| ``dpl`` - sets display items
| ``exp`` - export opml (stdout)
| ``imp`` - import opml
| ``mre`` - display cached output
| ``pwd`` - sasl nickserv name/pass
| ``rem`` - removes a rss feed
| ``res`` - restore deleted feeds
| ``rss`` - add a feed
| ``syn`` - sync rss feeds
| ``ver`` - show version
|

**FILES**

|
| ``~/.tob``
| ``~/.local/bin/tob``
| ``~/.local/pipx/venvs/tob/*``
|

**AUTHOR**

|
| Bart Thate <``bthate@dds.nl``>
|

**COPYRIGHT**

|
| ``tob`` is Public Domain.
|
