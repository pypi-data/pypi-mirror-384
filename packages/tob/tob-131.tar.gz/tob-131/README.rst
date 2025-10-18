T O B
=====


**NAME**


|
| ``tob`` - bot in reverse !
|


**SYNOPSIS**

::

    >>> from tob.objects import Object
    >>> from tob.serials import dumps, loads
    >>> o = Object()
    >>> o.a = "b"
    >>> print(loads(dumps(o)))
    {'a': 'b'}


**DESCRIPTION**

TOB has all you need to program a unix cli program, such as disk
perisistence for configuration files, event handler to handle the
client/server connection, etc.

TOB contains python3 code to program objects in a functional
way. it provides an “clean namespace” Object class that only has
dunder methods, so the namespace is not cluttered with method names.
This makes storing and reading to/from json possible.


**INSTALL**

installation is done with pip

|
| ``$ pip install tob``
|

**AUTHOR**

|
| Bart Thate <``bthate@dds.nl``>
|

**COPYRIGHT**

|
| ``TOB`` is Public Domain.
|
