#!/usr/bin/env bash

help="Usage: $(basename "$0") [OPTIONS]
Description:
	This script modifies common ACPI parameters for EKF boards

Options:
	-h		Show help
	-p PATH		Path to ACPI ASL
	-b BUS		PCI bus the board is attached to (varies with system board)
	-s SUN		Slot the board is being inserted into
"

while getopts :hp:b:s: flag
do
	case "${flag}" in
		h)
			echo "$help"
			exit 0
			;;
		p)
			path=${OPTARG}
			;;
		b)
			bus=${OPTARG}
			;;
		s)
			sun=${OPTARG}
			;;
		\?)
			echo "Invalid option: -${OPTARG}" >&2
			echo "$help"
			exit 1
			;;
		:)
			echo "Option -${OPTARG} requires an argument" >&2
			echo "$help"
			exit 1
			;;
	esac
done

if [[ -z "$path" || -z "$bus" || -z "$sun" ]]; then
    echo "Error: -p, -b, and -s options are required." >&2
    echo "$help"
    exit 1
fi

if ! sed -ie "s/\(_SB\.\)[^.]*\./\1$bus./g" "${path}"; then
	echo "Error: Failed to update PCI bus" >&2
	exit 1
fi

if ! sed -ie "s/\(Name\s*(_SUN,\s*\)0x[0-9A-Fa-f]\+/\1$(printf "0x%02x" "$sun")/g" "${path}"; then
	echo "Error: Failed to update SUN" >&2
	exit 1
fi

addr=$(printf "0x%x" $((0x70 | sun)))

if ! sed -i -E "s/_STR, Unicode \(\"0x[0-9a-fA-F]+ - MUX\"\)/_STR, Unicode \(\"$addr - MUX\"\)/1" "${path}"; then
	echo "Error: Failed to update _STR" >&2
	exit 1
fi

if ! sed -i -E "s/\"reg\", 0x[0-9a-fA-F]+\s*}/\"reg\", $addr }/1" "${path}"; then
	echo "Error: Failed to update reg" >&2
	exit 1
fi

if ! sed -i -E "0,/I2cSerialBusV2 \(0x[0-9a-fA-F]+,/s//I2cSerialBusV2 \($addr,/" "${path}"; then
	echo "Error: Failed to update I2cSerialBusV2 address" >&2
	exit 1
fi

if ! sed -i -E "s/MUX[0-9]{1}/MUX$sun/g" "${path}"; then
	echo "Error: Failed to update MUX" >&2
	exit 1
fi

exit 0
