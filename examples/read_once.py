import time
from esc import SerialTelemetryReader

PORT = "COM7"
UPDATE_INTERVAL_S = 0.5

print("Opening reader...")
print("Waiting for telemetry frames. Press CTRL+C to stop.")

last_print = 0.0

try:
    with SerialTelemetryReader(PORT) as reader:
        while True:
            frame = reader.read()

            if frame is None:
                continue

            now = time.time()
            if now - last_print < UPDATE_INTERVAL_S:
                continue

            last_print = now

            print(
                f"{frame.voltage_v:5.1f} V | "
                f"{frame.current_a:5.1f} A | "
                f"{frame.power_w:6.1f} W | "
                f"{frame.rpm_mechanical:7.0f} rpm | "
                f"THR {frame.throttle_input_pct:3d}/{frame.throttle_output_pct:3d} % | "
                f"MOS {frame.mos_temp_c:3d} C | "
                f"{', '.join(frame.status_messages)}"
            )

except KeyboardInterrupt:
    print("\nStopped.")