The inventory function provides access to the inventory, such as the
vendor, model, serial number (taken from the board's EEPROM), and revision (from the board's
GPIO device).


+------------------------------------------------------------------+-----------------------------+---------------+
| Method                                                           | Description                 | Example Value |
+------------------------------------------------------------------+-----------------------------+---------------+
| :meth:`~ekfsm.devices.eeprom.EKF_EEPROM.vendor`                  | Get the board vendor        | ``EKF``       |
+------------------------------------------------------------------+-----------------------------+---------------+
| :meth:`~ekfsm.devices.eeprom.EKF_EEPROM.model`                   | Get the board model         | ``SUR-UART``  |
+------------------------------------------------------------------+-----------------------------+---------------+
| :meth:`~ekfsm.devices.eeprom.EKF_EEPROM.serial`                  | Get the board serial number | ``12345678``  |
+------------------------------------------------------------------+-----------------------------+---------------+
| :meth:`~ekfsm.devices.gpio.EKFIdentificationIOExpander.revision` | Get the board revision      | ``1``         |
+------------------------------------------------------------------+-----------------------------+---------------+
