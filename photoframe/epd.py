"""Driver for the Waveshare 7.3" Spectra 6 (E6) e-paper panel, 800x480.

The command sequence is adapted from Waveshare's epd7in3e.py
(https://github.com/waveshare/e-Paper, MIT-style license, (c) Waveshare team),
trimmed to the Raspberry Pi and using spidev/gpiozero directly.

Hardware modules are imported lazily so the rest of the package (image
preparation, previews) works on machines without GPIO/SPI.
"""

import logging
import time

logger = logging.getLogger(__name__)

WIDTH = 800
HEIGHT = 480

# BCM pin numbers used by the Waveshare HAT / e-Paper driver board.
RST_PIN = 17
DC_PIN = 25
BUSY_PIN = 24
PWR_PIN = 18

# 4-bit color codes understood by the panel controller (code 4 is unused).
BLACK = 0x0
WHITE = 0x1
YELLOW = 0x2
RED = 0x3
BLUE = 0x5
GREEN = 0x6

BUSY_TIMEOUT_S = 90


class EPD:
    """Use as a context manager: powers up + initialises on enter, sleeps on exit."""

    width = WIDTH
    height = HEIGHT

    def __init__(self, spi_bus=0, spi_device=0, spi_hz=4_000_000):
        self._spi_bus = spi_bus
        self._spi_device = spi_device
        self._spi_hz = spi_hz
        self._spi = None

    def __enter__(self):
        self.open()
        self.init()
        return self

    def __exit__(self, *exc):
        self.sleep()
        return False

    # -- low level ---------------------------------------------------------

    def open(self):
        import gpiozero
        import spidev

        self._rst = gpiozero.DigitalOutputDevice(RST_PIN)
        self._dc = gpiozero.DigitalOutputDevice(DC_PIN)
        self._pwr = gpiozero.DigitalOutputDevice(PWR_PIN)
        self._busy = gpiozero.DigitalInputDevice(BUSY_PIN, pull_up=False)

        self._spi = spidev.SpiDev()
        self._spi.open(self._spi_bus, self._spi_device)
        self._spi.max_speed_hz = self._spi_hz
        self._spi.mode = 0b00

        self._pwr.on()

    def close(self):
        if self._spi is None:
            return
        self._spi.close()
        self._spi = None
        self._rst.off()
        self._dc.off()
        self._pwr.off()
        for dev in (self._rst, self._dc, self._pwr, self._busy):
            dev.close()

    def _reset(self):
        self._rst.on()
        time.sleep(0.02)
        self._rst.off()
        time.sleep(0.002)
        self._rst.on()
        time.sleep(0.02)

    def _command(self, cmd, *data):
        # Chip select is driven by the kernel SPI driver (CE0).
        self._dc.off()
        self._spi.writebytes([cmd])
        if data:
            self._dc.on()
            self._spi.writebytes(list(data))

    def _data_bulk(self, buf):
        self._dc.on()
        self._spi.writebytes2(buf)

    def _wait_idle(self):
        # BUSY is low while the controller is working.
        deadline = time.monotonic() + BUSY_TIMEOUT_S
        while self._busy.value == 0:
            if time.monotonic() > deadline:
                raise TimeoutError("e-paper stayed busy; check wiring and SPI")
            time.sleep(0.01)

    # -- panel operations ----------------------------------------------------

    def init(self):
        self._reset()
        self._wait_idle()
        time.sleep(0.03)

        self._command(0xAA, 0x49, 0x55, 0x20, 0x08, 0x09, 0x18)
        self._command(0x01, 0x3F)
        self._command(0x00, 0x5F, 0x69)
        self._command(0x03, 0x00, 0x54, 0x00, 0x44)
        self._command(0x05, 0x40, 0x1F, 0x1F, 0x2C)
        self._command(0x06, 0x6F, 0x1F, 0x17, 0x49)
        self._command(0x08, 0x6F, 0x1F, 0x1F, 0x22)
        self._command(0x30, 0x03)
        self._command(0x50, 0x3F)
        self._command(0x60, 0x02, 0x00)
        self._command(0x61, 0x03, 0x20, 0x01, 0xE0)  # 800 x 480
        self._command(0x84, 0x01)
        self._command(0xE3, 0x2F)

        self._command(0x04)  # power on
        self._wait_idle()

    def _refresh(self):
        self._command(0x04)  # power on
        self._wait_idle()
        self._command(0x12, 0x00)  # display refresh
        self._wait_idle()
        self._command(0x02, 0x00)  # power off
        self._wait_idle()

    def display(self, buf):
        """Show a packed frame buffer (2 pixels per byte, see image.pack)."""
        expected = self.width * self.height // 2
        if len(buf) != expected:
            raise ValueError(f"buffer is {len(buf)} bytes, expected {expected}")
        logger.info("sending frame and refreshing (takes ~30 s)")
        self._command(0x10)
        self._data_bulk(buf)
        self._refresh()

    def clear(self, color=WHITE):
        self.display(bytes([(color << 4) | color]) * (self.width * self.height // 2))

    def sleep(self):
        if self._spi is None:
            return
        self._command(0x07, 0xA5)  # deep sleep
        time.sleep(2)
        self.close()
