import click

import teensytoany
from teensytoany.i2c_scan import i2c_scan
from teensytoany.list import teensytoany_list
from teensytoany.programmer import teensytoany_programmer


@click.group(epilog=f"Version {teensytoany.__version__}")
@click.version_option(teensytoany.__version__)
def teensytoany_cli():
    """TeensyToAny command line interface"""


@teensytoany_cli.command()
@click.option(
    '--serial-number',
    default=None,
    help=(
        'Serial number of the Teensy device to program. '
        'If not provided and only one Teensy device found, '
        'it will be programmed.'
    )
)
@click.option(
    '--mcu',
    type=click.Choice(['TEENSY40', 'TEENSY32']),
    default='TEENSY40',
    help='Microcontroller to program.'
)
@click.option(
    '--firmware-version',
    default=None,
    type=str,
    help='Firmware version to program. If not provided, the latest version will be programmed.'
)
@click.option(
    '--firmware-variant',
    default=None,
    type=str,
    help='Firmware variant to program. If not provided, the standard variant will be programmed.'
)
@click.option(
    '--download-only',
    is_flag=True,
    default=False,
    help='Download the firmware only, do not program the device.'
)
def programmer(
    serial_number=None,
    mcu='TEENSY40',
    firmware_version=None,
    firmware_variant=None,
    download_only=False
):
    """Program a Teensy device with a given firmware version"""
    # pylint: disable=duplicate-code
    teensytoany_programmer(
        serial_number=serial_number,
        mcu=mcu,
        firmware_version=firmware_version,
        firmware_variant=firmware_variant,
        download_only=download_only
    )


@teensytoany_cli.command()
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
def i2c_scan_command(
    serial_number=None,
    interface=0,
    seven_bit_mode=False,
    baud_rate=100_100,
    verbose=False,
):
    """Scan I2C devices connected to TeensyToAny"""
    # pylint: disable=duplicate-code
    i2c_scan(
        serial_number=serial_number,
        interface=interface,
        baud_rate=baud_rate,
        seven_bit_mode=seven_bit_mode,
        verbose=verbose,
    )


@teensytoany_cli.command()
@click.option(
    '--manufacturer',
    type=str,
    default="TeensyToAny",
    show_default=True,
    help="Manufacturer of the device to list.",
)
@click.option(
    '--teensyduino',
    is_flag=True,
    default=False,
    help=(
        "List devices with manufacturer 'TeensyToAny'. "
        "This is a shortcut for --manufacturer=TeensyToAny"
    ),
)
def list_command(
    manufacturer="TeensyToAny",
    teensyduino=False,
):
    """List available TeensyToAny devices"""
    teensytoany_list(
        manufacturer=manufacturer,
        teensyduino=teensyduino,
    )


if __name__ == '__main__':
    teensytoany_cli()
