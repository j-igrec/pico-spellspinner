"""screens/details.py — Detailed spell view.

Reads the current spell index from screens.spell_card so the details page
always shows the spell that was on screen when the user pressed A.

UP/DOWN  → scroll the description
B        → goto spell_card

Standalone:
    python3 pico-ui-kit/simulator/run.py screens/details.py
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

from components.button import button
import icons.option_b as _option_b_icon

from drawing.rect import fill_rounded_rect

from tokens.semantic import (
    STRUCTURE_SURFACES_LEVEL_0,
    STRUCTURE_SURFACES_LEVEL_2,
    TEXT_COLOUR_PRIMARY,
)
from tokens.viewport import GAP_2, GAP_4, PADDING_3, RADIUS_SM

from data import spells as _spells_data
from screens import spell_card as _spell_card

_NAME = 0
_DESCRIPTION = 11

_BG       = STRUCTURE_SURFACES_LEVEL_0
_CARD_BG  = STRUCTURE_SURFACES_LEVEL_2
_TEXT_PRI = TEXT_COLOUR_PRIMARY

_PAD      = GAP_4              # 12 around the card
_CARD_PAD = PADDING_3          # 8 inside the card

# State — how many lines we've scrolled in the description.
_scroll = 0


def draw(display):
    spell = _spell_card.current_spell()
    if spell is None:
        spell = _spells_data.get(0)
    _render(display, spell)


def on_input(key, display):
    global _scroll
    if key == 'B':
        from screens import router
        _scroll = 0
        router.goto('spell_card', display)
        return
    if key == 'UP':
        if _scroll > 0:
            _scroll -= 1
            _render(display, _spell_card.current_spell() or _spells_data.get(0))
        return
    if key == 'DOWN':
        _scroll += 1
        _render(display, _spell_card.current_spell() or _spells_data.get(0))
        return


def _render(display, spell):
    w = getattr(display, 'width', 240)
    h = getattr(display, 'height', 135)

    display.fill(_BG)

    card_x = _PAD
    card_y = _PAD
    card_w = w - _PAD * 2
    card_h = h - _PAD * 2
    fill_rounded_rect(display, card_x, card_y, card_w, card_h, RADIUS_SM, _CARD_BG)

    inner_x = card_x + _CARD_PAD
    inner_y = card_y + _CARD_PAD
    inner_w = card_w - _CARD_PAD * 2

    # Top row (level + ritual + V·S·M) intentionally hidden — the description
    # gets more room. Re-enable by restoring _draw_top_row().

    y = inner_y

    display.write(_bold16, spell[_NAME], inner_x, y, _TEXT_PRI, None)
    y += _bold16.height() + GAP_2

    btn_h = _reg8.height() + 8 + 2
    desc_y_end = card_y + card_h - _CARD_PAD - btn_h - GAP_2
    _draw_description(display, _reg8, spell[_DESCRIPTION], inner_x, y, inner_w,
                      desc_y_end, _CARD_BG)

    btn_y = card_y + card_h - _CARD_PAD - btn_h
    button(display, _reg8, 'Back', inner_x, btn_y,
           type='primary', lead_icon=_option_b_icon)

    display.show()


def _wrap(text, chars_per_line):
    """Word-wrap into a list of lines (no max). Empty input → []."""
    if not text:
        return []
    lines = []
    current = ''
    for word in text.split():
        candidate = (current + ' ' + word).strip()
        if len(candidate) <= chars_per_line:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
            while len(current) > chars_per_line:
                lines.append(current[:chars_per_line])
                current = current[chars_per_line:]
    if current:
        lines.append(current)
    return lines


def _draw_description(display, font, text, x, y, w, y_end, bg):
    global _scroll
    chars_per_line = w // font.max_width()
    if chars_per_line < 1:
        chars_per_line = 1
    lines = _wrap(text, chars_per_line)
    line_h = font.height() + 1
    visible = max(0, (y_end - y) // line_h)

    max_scroll = max(0, len(lines) - visible)
    if _scroll > max_scroll:
        _scroll = max_scroll

    start = _scroll
    end   = min(len(lines), start + visible)
    for i, line in enumerate(lines[start:end]):
        display.write(font, line, x, y + i * line_h, _TEXT_PRI, bg)
