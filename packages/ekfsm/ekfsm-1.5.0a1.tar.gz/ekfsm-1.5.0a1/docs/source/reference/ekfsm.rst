ekfsm package
=============

.. This generates documentation for all members in the __all__ list of the ekfsm package.
.. automodule:: ekfsm

Exceptions
----------

.. automodule:: ekfsm.exceptions

CLI
---

.. click:: ekfsm.cli:cli
   :prog: ekfsm-cli
   :show-nested:


Locking
-------

.. automodule:: ekfsm.lock

Utils
-----
.. automodule:: ekfsm.utils


ekfsm.devices package
=====================

.. We don't want the __all__ list in this package, so we must mention each module explicitly.


I2C Devices using SysFs
-----------------------

EEPROM
~~~~~~
.. automodule:: ekfsm.devices.eeprom
   :members:
   :undoc-members:
   :show-inheritance:

GPIO
~~~~
.. automodule:: ekfsm.devices.gpio

EKF SUR LED
~~~~~~~~~~~
.. automodule:: ekfsm.devices.ekf_sur_led

PMBUS
~~~~~
.. automodule:: ekfsm.devices.pmbus

IIO Thermal and Humidity Sensor
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: ekfsm.devices.iio_thermal_humidity

I2C MUX
~~~~~~~
.. automodule:: ekfsm.devices.mux

I2C Devices using SMBus directly
--------------------------------

EKF CCU Microcontroller
~~~~~~~~~~~~~~~~~~~~~~~
.. automodule:: ekfsm.devices.ekf_ccu_uc


Devices using SysFs
-------------------

CoreTemp
~~~~~~~~
.. automodule:: ekfsm.devices.coretemp

SMBIOS
~~~~~~
.. automodule:: ekfsm.devices.smbios

IO4Edge Devices
---------------

.. automodule:: ekfsm.devices.io4edge
.. automodule:: ekfsm.devices.ledArray
.. automodule:: ekfsm.devices.colorLed
.. automodule:: ekfsm.devices.buttonArray
.. automodule:: ekfsm.devices.button
.. automodule:: ekfsm.devices.thermal_humidity
.. automodule:: ekfsm.devices.watchdog

Base Classes and Utilities
--------------------------

.. automodule:: ekfsm.devices.generic
.. automodule:: ekfsm.devices.utils
.. automodule:: ekfsm.devices.iio
.. automodule:: ekfsm.devices.imu

ekfsm.core package
=====================

.. We don't want the __all__ list in this package, so we must mention each module explicitly.
.. automodule:: ekfsm.core.components
.. automodule:: ekfsm.core.probe
.. automodule:: ekfsm.core.slots
.. automodule:: ekfsm.core.sysfs
.. automodule:: ekfsm.core.utils
