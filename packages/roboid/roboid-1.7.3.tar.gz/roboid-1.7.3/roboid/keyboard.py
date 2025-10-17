# Part of the ROBOID project - http://hamster.school
# Copyright (C) 2016 Kwang-Hyun Park (akaii@kw.ac.kr)
# 
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General
# Public License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place, Suite 330,
# Boston, MA  02111-1307  USA

import os


if os.name == "nt":  # sys.platform == "win32":
    import msvcrt

    class Keyboard(object):
        BACKSPACE = 8
        TAB = 9
        ENTER = 13
        ESC = 27
        F1 = 59
        F2 = 60
        F3 = 61
        F4 = 62
        F5 = 63
        F6 = 64
        F7 = 65
        F8 = 66
        F9 = 67
        F10 = 68
        F11 = 133
        F12 = 134

        HOME = 71
        UP = 72
        PAGE_UP = 73
        LEFT = 75
        RIGHT = 77
        END = 79
        DOWN = 80
        PAGE_DOWN = 81
        INSERT = 82
        DELETE = 83
        
        _special_keys = (BACKSPACE, TAB, ENTER, ESC)
        _function_numpads = (F1, F2, F3, F4, F5, F6, F7, F8, F9, F10, HOME, UP, PAGE_UP, LEFT, RIGHT, END, DOWN, PAGE_DOWN, INSERT, DELETE)

        @staticmethod
        def read():
            if msvcrt.kbhit():
                key = msvcrt.getch()
                code = ord(key)
                if code == 224: # special key (F11, F12, HOME, UP, PAGE_UP, LEFT, RIGHT, END, DOWN, PAGE_DOWN, INSERT, DELETE)
                    return ord(msvcrt.getch())
                elif code == 0: # function key (F1 - F10) or num pad
                    code = ord(msvcrt.getch())
                    if code in Keyboard._function_numpads:
                        return code
                elif code in Keyboard._special_keys:
                    return code
                else:
                    return key.decode("utf-8")
else:
    import sys
    import termios
    from contextlib import contextmanager

    class Keyboard(object):
        BACKSPACE = 127
        TAB = 9
        ENTER = 10
        F1 = 80 # 27 79 80
        F2 = 81 # 27 79 81
        F3 = 82 # 27 79 82
        F4 = 83 # 27 79 83
        F5 = 53 # 27 91 49 53 126
        F6 = 55 # 27 91 49 55 126
        F7 = 56 # 27 91 49 56 126
        F8 = 57 # 27 91 49 57 126
        F9 = 48 # 27 91 50 48 126
        F10 = 49 # 27 91 50 49 126
        F11 = 51
        F12 = 52 # 27 91 50 52 126

        HOME = 72 # 27 91 72
        UP = 65 # 27 91 65
        PAGE_UP = 153 # 27 91 53 126
        LEFT = 68 # 27 91 68
        RIGHT = 67 # 27 91 67
        END = 70 # 27 91 70
        DOWN = 66 # 27 91 66
        PAGE_DOWN = 154 # 27 91 54 126
        INSERT = 150 # 27 91 50 126
        DELETE = 151 # 27 91 51 126
        
        _special_keys = (BACKSPACE, TAB, ENTER)

        @staticmethod
        @contextmanager
        def _mode(file):
            old_attrs = termios.tcgetattr(file.fileno())
            new_attrs = old_attrs[:]
            new_attrs[3] = new_attrs[3] & ~(termios.ECHO | termios.ICANON)
            try:
                termios.tcsetattr(file.fileno(), termios.TCSADRAIN, new_attrs)
                yield
            finally:
                termios.tcsetattr(file.fileno(), termios.TCSADRAIN, old_attrs)

        @staticmethod
        def read():
            with Keyboard._mode(sys.stdin):
                key = sys.stdin.read(1)
                code = ord(key)
                if code == 27: # special key
                    code = ord(sys.stdin.read(1))
                    if code == 79:
                        return ord(sys.stdin.read(1))
                    elif code == 91:
                        code = ord(sys.stdin.read(1))
                        if code >= 65:
                            return code
                        else:
                            code2 = ord(sys.stdin.read(1))
                            if code2 == 126:
                                return code + 100
                            else:
                                sys.stdin.read(1) # 126
                                return code2
                    else:
                        return code
                elif code in Keyboard._special_keys:
                    return code
                else:
                    return key
