#!/usr/bin/env python3
"""
tools/build_spells.py

Converts data/src/spell-sheet.csv -> data/spells.jsonl (one JSON-encoded
spell per line). The Pico's data/spells.py reads this file lazily so we
never have to load all spells into RAM at once.

Usage:
    python3 tools/build_spells.py
"""

import csv
import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(_HERE, '..', 'data', 'src', 'spell-sheet.csv')
DST = os.path.join(_HERE, '..', 'data', 'spells.jsonl')

_CLASS_COLS = ['Bard', 'Cleric', 'Druid', 'Paladin', 'Ranger', 'Sorcerer', 'Warlock', 'Wizard']

_CASTING_TIME_ALIASES = {
    '1 action': 'Action',
    'action':   'Action',
    '1 bonus action': 'Bonus Action',
    'bonus action':   'Bonus Action',
    '1 reaction': 'Reaction',
    'reaction':   'Reaction',
    '1 minute':  '1 Min',
    '10 minutes': '10 Min',
    '1 hour':    '1 Hour',
    '8 hours':   '8 Hours',
    '12 hours':  '12 Hours',
    '24 hours':  '24 Hours',
}


def _components(raw):
    """Return (v, s, m) booleans from raw component string, stripping asterisks."""
    tokens = {t.strip() for t in re.sub(r'\*+', '', raw).split(',')}
    return 'V' in tokens, 'S' in tokens, 'M' in tokens


def _casting_time(raw):
    return _CASTING_TIME_ALIASES.get(raw.strip().lower(), raw.strip())


def _classes(row):
    return [c for c in _CLASS_COLS if row.get(c, '').strip() == 'Yes']


def _level_sort_key(spell):
    lvl = spell['level']
    try:
        return 0 if lvl == 'Cantrip' else int(lvl)
    except ValueError:
        return 99


def _description(raw):
    text = raw.replace('\r\n', '\n').replace('\r', '\n')
    return ' '.join(text.split())


def build():
    with open(SRC, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        _ = reader.fieldnames           # trigger header read
        cleaned = [h.strip() for h in reader.fieldnames]
        # The current sheet leaves the School column header blank — recover by
        # naming the second blank field "School".
        if len(cleaned) > 1 and cleaned[1] == '':
            cleaned[1] = 'School'
        reader.fieldnames = cleaned
        rows = list(reader)

    spells = []
    skipped = 0
    for row in rows:
        name = row.get('Spell Name', '').strip()
        level = (row.get('Level') or row.get('Option_A') or '').strip()
        if not name or not level:
            skipped += 1
            continue
        v, s, m = _components(row.get('Components', ''))
        spells.append({
            'name':         name,
            'level':        level,
            'ritual':       row.get('Ritual', '').strip() == 'Yes',
            'v':            v,
            's':            s,
            'm':            m,
            'casting_time': _casting_time(row.get('Casting Time', '')),
            'use':          row.get('Use', '').strip(),
            'page':         row.get('Page No.', '').strip(),
            'classes':      _classes(row),
            'school':       row.get('School', '').strip().title(),
            'description':  _description(row.get('Discription', '')),
        })

    spells.sort(key=_level_sort_key)

    # One JSON array per line. Field order must match spell_card.py constants:
    #   0 name  1 level  2 ritual  3 v  4 s  5 m
    #   6 casting_time  7 use  8 page  9 classes  10 school  11 description
    with open(DST, 'w', encoding='utf-8') as f:
        for s in spells:
            entry = [
                s['name'],
                s['level'],
                s['ritual'],
                s['v'],
                s['s'],
                s['m'],
                s['casting_time'],
                s['use'],
                s['page'],
                s['classes'],
                s['school'],
                s['description'],
            ]
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    print('Spells written : ' + str(len(spells)))
    print('Rows skipped   : ' + str(skipped))
    print('Output         : ' + os.path.abspath(DST))


if __name__ == '__main__':
    build()
