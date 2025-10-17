# Curverunner Python
![Curverunner Board](assets/curverunner_board.png)

---

Python library to interface with the [Curverunner](https://github.com/connor-belli/CurverunnerFW/tree/main) motor controller

## Features
 * Control up to 3 servos, 2 DC motors, and 3 auxiliary IOs
 * Supports I2C and USB serial communication
 * Programmable device ID for multiple devices on the same bus
 * Closed loop control for DC motors with encoders

## Quick Start
1. Install the library via pip:
```bash
pip install curverunner
```
2. Connect to Curverunner device via USB serial for initial setup
    * After setup, I2C is recommended for Raspberry Pi or similar devices
3. Use Python API to communicate with the device
```python
from curverunner import Curverunner, CurverunnerCommSerial

comm = CurverunnerCommSerial()  # Connect via USB serial
cr = Curverunner(comm)          # Create Curverunner instance
cr.servo1.write_degrees(45)     # Set servo 1 to 45 degrees
```

For further examples, see the [examples](examples/) directory.

## Documentation
* [API Reference](https://curverunner.readthedocs.io/en/latest/) (Incomplete)
* [Examples](examples/)


