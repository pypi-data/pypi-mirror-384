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


class HamsterS(Robot):
    ID = "kr.robomation.physical.hamster.s"

    LEFT_WHEEL = 0x00400000
    RIGHT_WHEEL = 0x00400001
    BUZZER = 0x00400002
    OUTPUT_A = 0x00400003
    OUTPUT_B = 0x00400004
    NOTE = 0x00400008
    LINE_TRACER_MODE = 0x00400009
    LINE_TRACER_SPEED = 0x0040000a
    IO_MODE_A = 0x0040000b
    IO_MODE_B = 0x0040000c
    CONFIG_PROXIMITY = 0x0040000d
    CONFIG_GRAVITY = 0x0040000e
    CONFIG_BAND_WIDTH = 0x0040000f

    LEFT_RGB = 0x00E00100
    RIGHT_RGB = 0x00E00101
    PULSE = 0x00E00102
    SOUND = 0x00E00103
    LINE_TRACER_GAIN = 0x00E00104
    WRITE_SERIAL = 0x00E00105
    MOTOR_MODE = 0x00E00107

    SIGNAL_STRENGTH = 0x00400010
    LEFT_PROXIMITY = 0x00400011
    RIGHT_PROXIMITY = 0x00400012
    LEFT_FLOOR = 0x00400013
    RIGHT_FLOOR = 0x00400014
    ACCELERATION = 0x00400015
    LIGHT = 0x00400016
    TEMPERATURE = 0x00400017
    INPUT_A = 0x00400018
    INPUT_B = 0x00400019
    LINE_TRACER_STATE = 0x0040001a
    TILT = 0x0040001b
    BATTERY_STATE = 0x0040001c

    FREE_FALL = 0x00E00200
    TAP = 0x00E00201
    READ_SERIAL = 0x00E00202
    PULSE_COUNT = 0x00E00203
    WHEEL_STATE = 0x00E00204
    SOUND_STATE = 0x00E00205
    SERIAL_STATE = 0x00E00206

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

    LINE_TRACER_MODE_OFF = 0
    LINE_TRACER_MODE_BLACK_LEFT_SENSOR = 1
    LINE_TRACER_MODE_BLACK_RIGHT_SENSOR = 2
    LINE_TRACER_MODE_BLACK_BOTH_SENSORS = 3
    LINE_TRACER_MODE_BLACK_TURN_LEFT = 4
    LINE_TRACER_MODE_BLACK_TURN_RIGHT = 5
    LINE_TRACER_MODE_BLACK_MOVE_FORWARD = 6
    LINE_TRACER_MODE_BLACK_UTURN = 7
    LINE_TRACER_MODE_WHITE_LEFT_SENSOR = 8
    LINE_TRACER_MODE_WHITE_RIGHT_SENSOR = 9
    LINE_TRACER_MODE_WHITE_BOTH_SENSORS = 10
    LINE_TRACER_MODE_WHITE_TURN_LEFT = 11
    LINE_TRACER_MODE_WHITE_TURN_RIGHT = 12
    LINE_TRACER_MODE_WHITE_MOVE_FORWARD = 13
    LINE_TRACER_MODE_WHITE_UTURN = 14

    IO_MODE_ANALOG_INPUT = 0
    IO_MODE_ANALOG_INPUT_RELATIVE = 0
    IO_MODE_DIGITAL_INPUT = 1
    IO_MODE_DIGITAL_INPUT_TRI_STATE = 1
    IO_MODE_DIGITAL_INPUT_PULL_UP = 2
    IO_MODE_DIGITAL_INPUT_PULL_DOWN = 3
    IO_MODE_ANALOG_INPUT_ABSOLUTE = 4
    IO_MODE_VOLTAGE_INPUT = 5
    IO_MODE_SERVO_OUTPUT = 8
    IO_MODE_PWM_OUTPUT = 9
    IO_MODE_DIGITAL_OUTPUT = 10
    IO_MODE_SERIAL_9600 = 176
    IO_MODE_SERIAL_14400 = 177
    IO_MODE_SERIAL_19200 = 178
    IO_MODE_SERIAL_28800 = 179
    IO_MODE_SERIAL_38400 = 180
    IO_MODE_SERIAL_57600 = 181
    IO_MODE_SERIAL_76800 = 182
    IO_MODE_SERIAL_115200 = 183

    IO_MODE_NAME_ANALOG_INPUT = "analog input"
    IO_MODE_NAME_DIGITAL_INPUT = "digital input"
    IO_MODE_NAME_DIGITAL_INPUT_PULL_UP = "digital input pull up"
    IO_MODE_NAME_DIGITAL_INPUT_PULL_DOWN = "digital input pull down"
    IO_MODE_NAME_VOLTAGE_INPUT = "voltage input"
    IO_MODE_NAME_SERVO_OUTPUT = "servo output"
    IO_MODE_NAME_PWM_OUTPUT = "pwm output"
    IO_MODE_NAME_DIGITAL_OUTPUT = "digital output"

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

    TILT_FORWARD = 1
    TILT_BACKWARD = -1
    TILT_LEFT = 2
    TILT_RIGHT = -2
    TILT_FLIP = 3
    TILT_NOT = -3

    BATTERY_NORMAL = 2
    BATTERY_LOW = 1
    BATTERY_EMPTY = 0

    MOTOR_AUTO = 0
    MOTOR_WAVE = 1
    MOTOR_HALF = 2
    MOTOR_FULL = 3

    DELIMITER_COMMA = ","
    DELIMITER_COLON = ":"
    DELIMITER_DOLLAR = "$"
    DELIMITER_SHARP = "#"
    DELIMITER_LINE = "\r"

    _MOTOR_MODES = {
        "auto": 0,
        "wave": 1,
        "half": 2,
        "full": 3
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
        "sleep": 15
    }
    _IO_MODES = {
        "analog_input": IO_MODE_ANALOG_INPUT,
        "analog input": IO_MODE_ANALOG_INPUT,
        "digital_input": IO_MODE_DIGITAL_INPUT,
        "digital input": IO_MODE_DIGITAL_INPUT,
        "digital_input_pull_up": IO_MODE_DIGITAL_INPUT_PULL_UP,
        "digital input pull up": IO_MODE_DIGITAL_INPUT_PULL_UP,
        "digital_input_pull_down": IO_MODE_DIGITAL_INPUT_PULL_DOWN,
        "digital input pull down": IO_MODE_DIGITAL_INPUT_PULL_DOWN,
        "voltage_input": IO_MODE_VOLTAGE_INPUT,
        "voltage input": IO_MODE_VOLTAGE_INPUT,
        "servo_output": IO_MODE_SERVO_OUTPUT,
        "servo output": IO_MODE_SERVO_OUTPUT,
        "pwm_output": IO_MODE_PWM_OUTPUT,
        "pwm output": IO_MODE_PWM_OUTPUT,
        "digital_output": IO_MODE_DIGITAL_OUTPUT,
        "digital output": IO_MODE_DIGITAL_OUTPUT
    }
    _SPEED_TO_GAIN = {
        1: 6,
        2: 6,
        3: 5,
        4: 5,
        5: 4,
        6: 4,
        7: 3,
        8: 3,
        9: 2,
        10: 2
    }
    _SERIAL_DELIMITERS = {
        ",": 0x2C,
        ":": 0x3A,
        "$": 0x24,
        "#": 0x23,
        "\r": 0x0D
    }
    _SERIAL_BAUDS = {
        9600: IO_MODE_SERIAL_9600,
        14400: IO_MODE_SERIAL_14400,
        19200: IO_MODE_SERIAL_19200,
        28800: IO_MODE_SERIAL_28800,
        38400: IO_MODE_SERIAL_38400,
        57600: IO_MODE_SERIAL_57600,
        76800: IO_MODE_SERIAL_76800,
        115200: IO_MODE_SERIAL_115200
    }
    WHEEL_CENTER_DISTANCE = 1.636
    PEN_CENTER_DISTANCE = 2.462
    CM_TO_PULSE = 138.2666
    DEG_TO_PULSE = 4.039
    DEG_TO_PULSE_PIVOT = 8.047
    DEG_TO_PULSE_PIVOT_PEN = 3.984
    DEG_TO_PULSE_CIRCLE = 3.908
    DEG_TO_PULSE_CIRCLE_PEN_SAME = 3.833
    DEG_TO_PULSE_CIRCLE_PEN_DIFF = 3.916
    WHEEL_ROTATION_TO_PULSE = 2.46032
    _robots = {}

    def __init__(self, index=0, port_name=None):
        if isinstance(index, str):
            index = 0
            port_name = index
        if index in HamsterS._robots:
            robot = HamsterS._robots[index]
            if robot: robot.dispose()
        HamsterS._robots[index] = self
        super(HamsterS, self).__init__(HamsterS.ID, "HamsterS", index)
        self._bpm = 60
        self._gain = -1
        self._speed = 5
        self._serial_baud = HamsterS.IO_MODE_SERIAL_9600
        self._serial_input = ""
        self._init(port_name)

    def dispose(self):
        HamsterS._robots[self.get_index()] = None
        self._roboid._dispose()
        Runner.unregister_robot(self)

    def reset(self):
        self._bpm = 60
        self._gain = -1
        self._speed = 5
        self._serial_baud = HamsterS.IO_MODE_SERIAL_9600
        self._serial_input = ""
        self._roboid._reset()

    def _init(self, port_name):
        from roboid.hamster_s_roboid import HamsterSRoboid
        self._roboid = HamsterSRoboid(self.get_index())
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
            return Util.round(cm * HamsterS.CM_TO_PULSE)
        else:
            return 0

    def calc_turn_pulse(self, degree):
        if isinstance(degree, (int, float)):
            return Util.round(degree * HamsterS.DEG_TO_PULSE)
        else:
            return 0

    def calc_pivot_pulse(self, degree):
        if isinstance(degree, (int, float)):
            return Util.round(degree * HamsterS.DEG_TO_PULSE_PIVOT)
        else:
            return 0

    def calc_inner_velocity(self, outer_velocity, radius):
        if isinstance(outer_velocity, (int, float)) and isinstance(radius, (int, float)):
            return outer_velocity * (radius * 1.052 - HamsterS.WHEEL_CENTER_DISTANCE) / (radius * 1.052 + HamsterS.WHEEL_CENTER_DISTANCE)
        else:
            return 0

    def calc_circle_pulse(self, degree, radius, degree_to_pulse):
        if isinstance(degree, (int, float)) and isinstance(radius, (int, float)):
            return Util.round(degree * (2.3008 * radius + 4.234))
        else:
            return 0

    def motor_mode(self, mode):
        if isinstance(mode, (int, float)):
            self.write(HamsterS.MOTOR_MODE, int(mode))
        elif isinstance(mode, str):
            tmp = mode.lower()
            if tmp in HamsterS._MOTOR_MODES:
                self.write(HamsterS.MOTOR_MODE, HamsterS._MOTOR_MODES[tmp])

    def wheels(self, left_velocity, right_velocity=None):
        self.write(HamsterS.PULSE, 0)
        self.write(HamsterS.LINE_TRACER_MODE, HamsterS.LINE_TRACER_MODE_OFF)
        if isinstance(left_velocity, (int, float)):
            self.write(HamsterS.LEFT_WHEEL, left_velocity)
        if isinstance(right_velocity, (int, float)):
            self.write(HamsterS.RIGHT_WHEEL, right_velocity)
        else:
            if isinstance(left_velocity, (int, float)):
                self.write(HamsterS.RIGHT_WHEEL, left_velocity)

    def left_wheel(self, velocity):
        self.write(HamsterS.PULSE, 0)
        self.write(HamsterS.LINE_TRACER_MODE, HamsterS.LINE_TRACER_MODE_OFF)
        if isinstance(velocity, (int, float)):
            self.write(HamsterS.LEFT_WHEEL, velocity)

    def right_wheel(self, velocity):
        self.write(HamsterS.PULSE, 0)
        self.write(HamsterS.LINE_TRACER_MODE, HamsterS.LINE_TRACER_MODE_OFF)
        if isinstance(velocity, (int, float)):
            self.write(HamsterS.RIGHT_WHEEL, velocity)

    def stop(self):
        self.write(HamsterS.PULSE, 0)
        self.write(HamsterS.LINE_TRACER_MODE, HamsterS.LINE_TRACER_MODE_OFF)
        self.write(HamsterS.LEFT_WHEEL, 0)
        self.write(HamsterS.RIGHT_WHEEL, 0)

    def _evaluate_wheel_state(self):
        return self.e(HamsterS.WHEEL_STATE) and self.read(HamsterS.WHEEL_STATE) == 2

    def _motion(self, pulse, left_velocity, right_velocity):
        self.write(HamsterS.LINE_TRACER_MODE, HamsterS.LINE_TRACER_MODE_OFF)
        if pulse > 0:
            self.write(HamsterS.LEFT_WHEEL, left_velocity)
            self.write(HamsterS.RIGHT_WHEEL, right_velocity)
            self.write(HamsterS.PULSE, pulse)
            Runner.wait_until(self._evaluate_wheel_state)
            self.write(HamsterS.LEFT_WHEEL, 0)
            self.write(HamsterS.RIGHT_WHEEL, 0)
        else:
            self.write(HamsterS.LEFT_WHEEL, 0)
            self.write(HamsterS.RIGHT_WHEEL, 0)
            self.write(HamsterS.PULSE, 0)

    def rotate_wheels(self, degree=90, velocity=30):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(Util.round(degree * HamsterS.WHEEL_ROTATION_TO_PULSE), velocity, velocity)

    def rotate_left_wheel(self, degree=90, velocity=30):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(Util.round(degree * HamsterS.WHEEL_ROTATION_TO_PULSE), velocity, 0)

    def rotate_right_wheel(self, degree=90, velocity=30):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(Util.round(degree * HamsterS.WHEEL_ROTATION_TO_PULSE), 0, velocity)

    def move_forward(self, cm=5, velocity=30):
        if isinstance(cm, (int, float)) and isinstance(velocity, (int, float)):
            if cm < 0:
                cm = -cm
                velocity = -velocity
            self._motion(self.cm_to_pulse(cm), velocity, velocity)

    def move_backward(self, cm=5, velocity=30):
        if isinstance(cm, (int, float)) and isinstance(velocity, (int, float)):
            if cm < 0:
                cm = -cm
                velocity = -velocity
            self._motion(self.cm_to_pulse(cm), -velocity, -velocity)

    def turn_left(self, degree=90, velocity=30):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(self.calc_turn_pulse(degree), -velocity, velocity)

    def turn_right(self, degree=90, velocity=30):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(self.calc_turn_pulse(degree), velocity, -velocity)

    def pivot_left_wheel(self, degree, velocity=30):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(self.calc_pivot_pulse(degree), 0, velocity)

    def pivot_right_wheel(self, degree, velocity=30):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            self._motion(self.calc_pivot_pulse(degree), velocity, 0)

    def pivot_left_pen(self, degree, velocity=30):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            left_velocity = self.calc_inner_velocity(velocity, HamsterS.PEN_CENTER_DISTANCE)
            pulse = self.calc_circle_pulse(degree, HamsterS.PEN_CENTER_DISTANCE, HamsterS.DEG_TO_PULSE_PIVOT_PEN)
            self._motion(pulse, left_velocity, velocity)

    def pivot_right_pen(self, degree, velocity=30):
        if isinstance(degree, (int, float)) and isinstance(velocity, (int, float)):
            if degree < 0:
                degree = -degree
                velocity = -velocity
            right_velocity = self.calc_inner_velocity(velocity, HamsterS.PEN_CENTER_DISTANCE)
            pulse = self.calc_circle_pulse(degree, HamsterS.PEN_CENTER_DISTANCE, HamsterS.DEG_TO_PULSE_PIVOT_PEN)
            self._motion(pulse, velocity, right_velocity)

    def circle_left(self, degree, radius, velocity=30):
        if isinstance(degree, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: degree = 0
            if degree < 0:
                degree = -degree
                velocity = -velocity
            left_velocity = self.calc_inner_velocity(velocity, radius)
            pulse = self.calc_circle_pulse(degree, radius, HamsterS.DEG_TO_PULSE_CIRCLE)
            self._motion(pulse, left_velocity, velocity)

    def circle_right(self, degree, radius, velocity=30):
        if isinstance(degree, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: degree = 0
            if degree < 0:
                degree = -degree
                velocity = -velocity
            right_velocity = self.calc_inner_velocity(velocity, radius)
            pulse = self.calc_circle_pulse(degree, radius, HamsterS.DEG_TO_PULSE_CIRCLE)
            self._motion(pulse, velocity, right_velocity)

    def left_pen_circle_left(self, degree, radius, velocity=30):
        if isinstance(degree, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: degree = 0
            if degree < 0:
                degree = -degree
                velocity = -velocity
            radius += HamsterS.PEN_CENTER_DISTANCE
            left_velocity = self.calc_inner_velocity(velocity, radius)
            pulse = self.calc_circle_pulse(degree, radius, HamsterS.DEG_TO_PULSE_CIRCLE_PEN_SAME)
            self._motion(pulse, left_velocity, velocity)

    def left_pen_circle_right(self, degree, radius, velocity=30):
        if isinstance(degree, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: degree = 0
            if degree < 0:
                degree = -degree
                velocity = -velocity
            if radius >= HamsterS.PEN_CENTER_DISTANCE:
                radius -= HamsterS.PEN_CENTER_DISTANCE
                left_velocity = velocity
                right_velocity = self.calc_inner_velocity(velocity, radius)
            else:
                radius = HamsterS.PEN_CENTER_DISTANCE - radius
                left_velocity = -self.calc_inner_velocity(velocity, radius)
                right_velocity = -velocity
            pulse = self.calc_circle_pulse(degree, radius, HamsterS.DEG_TO_PULSE_CIRCLE_PEN_DIFF)
            self._motion(pulse, left_velocity, right_velocity)

    def right_pen_circle_left(self, degree, radius, velocity=30):
        if isinstance(degree, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: degree = 0
            if degree < 0:
                degree = -degree
                velocity = -velocity
            if radius >= HamsterS.PEN_CENTER_DISTANCE:
                radius -= HamsterS.PEN_CENTER_DISTANCE
                left_velocity = self.calc_inner_velocity(velocity, radius)
                right_velocity = velocity
            else:
                radius = HamsterS.PEN_CENTER_DISTANCE - radius
                left_velocity = -velocity
                right_velocity = -self.calc_inner_velocity(velocity, radius)
            pulse = self.calc_circle_pulse(degree, radius, HamsterS.DEG_TO_PULSE_CIRCLE_PEN_DIFF)
            self._motion(pulse, left_velocity, right_velocity)

    def right_pen_circle_right(self, degree, radius, velocity=30):
        if isinstance(degree, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: degree = 0
            if degree < 0:
                degree = -degree
                velocity = -velocity
            radius += HamsterS.PEN_CENTER_DISTANCE
            right_velocity = self.calc_inner_velocity(velocity, radius)
            pulse = self.calc_circle_pulse(degree, radius, HamsterS.DEG_TO_PULSE_CIRCLE_PEN_SAME)
            self._motion(pulse, velocity, right_velocity)

    def _motion_sec(self, sec, left_velocity, right_velocity):
        self.write(HamsterS.PULSE, 0)
        self.write(HamsterS.LINE_TRACER_MODE, HamsterS.LINE_TRACER_MODE_OFF)
        if sec < 0:
            sec = -sec
            left_velocity = -left_velocity
            right_velocity = -right_velocity
        if sec > 0:
            self.write(HamsterS.LEFT_WHEEL, left_velocity)
            self.write(HamsterS.RIGHT_WHEEL, right_velocity)
            Runner.wait(sec * 1000)
        self.write(HamsterS.LEFT_WHEEL, 0)
        self.write(HamsterS.RIGHT_WHEEL, 0)

    def move_forward_sec(self, sec, velocity=30):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, velocity, velocity)

    def move_backward_sec(self, sec, velocity=30):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, -velocity, -velocity)

    def turn_left_sec(self, sec, velocity=30):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, -velocity, velocity)

    def turn_right_sec(self, sec, velocity=30):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, velocity, -velocity)

    def pivot_left_wheel_sec(self, sec, velocity=30):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, 0, velocity)

    def pivot_right_wheel_sec(self, sec, velocity=30):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, velocity, 0)

    def pivot_left_pen_sec(self, sec, velocity=30):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            left_velocity = self.calc_inner_velocity(velocity, HamsterS.PEN_CENTER_DISTANCE)
            self._motion_sec(sec, left_velocity, velocity)

    def pivot_right_pen_sec(self, sec, velocity=30):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            right_velocity = self.calc_inner_velocity(velocity, HamsterS.PEN_CENTER_DISTANCE)
            self._motion_sec(sec, velocity, right_velocity)

    def circle_left_sec(self, sec, radius, velocity=30):
        if isinstance(sec, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: sec = 0
            left_velocity = self.calc_inner_velocity(velocity, radius)
            self._motion_sec(sec, left_velocity, velocity)

    def circle_right_sec(self, sec, radius, velocity=30):
        if isinstance(sec, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: sec = 0
            right_velocity = self.calc_inner_velocity(velocity, radius)
            self._motion_sec(sec, velocity, right_velocity)

    def left_pen_circle_left_sec(self, sec, radius, velocity=30):
        if isinstance(sec, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: sec = 0
            left_velocity = self.calc_inner_velocity(velocity, radius + HamsterS.PEN_CENTER_DISTANCE)
            self._motion_sec(sec, left_velocity, velocity)

    def left_pen_circle_right_sec(self, sec, radius, velocity=30):
        if isinstance(sec, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: sec = 0
            if radius >= HamsterS.PEN_CENTER_DISTANCE:
                left_velocity = velocity
                right_velocity = self.calc_inner_velocity(velocity, radius - HamsterS.PEN_CENTER_DISTANCE)
            else:
                left_velocity = -self.calc_inner_velocity(velocity, HamsterS.PEN_CENTER_DISTANCE - radius)
                right_velocity = -velocity
            self._motion_sec(sec, left_velocity, right_velocity)

    def right_pen_circle_left_sec(self, sec, radius, velocity=30):
        if isinstance(sec, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: sec = 0
            if radius >= HamsterS.PEN_CENTER_DISTANCE:
                left_velocity = self.calc_inner_velocity(velocity, radius - HamsterS.PEN_CENTER_DISTANCE)
                right_velocity = velocity
            else:
                left_velocity = -velocity
                right_velocity = -self.calc_inner_velocity(velocity, HamsterS.PEN_CENTER_DISTANCE - radius)
            self._motion_sec(sec, left_velocity, right_velocity)

    def right_pen_circle_right_sec(self, sec, radius, velocity=30):
        if isinstance(sec, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: sec = 0
            right_velocity = self.calc_inner_velocity(velocity, radius + HamsterS.PEN_CENTER_DISTANCE)
            self._motion_sec(sec, velocity, right_velocity)

    def move_forward_pulse(self, pulse, velocity=30):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), velocity, velocity)

    def move_backward_pulse(self, pulse, velocity=30):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), -velocity, -velocity)

    def turn_left_pulse(self, pulse, velocity=30):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), -velocity, velocity)

    def turn_right_pulse(self, pulse, velocity=30):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), velocity, -velocity)

    def pivot_left_wheel_pulse(self, pulse, velocity=30):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), 0, velocity)

    def pivot_right_wheel_pulse(self, pulse, velocity=30):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            self._motion(Util.round(pulse), velocity, 0)

    def pivot_left_pen_pulse(self, pulse, velocity=30):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            left_velocity = self.calc_inner_velocity(velocity, HamsterS.PEN_CENTER_DISTANCE)
            self._motion(Util.round(pulse), left_velocity, velocity)

    def pivot_right_pen_pulse(self, pulse, velocity=30):
        if isinstance(pulse, (int, float)) and isinstance(velocity, (int, float)):
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            right_velocity = self.calc_inner_velocity(velocity, HamsterS.PEN_CENTER_DISTANCE)
            self._motion(Util.round(pulse), velocity, right_velocity)

    def circle_left_pulse(self, pulse, radius, velocity=30):
        if isinstance(pulse, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: pulse = 0
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            left_velocity = self.calc_inner_velocity(velocity, radius)
            self._motion(Util.round(pulse), left_velocity, velocity)

    def circle_right_pulse(self, pulse, radius, velocity=30):
        if isinstance(pulse, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: pulse = 0
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            right_velocity = self.calc_inner_velocity(velocity, radius)
            self._motion(Util.round(pulse), velocity, right_velocity)

    def left_pen_circle_left_pulse(self, pulse, radius, velocity=30):
        if isinstance(pulse, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: pulse = 0
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            left_velocity = self.calc_inner_velocity(velocity, radius + HamsterS.PEN_CENTER_DISTANCE)
            self._motion(Util.round(pulse), left_velocity, velocity)

    def left_pen_circle_right_pulse(self, pulse, radius, velocity=30):
        if isinstance(pulse, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: pulse = 0
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            if radius >= HamsterS.PEN_CENTER_DISTANCE:
                left_velocity = velocity
                right_velocity = self.calc_inner_velocity(velocity, radius - HamsterS.PEN_CENTER_DISTANCE)
            else:
                left_velocity = -self.calc_inner_velocity(velocity, HamsterS.PEN_CENTER_DISTANCE - radius)
                right_velocity = -velocity
            self._motion(Util.round(pulse), left_velocity, right_velocity)

    def right_pen_circle_left_pulse(self, pulse, radius, velocity=30):
        if isinstance(pulse, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: pulse = 0
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            if radius >= HamsterS.PEN_CENTER_DISTANCE:
                left_velocity = self.calc_inner_velocity(velocity, radius - HamsterS.PEN_CENTER_DISTANCE)
                right_velocity = velocity
            else:
                left_velocity = -velocity
                right_velocity = -self.calc_inner_velocity(velocity, HamsterS.PEN_CENTER_DISTANCE - radius)
            self._motion(Util.round(pulse), left_velocity, right_velocity)

    def right_pen_circle_right_pulse(self, pulse, radius, velocity=30):
        if isinstance(pulse, (int, float)) and isinstance(radius, (int, float)) and isinstance(velocity, (int, float)):
            if radius < 0: pulse = 0
            if pulse < 0:
                pulse = -pulse
                velocity = -velocity
            right_velocity = self.calc_inner_velocity(velocity, radius + HamsterS.PEN_CENTER_DISTANCE)
            self._motion(Util.round(pulse), velocity, right_velocity)

    def _evaluate_line_tracer(self):
        return self.e(HamsterS.LINE_TRACER_STATE) and self.read(HamsterS.LINE_TRACER_STATE) == 0x40

    def line_tracer_mode(self, mode):
        self.write(HamsterS.LEFT_WHEEL, 0)
        self.write(HamsterS.RIGHT_WHEEL, 0)
        self.write(HamsterS.PULSE, 0)
        if isinstance(mode, (int, float)):
            mode = int(mode)
            self.write(HamsterS.LINE_TRACER_MODE, mode)
            if (mode >= 4 and mode <= 7) or (mode >= 11 and mode <= 14):
                Runner.wait_until(self._evaluate_line_tracer)
                self.write(HamsterS.LINE_TRACER_MODE, HamsterS.LINE_TRACER_MODE_OFF)

    def line_left(self):
        self.line_tracer_mode(HamsterS.LINE_TRACER_MODE_BLACK_LEFT_SENSOR)

    def line_right(self):
        self.line_tracer_mode(HamsterS.LINE_TRACER_MODE_BLACK_RIGHT_SENSOR)

    def line_both(self):
        self.line_tracer_mode(HamsterS.LINE_TRACER_MODE_BLACK_BOTH_SENSORS)

    def cross_forward(self):
        self.line_tracer_mode(HamsterS.LINE_TRACER_MODE_BLACK_MOVE_FORWARD)

    def cross_left(self):
        self.line_tracer_mode(HamsterS.LINE_TRACER_MODE_BLACK_TURN_LEFT)

    def cross_right(self):
        self.line_tracer_mode(HamsterS.LINE_TRACER_MODE_BLACK_TURN_RIGHT)

    def cross_uturn(self):
        self.line_tracer_mode(HamsterS.LINE_TRACER_MODE_BLACK_UTURN)

    def white_line_left(self):
        self.line_tracer_mode(HamsterS.LINE_TRACER_MODE_WHITE_LEFT_SENSOR)

    def white_line_right(self):
        self.line_tracer_mode(HamsterS.LINE_TRACER_MODE_WHITE_RIGHT_SENSOR)

    def white_line_both(self):
        self.line_tracer_mode(HamsterS.LINE_TRACER_MODE_WHITE_BOTH_SENSORS)

    def white_cross_forward(self):
        self.line_tracer_mode(HamsterS.LINE_TRACER_MODE_WHITE_MOVE_FORWARD)

    def white_cross_left(self):
        self.line_tracer_mode(HamsterS.LINE_TRACER_MODE_WHITE_TURN_LEFT)

    def white_cross_right(self):
        self.line_tracer_mode(HamsterS.LINE_TRACER_MODE_WHITE_TURN_RIGHT)

    def white_cross_uturn(self):
        self.line_tracer_mode(HamsterS.LINE_TRACER_MODE_WHITE_UTURN)

    def _speed_to_gain(self, speed):
        if isinstance(speed, (int, float)):
            speed = int(speed)
            if speed > 10: speed = 10
            elif speed < 1: speed = 1
            return HamsterS._SPEED_TO_GAIN[speed]
        return 2

    def line_gain(self, gain):
        if isinstance(gain, str):
            tmp = gain.lower()
            if tmp == "auto":
                gain = -1
        if isinstance(gain, (int, float)):
            gain = int(gain)
            if gain > 0:
                self._gain = gain
                self.write(HamsterS.LINE_TRACER_GAIN, gain)
            else:
                self._gain = -1
                gain = self._speed_to_gain(self._speed)
                if gain > 0:
                    self.write(HamsterS.LINE_TRACER_GAIN, gain)

    def line_speed(self, speed):
        if isinstance(speed, (int, float)):
            speed = int(speed)
            gain = self._gain
            if gain < 0: gain = self._speed_to_gain(speed)
            if speed > 0 and gain > 0:
                self._speed = speed
                self.write(HamsterS.LINE_TRACER_SPEED, speed)
                self.write(HamsterS.LINE_TRACER_GAIN, gain)

    def line_tracer_speed(self, speed):
        self.line_speed(speed)

    def _evaluate_board_forward(self):
        if self._board_state == 1:
            if self._board_count < 2:
                left_floor = self.read(HamsterS.LEFT_FLOOR)
                right_floor = self.read(HamsterS.RIGHT_FLOOR)
                if left_floor < 50 and right_floor < 50:
                    self._board_count += 1
                else:
                    self._board_count = 0
                diff = (left_floor - right_floor) * 0.25
                self.write(HamsterS.LEFT_WHEEL, 45 + diff)
                self.write(HamsterS.RIGHT_WHEEL, 45 - diff)
            else:
                self._board_count = 0
                self._board_state = 2
        elif self._board_state == 2:
            if self._board_count < 10:
                self._board_count += 1
                diff = (self.read(HamsterS.LEFT_FLOOR) - self.read(HamsterS.RIGHT_FLOOR)) * 0.25
                self.write(HamsterS.LEFT_WHEEL, 45 + diff)
                self.write(HamsterS.RIGHT_WHEEL, 45 - diff)
            else:
                self.write(HamsterS.LEFT_WHEEL, 0)
                self.write(HamsterS.RIGHT_WHEEL, 0)
                return True
        return False

    def board_forward(self):
        self.write(HamsterS.PULSE, 0)
        self.write(HamsterS.LINE_TRACER_MODE, HamsterS.LINE_TRACER_MODE_OFF)
        self.write(HamsterS.LEFT_WHEEL, 45)
        self.write(HamsterS.RIGHT_WHEEL, 45)
        self._board_count = 0
        self._board_state = 1
        Runner.wait_until(self._evaluate_board_forward)

    def _evaluate_board_left(self):
        state = self._board_state
        if state == 1:
            if self._board_count < 2:
                if self.read(HamsterS.LEFT_FLOOR) > 50:
                    self._board_count += 1
            else:
                self._board_count = 0
                self._board_state = 2
        elif state == 2:
            if self.read(HamsterS.LEFT_FLOOR) < 20:
                self._board_state = 3
        elif state == 3:
            if self._board_count < 2:
                if self.read(HamsterS.LEFT_FLOOR) < 20:
                    self._board_count += 1
            else:
                self._board_count = 0
                self._board_state = 4
        elif state == 4:
            if self.read(HamsterS.LEFT_FLOOR) > 50:
                self._board_state = 5
        elif state == 5:
            diff = self.read(HamsterS.LEFT_FLOOR) - self.read(HamsterS.RIGHT_FLOOR)
            if diff > -15:
                self.write(HamsterS.LEFT_WHEEL, 0)
                self.write(HamsterS.RIGHT_WHEEL, 0)
                return True
            else:
                diff *= 0.5
                self.write(HamsterS.LEFT_WHEEL, diff)
                self.write(HamsterS.RIGHT_WHEEL, -diff)
        return False

    def board_left(self):
        self.turn_left(90, 45)
        """self.write(HamsterS.PULSE, 0)
        self.write(HamsterS.LINE_TRACER_MODE, HamsterS.LINE_TRACER_MODE_OFF)
        self.write(HamsterS.LEFT_WHEEL, -45)
        self.write(HamsterS.RIGHT_WHEEL, 45)
        self._board_count = 0
        self._board_state = 1
        Runner.wait_until(self._evaluate_board_left)"""

    def _evaluate_board_right(self):
        state = self._board_state
        if state == 1:
            if self._board_count < 2:
                if self.read(HamsterS.RIGHT_FLOOR) > 50:
                    self._board_count += 1
            else:
                self._board_count = 0
                self._board_state = 2
        elif state == 2:
            if self.read(HamsterS.RIGHT_FLOOR) < 20:
                self._board_state = 3
        elif state == 3:
            if self._board_count < 2:
                if self.read(HamsterS.RIGHT_FLOOR) < 20:
                    self._board_count += 1
            else:
                self._board_count = 0
                self._board_state = 4
        elif state == 4:
            if self.read(HamsterS.RIGHT_FLOOR) > 50:
                self._board_state = 5
        elif state == 5:
            diff = self.read(HamsterS.RIGHT_FLOOR) - self.read(HamsterS.LEFT_FLOOR)
            if diff > -15:
                self.write(HamsterS.LEFT_WHEEL, 0)
                self.write(HamsterS.RIGHT_WHEEL, 0)
                return True
            else:
                diff *= 0.5
                self.write(HamsterS.LEFT_WHEEL, -diff)
                self.write(HamsterS.RIGHT_WHEEL, diff)
        return False

    def board_right(self):
        self.turn_right(90, 45)
        """self.write(HamsterS.PULSE, 0)
        self.write(HamsterS.LINE_TRACER_MODE, HamsterS.LINE_TRACER_MODE_OFF)
        self.write(HamsterS.LEFT_WHEEL, 45)
        self.write(HamsterS.RIGHT_WHEEL, -45)
        self._board_count = 0
        self._board_state = 1
        Runner.wait_until(self._evaluate_board_right)"""

    def rgbs(self, color1, color2=None, color3=None, color4=None, color5=None, color6=None):
        if isinstance(color1, (int, float)):
            color1 = Util.round(color1)
            if isinstance(color2, (int, float)):
                color2 = Util.round(color2)
                if isinstance(color3, (int, float)):
                    color3 = Util.round(color3)
                    self.write(HamsterS.LEFT_RGB, 0, color1)
                    self.write(HamsterS.LEFT_RGB, 1, color2)
                    self.write(HamsterS.LEFT_RGB, 2, color3)
                    if isinstance(color4, (int, float)) and isinstance(color5, (int, float)) and isinstance(color6, (int, float)):
                        color4 = Util.round(color4)
                        color5 = Util.round(color5)
                        color6 = Util.round(color6)
                        self.write(HamsterS.RIGHT_RGB, 0, color4)
                        self.write(HamsterS.RIGHT_RGB, 1, color5)
                        self.write(HamsterS.RIGHT_RGB, 2, color6)
                    else:
                        self.write(HamsterS.RIGHT_RGB, 0, color1)
                        self.write(HamsterS.RIGHT_RGB, 1, color2)
                        self.write(HamsterS.RIGHT_RGB, 2, color3)
                else:
                    self.write(HamsterS.LEFT_RGB, 0, color1)
                    self.write(HamsterS.LEFT_RGB, 1, color1)
                    self.write(HamsterS.LEFT_RGB, 2, color1)
                    self.write(HamsterS.RIGHT_RGB, 0, color2)
                    self.write(HamsterS.RIGHT_RGB, 1, color2)
                    self.write(HamsterS.RIGHT_RGB, 2, color2)
            else:
                self.write(HamsterS.LEFT_RGB, 0, color1)
                self.write(HamsterS.LEFT_RGB, 1, color1)
                self.write(HamsterS.LEFT_RGB, 2, color1)
                self.write(HamsterS.RIGHT_RGB, 0, color1)
                self.write(HamsterS.RIGHT_RGB, 1, color1)
                self.write(HamsterS.RIGHT_RGB, 2, color1)
        elif isinstance(color1, (list, tuple)):
            if len(color1) >= 3 and isinstance(color1[0], (int, float)) and isinstance(color1[1], (int, float)) and isinstance(color1[2], (int, float)):
                r = Util.round(color1[0])
                g = Util.round(color1[1])
                b = Util.round(color1[2])
                self.write(HamsterS.LEFT_RGB, 0, r)
                self.write(HamsterS.LEFT_RGB, 1, g)
                self.write(HamsterS.LEFT_RGB, 2, b)
                if isinstance(color2, (list, tuple)):
                    if len(color2) >= 3 and isinstance(color2[0], (int, float)) and isinstance(color2[1], (int, float)) and isinstance(color2[2], (int, float)):
                        self.write(HamsterS.RIGHT_RGB, 0, Util.round(color2[0]))
                        self.write(HamsterS.RIGHT_RGB, 1, Util.round(color2[1]))
                        self.write(HamsterS.RIGHT_RGB, 2, Util.round(color2[2]))
                else:
                    self.write(HamsterS.RIGHT_RGB, 0, r)
                    self.write(HamsterS.RIGHT_RGB, 1, g)
                    self.write(HamsterS.RIGHT_RGB, 2, b)

    def left_rgb(self, red, green=None, blue=None):
        if isinstance(red, (int, float)):
            red = Util.round(red)
            if isinstance(green, (int, float)) and isinstance(blue, (int, float)):
                green = Util.round(green)
                blue = Util.round(blue)
                self.write(HamsterS.LEFT_RGB, 0, red)
                self.write(HamsterS.LEFT_RGB, 1, green)
                self.write(HamsterS.LEFT_RGB, 2, blue)
            else:
                self.write(HamsterS.LEFT_RGB, 0, red)
                self.write(HamsterS.LEFT_RGB, 1, red)
                self.write(HamsterS.LEFT_RGB, 2, red)
        elif isinstance(red, (list, tuple)):
            if len(red) >= 3 and isinstance(red[0], (int, float)) and isinstance(red[1], (int, float)) and isinstance(red[2], (int, float)):
                self.write(HamsterS.LEFT_RGB, 0, Util.round(red[0]))
                self.write(HamsterS.LEFT_RGB, 1, Util.round(red[1]))
                self.write(HamsterS.LEFT_RGB, 2, Util.round(red[2]))

    def right_rgb(self, red, green=None, blue=None):
        if isinstance(red, (int, float)):
            red = Util.round(red)
            if isinstance(green, (int, float)) and isinstance(blue, (int, float)):
                green = Util.round(green)
                blue = Util.round(blue)
                self.write(HamsterS.RIGHT_RGB, 0, red)
                self.write(HamsterS.RIGHT_RGB, 1, green)
                self.write(HamsterS.RIGHT_RGB, 2, blue)
            else:
                self.write(HamsterS.RIGHT_RGB, 0, red)
                self.write(HamsterS.RIGHT_RGB, 1, red)
                self.write(HamsterS.RIGHT_RGB, 2, red)
        elif isinstance(red, (list, tuple)):
            if len(red) >= 3 and isinstance(red[0], (int, float)) and isinstance(red[1], (int, float)) and isinstance(red[2], (int, float)):
                self.write(HamsterS.RIGHT_RGB, 0, Util.round(red[0]))
                self.write(HamsterS.RIGHT_RGB, 1, Util.round(red[1]))
                self.write(HamsterS.RIGHT_RGB, 2, Util.round(red[2]))

    def leds(self, color1, color2=None, color3=None, color4=None, color5=None, color6=None):
        if isinstance(color1, (int, float)):
            color1 = Util.round(color1)
            if isinstance(color2, (int, float)):
                color2 = Util.round(color2)
                if isinstance(color3, (int, float)):
                    color3 = Util.round(color3)
                    self.write(HamsterS.LEFT_RGB, 0, color1)
                    self.write(HamsterS.LEFT_RGB, 1, color2)
                    self.write(HamsterS.LEFT_RGB, 2, color3)
                    if isinstance(color4, (int, float)) and isinstance(color5, (int, float)) and isinstance(color6, (int, float)):
                        color4 = Util.round(color4)
                        color5 = Util.round(color5)
                        color6 = Util.round(color6)
                        self.write(HamsterS.RIGHT_RGB, 0, color4)
                        self.write(HamsterS.RIGHT_RGB, 1, color5)
                        self.write(HamsterS.RIGHT_RGB, 2, color6)
                    else:
                        self.write(HamsterS.RIGHT_RGB, 0, color1)
                        self.write(HamsterS.RIGHT_RGB, 1, color2)
                        self.write(HamsterS.RIGHT_RGB, 2, color3)
                else:
                    self.write(HamsterS.LEFT_RGB, 0, color1)
                    self.write(HamsterS.LEFT_RGB, 1, color1)
                    self.write(HamsterS.LEFT_RGB, 2, color1)
                    self.write(HamsterS.RIGHT_RGB, 0, color2)
                    self.write(HamsterS.RIGHT_RGB, 1, color2)
                    self.write(HamsterS.RIGHT_RGB, 2, color2)
            else:
                self.write(HamsterS.LEFT_RGB, 0, color1)
                self.write(HamsterS.LEFT_RGB, 1, color1)
                self.write(HamsterS.LEFT_RGB, 2, color1)
                self.write(HamsterS.RIGHT_RGB, 0, color1)
                self.write(HamsterS.RIGHT_RGB, 1, color1)
                self.write(HamsterS.RIGHT_RGB, 2, color1)
        elif isinstance(color1, str):
            color1 = color1.lower()
            if color1 in HamsterS._COLOR2RGB:
                self.write(HamsterS.LEFT_RGB, HamsterS._COLOR2RGB[color1])
            if isinstance(color2, str):
                color2 = color2.lower()
                if color2 in HamsterS._COLOR2RGB:
                    self.write(HamsterS.RIGHT_RGB, HamsterS._COLOR2RGB[color2])
            elif color1 in HamsterS._COLOR2RGB:
                self.write(HamsterS.RIGHT_RGB, HamsterS._COLOR2RGB[color1])
        elif isinstance(color1, (list, tuple)):
            if len(color1) >= 3 and isinstance(color1[0], (int, float)) and isinstance(color1[1], (int, float)) and isinstance(color1[2], (int, float)):
                r = Util.round(color1[0])
                g = Util.round(color1[1])
                b = Util.round(color1[2])
                self.write(HamsterS.LEFT_RGB, 0, r)
                self.write(HamsterS.LEFT_RGB, 1, g)
                self.write(HamsterS.LEFT_RGB, 2, b)
                if isinstance(color2, (list, tuple)):
                    if len(color2) >= 3 and isinstance(color2[0], (int, float)) and isinstance(color2[1], (int, float)) and isinstance(color2[2], (int, float)):
                        self.write(HamsterS.RIGHT_RGB, 0, Util.round(color2[0]))
                        self.write(HamsterS.RIGHT_RGB, 1, Util.round(color2[1]))
                        self.write(HamsterS.RIGHT_RGB, 2, Util.round(color2[2]))
                else:
                    self.write(HamsterS.RIGHT_RGB, 0, r)
                    self.write(HamsterS.RIGHT_RGB, 1, g)
                    self.write(HamsterS.RIGHT_RGB, 2, b)

    def left_led(self, color1, color2=None, color3=None):
        if isinstance(color1, (int, float)):
            color1 = Util.round(color1)
            if isinstance(color2, (int, float)) and isinstance(color3, (int, float)):
                color2 = Util.round(color2)
                color3 = Util.round(color3)
                self.write(HamsterS.LEFT_RGB, 0, color1)
                self.write(HamsterS.LEFT_RGB, 1, color2)
                self.write(HamsterS.LEFT_RGB, 2, color3)
            else:
                self.write(HamsterS.LEFT_RGB, 0, color1)
                self.write(HamsterS.LEFT_RGB, 1, color1)
                self.write(HamsterS.LEFT_RGB, 2, color1)
        elif isinstance(color1, str):
            tmp = color1.lower()
            if tmp in HamsterS._COLOR2RGB:
                self.write(HamsterS.LEFT_RGB, HamsterS._COLOR2RGB[tmp])
        elif isinstance(color1, (list, tuple)):
            if len(color1) >= 3 and isinstance(color1[0], (int, float)) and isinstance(color1[1], (int, float)) and isinstance(color1[2], (int, float)):
                self.write(HamsterS.LEFT_RGB, 0, Util.round(color1[0]))
                self.write(HamsterS.LEFT_RGB, 1, Util.round(color1[1]))
                self.write(HamsterS.LEFT_RGB, 2, Util.round(color1[2]))

    def right_led(self, color1, color2=None, color3=None):
        if isinstance(color1, (int, float)):
            color1 = Util.round(color1)
            if isinstance(color2, (int, float)) and isinstance(color3, (int, float)):
                color2 = Util.round(color2)
                color3 = Util.round(color3)
                self.write(HamsterS.RIGHT_RGB, 0, color1)
                self.write(HamsterS.RIGHT_RGB, 1, color2)
                self.write(HamsterS.RIGHT_RGB, 2, color3)
            else:
                self.write(HamsterS.RIGHT_RGB, 0, color1)
                self.write(HamsterS.RIGHT_RGB, 1, color1)
                self.write(HamsterS.RIGHT_RGB, 2, color1)
        elif isinstance(color1, str):
            tmp = color1.lower()
            if tmp in HamsterS._COLOR2RGB:
                self.write(HamsterS.RIGHT_RGB, HamsterS._COLOR2RGB[tmp])
        elif isinstance(color1, (list, tuple)):
            if len(color1) >= 3 and isinstance(color1[0], (int, float)) and isinstance(color1[1], (int, float)) and isinstance(color1[2], (int, float)):
                self.write(HamsterS.RIGHT_RGB, 0, Util.round(color1[0]))
                self.write(HamsterS.RIGHT_RGB, 1, Util.round(color1[1]))
                self.write(HamsterS.RIGHT_RGB, 2, Util.round(color1[2]))

    def buzzer(self, hz):
        self.write(HamsterS.NOTE, HamsterS.NOTE_OFF)
        self._roboid._cancel_sound()
        if isinstance(hz, (int, float)):
            self.write(HamsterS.BUZZER, hz)

    def tempo(self, bpm):
        if isinstance(bpm, (int, float)):
            if bpm > 0:
                self._bpm = bpm

    def note(self, pitch, beats=None):
        self.write(HamsterS.BUZZER, 0)
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
                if tmp in HamsterS._NOTES:
                    pitch = HamsterS._NOTES[tmp] + (octave - 1) * 12
        if isinstance(pitch, (int, float)):
            pitch = int(pitch)
            if isinstance(beats, (int, float)):
                bpm = self._bpm
                if beats > 0 and bpm > 0:
                    if pitch == 0:
                        self.write(HamsterS.NOTE, HamsterS.NOTE_OFF)
                        Runner.wait(beats * 60 * 1000.0 / bpm)
                    elif pitch > 0:
                        timeout = beats * 60 * 1000.0 / bpm
                        tail = 0
                        if timeout > 100:
                            tail = 100
                        self.write(HamsterS.NOTE, pitch)
                        Runner.wait(timeout - tail)
                        self.write(HamsterS.NOTE, HamsterS.NOTE_OFF)
                        if tail > 0:
                            Runner.wait(tail)
                else:
                    self.write(HamsterS.NOTE, HamsterS.NOTE_OFF)
            elif pitch >= 0:
                self.write(HamsterS.NOTE, pitch)

    def _evaluate_sound(self):
        return self.e(HamsterS.SOUND_STATE) and self.read(HamsterS.SOUND_STATE) == 0

    def sound(self, sound, repeat=1):
        self.write(HamsterS.BUZZER, 0)
        self.write(HamsterS.NOTE, HamsterS.NOTE_OFF)
        if isinstance(sound, str):
            tmp = sound.lower()
            if tmp in HamsterS._SOUNDS:
                sound = HamsterS._SOUNDS[tmp]
        if isinstance(sound, (int, float)) and isinstance(repeat, (int, float)):
            sound = int(sound)
            repeat = int(repeat)
            if sound > 0 and repeat != 0:
                self._roboid._run_sound(sound, repeat)
            else:
                self._roboid._cancel_sound()

    def sound_until_done(self, sound, repeat=1):
        self.write(HamsterS.BUZZER, 0)
        self.write(HamsterS.NOTE, HamsterS.NOTE_OFF)
        if isinstance(sound, str):
            tmp = sound.lower()
            if tmp in HamsterS._SOUNDS:
                sound = HamsterS._SOUNDS[tmp]
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

    def io_mode_a(self, mode):
        if isinstance(mode, (int, float)):
            self.write(HamsterS.IO_MODE_A, int(mode))
        elif isinstance(mode, str):
            tmp = mode.lower()
            if tmp in HamsterS._IO_MODES:
                self.write(HamsterS.IO_MODE_A, HamsterS._IO_MODES[tmp])

    def io_mode_b(self, mode):
        if isinstance(mode, (int, float)):
            self.write(HamsterS.IO_MODE_B, int(mode))
        elif isinstance(mode, str):
            tmp = mode.lower()
            if tmp in HamsterS._IO_MODES:
                self.write(HamsterS.IO_MODE_B, HamsterS._IO_MODES[tmp])

    def output_a(self, value):
        if isinstance(value, (int, float)):
            self.write(HamsterS.OUTPUT_A, Util.round(value))

    def output_b(self, value):
        if isinstance(value, (int, float)):
            self.write(HamsterS.OUTPUT_B, Util.round(value))

    def open_gripper(self):
        self.write(HamsterS.IO_MODE_A, HamsterS.IO_MODE_DIGITAL_OUTPUT)
        self.write(HamsterS.IO_MODE_B, HamsterS.IO_MODE_DIGITAL_OUTPUT)
        self.write(HamsterS.OUTPUT_A, 1)
        self.write(HamsterS.OUTPUT_B, 0)
        Runner.wait(500)

    def close_gripper(self):
        self.write(HamsterS.IO_MODE_A, HamsterS.IO_MODE_DIGITAL_OUTPUT)
        self.write(HamsterS.IO_MODE_B, HamsterS.IO_MODE_DIGITAL_OUTPUT)
        self.write(HamsterS.OUTPUT_A, 0)
        self.write(HamsterS.OUTPUT_B, 1)
        Runner.wait(500)

    def release_gripper(self):
        self.write(HamsterS.IO_MODE_A, HamsterS.IO_MODE_DIGITAL_OUTPUT)
        self.write(HamsterS.IO_MODE_B, HamsterS.IO_MODE_DIGITAL_OUTPUT)
        self.write(HamsterS.OUTPUT_A, 0)
        self.write(HamsterS.OUTPUT_B, 0)

    def _evaluate_write_serial(self, id):
        return self._roboid._is_serial_written(id)

    def write_serial(self, text):
        self.write(HamsterS.IO_MODE_A, self._serial_baud)
        self.write(HamsterS.IO_MODE_B, self._serial_baud)
        if isinstance(text, str):
            id = self._roboid._write_serial(text, False)
            if id >= 0:
                Runner.wait_until(self._evaluate_write_serial, id)

    def write_serial_line(self, text):
        self.write(HamsterS.IO_MODE_A, self._serial_baud)
        self.write(HamsterS.IO_MODE_B, self._serial_baud)
        if isinstance(text, str):
            id = self._roboid._write_serial(text, True)
            if id >= 0:
                Runner.wait_until(self._evaluate_write_serial, id)

    def _evaluate_read_serial(self, delimiter):
        serial_input = self._roboid._read_serial(delimiter)
        if serial_input is None: return False
        self._serial_input = serial_input
        return True

    def read_serial(self, delimiter=None):
        self.write(HamsterS.IO_MODE_A, self._serial_baud)
        self.write(HamsterS.IO_MODE_B, self._serial_baud)
        deli = 0
        if isinstance(delimiter, str):
            if delimiter in HamsterS._SERIAL_DELIMITERS:
                deli = HamsterS._SERIAL_DELIMITERS[delimiter]
        Runner.wait_until(self._evaluate_read_serial, deli)
        return self._serial_input

    def serial_rate(self, baud):
        if isinstance(baud, (int, float)):
            baud = int(baud)
            if baud in HamsterS._SERIAL_BAUDS:
                baud = HamsterS._SERIAL_BAUDS[baud]
                self._serial_baud = baud
                self.write(HamsterS.IO_MODE_A, baud)
                self.write(HamsterS.IO_MODE_B, baud)

    def signal_strength(self):
        return self.read(HamsterS.SIGNAL_STRENGTH)

    def left_proximity(self):
        return self.read(HamsterS.LEFT_PROXIMITY)

    def right_proximity(self):
        return self.read(HamsterS.RIGHT_PROXIMITY)

    def left_floor(self):
        return self.read(HamsterS.LEFT_FLOOR)

    def right_floor(self):
        return self.read(HamsterS.RIGHT_FLOOR)

    def acceleration_x(self):
        return self.read(HamsterS.ACCELERATION, 0)

    def acceleration_y(self):
        return self.read(HamsterS.ACCELERATION, 1)

    def acceleration_z(self):
        return self.read(HamsterS.ACCELERATION, 2)

    def light(self):
        return self.read(HamsterS.LIGHT)

    def temperature(self):
        return self.read(HamsterS.TEMPERATURE)

    def input_a(self):
        return self.read(HamsterS.INPUT_A)

    def input_b(self):
        return self.read(HamsterS.INPUT_B)

    def voltage_a(self):
        return round(self.input_a() * 3.6 / 255, 2)

    def voltage_b(self):
        return round(self.input_b() * 3.6 / 255, 2)

    def free_fall(self):
        return self.e(HamsterS.FREE_FALL)

    def tap(self):
        return self.e(HamsterS.TAP)

    def tilt(self):
        return self.read(HamsterS.TILT)

    def pulse_count(self):
        return self.read(HamsterS.PULSE_COUNT)

    def battery_state(self):
        return self.read(HamsterS.BATTERY_STATE)
