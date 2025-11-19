# Traffic Signals Module

Smart traffic signal control system with ambulance priority.

## Status: 🚧 Under Development

This module will provide:

- Signal state machine (RED/YELLOW/GREEN/EMERGENCY)
- Emergency priority manager for ambulances
- Visual signal simulator for testing
- Hardware controller interfaces (GPIO, Modbus)
- REST/MQTT API for remote control

## Tech Stack

**Core:**

- Python 3.8+
- Transitions (state machine library)
- AsyncIO for async operations

**Simulator:**

- Pygame (visual testing)

**Hardware:**

- RPi.GPIO (Raspberry Pi)
- pyModbusTCP (Industrial controllers)
- paho-mqtt (IoT messaging)

## Directory Structure

```
traffic_signals/
├── core/
│   ├── __init__.py
│   ├── state_machine.py       # Signal FSM
│   ├── priority_manager.py    # Emergency priority
│   └── timing_controller.py   # Signal timing
├── hardware/
│   ├── __init__.py
│   ├── signal_simulator.py    # Visual simulator
│   ├── gpio_controller.py     # Raspberry Pi
│   └── modbus_controller.py   # Industrial signals
└── README.md
```

## Configuration

Uses existing config files:

- `config/development.yaml`
- `config/production.yaml`

```yaml
traffic_controller:
  controller_type: "simulator" # or "gpio", "modbus"
  signal_phases:
    north_south: 30
    east_west: 25
  emergency:
    priority_duration: 45
```

## Installation

```bash
# Core dependencies
pip install transitions asyncio

# Simulator
pip install pygame

# Hardware (production)
pip install RPi.GPIO pyModbusTCP paho-mqtt
```

## Usage

```bash
# Run signal simulator
python run_signals.py

# Test with detection system
python run_detection.py --source video.mp4 --enable-signals
```

## Development Status

- [ ] Signal state machine
- [ ] Priority manager
- [ ] Visual simulator
- [ ] GPIO controller
- [ ] Modbus controller
- [ ] REST API
- [ ] Integration with detection system

See `ROADMAP.md` for detailed implementation plan.
