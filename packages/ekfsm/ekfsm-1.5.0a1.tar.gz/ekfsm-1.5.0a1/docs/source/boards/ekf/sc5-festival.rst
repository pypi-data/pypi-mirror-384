================
EKF SC5-FESTIVAL
================

See `Product Page <https://ekf.com/product/sc5>`_ for the board's technical specifications.

Inventory (Object: `inventory`)
===============================

The inventory function provides access to the inventory, such as the
vendor, model, serial number (taken from the board's EEPROM), and revision (from SMBIOS sysfs entry).


+------------------------------------------------------+-----------------------------+-----------------+
| Method                                               | Description                 | Example Value   |
+------------------------------------------------------+-----------------------------+-----------------+
| :meth:`~ekfsm.devices.eeprom.EKF_EEPROM.vendor`      | Get the board vendor        | ``EKF``         |
+------------------------------------------------------+-----------------------------+-----------------+
| :meth:`~ekfsm.devices.eeprom.EKF_EEPROM.model`       | Get the board model         | ``SC9-TOCCATA`` |
+------------------------------------------------------+-----------------------------+-----------------+
| :meth:`~ekfsm.devices.eeprom.EKF_EEPROM.serial`      | Get the board serial number | ``12345678``    |
+------------------------------------------------------+-----------------------------+-----------------+
| :meth:`~ekfsm.devices.eeprom.EKF_EEPROM.repaired_at` | Board repair date           |                 |
+------------------------------------------------------+-----------------------------+-----------------+
| :meth:`~ekfsm.devices.eeprom.EKF_EEPROM.repaired_at` | Board manufacturing date    |                 |
+------------------------------------------------------+-----------------------------+-----------------+
| :meth:`~ekfsm.devices.smbios.SMBIOS.revision`        | Get the board revision      | ``1``           |
+------------------------------------------------------+-----------------------------+-----------------+


CPU Temperature (Object: `cputemp`)
===================================

The CPU temperature object provides the current CPU Die temperature in degrees Celsius.



+--------------------------------------------------+------------------+---------------+
| Method                                           | Description      | Example Value |
+--------------------------------------------------+------------------+---------------+
| :meth:`~ekfsm.devices.coretemp.CoreTemp.cputemp` | Get the CPU temp | ``65``        |
+--------------------------------------------------+------------------+---------------+
