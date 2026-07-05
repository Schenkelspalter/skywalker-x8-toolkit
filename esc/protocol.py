"""ZTW Mantis G2 telemetry protocol constants."""

FRAME_LENGTH = 32
HEADER = bytes([0xDD, 0x01])
BAUD_RATE = 115200

VOLTAGE_SCALE = 0.1
CURRENT_SCALE = 0.1
RPM_SCALE = 10
BEC_VOLTAGE_SCALE = 1.0

DEFAULT_POLE_PAIRS = 7

STATE_L_BITS = {
    0x01: "Short circuit protection",
    0x02: "Motor wire break",
    0x04: "PPM throttle lost",
    0x08: "Power-on throttle not zero",
    0x10: "Low-voltage protection",
    0x20: "Temperature protection",
    0x40: "Start locked-rotor protection",
    0x80: "Current protection",
}

STATE_H_BITS = {
    0x01: "PPM throttle out of range",
    0x02: "UART throttle out of range",
    0x04: "UART throttle lost",
    0x08: "CAN throttle lost",
    0x10: "Battery voltage out of range",
}