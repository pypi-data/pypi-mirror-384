.. _sur-uart:

============
EKF SUR-UART
============

Inventory
=========

.. include:: snippets/cpci_inventory.rst

Thermal and Humidity Sensor (Object: `th`)
==========================================

The EKF SUR-UART board has a built-in temperature and humidity sensor HDC2010.
The sensor is connected to the board's I2C bus.

+----------------------------------------------------------------------------+---------------------+---------------+
| Method                                                                     | Description         | Example Value |
+----------------------------------------------------------------------------+---------------------+---------------+
| :meth:`~ekfsm.devices.iio_thermal_humidity.IIOThermalHumidity.temperature` | Get the temperature | ``-10``       |
+----------------------------------------------------------------------------+---------------------+---------------+
| :meth:`~ekfsm.devices.iio_thermal_humidity.IIOThermalHumidity.humidity`    | Get the humidity    | ``50``        |
+----------------------------------------------------------------------------+---------------------+---------------+

Front Panel LEDs (Object: `led_a`, `led_b`, `led_c`, `led_d`)
=============================================================

The EKF SUR-UART board has eight triple-color front panel LEDs.
Two of them form one group accessible by on of the four objects `led_a`, `led_b`, `led_c`, `led_d`.

+--------------------------------------------------+------------------------+----------------+
| Method                                           | Description            | Example Value  |
+--------------------------------------------------+------------------------+----------------+
| :meth:`~ekfsm.devices.ekf_sur_led.EKFSurLed.set` | Set the color of a LED | ``0``, ``red`` |
+--------------------------------------------------+------------------------+----------------+
