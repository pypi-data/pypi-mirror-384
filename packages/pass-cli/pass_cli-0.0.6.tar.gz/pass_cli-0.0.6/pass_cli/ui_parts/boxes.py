import urwid as ui


class FancyListBox(ui.ListBox):
    def keypress(self, size, key):
        """Handle keypresses."""
        if key == "e":
            self._app.pass_edit(originator=self, path=self._app.current)

        if self.body:
            currentfocus = self.focus_position
            maxindex = len(self.body) - 1
            newfocus = None
            if key == 'home':
                newfocus = 0
            elif key == 'end':
                newfocus = maxindex
            elif key == 'k':
                newfocus = currentfocus - 1
            elif key == 'j':
                newfocus = currentfocus + 1

            elif key.isdigit() and int(key) in range(1, 10):
                newfocus = int(key) - 1

            if newfocus is not None:
                if newfocus < 0:
                    newfocus = 0
                elif newfocus > maxindex:
                    newfocus = maxindex
                self.set_focus(newfocus)
        return super(FancyListBox, self).keypress(size, key)


class CommandBox(ui.Edit):
    def __init__(self, *args, **kwargs):
        self._user_cmd = None
        super(CommandBox, self).__init__(*args, **kwargs)

    def keypress(self, size, key):
        if key == 'esc':
            self.set_edit_text('')

        return super(CommandBox, self).keypress(size, key)
