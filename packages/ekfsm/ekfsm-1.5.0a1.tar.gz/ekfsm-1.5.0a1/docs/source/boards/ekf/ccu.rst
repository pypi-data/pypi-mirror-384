.. _ccu:

===========
EKF CCU
===========


Chassis Inventory (Object: `chassis_inventory`)
===============================================

The system inventory provides access to the chassis inventory, such as the vendor, model, serial number, and revision.

You can access the chassis inventory from the ccu object via the `chassis_inventory` attribute.

Alternatively, if your system configuration has the following snippet:

.. code-block:: yaml

    system_config:
    name: "MySystem"
    aggregates:
        chassis_inventory: inventory

you can access the chassis inventory via the system object's `inventory` attribute.

+--------------------------------------------------------------------+-------------------------------+--------------------+
| Method                                                             | Description                   | Example Value      |
+--------------------------------------------------------------------+-------------------------------+--------------------+
| :meth:`vendor() <ekfsm.devices.eeprom.EKF_CCU_EEPROM.cvendor>`     | Get the chassis vendor        | ``EKF Elektronik`` |
+--------------------------------------------------------------------+-------------------------------+--------------------+
| :meth:`model() <ekfsm.devices.eeprom.EKF_CCU_EEPROM.cmodel>`       | Get the chassis model         | ``SRS-C001``       |
+--------------------------------------------------------------------+-------------------------------+--------------------+
| :meth:`serial() <ekfsm.devices.eeprom.EKF_CCU_EEPROM.cserial>`     | Get the chassis serial number | ``12345678``       |
+--------------------------------------------------------------------+-------------------------------+--------------------+
| :meth:`revision() <ekfsm.devices.eeprom.EKF_CCU_EEPROM.crevision>` | Get the chassis revision      | ``2.0``            |
+--------------------------------------------------------------------+-------------------------------+--------------------+
| :meth:`~ekfsm.devices.eeprom.EKF_CCU_EEPROM.unit`                  | Get subsystem unit number     | ``1``              |
+--------------------------------------------------------------------+-------------------------------+--------------------+


Inventory of the CCU board (Object: `inventory`)
================================================

.. include:: snippets/cpci_inventory.rst


CCU EEPROM Customer area (Object: `custom_eeprom`)
==================================================

The CCU EEPROM provides 64 bytes for custom data storage.

+---------------------------------------------------------------------------+------------------------------------------+----------------------------+
| Method                                                                    | Description                              | Example Value              |
+---------------------------------------------------------------------------+------------------------------------------+----------------------------+
| :meth:`write() <ekfsm.devices.eeprom.EKF_CCU_EEPROM.write_customer_area>` | Write data to CCU EEPROM customer are    | ``b'\x01\x02\x03\x04\x05`` |
+---------------------------------------------------------------------------+------------------------------------------+----------------------------+
| :meth:`read() <ekfsm.devices.eeprom.EKF_CCU_EEPROM.customer_area>`        | Get the customer area of the CCU EEPROM. | ``b'\x01\x02\x03\x04\x05`` |
+---------------------------------------------------------------------------+------------------------------------------+----------------------------+


CCU Management (Object: `management`)
======================================

+--------------------------------------------------------------+-----------------------------------------------+----------------------------------------------------+
| Method                                                       | Description                                   | Example Value                                      |
+--------------------------------------------------------------+-----------------------------------------------+----------------------------------------------------+
| :meth:`~ekfsm.devices.ekf_ccu_uc.EKFCcuUc.identify_firmware` | Get the firmware title and version of the CCU | ``fw-ccu-00-default`` ``1.0.0``                    |
+--------------------------------------------------------------+-----------------------------------------------+----------------------------------------------------+
| :meth:`~ekfsm.devices.ekf_ccu_uc.EKFCcuUc.load_firmware`     | Load firmware into the CCU                    | <binary data>                                      |
+--------------------------------------------------------------+-----------------------------------------------+----------------------------------------------------+
| :meth:`~ekfsm.devices.ekf_ccu_uc.EKFCcuUc.get_parameterset`  | Get the CCU parameterset in JSON format       | ``{"version": "factory", "parameters": { ... } }`` |
+--------------------------------------------------------------+-----------------------------------------------+----------------------------------------------------+
| :meth:`~ekfsm.devices.ekf_ccu_uc.EKFCcuUc.load_parameterset` | Load a parameterset into the CCU              | ``{"version": "1.0.0", "parameters": { ... } }``   |
+--------------------------------------------------------------+-----------------------------------------------+----------------------------------------------------+
| :meth:`~ekfsm.devices.ekf_ccu_uc.EKFCcuUc.restart`           | Restart the CCU                               | N/A                                                |
+--------------------------------------------------------------+-----------------------------------------------+----------------------------------------------------+


System State Controller (Object: `sysstate`)
============================================

The system state controller provides method to influence the CCU's system state controller.

+--------------------------------------------------------+----------------------------------------+---------------+
| Method                                                 | Description                            | Example Value |
+--------------------------------------------------------+----------------------------------------+---------------+
| :meth:`~ekfsm.devices.ekf_ccu_uc.EKFCcuUc.wd_trigger`  | Trigger Watchdog                       | N/A           |
+--------------------------------------------------------+----------------------------------------+---------------+
| :meth:`~ekfsm.devices.ekf_ccu_uc.EKFCcuUc.sw_shutdown` | Tell CCU that we are going to shutdown | ``50``        |
+--------------------------------------------------------+----------------------------------------+---------------+


Fan Controller (Object: `fan`)
===============================

+-------------------------------------------------------------+----------------------------------------------+---------------------------+
| Method                                                      | Description                                  | Example Value             |
+-------------------------------------------------------------+----------------------------------------------+---------------------------+
| :meth:`~ekfsm.devices.ekf_ccu_uc.EKFCcuUc.fan_status`       | Get the status of a fan                      | ``5500``, ``5380``, ``3`` |
+-------------------------------------------------------------+----------------------------------------------+---------------------------+
| :meth:`~ekfsm.devices.ekf_ccu_uc.EKFCcuUc.push_temperature` | Tell FAN controller the external temperature | ``65``                    |
+-------------------------------------------------------------+----------------------------------------------+---------------------------+

Example
-------
.. code-block:: python

    # Get the fan status
    fan_status = ccu.fan.fan_status()
    print(f"Fan status: {fan_status}")

    # Push the temperature to the fan controller
    ccu.fan.push_temperature(65)
    print("Temperature pushed to fan controller.")

    # Wait for one second
    time.sleep(1)

    # Get the fan status again
    fan_status = ccu.fan.fan_status()
    print(f"Fan status: {fan_status}")


Inertial Measurement Unit (Object: `imu`)
=========================================

+-----------------------------------------------------------------+--------------------------+---------------------------------------------------------------------------------------------------------------------------------------------+
| Method                                                          | Description              | Example Value                                                                                                                               |
+-----------------------------------------------------------------+--------------------------+---------------------------------------------------------------------------------------------------------------------------------------------+
| :meth:`sample() <ekfsm.devices.ekf_ccu_uc.EKFCcuUc.imu_sample>` | Read the next IMU sample | ``accel: [-0.0047884033203125, -0.0143652099609375, 9.859322436523437], gyro: [-0.3662109375, -0.54931640625, 0.18310546875], lost: False`` |
+-----------------------------------------------------------------+--------------------------+---------------------------------------------------------------------------------------------------------------------------------------------+

Thermal and Humidity Sensor (Object: `th`)
==========================================

+--------------------------------------------------------+---------------------+---------------+
| Method                                                 | Description         | Example Value |
+--------------------------------------------------------+---------------------+---------------+
| :meth:`~ekfsm.devices.ekf_ccu_uc.EKFCcuUc.temperature` | Get the temperature | ``-10``       |
+--------------------------------------------------------+---------------------+---------------+
| :meth:`~ekfsm.devices.ekf_ccu_uc.EKFCcuUc.humidity`    | Get the humidity    | ``50``        |
+--------------------------------------------------------+---------------------+---------------+

System Input Voltage (Object: `vin`)
==========================================

+-------------------------------------------------------------------+------------------------------+---------------+
| Method                                                            | Description                  | Example Value |
+-------------------------------------------------------------------+------------------------------+---------------+
| :meth:`voltage() <ekfsm.devices.ekf_ccu_uc.EKFCcuUc.vin_voltage>` | Get the system input voltage | ``108``       |
+-------------------------------------------------------------------+------------------------------+---------------+
