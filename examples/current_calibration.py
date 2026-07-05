"""
Skywalker X8 Toolkit

Current calibration tool using the telemetry core library.
Stores averaged 2-second snapshots at predefined measured current levels.
"""

import csv
import os
import time
import msvcrt
from datetime import datetime
from pathlib import Path

from esc import SerialTelemetryReader, RollingFrameStatistics

PORT = "COM7"
TARGET_CURRENTS_A = [3, 7, 11, 15, 19]
SNAPSHOT_WINDOW_S = 2.0
DISPLAY_INTERVAL_S = 0.3


def clear() -> None:
    os.system("cls")


def create_output_file() -> Path:
    output_dir = Path("captures") / "snapshots"
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return output_dir / f"current_calibration_{timestamp}.csv"


def write_header(writer: csv.writer) -> None:
    writer.writerow([
        "timestamp_iso",
        "target_current_a",
        "sample_count",
        "time_span_s",
        "voltage_avg_v",
        "voltage_min_v",
        "voltage_max_v",
        "esc_current_avg_a",
        "esc_current_min_a",
        "esc_current_max_a",
        "target_to_esc_factor",
        "rpm_mech_avg",
        "rpm_mech_min",
        "rpm_mech_max",
        "throttle_in_avg_pct",
        "throttle_out_avg_pct",
        "state_h",
        "state_l",
        "status",
    ])


def save_snapshot(writer: csv.writer, target_current: float, stats: RollingFrameStatistics) -> None:
    latest = stats.latest
    if latest is None or stats.sample_count == 0:
        return

    voltage = stats.voltage
    current = stats.current
    rpm = stats.rpm_mechanical
    throttle_in = stats.throttle_input
    throttle_out = stats.throttle_output

    factor = ""
    if current.average > 0:
        factor = target_current / current.average

    writer.writerow([
        datetime.now().isoformat(timespec="seconds"),
        f"{target_current:.2f}",
        stats.sample_count,
        f"{stats.time_span_s:.3f}",
        f"{voltage.average:.3f}",
        f"{voltage.minimum:.3f}",
        f"{voltage.maximum:.3f}",
        f"{current.average:.3f}",
        f"{current.minimum:.3f}",
        f"{current.maximum:.3f}",
        "" if factor == "" else f"{factor:.4f}",
        f"{rpm.average:.0f}",
        f"{rpm.minimum:.0f}",
        f"{rpm.maximum:.0f}",
        f"{throttle_in.average:.1f}",
        f"{throttle_out.average:.1f}",
        f"0x{latest.state_h:02X}",
        f"0x{latest.state_l:02X}",
        ", ".join(latest.status_messages),
    ])


def display(target_current: float, target_index: int, stats: RollingFrameStatistics, output_file: Path) -> None:
    latest = stats.latest
    if latest is None or stats.sample_count == 0:
        return

    voltage = stats.voltage
    current = stats.current
    rpm = stats.rpm_mechanical
    throttle_in = stats.throttle_input
    throttle_out = stats.throttle_output

    factor = "-"
    if current.average > 0:
        factor = f"{target_current / current.average:.3f}"

    clear()

    print("============================================================")
    print("        ZTW CURRENT CALIBRATION TOOL")
    print("============================================================")
    print(f"Target current:      {target_current:8.2f} A  ({target_index + 1}/{len(TARGET_CURRENTS_A)})")
    print(f"Snapshot window:     {SNAPSHOT_WINDOW_S:8.2f} s")
    print(f"Samples in buffer:   {stats.sample_count:8d}")
    print(f"Buffer time span:    {stats.time_span_s:8.2f} s")
    print("------------------------------------------------------------")
    print("Adjust throttle until the clamp meter shows the target.")
    print("Wait a few seconds, then press SPACE.")
    print("ESC = Abort")
    print("------------------------------------------------------------")
    print(f"Voltage avg:         {voltage.average:8.2f} V")
    print(f"Voltage min/max:     {voltage.minimum:8.2f} / {voltage.maximum:.2f} V")
    print()
    print(f"ESC current avg:     {current.average:8.2f} A")
    print(f"ESC current min/max: {current.minimum:8.2f} / {current.maximum:.2f} A")
    print(f"Target/ESC factor:   {factor:>8}")
    print()
    print(f"RPM mech avg:        {rpm.average:8.0f} rpm")
    print(f"RPM mech min/max:    {rpm.minimum:8.0f} / {rpm.maximum:.0f} rpm")
    print()
    print(f"Throttle IN avg:     {throttle_in.average:8.1f} %")
    print(f"Throttle OUT avg:    {throttle_out.average:8.1f} %")
    print("------------------------------------------------------------")
    print(f"State-H/L:           0x{latest.state_h:02X} / 0x{latest.state_l:02X}")
    print(f"Status:              {', '.join(latest.status_messages)}")
    print("------------------------------------------------------------")
    print(f"Output file:         {output_file}")
    print("============================================================")


def main() -> None:
    output_file = create_output_file()
    stats = RollingFrameStatistics(window_seconds=SNAPSHOT_WINDOW_S)

    target_index = 0
    last_display = 0.0

    with SerialTelemetryReader(PORT) as reader, open(output_file, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file, delimiter=";")
        write_header(writer)

        while target_index < len(TARGET_CURRENTS_A):
            frame = reader.read()
            if frame is not None:
                stats.add(frame)

            now = time.time()
            if now - last_display > DISPLAY_INTERVAL_S:
                last_display = now
                display(TARGET_CURRENTS_A[target_index], target_index, stats, output_file)

            if msvcrt.kbhit():
                key = msvcrt.getch()

                if key == b"\x1b":
                    print("\nAborted.")
                    return

                if key == b" ":
                    save_snapshot(writer, TARGET_CURRENTS_A[target_index], stats)
                    csv_file.flush()

                    print(f"\nSaved averaged snapshot for {TARGET_CURRENTS_A[target_index]:.2f} A")
                    time.sleep(0.7)
                    target_index += 1

        print("\nMeasurement completed.")
        print(f"Saved file: {output_file}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped.")