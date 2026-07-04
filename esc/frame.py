from dataclasses import dataclass

from .checksum import is_checksum_valid
from .protocol import (
    FRAME_LENGTH,
    HEADER,
    VOLTAGE_SCALE,
    CURRENT_SCALE,
    RPM_SCALE,
    BEC_VOLTAGE_SCALE,
    DEFAULT_POLE_PAIRS,
)


def u16_be(data: bytes, index: int) -> int:
    return (data[index] << 8) | data[index + 1]


@dataclass
class ZTWMantisFrame:
    raw: bytes
    pole_pairs: int = DEFAULT_POLE_PAIRS

    @property
    def valid(self) -> bool:
        return (
            len(self.raw) == FRAME_LENGTH
            and self.raw.startswith(HEADER)
            and is_checksum_valid(self.raw)
        )

    @property
    def voltage_v(self) -> float:
        return u16_be(self.raw, 3) * VOLTAGE_SCALE

    @property
    def current_a(self) -> float:
        return u16_be(self.raw, 5) * CURRENT_SCALE

    @property
    def power_w(self) -> float:
        return self.voltage_v * self.current_a

    @property
    def throttle_input_pct(self) -> int:
        return self.raw[7]

    @property
    def rpm_electrical(self) -> int:
        return u16_be(self.raw, 8) * RPM_SCALE

    @property
    def rpm_mechanical(self) -> float:
        return self.rpm_electrical / self.pole_pairs

    @property
    def mos_temp_c(self) -> int:
        return self.raw[10]

    @property
    def motor_temp_c(self) -> int:
        return self.raw[11]

    @property
    def throttle_output_pct(self) -> int:
        return self.raw[12]

    @property
    def state_h(self) -> int:
        return self.raw[13]

    @property
    def state_l(self) -> int:
        return self.raw[14]

    @property
    def mah_used(self) -> int:
        return u16_be(self.raw, 15)

    @property
    def uart_throttle(self) -> int:
        return self.raw[17]

    @property
    def can_throttle(self) -> int:
        return self.raw[18]

    @property
    def bec_voltage_v(self) -> float:
        return self.raw[19] * BEC_VOLTAGE_SCALE

    @property
    def status_messages(self) -> list[str]:
        messages = []

        state_l_bits = {
            0x01: "Short circuit protection",
            0x02: "Motor wire break",
            0x04: "PPM throttle lost",
            0x08: "Power-on throttle not zero",
            0x10: "Low-voltage protection",
            0x20: "Temperature protection",
            0x40: "Start locked-rotor protection",
            0x80: "Current protection",
        }

        state_h_bits = {
            0x01: "PPM throttle out of range",
            0x02: "UART throttle out of range",
            0x04: "UART throttle lost",
            0x08: "CAN throttle lost",
            0x10: "Battery voltage out of range",
        }

        for bit, text in state_l_bits.items():
            if self.state_l & bit:
                messages.append(text)

        for bit, text in state_h_bits.items():
            if self.state_h & bit:
                messages.append(text)

        return messages if messages else ["OK"]