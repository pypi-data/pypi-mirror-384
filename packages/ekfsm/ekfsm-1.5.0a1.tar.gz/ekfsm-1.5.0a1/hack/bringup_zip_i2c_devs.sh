#!/bin/bash

sudo bash -c "cd /home/fp/sur && make install"
sudo bash -c "cd /home/fp/so1 && make install"
sudo bash -c "cd /home/klaus/ccu && make install"
sudo bash -c "echo 24c02 0x57 > /sys/devices/pci0000:00/0000:00:1f.4/i2c-*/new_device"
