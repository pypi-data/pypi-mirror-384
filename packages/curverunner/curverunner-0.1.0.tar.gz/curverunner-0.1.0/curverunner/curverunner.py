import struct
import time
from typing import List, Dict, Tuple

import serial
from serial.tools.list_ports import comports
import threading
import smbus2

from abc import ABC, abstractmethod

from curverunner.comm import CurverunnerComm, CurverunnerCommSerial, discover_devices_serial
from curverunner.util import INT16_MAX, map_value, unsigned_to_signed2, unsigned_to_signed4


class CurverunnerServo:
    SERVO_ANGLE_ADDRESSES = [3, 5, 7]

    SERVO_MIN_ANGLE = 0
    SERVO_MAX_ANGLE = 180

    SERVO_PORT_MIN_VAL = 0
    SERVO_PORT_MAX_VAL = 1800

    def __init__(self, comm: CurverunnerComm, servo_port: int = 1):
        self._comm = comm
        if servo_port < 1 or servo_port > 3:
            raise ValueError("Servo port must be between 1 and 3")
        self.servo_port = servo_port
        self._servo_addr = self.SERVO_ANGLE_ADDRESSES[servo_port - 1]

    def set_angle(self, degrees: float):
        """Move servo to the specified angle in degrees. \n

        Note that this method returns immediately and will not wait for the servo to reach the position.

        Args:
            degrees (float): The desired servo angle in degrees. Must be between 0 and 180 degrees.

        Raises:
            ValueError: If the degrees value is outside the valid servo angle range.
        """

        if degrees < self.SERVO_MIN_ANGLE or degrees > self.SERVO_MAX_ANGLE:
            raise ValueError(
                f"Servo angle must be between {self.SERVO_MIN_ANGLE} and {self.SERVO_MAX_ANGLE}"
            )
        val = int(
            map_value(
                degrees,
                self.SERVO_MIN_ANGLE,
                self.SERVO_MAX_ANGLE,
                self.SERVO_PORT_MIN_VAL,
                self.SERVO_PORT_MAX_VAL,
            )
        )
        self._comm.write2(self._servo_addr, val)

    def get_angle(self) -> float:
        """Gets the current servo angle in degrees.

        Returns:
            float: The current servo angle in degrees.
        """
        val = self._comm.read1(self._servo_addr)
        degrees = map_value(
            val,
            self.SERVO_PORT_MIN_VAL,
            self.SERVO_PORT_MAX_VAL,
            self.SERVO_MIN_ANGLE,
            self.SERVO_MAX_ANGLE,
        )
        return degrees


class CurverunnerMotor:
    REG_OFFSET_MOTOR_TYPE = 0
    REG_OFFSET_PULSES_PER_REV = 1
    REG_OFFSET_MOTOR_INVERTED = 3
    REG_OFFSET_ENCODER_INVERTED = 4
    REG_OFFSET_SLEW_RATE = 5
    REG_OFFSET_P = 7
    REG_OFFSET_I = 9
    REG_OFFSET_D = 11
    REG_OFFSET_FF = 13
    REG_OFFSET_TARGET = 15
    REG_OFFSET_CONTROL_MODE = 19
    REG_OFFSET_VEL = 20
    REG_OFFSET_POS = 22
    REG_OFFSET_PERCENT_OUTPUT = 26

    PIDF_SCALE = 1000

    MOTOR_TYPE_DISABLED = 0
    MOTOR_TYPE_OPEN_LOOP_BDC = 1
    MOTOR_TYPE_CLOSED_LOOP_BDC = 2
    MOTOR_TYPE_FIT0441 = 3

    CONTROL_MODE_DISABLED = 0
    CONTROL_MODE_PERCENT_OUTPUT = 1
    CONTROL_MODE_VELOCITY = 2
    CONTROL_MODE_POSITION = 3

    MOTOR_BASE_ADDRS = [15, 0]

    def __init__(self, comm: CurverunnerComm, motor_port: int = 1):
        if motor_port < 1 or motor_port > 2:
            raise ValueError("Motor port must be between 1 and 2")
        self.motor_port = motor_port
        self._base_addr = self.MOTOR_BASE_ADDRS[motor_port - 1]
        self._comm = comm

    def set_percent_out(self, percent_out: float):
        INT_16_MAX = (1 << 15) - 1
        if percent_out < -1:
            percent_out = -1
        elif percent_out > 1:
            percent_out = 1

        # convert to
        percent_out_write = int(percent_out * INT_16_MAX + INT_16_MAX)
        self._comm.write2(self._base_addr + self.REG_OFFSET_TARGET, percent_out_write)
        self._comm.write2(
            self._base_addr + self.REG_OFFSET_CONTROL_MODE, int(self.CONTROL_MODE_PERCENT_OUTPUT)
        )

    def set_target_velocity(self, velocity: int):
        vel = int(velocity)
        self._comm.write2(self._base_addr + self.REG_OFFSET_TARGET, vel)
        self._comm.write2(
            self._base_addr + self.REG_OFFSET_CONTROL_MODE, int(self.CONTROL_MODE_VELOCITY)
        )

    def get_position_raw(self) -> int:
        return unsigned_to_signed4(self._comm.read4(self._base_addr + self.REG_OFFSET_POS))

    def get_velocity_raw(self) -> int:
        return unsigned_to_signed2(self._comm.read2(self._base_addr + self.REG_OFFSET_VEL))

    def get_percent_out(self) -> float:
        return (
            unsigned_to_signed2(self._comm.read2(self._base_addr + self.REG_OFFSET_PERCENT_OUTPUT))
            / INT16_MAX
        )

    def set_p(self, p: float):
        self._comm.write2(self._base_addr + self.REG_OFFSET_P, int(p * self.PIDF_SCALE))

    def get_p(self) -> float:
        return self._comm.read2(self._base_addr + self.REG_OFFSET_P) / self.PIDF_SCALE

    def set_i(self, i: float):
        self._comm.write2(self._base_addr + self.REG_OFFSET_I, int(i * self.PIDF_SCALE))

    def get_i(self) -> float:
        return self._comm.read2(self._base_addr + self.REG_OFFSET_I) / self.PIDF_SCALE

    def set_d(self, d: float):
        self._comm.write2(self._base_addr + self.REG_OFFSET_D, int(d * self.PIDF_SCALE))

    def get_d(self) -> float:
        return self._comm.read2(self._base_addr + self.REG_OFFSET_D) / self.PIDF_SCALE

    def set_ff(self, f: float):
        self._comm.write2(self._base_addr + self.REG_OFFSET_FF, int(f * self.PIDF_SCALE))

    def get_ff(self) -> float:
        return self._comm.read2(self._base_addr + self.REG_OFFSET_FF) / self.PIDF_SCALE

    def get_motor_type(self) -> int:
        return self._comm.read1(self._base_addr + self.REG_OFFSET_MOTOR_TYPE)

    def set_motor_type(self, motor_type: int):
        if motor_type < 0 or motor_type > 3:
            raise RuntimeError("Motor type must be between 0 and 3")
        self._comm.write1(self._base_addr + self.REG_OFFSET_MOTOR_TYPE, int(motor_type))

    def set_encoder_inverted(self, inverted: bool):
        self._comm.write1(self._base_addr + self.REG_OFFSET_ENCODER_INVERTED, int(inverted))

    def get_encoder_inverted(self) -> bool:
        return self._comm.read1(self._base_addr + self.REG_OFFSET_ENCODER_INVERTED) == 1

    def set_motor_inverted(self, inverted: bool):
        self._comm.write1(self._base_addr + self.REG_OFFSET_MOTOR_INVERTED, int(inverted))

    def get_motor_inverted(self) -> bool:
        return self._comm.read1(self._base_addr + self.REG_OFFSET_MOTOR_INVERTED) == 1


class Curverunner:
    REG_VERSION = 0
    REG_DEVICE_ID = 1

    REG_PARAM1 = 71
    REG_PARAM2 = 73
    REG_COMMAND = 75

    COMMAND_SAVE_CONFIG = 1
    COMMAND_RELOAD_CONFIG = 2
    COMMAND_FACTORY_RESET = 3
    COMMAND_SET_DEVICE_ID = 4

    def __init__(self, comm: CurverunnerComm):
        self.comm = comm
        self.servo1 = CurverunnerServo(comm, 1)
        self.servo2 = CurverunnerServo(comm, 2)
        self.servo3 = CurverunnerServo(comm, 3)

        self.motor1 = CurverunnerMotor(comm, 1)

    def get_device_id(self) -> int:
        return self.comm.read1(self.REG_DEVICE_ID)

    def set_device_id(self, device_id: int):
        self.comm.write1(self.REG_DEVICE_ID, device_id)
        self.comm.write1(self.REG_COMMAND, self.COMMAND_SET_DEVICE_ID)

    def save_config(self):
        self.comm.write1(self.REG_COMMAND, self.COMMAND_SAVE_CONFIG)

    def reload_config(self):
        self.comm.write1(self.REG_COMMAND, self.COMMAND_RELOAD_CONFIG)

    def factory_reset(self):
        self.comm.write1(self.REG_COMMAND, self.COMMAND_FACTORY_RESET)
