import attr
import contextlib as ctxlib
import pathlib as fs
import typing as t
import unicodedata as ucd

from Xlib.display import Display


unicode_to_keysym = {
    int(column[1][1:], base=16): int(column[0][2:], base=16)
    for column in [
        line.split()
        for line in fs.Path('keysyms.txt').read_text().strip().splitlines()
        if not line.startswith('#') and line.strip()
    ]
    if column[0][:2] == '0x' and column[1][:1] == 'U' and column[2] == '.'
}


@ctxlib.contextmanager
def keyboard_from_display(display=None):
    if display is None:
        display = Display()

    kbd = Keyboard(display)
    yield kbd
    kbd.flush()

@attr.s
class Keyboard:
    display = attr.ib()
    changes = attr.ib(init=False, default=attr.Factory(dict))

    def map(self, glyph):
        if ord(glyph) in unicode_to_keysym:
            # Pre-unicode standard
            return unicode_to_keysym[ord(glyph)]
        else:
            # Newer values
            return ord(glyph) + 0x01000000

    def flush(self):
        for keycode, keysyms in self.changes.items():
            self.display.change_keyboard_mapping(keycode, [keysyms])

        self.display.flush()

    def __getitem__(self, item: str):
        keysym  = self.map(item)
        keycode = self.display._keymap_syms[keysym][0][1]

        return Key(keycode)

    def __setitem__(self, item, glyph: str):
        if item.keycode not in self.changes:
            self.changes[item.keycode] = \
                self.display._keymap_codes[item.keycode]

        self.changes[item.keycode][item.modifier] = self.map(glyph)


@attr.s(frozen=True)
class Key:
    keycode  = attr.ib()
    modifier = attr.ib(default=0)


@attr.s(frozen=True)
class Modifier:
    modifier = attr.ib()

    def __and__(self, x):
        return attr.evolve(x, modifier=self.modifier + x.modifier)

    __rand__ = __and__


# Positions in the KeySym-list. Not sure how to find them via the API.
# Should match most default xkb settings for western international
# keyboard layouts.
Shift = Modifier(1)
AltGr = Modifier(4)
