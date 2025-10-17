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
import math


class AlbertAiController(object):
    _POSITION_TOLERANCE_FINE = 3
    _POSITION_TOLERANCE_FINE_LARGE = 5
    _POSITION_TOLERANCE_ROUGH = 5
    _POSITION_TOLERANCE_ROUGH_LARGE = 10
    _ORIENTATION_TOLERANCE_FINAL = 0.087
    _ORIENTATION_TOLERANCE_FINAL_LARGE = 0.122
    _ORIENTATION_TOLERANCE_FINAL_LARGE_LARGE = 0.262
    _ORIENTATION_TOLERANCE_ROUGH = 0.122
    _ORIENTATION_TOLERANCE_ROUGH_LARGE = 0.262
    _MINIMUM_WHEEL_SPEED = 18
    _MINIMUM_WHEEL_SPEED_FINE = 15

    _GAIN_ANGLE = 30
    _GAIN_ANGLE_FINE = 30
    _GAIN_POSITION_FINE = 30
    _STRAIGHT_SPEED = 50
    _MAX_BASE_SPEED = 50
    _GAIN_BASE_SPEED = 2
    _GAIN_POSITION = 70

    def __init__(self):
        self._wheel = [0, 0]
        self._prev_direction = 0
        self._prev_direction_final = 0
        self._direction_count_final = 0
        self._position_count = 0
        self._position_count_final = 0
        self._backward = False

    def clear(self):
        self._prev_direction = 0
        self._prev_direction_final = 0
        self._direction_count_final = 0
        self._position_count = 0
        self._position_count_final = 0
    
    def set_backward(self, backward):
        self._backward = backward
    
    def check_position_initial(self, dx, dy):
        return math.sqrt(dx * dx + dy * dy) < AlbertAiController._POSITION_TOLERANCE_ROUGH_LARGE
    
    def control_angle_initial(self, current_radian, target_radian):
        if self._backward:
            current_radian += math.pi
        diff = self._validate_radian(target_radian - current_radian)
        mag = abs(diff)
        if mag < AlbertAiController._ORIENTATION_TOLERANCE_ROUGH:
            return None
        direction = 1 if diff > 0 else -1
        if mag < AlbertAiController._ORIENTATION_TOLERANCE_ROUGH_LARGE and direction * self._prev_direction < 0:
            return None
        self._prev_direction = direction
        
        value = 0
        if diff > 0:
            value = math.log(1 + mag) * AlbertAiController._GAIN_ANGLE
            if value < AlbertAiController._MINIMUM_WHEEL_SPEED:
                value = AlbertAiController._MINIMUM_WHEEL_SPEED
        else:
            value = -math.log(1 + mag) * AlbertAiController._GAIN_ANGLE
            if value > -AlbertAiController._MINIMUM_WHEEL_SPEED:
                value = -AlbertAiController._MINIMUM_WHEEL_SPEED
        
        self._wheel[0] = -int(value)
        self._wheel[1] = int(value)
        return self._wheel
    
    def control_angle_final(self, current_radian, target_radian):
        diff = self._validate_radian(target_radian - current_radian)
        mag = abs(diff)
        if mag < AlbertAiController._ORIENTATION_TOLERANCE_FINAL:
            return None
        direction = 1 if diff > 0 else -1
        if mag < AlbertAiController._ORIENTATION_TOLERANCE_FINAL_LARGE and direction * self._prev_direction_final < 0:
            return None
        if mag < AlbertAiController._ORIENTATION_TOLERANCE_FINAL_LARGE_LARGE and direction * self._prev_direction_final < 0:
            self._direction_count_final += 1
            if self._direction_count_final > 3:
                return None
        self._prev_direction_final = direction
        
        value = 0
        if diff > 0:
            value = math.log(1 + mag) * AlbertAiController._GAIN_ANGLE_FINE
            if value < AlbertAiController._MINIMUM_WHEEL_SPEED:
                value = AlbertAiController._MINIMUM_WHEEL_SPEED
        else:
            value = -math.log(1 + mag) * AlbertAiController._GAIN_ANGLE_FINE
            if value > -AlbertAiController._MINIMUM_WHEEL_SPEED:
                value = -AlbertAiController._MINIMUM_WHEEL_SPEED
        self._wheel[0] = -int(value)
        self._wheel[1] = int(value)
        return self._wheel
    
    def control_position_fine(self, current_x, current_y, current_radian, target_x, target_y):
        target_radian = -math.atan2(target_y - current_y, target_x - current_x)
        if self._backward:
            current_radian += math.pi
        diff = self._validate_radian(target_radian - current_radian)
        mag = abs(diff)
        ex = target_x - current_x
        ey = target_y - current_y
        dist = math.sqrt(ex * ex + ey * ey)
        if dist < AlbertAiController._POSITION_TOLERANCE_FINE:
            return None
        if dist < AlbertAiController._POSITION_TOLERANCE_FINE_LARGE:
            self._position_count_final += 1
            if self._position_count_final > 5:
                self._position_count_final = 0
                return None
        
        value = 0
        if diff > 0:
            value = math.log(1 + mag) * AlbertAiController._GAIN_POSITION_FINE
        else:
            value = -math.log(1 + mag) * AlbertAiController._GAIN_POSITION_FINE
        if self._backward:
            value = -value
        self._wheel[0] = AlbertAiController._MINIMUM_WHEEL_SPEED_FINE - int(value)
        self._wheel[1] = AlbertAiController._MINIMUM_WHEEL_SPEED_FINE + int(value)
        if self._backward:
            self._wheel[0] = -self._wheel[0]
            self._wheel[1] = -self._wheel[1]
        return self._wheel
    
    def control_position(self, current_x, current_y, current_radian, target_x, target_y):
        target_radian = -math.atan2(target_y - current_y, target_x - current_x)
        if self._backward:
            current_radian += math.pi
        diff = self._validate_radian(target_radian - current_radian)
        mag = abs(diff)
        ex = target_x - current_x
        ey = target_y - current_y
        dist = math.sqrt(ex * ex + ey * ey)
        if dist < AlbertAiController._POSITION_TOLERANCE_ROUGH:
            return None
        if dist < AlbertAiController._POSITION_TOLERANCE_ROUGH_LARGE:
            self._position_count += 1
            if self._position_count > 10:
                self._position_count = 0
                return None
        else:
            self._position_count = 0
        
        if mag < 0.01:
            self._wheel[0] = AlbertAiController._STRAIGHT_SPEED
            self._wheel[1] = AlbertAiController._STRAIGHT_SPEED
        else:
            base = (AlbertAiController._MINIMUM_WHEEL_SPEED + 0.5 / mag) * AlbertAiController._GAIN_BASE_SPEED
            if base > AlbertAiController._MAX_BASE_SPEED:
                base = AlbertAiController._MAX_BASE_SPEED
            value = 0
            if diff > 0:
                value = math.log(1 + mag) * AlbertAiController._GAIN_POSITION
            else:
                value = -math.log(1 + mag) * AlbertAiController._GAIN_POSITION
            if self._backward:
                value = -value
            self._wheel[0] = int(base - value)
            self._wheel[1] = int(base + value)
        if self._backward:
            self._wheel[0] = -self._wheel[0]
            self._wheel[1] = -self._wheel[1]
        return self._wheel
    
    def _validate_radian(self, radian):
        while radian > math.pi: radian -= 2 * math.pi
        while radian < -math.pi: radian += 2 * math.pi
        return radian


class AlbertAiNavigator(object):
    def __init__(self, robot):
        self._robot = robot
        self._controller = AlbertAiController()

        self._mode = 0
        self._state = 0
        self._initialized = False
        self._current_x = -1
        self._current_y = -1
        self._current_theta = -200
        self._target_x = -1
        self._target_y = -1
        self._target_theta = -200

    def _set_wheels(self, left_velocity, right_velocity):
        self._robot.write(AlbertAi.LEFT_WHEEL, left_velocity)
        self._robot.write(AlbertAi.RIGHT_WHEEL, right_velocity)

    def _set_both_wheels(self, velocity):
        self._robot.write(AlbertAi.LEFT_WHEEL, velocity[0])
        self._robot.write(AlbertAi.RIGHT_WHEEL, velocity[1])

    def clear(self):
        self._mode = 0
        self._state = 0
        self._initialized = False
        self._current_x = -1
        self._current_y = -1
        self._current_theta = -200
        self._target_x = -1
        self._target_y = -1
        self._target_theta = -200
        self._controller.clear()

    def cancel(self):
        self.clear()
        self._set_wheels(0, 0)

    def set_backward(self, backward):
        self._controller.set_backward(backward)

    def move_to(self, x, y):
        self.clear()
        self._target_x = x
        self._target_y = y
        self._state = 1
        self._mode = 1

    def turn_to(self, deg):
        self.clear()
        self._target_theta = deg
        self._state = 1
        self._mode = 2

    def run(self):
        robot = self._robot
        if self._mode == 1:
            x = robot.read(AlbertAi.POSITION, 0)
            y = robot.read(AlbertAi.POSITION, 1)
            if x >= 0: self._current_x = x
            if y >= 0: self._current_y = y
            self._current_theta = robot.read(AlbertAi.ORIENTATION)
            if self._state == 1:
                if self._initialized == False:
                    if self._current_x < 0 or self._current_y < 0:
                        self._set_wheels(20, -20)
                    else:
                        self._initialized = True
                if self._initialized:
                    current_radian = math.radians(self._current_theta)
                    dx = self._target_x - self._current_x
                    dy = self._target_y - self._current_y
                    if self._controller.check_position_initial(dx, dy):
                        self.clear()
                        self._set_wheels(0, 0)
                        return True
                    else:
                        target_radian = -math.atan2(dy, dx)
                        velocity = self._controller.control_angle_initial(current_radian, target_radian)
                        if velocity is None:
                            self._state = 2
                        else:
                            self._set_both_wheels(velocity)
            elif self._state == 2:
                current_radian = math.radians(self._current_theta)
                velocity = self._controller.control_position(self._current_x, self._current_y, current_radian, self._target_x, self._target_y)
                if velocity is None:
                    self._state = 3
                else:
                    self._set_both_wheels(velocity)
            elif self._state == 3:
                current_radian = math.radians(self._current_theta)
                velocity = self._controller.control_position_fine(self._current_x, self._current_y, current_radian, self._target_x, self._target_y)
                if velocity is None:
                    self.clear()
                    self._set_wheels(0, 0)
                    return True
                else:
                    self._set_both_wheels(velocity)
        elif self._mode == 2:
            self._current_theta = robot.read(AlbertAi.ORIENTATION)
            if self._state == 1:
                current_radian = math.radians(self._current_theta)
                target_radian = math.radians(self._target_theta)
                velocity = self._controller.control_angle_initial(current_radian, target_radian)
                if velocity is None:
                    self._state = 2
                else:
                    self._set_both_wheels(velocity)
            elif self._state == 2:
                current_radian = math.radians(self._current_theta)
                target_radian = math.radians(self._target_theta)
                velocity = self._controller.control_angle_final(current_radian, target_radian)
                if velocity is None:
                    self.clear()
                    self._set_wheels(0, 0)
                    return True
                else:
                    self._set_both_wheels(velocity)
        return False


class AlbertAi(Robot):
    ID = "kr.robomation.physical.albert.ai"

    SPEAKER = 0x00a00000
    VOLUME = 0x00a00001
    LIP = 0x00a00002
    LEFT_WHEEL = 0x00a00003
    RIGHT_WHEEL = 0x00a00004
    LEFT_EYE = 0x00a00005
    RIGHT_EYE = 0x00a00006
    MIC_LED = 0x00a00007
    BUZZER = 0x00a00008
    PULSE = 0x00a00009
    NOTE = 0x00a0000a
    SOUND = 0x00a0000b
    BOARD_SIZE = 0x00a0000c

    SIGNAL_STRENGTH = 0x00a0000e
    LEFT_PROXIMITY = 0x00a0000f
    RIGHT_PROXIMITY = 0x00a00010
    ACCELERATION = 0x00a00011
    POSITION = 0x00a00012
    ORIENTATION = 0x00a00013
    LIGHT = 0x00a00014
    BATTERY = 0x00a00015
    MIC_TOUCH = 0x00a00016
    VOLUME_UP_TOUCH = 0x00a00017
    VOLUME_DOWN_TOUCH = 0x00a00018
    PLAY_TOUCH = 0x00a00019
    BACK_TOUCH = 0x00a0001a
    MIC_CLICKED = 0x00a0001b
    VOLUME_UP_CLICKED = 0x00a0001c
    VOLUME_DOWN_CLICKED = 0x00a0001d
    PLAY_CLICKED = 0x00a0001e
    BACK_CLICKED = 0x00a0001f
    MIC_LONG_PRESSED = 0x00a00020
    VOLUME_UP_LONG_PRESSED = 0x00a00021
    VOLUME_DOWN_LONG_PRESSED = 0x00a00022
    PLAY_LONG_PRESSED = 0x00a00023
    BACK_LONG_PRESSED = 0x00a00024
    MIC_LONG_LONG_PRESSED = 0x00a00025
    VOLUME_UP_LONG_LONG_PRESSED = 0x00a00026
    VOLUME_DOWN_LONG_LONG_PRESSED = 0x00a00027
    PLAY_LONG_LONG_PRESSED = 0x00a00028
    BACK_LONG_LONG_PRESSED = 0x00a00029
    TAP = 0x00a0002a
    OID_MODE = 0x00a0002b
    OID = 0x00a0002c
    LIFT = 0x00a0002d
    PULSE_COUNT = 0x00a0002e
    WHEEL_STATE = 0x00a0002f
    SOUND_STATE = 0x00a00030
    BATTERY_STATE = 0x00a00031
    TILT = 0x00a00032

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
    SOUND_ROBOT = 5

    SOUND_NAME_OFF = "off"
    SOUND_NAME_BEEP = "beep"
    SOUND_NAME_RANDOM_BEEP = "random beep"
    SOUND_NAME_NOISE = "noise"
    SOUND_NAME_SIREN = "siren"
    SOUND_NAME_ENGINE = "engine"
    SOUND_NAME_ROBOT = "robot"

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
        "noise": 10,
        "siren": 3,
        "engine": 4,
        "robot": 5
    }
    DEG_TO_PULSE = 970 / 360.0
    CM_TO_PULSE = 41.7
    _robots = {}

    def __init__(self, index=0, port_name=None):
        if isinstance(index, str):
            index = 0
            port_name = index
        if index in AlbertAi._robots:
            robot = AlbertAi._robots[index]
            if robot: robot.dispose()
        AlbertAi._robots[index] = self
        super(AlbertAi, self).__init__(AlbertAi.ID, "AlbertAi", index)
        self._bpm = 60
        self._navigator = None
        self._init(port_name)

    def dispose(self):
        AlbertAi._robots[self.get_index()] = None
        self._roboid._dispose()
        Runner.unregister_robot(self)

    def reset(self):
        self._bpm = 60
        if self._navigator is not None: self._navigator.cancel()
        self._roboid._reset()

    def _init(self, port_name):
        from roboid.albert_ai_roboid import AlbertAiRoboid
        self._roboid = AlbertAiRoboid(self.get_index())
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
            return Util.round(cm * AlbertAi.CM_TO_PULSE)
        else:
            return 0

    def calc_turn_pulse(self, degree):
        if isinstance(degree, (int, float)):
            return Util.round(degree * AlbertAi.DEG_TO_PULSE)
        else:
            return 0

    def calc_pivot_pulse(self, degree):
        if isinstance(degree, (int, float)):
            return Util.round(degree * AlbertAi.DEG_TO_PULSE * 2)
        else:
            return 0

    def wheels(self, left_velocity, right_velocity=None):
        self.write(AlbertAi.PULSE, 0)
        if isinstance(left_velocity, (int, float)):
            self.write(AlbertAi.LEFT_WHEEL, left_velocity)
        if isinstance(right_velocity, (int, float)):
            self.write(AlbertAi.RIGHT_WHEEL, right_velocity)
        else:
            if isinstance(left_velocity, (int, float)):
                self.write(AlbertAi.RIGHT_WHEEL, left_velocity)

    def left_wheel(self, velocity):
        self.write(AlbertAi.PULSE, 0)
        if isinstance(velocity, (int, float)):
            self.write(AlbertAi.LEFT_WHEEL, velocity)

    def right_wheel(self, velocity):
        self.write(AlbertAi.PULSE, 0)
        if isinstance(velocity, (int, float)):
            self.write(AlbertAi.RIGHT_WHEEL, velocity)

    def stop(self):
        self.write(AlbertAi.PULSE, 0)
        self.write(AlbertAi.LEFT_WHEEL, 0)
        self.write(AlbertAi.RIGHT_WHEEL, 0)

    def _evaluate_wheel_state(self):
        return self.e(AlbertAi.WHEEL_STATE) and self.read(AlbertAi.WHEEL_STATE) == 2

    def _motion(self, pulse, left_velocity, right_velocity):
        if pulse > 0:
            self.write(AlbertAi.LEFT_WHEEL, left_velocity)
            self.write(AlbertAi.RIGHT_WHEEL, right_velocity)
            self.write(AlbertAi.PULSE, pulse)
            Runner.wait_until(self._evaluate_wheel_state)
            self.write(AlbertAi.LEFT_WHEEL, 0)
            self.write(AlbertAi.RIGHT_WHEEL, 0)
        else:
            self.write(AlbertAi.LEFT_WHEEL, 0)
            self.write(AlbertAi.RIGHT_WHEEL, 0)
            self.write(AlbertAi.PULSE, 0)

    def move_forward(self, cm=5, velocity=50):
        if isinstance(cm, (int, float)) and isinstance(velocity, (int, float)):
            if cm < 0:
                cm = -cm
                velocity = -velocity
            self._motion(self.cm_to_pulse(cm), velocity, velocity)

    def move_backward(self, cm=5, velocity=50):
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
        self.write(AlbertAi.PULSE, 0)
        if sec < 0:
            sec = -sec
            left_velocity = -left_velocity
            right_velocity = -right_velocity
        if sec > 0:
            self.write(AlbertAi.LEFT_WHEEL, left_velocity)
            self.write(AlbertAi.RIGHT_WHEEL, right_velocity)
            Runner.wait(sec * 1000)
        self.write(AlbertAi.LEFT_WHEEL, 0)
        self.write(AlbertAi.RIGHT_WHEEL, 0)

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

    def board_size(self, width, height):
        if isinstance(width, (int, float)) and isinstance(height, (int, float)):
            width = int(width)
            height = int(height)
            if width < 0: width = 0
            if height < 0: height = 0
            self.write(AlbertAi.BOARD_SIZE, 0, width)
            self.write(AlbertAi.BOARD_SIZE, 1, height)

    def _get_navigator(self):
        if self._navigator is None:
            self._navigator = AlbertAiNavigator(self)
        return self._navigator

    def _evaluate_board(self):
        return self._get_navigator().run()

    def _board_to(self, x, y, backward):
        self.write(AlbertAi.LEFT_WHEEL, 0)
        self.write(AlbertAi.RIGHT_WHEEL, 0)
        self.write(AlbertAi.PULSE, 0)

        if x >= 0 and y >= 0:
            navigator = self._get_navigator()
            navigator.set_backward(backward)
            navigator.move_to(x, y)
            Runner.wait_until(self._evaluate_board)

    def board_forward(self, x, y):
        self._board_to(x, y, False)

    def board_backward(self, x, y):
        self._board_to(x, y, True)

    def board_direction(self, degree):
        self.write(AlbertAi.LEFT_WHEEL, 0)
        self.write(AlbertAi.RIGHT_WHEEL, 0)
        self.write(AlbertAi.PULSE, 0)

        navigator = self._get_navigator()
        navigator.set_backward(False)
        navigator.turn_to(degree)
        Runner.wait_until(self._evaluate_board)

    def eyes(self, color1, color2=None, color3=None, color4=None, color5=None, color6=None):
        if isinstance(color1, (int, float)):
            color1 = Util.round(color1)
            if isinstance(color2, (int, float)):
                color2 = Util.round(color2)
                if isinstance(color3, (int, float)):
                    color3 = Util.round(color3)
                    self.write(AlbertAi.LEFT_EYE, 0, color1)
                    self.write(AlbertAi.LEFT_EYE, 1, color2)
                    self.write(AlbertAi.LEFT_EYE, 2, color3)
                    if isinstance(color4, (int, float)) and isinstance(color5, (int, float)) and isinstance(color6, (int, float)):
                        color4 = Util.round(color4)
                        color5 = Util.round(color5)
                        color6 = Util.round(color6)
                        self.write(AlbertAi.RIGHT_EYE, 0, color4)
                        self.write(AlbertAi.RIGHT_EYE, 1, color5)
                        self.write(AlbertAi.RIGHT_EYE, 2, color6)
                    else:
                        self.write(AlbertAi.RIGHT_EYE, 0, color1)
                        self.write(AlbertAi.RIGHT_EYE, 1, color2)
                        self.write(AlbertAi.RIGHT_EYE, 2, color3)
                else:
                    self.write(AlbertAi.LEFT_EYE, 0, color1)
                    self.write(AlbertAi.LEFT_EYE, 1, color1)
                    self.write(AlbertAi.LEFT_EYE, 2, color1)
                    self.write(AlbertAi.RIGHT_EYE, 0, color2)
                    self.write(AlbertAi.RIGHT_EYE, 1, color2)
                    self.write(AlbertAi.RIGHT_EYE, 2, color2)
            else:
                self.write(AlbertAi.LEFT_EYE, 0, color1)
                self.write(AlbertAi.LEFT_EYE, 1, color1)
                self.write(AlbertAi.LEFT_EYE, 2, color1)
                self.write(AlbertAi.RIGHT_EYE, 0, color1)
                self.write(AlbertAi.RIGHT_EYE, 1, color1)
                self.write(AlbertAi.RIGHT_EYE, 2, color1)
        elif isinstance(color1, str):
            color1 = color1.lower()
            if color1 in AlbertAi._COLOR2RGB:
                self.write(AlbertAi.LEFT_EYE, AlbertAi._COLOR2RGB[color1])
            if isinstance(color2, str):
                color2 = color2.lower()
                if color2 in AlbertAi._COLOR2RGB:
                    self.write(AlbertAi.RIGHT_EYE, AlbertAi._COLOR2RGB[color2])
            elif color1 in AlbertAi._COLOR2RGB:
                self.write(AlbertAi.RIGHT_EYE, AlbertAi._COLOR2RGB[color1])
        elif isinstance(color1, (list, tuple)):
            if len(color1) >= 3 and isinstance(color1[0], (int, float)) and isinstance(color1[1], (int, float)) and isinstance(color1[2], (int, float)):
                r = Util.round(color1[0])
                g = Util.round(color1[1])
                b = Util.round(color1[2])
                self.write(AlbertAi.LEFT_EYE, 0, r)
                self.write(AlbertAi.LEFT_EYE, 1, g)
                self.write(AlbertAi.LEFT_EYE, 2, b)
                if isinstance(color2, (list, tuple)):
                    if len(color2) >= 3 and isinstance(color2[0], (int, float)) and isinstance(color2[1], (int, float)) and isinstance(color2[2], (int, float)):
                        self.write(AlbertAi.RIGHT_EYE, 0, Util.round(color2[0]))
                        self.write(AlbertAi.RIGHT_EYE, 1, Util.round(color2[1]))
                        self.write(AlbertAi.RIGHT_EYE, 2, Util.round(color2[2]))
                else:
                    self.write(AlbertAi.RIGHT_EYE, 0, r)
                    self.write(AlbertAi.RIGHT_EYE, 1, g)
                    self.write(AlbertAi.RIGHT_EYE, 2, b)

    def left_eye(self, color1, color2=None, color3=None):
        if isinstance(color1, (int, float)):
            color1 = Util.round(color1)
            if isinstance(color2, (int, float)) and isinstance(color3, (int, float)):
                color2 = Util.round(color2)
                color3 = Util.round(color3)
                self.write(AlbertAi.LEFT_EYE, 0, color1)
                self.write(AlbertAi.LEFT_EYE, 1, color2)
                self.write(AlbertAi.LEFT_EYE, 2, color3)
            else:
                self.write(AlbertAi.LEFT_EYE, 0, color1)
                self.write(AlbertAi.LEFT_EYE, 1, color1)
                self.write(AlbertAi.LEFT_EYE, 2, color1)
        elif isinstance(color1, str):
            tmp = color1.lower()
            if tmp in AlbertAi._COLOR2RGB:
                self.write(AlbertAi.LEFT_EYE, AlbertAi._COLOR2RGB[tmp])
        elif isinstance(color1, (list, tuple)):
            if len(color1) >= 3 and isinstance(color1[0], (int, float)) and isinstance(color1[1], (int, float)) and isinstance(color1[2], (int, float)):
                self.write(AlbertAi.LEFT_EYE, 0, Util.round(color1[0]))
                self.write(AlbertAi.LEFT_EYE, 1, Util.round(color1[1]))
                self.write(AlbertAi.LEFT_EYE, 2, Util.round(color1[2]))

    def right_eye(self, color1, color2=None, color3=None):
        if isinstance(color1, (int, float)):
            color1 = Util.round(color1)
            if isinstance(color2, (int, float)) and isinstance(color3, (int, float)):
                color2 = Util.round(color2)
                color3 = Util.round(color3)
                self.write(AlbertAi.RIGHT_EYE, 0, color1)
                self.write(AlbertAi.RIGHT_EYE, 1, color2)
                self.write(AlbertAi.RIGHT_EYE, 2, color3)
            else:
                self.write(AlbertAi.RIGHT_EYE, 0, color1)
                self.write(AlbertAi.RIGHT_EYE, 1, color1)
                self.write(AlbertAi.RIGHT_EYE, 2, color1)
        elif isinstance(color1, str):
            tmp = color1.lower()
            if tmp in AlbertAi._COLOR2RGB:
                self.write(AlbertAi.RIGHT_EYE, AlbertAi._COLOR2RGB[tmp])
        elif isinstance(color1, (list, tuple)):
            if len(color1) >= 3 and isinstance(color1[0], (int, float)) and isinstance(color1[1], (int, float)) and isinstance(color1[2], (int, float)):
                self.write(AlbertAi.RIGHT_EYE, 0, Util.round(color1[0]))
                self.write(AlbertAi.RIGHT_EYE, 1, Util.round(color1[1]))
                self.write(AlbertAi.RIGHT_EYE, 2, Util.round(color1[2]))

    def buzzer(self, hz):
        self.write(AlbertAi.NOTE, AlbertAi.NOTE_OFF)
        self._roboid._cancel_sound()
        if isinstance(hz, (int, float)):
            self.write(AlbertAi.BUZZER, hz)

    def tempo(self, bpm):
        if isinstance(bpm, (int, float)):
            if bpm > 0:
                self._bpm = bpm

    def note(self, pitch, beats=None):
        self.write(AlbertAi.BUZZER, 0)
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
                if tmp in AlbertAi._NOTES:
                    pitch = AlbertAi._NOTES[tmp] + (octave - 1) * 12
        if isinstance(pitch, (int, float)):
            pitch = int(pitch)
            if isinstance(beats, (int, float)):
                bpm = self._bpm
                if beats > 0 and bpm > 0:
                    if pitch == 0:
                        self.write(AlbertAi.NOTE, AlbertAi.NOTE_OFF)
                        Runner.wait(beats * 60 * 1000.0 / bpm)
                    elif pitch > 0:
                        timeout = beats * 60 * 1000.0 / bpm
                        tail = 0
                        if timeout > 100:
                            tail = 100
                        self.write(AlbertAi.NOTE, pitch)
                        Runner.wait(timeout - tail)
                        self.write(AlbertAi.NOTE, AlbertAi.NOTE_OFF)
                        if tail > 0:
                            Runner.wait(tail)
                else:
                    self.write(AlbertAi.NOTE, AlbertAi.NOTE_OFF)
            elif pitch >= 0:
                self.write(AlbertAi.NOTE, pitch)

    def _evaluate_sound(self):
        return self.e(AlbertAi.SOUND_STATE) and self.read(AlbertAi.SOUND_STATE) == 0

    def sound(self, sound, repeat=1):
        self.write(AlbertAi.BUZZER, 0)
        self.write(AlbertAi.NOTE, AlbertAi.NOTE_OFF)
        if isinstance(sound, str):
            tmp = sound.lower()
            if tmp in AlbertAi._SOUNDS:
                sound = AlbertAi._SOUNDS[tmp]
        if isinstance(sound, (int, float)) and isinstance(repeat, (int, float)):
            sound = int(sound)
            repeat = int(repeat)
            if sound > 0 and repeat != 0:
                self._roboid._run_sound(sound, repeat)
            else:
                self._roboid._cancel_sound()

    def sound_until_done(self, sound, repeat=1):
        self.write(AlbertAi.BUZZER, 0)
        self.write(AlbertAi.NOTE, AlbertAi.NOTE_OFF)
        if isinstance(sound, str):
            tmp = sound.lower()
            if tmp in AlbertAi._SOUNDS:
                sound = AlbertAi._SOUNDS[tmp]
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
        return self.read(AlbertAi.SIGNAL_STRENGTH)

    def left_proximity(self):
        return self.read(AlbertAi.LEFT_PROXIMITY)

    def right_proximity(self):
        return self.read(AlbertAi.RIGHT_PROXIMITY)

    def acceleration_x(self):
        return self.read(AlbertAi.ACCELERATION, 0)

    def acceleration_y(self):
        return self.read(AlbertAi.ACCELERATION, 1)

    def acceleration_z(self):
        return self.read(AlbertAi.ACCELERATION, 2)

    def position_x(self):
        return self.read(AlbertAi.POSITION, 0)

    def position_y(self):
        return self.read(AlbertAi.POSITION, 1)

    def orientation(self):
        return self.read(AlbertAi.ORIENTATION)

    def light(self):
        return self.read(AlbertAi.LIGHT)

    def mic_touch(self):
        return self.read(AlbertAi.MIC_TOUCH)

    def volume_up_touch(self):
        return self.read(AlbertAi.VOLUME_UP_TOUCH)

    def volume_down_touch(self):
        return self.read(AlbertAi.VOLUME_DOWN_TOUCH)

    def play_touch(self):
        return self.read(AlbertAi.PLAY_TOUCH)

    def back_touch(self):
        return self.read(AlbertAi.BACK_TOUCH)

    def mic_clicked(self):
        return self.e(AlbertAi.MIC_CLICKED)

    def volume_up_clicked(self):
        return self.e(AlbertAi.VOLUME_UP_CLICKED)

    def volume_down_clicked(self):
        return self.e(AlbertAi.VOLUME_DOWN_CLICKED)

    def play_clicked(self):
        return self.e(AlbertAi.PLAY_CLICKED)

    def back_clicked(self):
        return self.e(AlbertAi.BACK_CLICKED)

    def mic_long_pressed(self):
        return self.e(AlbertAi.MIC_LONG_PRESSED)

    def volume_up_long_pressed(self):
        return self.e(AlbertAi.VOLUME_UP_LONG_PRESSED)

    def volume_down_long_pressed(self):
        return self.e(AlbertAi.VOLUME_DOWN_LONG_PRESSED)

    def play_long_pressed(self):
        return self.e(AlbertAi.PLAY_LONG_PRESSED)

    def back_long_pressed(self):
        return self.e(AlbertAi.BACK_LONG_PRESSED)

    def mic_long_long_pressed(self):
        return self.e(AlbertAi.MIC_LONG_LONG_PRESSED)

    def volume_up_long_long_pressed(self):
        return self.e(AlbertAi.VOLUME_UP_LONG_LONG_PRESSED)

    def volume_down_long_long_pressed(self):
        return self.e(AlbertAi.VOLUME_DOWN_LONG_LONG_PRESSED)

    def play_long_long_pressed(self):
        return self.e(AlbertAi.PLAY_LONG_LONG_PRESSED)

    def back_long_long_pressed(self):
        return self.e(AlbertAi.BACK_LONG_LONG_PRESSED)

    def tap(self):
        return self.e(AlbertAi.TAP)

    def oid_mode(self):
        return self.read(AlbertAi.OID_MODE)

    def oid(self):
        return self.read(AlbertAi.OID)

    def lift(self):
        return self.read(AlbertAi.LIFT)

    def pulse_count(self):
        return self.read(AlbertAi.PULSE_COUNT)

    def battery_state(self):
        return self.read(AlbertAi.BATTERY_STATE)

    def tilt(self):
        return self.read(AlbertAi.TILT)
