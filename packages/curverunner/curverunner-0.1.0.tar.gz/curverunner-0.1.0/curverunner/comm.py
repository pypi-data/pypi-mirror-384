import struct
import time
from typing import List, Dict, Tuple

import serial
from serial.tools.list_ports import comports
import threading
import smbus2

from abc import ABC, abstractmethod

from curverunner.util import INT16_MAX, map_value, unsigned_to_signed2, unsigned_to_signed4


class CurverunnerComm(ABC):
    """
    Abstract base class for communication with CurveRunner device.

    Methods to read and write 1, 2, and 4 byte values to/from specified addresses.
    """

    @abstractmethod
    def write1(self, addr: int, val: int) -> None:
        pass

    @abstractmethod
    def write2(self, addr: int, val: int) -> None:
        pass

    @abstractmethod
    def write4(self, addr: int, val: int) -> None:
        pass

    @abstractmethod
    def read1(self, addr: int) -> int:
        pass

    @abstractmethod
    def read2(self, addr: int) -> int:
        pass

    @abstractmethod
    def read4(self, addr: int) -> int:
        pass


class CurverunnerCommI2C(CurverunnerComm):
    def __init__(self, bus: smbus2.SMBus, addr: int = 0x08):
        self._bus = bus
        self._addr = addr

    def _attempt_write(self, reg, data):
        for _ in range(5):
            try:
                self._bus.write_i2c_block_data(self._addr, reg, data)
                break
            except OSError:
                time.sleep(0.02)

    def _attempt_read(self, reg, size):
        byte_data = None
        for _ in range(5):
            try:
                byte_data = bytes(self._bus.read_i2c_block_data(self._addr, reg, size))
                break
            except OSError:
                time.sleep(0.02)
        else:
            raise RuntimeError("Failed to read from I2C device")
        return byte_data

    def _write(self, addr: int, val: int, size: int) -> None:
        self._attempt_write(addr, val.to_bytes(size, "little"))

    def write1(self, addr: int, val: int) -> None:
        self._write(addr, val, 1)

    def write2(self, addr: int, val: int) -> None:
        self._write(addr, val, 2)

    def write4(self, addr: int, val: int) -> None:
        self._write(addr, val, 4)

    def _read(self, addr: int, size: int) -> int:
        return int.from_bytes(self._attempt_read(addr, size), "little")

    def read1(self, addr: int) -> int:
        return self._read(addr, 1)

    def read2(self, addr: int) -> int:
        return self._read(addr, 2)

    def read4(self, addr: int) -> int:
        return self._read(addr, 4)


class CurverunnerCommSerial(CurverunnerComm):
    def __init__(self, ser: str | serial.Serial | None = None):
        """_summary_

        Args:
            ser (str | serial.Serial | None, optional): Serial connection specification. Can be:
                - str: Serial port path/name (e.g., '/dev/ttyUSB0' or 'COM3')
                - serial.Serial: Existing Serial object to use
                - None: Auto-discover first available CurveRunner device

        Raises:
            RuntimeError: If no CurveRunner devices are found during auto-discovery
        """

        if isinstance(ser, str):
            self._ser = serial.Serial(ser, 115200)
        elif ser is None:
            # Find first valid CurveRunner device
            devices = discover_devices_serial()
            if len(devices) == 0:
                raise RuntimeError("No CurveRunner devices found")

            self._ser = serial.Serial(devices[0], 115200)
        else:
            self._ser = ser

        self._lock = threading.RLock()

    def _error_recovery(self):
        self._ser.write(b"\n")
        self._ser.write(b"\n")
        self._ser.flush()
        time.sleep(0.1)
        self._ser.readall()

    def _exec_command(self, command: str) -> str:
        with self._lock:
            self._ser.write(command.encode() + b"\n")
            res = self._ser.readline().decode()
            if res.startswith("!") or res.startswith("?"):
                self._error_recovery()
                raise RuntimeError("Invalid command")
            else:
                return res

    def write1(self, addr: int, val: int) -> None:
        try:
            res = self._exec_command(f"W1,{addr},{val}")
            if not res.startswith("S"):
                raise RuntimeError("Failed to write")
        except:
            self._error_recovery()
            raise

    def write2(self, addr: int, val: int) -> None:
        try:
            res = self._exec_command(f"W2,{addr},{val}")
            if not res.startswith("S"):
                raise RuntimeError("Failed to write")
        except:
            self._error_recovery()
            raise

    def write4(self, addr: int, val: int) -> None:
        try:
            res = self._exec_command(f"W4,{addr},{val}")
            if not res.startswith("S"):
                raise RuntimeError("Failed to write")
        except:
            self._error_recovery()
            raise

    def read1(self, addr: int) -> int:
        try:
            res = self._exec_command(f"R1,{addr},0")
            return int(res)
        except:
            self._error_recovery()
            raise

    def read2(self, addr: int) -> int:
        try:
            res = self._exec_command(f"R2,{addr},0")
            return int(res)
        except:
            self._error_recovery()
            raise

    def read4(self, addr: int) -> int:
        try:
            res = self._exec_command(f"R4,{addr},0")
            return int(res)
        except:
            self._error_recovery()
            raise


class CurverunnerCommMock(CurverunnerComm):
    def __init__(self):
        self._regs = bytearray(256)

    def write1(self, addr: int, val: int) -> None:
        if addr < 0 or addr >= len(self._regs):
            return
        self._regs[addr] = val & 0xFF

    def write2(self, addr: int, val: int) -> None:
        if addr < 0 or addr + 1 >= len(self._regs):
            return

        self._regs[addr] = val & 0xFF
        self._regs[addr + 1] = (val >> 8) & 0xFF

    def write4(self, addr: int, val: int) -> None:
        if addr < 0 or addr + 3 >= len(self._regs):
            return

        self._regs[addr] = val & 0xFF
        self._regs[addr + 1] = (val >> 8) & 0xFF
        self._regs[addr + 2] = (val >> 16) & 0xFF
        self._regs[addr + 3] = (val >> 24) & 0xFF

    def read1(self, addr: int) -> int:
        return self._regs[addr]

    def read2(self, addr: int) -> int:
        return (self._regs[addr + 1] << 8) | self._regs[addr]

    def read4(self, addr: int) -> int:
        return (
            (self._regs[addr + 3] << 24)
            | (self._regs[addr + 2] << 16)
            | (self._regs[addr + 1] << 8)
            | self._regs[addr]
        )


def discover_devices_serial_by_id() -> List[Tuple[int, str]]:
    port_infos = comports()
    cr_list = []
    for port_info in port_infos:
        if port_info.serial_number is None:
            continue
        try:
            with serial.Serial(port_info.device, 115200, timeout=0.05, write_timeout=0.05) as ser:
                comm = CurverunnerCommSerial(ser)

                version = comm.read1(1)
                cr_list.append((version, port_info.device))
        except:
            continue

    return cr_list


def discover_devices_serial() -> List[str]:
    return [dev for _, dev in discover_devices_serial_by_id()]
