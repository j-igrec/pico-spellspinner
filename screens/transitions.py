"""screens/transitions.py

Screen-to-screen transitions. Currently exports one effect:

    curtain(display, draw_next)
        Retro curtain wipe — black bars converge from top and bottom,
        the new screen is rendered behind them, and the bars retract to
        reveal the new content.

        Tune via _STEPS and _FRAME_MS at the top of this module:
          - _STEPS = 0 → instant cut (default; no visible animation)
          - _STEPS = N, _FRAME_MS = ms → 2N frames at ms each

Compatible with both MicroPython (uses time.sleep_ms) and CPython simulator.
"""

try:
    from utime import sleep_ms as _sleep_ms
except ImportError:
    import time as _time
    def _sleep_ms(ms):
        _time.sleep(ms / 1000.0)

from drawing.rect import fill_rect
from tokens.semantic import STRUCTURE_SURFACES_LEVEL_0

_BG = STRUCTURE_SURFACES_LEVEL_0

_STEPS = 0
_FRAME_MS = 8


def curtain(display, draw_next):
    """Animate a curtain between the current screen and draw_next.

    draw_next is the next screen's draw(display) function. It is invoked
    on every reveal frame so the new content fills in behind the retreating
    bars without needing a separate back buffer.

    _STEPS = 0 short-circuits to an instant cut — just renders draw_next.
    """
    if _STEPS <= 0:
        draw_next(display)
        display.show()
        return

    w = getattr(display, 'width', 240)
    h = getattr(display, 'height', 135)
    half = (h + 1) // 2

    # Phase 1 — close: bars converge from top + bottom.
    for i in range(1, _STEPS + 1):
        bar = (half * i) // _STEPS
        fill_rect(display, 0, 0, w, bar, _BG)
        fill_rect(display, 0, h - bar, w, bar, _BG)
        display.show()
        _sleep_ms(_FRAME_MS)

    # Phase 2 — open: re-render new content, overlay shrinking bars.
    for i in range(_STEPS - 1, -1, -1):
        draw_next(display)
        bar = (half * i) // _STEPS
        if bar > 0:
            fill_rect(display, 0, 0, w, bar, _BG)
            fill_rect(display, 0, h - bar, w, bar, _BG)
        display.show()
        _sleep_ms(_FRAME_MS)
