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

from roboid.runner import Runner
from roboid.util import Util
from roboid.model import DeviceType
from roboid.model import DataType
from roboid.model import Roboid
from roboid.connector import Result
from roboid.hamster_s import HamsterS
from roboid.serial_connector import SerialConnector


class HamsterSConnectionChecker(object):
    def __init__(self, roboid):
        self._roboid = roboid

    def check(self, info):
        return info[2] == "0E"


class HamsterSRoboid(Roboid):
    _SOUNDS = {
        HamsterS.SOUND_OFF: 0x00,
        HamsterS.SOUND_BEEP: 0x01,
        HamsterS.SOUND_RANDOM_BEEP: 0x05,
        HamsterS.SOUND_NOISE: 0x07,
        HamsterS.SOUND_SIREN: 0x09,
        HamsterS.SOUND_ENGINE: 0x0b,
        HamsterS.SOUND_CHOP: 0x12,
        HamsterS.SOUND_ROBOT: 0x20,
        HamsterS.SOUND_DIBIDIBIDIP: 0x21,
        HamsterS.SOUND_GOOD_JOB: 0x23,
        HamsterS.SOUND_HAPPY: 0x30,
        HamsterS.SOUND_ANGRY: 0x31,
        HamsterS.SOUND_SAD: 0x32,
        HamsterS.SOUND_SLEEP: 0x33,
        HamsterS.SOUND_MARCH: 0x34,
        HamsterS.SOUND_BIRTHDAY: 0x35
    }

    def __init__(self, index):
        super(HamsterSRoboid, self).__init__(HamsterS.ID, "HamsterS", 0x00e00000)
        self._index = index
        self._connector = None
        self._ready = False
        self._thread = None
        self._thread_lock = threading.Lock()

        self._left_wheel = 0
        self._right_wheel = 0
        self._left_red = 0
        self._left_green = 0
        self._left_blue = 0
        self._right_red = 0
        self._right_green = 0
        self._right_blue = 0
        self._buzzer = 0
        self._output_a = 0
        self._output_b = 0
        self._pulse = 0
        self._note = 0
        self._sound = 0
        self._line_tracer_mode = 0
        self._line_tracer_gain = 4
        self._line_tracer_speed = 5
        self._io_mode_a = 0
        self._io_mode_b = 0
        self._write_serial_data = [0] * 19
        self._read_serial_data = [0] * 19
        self._motor_mode = 0
        self._config_proximity = 2
        self._config_gravity = 0
        self._config_band_width = 0

        self._pulse_written = False
        self._note_written = False
        self._sound_written = False
        self._line_tracer_mode_written = False
        self._line_tracer_gain_written = False
        self._line_tracer_speed_written = False
        self._io_mode_a_written = False
        self._io_mode_b_written = False
        self._write_serial_written = False
        self._motor_mode_written = False
        self._config_proximity_written = False
        self._config_gravity_written = False
        self._config_band_width_written = False

        self._light = 0
        self._temperature = 0

        self._wheel_id = 0
        self._wheel_pulse = 0
        self._wheel_pulse_prev = -1
        self._wheel_event = 0
        self._wheel_state = 0
        self._wheel_count = 0
        self._wheel_move = False
        self._wheel_move_count = 0

        self._current_sound = 0
        self._sound_repeat = 1
        self._sound_flag = 0
        self._sound_event = 0
        self._sound_state = 0
        self._sound_count = 0

        self._line_tracer_id = 0
        self._line_tracer_event = 0
        self._line_tracer_state = 0
        self._line_tracer_count = 0

        self._event_free_fall_id = -1
        self._event_tap_id = -1
        self._event_tilt = -4
        self._event_serial_id = -1
        self._event_pulse_count = -1
        self._event_battery_state = -1

        self._command_serial_id = 0

        self._port_ack_id = -1
        self._port_serial = False
        self._serial_send_id = 0
        self._serial_send_prev_id = 0
        self._packet_sent = 0
        self._packet_received = 0
        
        self._write_queue = None
        self._read_queue = None
        self._write_serial_id = 0

        self._create_model()

    def _create_model(self):
        from roboid.hamster_s import HamsterS
        dict = self._device_dict = {}
        dict[HamsterS.LEFT_WHEEL] = self._left_wheel_device = self._add_device(HamsterS.LEFT_WHEEL, "LeftWheel", DeviceType.EFFECTOR, DataType.INTEGER, 1, -100, 100, 0)
        dict[HamsterS.RIGHT_WHEEL] = self._right_wheel_device = self._add_device(HamsterS.RIGHT_WHEEL, "RightWheel", DeviceType.EFFECTOR, DataType.INTEGER, 1, -100, 100, 0)
        dict[HamsterS.LEFT_RGB] = self._left_rgb_device = self._add_device(HamsterS.LEFT_RGB, "LeftRgb", DeviceType.EFFECTOR, DataType.INTEGER, 3, 0, 255, 0)
        dict[HamsterS.RIGHT_RGB] = self._right_rgb_device = self._add_device(HamsterS.RIGHT_RGB, "RightRgb", DeviceType.EFFECTOR, DataType.INTEGER, 3, 0, 255, 0)
        dict[HamsterS.BUZZER] = self._buzzer_device = self._add_device(HamsterS.BUZZER, "Buzzer", DeviceType.EFFECTOR, DataType.FLOAT, 1, 0, 167746.0, 0)
        dict[HamsterS.OUTPUT_A] = self._output_a_device = self._add_device(HamsterS.OUTPUT_A, "OutputA", DeviceType.EFFECTOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[HamsterS.OUTPUT_B] = self._output_b_device = self._add_device(HamsterS.OUTPUT_B, "OutputB", DeviceType.EFFECTOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[HamsterS.PULSE] = self._pulse_device = self._add_device(HamsterS.PULSE, "Pulse", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 65535, 0)
        dict[HamsterS.NOTE] = self._note_device = self._add_device(HamsterS.NOTE, "Note", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 88, 0)
        dict[HamsterS.SOUND] = self._sound_device = self._add_device(HamsterS.SOUND, "Sound", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 127, 0)
        dict[HamsterS.LINE_TRACER_MODE] = self._line_tracer_mode_device = self._add_device(HamsterS.LINE_TRACER_MODE, "LineTracerMode", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 15, 0)
        dict[HamsterS.LINE_TRACER_GAIN] = self._line_tracer_gain_device = self._add_device(HamsterS.LINE_TRACER_GAIN, "LineTracerGain", DeviceType.COMMAND, DataType.INTEGER, 1, 1, 10, 4)
        dict[HamsterS.LINE_TRACER_SPEED] = self._line_tracer_speed_device = self._add_device(HamsterS.LINE_TRACER_SPEED, "LineTracerSpeed", DeviceType.COMMAND, DataType.INTEGER, 1, 1, 10, 5)
        dict[HamsterS.IO_MODE_A] = self._io_mode_a_device = self._add_device(HamsterS.IO_MODE_A, "IoModeA", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 255, 0)
        dict[HamsterS.IO_MODE_B] = self._io_mode_b_device = self._add_device(HamsterS.IO_MODE_B, "IoModeB", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 255, 0)
        dict[HamsterS.WRITE_SERIAL] = self._write_serial_device = self._add_device(HamsterS.WRITE_SERIAL, "WriteSerial", DeviceType.COMMAND, DataType.INTEGER, 19, 0, 255, 0)
        dict[HamsterS.MOTOR_MODE] = self._motor_mode_device = self._add_device(HamsterS.MOTOR_MODE, "MotorMode", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 3, 0)
        dict[HamsterS.CONFIG_PROXIMITY] = self._config_proximity_device = self._add_device(HamsterS.CONFIG_PROXIMITY, "ConfigProximity", DeviceType.COMMAND, DataType.INTEGER, 1, 1, 7, 2)
        dict[HamsterS.CONFIG_GRAVITY] = self._config_gravity_device = self._add_device(HamsterS.CONFIG_GRAVITY, "ConfigGravity", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 3, 0)
        dict[HamsterS.CONFIG_BAND_WIDTH] = self._config_band_width_device = self._add_device(HamsterS.CONFIG_BAND_WIDTH, "ConfigBandWidth", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 7, 0)
        dict[HamsterS.SIGNAL_STRENGTH] = self._signal_strength_device = self._add_device(HamsterS.SIGNAL_STRENGTH, "SignalStrength", DeviceType.SENSOR, DataType.INTEGER, 1, -128, 0, 0)
        dict[HamsterS.LEFT_PROXIMITY] = self._left_proximity_device = self._add_device(HamsterS.LEFT_PROXIMITY, "LeftProximity", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[HamsterS.RIGHT_PROXIMITY] = self._right_proximity_device = self._add_device(HamsterS.RIGHT_PROXIMITY, "RightProximity", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[HamsterS.LEFT_FLOOR] = self._left_floor_device = self._add_device(HamsterS.LEFT_FLOOR, "LeftFloor", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[HamsterS.RIGHT_FLOOR] = self._right_floor_device = self._add_device(HamsterS.RIGHT_FLOOR, "RightFloor", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[HamsterS.ACCELERATION] = self._acceleration_device = self._add_device(HamsterS.ACCELERATION, "Acceleration", DeviceType.SENSOR, DataType.INTEGER, 3, -32768, 32767, 0)
        dict[HamsterS.LIGHT] = self._light_device = self._add_device(HamsterS.LIGHT, "Light", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 65535, 0)
        dict[HamsterS.TEMPERATURE] = self._temperature_device = self._add_device(HamsterS.TEMPERATURE, "Temperature", DeviceType.SENSOR, DataType.INTEGER, 1, -41, 87, 0)
        dict[HamsterS.INPUT_A] = self._input_a_device = self._add_device(HamsterS.INPUT_A, "InputA", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[HamsterS.INPUT_B] = self._input_b_device = self._add_device(HamsterS.INPUT_B, "InputB", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[HamsterS.FREE_FALL] = self._free_fall_device = self._add_device(HamsterS.FREE_FALL, "FreeFall", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[HamsterS.TAP] = self._tap_device = self._add_device(HamsterS.TAP, "Tap", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[HamsterS.TILT] = self._tilt_device = self._add_device(HamsterS.TILT, "Tilt", DeviceType.EVENT, DataType.INTEGER, 1, -3, 3, 0)
        dict[HamsterS.READ_SERIAL] = self._read_serial_device = self._add_device(HamsterS.READ_SERIAL, "ReadSerial", DeviceType.EVENT, DataType.INTEGER, 19, 0, 255, 0)
        dict[HamsterS.PULSE_COUNT] = self._pulse_count_device = self._add_device(HamsterS.PULSE_COUNT, "PulseCount", DeviceType.EVENT, DataType.INTEGER, 1, 0, 65535, 0)
        dict[HamsterS.WHEEL_STATE] = self._wheel_state_device = self._add_device(HamsterS.WHEEL_STATE, "WheelState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 3, 0)
        dict[HamsterS.SOUND_STATE] = self._sound_state_device = self._add_device(HamsterS.SOUND_STATE, "SoundState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[HamsterS.LINE_TRACER_STATE] = self._line_tracer_state_device = self._add_device(HamsterS.LINE_TRACER_STATE, "LineTracerState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 3, 0)
        dict[HamsterS.BATTERY_STATE] = self._battery_state_device = self._add_device(HamsterS.BATTERY_STATE, "BatteryState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 2, 2)
        dict[HamsterS.SERIAL_STATE] = self._serial_state_device = self._add_device(HamsterS.SERIAL_STATE, "SerialState", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)

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

    def _init(self, port_name=None):
        Runner.register_required()
        self._running = True
        self._releasing = 0
        thread = threading.Thread(target=self._run)
        self._thread = thread
        thread.daemon = True
        thread.start()

        tag = "HamsterS[{}]".format(self._index)
        self._connector = SerialConnector(tag, HamsterSConnectionChecker(self))
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
            super(HamsterSRoboid, self)._dispose()
            self._release()

    def _reset(self):
        super(HamsterSRoboid, self)._reset()

        self._left_wheel = 0
        self._right_wheel = 0
        self._left_red = 0
        self._left_green = 0
        self._left_blue = 0
        self._right_red = 0
        self._right_green = 0
        self._right_blue = 0
        self._buzzer = 0
        self._output_a = 0
        self._output_b = 0
        self._pulse = 0
        self._note = 0
        self._sound = 0
        self._line_tracer_mode = 0
        self._line_tracer_gain = 4
        self._line_tracer_speed = 5
        self._io_mode_a = 0
        self._io_mode_b = 0
        self._motor_mode = 0
        self._config_proximity = 2
        self._config_gravity = 0
        self._config_band_width = 0

        self._pulse_written = False
        self._note_written = False
        self._sound_written = False
        self._line_tracer_mode_written = False
        self._line_tracer_gain_written = False
        self._line_tracer_speed_written = False
        self._io_mode_a_written = False
        self._io_mode_b_written = False
        self._write_serial_written = False
        self._motor_mode_written = False
        self._config_proximity_written = False
        self._config_gravity_written = False
        self._config_band_width_written = False

        self._light = 0
        self._temperature = 0

        self._wheel_pulse = 0
        self._wheel_pulse_prev = -1
        self._wheel_event = 0
        self._wheel_state = 0
        self._wheel_count = 0
        self._wheel_move = False
        self._wheel_move_count = 0

        self._current_sound = 0
        self._sound_repeat = 1
        self._sound_event = 0
        self._sound_state = 0
        self._sound_count = 0

        self._line_tracer_event = 0
        self._line_tracer_state = 0
        self._line_tracer_count = 0

        self._event_free_fall_id = -1
        self._event_tap_id = -1
        self._event_tilt = -4
        self._event_serial_id = -1
        self._event_pulse_count = -1
        self._event_battery_state = -1

        self._port_ack_id = -1
        self._port_serial = False
        self._serial_send_id = 0
        self._serial_send_prev_id = 0
        self._packet_sent = 0
        self._packet_received = 0
        
        if self._write_queue is not None:
            self._write_queue.reset()
        if self._read_queue is not None:
            self._read_queue.reset()

    def _request_motoring_data(self):
        with self._thread_lock:
            self._left_wheel = self._left_wheel_device.read()
            self._right_wheel = self._right_wheel_device.read()
            self._left_red = self._left_rgb_device.read(0)
            self._left_green = self._left_rgb_device.read(1)
            self._left_blue = self._left_rgb_device.read(2)
            self._right_red = self._right_rgb_device.read(0)
            self._right_green = self._right_rgb_device.read(1)
            self._right_blue = self._right_rgb_device.read(2)
            self._buzzer = self._buzzer_device.read()
            self._output_a = self._output_a_device.read()
            self._output_b = self._output_b_device.read()
            if self._pulse_device._is_written():
                self._pulse = self._pulse_device.read()
                self._pulse_written = True
            if self._note_device._is_written():
                self._note = self._note_device.read()
                self._note_written = True
            if self._sound_device._is_written():
                self._sound = self._sound_device.read()
                self._sound_written = True
            if self._line_tracer_mode_device._is_written():
                self._line_tracer_mode = self._line_tracer_mode_device.read()
                self._line_tracer_mode_written = True
            if self._line_tracer_gain_device._is_written():
                self._line_tracer_gain = self._line_tracer_gain_device.read()
                self._line_tracer_gain_written = True
            if self._line_tracer_speed_device._is_written():
                self._line_tracer_speed = self._line_tracer_speed_device.read()
                self._line_tracer_speed_written = True
            if self._io_mode_a_device._is_written():
                self._io_mode_a = self._io_mode_a_device.read()
                self._io_mode_a_written = True
            if self._io_mode_b_device._is_written():
                self._io_mode_b = self._io_mode_b_device.read()
                self._io_mode_b_written = True
            if self._write_serial_device._is_written():
                self._write_serial_device.read(self._write_serial_data)
                self._write_serial_written = True
            if self._motor_mode_device._is_written():
                self._motor_mode = self._motor_mode_device.read()
                self._motor_mode_written = True
            if self._config_proximity_device._is_written():
                self._config_proximity = self._config_proximity_device.read()
                self._config_proximity_written = True
            if self._config_gravity_device._is_written():
                self._config_gravity = self._config_gravity_device.read()
                self._config_gravity_written = True
            if self._config_band_width_device._is_written():
                self._config_band_width = self._config_band_width_device.read()
                self._config_band_width_written = True
        self._clear_written()

    def _get_sound(self, sound):
        if isinstance(sound, (int, float)):
            sound = int(sound)
            if sound in HamsterSRoboid._SOUNDS:
                return HamsterSRoboid._SOUNDS[sound]
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

    def _encode_motoring_packet(self, address):
        result = ""
        with self._thread_lock:
            if self._port_serial and self._write_serial_written and self._packet_sent != 3:
                self._write_serial_written = False
                self._packet_sent = 3
                self._serial_send_id = (self._serial_send_id % 255) + 1
                
                length = self._write_serial_data[0]
                if length > 0:
                    if length > 18: length = 18
                    self._command_serial_id = (self._command_serial_id % 15) + 1
                    result += self._to_hex(0x20 | (self._command_serial_id & 0x0f))
                    result += self._to_hex(length)
                    for i in range(1, length + 1):
                        result += self._to_hex(self._write_serial_data[i])
                    if length < 18:
                        for i in range(length + 1, 19):
                            result += "00"
                    result += "-"
                    result += address
                    result += "\r"
                    return result

            result = "10"
            if self._motor_mode == 1: result = "11"
            elif self._motor_mode == 2: result = "12"
            elif self._motor_mode == 3: result = "13"
            if self._left_wheel == 0 and self._right_wheel == 0:
                if self._wheel_move:
                    self._wheel_move_count += 1
                    if self._wheel_move_count > 5:
                        self._wheel_move = False
            else:
                self._wheel_move = True
                self._wheel_move_count = 0
            result += self._to_hex(self._left_wheel)
            result += self._to_hex(self._right_wheel)
            result += self._to_hex(self._left_red)
            result += self._to_hex(self._left_green)
            result += self._to_hex(self._left_blue)
            result += self._to_hex(self._right_red)
            result += self._to_hex(self._right_green)
            result += self._to_hex(self._right_blue)
            self._wheel_pulse = self._pulse
            if self._pulse_written:
                if self._pulse != 0 or self._wheel_pulse_prev != 0:
                    self._wheel_id = (self._wheel_id % 255) + 1
                self._wheel_count = 0
                if self._pulse > 0:
                    self._wheel_event = 1
                else:
                    self._wheel_event = 0
                self._wheel_pulse_prev = self._pulse
                self._pulse_written = False
            result += self._to_hex(self._wheel_id)
            result += self._to_hex2(self._pulse)
            temp = self._line_tracer_mode & 0x0f
            if temp > 7: temp += 1
            if self._line_tracer_mode_written:
                self._line_tracer_count = 0
                if temp > 0:
                    self._line_tracer_id = (self._line_tracer_id % 15) + 1
                    self._line_tracer_event = 1
                else:
                    self._line_tracer_event = 0
                self._line_tracer_mode_written = False
            temp |= (self._line_tracer_id & 0x0f) << 4
            result += self._to_hex(temp)
            temp = (self._line_tracer_speed & 0x0f) << 4
            temp |= self._line_tracer_gain & 0x0f
            result += self._to_hex(temp)
            temp = (self._config_proximity & 0x07) << 5
            temp |= (self._config_band_width & 0x07) << 2
            temp |= (self._config_gravity & 0x03)
            result += self._to_hex(temp)
            if self._io_mode_a > 10:
                temp = self._io_mode_a
            else:
                v = self._io_mode_a
                if v == 5: v = 4
                temp = (v & 0x0f) << 4
                v = self._io_mode_b
                if v == 5: v = 4
                temp |= (v & 0x0f)
            result += self._to_hex(temp)
            result += self._to_hex(self._output_a)
            result += self._to_hex(self._output_b)
            
            temp = self._get_sound(self._sound)
            if self._sound_written:
                self._sound_count = 0
                if temp > 0:
                    self._sound_flag ^= 0x80
                    self._sound_event = 1
                else:
                    self._sound_event = 0
                self._sound_written = False
            if temp > 0:
                result += "00"
                result += self._to_hex(temp | self._sound_flag)
            elif self._note > 0:
                result += "01"
                result += self._to_hex(self._note)
            else:
                temp = self._buzzer
                if temp > 6500: temp = 6500
                result += self._to_hex2(Util.round(temp * 10) + 512)
            result += "-"
            result += address
            result += "\r"
            self._packet_sent = 1
            return result

    def _decode_sensory_packet(self, packet):
        packet = str(packet)
        self.packet_received = 0
        value = int(packet[0:1], 16)
        if value == 1:
            value = int(packet[2:6], 16)
            if value != self._event_pulse_count:
                self._pulse_count_device._put(value, self._event_pulse_count != -1)
                self._event_pulse_count = value
            value = int(packet[6:8], 16)
            self._left_proximity_device._put(value)
            value = int(packet[8:10], 16)
            self._right_proximity_device._put(value)
            value2 = int(packet[38:40], 16)
            if (value2 & 0x01) == 0:
                self._light = int(packet[10:14], 16)
            else:
                value = int(packet[10:12], 16)
                if value > 0x7f: value -= 0x100
                self._temperature = Util.round(value / 2.0 + 23)
            self._light_device._put(self._light)
            self._temperature_device._put(self._temperature)
            value = int(packet[14:16], 16)
            self._left_floor_device._put(value)
            value = int(packet[16:18], 16)
            self._right_floor_device._put(value)
            acc_x = int(packet[18:22], 16)
            if acc_x > 0x7fff: acc_x -= 0x10000
            self._acceleration_device._put_at(0, acc_x)
            acc_y = int(packet[22:26], 16)
            if acc_y > 0x7fff: acc_y -= 0x10000
            self._acceleration_device._put_at(1, acc_y)
            acc_z = int(packet[26:30], 16)
            if acc_z > 0x7fff: acc_z -= 0x10000
            self._acceleration_device._put_at(2, acc_z)
            if acc_z < 8192 and acc_x > 8192 and acc_y > -4096 and acc_y < 4096: value = 1
            elif acc_z < 8192 and acc_x < -8192 and acc_y > -4096 and acc_y < 4096: value = -1
            elif acc_z < 8192 and acc_y > 8192 and acc_x > -4096 and acc_x < 4096: value = 2
            elif acc_z < 8192 and acc_y < -8192 and acc_x > -4096 and acc_x < 4096: value = -2
            elif acc_z > 12288 and acc_x > -8192 and acc_x < 8192 and acc_y > -8192 and acc_y < 8192: value = 3
            elif acc_z < -12288 and acc_x > -4096 and acc_x < 4096 and acc_y > -4096 and acc_y < 4096: value = -3
            else: value = 0
            if value != self._event_tilt:
                self._tilt_device._put(value, self._event_tilt != -4)
                self._event_tilt = value
            value = int(packet[30:32], 16)
            self._input_a_device._put(value)
            value = int(packet[32:34], 16)
            self._input_b_device._put(value)
            value = int(packet[34:36], 16)
            id =  (value >> 6) & 0x03
            if id != self._event_free_fall_id:
                self._free_fall_device._put_empty(self._event_free_fall_id != -1)
                self._event_free_fall_id = id
            id = (value >> 4) & 0x03
            if id != self._event_tap_id:
                self._tap_device._put_empty(self._event_tap_id != -1 and self._wheel_move == False)
                self._event_tap_id = id
            state = (value >> 2) & 0x03
            if self._wheel_event == 1:
                if state == 2:
                    if self._wheel_pulse > 0 and self._wheel_pulse < 25:
                        self._wheel_count += 1
                        if self._wheel_count > 8: self._wheel_event = 2
                elif state == 3:
                    self._wheel_event = 2
            if self._wheel_event == 2:
                if state != self._wheel_state or self._wheel_count > 8:
                    self._wheel_state = state
                    self._wheel_state_device._put(state)
                    if state == 2:
                        self._wheel_event = 0
                        self._wheel_count = 0
            state = (value >> 1) & 0x01
            if self._sound_event == 1:
                if state == 0:
                    self._sound_count += 1
                    if self._sound_count > 5: self._sound_event = 2
                else:
                    self._soudn_event = 2
            if self._sound_event == 2:
                if state != self._sound_state or self._sound_count > 5:
                    self._sound_state = state
                    if state == 0:
                        self._sound_event = 0
                        self._sound_count = 0
                        if self._current_sound > 0:
                            if self._sound_repeat < 0:
                                self._run_sound(self._current_sound, -1)
                            elif self._sound_repeat > 1:
                                self._sound_repeat -= 1
                                self._run_sound(self._current_sound, self._sound_repeat)
                            else:
                                self._current_sound = 0
                                self._sound_repeat = 1
                                self._sound_state_device._put(state)
                        else:
                            self._current_sound = 0
                            self._sound_repeat = 1
            value = int(packet[36:38], 16)
            value -= 0x100
            self._signal_strength_device._put(value)
            state = (value2 >> 6) & 0x03
            if (state & 0x02) != 0:
                if self._line_tracer_event == 1:
                    if state == 0x02:
                        self._line_tracer_count += 1
                        if self._line_tracer_count > 5: self._line_tracer_event = 2
                    else:
                        self._line_tracer_event = 2
                if self._line_tracer_event == 2:
                    if state != self._line_tracer_state or self._line_tracer_count > 5:
                        self._line_tracer_state = state
                        self._line_tracer_state_device._put(state << 5)
                        if state == 0x02:
                            self._line_tracer_event = 0
                            self._line_tracer_count = 0
            state =  (value2 >> 1) & 0x03
            if state == 0: state = 2
            elif state >= 2: state = 0
            if state != self._event_battery_state:
                self._battery_state_device._put(state, self._event_battery_state != -1)
                self._event_battery_state = state
            id = (value2 >> 5) & 0x01
            if id != self._port_ack_id:
                if self._port_ack_id != -1:
                    if self._io_mode_a >= 176 and self._io_mode_a <= 183:
                        self._port_serial = True
                    else:
                        self._port_serial = False
                self._port_ack_id = id
            self._packet_received = 1
        elif value == 2:
            id = int(packet[1:2], 16)
            if id != self._event_serial_id:
                if self._event_serial_id != -1:
                    length = int(packet[2:4], 16)
                    if length > 18: length = 18
                    self._read_serial_data[0] = length
                    j = 4
                    for i in range(1, length + 1):
                        self._read_serial_data[i] = int(packet[j:(j+2)], 16)
                        j += 2
                    if length < 18:
                        for i in range(length + 1, 19):
                            self._read_serial_data[i] = 0
                    self._read_serial_device._put(self._read_serial_data)
                self._event_serial_id = id
            self._packet_received = 3
        if self._serial_send_id != self._serial_send_prev_id:
            self._serial_send_prev_id = self._serial_send_id
            self._serial_state_device._put_empty()
        if self._read_serial_device.e():
            self._get_read_queue().push(self._read_serial_data)
        if self._serial_state_device.e():
            temp = self._get_write_queue().pop()
            if temp is None:
                self._write_serial_id = (self._write_serial_id % 255) + 1
            else:
                self._write_serial_device.write(temp)
        return True

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
            packet = self._encode_motoring_packet(connector.get_address())
            connector.write(packet)

    def _get_write_queue(self):
        if self._write_queue is None:
            from roboid.serial_queue import WriteQueue
            self._write_queue = WriteQueue(64)
        return self._write_queue

    def _get_read_queue(self):
        if self._read_queue is None:
            from roboid.serial_queue import ReadQueue
            self._read_queue = ReadQueue(64)
        return self._read_queue

    def _is_serial_written(self, id):
        return self._write_serial_id != id

    def _write_serial(self, text, line):
        queue = self._get_write_queue()
        queue.push(text, line)
        temp = queue.pop()
        if temp is None:
            return -1
        else:
            self._write_serial_device.write(temp)
            return self._write_serial_id

    def _read_serial(self, delimiter):
        return self._get_read_queue().pop(delimiter)
