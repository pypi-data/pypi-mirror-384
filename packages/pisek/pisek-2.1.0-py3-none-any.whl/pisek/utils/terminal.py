# pisek  - Tool for developing tasks for programming competitions.
#
# Copyright (c)   2019 - 2022 Václav Volhejn <vaclav.volhejn@gmail.com>
# Copyright (c)   2019 - 2022 Jiří Beneš <mail@jiribenes.com>
# Copyright (c)   2020 - 2022 Michal Töpfer <michal.topfer@gmail.com>
# Copyright (c)   2022        Jiří Kalvoda <jirikalvoda@kam.mff.cuni.cz>
# Copyright (c)   2023        Daniel Skýpala <daniel@honza.info>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
import os

from pisek.utils.text import pad

MSG_LEN = 25

try:
    terminal_width, terminal_height = os.get_terminal_size()
except OSError:
    terminal_width, terminal_height = 100, 24

TARGET_LINE_WIDTH = min(terminal_width, 100)
LINE_SEPARATOR = "—" * terminal_width + "\n"


def separator_text(text: str):
    dashes = TARGET_LINE_WIDTH - len(text) - 2
    return "-" * (dashes // 2) + " " + text + " " + "-" * ((dashes + 1) // 2)


def right_aligned_text(left: str, right: str, offset: int = 0):
    return pad(left, TARGET_LINE_WIDTH - len(right) + offset - 1) + " " + right
