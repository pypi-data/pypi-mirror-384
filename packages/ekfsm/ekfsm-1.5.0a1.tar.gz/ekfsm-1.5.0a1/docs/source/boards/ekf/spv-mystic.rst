.. _spv-mystic:

==============
EKF SPV-MYSTIC
==============

See `Product Page <https://ekf.com/product/spv>`_ for the board's technical specifications.

Inventory
=========

.. include:: snippets/cpci_inventory.rst

GPIOs (Objects: `gpio0`, `gpio1`, `gpio2`)
==================================================

The EKF SPV-MYSTIC board has three 8-bit GPIOs that can be used to control the modems and
other peripherals on the board. Consult the hardware documentation for the usage of the GPIOs.

+------------------------------------------------+------------------------------------+-----------------+
| Method                                         | Description                        | Example Value   |
+------------------------------------------------+------------------------------------+-----------------+
| :meth:`~ekfsm.devices.gpio.GPIO.num_lines`     | Get number of GPIO lines available | ``8``           |
+------------------------------------------------+------------------------------------+-----------------+
| :meth:`~ekfsm.devices.gpio.GPIO.set_direction` | Set the direction of a GPIO pin    | ``0``, ``True`` |
+------------------------------------------------+------------------------------------+-----------------+
| :meth:`~ekfsm.devices.gpio.GPIO.set_pin`       | Set the value of a GPIO pin        | ``0``, ``True`` |
+------------------------------------------------+------------------------------------+-----------------+
| :meth:`~ekfsm.devices.gpio.GPIO.get_pin`       | Get the value of a GPIO pin        | ``True``        |
+------------------------------------------------+------------------------------------+-----------------+
