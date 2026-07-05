\# Architecture



```text

UART

&#x20; │

&#x20; ▼

Frame Reader

&#x20; │

&#x20; ▼

Checksum Validation

&#x20; │

&#x20; ▼

ZTW Mantis Frame Decoder

&#x20; │

&#x20; ├── Rolling Statistics

&#x20; ├── Live Monitor

&#x20; ├── Snapshot Logger

&#x20; ├── Calibration Tools

&#x20; ├── MQTT Bridge

&#x20; └── MAVLink Bridge

