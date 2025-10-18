# -*- encoding: utf-8 -*-

"""
CLI interface for pass.

:Copyright: © 2025, Aleksandr Block.
:License: MIT (see /LICENSE).
"""

import argparse
import os
import re
import subprocess
import sys
from functools import partial

import pyperclip
import urwid as ui

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pass_cli
from .enums import Mode, Part
from .ui_parts import CommandBox, FancyListBox, CustomButton, PasswordButton
from .utils import setup_logger, store_last_op

__all__ = ('main', 'App')

HEADER_BASE_TEXT = f"pass-cli v{pass_cli.__version__}"

logger = setup_logger(HEADER_BASE_TEXT, '%(asctime)s - %(name)s - %(levelname)s - %(message)s')


def exit_msg():
    return "Happy hacking!"


class AppState:
    last_op = None
    states = []


class App:
    palette = [
        ('header', 'white', 'dark red'),
        ('footer', 'white', 'dark blue'),
        ('footer_reversed', 'dark blue', 'white'),
        ('highlight', 'light blue', ''),
        ('error', 'light red', ''),
        ('button', 'default', ''),
        ('button_reversed', 'standout', ''),
    ]

    def __init__(self, config, search_query=None):
        self.__pass_dir = os.environ.get('PASSWORD_STORE', os.path.expanduser('~/.password-store'))
        self.current = ''
        self.mode = Mode.BASE
        self.header = ui.AttrWrap(ui.Text(HEADER_BASE_TEXT), Part.HEADER.value)
        listbox_content = ui.SimpleFocusListWalker([ui.Text('')])
        self.command_box = CommandBox(("highlight", ": "))
        self.box = FancyListBox(listbox_content)
        self.box._app = self
        self.last_query = search_query or 'gpg'

        self.keys = {'q': self._quit,
                     ':': partial(self._set_mode, Mode.COMMAND),
                     'b': self._revert_state,
                     'r': self._reload_state,
                     'esc': partial(self._set_mode, Mode.BASE),
                     'enter': self._process_command}

        self.frame = ui.Frame(self.box, header=self.header, footer=self.command_box)
        self.loop = ui.MainLoop(self.frame, self.palette, unhandled_input=self._unhandled)
        self._set_mode(mode=Mode.BASE, originator=self)
        self._perform_search(search_query)

    @store_last_op(AppState)
    def _perform_search(self, query):
        if not query:
            return
        pass_entries = []
        for root, dirs, files in os.walk(self.__pass_dir):
            if '.git' in dirs:
                dirs.remove('.git')
            for name in files:
                if query in name and name.endswith('.gpg'):
                    pass_entries.append(os.path.join(root, name))

        self._clear_box()
        self._make_password_buttons(pass_entries)
        AppState.states.append(partial(self._perform_search, query))

    def _make_password_buttons(self, passwords):
        """Add password buttons to the box."""
        for idx, p in enumerate(passwords):
            caption = p.replace(self.__pass_dir, "")
            caption = caption[:-len('.gpg')]
            self.box.body.append(PasswordButton(idx=idx,
                                                caption=caption,
                                                path=caption,
                                                actions=dict(edit=self.pass_edit, callback=self._pass_load)))

    def _make_items_buttons(self, entries, current_pass):
        """Add buttons of the password entries to the box."""
        for idx, k in enumerate(entries):
            value = entries[k]
            masked = value[-4:].rjust(len(value), ".")

            self.box.body.append(CustomButton(idx=idx,
                                              caption="{}: {}".format(k, masked),
                                              current_pass=current_pass,
                                              actions=dict(edit=self.pass_edit,
                                                           callback=partial(self._copy_to_buffer, value))))

    def _parse_entry(self, text):
        entries = {}
        for index, line in enumerate(text.split('\n')):
            entry = line.split(': ', 1)
            if len(entry) > 1:
                entries[entry[0]] = entry[1]
        return entries

    def _unhandled(self, key):
        """Handle unhandled input."""
        try:
            key = key.lower()
            if key in self.keys:
                self.keys[key]('unhandled')
            elif key == 'tab':
                if self.frame.focus_position == Part.BODY.value:
                    self.frame.focus_position = Part.FOOTER.value
                elif self.frame.focus_position == Part.FOOTER.value:
                    self.frame.focus_position = Part.FOOTER.value
        except AttributeError:
            # tuple == mouse event
            pass

    def _set_header(self, text):
        self.header.base_widget.set_text('{0} {1}'.format(HEADER_BASE_TEXT, text))

    def _clear_box(self):
        del self.box.body[:]
        self.loop.screen.clear()

    def _revert_state(self, originator):
        prev_state = AppState.states.pop() if len(AppState.states) > 1 else AppState.states[0]
        self._clear_box()
        prev_state()

    def _reload_state(self, originator):
        AppState.last_op()

    @staticmethod
    def _copy_to_buffer(value, originator, copytarget):
        pyperclip.copy(value)

    @store_last_op(AppState)
    def _pass_load(self, originator, path):
        self.current = path
        pargs = ['pass', path]
        p = subprocess.Popen(pargs, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()
        if p.returncode == 0:
            self._clear_box()
            self.loop.draw_screen()
            try:
                text = stdout.decode('utf-8')
            except AttributeError:
                text = stdout

            copiable_entries = self._parse_entry(text)
            self._make_items_buttons(copiable_entries, self.current)
        else:
            self._clear_box()
            self.box.body.append(ui.Text(('error', 'ERROR: %s' % stderr.strip())))
            self.loop.screen.clear()

    def pass_edit(self, originator, path):
        pargs = ['pass', 'edit', path]
        self.loop.stop()
        try:
            subprocess.call(pargs)
        finally:
            self.loop.start()
            self._reload_state(originator)

    def _process_command(self, originator):
        self._set_mode(mode=Mode.BASE, originator=originator)
        user_cmd = self.command_box.text[1:].strip()
        if user_cmd == 'q':
            self._quit(originator)
        m = re.match(r'^s\s+(?P<query>.+)', user_cmd)
        if m:
            query = m.group('query')
            self._perform_search(query)

        self.command_box.set_edit_text("")

    def _set_mode(self, mode, originator):
        self._set_header(mode.value.get('header', '[N]'))
        self.mode = mode

        self.frame.set_focus(mode.value.get('frame', 'body'))

    def help(self, originator):
        pass

    def _quit(self, originator):
        """Quit the program."""
        raise ui.ExitMainLoop()

    def run(self):
        self.loop.run()


def main():
    parser = argparse.ArgumentParser(description='CLI interface for `pass`')
    parser.add_argument('search_query',
                        metavar='SQ',
                        type=str,
                        nargs='?',
                        default=None,
                        help='a part of a search password entry')

    args = parser.parse_args()
    App(config=pass_cli.config, search_query=args.search_query).run()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        pass
    finally:
        print('\n', exit_msg())
