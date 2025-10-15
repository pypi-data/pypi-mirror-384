from .teensytoany import TeensyToAny

__all__ = ['TeensyPower']


class TeensyPower():
    def __init__(self, pin_number=13, *,
                 nominally_off=True, open=True, start_poweroff=True, **kwargs):
        """Open an AC power switch controlled by a Teensy microcontroller.

        Parameters
        ----------
        pin_number:
            The pin number on the teensy that is used to control the switch.

        nominally_off: bool
            If your device is connected to the nominally off port, set this to
            ``True``. If it is connected to the nominally on port, set this to
            ``False``.

        start_poweroff: bool
            If ``True``, the device will set the power to the off state upon
            startup. If ``False`` the device will set the power to the on
            state upon startup.

        **kwargs:
            Additional keyword arguments are passed to the ``TeensyToAny``
            constructor.

        """
        # auto_poweroff is used in the destructor. create it first
        # initialize other used variables to safe values
        self.auto_poweroff = True
        self._teensy = None
        self._nominally_off = bool(nominally_off)
        self.pin_number = pin_number

        self._teensy = TeensyToAny(open=open, **kwargs)
        if open:
            self.open(start_poweroff=start_poweroff)

    def open(self, *, start_poweroff=True):
        """Open the device.

        Parameters
        ----------

        start_poweroff: bool
            If ``True``, the device will set the power to the off state upon
            startup. If ``False`` the device will set the power to the on
            state upon startup.

        """
        self._teensy.open()
        self._teensy.gpio_pin_mode(self.pin_number, 1)
        if start_poweroff:
            self.poweroff()
        else:
            self.poweron()

    def __del__(self):
        self.close()

    def close(self):
        if self._teensy is not None:
            if self.auto_poweroff:
                if self._teensy._serial is not None:
                    self.poweroff()
            self._teensy.close()

    def poweron(self):
        """Turn the power outlet on.

        The outlets denoted ``Nominally Off`` will turn **on**.

        The outlets denoted ``Nominally On`` will turn **off**.
        """
        write_value = int(self._nominally_off)
        self._teensy.gpio_digital_write(self.pin_number, write_value)

    def poweroff(self):
        """Turn the power outlet on.

        The outlets denoted ``Nominally Off`` will turn **off**.

        The outlets denoted ``Nominally On`` will turn **on**.
        """
        write_value = int(not self._nominally_off)
        self._teensy.gpio_digital_write(self.pin_number, write_value)
