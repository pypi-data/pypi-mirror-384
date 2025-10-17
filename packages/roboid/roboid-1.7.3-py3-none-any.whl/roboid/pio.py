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


class Pio(Robot):
    ID = "kr.robomation.physical.pio"

    LEFT_WHEEL = 0x02000000
    RIGHT_WHEEL = 0x02000001
    LEFT_EYE = 0x02000002
    RIGHT_EYE = 0x02000003
    BUZZER = 0x02000004
    TURBO = 0x02000005
    PULSE = 0x02000006
    NECK_SPEED = 0x02000007
    NECK_ANGLE = 0x02000008
    EYE_PATTERN = 0x02000009
    NOTE = 0x0200000a
    SOUND = 0x0200000b
    MOTION = 0x0200000c

    SIGNAL_STRENGTH = 0x02000010
    FORWARD_BUTTON = 0x02000011
    BACKWARD_BUTTON = 0x02000012
    LEFT_BUTTON = 0x02000013
    RIGHT_BUTTON = 0x02000014
    RUN_BUTTON = 0x02000015
    BEHAVIOR_BUTTON = 0x02000016
    REPEAT_BUTTON = 0x02000017
    CLEAR_BUTTON = 0x02000018
    PULSE_COUNT = 0x02000019
    WHEEL_STATE = 0x0200001a
    NECK_ENCODER = 0x0200001b
    NECK_STATE = 0x0200001c
    EYE_STATE = 0x0200001d
    SOUND_STATE = 0x0200001e
    KEY_STATE = 0x0200001f
    BATTERY_STATE = 0x02000020
    USB_STATE = 0x02000021
    CHARGE_STATE = 0x02000022

    COLOR_NAME_OFF = "off"
    COLOR_NAME_RED = "red"
    COLOR_NAME_ORANGE = "orange"
    COLOR_NAME_YELLOW = "yellow"
    COLOR_NAME_GREEN = "green"
    COLOR_NAME_SKY_BLUE = "sky blue"
    COLOR_NAME_BLUE = "blue"
    COLOR_NAME_VIOLET = "violet"
    COLOR_NAME_PURPLE = "purple"
    COLOR_NAME_WHITE = "white"

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
    SOUND_RANDOM_MELODY = 18
    SOUND_POOP = 20
    SOUND_HAPPY = 12
    SOUND_ANGRY = 13
    SOUND_SAD = 14
    SOUND_SLEEP = 15
    SOUND_MARCH = 6
    SOUND_BIRTHDAY = 7
    SOUND_BATH = 21
    
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
    SOUND_NAME_RANDOM_MELODY = "random melody"
    SOUND_NAME_POOP = "poop"
    SOUND_NAME_HAPPY = "happy"
    SOUND_NAME_ANGRY = "angry"
    SOUND_NAME_SAD = "sad"
    SOUND_NAME_SLEEP = "sleep"
    SOUND_NAME_MARCH = "march"
    SOUND_NAME_BIRTHDAY = "birthday"
    SOUND_NAME_BATH = "bath"

    BATTERY_NORMAL = 3
    BATTERY_MIDDLE = 2
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
        "blue": (0, 0, 255),
        "violet": (63, 0, 255),
        "purple": (255, 0, 255),
        "white": (255, 255, 255)
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
        "sleep": 15,
        "random melody": 18,
        "random_melody": 18,
        "poop": 20,
        "bath": 21
    }
    CM_TO_PULSE = 968.0
    DEG_TO_PULSE_SPIN_RIGHT = 15104 / 360.0
    DEG_TO_PULSE_SPIN_LEFT = 15104 / 360.0
    DEG_TO_PULSE_PIVOT_RIGHT = 30336 / 360.0
    DEG_TO_PULSE_PIVOT_LEFT = 30375 / 360.0
    _robots = {}

    def __init__(self, index=0, port_name=None):
        if isinstance(index, str):
            index = 0
            port_name = index
        if index in Pio._robots:
            robot = Pio._robots[index]
            if robot: robot.dispose()
        Pio._robots[index] = self
        super(Pio, self).__init__(Pio.ID, "Pio", index)
        self._bpm = 60
        self._init(port_name)

    def dispose(self):
        Pio._robots[self.get_index()] = None
        self._roboid._dispose()
        Runner.unregister_robot(self)

    def reset(self):
        self._bpm = 60
        self._roboid._reset()

    def _init(self, port_name):
        from roboid.pio_roboid import PioRoboid
        self._roboid = PioRoboid(self.get_index())
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
            return Util.round(cm * Pio.CM_TO_PULSE)
        else:
            return 0

    def calc_turn_left_pulse(self, degree):
        if isinstance(degree, (int, float)):
            return Util.round(degree * Pio.DEG_TO_PULSE_SPIN_LEFT)
        else:
            return 0

    def calc_turn_right_pulse(self, degree):
        if isinstance(degree, (int, float)):
            return Util.round(degree * Pio.DEG_TO_PULSE_SPIN_RIGHT)
        else:
            return 0

    def calc_pivot_left_pulse(self, degree):
        if isinstance(degree, (int, float)):
            return Util.round(degree * Pio.DEG_TO_PULSE_PIVOT_LEFT)
        else:
            return 0

    def calc_pivot_right_pulse(self, degree):
        if isinstance(degree, (int, float)):
            return Util.round(degree * Pio.DEG_TO_PULSE_PIVOT_RIGHT)
        else:
            return 0

    def turbo(self, on):
        if on: self.write(Pio.TURBO, 1)
        else: self.write(Pio.TURBO, 0)

    def wheels(self, left_velocity, right_velocity=None):
        self.write(Pio.PULSE, 0)
        if isinstance(left_velocity, (int, float)):
            self.write(Pio.LEFT_WHEEL, left_velocity)
        if isinstance(right_velocity, (int, float)):
            self.write(Pio.RIGHT_WHEEL, right_velocity)
        else:
            if isinstance(left_velocity, (int, float)):
                self.write(Pio.RIGHT_WHEEL, left_velocity)

    def left_wheel(self, velocity):
        self.write(Pio.PULSE, 0)
        if isinstance(velocity, (int, float)):
            self.write(Pio.LEFT_WHEEL, velocity)

    def right_wheel(self, velocity):
        self.write(Pio.PULSE, 0)
        if isinstance(velocity, (int, float)):
            self.write(Pio.RIGHT_WHEEL, velocity)

    def stop(self):
        self.write(Pio.PULSE, 0)
        self.write(Pio.LEFT_WHEEL, 0)
        self.write(Pio.RIGHT_WHEEL, 0)

    def _evaluate_wheel_state(self):
        return self.e(Pio.WHEEL_STATE)

    def _motion(self, pulse, left_velocity, right_velocity):
        if pulse > 0:
            self.write(Pio.LEFT_WHEEL, left_velocity)
            self.write(Pio.RIGHT_WHEEL, right_velocity)
            self.write(Pio.PULSE, pulse)
            Runner.wait_until(self._evaluate_wheel_state)
            self.write(Pio.LEFT_WHEEL, 0)
            self.write(Pio.RIGHT_WHEEL, 0)
        else:
            self.write(Pio.LEFT_WHEEL, 0)
            self.write(Pio.RIGHT_WHEEL, 0)
            self.write(Pio.PULSE, 0)

    def move_forward(self, cm=10, velocity=70):
        if isinstance(cm, (int, float)) and isinstance(velocity, (int, float)):
            if cm < 0:
                cm = -cm
                velocity = -velocity
            self._motion(self.cm_to_pulse(cm), velocity, velocity)

    def move_backward(self, cm=10, velocity=70):
        if isinstance(cm, (int, float)) and isinstance(velocity, (int, float)):
            if cm < 0:
                cm = -cm
                velocity = -velocity
            self._motion(self.cm_to_pulse(cm), -velocity, -velocity)

    def turn_left(self, degree=90, velocity=70):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(self.calc_turn_left_pulse(degree), -velocity, velocity)

    def turn_right(self, degree=90, velocity=70):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(self.calc_turn_right_pulse(degree), velocity, -velocity)

    def pivot_left(self, degree, velocity=70):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(self.calc_pivot_left_pulse(degree), 0, velocity)

    def pivot_right(self, degree, velocity=70):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(self.calc_pivot_right_pulse(degree), velocity, 0)

    def _motion_sec(self, sec, left_velocity, right_velocity):
        self.write(Pio.PULSE, 0)
        if sec < 0:
            sec = -sec
            left_velocity = -left_velocity
            right_velocity = -right_velocity
        if sec > 0:
            self.write(Pio.LEFT_WHEEL, left_velocity)
            self.write(Pio.RIGHT_WHEEL, right_velocity)
            Runner.wait(sec * 1000)
        self.write(Pio.LEFT_WHEEL, 0)
        self.write(Pio.RIGHT_WHEEL, 0)

    def move_forward_sec(self, sec, velocity=70):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, velocity, velocity)

    def move_backward_sec(self, sec, velocity=70):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, -velocity, -velocity)

    def turn_left_sec(self, sec, velocity=70):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, -velocity, velocity)

    def turn_right_sec(self, sec, velocity=70):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, velocity, -velocity)

    def pivot_left_sec(self, sec, velocity=70):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, 0, velocity)

    def pivot_right_sec(self, sec, velocity=70):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, velocity, 0)

    def move_forward_pulse(self, pulse, velocity=70):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), velocity, velocity)

    def move_backward_pulse(self, pulse, velocity=70):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), -velocity, -velocity)

    def turn_left_pulse(self, pulse, velocity=70):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), -velocity, velocity)

    def turn_right_pulse(self, pulse, velocity=70):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), velocity, -velocity)

    def pivot_left_pulse(self, pulse, velocity=70):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), 0, velocity)

    def pivot_right_pulse(self, pulse, velocity=70):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), velocity, 0)

    def board_move_forward(self):
        self.move_forward(10)

    def board_move_backward(self):
        self.move_backward(10)

    def board_move_left(self):
        self.move_backward(1.45)
        self.turn_left(90)
        self.move_forward(11.45)

    def board_move_right(self):
        self.move_backward(1.45)
        self.turn_right(90)
        self.move_forward(11.45)

    def board_turn_left(self):
        self.move_backward(1.45)
        self.turn_left(90)
        self.move_forward(1.45)

    def board_turn_right(self):
        self.move_backward(1.45)
        self.turn_right(90)
        self.move_forward(1.45)

    def neck_speed(self, speed):
        if isinstance(speed, (int, float)):
            self.write(Pio.NECK_SPEED, Util.round(speed))

    def _evaluate_neck_state(self):
        return self.e(Pio.NECK_STATE)

    def neck_left(self, degree):
        if isinstance(degree, (int, float)):
            self.write(Pio.NECK_ANGLE, -degree)
            Runner.wait_until(self._evaluate_neck_state)

    def neck_right(self, degree):
        if isinstance(degree, (int, float)):
            self.write(Pio.NECK_ANGLE, degree)
            Runner.wait_until(self._evaluate_neck_state)

    def stop_neck(self):
        self.write(Pio.NECK_ANGLE, 0)

    def eyes(self, color1, color2=None, color3=None, color4=None, color5=None, color6=None):
        if isinstance(color1, (int, float)):
            color1 = Util.round(color1)
            if isinstance(color2, (int, float)):
                color2 = Util.round(color2)
                if isinstance(color3, (int, float)):
                    color3 = Util.round(color3)
                    self.write(Pio.LEFT_EYE, 0, color1)
                    self.write(Pio.LEFT_EYE, 1, color2)
                    self.write(Pio.LEFT_EYE, 2, color3)
                    if isinstance(color4, (int, float)) and isinstance(color5, (int, float)) and isinstance(color6, (int, float)):
                        color4 = Util.round(color4)
                        color5 = Util.round(color5)
                        color6 = Util.round(color6)
                        self.write(Pio.RIGHT_EYE, 0, color4)
                        self.write(Pio.RIGHT_EYE, 1, color5)
                        self.write(Pio.RIGHT_EYE, 2, color6)
                    else:
                        self.write(Pio.RIGHT_EYE, 0, color1)
                        self.write(Pio.RIGHT_EYE, 1, color2)
                        self.write(Pio.RIGHT_EYE, 2, color3)
                else:
                    self.write(Pio.LEFT_EYE, 0, color1)
                    self.write(Pio.LEFT_EYE, 1, color1)
                    self.write(Pio.LEFT_EYE, 2, color1)
                    self.write(Pio.RIGHT_EYE, 0, color2)
                    self.write(Pio.RIGHT_EYE, 1, color2)
                    self.write(Pio.RIGHT_EYE, 2, color2)
            else:
                self.write(Pio.LEFT_EYE, 0, color1)
                self.write(Pio.LEFT_EYE, 1, color1)
                self.write(Pio.LEFT_EYE, 2, color1)
                self.write(Pio.RIGHT_EYE, 0, color1)
                self.write(Pio.RIGHT_EYE, 1, color1)
                self.write(Pio.RIGHT_EYE, 2, color1)
        elif isinstance(color1, str):
            color1 = color1.lower()
            if color1 in Pio._COLOR2RGB:
                self.write(Pio.LEFT_EYE, Pio._COLOR2RGB[color1])
            if isinstance(color2, str):
                color2 = color2.lower()
                if color2 in Pio._COLOR2RGB:
                    self.write(Pio.RIGHT_EYE, Pio._COLOR2RGB[color2])
            elif color1 in Pio._COLOR2RGB:
                self.write(Pio.RIGHT_EYE, Pio._COLOR2RGB[color1])
        elif isinstance(color1, (list, tuple)):
            if len(color1) >= 3 and isinstance(color1[0], (int, float)) and isinstance(color1[1], (int, float)) and isinstance(color1[2], (int, float)):
                r = Util.round(color1[0])
                g = Util.round(color1[1])
                b = Util.round(color1[2])
                self.write(Pio.LEFT_EYE, 0, r)
                self.write(Pio.LEFT_EYE, 1, g)
                self.write(Pio.LEFT_EYE, 2, b)
                if isinstance(color2, (list, tuple)):
                    if len(color2) >= 3 and isinstance(color2[0], (int, float)) and isinstance(color2[1], (int, float)) and isinstance(color2[2], (int, float)):
                        self.write(Pio.RIGHT_EYE, 0, Util.round(color2[0]))
                        self.write(Pio.RIGHT_EYE, 1, Util.round(color2[1]))
                        self.write(Pio.RIGHT_EYE, 2, Util.round(color2[2]))
                else:
                    self.write(Pio.RIGHT_EYE, 0, r)
                    self.write(Pio.RIGHT_EYE, 1, g)
                    self.write(Pio.RIGHT_EYE, 2, b)

    def left_eye(self, color1, color2=None, color3=None):
        if isinstance(color1, (int, float)):
            color1 = Util.round(color1)
            if isinstance(color2, (int, float)) and isinstance(color3, (int, float)):
                color2 = Util.round(color2)
                color3 = Util.round(color3)
                self.write(Pio.LEFT_EYE, 0, color1)
                self.write(Pio.LEFT_EYE, 1, color2)
                self.write(Pio.LEFT_EYE, 2, color3)
            else:
                self.write(Pio.LEFT_EYE, 0, color1)
                self.write(Pio.LEFT_EYE, 1, color1)
                self.write(Pio.LEFT_EYE, 2, color1)
        elif isinstance(color1, str):
            tmp = color1.lower()
            if tmp in Pio._COLOR2RGB:
                self.write(Pio.LEFT_EYE, Pio._COLOR2RGB[tmp])
        elif isinstance(color1, (list, tuple)):
            if len(color1) >= 3 and isinstance(color1[0], (int, float)) and isinstance(color1[1], (int, float)) and isinstance(color1[2], (int, float)):
                self.write(Pio.LEFT_EYE, 0, Util.round(color1[0]))
                self.write(Pio.LEFT_EYE, 1, Util.round(color1[1]))
                self.write(Pio.LEFT_EYE, 2, Util.round(color1[2]))

    def right_eye(self, color1, color2=None, color3=None):
        if isinstance(color1, (int, float)):
            color1 = Util.round(color1)
            if isinstance(color2, (int, float)) and isinstance(color3, (int, float)):
                color2 = Util.round(color2)
                color3 = Util.round(color3)
                self.write(Pio.RIGHT_EYE, 0, color1)
                self.write(Pio.RIGHT_EYE, 1, color2)
                self.write(Pio.RIGHT_EYE, 2, color3)
            else:
                self.write(Pio.RIGHT_EYE, 0, color1)
                self.write(Pio.RIGHT_EYE, 1, color1)
                self.write(Pio.RIGHT_EYE, 2, color1)
        elif isinstance(color1, str):
            tmp = color1.lower()
            if tmp in Pio._COLOR2RGB:
                self.write(Pio.RIGHT_EYE, Pio._COLOR2RGB[tmp])
        elif isinstance(color1, (list, tuple)):
            if len(color1) >= 3 and isinstance(color1[0], (int, float)) and isinstance(color1[1], (int, float)) and isinstance(color1[2], (int, float)):
                self.write(Pio.RIGHT_EYE, 0, Util.round(color1[0]))
                self.write(Pio.RIGHT_EYE, 1, Util.round(color1[1]))
                self.write(Pio.RIGHT_EYE, 2, Util.round(color1[2]))

    def buzzer(self, hz):
        self.write(Pio.NOTE, Pio.NOTE_OFF)
        self._roboid._cancel_sound()
        if isinstance(hz, (int, float)):
            self.write(Pio.BUZZER, hz)

    def tempo(self, bpm):
        if isinstance(bpm, (int, float)):
            if bpm > 0:
                self._bpm = bpm

    def note(self, pitch, beats=None):
        self.write(Pio.BUZZER, 0)
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
                if tmp in Pio._NOTES:
                    pitch = Pio._NOTES[tmp] + (octave - 1) * 12
        if isinstance(pitch, (int, float)):
            pitch = int(pitch)
            if isinstance(beats, (int, float)):
                bpm = self._bpm
                if beats > 0 and bpm > 0:
                    if pitch == 0:
                        self.write(Pio.NOTE, Pio.NOTE_OFF)
                        Runner.wait(beats * 60 * 1000.0 / bpm)
                    elif pitch > 0:
                        timeout = beats * 60 * 1000.0 / bpm
                        tail = 0
                        if timeout > 100:
                            tail = 100
                        self.write(Pio.NOTE, pitch)
                        Runner.wait(timeout - tail)
                        self.write(Pio.NOTE, Pio.NOTE_OFF)
                        if tail > 0:
                            Runner.wait(tail)
                else:
                    self.write(Pio.NOTE, Pio.NOTE_OFF)
            elif pitch >= 0:
                self.write(Pio.NOTE, pitch)

    def _evaluate_sound(self):
        return self.e(Pio.SOUND_STATE)

    def sound(self, sound, repeat=1):
        self.write(Pio.BUZZER, 0)
        self.write(Pio.NOTE, Pio.NOTE_OFF)
        if isinstance(sound, str):
            tmp = sound.lower()
            if tmp in Pio._SOUNDS:
                sound = Pio._SOUNDS[tmp]
        if isinstance(sound, (int, float)) and isinstance(repeat, (int, float)):
            sound = int(sound)
            repeat = int(repeat)
            if sound > 0 and repeat != 0:
                self._roboid._run_sound(sound, repeat)
            else:
                self._roboid._cancel_sound()

    def sound_until_done(self, sound, repeat=1):
        self.write(Pio.BUZZER, 0)
        self.write(Pio.NOTE, Pio.NOTE_OFF)
        if isinstance(sound, str):
            tmp = sound.lower()
            if tmp in Pio._SOUNDS:
                sound = Pio._SOUNDS[tmp]
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
        return self.read(Pio.SIGNAL_STRENGTH)

    def forward_button(self):
        return self.read(Pio.FORWARD_BUTTON)

    def backward_button(self):
        return self.read(Pio.BACKWARD_BUTTON)

    def left_button(self):
        return self.read(Pio.LEFT_BUTTON)

    def right_button(self):
        return self.read(Pio.RIGHT_BUTTON)

    def run_button(self):
        return self.read(Pio.RUN_BUTTON)

    def behavior_button(self):
        return self.read(Pio.BEHAVIOR_BUTTON)

    def repeat_button(self):
        return self.read(Pio.REPEAT_BUTTON)

    def clear_button(self):
        return self.read(Pio.CLEAR_BUTTON)

    def forward_button_clicked(self):
        return self._roboid._is_forward_button_clicked()

    def backward_button_clicked(self):
        return self._roboid._is_backward_button_clicked()

    def left_button_clicked(self):
        return self._roboid._is_left_button_clicked()

    def right_button_clicked(self):
        return self._roboid._is_right_button_clicked()

    def run_button_clicked(self):
        return self._roboid._is_run_button_clicked()

    def behavior_button_clicked(self):
        return self._roboid._is_behavior_button_clicked()

    def repeat_button_clicked(self):
        return self._roboid._is_repeat_button_clicked()

    def clear_button_clicked(self):
        return self._roboid._is_clear_button_clicked()

    def forward_button_long_pressed(self):
        return self._roboid._is_forward_button_long_pressed()

    def backward_button_long_pressed(self):
        return self._roboid._is_backward_button_long_pressed()

    def left_button_long_pressed(self):
        return self._roboid._is_left_button_long_pressed()

    def right_button_long_pressed(self):
        return self._roboid._is_right_button_long_pressed()

    def run_button_long_pressed(self):
        return self._roboid._is_run_button_long_pressed()

    def behavior_button_long_pressed(self):
        return self._roboid._is_behavior_button_long_pressed()

    def repeat_button_long_pressed(self):
        return self._roboid._is_repeat_button_long_pressed()

    def clear_button_long_pressed(self):
        return self._roboid._is_clear_button_long_pressed()

    def pulse_count(self):
        return self.read(Pio.PULSE_COUNT)

    def battery_state(self):
        return self.read(Pio.BATTERY_STATE)

    def usb_state(self):
        return self.read(Pio.USB_STATE)

    def charge_state(self):
        return self.read(Pio.CHARGE_STATE)
