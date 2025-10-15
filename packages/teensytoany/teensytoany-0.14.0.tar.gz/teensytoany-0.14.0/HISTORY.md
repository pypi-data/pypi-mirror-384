# History

## 0.14.0 (2025-09-05)

* Provide support for teensytoany firmware 0.18.0 for ``spi_transfer16`` command.
* The returned value from ``spi_transfer`` is also returned as an integer.

## 0.13.0 (2025-08-22)

* Consolidate multiple entry points into a single `teensytoany` command with subcommands:
  - `teensytoany programmer` (replaces `teensytoany_programmer`)
  - `teensytoany i2c-scan` (replaces `teensytoany_i2c_scan`)
  - `teensytoany list` (replaces `teensytoany_list`)
* Maintain backward compatibility with deprecation warnings for old entry points

## 0.12.1 (2025-08-22)

* Add `fastled_set_max_refresh_rate` method to control FastLED refresh rate.
  - Supports rates from 1-800 Hz for normal operation
  - Rate of 0 runs as fast as possible

## 0.12.0 (2025-08-21)

* Add missing command methods to provide complete interface to all firmware commands:
  - I2C commands: `i2c_reset`, `i2c_read_no_register_uint8`, `i2c_write_no_register_uint8`,
    `i2c_read_payload_uint16`, `i2c_begin_transaction`, `i2c_write`, `i2c_end_transaction`,
    `i2c_buffer_size`, `i2c_write_bulk`
  - I2C_1 commands: `i2c_1_reset`, `i2c_1_read_no_register_uint8`, `i2c_1_write_no_register_uint8`,
    `i2c_1_read_payload_uint16`, `i2c_1_begin_transaction`, `i2c_1_write`, `i2c_1_end_transaction`,
    `i2c_1_buffer_size`, `i2c_1_write_bulk`
  - SPI commands: `spi_buffer_size`, `spi_set_clock_divider`
  - Register commands: `register_read_uint8`, `register_write_uint8`, `register_read_uint32`,
    `register_write_uint32`
  - Startup/Demo commands: `post_serial_startup_commands_available`, `read_post_serial_startup_command`
  - Utility commands: `sleep_seconds`
  - Info commands: `info`, `reboot`, `serialnumber`, `license`, `nop`
* Add `i2c_write_bulk` and `i2c_1_write_bulk` methods for writing up to 8k bytes with automatic
  chunking and transaction management
* Add `nop` command for testing purposes and comprehensive test suite

## 0.11.1 (2025-07-18)

* Provide an ability to define the device name at initialization time.

## 0.11.0 (2025-06-14)

* Try to automatically connect to devices with Manufacturer TeensyToAny. This
  requires firmware version 0.13.0 and up.

## 0.10.2 (2025-06-02)

* Fix I2C scanning command line utility by absorping the errors when no device
  is detected on the bus. Tested with a Teensy 4.0 and Sparkfun ISM330DHCX
  QWIIC board.

## 0.10.1 (2025-05-27)

* Attempt to fix i2c command line utility by correctly initializing the I2C bus.

## 0.10.0 (2025-05-26)

* Provide an i2c scan capabilities through the python api as well as a command
  line utility: `teensytoany_i2c_scan`.

## 0.9.0 (2025-05-16)

* Provide capabilities to program devices with board specific firmwares. #38

## 0.8.0 (2025-04-10)

* Automatically increase the timeout when issuing pulse commands to enable
  longer pulse durations.

## 0.7.0 (2025-03-12)

* Add support for Wire1 I2C interface.

## 0.6.0 (2025-03-09)

* Provide a method to control LEDs through FastLED.

## 0.5.0 (2024-11-10)

* Provide control over the startup and demo commands.
* Ensure that potentially undefined variable is defined.

## 0.4.0 (2024-04-05)

* Provide functions to fetch local and remote firmware versions.
* Provide a static method to program the latest firmware version and a CLI to
  do so from the terminal.

## 0.3.0 (2024-04-02)

* Add a `timeout` property to the functions that deal with updating the firmware.

## 0.2.0 (2023-11-07)

* Add a `timeout` property to simplify modifying the command timeout.

## 0.1.0 (2023-09-29)

* Provide access the new `mcu` command that reveals the microcontroller used at
  the time of firmware programming.

* Provide an internal method that can be used by developers to update to the
  latest firmware.

## 0.0.34 (2023-08-26)

* Small fixup in how reading the Teensy's registers is done to ensure better
  forward compatibility.

## 0.0.33 (2023-08-26)

The following features require teensy-to-any version 0.0.23 or greater
* Add support for `gpio_digital_pulse`.
* Add support for `analog_pulse`.
* Add support for new `value` parameter for `gpio_pin_mode`.
* Add support to read the data returned from `spi_transfer_bulk`.

## 0.0.32 (2023-08-30)

* Address bugs in reading the values from Teensy's registers.

## 0.0.31 (2023-08-21)

* Add the ability to read and write to the teensy's registers.

## 0.0.30 (2023-04-03)

* Increase default timeout to 0.2 seconds from 0.1. This helps receive error
  messages from missed I2C communications.
* Return an error if no response is returned from a standard command indicating
  a timeout.

## 0.0.29 (2023-03-06)

* Try to avoid racy conditions in version reading
* Flush buffers upon startup to help with crash recovery.

## 0.0.28 (2023-03-04)

* Make the error message when no device is found more human friendly.

## 0.0.27 (2022-10-16)

* Use packaging instead of distutils for version identification

## 0.0.26 (2021-09-13)

* added function `spi_read_byte` enabling the user to read SPI register.

## 0.0.25 (2021-07-14)

* added function `analog_read` enabling the user to read analog signals.

## 0.0.24 (2021-06-03)

* added `i2c_read_payload and` `i2c_write_payload functions` which allows users to read and write a contiguous payload of bytes

## 0.0.23 (2021-02-13)

* Ensure compatibility with pyserial 3.X
* Power a ``start_poweroff`` parameter to ``TeensyPower`` to start the device
  in the on state.
* Added the ability to close and open the device without deleting the python
  object.

## 0.0.22 (2020-06-18)

* Added the ability to control a power switch that is connected to the
  nominally on port.

## 0.0.20 (2019-12-14)

* Added capabilities for SPI and Analog functions

## 0.0.16 (2019-11-30)

* `TeensyPower` destructor will not raise an error when the device had failed
   to open.

## 0.0.15 (2019-11-29)

* `TeensyPower` devices will automatically poweroff the output when
  closed.

## 0.0.14 (2019-11-29)

* Added the specialized `TeensyPower` driver.

## 0.0.13 (2019-11-20)

* Added a few more serial numbers to the `teensytoany.known_devices`

## 0.0.1 (2019-11-07)

* First release on PyPI.
