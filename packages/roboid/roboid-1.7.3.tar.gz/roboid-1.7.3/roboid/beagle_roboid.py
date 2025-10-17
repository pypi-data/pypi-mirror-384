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

import time
import threading
import math

from roboid.runner import Runner
from roboid.util import Util
from roboid.model import DeviceType
from roboid.model import DataType
from roboid.model import Roboid
from roboid.connector import Result
from roboid.beagle import Beagle
from roboid.serial_connector import NusSerialConnector


class BeagleConnectionChecker(object):
    def __init__(self, roboid):
        self._roboid = roboid

    def check(self, info):
        return info[1] == "Beagle" and info[2] == "14"


class BeagleInterpolator(object):
    def __init__(self, method):
        self._method = method
        self._prev_index = -1
        self._prev_x = 0
        self._prev_y = 0
        self._prev_z = 0

    def interpolate(self, listener, index, timestamp, x, y, z):
        method = self._method
        if method is not None:
            prev_index = self._prev_index
            if prev_index != -1:
                prev_x = self._prev_x
                prev_y = self._prev_y
                prev_z = self._prev_z
                count = (index - prev_index) % 16
                if method == 'constant':
                    for i in range(1, count):
                        listener((prev_index + i) % 16, timestamp, prev_x, prev_y, prev_z)
                elif method == 'linear':
                    for i in range(1, count):
                        listener((prev_index + i) % 16, timestamp, prev_x + (x - prev_x) * i / count, prev_y + (y - prev_y) * i / count, prev_z + (z - prev_z) * i / count)
            self._prev_index = index
            self._prev_x = x
            self._prev_y = y
            self._prev_z = z


class BeagleRoboid(Roboid):
    _SOUNDS = {
        Beagle.SOUND_OFF: 0x00,
        Beagle.SOUND_BEEP: 0x01,
        Beagle.SOUND_RANDOM_BEEP: 0x05,
        Beagle.SOUND_NOISE: 0x07,
        Beagle.SOUND_SIREN: 0x09,
        Beagle.SOUND_ENGINE: 0x0b,
        Beagle.SOUND_CHOP: 0x12,
        Beagle.SOUND_ROBOT: 0x20,
        Beagle.SOUND_DIBIDIBIDIP: 0x21,
        Beagle.SOUND_GOOD_JOB: 0x23,
        Beagle.SOUND_HAPPY: 0x30,
        Beagle.SOUND_ANGRY: 0x31,
        Beagle.SOUND_SAD: 0x32,
        Beagle.SOUND_SLEEP: 0x33,
        Beagle.SOUND_MARCH: 0x34,
        Beagle.SOUND_BIRTHDAY: 0x35
    }

    def __init__(self, index):
        super(BeagleRoboid, self).__init__(Beagle.ID, "Beagle", 0x01400000)
        self._index = index
        self._connector = None
        self._ready = False
        self._thread = None
        self._thread_lock = threading.Lock()

        self._left_wheel = 0
        self._right_wheel = 0
        self._servo_output_a = 0
        self._servo_output_b = 0
        self._servo_output_c = 0
        self._buzzer = 0
        self._pulse = 0
        self._note = 0
        self._sound = 0
        self._servo_speed_a = 5
        self._servo_speed_b = 5
        self._servo_speed_c = 5
        self._enable_lidar = 0
        self._config_motor_sustain = 0
        self._config_motor_acceleration = 0
        self._config_accelerometer_odr_bw = 0x08
        self._config_accelerometer_range = 0x01
        self._config_gyroscope_odr_bw = 0x20
        self._config_gyroscope_range = 0x02
        self._config_magnetometer_odr = 0x20
        self._config_magnetometer_repetition_xy = 47
        self._config_magnetometer_repetition_z = 83

        self._pulse_written = False
        self._note_written = False
        self._sound_written = False
        self._servo_speed_a_written = False
        self._servo_speed_b_written = False
        self._servo_speed_c_written = False
        self._reset_encoder_written = False
        self._enable_lidar_written = False
        self._config_motor_sustain_written = False
        self._config_motor_acceleration_written = False
        self._config_accelerometer_odr_bw_written = False
        self._config_accelerometer_range_written = False
        self._config_gyroscope_odr_bw_written = False
        self._config_gyroscope_range_written = False
        self._config_magnetometer_odr_written = False
        self._config_magnetometer_repetition_xy_written = False
        self._config_magnetometer_repetition_z_written = False

        self._wheel_id = 0
        self._wheel_pulse = 0
        self._wheel_pulse_prev = -1
        self._wheel_event = 0
        self._wheel_state_id = -1

        self._current_sound = 0
        self._sound_repeat = 1
        self._sound_flag = 0
        self._sound_event = 0
        self._sound_state_id = -1

        self._command_system_id = 0
        self._command_basic_id = 0
        self._command_reset_encoder_id = 0
        self._command_accelerometer_id = 0
        self._command_gyroscope_id = 0
        self._command_magnetometer_id = 0
        self._command_lidar_id = 0

        self._event_basic_id = -1
        self._event_imu_id = -1
        self._event_accelerometer_id = -1
        self._event_gyroscope_id = -1
        self._event_magnetometer_id = -1
        self._event_tilt = -4
        self._event_resolution = -1
        self._event_battery_state = -1
        self._event_charge_state = -1
        self._event_accelerometer_range = 2
        self._event_gyroscope_range = 250

        self._imu_send_more_count = 0
        self._imu_last_packet = None
        self._raw_accelerometer_listener = None
        self._raw_accelerometer_interpolator = None
        self._accelerometer_listener = None
        self._accelerometer_interpolator = None
        self._raw_gyroscope_listener = None
        self._raw_gyroscope_interpolator = None
        self._gyroscope_listener = None
        self._gyroscope_interpolator = None

        self._lidar_mode = 0
        self._lidar_arr = None
        self._lidar_values = [None, None, None, None]
        self._lidar_valid = [False, False, False, False]
        self._lidar_ready = False
        self._lidar_activated = False
        self._lidar_deactivating = False
        self._lidar_send_more_count = 0
        self._lidar_last_packet = None
        self._lidar_directions = [65535] * 8

        self._load_packet = [0x52, 0x49, 0x04, 0x80, 0x02, 0, 0, 0, 0]
        self._basic_packet = None
        self._imu_packet = None
        self._lidar_packet = None
        self._packet_sent = 0
        self._packet_received = 0
        
        self._balance = 0
        self._bluetooth_reset_count = 0
        self._create_model()

    def _create_model(self):
        from roboid.beagle import Beagle
        dict = self._device_dict = {}
        dict[Beagle.LEFT_WHEEL] = self._left_wheel_device = self._add_device(Beagle.LEFT_WHEEL, "LeftWheel", DeviceType.EFFECTOR, DataType.FLOAT, 1, -100, 100, 0)
        dict[Beagle.RIGHT_WHEEL] = self._right_wheel_device = self._add_device(Beagle.RIGHT_WHEEL, "RightWheel", DeviceType.EFFECTOR, DataType.FLOAT, 1, -100, 100, 0)
        dict[Beagle.SERVO_OUTPUT_A] = self._servo_output_a_device = self._add_device(Beagle.SERVO_OUTPUT_A, "ServoOutputA", DeviceType.EFFECTOR, DataType.INTEGER, 1, 0, 180, 0)
        dict[Beagle.SERVO_OUTPUT_B] = self._servo_output_b_device = self._add_device(Beagle.SERVO_OUTPUT_B, "ServoOutputB", DeviceType.EFFECTOR, DataType.INTEGER, 1, 0, 180, 0)
        dict[Beagle.SERVO_OUTPUT_C] = self._servo_output_c_device = self._add_device(Beagle.SERVO_OUTPUT_C, "ServoOutputC", DeviceType.EFFECTOR, DataType.INTEGER, 1, 0, 180, 0)
        dict[Beagle.BUZZER] = self._buzzer_device = self._add_device(Beagle.BUZZER, "Buzzer", DeviceType.EFFECTOR, DataType.FLOAT, 1, 0, 167772.15, 0)
        dict[Beagle.PULSE] = self._pulse_device = self._add_device(Beagle.PULSE, "Pulse", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 65535, 0)
        dict[Beagle.NOTE] = self._note_device = self._add_device(Beagle.NOTE, "Note", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 88, 0)
        dict[Beagle.SOUND] = self._sound_device = self._add_device(Beagle.SOUND, "Sound", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 127, 0)
        dict[Beagle.SERVO_SPEED_A] = self._servo_speed_a_device = self._add_device(Beagle.SERVO_SPEED_A, "ServoSpeedA", DeviceType.COMMAND, DataType.INTEGER, 1, 1, 7, 5)
        dict[Beagle.SERVO_SPEED_B] = self._servo_speed_b_device = self._add_device(Beagle.SERVO_SPEED_B, "ServoSpeedB", DeviceType.COMMAND, DataType.INTEGER, 1, 1, 7, 5)
        dict[Beagle.SERVO_SPEED_C] = self._servo_speed_c_device = self._add_device(Beagle.SERVO_SPEED_C, "ServoSpeedC", DeviceType.COMMAND, DataType.INTEGER, 1, 1, 7, 5)
        dict[Beagle.RESET_ENCODER] = self._reset_encoder_device = self._add_device(Beagle.RESET_ENCODER, "ResetEncoder", DeviceType.COMMAND, DataType.INTEGER, 0, 0, 0, 0)
        dict[Beagle.ENABLE_LIDAR] = self._enable_lidar_device = self._add_device(Beagle.ENABLE_LIDAR, "EnableLidar", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 1, 0)
        dict[Beagle.CONFIG_MOTOR_SUSTAIN] = self._config_motor_sustain_device = self._add_device(Beagle.CONFIG_MOTOR_SUSTAIN, "ConfigMotorSustain", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 1, 0)
        dict[Beagle.CONFIG_MOTOR_ACCELERATION] = self._config_motor_acceleration_device = self._add_device(Beagle.CONFIG_MOTOR_ACCELERATION, "ConfigMotorAcceleration", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 9, 0)
        dict[Beagle.CONFIG_ACCELEROMETER_ODR_BW] = self._config_accelerometer_odr_bw_device = self._add_device(Beagle.CONFIG_ACCELEROMETER_ODR_BW, "ConfigAccelerometerOdrBw", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 255, 0x08)
        dict[Beagle.CONFIG_ACCELEROMETER_RANGE] = self._config_accelerometer_range_device = self._add_device(Beagle.CONFIG_ACCELEROMETER_RANGE, "ConfigAccelerometerRange", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 255, 0x01)
        dict[Beagle.CONFIG_GYROSCOPE_ODR_BW] = self._config_gyroscope_odr_bw_device = self._add_device(Beagle.CONFIG_GYROSCOPE_ODR_BW, "ConfigGyroscopeOdrBw", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 255, 0x20)
        dict[Beagle.CONFIG_GYROSCOPE_RANGE] = self._config_gyroscope_range_device = self._add_device(Beagle.CONFIG_GYROSCOPE_RANGE, "ConfigGyroscopeRange", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 255, 0x02)
        dict[Beagle.CONFIG_MAGNETOMETER_ODR] = self._config_magnetometer_odr_device = self._add_device(Beagle.CONFIG_MAGNETOMETER_ODR, "ConfigMagnetometerOdr", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 255, 0x20)
        dict[Beagle.CONFIG_MAGNETOMETER_REPETITION_XY] = self._config_magnetometer_repetition_xy_device = self._add_device(Beagle.CONFIG_MAGNETOMETER_REPETITION_XY, "ConfigMagnetometerRepetitionXy", DeviceType.COMMAND, DataType.INTEGER, 1, 1, 511, 47)
        dict[Beagle.CONFIG_MAGNETOMETER_REPETITION_Z] = self._config_magnetometer_repetition_z_device = self._add_device(Beagle.CONFIG_MAGNETOMETER_REPETITION_Z, "ConfigMagnetometerRepetitionZ", DeviceType.COMMAND, DataType.INTEGER, 1, 1, 256, 83)
        dict[Beagle.SIGNAL_STRENGTH] = self._signal_strength_device = self._add_device(Beagle.SIGNAL_STRENGTH, "SignalStrength", DeviceType.SENSOR, DataType.INTEGER, 1, -128, 0, 0)
        dict[Beagle.TEMPERATURE] = self._temperature_device = self._add_device(Beagle.TEMPERATURE, "Temperature", DeviceType.SENSOR, DataType.INTEGER, 1, -41, 87, 0)
        dict[Beagle.LEFT_ENCODER] = self._left_encoder_device = self._add_device(Beagle.LEFT_ENCODER, "LeftEncoder", DeviceType.SENSOR, DataType.INTEGER, 1, -2147483648, 2147483647, 0)
        dict[Beagle.RIGHT_ENCODER] = self._right_encoder_device = self._add_device(Beagle.RIGHT_ENCODER, "RightEncoder", DeviceType.SENSOR, DataType.INTEGER, 1, -2147483648, 2147483647, 0)
        dict[Beagle.SERVO_INPUT_A] = self._servo_input_a_device = self._add_device(Beagle.SERVO_INPUT_A, "ServoInputA", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 180, 0)
        dict[Beagle.SERVO_INPUT_B] = self._servo_input_b_device = self._add_device(Beagle.SERVO_INPUT_B, "ServoInputB", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 180, 0)
        dict[Beagle.SERVO_INPUT_C] = self._servo_input_c_device = self._add_device(Beagle.SERVO_INPUT_C, "ServoInputC", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 180, 0)
        dict[Beagle.ACCELEROMETER] = self._accelerometer_device = self._add_device(Beagle.ACCELEROMETER, "Accelerometer", DeviceType.SENSOR, DataType.INTEGER, 4, -2048, 2047, 0)
        dict[Beagle.GYROSCOPE] = self._gyroscope_device = self._add_device(Beagle.GYROSCOPE, "Gyroscope", DeviceType.SENSOR, DataType.INTEGER, 4, -32768, 32767, 0)
        dict[Beagle.MAGNETOMETER] = self._magnetometer_device = self._add_device(Beagle.MAGNETOMETER, "Magnetometer", DeviceType.SENSOR, DataType.FLOAT, 4, -2500, 2500, 0)
        dict[Beagle.COMPASS] = self._compass_device = self._add_device(Beagle.COMPASS, "Compass", DeviceType.SENSOR, DataType.INTEGER, 1, -1, 359, -1)
        dict[Beagle.LIDAR] = self._lidar_device = self._add_device(Beagle.LIDAR, "Lidar", DeviceType.SENSOR, DataType.INTEGER, 360, 0, 65535, 65535)
        dict[Beagle.TIMESTAMP_BASIC] = self._timestamp_basic_device = self._add_device(Beagle.TIMESTAMP_BASIC, "TimestampBasic", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 65535, 0)
        dict[Beagle.TIMESTAMP_IMU] = self._timestamp_imu_device = self._add_device(Beagle.TIMESTAMP_IMU, "TimestampImu", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 65535, 0)
        dict[Beagle.TILT] = self._tilt_device = self._add_device(Beagle.TILT, "Tilt", DeviceType.EVENT, DataType.INTEGER, 1, -3, 3, 0)
        dict[Beagle.RESOLUTION] = self._resolution_device = self._add_device(Beagle.RESOLUTION, "Resolution", DeviceType.EVENT, DataType.FLOAT, 1, 0.2, 1.5, 1.0)
        dict[Beagle.WHEEL_STATE] = self._wheel_state_device = self._add_device(Beagle.WHEEL_STATE, "WheelState", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Beagle.SOUND_STATE] = self._sound_state_device = self._add_device(Beagle.SOUND_STATE, "SoundState", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Beagle.BATTERY_STATE] = self._battery_state_device = self._add_device(Beagle.BATTERY_STATE, "BatteryState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 3, 3)
        dict[Beagle.CHARGE_STATE] = self._charge_state_device = self._add_device(Beagle.CHARGE_STATE, "ChargeState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Beagle.ACCELEROMETER_RANGE] = self._accelerometer_range_device = self._add_device(Beagle.ACCELEROMETER_RANGE, "AccelerometerRange", DeviceType.EVENT, DataType.INTEGER, 1, 2, 16, 2)
        dict[Beagle.GYROSCOPE_RANGE] = self._gyroscope_range_device = self._add_device(Beagle.GYROSCOPE_RANGE, "GyroscopeRange", DeviceType.EVENT, DataType.INTEGER, 1, 125, 2000, 250)

    def find_device_by_id(self, device_id):
        return self._device_dict.get(device_id)

    def _run(self):
        try:
            while self._running or self._releasing > 0:
                if self._receive(self._connector):
                    self._send(self._connector)
                    if self._releasing > 0:
                        self._releasing -= 1
                time.sleep(0.01)
        except:
            pass

    def _init(self, loader, port_name=None):
        Runner.register_required()
        self._running = True
        self._releasing = 0
        thread = threading.Thread(target=self._run)
        self._thread = thread
        thread.daemon = True
        thread.start()

        tag = "Beagle[{}]".format(self._index)
        self._connector = NusSerialConnector(tag, BeagleConnectionChecker(self), loader)
        result = self._connector.open(port_name)
        if result == Result.FOUND:
            while self._ready == False and self._is_disposed() == False:
                time.sleep(0.01)
        elif result == Result.NOT_AVAILABLE:
            Runner.register_checked()

    def _release(self):
        if self._ready:
            self._releasing = 5
        self._running = False
        thread = self._thread
        self._thread = None
        if thread:
            thread.join()

        connector = self._connector
        self._connector = None
        if connector:
            connector.close()

    def _dispose(self):
        if self._is_disposed() == False:
            super(BeagleRoboid, self)._dispose()
            self._release()

    def _reset(self):
        super(BeagleRoboid, self)._reset()

        self._left_wheel = 0
        self._right_wheel = 0
        self._servo_output_a = 0
        self._servo_output_b = 0
        self._servo_output_c = 0
        self._buzzer = 0
        self._pulse = 0
        self._note = 0
        self._sound = 0
        self._servo_speed_a = 5
        self._servo_speed_b = 5
        self._servo_speed_c = 5
        self._enable_lidar = 0
        self._config_motor_sustain = 0
        self._config_motor_acceleration = 0
        self._config_accelerometer_odr_bw = 0x08
        self._config_accelerometer_range = 0x01
        self._config_gyroscope_odr_bw = 0x20
        self._config_gyroscope_range = 0x02
        self._config_magnetometer_odr = 0x20
        self._config_magnetometer_repetition_xy = 47
        self._config_magnetometer_repetition_z = 83

        self._pulse_written = False
        self._note_written = False
        self._sound_written = False
        self._servo_speed_a_written = False
        self._servo_speed_b_written = False
        self._servo_speed_c_written = False
        self._reset_encoder_written = False
        self._enable_lidar_written = False
        self._config_motor_sustain_written = False
        self._config_motor_acceleration_written = False
        self._config_accelerometer_odr_bw_written = False
        self._config_accelerometer_range_written = False
        self._config_gyroscope_odr_bw_written = False
        self._config_gyroscope_range_written = False
        self._config_magnetometer_odr_written = False
        self._config_magnetometer_repetition_xy_written = False
        self._config_magnetometer_repetition_z_written = False

        self._wheel_pulse = 0
        self._wheel_pulse_prev = -1
        self._wheel_event = 0
        self._wheel_state_id = -1

        self._current_sound = 0
        self._sound_repeat = 1
        self._sound_event = 0
        self._sound_state_id = -1

        self._event_basic_id = -1
        self._event_imu_id = -1
        self._event_accelerometer_id = -1
        self._event_gyroscope_id = -1
        self._event_magnetometer_id = -1
        self._event_tilt = -4
        self._event_resolution = -1
        self._event_battery_state = -1
        self._event_charge_state = -1
        self._event_accelerometer_range = 2
        self._event_gyroscope_range = 250
        
        self._basic_packet = None
        self._imu_packet = None
        self._lidar_packet = None
        self._packet_sent = 0
        self._packet_received = 0
        
        self._lidar_mode = 0
        if self._lidar_activated:
            self._lidar_activated = False
            self._lidar_deactivating = True
            self._enable_lidar_written = True

    def _request_motoring_data(self):
        with self._thread_lock:
            self._left_wheel = self._left_wheel_device.read()
            self._right_wheel = self._right_wheel_device.read()
            self._servo_output_a = self._servo_output_a_device.read()
            self._servo_output_b = self._servo_output_b_device.read()
            self._servo_output_c = self._servo_output_c_device.read()
            self._buzzer = self._buzzer_device.read()
            if self._pulse_device._is_written():
                self._pulse = self._pulse_device.read()
                self._pulse_written = True
            if self._note_device._is_written():
                self._note = self._note_device.read()
                self._note_written = True
            if self._sound_device._is_written():
                self._sound = self._sound_device.read()
                self._sound_written = True
            if self._servo_speed_a_device._is_written():
                self._servo_speed_a = self._servo_speed_a_device.read()
                self._servo_speed_a_written = True
            if self._servo_speed_b_device._is_written():
                self._servo_speed_b = self._servo_speed_b_device.read()
                self._servo_speed_b_written = True
            if self._servo_speed_c_device._is_written():
                self._servo_speed_c = self._servo_speed_c_device.read()
                self._servo_speed_c_written = True
            if self._reset_encoder_device._is_written():
                self._reset_encoder_written = True
            if self._enable_lidar_device._is_written():
                self._enable_lidar = self._enable_lidar_device.read()
                self._enable_lidar_written = True
                self._lidar_activated = True
            if self._config_motor_sustain_device._is_written():
                self._config_motor_sustain = self._config_motor_sustain_device.read()
                self._config_motor_sustain_written = True
            if self._config_motor_acceleration_device._is_written():
                self._config_motor_acceleration = self._config_motor_acceleration_device.read()
                self._config_motor_acceleration_written = True
            if self._config_accelerometer_odr_bw_device._is_written():
                self._config_accelerometer_odr_bw = self._config_accelerometer_odr_bw_device.read()
                self._config_accelerometer_odr_bw_written = True
            if self._config_accelerometer_range_device._is_written():
                self._config_accelerometer_range = self._config_accelerometer_range_device.read()
                self._config_accelerometer_range_written = True
            if self._config_gyroscope_odr_bw_device._is_written():
                self._config_gyroscope_odr_bw = self._config_gyroscope_odr_bw_device.read()
                self._config_gyroscope_odr_bw_written = True
            if self._config_gyroscope_range_device._is_written():
                self._config_gyroscope_range = self._config_gyroscope_range_device.read()
                self._config_gyroscope_range_written = True
            if self._config_magnetometer_odr_device._is_written():
                self._config_magnetometer_odr = self._config_magnetometer_odr_device.read()
                self._config_magnetometer_odr_written = True
            if self._config_magnetometer_repetition_xy_device._is_written():
                self._config_magnetometer_repetition_xy = self._config_magnetometer_repetition_xy_device.read()
                self._config_magnetometer_repetition_xy_written = True
            if self._config_magnetometer_repetition_z_device._is_written():
                self._config_magnetometer_repetition_z = self._config_magnetometer_repetition_z_device.read()
                self._config_magnetometer_repetition_z_written = True
        self._clear_written()

    def _get_sound(self, sound):
        if isinstance(sound, (int, float)):
            sound = int(sound)
            if sound in BeagleRoboid._SOUNDS:
                return BeagleRoboid._SOUNDS[sound]
        return 0

    def _run_sound(self, sound, repeat):
        if isinstance(sound, (int, float)) and isinstance(repeat, (int, float)):
            sound = int(sound)
            repeat = int(repeat)
            if repeat < 0: repeat = -1
            if repeat != 0:
                self._current_sound = sound
                self._sound_repeat = repeat
                self._sound_device.write(sound)

    def _cancel_sound(self):
        self._run_sound(0, 1)

    def _get_load_packet(self, cmd):
        packet = self._load_packet
        self._command_system_id = (self._command_system_id % 255) + 1
        packet[5] = self._command_system_id & 0xff
        packet[6] = cmd & 0xff
        self._fill_checksum(packet, 7)
        return packet

    def _set_balance(self, balance):
        self._balance = balance

    def _get_or_create_quadrant_array(self, quadrant, sz):
        if self._lidar_values[quadrant] is None or len(self._lidar_values[quadrant]) != sz:
            self._lidar_values[quadrant] = [65535] * sz
        return self._lidar_values[quadrant]

    def _get_or_create_lidar_array(self, sz):
        if self._lidar_arr is None or len(self._lidar_arr) != sz:
            self._lidar_arr = [65535] * sz
        return self._lidar_arr

    def _clear_lidar(self):
        self._lidar_ready = False
        if self._lidar_arr is not None:
            for i in range(len(self._lidar_arr)):
                self._lidar_arr[i] = 65535
        for i in range(8):
            self._lidar_directions[i] = 65535

    def _get_or_create_basic_packet(self):
        if self._basic_packet is None:
            self._basic_packet = [0] * 27
        return self._basic_packet

    def _get_or_create_imu_packet(self):
        if self._imu_packet is None:
            self._imu_packet = [0] * 15
        return self._imu_packet

    def _get_imu_last_packet(self, packet):
        if self._imu_last_packet is None:
            self._imu_last_packet = [0] * 15
        p = self._imu_last_packet
        for i in range(15):
            p[i] = packet[i]
        return p

    def _get_or_create_lidar_packet(self):
        if self._lidar_packet is None:
            self._lidar_packet = [0] * 11
        return self._lidar_packet

    def _get_lidar_last_packet(self, packet):
        if self._lidar_last_packet is None:
            self._lidar_last_packet = [0] * 11
        p = self._lidar_last_packet
        for i in range(11):
            p[i] = packet[i]
        return p

    def _get_motor_accel(self, value):
        if value == 0: return 0x0f # no accel
        elif value == 1: return 1
        elif value == 2: return 2
        elif value == 3: return 3
        elif value == 4: return 4
        elif value == 5: return 5 # default
        elif value == 6: return 7
        elif value == 7: return 9
        elif value == 8: return 11
        elif value == 9: return 14
        return 5

    def _get_servo_speed(self, value):
        if value == 1: return 1
        elif value == 2: return 2
        elif value == 3: return 3
        elif value == 4: return 4
        elif value == 5: return 6 # default
        elif value == 6: return 8
        elif value == 7: return 10
        return 6

    def _fill_checksum(self, packet, sz):
        suma = 0
        sumb = 0
        for i in range(sz):
            suma += packet[i]
            sumb += suma
        packet[sz] = suma & 0xff
        packet[sz+1] = sumb & 0xff

    def _request_bluetooth_reset(self):
        self._bluetooth_reset_count = 4

    def _encode_motoring_packet(self):
        if self._bluetooth_reset_count > 0:
            self._bluetooth_reset_count -= 1
            return self._get_load_packet(0xF0)
        if self._imu_send_more_count > 0:
            self._imu_send_more_count -= 1
            self._packet_sent = 2 # imu
            if self._imu_last_packet is not None:
                return self._imu_last_packet
        if self._lidar_send_more_count > 0:
            self._lidar_send_more_count -= 1
            self._packet_sent = 3 # lidar
            if self._lidar_last_packet is not None:
                return self._lidar_last_packet
        
        if (self._config_accelerometer_odr_bw_written or self._config_accelerometer_range_written or self._config_gyroscope_odr_bw_written or self._config_gyroscope_range_written or self._config_magnetometer_odr_written or self._config_magnetometer_repetition_xy_written or self._config_magnetometer_repetition_z_written) and self._packet_sent != 2:
            self._packet_sent = 2 # imu
            if self._config_accelerometer_odr_bw_written or self._config_accelerometer_range_written:
                self._command_accelerometer_id = (self._command_accelerometer_id % 3) + 1
            if self._config_gyroscope_odr_bw_written or self._config_gyroscope_range_written:
                self._command_gyroscope_id = (self._command_gyroscope_id % 3) + 1
            if self._config_magnetometer_odr_written or self._config_magnetometer_repetition_xy_written or self._config_magnetometer_repetition_z_written:
                self._command_magnetometer_id = (self._command_magnetometer_id % 3) + 1
            self._config_accelerometer_odr_bw_written = False
            self._config_accelerometer_range_written = False
            self._config_gyroscope_odr_bw_written = False
            self._config_gyroscope_range_written = False
            self._config_magnetometer_odr_written = False
            self._config_magnetometer_repetition_xy_written = False
            self._config_magnetometer_repetition_z_written = False
            packet = self._get_or_create_imu_packet()
            packet[0] = 0x52
            packet[1] = 0x49
            packet[2] = 0x0A
            packet[3] = 0x20
            packet[4] = 0x08
            packet[5] = ((self._command_magnetometer_id & 0x03) << 4) | ((self._command_accelerometer_id & 0x03) << 2) | (self._command_gyroscope_id & 0x03)
            packet[6] = self._config_gyroscope_odr_bw & 0xff
            packet[7] = self._config_gyroscope_range & 0xff
            packet[8] = self._config_accelerometer_odr_bw & 0xff
            packet[9] = self._config_accelerometer_range & 0xff
            packet[10] = self._config_magnetometer_odr & 0xff
            packet[11] = ((self._config_magnetometer_repetition_xy - 1) // 2) & 0xff
            packet[12] = (self._config_magnetometer_repetition_z - 1) & 0xff
            self._fill_checksum(packet, 13)
            self._imu_last_packet = self._get_imu_last_packet(packet)
            self._imu_send_more_count = 4
            return packet
        
        if self._enable_lidar_written and self._packet_sent != 3:
            self._enable_lidar_written = False
            self._packet_sent = 3 # lidar
            self._command_lidar_id = (self._command_lidar_id % 255) + 1
            packet = self._get_or_create_lidar_packet()
            packet[0] = 0x52
            packet[1] = 0x49
            packet[2] = 0x06
            packet[3] = 0x30
            packet[4] = 0x04
            packet[5] = 0xfd
            packet[6] = 0xe0
            packet[7] = self._command_lidar_id & 0xff
            if self._lidar_deactivating:
                self._lidar_deactivating = False
                packet[8] = 0xf0
                self._clear_lidar()
            elif self._enable_lidar > 0:
                packet[8] = 0x0f
            else:
                packet[8] = 0xf0
                self._clear_lidar()
            self._fill_checksum(packet, 9)
            self._lidar_last_packet = self._get_lidar_last_packet(packet)
            self._lidar_send_more_count = 4
            return packet
        
        packet = self._get_or_create_basic_packet()
        packet[0] = 0x52
        packet[1] = 0x49
        packet[2] = 0x16
        packet[3] = 0x10
        packet[4] = 0x14
        self._command_basic_id = (self._command_basic_id % 255) + 1
        packet[5] = self._command_basic_id & 0xff
        if self._reset_encoder_written:
            self._reset_encoder_written = False
            self._command_reset_encoder_id = (self._command_reset_encoder_id % 3) + 1
        packet[6] = ((self._command_reset_encoder_id & 0x03) << 6) | ((self._config_motor_sustain & 0x01) << 5) | (self._get_motor_accel(self._config_motor_acceleration) & 0x0f)
        
        left_wheel = self._left_wheel
        right_wheel = self._right_wheel
        if left_wheel < 0:
            left_wheel = int(left_wheel * 30 - 0.5)
        else:
            left_wheel = int(left_wheel * 30 + 0.5)
        if right_wheel < 0:
            right_wheel = int(right_wheel * 30 * (self._balance + 200) / 200.0 - 0.5)
        else:
            right_wheel = int(right_wheel * 30 * (self._balance + 200) / 200.0 + 0.5)
        packet[7] = left_wheel & 0xff
        packet[8] = (left_wheel >> 8) & 0xff
        packet[9] = right_wheel & 0xff
        packet[10] = (right_wheel >> 8) & 0xff
        self._wheel_pulse = self._pulse
        if self._pulse_written:
            if self._wheel_pulse != 0 or self._wheel_pulse_prev != 0:
                self._wheel_id = (self._wheel_id % 255) + 1
            if self._wheel_pulse > 0:
                self._wheel_event = 1
            else:
                self._wheel_event = 0
            self._wheel_pulse_prev = self._wheel_pulse
            self._pulse_written = False
        packet[11] = self._wheel_id & 0xff
        packet[12] = self._wheel_pulse & 0xff
        packet[13] = (self._wheel_pulse >> 8) & 0xff
        tmp = Util.round(self._buzzer * 100)
        packet[14] = tmp & 0xff
        packet[15] = (tmp >> 8) & 0xff
        packet[16] = (tmp >> 16) & 0xff
        packet[17] = self._note & 0xff
        tmp = self._get_sound(self._sound)
        if self._sound_written:
            if tmp > 0:
                self._sound_flag ^= 0x80
                self._sound_event = 1
            else:
                self._sound_event = 0
            self._sound_written = False
        tmp |= self._sound_flag
        packet[18] = tmp & 0xff
        packet[19] = self._get_servo_speed(self._servo_speed_a) & 0xff
        packet[20] = self._servo_output_a & 0xff
        packet[21] = self._get_servo_speed(self._servo_speed_b) & 0xff
        packet[22] = self._servo_output_b & 0xff
        packet[23] = self._get_servo_speed(self._servo_speed_c) & 0xff
        packet[24] = self._servo_output_c & 0xff
        self._fill_checksum(packet, 25)
        self._packet_sent = 1
        return packet

    def _hex_to_float32(self, value):
        if value > 0 or value < 0:
            value = "{0:b}".format(value)
            sign = -1 if value[0] == '1' else 1
            exp = int(value[1:9], 2) - 127
            mantissa = "1" + value[9:]
            float32 = 0
            for i in range(len(mantissa)):
                float32 += 2**exp if mantissa[i] == '1' else 0
                exp -= 1
            return float32 * sign
        else:
            return 0

    def _decode_sensory_packet(self, packet):
        if len(packet) < 2: return False
        self._packet_received = 0
        if packet[0] == 0x10: # basic
            length = packet[1] & 0xff
            if length != 29: return False
            
            value = packet[3] & 0xff
            value |= (packet[4] & 0xff) << 8
            self._timestamp_basic_device._put(value)
            
            # left encoder
            value = packet[5] & 0xff
            value |= (packet[6] & 0xff) << 8
            value |= (packet[7] & 0xff) << 16
            value |= (packet[8] & 0xff) << 24
            if value > 0x7fffffff: value -= 0x100000000
            self._left_encoder_device._put(value)
            
            # right encoder
            value = packet[9] & 0xff
            value |= (packet[10] & 0xff) << 8
            value |= (packet[11] & 0xff) << 16
            value |= (packet[12] & 0xff) << 24
            if value > 0x7fffffff: value -= 0x100000000
            self._right_encoder_device._put(value)
            
            # temperature
            value = packet[13] & 0xff
            if value > 0x7f: value -= 0x100
            value = Util.round(value / 2.0 + 23)
            self._temperature_device._put(value)
            
            # signal strength
            value = (packet[14] & 0xff) - 0x100
            self._signal_strength_device._put(value)
            
            # battery state
            value = packet[16] & 0xff
            state = (value >> 1) & 0x03
            if state == 1: state = 2 # middle
            elif state == 2: state = 1 # low
            elif state == 3: state = 0 # empty
            else: state = 3 # normal
            if state != self._event_battery_state:
                self._battery_state_device._put(state, self._event_battery_state != -1)
                self._event_battery_state = state
            
            # charge state
            state = value & 0x01
            if state != self._event_charge_state:
                self._charge_state_device._put(state, self._event_charge_state != -1)
                self._event_charge_state = state
            
            # wheel state
            value = packet[17] & 0xff
            id = (value >> 1) & 0x03
            if self._wheel_event == 1:
                if id != self._wheel_state_id and self._wheel_state_id != -1:
                    self._wheel_state_device._put_empty()
                    self._wheel_event = 0
            self._wheel_state_id = id
            
            # sound state
            value = packet[18] & 0xff
            id = (value >> 1) & 0x03
            if self._sound_event == 1:
                if id != self._sound_state_id and self._sound_state_id != -1:
                    self._sound_event = 0
                    if self._current_sound > 0:
                        if self._sound_repeat < 0:
                            self._run_sound(self._current_sound, -1)
                        elif self._sound_repeat > 1:
                            self._sound_repeat -= 1
                            self._run_sound(self._current_sound, self._sound_repeat)
                        else:
                            self._current_sound = 0
                            self._sound_repeat = 1
                            self._sound_state_device._put_empty()
                    else:
                        self._current_sound = 0
                        self._sound_repeat = 1
            self._sound_state_id = id
            
            value = packet[20] & 0xff
            if value < 0: value = 0
            elif value > 180: value = 180
            self._servo_input_a_device._put(value)
            value = packet[22] & 0xff
            if value < 0: value = 0
            elif value > 180: value = 180
            self._servo_input_b_device._put(value)
            value = packet[24] & 0xff
            if value < 0: value = 0
            elif value > 180: value = 180
            self._servo_input_c_device._put(value)
            self._packet_received = 1 # basic
            return True
        elif packet[0] == 0x20:
            length = packet[1] & 0xff
            if length < 10: return False
            
            timestamp = packet[3] & 0xff
            timestamp |= (packet[4] & 0xff) << 8
            self._timestamp_imu_device._put(timestamp)
            
            gyroscope_range = 250
            value = packet[6] & 0xff
            if value == 0x01: gyroscope_range = 125
            elif value == 0x02: gyroscope_range = 250 # default
            elif value == 0x04: gyroscope_range = 500
            elif value == 0x08: gyroscope_range = 1000
            elif value == 0x10: gyroscope_range = 2000
            self._gyroscope_range_device._put(gyroscope_range, gyroscope_range != self._event_gyroscope_range)
            self._event_gyroscope_range = gyroscope_range
            
            accelerometer_range = 2
            value = packet[8] & 0xff
            if value == 0x01: accelerometer_range = 2 # default
            elif value == 0x02: accelerometer_range = 4
            elif value == 0x04: accelerometer_range = 8
            elif value == 0x08: accelerometer_range = 16
            self._accelerometer_range_device._put(accelerometer_range, accelerometer_range != self._event_accelerometer_range)
            self._event_accelerometer_range = accelerometer_range
            
            index = 12
            while index < length + 2:
                value = packet[index]
                index += 1
                id = (value >> 4) & 0x0f
                idx = value & 0x0f
                if id == 1: # gyroscope
                    self._gyroscope_device._put_at(0, idx)
                    raw_x = packet[index] & 0xff
                    raw_x |= (packet[index+1] & 0xff) << 8
                    if raw_x > 0x7fff: raw_x -= 0x10000
                    self._gyroscope_device._put_at(1, raw_x)
                    raw_y = packet[index+2] & 0xff
                    raw_y |= (packet[index+3] & 0xff) << 8
                    if raw_y > 0x7fff: raw_y -= 0x10000
                    self._gyroscope_device._put_at(2, raw_y)
                    raw_z = packet[index+4] & 0xff
                    raw_z |= (packet[index+5] & 0xff) << 8
                    if raw_z > 0x7fff: raw_z -= 0x10000
                    self._gyroscope_device._put_at(3, raw_z)
                    index += 6
                    if self._raw_gyroscope_listener is not None:
                        if self._raw_gyroscope_interpolator is not None:
                            self._raw_gyroscope_interpolator.interpolate(self._raw_gyroscope_listener, idx, timestamp, raw_x, raw_y, raw_z)
                        self._raw_gyroscope_listener(idx, timestamp, raw_x, raw_y, raw_z)
                    if self._gyroscope_listener is not None:
                        scale = gyroscope_range / 32768.0
                        raw_x *= scale
                        raw_y *= scale
                        raw_z *= scale
                        if self._gyroscope_interpolator is not None:
                            self._gyroscope_interpolator.interpolate(self._gyroscope_listener, idx, timestamp, raw_x, raw_y, raw_z)
                        self._gyroscope_listener(idx, timestamp, raw_x, raw_y, raw_z)
                elif id == 2: # accelerometer
                    self._accelerometer_device._put_at(0, idx)
                    raw_x = packet[index] & 0xff
                    raw_x |= (packet[index+1] & 0x0f) << 8
                    if raw_x > 0x7ff: raw_x -= 0x1000
                    raw_x *= -1
                    self._accelerometer_device._put_at(1, raw_x)
                    raw_y = packet[index+2] & 0xff
                    raw_y |= (packet[index+3] & 0x0f) << 8
                    if raw_y > 0x7ff: raw_y -= 0x1000
                    raw_y *= -1
                    self._accelerometer_device._put_at(2, raw_y)
                    raw_z = packet[index+4] & 0xff
                    raw_z |= (packet[index+5] & 0x0f) << 8
                    if raw_z > 0x7ff: raw_z -= 0x1000
                    raw_z *= -1
                    self._accelerometer_device._put_at(3, raw_z)
                    index += 7 # temperature
                    
                    # tilt
                    scale = accelerometer_range / 2048.0
                    acc_x = raw_x * scale
                    acc_y = raw_y * scale
                    acc_z = raw_z * scale
                    if acc_z < 0.5 and acc_x > 0.5 and acc_y > -0.25 and acc_y < 0.25: value = 1
                    elif acc_z < 0.5 and acc_x < -0.5 and acc_y > -0.25 and acc_y < 0.25: value = -1
                    elif acc_z < 0.5 and acc_y > 0.5 and acc_x > -0.25 and acc_x < 0.25: value = 2
                    elif acc_z < 0.5 and acc_y < -0.5 and acc_x > -0.25 and acc_x < 0.25: value = -2
                    elif acc_z > 0.75 and acc_x > -0.5 and acc_x < 0.5 and acc_y > -0.5 and acc_y < 0.5: value = 3
                    elif acc_z < -0.75 and acc_x > -0.25 and acc_x < 0.25 and acc_y > -0.25 and acc_y < 0.25: value = -3
                    else: value = 0
                    if value != self._event_tilt:
                        self._tilt_device._put(value, self._event_tilt != -4)
                        self._event_tilt = value
                    
                    if self._raw_accelerometer_listener is not None:
                        if self._raw_accelerometer_interpolator is not None:
                            self._raw_accelerometer_interpolator.interpolate(self._raw_accelerometer_listener, idx, timestamp, raw_x, raw_y, raw_z)
                        self._raw_accelerometer_listener(idx, timestamp, raw_x, raw_y, raw_z)
                    if self._accelerometer_listener is not None:
                        if self._accelerometer_interpolator is not None:
                            self._accelerometer_interpolator.interpolate(self._accelerometer_listener, idx, timestamp, acc_x, acc_y, acc_z)
                        self._accelerometer_listener(idx, timestamp, acc_x, acc_y, acc_z)
                elif id == 3: # magnetometer
                    '''self._magnetometer_device._put_at(0, idx)
                    value = packet[index] & 0xff
                    value |= (packet[index+1] & 0xff) << 8
                    value |= (packet[index+2] & 0xff) << 16
                    value |= (packet[index+3] & 0xff) << 24
                    mag_x = -self._hex_to_float32(value)
                    self._magnetometer_device._put_at(1, mag_x)
                    value = packet[index+4] & 0xff
                    value |= (packet[index+5] & 0xff) << 8
                    value |= (packet[index+6] & 0xff) << 16
                    value |= (packet[index+7] & 0xff) << 24
                    mag_y = -self._hex_to_float32(value)
                    self._magnetometer_device._put_at(2, mag_y)
                    value = packet[index+8] & 0xff
                    value |= (packet[index+9] & 0xff) << 8
                    value |= (packet[index+10] & 0xff) << 16
                    value |= (packet[index+11] & 0xff) << 24
                    mag_z = -self._hex_to_float32(value)
                    self._magnetometer_device._put_at(3, mag_z)
                    deg = Util.round(math.atan2(mag_y, mag_x) * 180 / math.pi + 180)
                    if deg < 1 or deg > 359: deg = 0
                    self._compass_device._put(deg)'''
                    index += 12
                elif id == 0:
                    break
            self._packet_received = 2 # imu
            return True
        elif packet[0] == 0x30:
            if self._enable_lidar == 0: return False
            length = packet[1] & 0xff
            if length < 1: return False
            if packet[2] == 0xfe:
                if length < 2: return False
                if packet[3] == 0x10:
                    if length < 9: return False
                    # 4: index, 5: system state, 8: output rate
                    quadrant = packet[6] & 0xff
                    if quadrant < 1 or quadrant > 4: return False
                    self._resolution_device._put((packet[7] & 0xff) / 10.0)
                    sz = packet[9] & 0xff
                    sz |= (packet[10] & 0xff) << 8
                    arr = self._get_or_create_quadrant_array(quadrant-1, sz)
                    for i in range(sz):
                        value = packet[2 * i + 11] & 0xff
                        value |= (packet[2 * i + 12] & 0xff) << 8
                        if value >= 65280 and value < 65535:
                            if self._lidar_mode == Beagle.LIDAR_ZERO:
                                value = 0
                            elif self._lidar_mode == Beagle.LIDAR_TRUNC:
                                value = 80
                            else:
                                value &= 0xff
                        arr[i] = value
                    self._lidar_valid[quadrant-1] = True
                    if quadrant == 4:
                        valid = True
                        for i in range(4):
                            if self._lidar_valid[i] == False or self._lidar_values[i] is None:
                                valid = False
                            self._lidar_valid[i] = False
                        if valid:
                            self._lidar_ready = True
                            sz = 0
                            for i in range(4):
                                sz += len(self._lidar_values[i])
                            arr = self._get_or_create_lidar_array(sz)
                            index = 0
                            for i in range(4):
                                values = self._lidar_values[i]
                                for val in values:
                                    arr[index] = val
                                    index += 1
                            self._lidar_device._put_array(arr)
                            length = len(arr)
                            if length > 16:
                                sz = length // 8
                                start = -(sz // 2)
                                for i in range(8):
                                    self._lidar_directions[i] = self._average_lidar(arr, start, sz)
                                    start += sz
            self._packet_received = 3
            return True

    def _set_raw_accelerometer_listener(self, listener, interpolation=None):
        self._raw_accelerometer_listener = listener
        self._raw_accelerometer_interpolator = BeagleInterpolator(interpolation)

    def _set_accelerometer_listener(self, listener, interpolation=None):
        self._accelerometer_listener = listener
        self._accelerometer_interpolator = BeagleInterpolator(interpolation)

    def _set_raw_gyroscope_listener(self, listener, interpolation=None):
        self._raw_gyroscope_listener = listener
        self._raw_gyroscope_interpolator = BeagleInterpolator(interpolation)

    def _set_gyroscope_listener(self, listener, interpolation=None):
        self._gyroscope_listener = listener
        self._gyroscope_interpolator = BeagleInterpolator(interpolation)

    def _set_lidar_mode(self, mode):
        self._lidar_mode = mode

    def _average_lidar(self, data, start, size):
        length = len(data)
        sumval = 0.0
        count = 0
        for i in range(start, start + size):
            val = data[i+length if i < 0 else i]
            if val != 65535:
                sumval += val
                count += 1
        return 65535 if count == 0 else sumval / count

    def _get_lidar_directions(self):
        return self._lidar_directions

    def _is_lidar_ready(self):
        return self._lidar_ready

    def _wait_until_lidar_ready(self):
        while self._lidar_ready == False:
            time.sleep(0.01)

    def _receive(self, connector):
        if connector:
            packets = connector.read()
            if packets:
                for packet in packets:
                    if self._decode_sensory_packet(packet):
                        if self._ready == False:
                            self._ready = True
                            Runner.register_checked()
                        self._notify_sensory_device_data_changed()
                return True
        return False

    def _send(self, connector):
        if connector:
            packet = self._encode_motoring_packet()
            connector.write(packet)
