"""Serial telemetry reader for ZTW Mantis G2 ESC telemetry."""

from __future__ import annotations

from typing import Iterator

import serial

from .checksum import is_checksum_valid
from .frame import ZTWMantisFrame
from .protocol import BAUD_RATE, FRAME_LENGTH, HEADER


class SerialTelemetryReader:
    """Reads valid ZTW Mantis telemetry frames from a serial port."""

    def __init__(
        self,
        port: str,
        baudrate: int = BAUD_RATE,
        timeout: float = 0.05,
    ) -> None:
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: serial.Serial | None = None

    def open(self) -> None:
        """Open the serial port."""
        if self._serial is not None and self._serial.is_open:
            return

        self._serial = serial.Serial(
            port=self.port,
            baudrate=self.baudrate,
            timeout=self.timeout,
        )

    def close(self) -> None:
        """Close the serial port."""
        if self._serial is not None and self._serial.is_open:
            self._serial.close()

    def __enter__(self) -> "SerialTelemetryReader":
        self.open()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def __iter__(self) -> Iterator[ZTWMantisFrame]:
        return self

    def __next__(self) -> ZTWMantisFrame:
        frame = self.read()

        if frame is None:
            raise StopIteration

        return frame

    def read(self) -> ZTWMantisFrame | None:
        """Read the next valid telemetry frame.

        Returns:
            A valid ZTWMantisFrame, or None if no valid frame was available
            before the serial timeout.
        """
        if self._serial is None or not self._serial.is_open:
            self.open()

        assert self._serial is not None

        raw = self._read_raw_frame()

        if raw is None:
            return None

        if not is_checksum_valid(raw):
            return None

        frame = ZTWMantisFrame(raw)

        if not frame.valid:
            return None

        return frame

    def _read_raw_frame(self) -> bytes | None:
        """Synchronize to header and read one raw frame."""
        assert self._serial is not None

        while True:
            first = self._serial.read(1)

            if not first:
                return None

            if first[0] != HEADER[0]:
                continue

            second = self._serial.read(1)

            if not second:
                return None

            if second[0] != HEADER[1]:
                continue

            rest = self._serial.read(FRAME_LENGTH - len(HEADER))

            if len(rest) != FRAME_LENGTH - len(HEADER):
                return None

            return HEADER + rest
