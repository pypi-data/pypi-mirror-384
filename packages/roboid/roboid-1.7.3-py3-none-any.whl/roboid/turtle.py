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


class TurtleLoader(object):
    def __init__(self, param):
        self._param = param

    def load(self, serial, address):
        loaded = False
        count = 0
        while True:
            try:
                packet = self._read(serial)
                if packet:
                    if loaded:
                        if packet[0] == "B" and packet[1] == "0":
                            self._parse(packet)
                            self._write(serial, "7000000000000000000000000000000000004400-" + address + "\r")
                        elif packet[0] == "1":
                            return
                    else:
                        if packet[0] == "B" and packet[1] == "0":
                            self._parse(packet)
                            self._write(serial, "7000000000000000000000000000000000004400-" + address + "\r")
                            loaded = True
                        else:
                            if count % 10 == 0:
                                self._write(serial, "B000000000000000000000000000000000004400-" + address + "\r")
                            count += 1
            except:
                pass

    def _read(self, serial):
        try:
            line = bytearray()
            terminator = ord("\r")
            while True:
                c = serial.read()[0]
                line.append(c)
                if c == terminator: break
            return line.decode("utf-8")
        except:
            return ""

    def _write(self, serial, packet):
        try:
            serial.write(packet.encode())
        except:
            pass

    def _parse(self, packet):
        param = self._param
        packet = str(packet)
        value = int(packet[2:4], 16)
        if value > 0x7f: value -= 0x100
        param[0] = value + 1
        value = int(packet[4:6], 16)
        if value > 0x7f: value -= 0x100
        param[1] = value + 1
        value = int(packet[6:8], 16)
        if value > 0x7f: value -= 0x100
        param[2] = value + 1
        value = int(packet[8:10], 16)
        if value > 0x7f: value -= 0x100
        param[3] = value + 1
        value = int(packet[10:14], 16)
        if value > 0x7fff: value -= 0x10000
        distance = 2.3125 + (value + 1) / 10000.0
        if distance <= 0: param[4] = 2.3125
        else: param[4] = distance


class Turtle(Robot):
    ID = "kr.robomation.physical.turtle"

    LEFT_WHEEL = 0x00900000
    RIGHT_WHEEL = 0x00900001
    LED = 0x00900002
    BUZZER = 0x00900003
    PULSE = 0x00900004
    NOTE = 0x00900005
    SOUND = 0x00900006
    LINE_TRACER_MODE = 0x00900007
    LINE_TRACER_GAIN = 0x00900008
    LINE_TRACER_SPEED = 0x00900009
    LAMP = 0x0090000a
    LOCK = 0x0090000b

    SIGNAL_STRENGTH = 0x0090000d
    COLOR = 0x0090000e
    FLOOR = 0x0090000f
    ACCELERATION = 0x00900010
    TEMPERATURE = 0x00900011
    BUTTON = 0x00900012
    CLICKED = 0x00900013
    DOUBLE_CLICKED = 0x00900014
    LONG_PRESSED = 0x00900015
    COLOR_NUMBER = 0x00900016
    COLOR_PATTERN = 0x00900017
    PULSE_COUNT = 0x00900018
    WHEEL_STATE = 0x00900019
    SOUND_STATE = 0x0090001a
    LINE_TRACER_STATE = 0x0090001b
    TILT = 0x0090001c
    BATTERY_STATE = 0x0090001d

    COLOR_NONE = -1
    COLOR_BLACK = 0
    COLOR_RED = 1
    COLOR_ORANGE = 2
    COLOR_YELLOW = 3
    COLOR_GREEN = 4
    COLOR_SKY_BLUE = 5
    COLOR_CYAN = 5
    COLOR_BLUE = 6
    COLOR_PURPLE = 7
    COLOR_MAGENTA = 7
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
    LINE_TRACER_MODE_BLACK = 10
    LINE_TRACER_MODE_RED = 11
    LINE_TRACER_MODE_GREEN = 13
    LINE_TRACER_MODE_BLUE = 15
    LINE_TRACER_MODE_ANY = 17
    LINE_TRACER_MODE_TURN_LEFT = 20
    LINE_TRACER_MODE_TURN_RIGHT = 30
    LINE_TRACER_MODE_CROSS = 40
    LINE_TRACER_MODE_UTURN = 50
    LINE_TRACER_MODE_BLACK_UNTIL_RED = 61
    LINE_TRACER_MODE_BLACK_UNTIL_YELLOW = 62
    LINE_TRACER_MODE_BLACK_UNTIL_GREEN = 63
    LINE_TRACER_MODE_BLACK_UNTIL_CYAN = 64
    LINE_TRACER_MODE_BLACK_UNTIL_BLUE = 65
    LINE_TRACER_MODE_BLACK_UNTIL_MAGENTA = 66
    LINE_TRACER_MODE_BLACK_UNTIL_ANY = 67
    LINE_TRACER_MODE_RED_UNTIL_BLACK = 71
    LINE_TRACER_MODE_GREEN_UNTIL_BLACK = 73
    LINE_TRACER_MODE_BLUE_UNTIL_BLACK = 75
    LINE_TRACER_MODE_ANY_UNTIL_BLACK = 77

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
    SOUND_RANDOM = 2
    SOUND_RANDOM_BEEP = 2
    SOUND_SIREN = 3
    SOUND_ENGINE = 4
    SOUND_ROBOT = 5
    SOUND_MARCH = 6
    SOUND_BIRTHDAY = 7
    SOUND_DIBIDIBIDIP = 8
    SOUND_GOOD_JOB = 9

    SOUND_NAME_OFF = "off"
    SOUND_NAME_BEEP = "beep"
    SOUND_NAME_RANDOM_BEEP = "random beep"
    SOUND_NAME_SIREN = "siren"
    SOUND_NAME_ENGINE = "engine"
    SOUND_NAME_ROBOT = "robot"
    SOUND_NAME_MARCH = "march"
    SOUND_NAME_BIRTHDAY = "birthday"
    SOUND_NAME_DIBIDIBIDIP = "dibidibidip"
    SOUND_NAME_GOOD_JOB = "good job"

    TILT_FORWARD = 1
    TILT_BACKWARD = -1
    TILT_LEFT = 2
    TILT_RIGHT = -2
    TILT_FLIP = 3
    TILT_NOT = -3

    BATTERY_NORMAL = 2
    BATTERY_LOW = 1
    BATTERY_EMPTY = 0

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
        "black": 0,
        "red": 1,
        "orange": 2,
        "yellow": 3,
        "green": 4,
        "sky_blue": 5,
        "skyblue": 5,
        "sky blue": 5,
        "cyan": 5,
        "blue": 6,
        "purple": 7,
        "magenta": 7,
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
        "good_job": 9
    }
    _robots = {}

    def __init__(self, index=0, port_name=None):
        if isinstance(index, str):
            index = 0
            port_name = index
        if index in Turtle._robots:
            robot = Turtle._robots[index]
            if robot: robot.dispose()
        Turtle._robots[index] = self
        super(Turtle, self).__init__(Turtle.ID, "Turtle", index)
        self._param = [0, 0, 0, 0, 2.3125]
        self._bpm = 60
        self._init(port_name)

    def dispose(self):
        Turtle._robots[self.get_index()] = None
        self._roboid._dispose()
        Runner.unregister_robot(self)

    def reset(self):
        self._bpm = 60
        self._roboid._reset()

    def _init(self, port_name):
        from roboid.turtle_roboid import TurtleRoboid
        self._roboid = TurtleRoboid(self.get_index())
        self._add_roboid(self._roboid)
        Runner.register_robot(self)
        Runner.start()
        loader = TurtleLoader(self._param)
        self._roboid._init(loader, port_name)

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
            return Util.round(cm * 106.8)
        else:
            return 0

    def calc_turn_left_pulse(self, degree):
        if isinstance(degree, (int, float)):
            return Util.round(degree * (1570 + self._param[2]) / 360.0)
        else:
            return 0

    def calc_turn_right_pulse(self, degree):
        if isinstance(degree, (int, float)):
            return Util.round(degree * (1570 + self._param[0]) / 360.0)
        else:
            return 0

    def calc_pivot_left_pulse(self, degree):
        if isinstance(degree, (int, float)):
            return Util.round(degree * (3140 + self._param[3]) / 360.0)
        else:
            return 0

    def calc_pivot_right_pulse(self, degree):
        if isinstance(degree, (int, float)):
            return Util.round(degree * (3140 + self._param[1]) / 360.0)
        else:
            return 0

    def calc_inner_velocity(self, outer_velocity, radius):
        if isinstance(outer_velocity, (int, float)) and isinstance(radius, (int, float)):
            return outer_velocity * (radius - self._param[4]) / (radius + self._param[4])
        else:
            return 0

    def calc_circle_left_pulse(self, degree, radius):
        if isinstance(degree, (int, float)) and isinstance(radius, (int, float)):
            return Util.round(degree * (1570 + self._param[2]) * (radius + self._param[4]) / 360.0 / self._param[4])
        else:
            return 0

    def calc_circle_right_pulse(self, degree, radius):
        if isinstance(degree, (int, float)) and isinstance(radius, (int, float)):
            return Util.round(degree * (1570 + self._param[0]) * (radius + self._param[4]) / 360.0 / self._param[4])
        else:
            return 0

    def wheels(self, left_velocity, right_velocity=None):
        self.write(Turtle.PULSE, 0)
        self.write(Turtle.LINE_TRACER_MODE, Turtle.LINE_TRACER_MODE_OFF)
        if isinstance(left_velocity, (int, float)):
            self.write(Turtle.LEFT_WHEEL, left_velocity)
        if isinstance(right_velocity, (int, float)):
            self.write(Turtle.RIGHT_WHEEL, right_velocity)
        else:
            if isinstance(left_velocity, (int, float)):
                self.write(Turtle.RIGHT_WHEEL, left_velocity)

    def left_wheel(self, velocity):
        self.write(Turtle.PULSE, 0)
        self.write(Turtle.LINE_TRACER_MODE, Turtle.LINE_TRACER_MODE_OFF)
        if isinstance(velocity, (int, float)):
            self.write(Turtle.LEFT_WHEEL, velocity)

    def right_wheel(self, velocity):
        self.write(Turtle.PULSE, 0)
        self.write(Turtle.LINE_TRACER_MODE, Turtle.LINE_TRACER_MODE_OFF)
        if isinstance(velocity, (int, float)):
            self.write(Turtle.RIGHT_WHEEL, velocity)

    def stop(self):
        self.write(Turtle.PULSE, 0)
        self.write(Turtle.LINE_TRACER_MODE, Turtle.LINE_TRACER_MODE_OFF)
        self.write(Turtle.LEFT_WHEEL, 0)
        self.write(Turtle.RIGHT_WHEEL, 0)

    def _evaluate_wheel_state(self):
        return self.e(Turtle.WHEEL_STATE) and self.read(Turtle.WHEEL_STATE) == 0

    def _motion(self, pulse, left_velocity, right_velocity):
        self.write(Turtle.LINE_TRACER_MODE, Turtle.LINE_TRACER_MODE_OFF)
        self.write(Turtle.LEFT_WHEEL, 0)
        self.write(Turtle.RIGHT_WHEEL, 0)
        self.write(Turtle.PULSE, 0)
        Runner.wait(100)
        if pulse > 0:
            self.write(Turtle.LEFT_WHEEL, left_velocity)
            self.write(Turtle.RIGHT_WHEEL, right_velocity)
            self.write(Turtle.PULSE, pulse)
            Runner.wait_until(self._evaluate_wheel_state)
            self.write(Turtle.LEFT_WHEEL, 0)
            self.write(Turtle.RIGHT_WHEEL, 0)
            self.write(Turtle.PULSE, 0)
            Runner.wait(100)

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
            self._motion(self.calc_turn_left_pulse(degree), -velocity, velocity)

    def turn_right(self, degree=90, velocity=50):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(self.calc_turn_right_pulse(degree), velocity, -velocity)

    def pivot_left(self, degree, velocity=50):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(self.calc_pivot_left_pulse(degree), 0, velocity)

    def pivot_right(self, degree, velocity=50):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(self.calc_pivot_right_pulse(degree), velocity, 0)

    def circle_left(self, degree, radius, velocity=50):
        if isinstance(degree, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: degree = 0
            if degree < 0:
                degree = -degree
                velocity = -velocity
            left_velocity = self.calc_inner_velocity(velocity, radius)
            pulse = self.calc_circle_left_pulse(degree, radius)
            self._motion(pulse, left_velocity, velocity)

    def swing_left(self, degree, radius, velocity=50):
        self.circle_left(degree, radius, velocity)

    def circle_right(self, degree, radius, velocity=50):
        if isinstance(degree, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: degree = 0
            if degree < 0:
                degree = -degree
                velocity = -velocity
            right_velocity = self.calc_inner_velocity(velocity, radius)
            pulse = self.calc_circle_right_pulse(degree, radius)
            self._motion(pulse, velocity, right_velocity)

    def swing_right(self, degree, radius, velocity=50):
        self.circle_right(degree, radius, velocity)

    def _motion_sec(self, sec, left_velocity, right_velocity):
        self.write(Turtle.PULSE, 0)
        self.write(Turtle.LINE_TRACER_MODE, Turtle.LINE_TRACER_MODE_OFF)
        if sec < 0:
            sec = -sec
            left_velocity = -left_velocity
            right_velocity = -right_velocity
        if sec > 0:
            self.write(Turtle.LEFT_WHEEL, left_velocity)
            self.write(Turtle.RIGHT_WHEEL, right_velocity)
            Runner.wait(sec * 1000)
        self.write(Turtle.LEFT_WHEEL, 0)
        self.write(Turtle.RIGHT_WHEEL, 0)

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

    def circle_left_sec(self, sec, radius, velocity=50):
        if isinstance(sec, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: sec = 0
            left_velocity = self.calc_inner_velocity(velocity, radius)
            self._motion_sec(sec, left_velocity, velocity)

    def swing_left_sec(self, sec, radius, velocity=50):
        self.circle_left_sec(sec, radius, velocity)

    def circle_right_sec(self, sec, radius, velocity=50):
        if isinstance(sec, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: sec = 0
            right_velocity = self.calc_inner_velocity(velocity, radius)
            self._motion_sec(sec, velocity, right_velocity)

    def swing_right_sec(self, sec, radius, velocity=50):
        self.circle_right_sec(sec, radius, velocity)

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

    def circle_left_pulse(self, pulse, radius, velocity=50):
        if isinstance(pulse, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: pulse = 0
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            left_velocity = self.calc_inner_velocity(velocity, radius)
            self._motion(Util.round(pulse), left_velocity, velocity)

    def swing_left_pulse(self, pulse, radius, velocity=50):
        self.circle_left_pulse(pulse, radius, velocity)

    def circle_right_pulse(self, pulse, radius, velocity=50):
        if isinstance(pulse, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: pulse = 0
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            right_velocity = self.calc_inner_velocity(velocity, radius)
            self._motion(Util.round(pulse), velocity, right_velocity)

    def swing_right_pulse(self, pulse, radius, velocity=50):
        self.circle_right_pulse(pulse, radius, velocity)

    def _evaluate_line_tracer(self):
        return self.e(Turtle.LINE_TRACER_STATE) and self.read(Turtle.LINE_TRACER_STATE) == 0x02

    def line_tracer_mode(self, mode):
        self.write(Turtle.LEFT_WHEEL, 0)
        self.write(Turtle.RIGHT_WHEEL, 0)
        self.write(Turtle.PULSE, 0)
        if isinstance(mode, (int, float)):
            mode = int(mode)
            self.write(Turtle.LINE_TRACER_MODE, mode)
            if mode == 20 or mode == 30 or mode == 40 or mode == 50 or (mode >= 61 and mode <= 67) or mode == 71 or mode == 73 or mode == 75 or mode == 77:
                Runner.wait_until(self._evaluate_line_tracer)
                self.write(Turtle.LINE_TRACER_MODE, Turtle.LINE_TRACER_MODE_OFF)

    def black_line(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_BLACK)

    def red_line(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_RED)

    def green_line(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_GREEN)

    def blue_line(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_BLUE)

    def any_line(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_ANY)

    def black_line_until_red(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_BLACK_UNTIL_RED)

    def black_line_until_yellow(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_BLACK_UNTIL_YELLOW)

    def black_line_until_green(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_BLACK_UNTIL_GREEN)

    def black_line_until_sky_blue(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_BLACK_UNTIL_CYAN)

    def black_line_until_blue(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_BLACK_UNTIL_BLUE)

    def black_line_until_purple(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_BLACK_UNTIL_MAGENTA)

    def black_line_until_any(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_BLACK_UNTIL_ANY)

    def red_line_until_black(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_RED_UNTIL_BLACK)

    def green_line_until_black(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_GREEN_UNTIL_BLACK)

    def blue_line_until_black(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_BLUE_UNTIL_BLACK)

    def any_line_until_black(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_ANY_UNTIL_BLACK)

    def cross_forward(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_CROSS)

    def cross_left(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_TURN_LEFT)

    def cross_right(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_TURN_RIGHT)

    def cross_uturn(self):
        self.line_tracer_mode(Turtle.LINE_TRACER_MODE_UTURN)

    def line_gain(self, gain):
        if isinstance(gain, (int, float)):
            self.write(Turtle.LINE_TRACER_GAIN, Util.round(gain))

    def line_tracer_gain(self, gain):
        self.line_gain(gain)

    def line_speed(self, speed):
        if isinstance(speed, (int, float)):
            self.write(Turtle.LINE_TRACER_SPEED, Util.round(speed))

    def line_tracer_speed(self, speed):
        self.line_speed(speed)

    def rgb(self, red, green=None, blue=None):
        if isinstance(red, (int, float)):
            red = Util.round(red)
            if isinstance(green, (int, float)) and isinstance(blue, (int, float)):
                green = Util.round(green)
                blue = Util.round(blue)
                self.write(Turtle.LED, 0, red)
                self.write(Turtle.LED, 1, green)
                self.write(Turtle.LED, 2, blue)
            else:
                self.write(Turtle.LED, 0, red)
                self.write(Turtle.LED, 1, red)
                self.write(Turtle.LED, 2, red)
        elif isinstance(red, (list, tuple)):
            if len(red) >= 3 and isinstance(red[0], (int, float)) and isinstance(red[1], (int, float)) and isinstance(red[2], (int, float)):
                self.write(Turtle.LED, 0, Util.round(red[0]))
                self.write(Turtle.LED, 1, Util.round(red[1]))
                self.write(Turtle.LED, 2, Util.round(red[2]))

    def led(self, color1, color2=None, color3=None):
        if isinstance(color1, (int, float)):
            color1 = Util.round(color1)
            if isinstance(color2, (int, float)) and isinstance(color3, (int, float)):
                color2 = Util.round(color2)
                color3 = Util.round(color3)
                self.write(Turtle.LED, 0, color1)
                self.write(Turtle.LED, 1, color2)
                self.write(Turtle.LED, 2, color3)
            else:
                self.write(Turtle.LED, 0, color1)
                self.write(Turtle.LED, 1, color1)
                self.write(Turtle.LED, 2, color1)
        elif isinstance(color1, str):
            tmp = color1.lower()
            if tmp in Turtle._COLOR2RGB:
                self.write(Turtle.LED, Turtle._COLOR2RGB[tmp])
        elif isinstance(color1, (list, tuple)):
            if len(color1) >= 3 and isinstance(color1[0], (int, float)) and isinstance(color1[1], (int, float)) and isinstance(color1[2], (int, float)):
                self.write(Turtle.LED, 0, Util.round(color1[0]))
                self.write(Turtle.LED, 1, Util.round(color1[1]))
                self.write(Turtle.LED, 2, Util.round(color1[2]))

    def buzzer(self, hz):
        self.write(Turtle.NOTE, Turtle.NOTE_OFF)
        self._roboid._cancel_sound()
        if isinstance(hz, (int, float)):
            self.write(Turtle.BUZZER, hz)

    def tempo(self, bpm):
        if isinstance(bpm, (int, float)):
            if bpm > 0:
                self._bpm = bpm

    def note(self, pitch, beats=None):
        self.write(Turtle.BUZZER, 0)
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
                if tmp in Turtle._NOTES:
                    pitch = Turtle._NOTES[tmp] + (octave - 1) * 12
        if isinstance(pitch, (int, float)):
            pitch = int(pitch)
            if isinstance(beats, (int, float)):
                bpm = self._bpm
                if beats > 0 and bpm > 0:
                    if pitch == 0:
                        self.write(Turtle.NOTE, Turtle.NOTE_OFF)
                        Runner.wait(beats * 60 * 1000.0 / bpm)
                    elif pitch > 0:
                        timeout = beats * 60 * 1000.0 / bpm
                        tail = 0
                        if timeout > 100:
                            tail = 100
                        self.write(Turtle.NOTE, pitch)
                        Runner.wait(timeout - tail)
                        self.write(Turtle.NOTE, Turtle.NOTE_OFF)
                        if tail > 0:
                            Runner.wait(tail)
                else:
                    self.write(Turtle.NOTE, Turtle.NOTE_OFF)
            elif pitch >= 0:
                self.write(Turtle.NOTE, pitch)

    def _evaluate_sound(self):
        return self.e(Turtle.SOUND_STATE) and self.read(Turtle.SOUND_STATE) == 0

    def sound(self, sound, repeat=1):
        self.write(Turtle.BUZZER, 0)
        self.write(Turtle.NOTE, Turtle.NOTE_OFF)
        if isinstance(sound, str):
            tmp = sound.lower()
            if tmp in Turtle._SOUNDS:
                sound = Turtle._SOUNDS[tmp]
        if isinstance(sound, (int, float)) and isinstance(repeat, (int, float)):
            sound = int(sound)
            repeat = int(repeat)
            if sound > 0 and repeat != 0:
                self._roboid._run_sound(sound, repeat)
            else:
                self._roboid._cancel_sound()

    def sound_until_done(self, sound, repeat=1):
        self.write(Turtle.BUZZER, 0)
        self.write(Turtle.NOTE, Turtle.NOTE_OFF)
        if isinstance(sound, str):
            tmp = sound.lower()
            if tmp in Turtle._SOUNDS:
                sound = Turtle._SOUNDS[tmp]
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

    def lamp(self, on):
        if on:
            self.write(Turtle.LAMP, 1)
        else:
            self.write(Turtle.LAMP, 0)

    def lock(self, on):
        if on:
            self.write(Turtle.LOCK, 1)
        else:
            self.write(Turtle.LOCK, 0)

    def signal_strength(self):
        return self.read(Turtle.SIGNAL_STRENGTH)

    def floor(self):
        return self.read(Turtle.FLOOR)

    def acceleration_x(self):
        return self.read(Turtle.ACCELERATION, 0)

    def acceleration_y(self):
        return self.read(Turtle.ACCELERATION, 1)

    def acceleration_z(self):
        return self.read(Turtle.ACCELERATION, 2)

    def temperature(self):
        return self.read(Turtle.TEMPERATURE)

    def button(self):
        return self.read(Turtle.BUTTON)

    def clicked(self):
        return self.e(Turtle.CLICKED)

    def double_clicked(self):
        return self.e(Turtle.DOUBLE_CLICKED)

    def long_pressed(self):
        return self.e(Turtle.LONG_PRESSED)

    def color_number(self):
        return self.read(Turtle.COLOR_NUMBER)

    def is_color(self, color):
        if isinstance(color, str):
            tmp = color.lower()
            if tmp in Turtle._COLORS:
                color = Turtle._COLORS[tmp]
        if isinstance(color, (int, float)):
            return int(color) == self.read(Turtle.COLOR_NUMBER)
        return False

    def is_color_number(self, color):
        return self.is_color(color)

    def color_pattern(self):
        if self.e(Turtle.COLOR_PATTERN):
            pattern = self.read(Turtle.COLOR_PATTERN)
            return (pattern // 10, pattern % 10)
        return None

    def is_color_pattern(self, color1, color2):
        if self.e(Turtle.COLOR_PATTERN):
            if isinstance(color1, str):
                tmp = color1.lower()
                if tmp in Turtle._COLORS:
                    color1 = Turtle._COLORS[tmp]
            if isinstance(color2, str):
                tmp = color2.lower()
                if tmp in Turtle._COLORS:
                    color2 = Turtle._COLORS[tmp]
            if isinstance(color1, (int, float)) and isinstance(color2, (int, float)):
                return int(color1) * 10 + int(color2) == self.read(Turtle.COLOR_PATTERN)
        return False

    def pulse_count(self):
        return self.read(Turtle.PULSE_COUNT)

    def tilt(self):
        return self.read(Turtle.TILT)

    def battery_state(self):
        return self.read(Turtle.BATTERY_STATE)
