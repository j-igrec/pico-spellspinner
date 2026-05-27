"""main.py

Hardware entry point for pico-spellspinner.

On the Pico: initialises display + IMU + buttons + joystick, then routes
events through screens.router which dispatches to the active screen
(start → spell_card → details).

On desktop: pico-ui-kit/simulator/run.py imports this module and calls
draw + on_input directly.
"""

import sys

# Desktop only: put the project root, pico-ui-kit, and lib/ on sys.path so the
# imports below resolve. On the Pico, files live flat at the device root, so
# this no-ops.
try:
    import os as _os
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _ui   = _os.path.join(_here, "pico-ui-kit")
    _lib  = _os.path.join(_here, "lib")
    for _p in (_here, _ui, _lib):
        if _p not in sys.path:
            sys.path.insert(0, _p)
except (AttributeError, NameError):
    pass

import config
from screens import router


def draw(display):
    """Initial render — sends the user to the start screen."""
    if router.current() is None:
        router.goto('start', display, animate=False)
    else:
        router.current().draw(display)


def on_input(key, display):
    print('KEY:', key)
    router.dispatch(key, display)


# ── Hardware main loop ────────────────────────────────────────────────────────

try:
    import machine
    import utime
    from lib.st7789 import ST7789
    from lib.mpu6050 import MPU6050
    _HARDWARE = True
except ImportError:
    _HARDWARE = False


def _hardware_main():
    spi = machine.SPI(
        config.LCD_SPI,
        baudrate=31_250_000,
        polarity=0,
        phase=0,
        sck=machine.Pin(config.LCD_CLK),
        mosi=machine.Pin(config.LCD_MOSI),
    )
    display = ST7789(
        spi, 240, 135,
        cs=machine.Pin(config.LCD_CS,  machine.Pin.OUT, value=1),
        dc=machine.Pin(config.LCD_DC,  machine.Pin.OUT, value=0),
        rst=machine.Pin(config.LCD_RST, machine.Pin.OUT, value=1),
        bl=machine.Pin(config.LCD_BL,  machine.Pin.OUT, value=1),
    )

    try:
        i2c = machine.I2C(
            config.IMU_I2C,
            sda=machine.Pin(config.IMU_SDA),
            scl=machine.Pin(config.IMU_SCL),
        )
        imu = MPU6050(i2c, addr=config.IMU_ADDR)
    except OSError as e:
        print('IMU not detected, shake disabled:', e)
        imu = None

    # All buttons + joystick directions are active-low with internal pull-up.
    inputs = (
        ('A',     machine.Pin(config.BTN_A,    machine.Pin.IN, machine.Pin.PULL_UP)),
        ('B',     machine.Pin(config.BTN_B,    machine.Pin.IN, machine.Pin.PULL_UP)),
        ('UP',    machine.Pin(config.JOY_UP,   machine.Pin.IN, machine.Pin.PULL_UP)),
        ('DOWN',  machine.Pin(config.JOY_DOWN, machine.Pin.IN, machine.Pin.PULL_UP)),
        ('LEFT',  machine.Pin(config.JOY_LEFT, machine.Pin.IN, machine.Pin.PULL_UP)),
        ('RIGHT', machine.Pin(config.JOY_RIGHT, machine.Pin.IN, machine.Pin.PULL_UP)),
        ('CTR',   machine.Pin(config.JOY_CTR,  machine.Pin.IN, machine.Pin.PULL_UP)),
    )

    draw(display)

    now = utime.ticks_ms()
    last_shake = now
    last_fired = {key: now for key, _ in inputs}
    imu_warned = False
    shake_threshold_sq = config.SHAKE_THRESHOLD * config.SHAKE_THRESHOLD

    while True:
        now = utime.ticks_ms()

        if imu is not None:
            try:
                ax, ay, az = imu.accel
                mag_sq = ax * ax + ay * ay + az * az
                if mag_sq > shake_threshold_sq and utime.ticks_diff(now, last_shake) > config.SHAKE_DEBOUNCE:
                    last_shake = now
                    on_input('SHAKE', display)
            except OSError as e:
                if not imu_warned:
                    print('IMU read failed:', e)
                    imu_warned = True

        for key, pin in inputs:
            if not pin.value() and utime.ticks_diff(now, last_fired[key]) > config.BTN_DEBOUNCE:
                last_fired[key] = now
                on_input(key, display)

        utime.sleep_ms(20)


if _HARDWARE:
    _hardware_main()
