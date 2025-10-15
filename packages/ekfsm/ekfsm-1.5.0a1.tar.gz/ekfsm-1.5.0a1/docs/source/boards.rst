.. _boards:

=========================
Supported Boards
=========================


.. toctree::
    :maxdepth: 1
    :glob:

    boards/*/*

Accessing Boards
----------------

Boards are appended to the system object and can be accessed e.g. via `system.ccu`.
Objects described in the board documentation are available via the boards object.

Example
~~~~~~~
>>> from ekfsm import System
>>> sm = System("path/to/config.yaml")
>>> sm.ccu.fan.fan_status()
