"""screens/start.py — Title screen.

A → enter the spinner (transitions to spell_card).
B → no-op.

Standalone:
    python3 pico-ui-kit/simulator/run.py screens/start.py
"""

import sys

try:
    import os as _os
    _here = _os.path.dirname(_os.path.abspath(__file__))
    _root = _os.path.dirname(_here)
    _ui   = _os.path.join(_root, "pico-ui-kit")
    _lib  = _os.path.join(_root, "lib")
    for _p in (_root, _ui, _lib):
        if _p not in sys.path:
            sys.path.insert(0, _p)
except (AttributeError, NameError):
    pass

import fonts.monob16 as _bold16
import fonts.monor8  as _reg8

from components.badge import badge
from components.button import button
import icons.option_a as _option_a_icon

from drawing.text import text_w
from tokens.semantic import STRUCTURE_SURFACES_LEVEL_0, TEXT_COLOUR_PRIMARY
from tokens.viewport import GAP_3

_BG       = STRUCTURE_SURFACES_LEVEL_0
_TEXT_PRI = TEXT_COLOUR_PRIMARY

_VERSION = 'V0.0.1'

_TITLE_LINE_1 = 'SPELL'
_TITLE_LINE_2 = 'SPINNER'

_BTN_LABEL = 'Start'


def draw(display):
    w = getattr(display, 'width', 240)
    h = getattr(display, 'height', 135)
    display.fill(_BG)

    badge_w = _reg8.max_width() * len(_VERSION) + 8 + 4 + 4
    line1_w = _bold16.max_width() * len(_TITLE_LINE_1)
    line2_w = _bold16.max_width() * len(_TITLE_LINE_2)
    title_h = _bold16.height() * 2
    btn_w   = text_w(_reg8, _BTN_LABEL) + 8 + 12 + 2

    badge_h = _reg8.height() + 4
    btn_h   = _reg8.height() + 8 + 2

    block_h = badge_h + GAP_3 + title_h + GAP_3 + btn_h
    y = (h - block_h) // 2

    badge_x = (w - badge_w) // 2
    badge(display, _reg8, _VERSION, badge_x, y,
          colour='information', emphasis='subtle', type='semantic',
          status_dot=False, icon=False)
    y += badge_h + GAP_3

    line1_x = (w - line1_w) // 2
    display.write(_bold16, _TITLE_LINE_1, line1_x, y, _TEXT_PRI, None)
    line2_x = (w - line2_w) // 2
    display.write(_bold16, _TITLE_LINE_2, line2_x, y + _bold16.height(), _TEXT_PRI, None)
    y += title_h + GAP_3

    btn_x = (w - btn_w) // 2
    button(display, _reg8, _BTN_LABEL, btn_x, y,
           type='primary', trail_icon=_option_a_icon)

    display.show()


def on_input(key, display):
    if key == 'A':
        from screens import router
        router.goto('spell_card', display)
