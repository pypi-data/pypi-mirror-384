import urwid as ui


class CustomButton(ui.Button):
    def __init__(self, caption, current_pass, actions, idx=0):
        super(CustomButton, self).__init__("")
        self.path = current_pass
        self.actions = actions
        self.idx = idx + 1
        self.caption = caption
        ui.connect_signal(self, 'click', actions['callback'], self.caption)
        self._w = ui.AttrMap(ui.SelectableIcon(
            [u' %s) ' % self.idx, self.caption], 0), 'button', 'button_reversed')


class PasswordButton(CustomButton):
    """A password button."""

    def __init__(self, caption, actions, path, idx=0):
        self.path = path
        self.actions = actions
        super(PasswordButton, self).__init__(caption, path, actions, idx=idx)
