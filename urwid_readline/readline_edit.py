import re
import string
import unicodedata
import urwid


def _clamp(number, min_value, max_value):
    return max(min_value, min(max_value, number))


def _is_valid_key(ch):
    return urwid.util.is_wide_char(ch, 0) or (len(ch) == 1 and ord(ch) >= 32)


class ReadlineEdit(urwid.Text):
    signals = ['change']

    def __init__(
            self,
            *args,
            word_chars=string.ascii_letters + string.digits + '_',
            **kwargs):
        super().__init__(*args, **kwargs)
        self._word_regex1 = re.compile(
            '([%s]+)' % '|'.join(re.escape(ch) for ch in word_chars))
        self._word_regex2 = re.compile(
            '([^%s]+)' % '|'.join(re.escape(ch) for ch in word_chars))
        self._edit_pos = 0

    @property
    def edit_pos(self):
        return self._edit_pos

    @edit_pos.setter
    def edit_pos(self, pos):
        self._edit_pos = _clamp(pos, 0, len(self.text))
        self._invalidate()

    @property
    def text(self):
        return self.get_text()[0]

    @text.setter
    def text(self, text):
        self.set_text(text)
        self.edit_pos = _clamp(self.edit_pos, 0, len(text))
        urwid.signals.emit_signal(self, 'change', self, text)

    def render(self, size, focus=False):
        (maxcol,) = size
        canv = urwid.Text.render(self, (maxcol,))
        if focus:
            canv = urwid.CompositeCanvas(canv)
            canv.cursor = (
                min(
                    urwid.util.calc_width(self._text, 0, self._edit_pos),
                    maxcol - 1),
                0)
        return canv

    def selectable(self):
        return True

    def keypress(self, _size, key):
        keymap = {
            'ctrl f':         self.forward_char,
            'ctrl b':         self.backward_char,
            'right':          self.forward_char,
            'left':           self.backward_char,
            'ctrl a':         self.beginning_of_line,
            'ctrl e':         self.end_of_line,
            'home':           self.beginning_of_line,
            'end':            self.end_of_line,
            'meta f':         self.forward_word,
            'meta b':         self.backward_word,
            'shift right':    self.forward_word,
            'shift left':     self.backward_word,

            'ctrl d':         self.delete_char,
            'ctrl h':         self.backward_delete_char,
            'delete':         self.delete_char,
            'backspace':      self.backward_delete_char,
            'ctrl u':         self.kill_whole_line,
            'ctrl k':         self.kill_line,
            'meta d':         self.kill_word,
            'ctrl w':         self.backward_kill_word,
            'meta backspace': self.backward_kill_word,
            'ctrl t':         self.transpose_chars,
        }
        if key in keymap:
            keymap[key]()
            return None
        elif _is_valid_key(key):
            self._insert_char_at_cusor(key)
            return None
        return key

    def _insert_char_at_cusor(self, key):
        self.text = (
            self.text[0:self.edit_pos] + key + self.text[self.edit_pos:])
        self.edit_pos += 1

    def backward_char(self):
        if self.edit_pos > 0:
            self.edit_pos -= 1

    def forward_char(self):
        if self.edit_pos < len(self.text):
            self.edit_pos += 1

    def backward_word(self):
        iterator = self._word_regex1.finditer(self.text[0:self.edit_pos][::-1])
        for match in iterator:
            self.edit_pos -= match.end(1)
            return
        self.edit_pos = 0

    def forward_word(self):
        iterator = self._word_regex2.finditer(self.text[self.edit_pos:])
        for match in iterator:
            self.edit_pos += match.end(1)
            return
        self.edit_pos = len(self.text)

    def delete_char(self):
        if self.edit_pos < len(self.text):
            self.text = (
                self.text[0:self.edit_pos] + self.text[self.edit_pos+1:])

    def backward_delete_char(self):
        if self.edit_pos > 0:
            self.edit_pos -= 1
            self.text = (
                self.text[0:self.edit_pos] + self.text[self.edit_pos+1:])

    def kill_whole_line(self):
        self.text = ''
        self.edit_pos = 0

    def kill_line(self):
        self.text = self.text[0:self.edit_pos]

    def backward_kill_word(self):
        pos = self.edit_pos
        self.backward_word()
        self.text = self.text[0:self.edit_pos] + self.text[pos:]

    def kill_word(self):
        pos = self.edit_pos
        self.forward_word()
        self.text = self.text[0:pos] + self.text[self.edit_pos:]
        self.edit_pos = pos

    def beginning_of_line(self):
        self.edit_pos = 0

    def end_of_line(self):
        self.edit_pos = len(self.text)

    def transpose_chars(self):
        self.edit_pos = max(2, self.edit_pos + 1)
        if len(self.text) >= 2:
            self.text = (
                self.text[0:self.edit_pos - 2]
                + self.text[self.edit_pos - 1]
                + self.text[self.edit_pos - 2]
                + self.text[self.edit_pos:])