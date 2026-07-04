def calculate_checksum(frame: bytes) -> int:
    return sum(frame[:30]) & 0xFFFF


def read_checksum(frame: bytes) -> int:
    return (frame[30] << 8) | frame[31]


def is_checksum_valid(frame: bytes) -> bool:
    if len(frame) != 32:
        return False
    return calculate_checksum(frame) == read_checksum(frame)