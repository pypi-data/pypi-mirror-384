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


class Raccoon(Robot):
    ID = "kr.robomation.physical.raccoon"

    JOINT_VELOCITY = 0x03000000
    JOINT_SPEED = 0x03000001
    JOINT_ANGLE = 0x03000002
    NOTE = 0x03000003
    SOUND = 0x03000004
    JOINT_MODE = 0x03000005
    WRITE_EXT = 0x03000006

    SIGNAL_STRENGTH = 0x03000010
    ENCODER = 0x03000011
    TEACH_BUTTON = 0x03000012
    PLAYBACK_BUTTON = 0x03000013
    DELETE_BUTTON = 0x03000014
    TEACH_CLICKED = 0x03000015
    PLAYBACK_CLICKED = 0x03000016
    DELETE_CLICKED = 0x03000017
    TEACH_LONG_PRESSED = 0x03000018
    PLAYBACK_LONG_PRESSED = 0x03000019
    DELETE_LONG_PRESSED = 0x0300001a
    WARNING = 0x0300001b
    MOVING = 0x0300001c
    COLLISION_1 = 0x0300001d
    COLLISION_2 = 0x0300001e
    COLLISION_3 = 0x0300001f
    COLLISION_4 = 0x03000020
    JOINT_STATE = 0x03000021
    SOUND_STATE = 0x03000022
    BATTERY_STATE = 0x03000023
    CHARGE_STATE = 0x03000024
    READ_EXT = 0x03000025

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
    SOUND_WAKE_UP = 22
    SOUND_START = 23
    SOUND_BYE = 24
    
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
    SOUND_NAME_WAKE_UP = "wake up"
    SOUND_NAME_START = "start"
    SOUND_NAME_BYE = "bye"

    BATTERY_NORMAL = 2
    BATTERY_LOW = 1
    BATTERY_EMPTY = 0

    JOINT_MODE_VELOCITY = 0
    JOINT_MODE_ANGLE = 1
    JOINT_MODE_VELOCITY_HORZ = 2
    JOINT_MODE_VELOCITY_VERT = 3
    JOINT_MODE_ANGLE_HORZ = 4
    JOINT_MODE_ANGLE_VERT = 5

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
        "dibidibidip": 8,
        "good job": 9,
        "good_job": 9,
        "noise": 10,
        "chop": 11,
        "random melody": 18,
        "random_melody": 18,
        "wake up": 22,
        "wake_up": 22,
        "start": 23,
        "bye": 24
    }
    _L1 = 8.25
    _L2 = 10
    _L3 = 10
    #_L4 = 9.25
    _robots = {}

    def __init__(self, index=0, port_name=None):
        if isinstance(index, str):
            index = 0
            port_name = index
        if index in Raccoon._robots:
            robot = Raccoon._robots[index]
            if robot: robot.dispose()
        Raccoon._robots[index] = self
        super(Raccoon, self).__init__(Raccoon.ID, "Raccoon", index)
        self._joint_mode = Raccoon.JOINT_MODE_VELOCITY
        self._bpm = 60
        self._ext = [0] * 8
        self._init(port_name)

    def dispose(self):
        Raccoon._robots[self.get_index()] = None
        self._roboid._dispose()
        Runner.unregister_robot(self)

    def reset(self):
        self._joint_mode = Raccoon.JOINT_MODE_VELOCITY
        self._bpm = 60
        self._roboid._reset()

    def _init(self, port_name):
        from roboid.raccoon_roboid import RaccoonRoboid
        self._roboid = RaccoonRoboid(self.get_index())
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

    def _check_joint_mode(self, mode):
        if mode == Raccoon.JOINT_MODE_VELOCITY:
            if self._joint_mode == Raccoon.JOINT_MODE_VELOCITY_HORZ or self._joint_mode == Raccoon.JOINT_MODE_ANGLE_HORZ:
                self._joint_mode = Raccoon.JOINT_MODE_VELOCITY_HORZ
            elif self._joint_mode == Raccoon.JOINT_MODE_VELOCITY_VERT or self._joint_mode == Raccoon.JOINT_MODE_ANGLE_VERT:
                self._joint_mode = Raccoon.JOINT_MODE_VELOCITY_VERT
            else:
                self._joint_mode = Raccoon.JOINT_MODE_VELOCITY
        elif mode == Raccoon.JOINT_MODE_ANGLE:
            if self._joint_mode == Raccoon.JOINT_MODE_ANGLE_HORZ or self._joint_mode == Raccoon.JOINT_MODE_VELOCITY_HORZ:
                self._joint_mode = Raccoon.JOINT_MODE_ANGLE_HORZ
            elif self._joint_mode == Raccoon.JOINT_MODE_ANGLE_VERT or self._joint_mode == Raccoon.JOINT_MODE_VELOCITY_VERT:
                self._joint_mode = Raccoon.JOINT_MODE_ANGLE_VERT
            else:
                self._joint_mode = Raccoon.JOINT_MODE_ANGLE
        return self._joint_mode

    def velocity(self, joint, value, arg3=-9999, arg4=-9999):
        self.write(Raccoon.JOINT_MODE, self._check_joint_mode(Raccoon.JOINT_MODE_VELOCITY))
        if arg3 == -9999: # joint, value
            if isinstance(joint, (int, float)) and isinstance(value, (int, float)):
                joint = int(joint)
                if joint < 0:
                    for idx in range(4):
                        self.write(Raccoon.JOINT_VELOCITY, idx, value)
                elif joint > 0:
                    self.write(Raccoon.JOINT_VELOCITY, joint - 1, value)
        else:
            if isinstance(joint, (int, float)):
                self.write(Raccoon.JOINT_VELOCITY, 0, joint)
            if isinstance(value, (int, float)):
                self.write(Raccoon.JOINT_VELOCITY, 1, value)
            if isinstance(arg3, (int, float)) and arg3 != -9999:
                self.write(Raccoon.JOINT_VELOCITY, 2, arg3)
            if isinstance(arg4, (int, float)) and arg4 != -9999:
                self.write(Raccoon.JOINT_VELOCITY, 3, arg4)

    def _evaluate_joint_state(self):
        return self.e(Raccoon.JOINT_STATE)

    def _release_joints(self):
        self.velocity(-1, 0)

    def _angle_to(self, joint, value, speed=-9999, arg4=-9999, arg5=-9999, wait=True):
        self.write(Raccoon.JOINT_MODE, self._check_joint_mode(Raccoon.JOINT_MODE_ANGLE))
        if arg4 == -9999: # joint, value, speed
            if speed == -9999:
                speed = 100
            if isinstance(joint, (int, float)) and isinstance(value, (int, float)) and isinstance(speed, (int, float)):
                self.write(Raccoon.JOINT_SPEED, Util.round(speed))
                joint = int(joint)
                if joint < 0:
                    for idx in range(4):
                        self.write(Raccoon.JOINT_ANGLE, idx, value)
                    if wait:
                        Runner.wait_until(self._evaluate_joint_state)
                        self._release_joints()
                elif joint > 0:
                    self.write(Raccoon.JOINT_ANGLE, joint - 1, value)
                    if wait:
                        Runner.wait_until(self._evaluate_joint_state)
                        self._release_joints()
        else:
            if arg5 == -9999:
                arg5 = 100 # speed 100
            if isinstance(arg5, (int, float)):
                self.write(Raccoon.JOINT_SPEED, Util.round(arg5))
                if isinstance(joint, (int, float)):
                    self.write(Raccoon.JOINT_ANGLE, 0, joint)
                if isinstance(value, (int, float)):
                    self.write(Raccoon.JOINT_ANGLE, 1, value)
                if isinstance(speed, (int, float)) and speed != -9999:
                    self.write(Raccoon.JOINT_ANGLE, 2, speed)
                if isinstance(arg4, (int, float)) and arg4 != -9999:
                    self.write(Raccoon.JOINT_ANGLE, 3, arg4)
                if wait:
                    Runner.wait_until(self._evaluate_joint_state)
                    self._release_joints()

    def _angle_by(self, joint, value, speed=-9999, arg4=-9999, arg5=-9999, wait=True):
        self.write(Raccoon.JOINT_MODE, self._check_joint_mode(Raccoon.JOINT_MODE_ANGLE))
        if arg4 == -9999: # joint, value, speed
            if speed == -9999:
                speed = 100
            if isinstance(joint, (int, float)) and isinstance(value, (int, float)) and isinstance(speed, (int, float)):
                self.write(Raccoon.JOINT_SPEED, Util.round(speed))
                joint = int(joint)
                if joint < 0:
                    for idx in range(4):
                        self.write(Raccoon.JOINT_ANGLE, idx, self.read(Raccoon.ENCODER, idx) + value)
                    if wait:
                        Runner.wait_until(self._evaluate_joint_state)
                        self._release_joints()
                elif joint > 0:
                    joint -= 1
                    self.write(Raccoon.JOINT_ANGLE, joint, self.read(Raccoon.ENCODER, joint) + value)
                    if wait:
                        Runner.wait_until(self._evaluate_joint_state)
                        self._release_joints()
        else:
            if arg5 == -9999:
                arg5 = 100
            if isinstance(arg5, (int, float)):
                self.write(Raccoon.JOINT_SPEED, Util.round(arg5))
                if isinstance(joint, (int, float)):
                    self.write(Raccoon.JOINT_ANGLE, 0, self.read(Raccoon.ENCODER, 0) + joint)
                if isinstance(value, (int, float)):
                    self.write(Raccoon.JOINT_ANGLE, 1, self.read(Raccoon.ENCODER, 1) + value)
                if isinstance(speed, (int, float)) and speed != -9999:
                    self.write(Raccoon.JOINT_ANGLE, 2, self.read(Raccoon.ENCODER, 2) + speed)
                if isinstance(arg4, (int, float)) and arg4 != -9999:
                    self.write(Raccoon.JOINT_ANGLE, 3, self.read(Raccoon.ENCODER, 3) + arg4)
                if wait:
                    Runner.wait_until(self._evaluate_joint_state)
                    self._release_joints()

    def degree_to(self, joint, value, speed=-9999, arg4=-9999, arg5=-9999):
        self._angle_to(joint, value, speed, arg4, arg5, True)

    #deprecated
    def angle_to(self, joint, value, speed=-9999, arg4=-9999, arg5=-9999):
        self.degree_to(joint, value, speed, arg4, arg5)

    def degree_by(self, joint, value, speed=-9999, arg4=-9999, arg5=-9999):
        self._angle_by(joint, value, speed, arg4, arg5, True)

    #deprecated
    def angle_by(self, joint, value, speed=-9999, arg4=-9999, arg5=-9999):
        self.degree_by(joint, value, speed, arg4, arg5)

    def set_degree(self, joint, value, speed=-9999, arg4=-9999, arg5=-9999):
        self._angle_to(joint, value, speed, arg4, arg5, False)

    #deprecated
    def target_angle(self, joint, value, speed=-9999, arg4=-9999, arg5=-9999):
        self.set_degree(joint, value, speed, arg4, arg5)

    def stop(self):
        self.write(Raccoon.JOINT_MODE, self._check_joint_mode(Raccoon.JOINT_MODE_VELOCITY))
        for idx in range(4):
            self.write(Raccoon.JOINT_VELOCITY, idx, 0)

    def lock_horz(self):
        if self._joint_mode == Raccoon.JOINT_MODE_VELOCITY or self._joint_mode == Raccoon.JOINT_MODE_VELOCITY_HORZ or self._joint_mode == Raccoon.JOINT_MODE_VELOCITY_VERT:
            self._joint_mode = Raccoon.JOINT_MODE_VELOCITY_HORZ
        else:
            self._joint_mode = Raccoon.JOINT_MODE_ANGLE_HORZ
        self.write(Raccoon.JOINT_MODE, self._joint_mode)
        self._angle_by(4, 0)

    def lock_vert(self):
        if self._joint_mode == Raccoon.JOINT_MODE_VELOCITY or self._joint_mode == Raccoon.JOINT_MODE_VELOCITY_HORZ or self._joint_mode == Raccoon.JOINT_MODE_VELOCITY_VERT:
            self._joint_mode = Raccoon.JOINT_MODE_VELOCITY_VERT
        else:
            self._joint_mode = Raccoon.JOINT_MODE_ANGLE_VERT
        self.write(Raccoon.JOINT_MODE, self._joint_mode)
        self._angle_by(4, 0)

    def unlock(self):
        if self._joint_mode == Raccoon.JOINT_MODE_VELOCITY or self._joint_mode == Raccoon.JOINT_MODE_VELOCITY_HORZ or self._joint_mode == Raccoon.JOINT_MODE_VELOCITY_VERT:
            self._joint_mode = Raccoon.JOINT_MODE_VELOCITY
        else:
            self._joint_mode = Raccoon.JOINT_MODE_ANGLE
        self.write(Raccoon.JOINT_MODE, self._joint_mode)

    def open_gripper(self):
        self._ext[0] = 0x21;
        self._ext[1] = 0x00;
        self._ext[2] = 0;
        for i in range(3, 8):
            self._ext[i] = 0;
        self.write(Raccoon.WRITE_EXT, self._ext)
        Runner.wait(500)

    def close_gripper(self):
        self._ext[0] = 0x21;
        self._ext[1] = 0x00;
        self._ext[2] = 1;
        for i in range(3, 8):
            self._ext[i] = 0;
        self.write(Raccoon.WRITE_EXT, self._ext)
        Runner.wait(500)

    def deg_to_xyz(self, deg1, deg2, deg3, deg4, length=0):
        th1 = math.radians(deg1)
        th2 = math.radians(deg2)
        th3 = math.radians(deg3)
        th4 = math.radians(deg4)
        c1 = math.cos(th1)
        s1 = math.sin(th1)
        c4 = math.cos(th4)
        s4 = math.sin(th4)
        c23 = math.cos(th2 + th3)
        s23 = math.sin(th2 + th3)
        M1 = c4 * length + Raccoon._L3
        M2 = s4 * length
        M = s23 * M1 + c23 * M2 + math.sin(th2) * Raccoon._L2
        x = -c1 * M
        y = -s1 * M
        z = c23 * M1 - s23 * M2 + math.cos(th2) * Raccoon._L2 + Raccoon._L1
        return -y, x, z

    def xyz(self, length=0):
        return self.deg_to_xyz(self.read(Raccoon.ENCODER, 0), self.read(Raccoon.ENCODER, 1), self.read(Raccoon.ENCODER, 2), self.read(Raccoon.ENCODER, 3), length)

    #deprecated
    def current_xyz(self, length=0):
        return self.xyz(length)

    def _calc_inv_kinematics(self, x, y, z):
        x, y = y, -x
        th1 = math.atan2(y, x)
        c1 = math.cos(th1)
        s1 = math.sin(th1)
        zL1 = z - Raccoon._L1
        c3 = (x*x + y*y + zL1*zL1 - Raccoon._L2*Raccoon._L2 - Raccoon._L3*Raccoon._L3) / (2 * Raccoon._L2 * Raccoon._L3)
        c32 = c3*c3
        if c32 > 1: c32 = 1
        s3 = -math.sqrt(1 - c32)
        th3 = math.atan2(s3, c3)
        M1 = c3 * Raccoon._L3 + Raccoon._L2
        M2 = z - Raccoon._L1
        M3 = s3 * Raccoon._L3
        M4 = c1*x + s1*y
        c2 = M1*M2 - M3*M4
        s2 = -M2*M3 - M1*M4
        th2 = math.atan2(s2, c2)
        
        th1 = math.degrees(th1)
        th2 = math.degrees(th2)
        th3 = math.degrees(th3)
        return th1, th2, th3

    def xyz_to_deg(self, x, y, z):
        return self._calc_inv_kinematics(x, y, z)

    def can_move_to(self, x, y, z):
        if isinstance(x, (int, float)) and isinstance(y, (int, float)) and isinstance(z, (int, float)):
            th1, th2, th3 = self._calc_inv_kinematics(x, y, z)
            if th1 < -120: return False
            if th1 > 120: return False
            if th2 < -90: return False
            if th2 > 30: return False
            if th3 < -150: return False
            if th3 > 0: return False
            return True
        return False

    def move_to(self, x, y, z, speed=100):
        if isinstance(x, (int, float)) and isinstance(y, (int, float)) and isinstance(z, (int, float)) and isinstance(speed, (int, float)):
            th1, th2, th3 = self._calc_inv_kinematics(x, y, z)
            self._angle_to(th1, th2, th3, None, speed, True)

    def can_move_by(self, dx, dy, dz):
        if isinstance(dx, (int, float)) and isinstance(dy, (int, float)) and isinstance(dz, (int, float)):
            x, y, z = self.xyz()
            return self.can_move_to(x + dx, y + dy, z + dz)
        return False

    def move_by(self, dx, dy, dz, speed=100):
        if isinstance(dx, (int, float)) and isinstance(dy, (int, float)) and isinstance(dz, (int, float)) and isinstance(speed, (int, float)):
            x, y, z = self.xyz()
            self.move_to(x + dx, y + dy, z + dz, speed)

    def tempo(self, bpm):
        if isinstance(bpm, (int, float)):
            if bpm > 0:
                self._bpm = bpm

    def note(self, pitch, beats=None):
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
                if tmp in Raccoon._NOTES:
                    pitch = Raccoon._NOTES[tmp] + (octave - 1) * 12
        if isinstance(pitch, (int, float)):
            pitch = int(pitch)
            if isinstance(beats, (int, float)):
                bpm = self._bpm
                if beats > 0 and bpm > 0:
                    if pitch == 0:
                        self.write(Raccoon.NOTE, Raccoon.NOTE_OFF)
                        Runner.wait(beats * 60 * 1000.0 / bpm)
                    elif pitch > 0:
                        timeout = beats * 60 * 1000.0 / bpm
                        tail = 0
                        if timeout > 100:
                            tail = 100
                        self.write(Raccoon.NOTE, pitch)
                        Runner.wait(timeout - tail)
                        self.write(Raccoon.NOTE, Raccoon.NOTE_OFF)
                        if tail > 0:
                            Runner.wait(tail)
                else:
                    self.write(Raccoon.NOTE, Raccoon.NOTE_OFF)
            elif pitch >= 0:
                self.write(Raccoon.NOTE, pitch)

    def _evaluate_sound(self):
        return self.e(Raccoon.SOUND_STATE)

    def sound(self, sound, repeat=1):
        self.write(Raccoon.NOTE, Raccoon.NOTE_OFF)
        if isinstance(sound, str):
            tmp = sound.lower()
            if tmp in Raccoon._SOUNDS:
                sound = Raccoon._SOUNDS[tmp]
        if isinstance(sound, (int, float)) and isinstance(repeat, (int, float)):
            sound = int(sound)
            repeat = int(repeat)
            if sound > 0 and repeat != 0:
                self._roboid._run_sound(sound, repeat)
            else:
                self._roboid._cancel_sound()

    def sound_until_done(self, sound, repeat=1):
        self.write(Raccoon.NOTE, Raccoon.NOTE_OFF)
        if isinstance(sound, str):
            tmp = sound.lower()
            if tmp in Raccoon._SOUNDS:
                sound = Raccoon._SOUNDS[tmp]
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
        return self.read(Raccoon.SIGNAL_STRENGTH)

    def encoder(self, joint=-1):
        if isinstance(joint, (int, float)):
            joint = int(joint)
            if joint < 0:
                return (self.read(Raccoon.ENCODER, 0), self.read(Raccoon.ENCODER, 1), self.read(Raccoon.ENCODER, 2), self.read(Raccoon.ENCODER, 3))
            elif joint > 0:
                return self.read(Raccoon.ENCODER, joint - 1)
        return 0

    def teach_button(self):
        return self.read(Raccoon.TEACH_BUTTON)

    def playback_button(self):
        return self.read(Raccoon.PLAYBACK_BUTTON)

    def delete_button(self):
        return self.read(Raccoon.DELETE_BUTTON)

    def teach_clicked(self):
        return self.e(Raccoon.TEACH_CLICKED)

    def playback_clicked(self):
        return self.e(Raccoon.PLAYBACK_CLICKED)

    def delete_clicked(self):
        return self.e(Raccoon.DELETE_CLICKED)

    def teach_long_pressed(self):
        return self.e(Raccoon.TEACH_LONG_PRESSED)

    def playback_long_pressed(self):
        return self.e(Raccoon.PLAYBACK_LONG_PRESSED)

    def delete_long_pressed(self):
        return self.e(Raccoon.DELETE_LONG_PRESSED)

    def warning(self):
        return self.read(Raccoon.WARNING)

    def collision(self, joint):
        if isinstance(joint, (int, float)):
            joint = int(joint)
            if joint == 1:
                return self.e(Raccoon.COLLISION_1)
            elif joint == 2:
                return self.e(Raccoon.COLLISION_2)
            elif joint == 3:
                return self.e(Raccoon.COLLISION_3)
            elif joint == 4:
                return self.e(Raccoon.COLLISION_4)
        return False

    def collision_any(self):
        return self.e(Raccoon.COLLISION_1) or self.e(Raccoon.COLLISION_2) or self.e(Raccoon.COLLISION_3) or self.e(Raccoon.COLLISION_4)

    def battery_state(self):
        return self.read(Raccoon.BATTERY_STATE)

    def charge_state(self):
        return self.read(Raccoon.CHARGE_STATE)
