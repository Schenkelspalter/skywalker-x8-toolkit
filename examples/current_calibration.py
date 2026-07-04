"""
Skywalker X8 Toolkit

Module:
Current Calibration Tool

Description:
Measures the relationship between actual DC input current
and the telemetry current reported by the ZTW Mantis G2 ESC.

License:
MIT
"""

import csv
import os
import sys
import time
import msvcrt
from datetime import datetime
from pathlib import Path

import serial


PORT = "COM7"
BAUD_RATE = 115200
FRAME_LENGTH = 32
POLE_PAIRS = 7

TARGET_CURRENTS_A = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]


def u16_be(data: bytes, index: int) -> int:
    return (data[index] << 8) | data[index + 1]


def checksum_valid(frame: bytes) -> bool:
    calculated = sum(frame[:30]) & 0xFFFF
    received = u16_be(frame, 30)
    return calculated == received


def read_frame(ser: serial.Serial) -> bytes | None:
    b = ser.read(1)

    if not b or b[0] != 0xDD:
        return None

    b1 = ser.read(1)
    if not b1 or b1[0] != 0x01:
        return None

    rest = ser.read(FRAME_LENGTH - 2)
    if len(rest) != FRAME_LENGTH - 2:
        return None

    frame = bytes([0xDD, 0x01]) + rest

    if not checksum_valid(frame):
        return None

    return frame


def decode_frame(frame: bytes) -> dict:
    voltage_v = u16_be(frame, 3) / 10.0
    esc_current_a = u16_be(frame, 5) / 10.0
    rpm_electrical = u16_be(frame, 8) * 10
    rpm_mechanical = rpm_electrical / POLE_PAIRS

    return {
        "voltage_v": voltage_v,
        "esc_current_a": esc_current_a,
        "power_w": voltage_v * esc_current_a,
        "throttle_input_pct": frame[7],
        "rpm_electrical": rpm_electrical,
        "rpm_mechanical": rpm_mechanical,
        "mos_temp_c": frame[10],
        "motor_temp_c": frame[11],
        "throttle_output_pct": frame[12],
        "state_h": frame[13],
        "state_l": frame[14],
        "mah_used": u16_be(frame, 15),
        "bec_voltage_v": frame[19],
        "raw": " ".join(f"{b:02X}" for b in frame),
    }


def clear_screen() -> None:
    os.system("cls")


def create_output_file() -> Path:
    output_dir = Path("captures") / "snapshots"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return output_dir / f"current_calibration_{timestamp}.csv"


def write_header(writer: csv.writer) -> None:
    writer.writerow(
        [
            "timestamp_iso",
            "target_current_a",
            "voltage_v",
            "esc_current_a",
            "meter_to_esc_factor",
            "power_w",
            "throttle_input_pct",
            "throttle_output_pct",
            "rpm_electrical",
            "rpm_mechanical",
            "mos_temp_c",
            "motor_temp_c",
            "mah_used",
            "bec_voltage_v",
            "state_h",
            "state_l",
            "raw",
        ]
    )


def write_snapshot(writer: csv.writer, target_current: float, data: dict) -> None:
    factor = ""
    if data["esc_current_a"] > 0:
        factor = target_current / data["esc_current_a"]

    writer.writerow(
        [
            datetime.now().isoformat(timespec="seconds"),
            f"{target_current:.1f}",
            f"{data['voltage_v']:.2f}",
            f"{data['esc_current_a']:.2f}",
            "" if factor == "" else f"{factor:.4f}",
            f"{data['power_w']:.2f}",
            data["throttle_input_pct"],
            data["throttle_output_pct"],
            data["rpm_electrical"],
            f"{data['rpm_mechanical']:.0f}",
            data["mos_temp_c"],
            data["motor_temp_c"],
            data["mah_used"],
            f"{data['bec_voltage_v']:.1f}",
            f"0x{data['state_h']:02X}",
            f"0x{data['state_l']:02X}",
            data["raw"],
        ]
    )


def display(target_current: float, target_index: int, total_targets: int, data: dict, filename: Path) -> None:
    clear_screen()

    print("============================================================")
    print("        ZTW CURRENT CALIBRATION TOOL")
    print("============================================================")
    print(f"Target:          {target_current:6.1f} A  ({target_index + 1}/{total_targets})")
    print()
    print("Adjust throttle until the clamp meter shows the target current.")
    print("Press SPACE to save this measurement.")
    print("Press ESC to abort.")
    print("------------------------------------------------------------")
    print(f"Voltage:         {data['voltage_v']:8.2f} V")
    print(f"ESC Current:     {data['esc_current_a']:8.2f} A")
    print(f"Factor target/ESC:" + (
        f" {target_current / data['esc_current_a']:8.3f}"
        if data["esc_current_a"] > 0
        else "        -"
    ))
    print(f"Power ESC:       {data['power_w']:8.2f} W")
    print("------------------------------------------------------------")
    print(f"Throttle IN:     {data['throttle_input_pct']:8d} %")
    print(f"Throttle OUT:    {data['throttle_output_pct']:8d} %")
    print(f"RPM electrical:  {data['rpm_electrical']:8d}")
    print(f"RPM mechanical:  {data['rpm_mechanical']:8.0f}")
    print("------------------------------------------------------------")
    print(f"MOS Temp:        {data['mos_temp_c']:8d} C")
    print(f"Motor Temp:      {data['motor_temp_c']:8d} C")
    print(f"mAh used:        {data['mah_used']:8d} mAh")
    print(f"BEC Voltage:     {data['bec_voltage_v']:8.1f} V")
    print("------------------------------------------------------------")
    print(f"State-H:         0x{data['state_h']:02X}")
    print(f"State-L:         0x{data['state_l']:02X}")
    print("------------------------------------------------------------")
    print(f"Output file:     {filename}")
    print("============================================================")


def main() -> None:
    filename = create_output_file()

    print("Opening serial port...")
    print(f"Port: {PORT}")
    print(f"Baud: {BAUD_RATE}")

    target_index = 0
    last_display = 0.0
    latest_data = None

    with serial.Serial(PORT, BAUD_RATE, timeout=0.05) as ser, open(
        filename, "w", newline="", encoding="utf-8"
    ) as csv_file:
        writer = csv.writer(csv_file, delimiter=";")
        write_header(writer)

        while target_index < len(TARGET_CURRENTS_A):
            frame = read_frame(ser)

            if frame is not None:
                latest_data = decode_frame(frame)

            if latest_data is None:
                continue

            now = time.time()

            if now - last_display > 0.3:
                last_display = now
                display(
                    TARGET_CURRENTS_A[target_index],
                    target_index,
                    len(TARGET_CURRENTS_A),
                    latest_data,
                    filename,
                )

            if msvcrt.kbhit():
                key = msvcrt.getch()

                if key == b"\x1b":
                    print("\nAborted.")
                    return

                if key == b" ":
                    write_snapshot(writer, TARGET_CURRENTS_A[target_index], latest_data)
                    csv_file.flush()

                    print(f"\nSaved snapshot for {TARGET_CURRENTS_A[target_index]:.1f} A")
                    time.sleep(0.5)

                    target_index += 1

        print("\nMeasurement completed.")
        print(f"Saved file: {filename}")


if __name__ == "__main__":
    try:
        main()
    except serial.SerialException as exc:
        print(f"Serial error: {exc}")
        sys.exit(1)