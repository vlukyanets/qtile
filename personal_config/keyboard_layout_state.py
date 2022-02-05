# -*- coding: utf-8 -*-
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
            "grp:lalt_shift_toggle",
            "X11 keyboard options. Allowed to pass in two variants: 'grp:...' or 'Ctrl+Shift'"
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
        if not self.switch_hotkey.startswith("grp:"):
            x11_rules_file = "/usr/share/X11/xkb/rules/base.lst"

            with open(x11_rules_file, "r") as f:
                for line in f:
                    option, hotkey = line.strip().split(maxsplit=1)
                    if option.startswith("grp:") and hotkey == self.switch_hotkey:
                        return option

                raise ConfigError(self.__class__.__name__ + ": unknown hotkey " + self.switch_hotkey)
        else:
            return self.switch_hotkey

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

    @staticmethod
    def _clear_old_layouts_config():
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

    @staticmethod
    def next_layout():
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
