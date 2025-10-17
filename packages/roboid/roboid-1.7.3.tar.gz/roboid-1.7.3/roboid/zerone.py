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

from roboid.runner import Runner
from roboid.util import Util
from roboid.model import Robot


class Zerone(Robot):
    ID = "kr.robomation.physical.zerone"

    LEFT_WHEEL = 0x00F00000
    RIGHT_WHEEL = 0x00F00001
    LEFT_HEAD_LED = 0x00F00002
    RIGHT_HEAD_LED = 0x00F00003
    LEFT_TAIL_LED = 0x00F00004
    RIGHT_TAIL_LED = 0x00F00005
    BUZZER = 0x00F00006
    PULSE = 0x00F00007
    NOTE = 0x00F00008
    SOUND = 0x00F00009
    LINE_TRACER_MODE = 0x00F0000a
    LINE_TRACER_SPEED = 0x00F0000b

    SIGNAL_STRENGTH = 0x00F0000d
    LEFT_PROXIMITY = 0x00F0000e
    RIGHT_PROXIMITY = 0x00F0000f
    FRONT_PROXIMITY = 0x00F00010
    REAR_PROXIMITY = 0x00F00011
    COLOR = 0x00F00012
    FLOOR = 0x00F00013
    BUTTON = 0x00F00014
    CLICKED = 0x00F00015
    DOUBLE_CLICKED = 0x00F00016
    LONG_PRESSED = 0x00F00017
    GESTURE = 0x00F00018
    COLOR_NUMBER = 0x00F00019
    COLOR_PATTERN = 0x00F0001a
    PULSE_COUNT = 0x00F0001b
    WHEEL_STATE = 0x00F0001c
    SOUND_STATE = 0x00F0001d
    LINE_TRACER_STATE = 0x00F0001e
    BATTERY_STATE = 0x00F0001f

    COLOR_NONE = -1
    COLOR_UNKNOWN = -2
    COLOR_BLACK = 0
    COLOR_RED = 1
    COLOR_ORANGE = 7
    COLOR_YELLOW = 2
    COLOR_GREEN = 3
    COLOR_CYAN = 4
    COLOR_SKY_BLUE = 4
    COLOR_BLUE = 5
    COLOR_MAGENTA = 6
    COLOR_PURPLE = 6
    COLOR_WHITE = 8

    COLOR_NAME_OFF = "off"
    COLOR_NAME_BLACK = "black"
    COLOR_NAME_RED = "red"
    COLOR_NAME_ORANGE = "orange"
    COLOR_NAME_YELLOW = "yellow"
    COLOR_NAME_GREEN = "green"
    COLOR_NAME_SKY_BLUE = "sky blue"
    COLOR_NAME_BLUE = "blue"
    COLOR_NAME_VIOLET = "violet"
    COLOR_NAME_PURPLE = "purple"
    COLOR_NAME_WHITE = "white"

    LINE_TRACER_MODE_OFF = 0
    LINE_TRACER_MODE_FOLLOW = 1
    LINE_TRACER_MODE_MOVE_FORWARD = 3
    LINE_TRACER_MODE_TURN_LEFT = 4
    LINE_TRACER_MODE_TURN_RIGHT = 5
    LINE_TRACER_MODE_UTURN = 6
    LINE_TRACER_MODE_JUMP_LEFT = 7
    LINE_TRACER_MODE_JUMP_RIGHT = 8
    LINE_TRACER_MODE_UNTIL_CROSS = 9
    LINE_TRACER_MODE_UNTIL_RED = 10
    LINE_TRACER_MODE_UNTIL_YELLOW = 11
    LINE_TRACER_MODE_UNTIL_GREEN = 12
    LINE_TRACER_MODE_UNTIL_CYAN = 13
    LINE_TRACER_MODE_UNTIL_SKY_BLUE = 13
    LINE_TRACER_MODE_UNTIL_BLUE = 14
    LINE_TRACER_MODE_UNTIL_MAGENTA = 15
    LINE_TRACER_MODE_UNTIL_PURPLE = 15
    LINE_TRACER_MODE_UNTIL_ANY = 2

    NOTE_OFF = 0
    NOTE_A_0 = 1
    NOTE_A_SHARP_0 = 2
    NOTE_B_FLAT_0 = 2
    NOTE_B_0 = 3
    NOTE_C_1 = 4
    NOTE_C_SHARP_1 = 5
    NOTE_D_FLAT_1 = 5
    NOTE_D_1 = 6
    NOTE_D_SHARP_1 = 7
    NOTE_E_FLAT_1 = 7
    NOTE_E_1 = 8
    NOTE_F_1 = 9
    NOTE_F_SHARP_1 = 10
    NOTE_G_FLAT_1 = 10
    NOTE_G_1 = 11
    NOTE_G_SHARP_1 = 12
    NOTE_A_FLAT_1 = 12
    NOTE_A_1 = 13
    NOTE_A_SHARP_1 = 14
    NOTE_B_FLAT_1 = 14
    NOTE_B_1 = 15
    NOTE_C_2 = 16
    NOTE_C_SHARP_2 = 17
    NOTE_D_FLAT_2 = 17
    NOTE_D_2 = 18
    NOTE_D_SHARP_2 = 19
    NOTE_E_FLAT_2 = 19
    NOTE_E_2 = 20
    NOTE_F_2 = 21
    NOTE_F_SHARP_2 = 22
    NOTE_G_FLAT_2 = 22
    NOTE_G_2 = 23
    NOTE_G_SHARP_2 = 24
    NOTE_A_FLAT_2 = 24
    NOTE_A_2 = 25
    NOTE_A_SHARP_2 = 26
    NOTE_B_FLAT_2 = 26
    NOTE_B_2 = 27
    NOTE_C_3 = 28
    NOTE_C_SHARP_3 = 29
    NOTE_D_FLAT_3 = 29
    NOTE_D_3 = 30
    NOTE_D_SHARP_3 = 31
    NOTE_E_FLAT_3 = 31
    NOTE_E_3 = 32
    NOTE_F_3 = 33
    NOTE_F_SHARP_3 = 34
    NOTE_G_FLAT_3 = 34
    NOTE_G_3 = 35
    NOTE_G_SHARP_3 = 36
    NOTE_A_FLAT_3 = 36
    NOTE_A_3 = 37
    NOTE_A_SHARP_3 = 38
    NOTE_B_FLAT_3 = 38
    NOTE_B_3 = 39
    NOTE_C_4 = 40
    NOTE_C_SHARP_4 = 41
    NOTE_D_FLAT_4 = 41
    NOTE_D_4 = 42
    NOTE_D_SHARP_4 = 43
    NOTE_E_FLAT_4 = 43
    NOTE_E_4 = 44
    NOTE_F_4 = 45
    NOTE_F_SHARP_4 = 46
    NOTE_G_FLAT_4 = 46
    NOTE_G_4 = 47
    NOTE_G_SHARP_4 = 48
    NOTE_A_FLAT_4 = 48
    NOTE_A_4 = 49
    NOTE_A_SHARP_4 = 50
    NOTE_B_FLAT_4 = 50
    NOTE_B_4 = 51
    NOTE_C_5 = 52
    NOTE_C_SHARP_5 = 53
    NOTE_D_FLAT_5 = 53
    NOTE_D_5 = 54
    NOTE_D_SHARP_5 = 55
    NOTE_E_FLAT_5 = 55
    NOTE_E_5 = 56
    NOTE_F_5 = 57
    NOTE_F_SHARP_5 = 58
    NOTE_G_FLAT_5 = 58
    NOTE_G_5 = 59
    NOTE_G_SHARP_5 = 60
    NOTE_A_FLAT_5 = 60
    NOTE_A_5 = 61
    NOTE_A_SHARP_5 = 62
    NOTE_B_FLAT_5 = 62
    NOTE_B_5 = 63
    NOTE_C_6 = 64
    NOTE_C_SHARP_6 = 65
    NOTE_D_FLAT_6 = 65
    NOTE_D_6 = 66
    NOTE_D_SHARP_6 = 67
    NOTE_E_FLAT_6 = 67
    NOTE_E_6 = 68
    NOTE_F_6 = 69
    NOTE_F_SHARP_6 = 70
    NOTE_G_FLAT_6 = 70
    NOTE_G_6 = 71
    NOTE_G_SHARP_6 = 72
    NOTE_A_FLAT_6 = 72
    NOTE_A_6 = 73
    NOTE_A_SHARP_6 = 74
    NOTE_B_FLAT_6 = 74
    NOTE_B_6 = 75
    NOTE_C_7 = 76
    NOTE_C_SHARP_7 = 77
    NOTE_D_FLAT_7 = 77
    NOTE_D_7 = 78
    NOTE_D_SHARP_7 = 79
    NOTE_E_FLAT_7 = 79
    NOTE_E_7 = 80
    NOTE_F_7 = 81
    NOTE_F_SHARP_7 = 82
    NOTE_G_FLAT_7 = 82
    NOTE_G_7 = 83
    NOTE_G_SHARP_7 = 84
    NOTE_A_FLAT_7 = 84
    NOTE_A_7 = 85
    NOTE_A_SHARP_7 = 86
    NOTE_B_FLAT_7 = 86
    NOTE_B_7 = 87
    NOTE_C_8 = 88

    NOTE_NAME_C = "C"
    NOTE_NAME_C_SHARP = "C#"
    NOTE_NAME_D_FLAT = "Db"
    NOTE_NAME_D = "D"
    NOTE_NAME_D_SHARP = "D#"
    NOTE_NAME_E_FLAT = "Eb"
    NOTE_NAME_E = "E"
    NOTE_NAME_F = "F"
    NOTE_NAME_F_SHARP = "F#"
    NOTE_NAME_G_FLAT = "Gb"
    NOTE_NAME_G = "G"
    NOTE_NAME_G_SHARP = "G#"
    NOTE_NAME_A_FLAT = "Ab"
    NOTE_NAME_A = "A"
    NOTE_NAME_A_SHARP = "A#"
    NOTE_NAME_B_FLAT = "Bb"
    NOTE_NAME_B = "B"

    SOUND_OFF = 0
    SOUND_BEEP = 1
    SOUND_RANDOM_BEEP = 2
    SOUND_NOISE = 10
    SOUND_SIREN = 3
    SOUND_ENGINE = 4
    SOUND_CHOP = 11
    SOUND_ROBOT = 5
    SOUND_DIBIDIBIDIP = 8
    SOUND_GOOD_JOB = 9
    SOUND_HAPPY = 12
    SOUND_ANGRY = 13
    SOUND_SAD = 14
    SOUND_SLEEP = 15
    SOUND_MARCH = 6
    SOUND_BIRTHDAY = 7

    SOUND_NAME_OFF = "off"
    SOUND_NAME_BEEP = "beep"
    SOUND_NAME_RANDOM_BEEP = "random beep"
    SOUND_NAME_NOISE = "noise"
    SOUND_NAME_SIREN = "siren"
    SOUND_NAME_ENGINE = "engine"
    SOUND_NAME_CHOP = "chop"
    SOUND_NAME_ROBOT = "robot"
    SOUND_NAME_DIBIDIBIDIP = "dibidibidip"
    SOUND_NAME_GOOD_JOB = "good job"
    SOUND_NAME_HAPPY = "happy"
    SOUND_NAME_ANGRY = "angry"
    SOUND_NAME_SAD = "sad"
    SOUND_NAME_SLEEP = "sleep"
    SOUND_NAME_MARCH = "march"
    SOUND_NAME_BIRTHDAY = "birthday"

    GESTURE_NONE = -1
    GESTURE_FORWARD = 0
    GESTURE_BACKWARD = 1
    GESTURE_LEFTWARD = 2
    GESTURE_RIGHTWARD = 3
    GESTURE_NEAR = 4
    GESTURE_FAR = 5
    GESTURE_LONG_TOUCH = 6

    GESTURE_NAME_FORWARD = "forward"
    GESTURE_NAME_BACKWARD = "backward"
    GESTURE_NAME_LEFTWARD = "leftward"
    GESTURE_NAME_RIGHTWARD = "rightward"
    GESTURE_NAME_NEAR = "near"
    GESTURE_NAME_FAR = "far"
    GESTURE_NAME_LONG_TOUCH = "long touch"

    BATTERY_NORMAL = 2
    BATTERY_LOW = 1
    BATTERY_EMPTY = 0

    _LEDS = {
        "left head": 0x8,
        "left_head": 0x8,
        "right head": 0x4,
        "right_head": 0x4,
        "left tail": 0x2,
        "left_tail": 0x2,
        "right tail": 0x1,
        "right_tail": 0x1,
        "left": 0xa,
        "right": 0x5,
        "head": 0xc,
        "tail": 0x3,
        "all": 0xf
    }
    _COLOR2RGB = {
        "off": (0, 0, 0),
        "red": (255, 0, 0),
        "orange": (255, 63, 0),
        "yellow": (255, 255, 0),
        "green": (0, 255, 0),
        "sky_blue": (0, 255, 255),
        "skyblue": (0, 255, 255),
        "sky blue": (0, 255, 255),
        "cyan": (0, 255, 255),
        "blue": (0, 0, 255),
        "violet": (63, 0, 255),
        "purple": (255, 0, 255),
        "magenta": (255, 0, 255),
        "white": (255, 255, 255)
    }
    _COLORS = {
        "none": -1,
        "unknown": -2,
        "black": 0,
        "red": 1,
        "orange": 7,
        "yellow": 2,
        "green": 3,
        "sky_blue": 4,
        "skyblue": 4,
        "sky blue": 4,
        "cyan": 4,
        "blue": 5,
        "purple": 6,
        "magenta": 6,
        "white": 8
    }
    _NOTES = {
        "c": NOTE_C_1,
        "c#": NOTE_C_SHARP_1,
        "db": NOTE_D_FLAT_1,
        "d": NOTE_D_1,
        "d#": NOTE_D_SHARP_1,
        "eb": NOTE_E_FLAT_1,
        "e": NOTE_E_1,
        "f": NOTE_F_1,
        "f#": NOTE_F_SHARP_1,
        "gb": NOTE_G_FLAT_1,
        "g": NOTE_G_1,
        "g#": NOTE_G_SHARP_1,
        "ab": NOTE_A_FLAT_1,
        "a": NOTE_A_1,
        "a#": NOTE_A_SHARP_1,
        "bb": NOTE_B_FLAT_1,
        "b": NOTE_B_1
    }
    _SOUNDS = {
        "off": 0,
        "beep": 1,
        "random beep": 2,
        "random_beep": 2,
        "siren": 3,
        "engine": 4,
        "robot": 5,
        "march": 6,
        "birthday": 7,
        "dibidibidip": 8,
        "good job": 9,
        "good_job": 9,
        "noise": 10,
        "chop": 11,
        "happy": 12,
        "angry": 13,
        "sad": 14,
        "sleep": 15
    }
    _GESTURES = {
        "forward": 0,
        "backward": 1,
        "leftward": 2,
        "left": 2,
        "rightward": 3,
        "right": 3,
        "near": 4,
        "far": 5,
        "long touch": 6,
        "long_touch": 6
    }
    CM_TO_PULSE = 642.0 / 7
    DEG_TO_PULSE = 1122.0 / 360
    _robots = {}

    def __init__(self, index=0, port_name=None):
        if isinstance(index, str):
            index = 0
            port_name = index
        if index in Zerone._robots:
            robot = Zerone._robots[index]
            if robot: robot.dispose()
        Zerone._robots[index] = self
        super(Zerone, self).__init__(Zerone.ID, "Zerone", index)
        self._bpm = 60
        self._init(port_name)

    def dispose(self):
        Zerone._robots[self.get_index()] = None
        self._roboid._dispose()
        Runner.unregister_robot(self)

    def reset(self):
        self._bpm = 60
        self._roboid._reset()

    def _init(self, port_name):
        from roboid.zerone_roboid import ZeroneRoboid
        self._roboid = ZeroneRoboid(self.get_index())
        self._add_roboid(self._roboid)
        Runner.register_robot(self)
        Runner.start()
        self._roboid._init(port_name)

    def find_device_by_id(self, device_id):
        return self._roboid.find_device_by_id(device_id)

    def _request_motoring_data(self):
        self._roboid._request_motoring_data()

    def _update_sensory_device_state(self):
        self._roboid._update_sensory_device_state()

    def _update_motoring_device_state(self):
        self._roboid._update_motoring_device_state()

    def _notify_sensory_device_data_changed(self):
        self._roboid._notify_sensory_device_data_changed()

    def _notify_motoring_device_data_changed(self):
        self._roboid._notify_motoring_device_data_changed()

    def cm_to_pulse(self, cm):
        if isinstance(cm, (int, float)):
            return Util.round(cm * Zerone.CM_TO_PULSE)
        else:
            return 0

    def calc_turn_pulse(self, degree):
        if isinstance(degree, (int, float)):
            return Util.round(degree * Zerone.DEG_TO_PULSE)
        else:
            return 0

    def calc_pivot_pulse(self, degree):
        if isinstance(degree, (int, float)):
            return Util.round(degree * Zerone.DEG_TO_PULSE * 2)
        else:
            return 0

    def wheels(self, left_velocity, right_velocity=None):
        self.write(Zerone.PULSE, 0)
        self.write(Zerone.LINE_TRACER_MODE, Zerone.LINE_TRACER_MODE_OFF)
        if isinstance(left_velocity, (int, float)):
            self.write(Zerone.LEFT_WHEEL, left_velocity)
        if isinstance(right_velocity, (int, float)):
            self.write(Zerone.RIGHT_WHEEL, right_velocity)
        else:
            if isinstance(left_velocity, (int, float)):
                self.write(Zerone.RIGHT_WHEEL, left_velocity)

    def left_wheel(self, velocity):
        self.write(Zerone.PULSE, 0)
        self.write(Zerone.LINE_TRACER_MODE, Zerone.LINE_TRACER_MODE_OFF)
        if isinstance(velocity, (int, float)):
            self.write(Zerone.LEFT_WHEEL, velocity)

    def right_wheel(self, velocity):
        self.write(Zerone.PULSE, 0)
        self.write(Zerone.LINE_TRACER_MODE, Zerone.LINE_TRACER_MODE_OFF)
        if isinstance(velocity, (int, float)):
            self.write(Zerone.RIGHT_WHEEL, velocity)

    def stop(self):
        self.write(Zerone.PULSE, 0)
        self.write(Zerone.LINE_TRACER_MODE, Zerone.LINE_TRACER_MODE_OFF)
        self.write(Zerone.LEFT_WHEEL, 0)
        self.write(Zerone.RIGHT_WHEEL, 0)

    def _evaluate_wheel_state(self):
        return self.e(Zerone.WHEEL_STATE)

    def _motion(self, pulse, left_velocity, right_velocity):
        self.write(Zerone.LINE_TRACER_MODE, Zerone.LINE_TRACER_MODE_OFF)
        if pulse > 0:
            self.write(Zerone.LEFT_WHEEL, left_velocity)
            self.write(Zerone.RIGHT_WHEEL, right_velocity)
            self.write(Zerone.PULSE, pulse)
            Runner.wait_until(self._evaluate_wheel_state)
            self.write(Zerone.LEFT_WHEEL, 0)
            self.write(Zerone.RIGHT_WHEEL, 0)
        else:
            self.write(Zerone.LEFT_WHEEL, 0)
            self.write(Zerone.RIGHT_WHEEL, 0)
            self.write(Zerone.PULSE, 0)

    def move_forward(self, cm=6, velocity=50):
        if isinstance(cm, (int, float)) and isinstance(velocity, (int, float)):
            if cm < 0:
                cm = -cm
                velocity = -velocity
            self._motion(self.cm_to_pulse(cm), velocity, velocity)

    def move_backward(self, cm=6, velocity=50):
        if isinstance(cm, (int, float)) and isinstance(velocity, (int, float)):
            if cm < 0:
                cm = -cm
                velocity = -velocity
            self._motion(self.cm_to_pulse(cm), -velocity, -velocity)

    def turn_left(self, degree=90, velocity=50):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(self.calc_turn_pulse(degree), -velocity, velocity)

    def turn_right(self, degree=90, velocity=50):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(self.calc_turn_pulse(degree), velocity, -velocity)

    def pivot_left(self, degree, velocity=50):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(self.calc_pivot_pulse(degree), 0, velocity)

    def pivot_right(self, degree, velocity=50):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(self.calc_pivot_pulse(degree), velocity, 0)

    def _motion_sec(self, sec, left_velocity, right_velocity):
        self.write(Zerone.PULSE, 0)
        self.write(Zerone.LINE_TRACER_MODE, Zerone.LINE_TRACER_MODE_OFF)
        if sec < 0:
            sec = -sec
            left_velocity = -left_velocity
            right_velocity = -right_velocity
        if sec > 0:
            self.write(Zerone.LEFT_WHEEL, left_velocity)
            self.write(Zerone.RIGHT_WHEEL, right_velocity)
            Runner.wait(sec * 1000)
        self.write(Zerone.LEFT_WHEEL, 0)
        self.write(Zerone.RIGHT_WHEEL, 0)

    def move_forward_sec(self, sec, velocity=50):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, velocity, velocity)

    def move_backward_sec(self, sec, velocity=50):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, -velocity, -velocity)

    def turn_left_sec(self, sec, velocity=50):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, -velocity, velocity)

    def turn_right_sec(self, sec, velocity=50):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, velocity, -velocity)

    def pivot_left_sec(self, sec, velocity=50):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, 0, velocity)

    def pivot_right_sec(self, sec, velocity=50):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, velocity, 0)

    def move_forward_pulse(self, pulse, velocity=50):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), velocity, velocity)

    def move_backward_pulse(self, pulse, velocity=50):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), -velocity, -velocity)

    def turn_left_pulse(self, pulse, velocity=50):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), -velocity, velocity)

    def turn_right_pulse(self, pulse, velocity=50):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), velocity, -velocity)

    def pivot_left_pulse(self, pulse, velocity=50):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), 0, velocity)

    def pivot_right_pulse(self, pulse, velocity=50):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), velocity, 0)

    def _evaluate_line_tracer(self):
        return self.e(Zerone.LINE_TRACER_STATE)

    def line_tracer_mode(self, mode):
        self.write(Zerone.LEFT_WHEEL, 0)
        self.write(Zerone.RIGHT_WHEEL, 0)
        self.write(Zerone.PULSE, 0)
        if isinstance(mode, (int, float)):
            mode = int(mode)
            self.write(Zerone.LINE_TRACER_MODE, mode)
            if mode >= 2 and mode <= 15:
                Runner.wait_until(self._evaluate_line_tracer)
                self.write(Zerone.LINE_TRACER_MODE, Zerone.LINE_TRACER_MODE_OFF)

    def follow_line(self):
        self.line_tracer_mode(Zerone.LINE_TRACER_MODE_FOLLOW)

    def line_until_cross(self):
        self.line_tracer_mode(Zerone.LINE_TRACER_MODE_UNTIL_CROSS)

    def line_until_red(self):
        self.line_tracer_mode(Zerone.LINE_TRACER_MODE_UNTIL_RED)

    def line_until_yellow(self):
        self.line_tracer_mode(Zerone.LINE_TRACER_MODE_UNTIL_YELLOW)

    def line_until_green(self):
        self.line_tracer_mode(Zerone.LINE_TRACER_MODE_UNTIL_GREEN)

    def line_until_sky_blue(self):
        self.line_tracer_mode(Zerone.LINE_TRACER_MODE_UNTIL_SKY_BLUE)

    def line_until_blue(self):
        self.line_tracer_mode(Zerone.LINE_TRACER_MODE_UNTIL_BLUE)

    def line_until_purple(self):
        self.line_tracer_mode(Zerone.LINE_TRACER_MODE_UNTIL_PURPLE)

    def line_until_any(self):
        self.line_tracer_mode(Zerone.LINE_TRACER_MODE_UNTIL_ANY)

    def cross_forward(self):
        self.line_tracer_mode(Zerone.LINE_TRACER_MODE_MOVE_FORWARD)

    def cross_left(self):
        self.line_tracer_mode(Zerone.LINE_TRACER_MODE_TURN_LEFT)

    def cross_right(self):
        self.line_tracer_mode(Zerone.LINE_TRACER_MODE_TURN_RIGHT)

    def cross_uturn(self):
        self.line_tracer_mode(Zerone.LINE_TRACER_MODE_UTURN)

    def jump_left(self):
        self.line_tracer_mode(Zerone.LINE_TRACER_MODE_JUMP_LEFT)

    def jump_right(self):
        self.line_tracer_mode(Zerone.LINE_TRACER_MODE_JUMP_RIGHT)

    def line_speed(self, speed):
        if isinstance(speed, (int, float)):
            self.write(Zerone.LINE_TRACER_SPEED, Util.round(speed))

    def rgbs(self, led, red, green=None, blue=None):
        if isinstance(led, str):
            tmp = led.lower()
            if tmp in Zerone._LEDS:
                led = Zerone._LEDS[tmp]
                if isinstance(red, (int, float)):
                    red = Util.round(red)
                    if isinstance(green, (int, float)) and isinstance(blue, (int, float)):
                        green = Util.round(green)
                        blue = Util.round(blue)
                        if led & 0x8:
                            self.write(Zerone.LEFT_HEAD_LED, 0, red)
                            self.write(Zerone.LEFT_HEAD_LED, 1, green)
                            self.write(Zerone.LEFT_HEAD_LED, 2, blue)
                        if led & 0x4:
                            self.write(Zerone.RIGHT_HEAD_LED, 0, red)
                            self.write(Zerone.RIGHT_HEAD_LED, 1, green)
                            self.write(Zerone.RIGHT_HEAD_LED, 2, blue)
                        if led & 0x2:
                            self.write(Zerone.LEFT_TAIL_LED, 0, red)
                            self.write(Zerone.LEFT_TAIL_LED, 1, green)
                            self.write(Zerone.LEFT_TAIL_LED, 2, blue)
                        if led & 0x1:
                            self.write(Zerone.RIGHT_TAIL_LED, 0, red)
                            self.write(Zerone.RIGHT_TAIL_LED, 1, green)
                            self.write(Zerone.RIGHT_TAIL_LED, 2, blue)
                    else:
                        if led & 0x8:
                            self.write(Zerone.LEFT_HEAD_LED, 0, red)
                            self.write(Zerone.LEFT_HEAD_LED, 1, red)
                            self.write(Zerone.LEFT_HEAD_LED, 2, red)
                        if led & 0x4:
                            self.write(Zerone.RIGHT_HEAD_LED, 0, red)
                            self.write(Zerone.RIGHT_HEAD_LED, 1, red)
                            self.write(Zerone.RIGHT_HEAD_LED, 2, red)
                        if led & 0x2:
                            self.write(Zerone.LEFT_TAIL_LED, 0, red)
                            self.write(Zerone.LEFT_TAIL_LED, 1, red)
                            self.write(Zerone.LEFT_TAIL_LED, 2, red)
                        if led & 0x1:
                            self.write(Zerone.RIGHT_TAIL_LED, 0, red)
                            self.write(Zerone.RIGHT_TAIL_LED, 1, red)
                            self.write(Zerone.RIGHT_TAIL_LED, 2, red)
                elif isinstance(red, (list, tuple)):
                    if len(red) >= 3 and isinstance(red[0], (int, float)) and isinstance(red[1], (int, float)) and isinstance(red[2], (int, float)):
                        r = Util.round(red[0])
                        g = Util.round(red[1])
                        b = Util.round(red[2])
                        if led & 0x8:
                            self.write(Zerone.LEFT_HEAD_LED, 0, r)
                            self.write(Zerone.LEFT_HEAD_LED, 1, g)
                            self.write(Zerone.LEFT_HEAD_LED, 2, b)
                        if led & 0x4:
                            self.write(Zerone.RIGHT_HEAD_LED, 0, r)
                            self.write(Zerone.RIGHT_HEAD_LED, 1, g)
                            self.write(Zerone.RIGHT_HEAD_LED, 2, b)
                        if led & 0x2:
                            self.write(Zerone.LEFT_TAIL_LED, 0, r)
                            self.write(Zerone.LEFT_TAIL_LED, 1, g)
                            self.write(Zerone.LEFT_TAIL_LED, 2, b)
                        if led & 0x1:
                            self.write(Zerone.RIGHT_TAIL_LED, 0, r)
                            self.write(Zerone.RIGHT_TAIL_LED, 1, g)
                            self.write(Zerone.RIGHT_TAIL_LED, 2, b)

    def leds(self, led, color1, color2=None, color3=None):
        if isinstance(led, str):
            tmp = led.lower()
            if tmp in Zerone._LEDS:
                led = Zerone._LEDS[tmp]
                if isinstance(color1, (int, float)):
                    color1 = Util.round(color1)
                    if isinstance(color2, (int, float)) and isinstance(color3, (int, float)):
                        color2 = Util.round(color2)
                        color3 = Util.round(color3)
                        if led & 0x8:
                            self.write(Zerone.LEFT_HEAD_LED, 0, color1)
                            self.write(Zerone.LEFT_HEAD_LED, 1, color2)
                            self.write(Zerone.LEFT_HEAD_LED, 2, color3)
                        if led & 0x4:
                            self.write(Zerone.RIGHT_HEAD_LED, 0, color1)
                            self.write(Zerone.RIGHT_HEAD_LED, 1, color2)
                            self.write(Zerone.RIGHT_HEAD_LED, 2, color3)
                        if led & 0x2:
                            self.write(Zerone.LEFT_TAIL_LED, 0, color1)
                            self.write(Zerone.LEFT_TAIL_LED, 1, color2)
                            self.write(Zerone.LEFT_TAIL_LED, 2, color3)
                        if led & 0x1:
                            self.write(Zerone.RIGHT_TAIL_LED, 0, color1)
                            self.write(Zerone.RIGHT_TAIL_LED, 1, color2)
                            self.write(Zerone.RIGHT_TAIL_LED, 2, color3)
                    else:
                        if led & 0x8:
                            self.write(Zerone.LEFT_HEAD_LED, 0, color1)
                            self.write(Zerone.LEFT_HEAD_LED, 1, color1)
                            self.write(Zerone.LEFT_HEAD_LED, 2, color1)
                        if led & 0x4:
                            self.write(Zerone.RIGHT_HEAD_LED, 0, color1)
                            self.write(Zerone.RIGHT_HEAD_LED, 1, color1)
                            self.write(Zerone.RIGHT_HEAD_LED, 2, color1)
                        if led & 0x2:
                            self.write(Zerone.LEFT_TAIL_LED, 0, color1)
                            self.write(Zerone.LEFT_TAIL_LED, 1, color1)
                            self.write(Zerone.LEFT_TAIL_LED, 2, color1)
                        if led & 0x1:
                            self.write(Zerone.RIGHT_TAIL_LED, 0, color1)
                            self.write(Zerone.RIGHT_TAIL_LED, 1, color1)
                            self.write(Zerone.RIGHT_TAIL_LED, 2, color1)
                elif isinstance(color1, str):
                    tmp = color1.lower()
                    if tmp in Zerone._COLOR2RGB:
                        color1 = Zerone._COLOR2RGB[tmp]
                        if led & 0x8:
                            self.write(Zerone.LEFT_HEAD_LED, color1)
                        if led & 0x4:
                            self.write(Zerone.RIGHT_HEAD_LED, color1)
                        if led & 0x2:
                            self.write(Zerone.LEFT_TAIL_LED, color1)
                        if led & 0x1:
                            self.write(Zerone.RIGHT_TAIL_LED, color1)
                elif isinstance(color1, (list, tuple)):
                    if len(color1) >= 3 and isinstance(color1[0], (int, float)) and isinstance(color1[1], (int, float)) and isinstance(color1[2], (int, float)):
                        r = Util.round(color1[0])
                        g = Util.round(color1[1])
                        b = Util.round(color1[2])
                        if led & 0x8:
                            self.write(Zerone.LEFT_HEAD_LED, 0, r)
                            self.write(Zerone.LEFT_HEAD_LED, 1, g)
                            self.write(Zerone.LEFT_HEAD_LED, 2, b)
                        if led & 0x4:
                            self.write(Zerone.RIGHT_HEAD_LED, 0, r)
                            self.write(Zerone.RIGHT_HEAD_LED, 1, g)
                            self.write(Zerone.RIGHT_HEAD_LED, 2, b)
                        if led & 0x2:
                            self.write(Zerone.LEFT_TAIL_LED, 0, r)
                            self.write(Zerone.LEFT_TAIL_LED, 1, g)
                            self.write(Zerone.LEFT_TAIL_LED, 2, b)
                        if led & 0x1:
                            self.write(Zerone.RIGHT_TAIL_LED, 0, r)
                            self.write(Zerone.RIGHT_TAIL_LED, 1, g)
                            self.write(Zerone.RIGHT_TAIL_LED, 2, b)

    def buzzer(self, hz):
        self.write(Zerone.NOTE, Zerone.NOTE_OFF)
        self._roboid._cancel_sound()
        if isinstance(hz, (int, float)):
            self.write(Zerone.BUZZER, hz)

    def tempo(self, bpm):
        if isinstance(bpm, (int, float)):
            if bpm > 0:
                self._bpm = bpm

    def note(self, pitch, beats=None):
        self.write(Zerone.BUZZER, 0)
        self._roboid._cancel_sound()
        if isinstance(pitch, str) and len(pitch) > 0:
            tmp = pitch.lower()
            if tmp == "off":
                pitch = 0
            else:
                octave = 4
                try:
                    octave = int(tmp[-1])
                    tmp = tmp[:-1]
                except ValueError:
                    pass
                if tmp in Zerone._NOTES:
                    pitch = Zerone._NOTES[tmp] + (octave - 1) * 12
        if isinstance(pitch, (int, float)):
            pitch = int(pitch)
            if isinstance(beats, (int, float)):
                bpm = self._bpm
                if beats > 0 and bpm > 0:
                    if pitch == 0:
                        self.write(Zerone.NOTE, Zerone.NOTE_OFF)
                        Runner.wait(beats * 60 * 1000.0 / bpm)
                    elif pitch > 0:
                        timeout = beats * 60 * 1000.0 / bpm
                        tail = 0
                        if timeout > 100:
                            tail = 100
                        self.write(Zerone.NOTE, pitch)
                        Runner.wait(timeout - tail)
                        self.write(Zerone.NOTE, Zerone.NOTE_OFF)
                        if tail > 0:
                            Runner.wait(tail)
                else:
                    self.write(Zerone.NOTE, Zerone.NOTE_OFF)
            elif pitch >= 0:
                self.write(Zerone.NOTE, pitch)

    def _evaluate_sound(self):
        return self.e(Zerone.SOUND_STATE)

    def sound(self, sound, repeat=1):
        self.write(Zerone.BUZZER, 0)
        self.write(Zerone.NOTE, Zerone.NOTE_OFF)
        if isinstance(sound, str):
            tmp = sound.lower()
            if tmp in Zerone._SOUNDS:
                sound = Zerone._SOUNDS[tmp]
        if isinstance(sound, (int, float)) and isinstance(repeat, (int, float)):
            sound = int(sound)
            repeat = int(repeat)
            if sound > 0 and repeat != 0:
                self._roboid._run_sound(sound, repeat)
            else:
                self._roboid._cancel_sound()

    def sound_until_done(self, sound, repeat=1):
        self.write(Zerone.BUZZER, 0)
        self.write(Zerone.NOTE, Zerone.NOTE_OFF)
        if isinstance(sound, str):
            tmp = sound.lower()
            if tmp in Zerone._SOUNDS:
                sound = Zerone._SOUNDS[tmp]
        if isinstance(sound, (int, float)) and isinstance(repeat, (int, float)):
            sound = int(sound)
            repeat = int(repeat)
            if sound > 0 and repeat != 0:
                self._roboid._run_sound(sound, repeat)
                Runner.wait_until(self._evaluate_sound)
            else:
                self._roboid._cancel_sound()

    def beep(self):
        self.sound_until_done('beep')

    def signal_strength(self):
        return self.read(Zerone.SIGNAL_STRENGTH)

    def left_proximity(self):
        return self.read(Zerone.LEFT_PROXIMITY)

    def right_proximity(self):
        return self.read(Zerone.RIGHT_PROXIMITY)

    def front_proximity(self):
        return self.read(Zerone.FRONT_PROXIMITY)

    def rear_proximity(self):
        return self.read(Zerone.REAR_PROXIMITY)

    def color(self):
        return (self.read(Zerone.COLOR, 0), self.read(Zerone.COLOR, 1), self.read(Zerone.COLOR, 2))

    def color_r(self):
        return self.read(Zerone.COLOR, 0)

    def color_g(self):
        return self.read(Zerone.COLOR, 1)

    def color_b(self):
        return self.read(Zerone.COLOR, 2)

    def floor(self):
        return self.read(Zerone.FLOOR)

    def button(self):
        return self.read(Zerone.BUTTON)

    def clicked(self):
        return self.e(Zerone.CLICKED)

    def double_clicked(self):
        return self.e(Zerone.DOUBLE_CLICKED)

    def long_pressed(self):
        return self.e(Zerone.LONG_PRESSED)

    def gesture(self):
        if self.e(Zerone.GESTURE):
            return self.read(Zerone.GESTURE)
        return None

    def is_gesture(self, gesture):
        if self.e(Zerone.GESTURE):
            if isinstance(gesture, str):
                tmp = gesture.lower()
                if tmp in Zerone._GESTURES:
                    gesture = Zerone._GESTURES[tmp]
            if isinstance(gesture, (int, float)):
                return int(gesture) == self.read(Zerone.GESTURE)
        return False

    def color_number(self):
        return self.read(Zerone.COLOR_NUMBER)

    def is_color(self, color):
        if isinstance(color, str):
            tmp = color.lower()
            if tmp in Zerone._COLORS:
                color = Zerone._COLORS[tmp]
        if isinstance(color, (int, float)):
            return int(color) == self.read(Zerone.COLOR_NUMBER)
        return False

    def color_pattern(self):
        if self.e(Zerone.COLOR_PATTERN):
            pattern = self.read(Zerone.COLOR_PATTERN)
            return (pattern // 10, pattern % 10)
        return None

    def is_color_pattern(self, color1, color2):
        if self.e(Zerone.COLOR_PATTERN):
            if isinstance(color1, str):
                tmp = color1.lower()
                if tmp in Zerone._COLORS:
                    color1 = Zerone._COLORS[tmp]
            if isinstance(color2, str):
                tmp = color2.lower()
                if tmp in Zerone._COLORS:
                    color2 = Zerone._COLORS[tmp]
            if isinstance(color1, (int, float)) and isinstance(color2, (int, float)):
                return int(color1) * 10 + int(color2) == self.read(Zerone.COLOR_PATTERN)
        return False

    def pulse_count(self):
        return self.read(Zerone.PULSE_COUNT)

    def battery_state(self):
        return self.read(Zerone.BATTERY_STATE)
