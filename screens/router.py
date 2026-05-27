"""screens/router.py

Tiny screen router. Holds the active screen module and dispatches input
to it. goto(name, display) animates a curtain transition between screens.

Usage:
    from screens import router
    router.goto('start', display)        # initial render — no transition
    ...
    router.dispatch('A', display)        # forward a key event to the active screen

Each screen module must expose:
    draw(display)
    on_input(key, display)
"""

import gc

from screens import transitions as _transitions

_REGISTRY = ('start', 'spell_card', 'details')

_current_name = None
_current_module = None


def _load(name):
    gc.collect()
    if name == 'start':
        from screens import start as mod
    elif name == 'spell_card':
        from screens import spell_card as mod
    elif name == 'details':
        from screens import details as mod
    else:
        raise ValueError('unknown screen: ' + name)
    return mod


def current():
    return _current_module


def name():
    return _current_name


def goto(target, display, animate=True):
    """Switch to screen `target`. Renders the curtain if animate=True,
    otherwise renders straight (use for initial boot)."""
    global _current_name, _current_module
    next_mod = _load(target)
    if animate and _current_module is not None:
        _transitions.curtain(display, next_mod.draw)
    else:
        next_mod.draw(display)
    _current_name = target
    _current_module = next_mod


def dispatch(key, display):
    if _current_module is not None:
        _current_module.on_input(key, display)
