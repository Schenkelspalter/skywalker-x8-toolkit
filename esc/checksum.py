"""Checksum helpers for ZTW Mantis telemetry frames."""

from .protocol import FRAME_LENGTH


def u16_be(data: bytes, index: int) -> int:
    return (data[index] << 8) | data[index + 1]


def calculate_checksum(frame: bytes) -> int:
    return sum(frame[:30]) & 0xFFFF


def read_checksum(frame: bytes) -> int:
    return u16_be(frame, 30)


def is_checksum_valid(frame: bytes) -> bool:
    if len(frame) != FRAME_LENGTH:
        return False
    return calculate_checksum(frame) == read_checksum(frame)