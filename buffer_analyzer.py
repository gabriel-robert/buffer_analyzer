import sys
import curses
from ui import *

data = bytearray([
0x00, 0x02, 0x3a, 0x00, 0x01, 0x00, 0x00, 0x00,
0x00, 0x00, 0x00, 0x00, 0x23, 0x01, 0xcf, 0x0d,
0xd4, 0x57, 0xe6, 0x61, 0x7a, 0xd0, 0xaf, 0x05,
0xea, 0x38, 0xc0, 0xfa, 0x65, 0x21, 0xe1, 0xc6,
0x16, 0x85, 0x1a, 0xb2, 0xe8, 0x27, 0x35, 0x8e,
0x5a, 0x88, 0x5f, 0x6a, 0xb0, 0xc2, 0x47, 0x31,
0x82, 0x50, 0x73, 0x15, 0x78, 0x8d, 0xde, 0xc8,
0x9c, 0x5c
])

class WordView(TextView):

    def __init__(self, parent, base=16):
        super().__init__(parent)
        self.word = bytearray([])
        self.word_size = 1
        self.byteorder = sys.byteorder
        self.base = base

    def set_format(self, format):
        self.format = format

    def set_word(self, word, word_size):
        self.word = word
        self.word_size = word_size

    def refresh(self, *args, **kwargs):
        format = "%%0%dx" % (self.word_size * 2)
        if self.base == 10:
            format = "%d"
        word = format % int.from_bytes(self.word, self.byteorder)

        s = "0x%s" % word
        if self.base == 10:
            s = "%s" % word

        self.set_text(s)

        return super().refresh(*args, **kwargs)

    def get_word_size(self):
        return self.word_size

    def toggle_byteorder(self):
        self.byteorder = "little" if self.byteorder == "big" else "big"

    def get_byteorder(self):
        return self.byteorder

class PacketView(View):

    def __init__(self, parent):
        super().__init__(parent)
        self.set_highlight()

    def refresh(self, x, y, max_width, max_height, width_flags=Window.EXPAND, height_flags=Window.EXPAND):
        return self.print_packet(x, y, max_width, max_height)

    def set_packet(self, buffer):
        self.buffer = buffer

    def set_highlight(self, start=0, length=0):
        self.highlight = (start, length)

    def get_highlight(self):
        start, length = self.highlight
        return start, length, self.get_packet(start, length)

    def get_packet(self, start=0, length=None):
        if length is None:
            length = len(self.buffer) - start
        end = min(start + length, len(self.buffer))
        return self.buffer[start:end]

    def get_length(self):
        return len(self.buffer)

    def print_packet(self, x, y, max_width, max_height, format="%02x"):
        _x = 0
        _y = 0
        start, length = self.highlight
        for i in range(len(self.buffer)):
            if i >= start and i < start + length:
                color = RED_ON_WHITE
            else:
                color = WHITE_ON_BLACK

            byte = format % self.buffer[i]

            if _x + len(byte) >= max_width - Window.BORDER_WIDTH:
                if (_y + 1 >= max_height - Window.BORDER_HEIGHT):
                    return _x, _y
                _y += 1
                _x = 0

            self.get_screen().addstr(y + _y, x + _x, byte, curses.color_pair(color))
            _x += len(byte)

            if i + 1 >= start + length:
                color = WHITE_ON_BLACK

            if i < len(self.buffer):
                self.get_screen().addstr(y + _y, x + _x, " ", curses.color_pair(color))
                _x += 1
        _y += 1
        return _x, _y

def main(stdscr):
    init_ui()
    def refresh():
        start, length, word = packet_view.get_highlight()
        word_view_hex.set_word(word, length)
        word_view_dec.set_word(word, length)
        cursor_view.set_text("Buffer (%d bytes, %d / %d)" % (packet_view.get_length(), packet_view.get_highlight()[0], packet_view.get_length() - 1))
        byteorder_view.set_text("Word (%d bits, %s endian):" % (word_view_dec.get_word_size() * 8, word_view_dec.get_byteorder()))

    def _on_key_up():
        start, length, word = packet_view.get_highlight()
        if length < 8:
            length *= 2
        packet_view.set_highlight(start, length)
        refresh()

    def _on_key_down():
        start, length, word = packet_view.get_highlight()
        if length > 1:
            length = int(length / 2)
        packet_view.set_highlight(start, length)
        refresh()

    def _on_key_left():
        start, length, word = packet_view.get_highlight()
        packet_view.set_highlight(start - 1 if start > 0 else start, length)
        refresh()

    def _on_key_right():
        start, length, word = packet_view.get_highlight()
        packet_view.set_highlight(start + 1 if start + 1 < packet_view.get_length() else start, length)
        refresh()

    def _on_key_b():
        word_view_hex.toggle_byteorder()
        word_view_dec.toggle_byteorder()
        refresh()

    def _on_key_q():
        exit(0)

    window = Window(stdscr, "Buffer Analyzer")

    packet_view = PacketView(window)
    packet_view.set_packet(data)
    packet_view.set_highlight(0, 1)

    word_view_hex = WordView(window)
    _, word_size, word = packet_view.get_highlight()
    word_view_hex.set_word(word, word_size)

    word_view_dec = WordView(window, 10)
    _, word_size, word = packet_view.get_highlight()
    word_view_dec.set_word(word, word_size)

    cursor_view = TextView(window, "Buffer (%d bytes, %d / %d)" % (packet_view.get_length(), packet_view.get_highlight()[0], packet_view.get_length() - 1))
    byteorder_view = TextView(window, "Word (%d bits, %s endian):" % (word_view_dec.get_word_size() * 8, word_view_dec.get_byteorder()))

    window.add_child(cursor_view, 0, 0, *window.get_size())
    window.add_child(packet_view, 0, 0, *window.get_size())
    window.add_child(Separator(window), 0, 0, *window.get_size())
    window.add_child(byteorder_view, 0, 0, *window.get_size())
    window.add_child(word_view_hex, 0, 0, *window.get_size())
    window.add_child(word_view_dec, 0, 0, *window.get_size())

    window.add_key_handler(curses.KEY_UP, _on_key_up)
    window.add_key_handler(curses.KEY_DOWN, _on_key_down)
    window.add_key_handler(curses.KEY_LEFT, _on_key_left)
    window.add_key_handler(curses.KEY_RIGHT, _on_key_right)
    window.add_key_handler(ord('b'), _on_key_b)
    window.add_key_handler(ord('q'), _on_key_q)

    window.mainloop()

if __name__ == "__main__":
    curses.wrapper(main)
