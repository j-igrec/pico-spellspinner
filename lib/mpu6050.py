import struct

_PWR_MGMT_1   = 0x6B
_ACCEL_XOUT_H = 0x3B
_ACCEL_SCALE  = 16384.0   # LSB/g at ±2g full-scale range (default)


class MPU6050:
    def __init__(self, i2c, addr=0x68):
        self._i2c  = i2c
        self._addr = addr
        # Clear sleep bit so the device stops being in power-save mode.
        i2c.writeto_mem(addr, _PWR_MGMT_1, b'\x00')

    @property
    def accel(self):
        """Return (ax, ay, az) in g."""
        raw = self._i2c.readfrom_mem(self._addr, _ACCEL_XOUT_H, 6)
        ax, ay, az = struct.unpack('>hhh', raw)
        return ax / _ACCEL_SCALE, ay / _ACCEL_SCALE, az / _ACCEL_SCALE
