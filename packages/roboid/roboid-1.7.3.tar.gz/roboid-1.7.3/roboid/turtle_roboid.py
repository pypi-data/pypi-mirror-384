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
from roboid.turtle import Turtle
from roboid.serial_connector import SerialConnector


class TurtleConnectionChecker(object):
    def __init__(self, roboid):
        self._roboid = roboid

    def check(self, info):
        return info[1] == "Turtle" and info[2] == "09"


class TurtleRoboid(Roboid):
    _MODES = {
        Turtle.LINE_TRACER_MODE_OFF: 0x00,
        Turtle.LINE_TRACER_MODE_BLACK: 0x08,
        Turtle.LINE_TRACER_MODE_RED: 0x09,
        Turtle.LINE_TRACER_MODE_GREEN: 0x0b,
        Turtle.LINE_TRACER_MODE_BLUE: 0x0d,
        Turtle.LINE_TRACER_MODE_ANY: 0x0f,
        Turtle.LINE_TRACER_MODE_TURN_LEFT: 0x10,
        Turtle.LINE_TRACER_MODE_TURN_RIGHT: 0x18,
        Turtle.LINE_TRACER_MODE_CROSS: 0x20,
        Turtle.LINE_TRACER_MODE_UTURN: 0x28,
        Turtle.LINE_TRACER_MODE_BLACK_UNTIL_RED: 0x31,
        Turtle.LINE_TRACER_MODE_BLACK_UNTIL_YELLOW: 0x32,
        Turtle.LINE_TRACER_MODE_BLACK_UNTIL_GREEN: 0x33,
        Turtle.LINE_TRACER_MODE_BLACK_UNTIL_CYAN: 0x34,
        Turtle.LINE_TRACER_MODE_BLACK_UNTIL_BLUE: 0x35,
        Turtle.LINE_TRACER_MODE_BLACK_UNTIL_MAGENTA: 0x36,
        Turtle.LINE_TRACER_MODE_BLACK_UNTIL_ANY: 0x37,
        Turtle.LINE_TRACER_MODE_RED_UNTIL_BLACK: 0x39,
        Turtle.LINE_TRACER_MODE_GREEN_UNTIL_BLACK: 0x3b,
        Turtle.LINE_TRACER_MODE_BLUE_UNTIL_BLACK: 0x3d,
        Turtle.LINE_TRACER_MODE_ANY_UNTIL_BLACK: 0x3f
    }
    _SOUNDS = {
        Turtle.SOUND_OFF: 0x00,
        Turtle.SOUND_BEEP: 0x01,
        Turtle.SOUND_RANDOM: 0x05,
        Turtle.SOUND_SIREN: 0x10,
        Turtle.SOUND_ENGINE: 0x20,
        Turtle.SOUND_ROBOT: 0x30,
        Turtle.SOUND_MARCH: 0x40,
        Turtle.SOUND_BIRTHDAY: 0x41,
        Turtle.SOUND_DIBIDIBIDIP: 0x42,
        Turtle.SOUND_GOOD_JOB: 0x43
    }

    def __init__(self, index):
        super(TurtleRoboid, self).__init__(Turtle.ID, "Turtle", 0x00900000)
        self._index = index
        self._connector = None
        self._ready = False
        self._thread = None
        self._thread_lock = threading.Lock()

        self._left_wheel = 0
        self._right_wheel = 0
        self._led_red = 0
        self._led_green = 0
        self._led_blue = 0
        self._buzzer = 0
        self._pulse = 0
        self._note = 0
        self._sound = 0
        self._line_tracer_mode = 0
        self._line_tracer_gain = 5
        self._line_tracer_speed = 5
        self._lamp = 1
        self._lock = 0

        self._pulse_written = False
        self._note_written = False
        self._sound_written = False
        self._line_tracer_mode_written = False
        self._line_tracer_gain_written = False
        self._line_tracer_speed_written = False
        self._lamp_written = False
        self._lock_written = False

        self._acceleration_x = [0] * 10
        self._acceleration_y = [0] * 10
        self._acceleration_z = [0] * 10
        self._acceleration_sum_x = 0.0
        self._acceleration_sum_y = 0.0
        self._acceleration_sum_z = 0.0
        self._acceleration_index = 0
        self._acceleration_count = 0

        self._button_click_id = -1
        self._button_long_press_id = -1

        self._wheel_id = 0
        self._wheel_pulse = 0
        self._wheel_pulse_prev = -1
        self._wheel_event = 0
        self._wheel_state = 0
        self._wheel_count = 0

        self._current_sound = 0
        self._sound_repeat = 1
        self._sound_flag = 0
        self._sound_event = 0
        self._sound_state = 0
        self._sound_count = 0

        self._line_tracer_flag = 0
        self._line_tracer_event = 0
        self._line_tracer_state = 0
        self._line_tracer_count = 0

        self._event_button = -1
        self._event_color_number = -2
        self._event_color_pattern = -1
        self._event_pulse_count = -1
        self._event_tilt = -4
        self._event_battery_state = -1

        self._create_model()

    def _create_model(self):
        from roboid.turtle import Turtle
        dict = self._device_dict = {}
        dict[Turtle.LEFT_WHEEL] = self._left_wheel_device = self._add_device(Turtle.LEFT_WHEEL, "LeftWheel", DeviceType.EFFECTOR, DataType.FLOAT, 1, -400.0, 400.0, 0.0)
        dict[Turtle.RIGHT_WHEEL] = self._right_wheel_device = self._add_device(Turtle.RIGHT_WHEEL, "RightWheel", DeviceType.EFFECTOR, DataType.FLOAT, 1, -400.0, 400.0, 0.0)
        dict[Turtle.LED] = self._led_device = self._add_device(Turtle.LED, "Led", DeviceType.EFFECTOR, DataType.INTEGER, 3, 0, 255, 0)
        dict[Turtle.BUZZER] = self._buzzer_device = self._add_device(Turtle.BUZZER, "Buzzer", DeviceType.EFFECTOR, DataType.FLOAT, 1, 0, 167772.15, 0.0)
        dict[Turtle.PULSE] = self._pulse_device = self._add_device(Turtle.PULSE, "Pulse", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 65535, 0)
        dict[Turtle.NOTE] = self._note_device = self._add_device(Turtle.NOTE, "Note", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 88, 0)
        dict[Turtle.SOUND] = self._sound_device = self._add_device(Turtle.SOUND, "Sound", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 127, 0)
        dict[Turtle.LINE_TRACER_MODE] = self._line_tracer_mode_device = self._add_device(Turtle.LINE_TRACER_MODE, "LineTracerMode", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 127, 0)
        dict[Turtle.LINE_TRACER_GAIN] = self._line_tracer_gain_device = self._add_device(Turtle.LINE_TRACER_GAIN, "LineTracerGain", DeviceType.COMMAND, DataType.INTEGER, 1, 1, 8, 5)
        dict[Turtle.LINE_TRACER_SPEED] = self._line_tracer_speed_device = self._add_device(Turtle.LINE_TRACER_SPEED, "LineTracerSpeed", DeviceType.COMMAND, DataType.INTEGER, 1, 1, 8, 5)
        dict[Turtle.LAMP] = self._lamp_device = self._add_device(Turtle.LAMP, "Lamp", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 1, 1)
        dict[Turtle.LOCK] = self._lock_device = self._add_device(Turtle.LOCK, "Lock", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 1, 0)
        dict[Turtle.SIGNAL_STRENGTH] = self._signal_strength_device = self._add_device(Turtle.SIGNAL_STRENGTH, "SignalStrength", DeviceType.SENSOR, DataType.INTEGER, 1, -128, 0, 0)
        dict[Turtle.COLOR] = self._color_device = self._add_device(Turtle.COLOR, "Color", DeviceType.SENSOR, DataType.INTEGER, 4, 0, 255, 0)
        dict[Turtle.FLOOR] = self._floor_device = self._add_device(Turtle.FLOOR, "Floor", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[Turtle.ACCELERATION] = self._acceleration_device = self._add_device(Turtle.ACCELERATION, "Acceleration", DeviceType.SENSOR, DataType.INTEGER, 3, -32768, 32767, 0)
        dict[Turtle.TEMPERATURE] = self._temperature_device = self._add_device(Turtle.TEMPERATURE, "Temperature", DeviceType.SENSOR, DataType.INTEGER, 1, -40, 88, 0)
        dict[Turtle.BUTTON] = self._button_device = self._add_device(Turtle.BUTTON, "Button", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Turtle.CLICKED] = self._clicked_device = self._add_device(Turtle.CLICKED, "Clicked", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Turtle.DOUBLE_CLICKED] = self._double_clicked_device = self._add_device(Turtle.DOUBLE_CLICKED, "DoubleClicked", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Turtle.LONG_PRESSED] = self._long_pressed_device = self._add_device(Turtle.LONG_PRESSED, "LongPressed", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Turtle.COLOR_NUMBER] = self._color_number_device = self._add_device(Turtle.COLOR_NUMBER, "ColorNumber", DeviceType.EVENT, DataType.INTEGER, 1, -1, 8, -1)
        dict[Turtle.COLOR_PATTERN] = self._color_pattern_device = self._add_device(Turtle.COLOR_PATTERN, "ColorPattern", DeviceType.EVENT, DataType.INTEGER, 1, -1, 88, -1)
        dict[Turtle.PULSE_COUNT] = self._pulse_count_device = self._add_device(Turtle.PULSE_COUNT, "PulseCount", DeviceType.EVENT, DataType.INTEGER, 1, 0, 65535, 0)
        dict[Turtle.WHEEL_STATE] = self._wheel_state_device = self._add_device(Turtle.WHEEL_STATE, "WheelState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Turtle.SOUND_STATE] = self._sound_state_device = self._add_device(Turtle.SOUND_STATE, "SoundState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Turtle.LINE_TRACER_STATE] = self._line_tracer_state_device = self._add_device(Turtle.LINE_TRACER_STATE, "LineTracerState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 3, 0)
        dict[Turtle.TILT] = self._tilt_device = self._add_device(Turtle.TILT, "Tilt", DeviceType.EVENT, DataType.INTEGER, 1, -3, 3, 0)
        dict[Turtle.BATTERY_STATE] = self._battery_state_device = self._add_device(Turtle.BATTERY_STATE, "BatteryState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 2, 2)

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

        tag = "Turtle[{}]".format(self._index)
        self._connector = SerialConnector(tag, TurtleConnectionChecker(self), loader)
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
            super(TurtleRoboid, self)._dispose()
            self._release()

    def _reset(self):
        super(TurtleRoboid, self)._reset()

        self._left_wheel = 0
        self._right_wheel = 0
        self._led_red = 0
        self._led_green = 0
        self._led_blue = 0
        self._buzzer = 0
        self._pulse = 0
        self._note = 0
        self._sound = 0
        self._line_tracer_mode = 0
        self._line_tracer_gain = 5
        self._line_tracer_speed = 5
        self._lamp = 1
        self._lock = 0

        self._pulse_written = False
        self._note_written = False
        self._sound_written = False
        self._line_tracer_mode_written = False
        self._line_tracer_gain_written = False
        self._line_tracer_speed_written = False
        self._lamp_written = False
        self._lock_written = False

        self._acceleration_sum_x = 0.0
        self._acceleration_sum_y = 0.0
        self._acceleration_sum_z = 0.0
        self._acceleration_index = 0
        self._acceleration_count = 0

        self._button_click_id = -1
        self._button_long_press_id = -1

        self._wheel_pulse = 0
        self._wheel_pulse_prev = -1
        self._wheel_event = 0
        self._wheel_state = 0
        self._wheel_count = 0

        self._current_sound = 0
        self._sound_repeat = 1
        self._sound_event = 0
        self._sound_state = 0
        self._sound_count = 0

        self._line_tracer_event = 0
        self._line_tracer_state = 0
        self._line_tracer_count = 0

        self._event_button = -1
        self._event_color_number = -2
        self._event_color_pattern = -1
        self._event_pulse_count = -1
        self._event_tilt = -4
        self._event_battery_state = -1

    def _request_motoring_data(self):
        with self._thread_lock:
            self._left_wheel = self._left_wheel_device.read()
            self._right_wheel = self._right_wheel_device.read()
            self._led_red = self._led_device.read(0)
            self._led_green = self._led_device.read(1)
            self._led_blue = self._led_device.read(2)
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
            if self._line_tracer_mode_device._is_written():
                self._line_tracer_mode = self._line_tracer_mode_device.read()
                self._line_tracer_mode_written = True
            if self._line_tracer_gain_device._is_written():
                self._line_tracer_gain = self._line_tracer_gain_device.read()
                self._line_tracer_gain_written = True
            if self._line_tracer_speed_device._is_written():
                self._line_tracer_speed = self._line_tracer_speed_device.read()
                self._line_tracer_speed_written = True
            if self._lamp_device._is_written():
                self._lamp = self._lamp_device.read()
                self._lamp_written = True
            if self._lock_device._is_written():
                self._lock = self._lock_device.read()
                self._lock_written = True
        self._clear_written()

    def _get_mode(self, mode):
        if isinstance(mode, (int, float)):
            mode = int(mode)
            if mode in TurtleRoboid._MODES:
                return TurtleRoboid._MODES[mode]
        return 0

    def _get_sound(self, sound):
        if isinstance(sound, (int, float)):
            sound = int(sound)
            if sound in TurtleRoboid._SOUNDS:
                return TurtleRoboid._SOUNDS[sound]
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
        result = "10"
        with self._thread_lock:
            result += self._to_hex2(Util.round(self._left_wheel * 10.68))
            result += self._to_hex2(Util.round(self._right_wheel * 10.68))
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
            temp = self._get_mode(self._line_tracer_mode)
            if self._line_tracer_mode_written:
                self._line_tracer_count = 0
                if temp > 0:
                    self._line_tracer_flag ^= 0x80
                    self._line_tracer_event = 1
                else:
                    self._line_tracer_event = 0
                self._line_tracer_mode_written = False
            temp |= self._line_tracer_flag
            result += self._to_hex(temp)
            result += self._to_hex(self._led_red)
            result += self._to_hex(self._led_green)
            result += self._to_hex(self._led_blue)
            temp = (self._lock & 0x01) << 4
            temp |= (1 - self._lamp) & 0x01
            result += self._to_hex(temp)
            result += self._to_hex3(Util.round(self._buzzer * 100))
            result += self._to_hex(self._note)
            temp = self._get_sound(self._sound)
            if self._sound_written:
                self._sound_count = 0
                if temp > 0:
                    self._sound_flag ^= 0x80
                    self._sound_event = 1
                else:
                    self._sound_event = 0
                self._sound_written = False
            temp |= self._sound_flag
            result += self._to_hex(temp)
            temp = ((self._line_tracer_gain - 1) << 4) & 0xf0
            temp |= (self._line_tracer_speed - 1) & 0x0f
            result += self._to_hex(temp)
        result += "00-"
        result += address
        result += "\r"
        return result

    def _decode_sensory_packet(self, packet):
        packet = str(packet)
        value = int(packet[0:1], 16)
        if value != 1: return False
        red = int(packet[2:6], 16)
        green = int(packet[6:10], 16)
        blue = int(packet[10:14], 16)
        value = int(packet[14:16], 16)
        
        r = Util.round(red * 255.0 / 1023)
        g = Util.round(green * 255.0 / 1023)
        b = Util.round(blue * 255.0 / 1023)
        if r > 255: r = 255
        elif r < 0: r = 0
        if g > 255: g = 255
        elif g < 0: g = 0
        if b > 255: b = 255
        elif b < 0: b = 0
        
        self._color_device._put_at(0, r)
        self._color_device._put_at(1, g)
        self._color_device._put_at(2, b)
        self._color_device._put_at(3, value)
        
        color_number = Turtle.COLOR_NONE
        if value < 75:
            if red > 600 and green > 600 and blue > 600:
                color_number = Turtle.COLOR_WHITE
            elif green < red * 3/10 and blue < red * 3/10 and red > 350:
                color_number = Turtle.COLOR_RED
            elif blue < red * 5/10 and blue < green * 6/10 and red > 300 and green > 250:
                if green < red * 15/20:
                    color_number = Turtle.COLOR_ORANGE
                else:
                    color_number = Turtle.COLOR_YELLOW
            elif red < green * 6/10 and blue < green * 6/10 and green > 300:
                color_number = Turtle.COLOR_GREEN
            elif red < blue * 6/10 and green < blue * 7/10 and blue > 250:
                color_number = Turtle.COLOR_BLUE
            elif red < green * 6/10 and red < blue * 6/10 and blue > 250 and green > 250:
                color_number = Turtle.COLOR_CYAN
            elif green < red * 7/10 and green < blue * 7/10 and red > 250:
                color_number = Turtle.COLOR_MAGENTA
            elif red < 300 and green < 300 and blue < 250:
                color_number = Turtle.COLOR_BLACK
        if color_number != self._event_color_number:
            self._color_number_device._put(color_number, self._event_color_number != -2)
            self._event_color_number = color_number
        value = int(packet[16:18], 16)
        clicked_id = (value >> 2) & 0x03
        long_pressed_id = (value >> 4) & 0x03
        if self._button_click_id < 0:
            self._button_click_id = clicked_id
        elif clicked_id != self._button_click_id:
            self._button_click_id = clicked_id
            value = value & 0x03
            if value == 1:
                self._clicked_device._put_empty()
            elif value == 2:
                self._double_clicked_device._put_empty()
        if self._button_long_press_id < 0:
            self._button_long_press_id = long_pressed_id
        elif long_pressed_id != self._button_long_press_id:
            self._button_long_press_id = long_pressed_id
            self._long_pressed_device._put_empty()
        value = int(packet[18:20], 16)
        self._floor_device._put(value)
        value = int(packet[20:22], 16)
        pattern = (value >> 1) & 0x7f
        if self._event_color_pattern < 0:
            self._event_color_pattern = pattern
        elif pattern != self._event_color_pattern:
            self._event_color_pattern = pattern
            pattern1 = (pattern >> 3) & 0x07
            if pattern1 > 1: pattern1 += 1
            pattern2 = pattern & 0x07
            if pattern2 > 1: pattern2 += 1
            self._color_pattern_device._put(pattern1 * 10 + pattern2)
        value = value & 0x01
        if value != self._event_button:
            self._button_device._put(value, self._event_button != -1)
            self._event_button = value
        value = int(packet[22:26], 16)
        if value != self._event_pulse_count:
            self._pulse_count_device._put(value, self._event_pulse_count != -1)
            self._event_pulse_count = value
        if self._acceleration_count < 10:
            self._acceleration_count += 1
        else:
            self._acceleration_index %= 10
            self._acceleration_sum_x -= self._acceleration_x[self._acceleration_index]
            self._acceleration_sum_y -= self._acceleration_y[self._acceleration_index]
            self._acceleration_sum_z -= self._acceleration_z[self._acceleration_index]
        value = int(packet[26:28], 16)
        if value > 0x7f: value -= 0x100
        value *= 256
        self._acceleration_sum_x += value
        self._acceleration_x[self._acceleration_index] = value
        value = int(packet[28:30], 16)
        if value > 0x7f: value -= 0x100
        value *= 256
        self._acceleration_sum_y += value
        self._acceleration_y[self._acceleration_index] = value
        value = int(packet[30:32], 16)
        if value > 0x7f: value -= 0x100
        value *= 256
        self._acceleration_sum_z += value
        self._acceleration_z[self._acceleration_index] = value
        self._acceleration_index += 1
        acc_x = int(self._acceleration_sum_x / self._acceleration_count)
        acc_y = int(self._acceleration_sum_y / self._acceleration_count)
        acc_z = int(self._acceleration_sum_z / self._acceleration_count)
        self._acceleration_device._put_at(0, acc_x)
        self._acceleration_device._put_at(1, acc_y)
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
        value = int(packet[32:34], 16)
        if value > 0x7f: value -= 0x100
        value = Util.round(value / 2.0 + 24)
        self._temperature_device._put(value)
        value = int(packet[34:36], 16)
        value -= 0x100
        self._signal_strength_device._put(value)
        value = (int(packet[36:38], 16) + 200) / 100.0
        if value < 3.65: value = 0
        elif value < 3.75: value = 1
        else: value = 2
        if value != self._event_battery_state:
            self._battery_state_device._put(value, self._event_battery_state != -1)
            self._event_battery_state = value
        value = int(packet[38:40], 16)
        state = (value >> 4) & 0x01
        if self._wheel_event == 1:
            if state == 0:
                if self._wheel_pulse > 0 and self._wheel_pulse < 20:
                    self._wheel_count += 1
                    if self._wheel_count > 8: self._wheel_event = 2
            else:
                self._wheel_event = 2
        if self._wheel_event == 2:
            if state != self._wheel_state or self._wheel_count > 8:
                self._wheel_state = state
                self._wheel_state_device._put(state)
                if state == 0:
                    self._wheel_event = 0
                    self._wheel_count = 0
        state = value & 0x03
        if state > 1: state = 1
        if self._sound_event == 1:
            if state == 0:
                self._sound_count += 1
                if self._sound_count > 5: self._sound_event = 2
            else:
                self._sound_event = 2
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
        state = (value >> 2) & 0x03
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
                    self._line_tracer_state_device._put(state)
                    if state == 0x02:
                        self._line_tracer_event = 0
                        self._line_tracer_count = 0
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
