# Copyright (C) 2022 Valentin Lukyanets
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import annotations

from typing import TYPE_CHECKING

import subprocess
import shutil

from libqtile.widget import base
from libqtile.log_utils import logger
from libqtile.confreader import ConfigError

if TYPE_CHECKING:
    from libqtile.core.manager import Qtile


# TODO: docs
# TODO: flag
class KeyboardLayoutStateX11(base.InLoopPollText):
    defaults = [
        (
            "update_interval",
            1,
            "Update time in seconds"
        ),
        (
            "configured_layouts",
            ["us"],
            "A list of predefined keyboard layouts represented as strings"
        ),
        (
            "display_map",
            {},
            "Custom display map of layout. Supports custom names or flag image file names"
        ),
        (
            "mode",
            "default",
            "Layout display mode. Supported values: 'default', 'flag'"
        ),
        (
            "flag_basedir",
            None,
            "Base directory for flag images. If specified, used as base folder for relative flag image files"
        ),
        (
            "switch_hotkey",
            "Left Alt+Left Shift",
            "Switch layout hotkey. See available options in code"
        ),
    ]

    def __init__(self, **config):
        base.InLoopPollText.__init__(self, **config)
        self.add_defaults(KeyboardLayoutStateX11.defaults)
        self.add_callbacks(
            {"Button1": self.next_layout},
            # {"Button3": self.show_popup_layouts},
        )

    def _generate_option(self):
        # TODO: Read values from X11 config files
        switch_hotkey_options = {
            'Left Alt (while pressed)': 'grp:lswitch',
            'Left Win (while pressed)': 'grp:lwin_switch',
            'Right Win (while pressed)': 'grp:rwin_switch',
            'Any Win key (while pressed)': 'grp:win_switch',
            'Caps Lock (while pressed), Alt+Caps Lock does the original capslock action': 'grp:caps_switch',
            'Right Ctrl (while pressed)': 'grp:rctrl_switch',
            'Right Alt': 'grp:toggle',
            'Left Alt': 'grp:lalt_toggle',
            'Caps Lock': 'grp:caps_toggle',
            'Shift+Caps Lock': 'grp:shift_caps_toggle',
            'Caps Lock (to first layout), Shift+Caps Lock (to last layout)': 'grp:shift_caps_switch',
            'Left Win (to first layout), Right Win/Menu (to last layout)': 'grp:win_menu_switch',
            'Left Ctrl (to first layout), Right Ctrl (to last layout)': 'grp:lctrl_rctrl_switch',
            'Alt+Caps Lock': 'grp:alt_caps_toggle',
            'Both Shift keys together': 'grp:shifts_toggle',
            'Both Alt keys together': 'grp:alts_toggle',
            'Both Ctrl keys together': 'grp:ctrls_toggle',
            'Ctrl+Shift': 'grp:ctrl_shift_toggle',
            'Left Ctrl+Left Shift': 'grp:lctrl_lshift_toggle',
            'Right Ctrl+Right Shift': 'grp:rctrl_rshift_toggle',
            'Alt+Ctrl': 'grp:ctrl_alt_toggle',
            'Alt+Shift': 'grp:alt_shift_toggle',
            'Left Alt+Left Shift': 'grp:lalt_lshift_toggle',
            'Alt+Space': 'grp:alt_space_toggle',
            'Menu': 'grp:menu_toggle',
            'Left Win': 'grp:lwin_toggle',
            'Win Key+Space': 'grp:win_space_toggle',
            'Right Win': 'grp:rwin_toggle',
            'Left Shift': 'grp:lshift_toggle',
            'Right Shift': 'grp:rshift_toggle',
            'Left Ctrl': 'grp:lctrl_toggle',
            'Right Ctrl': 'grp:rctrl_toggle',
            'Scroll Lock': 'grp:sclk_toggle',
            'LeftCtrl+LeftWin (to first layout), RightCtrl+Menu (to second layout)': 'grp:lctrl_lwin_rctrl_menu',
        }

        try:
            return switch_hotkey_options[self.switch_hotkey]
        except ValueError:
            raise ConfigError(self.__class__.__name__ + ": unknown hotkey " + self.switch_hotkey)

    def _configure(self, qtile: Qtile, bar):
        base.InLoopPollText._configure(self, qtile, bar)

        if qtile.core.name != "x11":
            raise ConfigError(self.__class__.__name__ + " does not support backend: " + qtile.core.name)

        required_programs = ["setxkbmap", "xkblayout-state"]
        for program in required_programs:
            path = shutil.which(program)
            if not path:
                raise ConfigError(self.__class__.__name__ + " requires " + program + " utility")

        self._option = self._generate_option()
        self._clear_old_layouts_config()
        self._configure_layouts()

    def _clear_old_layouts_config(self):
        # Workaround for '' argument
        command = ["setxkbmap", "-layout", '', "-variant", '', "-option", '']
        try:
            subprocess.check_output(command)
        except subprocess.CalledProcessError as e:
            logger.error("Can't clear old keyboard layout settings: {0}".format(e))
        except OSError as e:
            logger.error("Please, check that setxkbmap is available: {0}".format(e))

    def _configure_layouts(self):
        command = ["setxkbmap", "-layout", ",".join(self.configured_layouts)]
        if self._option:
            command.extend(["-option", self._option])
        try:
            subprocess.check_output(command)
        except subprocess.CalledProcessError as e:
            logger.error("Can't change the keyboard layout: {0}".format(e))
        except OSError as e:
            logger.error("Please, check that setxkbmap is available: {0}".format(e))

    def get_layout(self) -> str:
        command = ["xkblayout-state", "print", "%s"]
        try:
            xkblayout_state_output = subprocess.check_output(command).decode()
            layout = xkblayout_state_output.strip()
            if layout in self.configured_layouts:
                return layout
        except subprocess.CalledProcessError as e:
            logger.error("Can't get the keyboard layout: {0}".format(e))
        except OSError as e:
            logger.error("Please, check that xkblayout-state is available: {0}".format(e))

        return "unknown"

    def next_layout(self):
        command = ["xkblayout-state", "set", "+1"]
        try:
            subprocess.check_output(command)
        except subprocess.CalledProcessError as e:
            logger.error("Can't switch keyboard layout to next: {0}".format(e))
        except OSError as e:
            logger.error("Please, check that xkblayout-state is available: {0}".format(e))

    def poll(self):
        layout = self.get_layout()
        if layout in self.display_map.keys():
            return self.display_map[layout]
        return layout.upper()


__all__ = ["KeyboardLayoutStateX11"]
