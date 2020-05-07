import curses

WHITE_ON_BLACK = 1
RED_ON_WHITE = 2
BLUE_ON_WHITE = 3

class Window(object):

    BORDER_WIDTH = 2
    BORDER_HEIGHT = 2

    WRAP = 0
    EXPAND = 1

    def __init__(self, scr, title):
        self.scr = scr
        self.title = title
        self.height, self.width = self.scr.getmaxyx()
        self.children = []
        self.key_handlers = {}
        self.scr.clearok(True)

    def get_size(self):
        return self.width - Window.BORDER_WIDTH, self.height - Window.BORDER_HEIGHT

    def set_title(self, title):
        self.title = title

    def refresh(self):
        self.scr.clear()
        self.scr.border()
        self.scr.addstr(0, int(self.width / 2) - int(len(self.title) / 2), self.title, curses.color_pair(BLUE_ON_WHITE))

        x = Window.BORDER_WIDTH
        y = Window.BORDER_HEIGHT

        for child in self.children:
            width, height = child.refresh(x, y, *self.get_size())
            y += height
            if y >= self.height - Window.BORDER_HEIGHT:
                break
        self.scr.refresh()

    def add_child(self, window, x, y, width_flags, height_flags):
        self.children.append(window)

    def add_key_handler(self, key, handler):
        if not key in self.key_handlers:
            self.key_handlers[key] = []
        self.key_handlers[key].append(handler)

    def remove_key_handler(self, key, handler):
        pass

    def mainloop(self):
        while True:
            self.refresh()
            ch = self.scr.getch()
            if ch == curses.KEY_RESIZE:
                self.height, self.width = self.scr.getmaxyx()
                self.scr.clear()
            for key, handlers in self.key_handlers.items():
                if ch == key:
                    for handler in handlers:
                        handler()

class View(object):

    def __init__(self, parent):
        self.parent = parent
        self.scr = parent.scr
        self.real_height = None
        self.real_width = None
        self.height_flags = Window.EXPAND
        self.width_flags = Window.EXPAND

    def get_parent(self):
        return self.parent

    def get_screen(self):
        return self.scr

    def set_flags(self, height_flags, width_flags):
        self.height_flags = height_flags
        self.width_flags = width_flags

    def get_flags(self):
        return self.width_flags, self.height_flags

    def set_real_size(self, width, height):
        self.real_width = width
        self.real_height = height

    def get_real_size(self):
        return self.real_width, self.real_height

    def refresh(self, x, y, max_width, max_height, width_flags=Window.EXPAND, height_flags=Window.EXPAND):
        pass

class Separator(View):

    def __init__(self, parent, height=1, color=WHITE_ON_BLACK):
        super().__init__(parent)
        self.height = height
        self.color = color

    def refresh(self, x, y, max_width, max_height, width_flags=Window.EXPAND, height_flags=Window.EXPAND):
        for _y in range(self.height):
            line = "".join([" " for _ in range(max_width - x)])
            self.scr.addstr(y + _y, x, line, curses.color_pair(self.color))
        return len(line), self.height

class TextView(View):
    def __init__(self, parent, text="", color=WHITE_ON_BLACK):
        super().__init__(parent)
        self.text = text
        self.color = WHITE_ON_BLACK

    def refresh(self, x, y, max_width, max_height, width_flags=Window.EXPAND, height_flags=Window.EXPAND):
        _x = 0
        _y = 0
        for c in self.text:
            if _x + len(c) >= max_width - Window.BORDER_WIDTH:
                if (_y + 1 >= max_height - - Window.BORDER_HEIGHT):
                    return _x, _y
                _y += 1
                _x = x
            self.scr.addstr(y + _y, x + _x, c, curses.color_pair(self.color))
            _x += len(c)
        _y += 1
        return _x, _y

    def set_text(self, text):
        self.text = text

def init_ui():
    curses.init_pair(WHITE_ON_BLACK, curses.COLOR_WHITE, curses.COLOR_BLACK)
    curses.init_pair(RED_ON_WHITE, curses.COLOR_RED, curses.COLOR_WHITE)
    curses.init_pair(BLUE_ON_WHITE, curses.COLOR_BLUE, curses.COLOR_WHITE)
