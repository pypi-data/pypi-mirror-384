import sys

import click

import teensytoany
from teensytoany import TeensyToAny


def teensytoany_list(
    manufacturer="TeensyToAny",
    teensyduino=False,
):
    """
    List available TeensyToAny devices.
    """
    if teensyduino:
        manufacturer = "Teensyduino"

    try:
        device_serial_numbers = TeensyToAny.device_serial_number_pairs(manufacturer=manufacturer)
    except RuntimeError:
        click.echo(f"Error: Could not find any devices with manufacturer '{manufacturer}'.")
        sys.exit(1)

    for device, serial_number in device_serial_numbers:
        click.echo(f"Port: {device} -- Serial Number: {serial_number}")


@click.command(epilog=f"Version {teensytoany.__version__}")
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
@click.version_option(teensytoany.__version__)
def main(
    manufacturer="TeensyToAny",
    teensyduino=False,
):
    """
    List available TeensyToAny devices.
    """
    click.echo("WARNING: teensytoany_list is deprecated. Use 'teensytoany list' instead.", err=True)
    teensytoany_list(
        manufacturer=manufacturer,
        teensyduino=teensyduino,
    )
