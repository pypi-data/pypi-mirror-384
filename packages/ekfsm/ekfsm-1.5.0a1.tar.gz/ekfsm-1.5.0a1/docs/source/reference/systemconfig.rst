.. _systemconfig:

System Configuration File
=============================

The system configuration is defined in a YAML configuration file.

The configuration file defines the modular components of the system,
i.e. you define which board types are expected in which slots of the chassis.

Let's break down the configuration file:

.. code-block:: yaml

  system_config:
    name: "Simple System"
    slots:

      - name: SYSTEM_SLOT
        slot_type: CPCI_S0_SYS
        desired_hwmodule_type: EKF SC9-TOCCATA
        desired_hwmodule_name: CPU
        attributes:
            is_master: true

      - name: SLOT1
        slot_type: CPCI_S0_PER
        desired_hwmodule_type: EKF SUR-UART
        desired_hwmodule_name: FAN
        attributes:
            slot_coding: 0x1


`system_config.name` is the name of the system configuration. It can be any string,
currently not used, but you can access it via the `System` object's `name` attribute.

`system_config.slots` is a list of slots in the chassis.

- There must be one `Master` slot (designated by `is_master: true`) in the system. The master
  slot can be anywhere in the list

- You don't need to describe all physical slots in the chassis.
  You can leave out slots that are empty.

- The slot name is a string that can be any name you choose.
  It is used to identify the slot in the system. If the physical slots are labelled,
  it is a good idea to use the same label in the configuration file.

- `slot_type` is the type of the slot. It must be one of
  `CPCI_S0_SYS`, `CPCI_S0_PER`, `CPCI_S0_UTILITY`, `CPCI_S0_PSU`

- `desired_hwmodule_type` is the type of the hardware module that is expected in the slot.
  It must be one of the supported hardware module types. To see the supported hardware module types,
  refer to the :ref:`boards` section.

- `desired_hwmodule_name` is name that will be assigned to the hardware module object.
  It can be any string. It is used to identify the hardware module in the system. You
  use this name later to access the hardware module object.

- `attributes` is a dictionary of attributes.

   - For CompactPCI slots, `slot_coding` defines the geographical address of the slot, i.e.
     the setting of the GA[3:0] pins on the backplane.
   - The `is_master` attribute is used to designate the master slot.


Making board objects accessible from the system object
------------------------------------------------------

Some hardware modules provide functions that belong to the whole system, such as the
:ref:`ccu`, which provides a `chassis_inventory` function that returns the serial number etc.
of the complete system. You can make this function accessible from the system object like so:

.. code-block:: yaml

  system_config:
    name: "Simple System"
    aggregates:
      chassis_inventory: inventory

Then, you can access the function like this:

.. code-block:: python

    import ekfsm

    system = ekfsm.System("system.yaml")
    serial = system.inventory.serial()
