"""
ST7789VW driver for Waveshare 1.14" 240×135 IPS LCD.

Exposes the same API as simulator/display.py so components run unchanged:
    fill(color)
    fill_rect(x, y, w, h, color)
    hline(x, y, w, color)
    vline(x, y, h, color)
    pixel(x, y, color)
    write(font, text, x, y, fg, bg=None)
    show()

Colors are (r, g, b) tuples — converted to RGB565 on flush.

Column/row offsets (X_OFFSET, Y_OFFSET) account for the 240×135 panel being
a window into the ST7789's 240×320 frame memory. These values are correct for
the Waveshare Pico-LCD-1.14 in landscape orientation. If the image appears
shifted, adjust _X_OFFSET and _Y_OFFSET at the top of this file.
"""

import struct
import time

_SWRESET = 0x01
_SLPOUT  = 0x11
_COLMOD  = 0x3A
_MADCTL  = 0x36
_INVON   = 0x21
_DISPON  = 0x29
_CASET   = 0x2A
_RASET   = 0x2B
_RAMWR   = 0x2C

# Panel offset within the ST7789's 240×320 frame memory (landscape mode).
_X_OFFSET = 40
_Y_OFFSET = 53


def _rgb565(color):
    r, g, b = color[0], color[1], color[2]
    c = ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)
    return c >> 8, c & 0xFF


class ST7789:
    def __init__(self, spi, width, height, cs, dc, rst, bl):
        self._spi    = spi
        self._cs     = cs
        self._dc     = dc
        self._rst    = rst
        self._bl     = bl
        self.width   = width
        self.height  = height
        self._buf    = bytearray(width * height * 2)
        self._init()

    # ── SPI primitives ────────────────────────────────────────────────────────

    def _cmd(self, cmd):
        self._dc.value(0)
        self._cs.value(0)
        self._spi.write(bytes([cmd]))
        self._cs.value(1)

    def _data(self, data):
        self._dc.value(1)
        self._cs.value(0)
        self._spi.write(data)
        self._cs.value(1)

    # ── Init sequence ─────────────────────────────────────────────────────────

    def _init(self):
        self._rst.value(0)
        time.sleep_ms(50)
        self._rst.value(1)
        time.sleep_ms(150)

        self._bl.value(1)

        self._cmd(_SWRESET);             time.sleep_ms(150)
        self._cmd(_SLPOUT);              time.sleep_ms(500)
        self._cmd(_COLMOD); self._data(b'\x55')   # 16-bit RGB565
        self._cmd(_MADCTL); self._data(b'\x70')   # landscape, BGR swap
        self._cmd(_INVON)                          # IPS panels need inversion
        self._cmd(_DISPON);              time.sleep_ms(100)

    # ── Window + flush ────────────────────────────────────────────────────────

    def _set_window(self, x0, y0, x1, y1):
        self._cmd(_CASET)
        self._data(struct.pack('>HH', x0 + _X_OFFSET, x1 + _X_OFFSET))
        self._cmd(_RASET)
        self._data(struct.pack('>HH', y0 + _Y_OFFSET, y1 + _Y_OFFSET))
        self._cmd(_RAMWR)

    def show(self):
        self._set_window(0, 0, self.width - 1, self.height - 1)
        self._dc.value(1)
        self._cs.value(0)
        self._spi.write(self._buf)
        self._cs.value(1)

    # ── Drawing API ───────────────────────────────────────────────────────────

    def fill(self, color):
        hi, lo = _rgb565(color)
        self._buf[:] = bytes([hi, lo]) * (self.width * self.height)

    def fill_rect(self, x, y, w, h, color):
        hi, lo = _rgb565(color)
        row = bytes([hi, lo]) * w
        for row_y in range(h):
            off = ((y + row_y) * self.width + x) * 2
            self._buf[off : off + w * 2] = row

    def hline(self, x, y, w, color):
        self.fill_rect(x, y, w, 1, color)

    def vline(self, x, y, h, color):
        self.fill_rect(x, y, 1, h, color)

    def pixel(self, x, y, color):
        hi, lo = _rgb565(color)
        off = (y * self.width + x) * 2
        self._buf[off]     = hi
        self._buf[off + 1] = lo

    def write(self, font, text, x, y, fg, bg=None):
        """Render font_to_py bitmap text. bg=None renders transparently."""
        fg_hi, fg_lo = _rgb565(fg)
        bg_hi = bg_lo = None
        if bg is not None:
            bg_hi, bg_lo = _rgb565(bg)
        cx = x
        for ch in text:
            try:
                glyph, h, w = font.get_ch(ch)
            except Exception:
                continue
            row_bytes = (w + 7) // 8
            for row in range(h):
                if y + row >= self.height:
                    break
                off = ((y + row) * self.width + cx) * 2
                for col in range(w):
                    if cx + col >= self.width:
                        break
                    byte_idx = row * row_bytes + col // 8
                    bit      = 7 - (col % 8)
                    if byte_idx < len(glyph) and glyph[byte_idx] & (1 << bit):
                        self._buf[off]     = fg_hi
                        self._buf[off + 1] = fg_lo
                    elif bg is not None:
                        self._buf[off]     = bg_hi
                        self._buf[off + 1] = bg_lo
                    off += 2
            cx += w
