import click
from packaging.version import Version

import teensytoany
from teensytoany import TeensyToAny


@click.command(epilog=f"Version {teensytoany.__version__}")
@click.option(
    '--serial-number', '-s',
    type=str,
    default=None,
    show_default=False,
    help='Serial number of the Teensy device.'
)
@click.option(
    '--interface',
    '-i',
    type=int,
    default=0,
    show_default=True,
    help='I2C interface to use (0 for I2C, 1 for I2C1).'
)
@click.option(
    '--seven-bit-mode',
    '-7',
    is_flag=True,
    default=False,
    help=(
        'Report addresses in 7-bit mode instead of 8-bit mode. '
        'By default, addresses are reported in 8-bit mode.'
    ),
)
@click.option(
    '--baud-rate',
    type=int,
    default=100_100,
    show_default=True,
    help='Baud rate for the I2C bus.',
)
@click.option(
    '--verbose',
    is_flag=True,
    default=False,
    help='Report in verbose mode, print out all pinged addresses.',
)
@click.version_option(teensytoany.__version__)
def main(
    serial_number=None,
    interface=0,
    seven_bit_mode=False,
    baud_rate=100_100,
    verbose=False,
):
    click.echo(
        "WARNING: teensytoany_i2c_scan is deprecated. Use 'teensytoany i2c_scan' instead.",
        err=True
    )
    # pylint: disable=duplicate-code
    return i2c_scan(
        serial_number=serial_number,
        interface=interface,
        baud_rate=baud_rate,
        seven_bit_mode=seven_bit_mode,
        verbose=verbose,
    )


def _scan_and_print(teensy, interface, baud_rate, seven_bit_mode, verbose):
    if interface == 0:
        teensy.i2c_init(baud_rate=baud_rate)
    elif interface == 1:
        teensy.i2c_1_init(baud_rate=baud_rate)
    else:
        raise ValueError(f"Unknown interface {interface}. Must be 0 or 1")

    for address_7bit in range(1, 128):
        address = address_7bit << 1
        try:
            if interface == 0:
                teensy.i2c_ping(address=address)
            elif interface == 1:
                teensy.i2c_1_ping(address=address)
            if seven_bit_mode:
                print(f"Found device at address 0x{address_7bit:02X}")
            else:
                print(f"Found device at address 0x{address:02X}")
        except RuntimeError:
            pass
        finally:
            if verbose and seven_bit_mode:
                print(f"No device found at addr 0x{address_7bit:02X}")
            elif verbose and not seven_bit_mode:
                print(f"No device found at addr 0x{address:02X}")
            # else not verbose:
            #     pass


def i2c_scan(
    serial_number=None,
    interface=0,
    baud_rate=100_100,
    seven_bit_mode=False,
    verbose=False,
):

    teensy = TeensyToAny(serial_number=serial_number)
    if Version(teensy.version) < Version('0.12.0'):
        teensy.close()
        raise RuntimeError(
            "This script requires TeensyToAny version 0.12.0 or higher."
        )
    try:
        _scan_and_print(
            teensy,
            interface=interface,
            baud_rate=baud_rate,
            seven_bit_mode=seven_bit_mode,
            verbose=verbose,
        )
    finally:
        teensy.close()


if __name__ == "__main__":
    main()
