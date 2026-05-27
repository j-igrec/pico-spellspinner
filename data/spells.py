"""data/spells.py — lazy spell data loader.

The full spell list lives in data/spells.jsonl (one JSON-encoded spell per
line), so we never materialise all 400+ spells in RAM at once. This module
builds a small offset index at import time (~1.6 KB) and serves individual
spells on demand.

Public surface:
    count()  → number of spells
    get(i)   → spell at index i, as a 12-element list (field order matches
               the index constants in screens/spell_card.py)

Regenerate the .jsonl file with: python3 tools/build_spells.py
"""

import json

_PATH = 'data/spells.jsonl'


def _build_index():
    offsets = []
    with open(_PATH, 'rb') as f:
        off = 0
        for line in f:
            offsets.append(off)
            off += len(line)
    return offsets


_OFFSETS = _build_index()


def count():
    return len(_OFFSETS)


def get(i):
    with open(_PATH, 'rb') as f:
        f.seek(_OFFSETS[i])
        line = f.readline()
    return json.loads(line)
