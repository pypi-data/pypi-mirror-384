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

import math

from roboid.runner import Runner
from roboid.util import Util
from roboid.model import Robot


class BeagleLoader(object):
    def __init__(self, roboid):
        self._roboid = roboid

    def load(self, serial, address):
        loaded = False
        count = 0
        while True:
            try:
                packet = self._read(serial)
                if packet is not None:
                    if loaded:
                        if packet[0] == 0x80 and packet[1] == 0x16 and packet[3] == 0xC1:
                            self._parse(packet)
                            self._write(serial, self._roboid._get_load_packet(0xC2))
                        elif packet[0] == 0x10:
                            return
                    else:
                        if packet[0] == 0x80 and packet[1] == 0x16 and packet[3] == 0xC1:
                            self._parse(packet)
                            self._write(serial, self._roboid._get_load_packet(0xC2))
                            loaded = True
                        else:
                            if count % 10 == 0:
                                self._write(serial, self._roboid._get_load_packet(0xC1))
                            count += 1
            except:
                pass

    def _read(self, serial):
        try:
            state = 0
            suma = 0
            sumb = 0
            while True:
                c = serial.read()[0]
                if state == 0: # idle
                    if c == 0x52: # header1
                        suma = c & 0xff
                        sumb = suma
                        state = 1
                elif state == 1: # header
                    if c == 0x4F: # header2
                        suma = (suma + c) & 0xff
                        sumb = (sumb + suma) & 0xff
                        state = 2
                    else:
                        suma = 0
                        sumb = 0
                        state = 0
                elif state == 2: # length
                    length = c
                    if length > 244:
                        suma = 0
                        sumb = 0
                        state = 0
                    else:
                        buf = []
                        suma = (suma + c) & 0xff
                        sumb = (sumb + suma) & 0xff
                        state = 3
                elif state == 3: # packte
                    buf.append(c)
                    suma = (suma + c) & 0xff
                    sumb = (sumb + suma) & 0xff
                    if len(buf) == length:
                        state = 4
                elif state == 4: # checksum1
                    if c == suma:
                        state = 5
                    else:
                        state = 0
                elif state == 5: # checksum2
                    state = 0
                    if c == sumb:
                        return buf
        except:
            return None

    def _write(self, serial, packet):
        try:
            serial.write(packet)
        except:
            pass

    def _parse(self, packet):
        value = packet[4] & 0xff
        if value > 0x7f: value -= 0x100
        self._roboid._set_balance(value + 1)


class Beagle(Robot):
    ID = 'kr.robomation.physical.beagle'

    LEFT_WHEEL = 0x01400000
    RIGHT_WHEEL = 0x01400001
    SERVO_OUTPUT_A = 0x01400002
    SERVO_OUTPUT_B = 0x01400003
    SERVO_OUTPUT_C = 0x01400004
    BUZZER = 0x01400005
    PULSE = 0x01400006
    NOTE = 0x01400007
    SOUND = 0x01400008
    SERVO_SPEED_A = 0x01400009
    SERVO_SPEED_B = 0x0140000a
    SERVO_SPEED_C = 0x0140000b
    RESET_ENCODER = 0x0140000c
    ENABLE_LIDAR = 0x0140000d
    CONFIG_MOTOR_SUSTAIN = 0x0140000e
    CONFIG_MOTOR_ACCELERATION = 0x0140000f
    CONFIG_ACCELEROMETER_ODR_BW = 0x01400010
    CONFIG_ACCELEROMETER_RANGE = 0x01400011
    CONFIG_GYROSCOPE_ODR_BW = 0x01400012
    CONFIG_GYROSCOPE_RANGE = 0x01400013
    CONFIG_MAGNETOMETER_ODR = 0x01400014
    CONFIG_MAGNETOMETER_REPETITION_XY = 0x01400015
    CONFIG_MAGNETOMETER_REPETITION_Z = 0x01400016

    SIGNAL_STRENGTH = 0x01400020
    TEMPERATURE = 0x01400021
    LEFT_ENCODER = 0x01400022
    RIGHT_ENCODER = 0x01400023
    SERVO_INPUT_A = 0x01400024
    SERVO_INPUT_B = 0x01400025
    SERVO_INPUT_C = 0x01400026
    ACCELEROMETER = 0x01400027
    GYROSCOPE = 0x01400028
    MAGNETOMETER = 0x01400029
    COMPASS = 0x0140002a
    LIDAR = 0x0140002b
    TIMESTAMP_BASIC = 0x0140002c
    TIMESTAMP_IMU = 0x0140002d
    TILT = 0x0140002e
    RESOLUTION = 0x0140002f
    WHEEL_STATE = 0x01400030
    SOUND_STATE = 0x01400031
    BATTERY_STATE = 0x01400032
    CHARGE_STATE = 0x01400033
    ACCELEROMETER_RANGE = 0x01400034
    GYROSCOPE_RANGE = 0x01400035

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

    GYROSCOPE_ODR_200_BW_23 = 0x10
    GYROSCOPE_ODR_100_BW_12 = 0x20
    GYROSCOPE_ODR_200_BW_64 = 0x40
    GYROSCOPE_ODR_100_BW_32 = 0x80

    GYROSCOPE_RANGE_125 = 0x01
    GYROSCOPE_RANGE_250 = 0x02
    GYROSCOPE_RANGE_500 = 0x04
    GYROSCOPE_RANGE_1000 = 0x08
    GYROSCOPE_RANGE_2000 = 0x10

    ACCELEROMETER_ODR_15_63_BW_7_81 = 0x01
    ACCELEROMETER_ODR_31_25_BW_15_63 = 0x02
    ACCELEROMETER_ODR_62_5_BW_31_25 = 0x04
    ACCELEROMETER_ODR_125_BW_62_5 = 0x08
    ACCELEROMETER_ODR_250_BW_125 = 0x10

    ACCELEROMETER_RANGE_2 = 0x01
    ACCELEROMETER_RANGE_4 = 0x02
    ACCELEROMETER_RANGE_8 = 0x04
    ACCELEROMETER_RANGE_16 = 0x08

    MAGNETOMETER_ODR_2 = 0x01
    MAGNETOMETER_ODR_6 = 0x02
    MAGNETOMETER_ODR_8 = 0x04
    MAGNETOMETER_ODR_10 = 0x08
    MAGNETOMETER_ODR_15 = 0x10
    MAGNETOMETER_ODR_20 = 0x20
    MAGNETOMETER_ODR_25 = 0x40
    MAGNETOMETER_ODR_30 = 0x80

    BATTERY_NORMAL = 3
    BATTERY_MIDDLE = 2
    BATTERY_LOW = 1
    BATTERY_EMPTY = 0

    LIDAR_RAW = 0
    LIDAR_BASIC = 0
    LIDAR_ZERO = 1
    LIDAR_FLOOR = 1
    LIDAR_TRUNC = 2
    LIDAR_CEILING = 2

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
    _LIDAR_MODES = {
        "raw": 0,
        "basic": 0,
        "zero": 1,
        "floor": 1,
        "trunc": 2,
        "truncate": 2,
        "ceiling": 2,
    }
    _robots = {}

    def __init__(self, index=0, port_name=None):
        if isinstance(index, str):
            index = 0
            port_name = index
        if index in Beagle._robots:
            robot = Beagle._robots[index]
            if robot: robot.dispose()
        Beagle._robots[index] = self
        super(Beagle, self).__init__(Beagle.ID, "Beagle", index)
        self._bpm = 60
        self._servo_output_a = 0
        self._servo_output_b = 0
        self._servo_output_c = 0
        self._lidar = [65535] * 360
        self._lidar_chart = None
        self._init(port_name)

    def dispose(self):
        Beagle._robots[self.get_index()] = None
        self._roboid._dispose()
        Runner.unregister_robot(self)

    def reset(self):
        self._bpm = 60
        self._servo_output_a = 0
        self._servo_output_b = 0
        self._servo_output_c = 0
        self._lidar = [65535] * 360
        self._roboid._reset()

    def _init(self, port_name):
        from roboid.beagle_roboid import BeagleRoboid
        self._roboid = BeagleRoboid(self.get_index())
        self._add_roboid(self._roboid)
        Runner.register_robot(self)
        Runner.start()
        loader = BeagleLoader(self._roboid)
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

    def wheels(self, left_velocity, right_velocity=None):
        self.write(Beagle.PULSE, 0)
        if isinstance(left_velocity, (int, float)):
            self.write(Beagle.LEFT_WHEEL, left_velocity)
        if isinstance(right_velocity, (int, float)):
            self.write(Beagle.RIGHT_WHEEL, right_velocity)
        else:
            if isinstance(left_velocity, (int, float)):
                self.write(Beagle.RIGHT_WHEEL, left_velocity)

    def left_wheel(self, velocity):
        self.write(Beagle.PULSE, 0)
        if isinstance(velocity, (int, float)):
            self.write(Beagle.LEFT_WHEEL, velocity)

    def right_wheel(self, velocity):
        self.write(Beagle.PULSE, 0)
        if isinstance(velocity, (int, float)):
            self.write(Beagle.RIGHT_WHEEL, velocity)

    def stop(self):
        self.write(Beagle.PULSE, 0)
        self.write(Beagle.LEFT_WHEEL, 0)
        self.write(Beagle.RIGHT_WHEEL, 0)

    def _motion_sec(self, sec, left_velocity, right_velocity):
        self.write(Beagle.PULSE, 0)
        if sec < 0:
            sec = -sec
            left_velocity = -left_velocity
            right_velocity = -right_velocity
        if sec > 0:
            self.write(Beagle.LEFT_WHEEL, left_velocity)
            self.write(Beagle.RIGHT_WHEEL, right_velocity)
            Runner.wait(sec * 1000)
        self.write(Beagle.LEFT_WHEEL, 0)
        self.write(Beagle.RIGHT_WHEEL, 0)

    def move_forward(self, sec=1, velocity=50):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, velocity, velocity)

    def move_backward(self, sec=1, velocity=50):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, -velocity, -velocity)

    def turn_left(self, sec=1, velocity=50):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, -velocity, velocity)

    def turn_right(self, sec=1, velocity=50):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, velocity, -velocity)

    def pivot_left(self, sec=1, velocity=50):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, 0, velocity)

    def pivot_right(self, sec=1, velocity=50):
        if isinstance(sec, (int, float)) and isinstance(velocity, (int, float)):
            self._motion_sec(sec, velocity, 0)

    def move_forward_sec(self, sec=1, velocity=50):
        self.move_forward(sec, velocity)

    def move_backward_sec(self, sec=1, velocity=50):
        self.move_backward(sec, velocity)

    def turn_left_sec(self, sec=1, velocity=50):
        self.turn_left(sec, velocity)

    def turn_right_sec(self, sec=1, velocity=50):
        self.turn_right(sec, velocity)

    def pivot_left_sec(self, sec=1, velocity=50):
        self.pivot_left(sec, velocity)

    def pivot_right_sec(self, sec=1, velocity=50):
        self.pivot_right(sec, velocity)

    def _evaluate_wheel_state(self):
        return self.e(Beagle.WHEEL_STATE)

    def _motion(self, pulse, left_velocity, right_velocity):
        if pulse > 0:
            self.write(Beagle.LEFT_WHEEL, left_velocity)
            self.write(Beagle.RIGHT_WHEEL, right_velocity)
            self.write(Beagle.PULSE, pulse)
            Runner.wait_until(self._evaluate_wheel_state)
            self.write(Beagle.LEFT_WHEEL, 0)
            self.write(Beagle.RIGHT_WHEEL, 0)
        else:
            self.write(Beagle.LEFT_WHEEL, 0)
            self.write(Beagle.RIGHT_WHEEL, 0)
            self.write(Beagle.PULSE, 0)

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

    def buzzer(self, hz):
        self.write(Beagle.NOTE, Beagle.NOTE_OFF)
        self._roboid._cancel_sound()
        if isinstance(hz, (int, float)):
            self.write(Beagle.BUZZER, hz)

    def tempo(self, bpm):
        if isinstance(bpm, (int, float)):
            if bpm > 0:
                self._bpm = bpm

    def note(self, pitch, beats=None):
        self.write(Beagle.BUZZER, 0)
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
                if tmp in Beagle._NOTES:
                    pitch = Beagle._NOTES[tmp] + (octave - 1) * 12
        if isinstance(pitch, (int, float)):
            pitch = int(pitch)
            if isinstance(beats, (int, float)):
                bpm = self._bpm
                if beats > 0 and bpm > 0:
                    if pitch == 0:
                        self.write(Beagle.NOTE, Beagle.NOTE_OFF)
                        Runner.wait(beats * 60 * 1000.0 / bpm)
                    elif pitch > 0:
                        timeout = beats * 60 * 1000.0 / bpm
                        tail = 0
                        if timeout > 100:
                            tail = 100
                        self.write(Beagle.NOTE, pitch)
                        Runner.wait(timeout - tail)
                        self.write(Beagle.NOTE, Beagle.NOTE_OFF)
                        if tail > 0:
                            Runner.wait(tail)
                else:
                    self.write(Beagle.NOTE, Beagle.NOTE_OFF)
            elif pitch >= 0:
                self.write(Beagle.NOTE, pitch)

    def _evaluate_sound(self):
        return self.e(Beagle.SOUND_STATE)

    def sound(self, sound, repeat=1):
        self.write(Beagle.BUZZER, 0)
        self.write(Beagle.NOTE, Beagle.NOTE_OFF)
        if isinstance(sound, str):
            tmp = sound.lower()
            if tmp in Beagle._SOUNDS:
                sound = Beagle._SOUNDS[tmp]
        if isinstance(sound, (int, float)) and isinstance(repeat, (int, float)):
            sound = int(sound)
            repeat = int(repeat)
            if sound > 0 and repeat != 0:
                self._roboid._run_sound(sound, repeat)
            else:
                self._roboid._cancel_sound()

    def sound_until_done(self, sound, repeat=1):
        self.write(Beagle.BUZZER, 0)
        self.write(Beagle.NOTE, Beagle.NOTE_OFF)
        if isinstance(sound, str):
            tmp = sound.lower()
            if tmp in Beagle._SOUNDS:
                sound = Beagle._SOUNDS[tmp]
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

    def servo_output_a(self, degree):
        self._servo_output_a = degree
        if degree < 1: degree = 1
        self.write(Beagle.SERVO_OUTPUT_A, degree)

    def _evaluate_servo_a(self, degree):
        return self.servo_input_a() == degree

    def servo_output_a_until_done(self, degree):
        self.servo_output_a(degree)
        Runner.wait_until(self._evaluate_servo_a, degree)

    def servo_output_b(self, degree):
        self._servo_output_b = degree
        if degree < 1: degree = 1
        self.write(Beagle.SERVO_OUTPUT_B, degree)

    def _evaluate_servo_b(self, degree):
        return self.servo_input_b() == degree

    def servo_output_b_until_done(self, degree):
        self.servo_output_b(degree)
        Runner.wait_until(self._evaluate_servo_b, degree)

    def servo_output_c(self, degree):
        self._servo_output_c = degree
        if degree < 1: degree = 1
        self.write(Beagle.SERVO_OUTPUT_C, degree)

    def _evaluate_servo_c(self, degree):
        return self.servo_input_c() == degree

    def servo_output_c_until_done(self, degree):
        self.servo_output_c(degree)
        Runner.wait_until(self._evaluate_servo_c, degree)

    def servo_speed_a(self, speed):
        self.write(Beagle.SERVO_SPEED_A, speed)

    def servo_speed_b(self, speed):
        self.write(Beagle.SERVO_SPEED_B, speed)

    def servo_speed_c(self, speed):
        self.write(Beagle.SERVO_SPEED_C, speed)

    def release_servo_a(self):
        self.write(Beagle.SERVO_OUTPUT_A, 0)

    def release_servo_b(self):
        self.write(Beagle.SERVO_OUTPUT_B, 0)

    def release_servo_c(self):
        self.write(Beagle.SERVO_OUTPUT_C, 0)

    def reset_encoder(self):
        self.write(Beagle.RESET_ENCODER)

    def enable_lidar(self, value):
        self.write(Beagle.ENABLE_LIDAR, value)

    def start_lidar(self):
        self.write(Beagle.ENABLE_LIDAR, 1)

    def stop_lidar(self):
        self.write(Beagle.ENABLE_LIDAR, 0)

    def is_lidar_ready(self):
        return self._roboid._is_lidar_ready()

    def wait_until_lidar_ready(self):
        self._roboid._wait_until_lidar_ready()

    def signal_strength(self):
        return self.read(Beagle.SIGNAL_STRENGTH)

    def temperature(self):
        return self.read(Beagle.TEMPERATURE)

    def left_encoder(self):
        return self.read(Beagle.LEFT_ENCODER)

    def right_encoder(self):
        return self.read(Beagle.RIGHT_ENCODER)

    def servo_input_a(self):
        value = self.read(Beagle.SERVO_INPUT_A)
        if value == 1 and self._servo_output_a == 0: value = 0
        return value

    def servo_input_b(self):
        value = self.read(Beagle.SERVO_INPUT_B)
        if value == 1 and self._servo_output_b == 0: value = 0
        return value

    def servo_input_c(self):
        value = self.read(Beagle.SERVO_INPUT_C)
        if value == 1 and self._servo_output_c == 0: value = 0
        return value

    def scale_accelerometer(self):
        return self.read(Beagle.ACCELEROMETER_RANGE) / 2048.0

    def raw_accelerometer(self):
        return (self.read(Beagle.ACCELEROMETER, 0), self.read(Beagle.ACCELEROMETER, 1), self.read(Beagle.ACCELEROMETER, 2), self.read(Beagle.ACCELEROMETER, 3))

    def raw_accelerometer_x(self):
        return self.read(Beagle.ACCELEROMETER, 1)

    def raw_accelerometer_y(self):
        return self.read(Beagle.ACCELEROMETER, 2)

    def raw_accelerometer_z(self):
        return self.read(Beagle.ACCELEROMETER, 3)

    def accelerometer(self):
        scale = self.scale_accelerometer()
        return (self.read(Beagle.ACCELEROMETER, 0), self.read(Beagle.ACCELEROMETER, 1) * scale, self.read(Beagle.ACCELEROMETER, 2) * scale, self.read(Beagle.ACCELEROMETER, 3) * scale)

    def accelerometer_x(self):
        return self.read(Beagle.ACCELEROMETER, 1) * self.scale_accelerometer()

    def accelerometer_y(self):
        return self.read(Beagle.ACCELEROMETER, 2) * self.scale_accelerometer()

    def accelerometer_z(self):
        return self.read(Beagle.ACCELEROMETER, 3) * self.scale_accelerometer()

    def listen_raw_accelerometer(self, listener, interpolation=None):
        self._roboid._set_raw_accelerometer_listener(listener, interpolation)

    def listen_accelerometer(self, listener, interpolation=None):
        self._roboid._set_accelerometer_listener(listener, interpolation)

    def scale_gyroscope(self):
        return self.read(Beagle.GYROSCOPE_RANGE) / 32768.0

    def raw_gyroscope(self):
        return (self.read(Beagle.GYROSCOPE, 0), self.read(Beagle.GYROSCOPE, 1), self.read(Beagle.GYROSCOPE, 2), self.read(Beagle.GYROSCOPE, 3))

    def raw_gyroscope_x(self):
        return self.read(Beagle.GYROSCOPE, 1)

    def raw_gyroscope_y(self):
        return self.read(Beagle.GYROSCOPE, 2)

    def raw_gyroscope_z(self):
        return self.read(Beagle.GYROSCOPE, 3)

    def gyroscope(self):
        scale = self.scale_gyroscope()
        return (self.read(Beagle.GYROSCOPE, 0), self.read(Beagle.GYROSCOPE, 1) * scale, self.read(Beagle.GYROSCOPE, 2) * scale, self.read(Beagle.GYROSCOPE, 3) * scale)

    def gyroscope_x(self):
        return self.read(Beagle.GYROSCOPE, 1) * self.scale_gyroscope()

    def gyroscope_y(self):
        return self.read(Beagle.GYROSCOPE, 2) * self.scale_gyroscope()

    def gyroscope_z(self):
        return self.read(Beagle.GYROSCOPE, 3) * self.scale_gyroscope()

    def listen_raw_gyroscope(self, listener, interpolation=None):
        self._roboid._set_raw_gyroscope_listener(listener, interpolation)

    def listen_gyroscope(self, listener, interpolation=None):
        self._roboid._set_gyroscope_listener(listener, interpolation)

    def lidar(self):
        self.read(Beagle.LIDAR, self._lidar)
        return self._lidar

    def left_lidar(self):
        values = self._roboid._get_lidar_directions()
        if values: return values[2]
        return 65535

    def right_lidar(self):
        values = self._roboid._get_lidar_directions()
        if values: return values[6]
        return 65535

    def front_lidar(self):
        values = self._roboid._get_lidar_directions()
        if values: return values[0]
        return 65535

    def rear_lidar(self):
        values = self._roboid._get_lidar_directions()
        if values: return values[4]
        return 65535

    def left_front_lidar(self):
        values = self._roboid._get_lidar_directions()
        if values: return values[1]
        return 65535

    def right_front_lidar(self):
        values = self._roboid._get_lidar_directions()
        if values: return values[7]
        return 65535

    def left_rear_lidar(self):
        values = self._roboid._get_lidar_directions()
        if values: return values[3]
        return 65535

    def right_rear_lidar(self):
        values = self._roboid._get_lidar_directions()
        if values: return values[5]
        return 65535

    def timestamp_basic(self):
        return self.read(Beagle.TIMESTAMP_BASIC)

    def timestamp_imu(self):
        return self.read(Beagle.TIMESTAMP_IMU)

    def tilt(self):
        return self.read(Beagle.TILT)

    def resolution(self):
        return self.read(Beagle.RESOLUTION)

    def battery_state(self):
        return self.read(Beagle.BATTERY_STATE)

    def charge_state(self):
        return self.read(Beagle.CHARGE_STATE)

    def lidar_mode(self, mode):
        if isinstance(mode, (int, float)):
            if mode >= 0 and mode <= Beagle.LIDAR_CEILING:
                self._roboid._set_lidar_mode(int(mode))
        elif isinstance(mode, str):
            tmp = mode.lower()
            if tmp in Beagle._LIDAR_MODES:
                self._roboid._set_lidar_mode(Beagle._LIDAR_MODES[tmp])

    def _draw_lidar_chart(self):
        canvas = self._lidar_canvas
        width = 480
        height = 480
        scale = 0.25
        cx = width // 2
        cy = height // 2
        
        canvas.delete('all')
        canvas.create_line(0, cy, width, cy, fill='#aaaaaa', width=2)
        canvas.create_line(cx, 0, cx, height, fill='#aaaaaa', width=2)
        
        for r in range(100, 6000, 100):
            rr = r * scale
            if rr < width:
                canvas.create_oval(cx-rr, cy-rr, cx+rr, cy+rr, outline='#aaaaaa', width=0.5, dash=(5, 3))
        
        for r in range(1000, 6000, 1000):
            rr = r * scale
            if rr < width:
                canvas.create_oval(cx-rr, cy-rr, cx+rr, cy+rr, outline='#aaaaaa', width=2)
        
        values = self.lidar()
        sz = len(values)
        delta = 2 * math.pi / sz
        r = 2 * scale
        for i in range(sz):
            val = values[i]
            if val >= 0 and val != 65535:
                rad = i * delta + math.pi / 2
                x = 240 + scale * val * math.cos(rad)
                y = 240 - scale * val * math.sin(rad)
                if x + r >= 0 and x - r <= 480 and y + r >= 0 and y - r <= 480:
                    canvas.create_oval(x - r, y - r, x + r, y + r, fill='red', outline='red')
        canvas.after(10, self._draw_lidar_chart)

    def _on_lidar_chart_closing(self):
        if self._lidar_chart is not None:
            self._lidar_chart.quit()
            self._lidar_chart = None

    def _show_lidar_chart(self):
        import tkinter
        self._lidar_chart = tkinter.Tk()
        window = self._lidar_chart
        window.title('LiDAR Chart')
        window.resizable(False, False)
        window.protocol("WM_DELETE_WINDOW", self._on_lidar_chart_closing)
        self._lidar_canvas = tkinter.Canvas(window, width=480, height=480, bg='white')
        self._lidar_canvas.pack()
        self._draw_lidar_chart()
        window.mainloop()

    def lidar_chart(self):
        import threading
        thread = threading.Thread(target=self._show_lidar_chart)
        self._thread = thread
        thread.daemon = True
        thread.start()
