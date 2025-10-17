"""Example script to control a CurveRunner device via USB serial communication.
"""

from curverunner import Curverunner, CurverunnerCommSerial
import time


# Create a CurveRunner instance using USB serial communication
# When no argument is given, the first available CurveRunner device is used
# I2C is recommended for usage with Raspberry Pi
comm = CurverunnerCommSerial()
# Create a CurveRunner instance using the communication interface
cr = Curverunner(comm)
print(f"Connected to CurveRunner with ID: {cr.get_device_id()}")

print("Setting servo 1 to 0 degrees")
cr.servo1.set_angle(0)
time.sleep(2)

print("Setting servo 1 to 90 degrees")
cr.servo1.set_angle(90)
time.sleep(2)

print("Setting servo 1 to 0 degrees")
cr.servo1.set_angle(0)
