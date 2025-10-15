# ekfsm - EKF system management library

Provides a python library framework for access to system management functions on Linux based modular hardware systems,
such as CompactPCI-Serial systems.

## Features

- System configuration via YAML configuration file
- Obtain inventory information of the system and its components
- Obtain sensor information, such as temperature, humidity, voltage, current, accelerometer, gyroscope, etc.
- Write and read EEPROM contents
- Access to system level functions, such as system LEDs, system fan, system power supply, etc.
- Supports simulation mode for development and testing
- Probing of desired boards in configured slots

## Requirements

Prior to the use of I2C, PMBus or GPIO devices using the API, those devices have to be initialised by ACPI or manual device setup.

### Example

In order to initialize an EEPROM of type AT24 behind a Mux channel 0, manualy add the device:

```bash
cd /sys/bus/i2c/devices/0-0074/channel-0/
echo 24c02 0x55 >new_device
```

Now we can access the EEPROM contents:

```bash
hd 8-0055/eeprom
00000000  ff ff ff ff ff ff ff ff  ff ff ff ff ff ff ff ff  |................|
*
00000100
```


## Installation

To install the package via pip, you have to use a virtual environment to ensure full operabilty.
*Note: CLI entrypoint script won't work if installed in the system store!*

### Prepare virtual environment

First, name, create and activate your virtual environment (here `myvenv`):

```bash
$ python -m venv myvenv
$ source myvenv/bin/activate
```

### Package install

Now install the ekfsm package and all dependencies from the [project pypi registry](https://gitlab.ekf.com/libs/apis/ekfsm/-/packages):

```bash
(myvenv) $ pip install ekfsm --index-url https://gitlab.ekf.com/api/v4/projects/407/packages/pypi/simple
Looking in indexes: https://gitlab.ekf.com/api/v4/projects/407/packages/pypi/simple
Collecting ekfsm
  Downloading https://gitlab.ekf.com/api/v4/projects/407/packages/pypi/files/e400ee46de9346c086ce708675977cc6ab080c8c016d360970c82d1c436f7c89/ekfsm-0.12.0-py3-none-any.whl (43 kB)
Collecting anytree (from ekfsm)
  Using cached anytree-2.12.1-py3-none-any.whl.metadata (8.1 kB)
Collecting click>=8.0.1 (from ekfsm)
  Using cached click-8.1.8-py3-none-any.whl.metadata (2.3 kB)
Collecting crcmod (from ekfsm)
  Using cached crcmod-1.7-cp312-cp312-linux_x86_64.whl
Collecting gpiod>=2.1.0 (from ekfsm)
  Using cached gpiod-2.3.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (4.1 kB)
Collecting hexdump (from ekfsm)
  Using cached hexdump-3.3-py3-none-any.whl
Collecting more-itertools (from ekfsm)
  Using cached more_itertools-10.6.0-py3-none-any.whl.metadata (37 kB)
Collecting munch (from ekfsm)
  Using cached munch-4.0.0-py2.py3-none-any.whl.metadata (5.9 kB)
Collecting smbus2 (from ekfsm)
  Using cached smbus2-0.5.0-py2.py3-none-any.whl.metadata (6.9 kB)
Collecting types-pyyaml>=6.0.12.20241230 (from ekfsm)
  Using cached types_PyYAML-6.0.12.20241230-py3-none-any.whl.metadata (1.8 kB)
Collecting yamale (from ekfsm)
  Using cached yamale-6.0.0-py3-none-any.whl.metadata (22 kB)
Collecting six (from anytree->ekfsm)
  Using cached six-1.17.0-py2.py3-none-any.whl.metadata (1.7 kB)
Collecting pyyaml (from yamale->ekfsm)
  Using cached PyYAML-6.0.2-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl.metadata (2.1 kB)
Using cached click-8.1.8-py3-none-any.whl (98 kB)
Using cached gpiod-2.3.0-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (103 kB)
Using cached types_PyYAML-6.0.12.20241230-py3-none-any.whl (20 kB)
Using cached anytree-2.12.1-py3-none-any.whl (44 kB)
Using cached more_itertools-10.6.0-py3-none-any.whl (63 kB)
Using cached munch-4.0.0-py2.py3-none-any.whl (9.9 kB)
Using cached smbus2-0.5.0-py2.py3-none-any.whl (11 kB)
Using cached yamale-6.0.0-py3-none-any.whl (57 kB)
Using cached PyYAML-6.0.2-cp312-cp312-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (767 kB)
Using cached six-1.17.0-py2.py3-none-any.whl (11 kB)
Installing collected packages: smbus2, hexdump, crcmod, types-pyyaml, six, pyyaml, munch, more-itertools, gpiod, click, yamale, anytree, ekfsm
Successfully installed anytree-2.12.1 click-8.1.8 crcmod-1.7 ekfsm-0.12.0 gpiod-2.3.0 hexdump-3.3 more-itertools-10.6.0 munch-4.0.0 pyyaml-6.0.2 six-1.17.0 smbus2-0.5.0 types-pyyaml-6.0.12.20241230 yamale-6.0.0
```

## Example Usage Scenario

To use the library for a desired system, it must be configured in a system config yaml file:

```yaml
# Example config
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
```

### API

If you want to access the LEDs on the EKF SUR-UART, you can do the following:
```python
import ekfsm

system = ekfsm.System("system.yaml")

# alternative ways to get the SUR HWModule
sur = system["SER"]    # by using the HWModule name as key
sur = system.ser       # by using the HWmodule name as attribute
sur = system.slots["SLOT1"].hwmodule  # by using the slot name as key
sur = system.slots.slot1.hwmodule  # by using the slot name as attribute

# accessing the LED device
sur.led_a.set(0,"purple")  # set the color of the LED to purple
```

For further infos on all API aspects, please see the [API Reference](https://ekfsm.readthedocs.io/en/main/reference/index.html).

### CLI

Upon activation of a venv provided with the ekfsm library, an entry point script `ekfsm-cli` is exported in the current shell.

See `ekfsm-cli -h` for a help on the usage.


## Resources

[Documentation](https://ekfsm.readthedocs.io/en/main/)

[Source Code](https://gitlab.ekf.com/libs/apis/ekfsm)

[Developer Wiki](https://gitlab.ekf.com/libs/apis/ekfsm/-/wikis/home)
