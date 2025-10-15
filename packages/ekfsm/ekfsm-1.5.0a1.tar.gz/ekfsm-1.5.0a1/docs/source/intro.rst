============
Introduction
============

What is ekfsm?
==============

The ekfsm python package provides access to system management functions on Linux based modular hardware systems,
such as CompactPCI-Serial systems.


Features
========

* System configuration definition via YAML configuration file
* Obtain inventory information of the system and its components
* Obtain sensor information, such as temperature, humidity, voltage, current, accelerometer, gyroscope, etc.
* Access to system level functions, such as system LEDs, system fan, system power supply, etc.
* Supports simulation mode for development and testing


Core Concepts
=============

The ekfsm package is built around the following core concepts:

Passive
-------

The ekfsm package is designed to be passive. It will not perform any actions on the system,
unless called by the user.

System Configuration
--------------------

The system configuration is defined in a :ref:`systemconfig`. The configuration file defines the
modular components of the system, i.e. you define which board types (called :class:`~HWModule`s in ekfsm) are expected in which slots of the chassis.

The system configuration file is then passed to the :class:`~.System` constructor to create a system object.
During instantiation, the system object will create the necessary :class:`~ekfsm.core.components.HWModule` objects and all the
supported functions for the devices.

It will also check if the actual hardware configuration matches the expected configuration. The result
of this check in then available in the corresponding :class:`~.Slot` object.

Relation between objects
------------------------

The objects and subobjects model the hardware topology of the system.

An :class:`~.System` object is the root object of the ekfsm package.
The system object contains :class:`~.Slot` objects, which represent the slots of the chassis.
Each slot object contains zero or one :class:`~ekfsm.core.components.HWModule` objects, which represents the hardware module in the slot.

.. image:: _static/ekfsm_system.drawio.png
   :align: center

The hardware modules contain subfunctions, implemented by :class:`~.Device` objects and the device objects provide
methods to access the hardware functions.

.. image:: _static/devices.drawio.png
   :align: center

Accessing Device functions
--------------------------

Suppose you have the following configuration `system.yaml`:

.. code-block:: yaml

  system_config:
    name: "Simple System"
    slots:
      - name: SYSTEM_SLOT
        slot_type: CPCI_S0_SYS
        desired_hwmodule_type: EKF SC9-Toccata
        desired_hwmodule_name: CPU
        attributes:
          is_master: true
      - name: SLOT1
        slot_type: CPCI_S0_PER
        desired_hwmodule_type: EKF SRF-SUR
        desired_hwmodule_name: SER
        attributes:
          slot_coding: 0x1


If you want to access the LEDs on the :ref:`sur-uart`, you can do the following:

.. code-block:: python

    import ekfsm

    system = ekfsm.System("system.yaml")

    # alternative ways to get the SUR HWModule
    sur = system["SER"]    # by using the HWModule name as key
    sur = system.ser       # by using the HWModule name as attribute
    sur = system.slots["SLOT1"].hwmodule  # by using the slot name as key
    sur = system.slots.slot1.hwmodule  # by using the slot name as attribute

    # accessing the LED device
    sur.led_a.set(0,"purple")  # set the color of the LED to purple

For a list of each board's supported functions, see the :ref:`boards` section.

Querying slots
--------------

To check if the actual system configuration matches the one defined in the configuration file,
you can use the :meth:`~.Slot.info` method, which gives you the
desired and actual configuration of the slot.

.. code-block:: python

    import ekfsm

    system = ekfsm.System("system.yaml")

    for slot in system.slots:
        print(f"Slot {slot.info()}")


You can also use the :meth:`~.Slot.is_populated` method to check if a slot is populated and
the :meth:`~.Slot.is_correctly_populated` method to check if the slot contains the
correct hardware module.

.. warning::
    The detection mechanism has limitations. If a board is installed which is
    unknown to the ekfsm library, the slot will not be marked as populated.


Usage
=====

System Preparation
------------------

Many ekfsm devices rely on sysfs to access the hardware. Before ekfsm can be used,
the system must be configured so that all necessary sysfs entries are available.

For example, for an X86 CompactPCI Serial system, most of the devices supported by ekfsm
are I2C devices, but linux cannot detect them without further configuration.

Therefore, the I2C device tree is typically provided as ACPI SSDT (Secondary System Descriptor Table)
to the UEFI BIOS via a UEFI variable, and GRUB is configured to provide the device tree
(from that variable) to the kernel.

Consult your hardware provider for guidance.

Root Privileges
---------------

The ekfsm package requires root privileges to access the sysfs, dev and proc entries, so your
application must be run as root or with sudo.

Logging
-------

The ekfsm package uses the Python logging module for logging.
and follows `common practices for library logging <https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library>`_.
By default, if the application does not configure logging, the logging module will log
only messages with level WARNING or above and is using the default formatting, i.e.
only the message is printed.

To get a more verbose output, the application should call, for example

.. code-block:: python

    import logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


Usage from multiple processes
-----------------------------

It is possible to use ekfsm from multiple processes at the same time. The linux kernel
ensures that the relevant linux sysfs entries and devices are protected from concurrent access.

However, there are some exceptions due to the nature of some devices. For example, the
:ref:`ccu` has some methods that cannot be simultaneously accessed by multiple processes.

This is why the ekfsm package provides a locking mechanism for these devices. The locking mechanism is
implemented using a file lock. Application can choose to use the locking mechanism or not.
By default, the locking mechanism is enabled and uses the default lockfile directory ``/var/lock/ekfsm``.
The :meth:`~ekfsm.locking_configure` method can be used to enable or disable the locking mechanism and
to configure the lockfile directory.

To ensure that file locks are properly released, the application should
call the :meth:`~ekfsm.locking_cleanup` whenever the program exits. This can be done
using the `atexit` module.


Usage from within a container
-----------------------------

The ekfsm package can be used from within a container, but the container must have access to the `/sys`, `/dev` #
and - if locking is enabled - `/var/lock` directories of the host system.

This can be achieved by mounting the host's `/sys` and `/dev` directories into the container, e.g.

.. code-block:: bash

    docker run -v /sys:/sys -v /dev:/dev my_container
