#! /usr/bin/env python3
# import os
# import sys
# pyright: reportOptionalMemberAccess = false
import logging
from pathlib import Path

import click

from ekfsm.log import ekfsm_logger
from ekfsm.simctrl import enable_simulation, register_gpio_simulations
from ekfsm.system import System

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = ekfsm_logger(__name__)

sm: System | None = None

__all__ = ("cli", "main", "write", "show")


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--debug", "-d", is_flag=True, help="Enable debug output")
@click.option(
    "--sysfs",
    "-s",
    help="Use custom sysfs dir for simulation mode",
    is_flag=False,
    flag_value="tests/sim/sys",
    type=click.Path(exists=True),
)
@click.option(
    "--config",
    "-c",
    type=click.Path(exists=True),
    required=True,
    help="Path to configuration file",
)
def cli(verbose, debug, sysfs, config):
    global sm
    """POSIX-compliant CLI tool with subcommands
    for the EKF System Management (EKFSM) library.

    This tool provides a command-line interface for managing and
    interacting with the EKF System Management library. It allows
    users to perform various operations related to system management,
    including reading and writing data to the system, and displaying
    information about the system.

    Parameters
    ----------
    verbose
        Enable verbose output. If set, the logging level will be set to INFO.
    debug
        Enable debug output. If set, the logging level will be set to DEBUG.
    sysfs
        Use custom sysfs directory for simulation mode. If set, the
        simulation mode will be enabled and the specified directory
        will be used for sysfs operations.
    config
        Path to the configuration file. This file is required for
        initializing the system. The path should point to a valid
        configuration file in YAML format.
    """
    if verbose:
        logging.getLogger().setLevel(logging.INFO)
        logger.info("Verbose output enabled")
    if debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug output enabled")
    if sysfs:
        logger.warning("Simulation mode enabled")
        enable_simulation(Path(sysfs))
        register_gpio_simulations()

    sm = System(config)


@cli.command()
@click.option(
    "--serial",
    "-s",
    is_flag=False,
    prompt=True,
    type=int,
    help="Write chassis serial number",
)
@click.option("--unit", "-u", is_flag=False, prompt=True, type=int, help="Write chassis unit")
@click.option(
    "--vendor",
    "-n",
    is_flag=False,
    help="Write chassis vendor",
    default="EKF Elektronik",
)
@click.option("--revision", "-r", is_flag=False, help="Write chassis revision")
@click.option("--model", "-m", is_flag=False, help="Write chassis model")
@click.option("--custom", "-c", is_flag=False, help="Write chassis custom information")
@click.option("--version", "-v", is_flag=False, help="Write schema version", default=1)
def write(serial, unit, vendor, revision, model, custom, version):
    """Write data to the system"""
    chassis = sm.ccu.chassis_inventory
    eeprom = sm.ccu.mux.ch00.eeprom

    if serial:
        chassis.write_serial(serial)
    if unit:
        chassis.write_unit(unit)
    if vendor:
        chassis.write_vendor(vendor)
    if revision:
        chassis.write_revision(revision)
    if model:
        chassis.write_model(model)
    if custom:
        chassis.write_customer_area(custom)
    if version:
        eeprom.write_version(version)


@cli.command()
def show():
    """Show information about the system"""
    sm.print()


# Attach subgroups to main CLI
cli.add_command(write)
cli.add_command(show)


def main():
    cli(auto_envvar_prefix="EKFSM")


if __name__ == "__main__":
    main()
