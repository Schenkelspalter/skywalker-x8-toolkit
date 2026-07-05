from esc import SerialTelemetryReader

PORT = "COM7"

with SerialTelemetryReader(PORT) as reader:
    while True:
        frame = reader.read()

        if frame is None:
            continue

        print(f"{frame.voltage_v:.1f} V | {frame.current_a:.1f} A | {frame.rpm_mechanical:.0f} rpm | {frame.status_messages}")
