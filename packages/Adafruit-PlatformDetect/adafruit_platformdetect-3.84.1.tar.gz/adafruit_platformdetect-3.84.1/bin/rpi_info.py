#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2023 Melissa LeBlanc-Williams for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`bin.rpi_info`
================================================================================

Interactive mode will prompt for the revision code
Otherwise it will be detected automatically

* Author(s): Melissa LeBlanc-Williams

Implementation Notes
--------------------

**Software and Dependencies:**

* Linux and Python 3.7 or Higher

"""

import sys
import argparse
import adafruit_platformdetect
from adafruit_platformdetect.revcodes import PiDecoder

detector = adafruit_platformdetect.Detector()
parser = argparse.ArgumentParser()


def print_property(label, value):
    """Format and print a property"""
    print(f"{label}: {value}")


def main(interactive):
    """Run the program"""
    pi_rev_code = detector.board._pi_rev_code()  # pylint: disable=protected-access

    if pi_rev_code is None:
        print("Raspberry Pi not detected. Using interactive mode")

    if pi_rev_code is None or interactive:
        pi_rev_code = input(
            "Enter a Raspberry Pi revision code (e.g. d03114 or 000f): "
        )

    print_property("Revision Code", pi_rev_code)

    try:
        decoder = PiDecoder(pi_rev_code)
    except ValueError:
        print("Invalid revision code. It should be a hexadecimal value.")
        sys.exit(1)

    if not decoder.is_valid_code():
        print(
            "Code is invalid. This rev code includes at least one "
            "value that is outside of the expected range."
        )
        sys.exit(1)

    if decoder.is_new_format():
        print_property("Overvoltage", decoder.overvoltage)
        print_property("OTP Program", decoder.otp_program)
        print_property("OTP Read", decoder.otp_read)
        print_property("Warranty bit", decoder.warranty_bit)
        print_property("New flag", decoder.rev_style)
        print_property("Memory size", decoder.memory_size)
        print_property("Manufacturer", decoder.manufacturer)
        print_property("Processor", decoder.processor)
        print_property("Type", decoder.type)
        print_property("Revision", decoder.revision)
    else:
        print_property("Warranty bit", decoder.warranty_bit)
        print_property("Model", decoder.type)
        print_property("Revision", decoder.revision)
        print_property("RAM", decoder.memory_size)
        print_property("Manufacturer", decoder.manufacturer)


# Main function
if __name__ == "__main__":
    parser.add_argument(
        "-i", "--interactive", help="Interactive Mode", action="store_true"
    )
    args = parser.parse_args()
    main(args.interactive)
