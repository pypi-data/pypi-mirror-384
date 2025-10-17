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
from roboid.zerone import Zerone
from roboid.serial_connector import SerialConnector


class ZeroneConnectionChecker(object):
    def __init__(self, roboid):
        self._roboid = roboid

    def check(self, info):
        return info[1] == "Zerone" and info[2] == "0F"


class ZeroneRoboid(Roboid):
    _SOUNDS = {
        Zerone.SOUND_OFF: 0x00,
        Zerone.SOUND_BEEP: 0x01,
        Zerone.SOUND_RANDOM_BEEP: 0x05,
        Zerone.SOUND_NOISE: 0x07,
        Zerone.SOUND_SIREN: 0x09,
        Zerone.SOUND_ENGINE: 0x0b,
        Zerone.SOUND_CHOP: 0x12,
        Zerone.SOUND_ROBOT: 0x14,
        Zerone.SOUND_DIBIDIBIDIP: 0x15,
        Zerone.SOUND_GOOD_JOB: 0x17,
        Zerone.SOUND_HAPPY: 0x18,
        Zerone.SOUND_ANGRY: 0x19,
        Zerone.SOUND_SAD: 0x1a,
        Zerone.SOUND_SLEEP: 0x1b,
        Zerone.SOUND_MARCH: 0x1c,
        Zerone.SOUND_BIRTHDAY: 0x1d
    }

    def __init__(self, index):
        super(ZeroneRoboid, self).__init__(Zerone.ID, "Zerone", 0x00F00000)
        self._index = index
        self._connector = None
        self._ready = False
        self._thread = None
        self._thread_lock = threading.Lock()

        self._left_wheel = 0
        self._right_wheel = 0
        self._left_head_red = 0
        self._left_head_green = 0
        self._left_head_blue = 0
        self._right_head_red = 0
        self._right_head_green = 0
        self._right_head_blue = 0
        self._left_tail_red = 0
        self._left_tail_green = 0
        self._left_tail_blue = 0
        self._right_tail_red = 0
        self._right_tail_green = 0
        self._right_tail_blue = 0
        self._buzzer = 0
        self._pulse = 0
        self._note = 0
        self._sound = 0
        self._line_tracer_mode = 0
        self._line_tracer_speed = 4

        self._pulse_written = False
        self._note_written = False
        self._sound_written = False
        self._line_tracer_mode_written = False
        self._line_tracer_speed_written = False

        self._button_click_id = -1
        self._button_long_press_id = -1

        self._wheel_mode = 0
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

        self._line_tracer_event = 0
        self._line_tracer_state_id = -1

        self._event_button = -1
        self._event_gesture_id = -1
        self._event_color_number_id = -1
        self._event_color_pattern_id = -1
        self._event_pulse_count = -1
        self._event_battery_state = -1

        self._create_model()

    def _create_model(self):
        from roboid.zerone import Zerone
        dict = self._device_dict = {}
        dict[Zerone.LEFT_WHEEL] = self._left_wheel_device = self._add_device(Zerone.LEFT_WHEEL, "LeftWheel", DeviceType.EFFECTOR, DataType.INTEGER, 1, -100, 100, 0)
        dict[Zerone.RIGHT_WHEEL] = self._right_wheel_device = self._add_device(Zerone.RIGHT_WHEEL, "RightWheel", DeviceType.EFFECTOR, DataType.INTEGER, 1, -100, 100, 0)
        dict[Zerone.LEFT_HEAD_LED] = self._left_head_led_device = self._add_device(Zerone.LEFT_HEAD_LED, "LeftHeadLed", DeviceType.EFFECTOR, DataType.INTEGER, 3, 0, 255, 0)
        dict[Zerone.RIGHT_HEAD_LED] = self._right_head_led_device = self._add_device(Zerone.RIGHT_HEAD_LED, "RightHeadLed", DeviceType.EFFECTOR, DataType.INTEGER, 3, 0, 255, 0)
        dict[Zerone.LEFT_TAIL_LED] = self._left_tail_led_device = self._add_device(Zerone.LEFT_TAIL_LED, "LeftTailLed", DeviceType.EFFECTOR, DataType.INTEGER, 3, 0, 255, 0)
        dict[Zerone.RIGHT_TAIL_LED] = self._right_tail_led_device = self._add_device(Zerone.RIGHT_TAIL_LED, "RightTailLed", DeviceType.EFFECTOR, DataType.INTEGER, 3, 0, 255, 0)
        dict[Zerone.BUZZER] = self._buzzer_device = self._add_device(Zerone.BUZZER, "Buzzer", DeviceType.EFFECTOR, DataType.FLOAT, 1, 0, 6500, 0)
        dict[Zerone.PULSE] = self._pulse_device = self._add_device(Zerone.PULSE, "Pulse", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 65535, 0)
        dict[Zerone.NOTE] = self._note_device = self._add_device(Zerone.NOTE, "Note", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 88, 0)
        dict[Zerone.SOUND] = self._sound_device = self._add_device(Zerone.SOUND, "Sound", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 127, 0)
        dict[Zerone.LINE_TRACER_MODE] = self._line_tracer_mode_device = self._add_device(Zerone.LINE_TRACER_MODE, "LineTracerMode", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 15, 0)
        dict[Zerone.LINE_TRACER_SPEED] = self._line_tracer_speed_device = self._add_device(Zerone.LINE_TRACER_SPEED, "LineTracerSpeed", DeviceType.COMMAND, DataType.INTEGER, 1, 1, 8, 4)
        dict[Zerone.SIGNAL_STRENGTH] = self._signal_strength_device = self._add_device(Zerone.SIGNAL_STRENGTH, "SignalStrength", DeviceType.SENSOR, DataType.INTEGER, 1, -128, 0, 0)
        dict[Zerone.LEFT_PROXIMITY] = self._left_proximity_device = self._add_device(Zerone.LEFT_PROXIMITY, "LeftProximity", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[Zerone.RIGHT_PROXIMITY] = self._right_proximity_device = self._add_device(Zerone.RIGHT_PROXIMITY, "RightProximity", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[Zerone.FRONT_PROXIMITY] = self._front_proximity_device = self._add_device(Zerone.FRONT_PROXIMITY, "FrontProximity", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[Zerone.REAR_PROXIMITY] = self._rear_proximity_device = self._add_device(Zerone.REAR_PROXIMITY, "RearProximity", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[Zerone.COLOR] = self._color_device = self._add_device(Zerone.COLOR, "Color", DeviceType.SENSOR, DataType.INTEGER, 3, 0, 255, 0)
        dict[Zerone.FLOOR] = self._floor_device = self._add_device(Zerone.FLOOR, "Floor", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[Zerone.BUTTON] = self._button_device = self._add_device(Zerone.BUTTON, "Button", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Zerone.CLICKED] = self._clicked_device = self._add_device(Zerone.CLICKED, "Clicked", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Zerone.DOUBLE_CLICKED] = self._double_clicked_device = self._add_device(Zerone.DOUBLE_CLICKED, "DoubleClicked", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Zerone.LONG_PRESSED] = self._long_pressed_device = self._add_device(Zerone.LONG_PRESSED, "LongPressed", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Zerone.GESTURE] = self._gesture_device = self._add_device(Zerone.GESTURE, "Gesture", DeviceType.EVENT, DataType.INTEGER, 1, -1, 6, -1)
        dict[Zerone.COLOR_NUMBER] = self._color_number_device = self._add_device(Zerone.COLOR_NUMBER, "ColorNumber", DeviceType.EVENT, DataType.INTEGER, 1, -2, 8, -1)
        dict[Zerone.COLOR_PATTERN] = self._color_pattern_device = self._add_device(Zerone.COLOR_PATTERN, "ColorPattern", DeviceType.EVENT, DataType.INTEGER, 1, -1, 88, -1)
        dict[Zerone.PULSE_COUNT] = self._pulse_count_device = self._add_device(Zerone.PULSE_COUNT, "PulseCount", DeviceType.EVENT, DataType.INTEGER, 1, 0, 65535, 0)
        dict[Zerone.WHEEL_STATE] = self._wheel_state_device = self._add_device(Zerone.WHEEL_STATE, "WheelState", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Zerone.SOUND_STATE] = self._sound_state_device = self._add_device(Zerone.SOUND_STATE, "SoundState", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Zerone.LINE_TRACER_STATE] = self._line_tracer_state_device = self._add_device(Zerone.LINE_TRACER_STATE, "LineTracerState", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Zerone.BATTERY_STATE] = self._battery_state_device = self._add_device(Zerone.BATTERY_STATE, "BatteryState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 2, 2)

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

        tag = "Zerone[{}]".format(self._index)
        self._connector = SerialConnector(tag, ZeroneConnectionChecker(self))
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
            super(ZeroneRoboid, self)._dispose()
            self._release()

    def _reset(self):
        super(ZeroneRoboid, self)._reset()

        self._left_wheel = 0
        self._right_wheel = 0
        self._left_head_red = 0
        self._left_head_green = 0
        self._left_head_blue = 0
        self._right_head_red = 0
        self._right_head_green = 0
        self._right_head_blue = 0
        self._left_tail_red = 0
        self._left_tail_green = 0
        self._left_tail_blue = 0
        self._right_tail_red = 0
        self._right_tail_green = 0
        self._right_tail_blue = 0
        self._buzzer = 0
        self._pulse = 0
        self._note = 0
        self._sound = 0
        self._line_tracer_mode = 0
        self._line_tracer_speed = 4

        self._pulse_written = False
        self._note_written = False
        self._sound_written = False
        self._line_tracer_mode_written = False
        self._line_tracer_speed_written = False

        self._button_click_id = -1
        self._button_long_press_id = -1

        self._wheel_mode = 0
        self._wheel_pulse = 0
        self._wheel_pulse_prev = -1
        self._wheel_event = 0
        self._wheel_state_id = -1

        self._current_sound = 0
        self._sound_repeat = 1
        self._sound_event = 0
        self._sound_state_id = -1

        self._line_tracer_event = 0
        self._line_tracer_state_id = -1

        self._event_button = -1
        self._event_gesture_id = -1
        self._event_color_number_id = -1
        self._event_color_pattern_id = -1
        self._event_pulse_count = -1
        self._event_battery_state = -1

    def _request_motoring_data(self):
        with self._thread_lock:
            self._left_wheel = self._left_wheel_device.read()
            self._right_wheel = self._right_wheel_device.read()
            self._left_head_red = self._left_head_led_device.read(0)
            self._left_head_green = self._left_head_led_device.read(1)
            self._left_head_blue = self._left_head_led_device.read(2)
            self._right_head_red = self._right_head_led_device.read(0)
            self._right_head_green = self._right_head_led_device.read(1)
            self._right_head_blue = self._right_head_led_device.read(2)
            self._left_tail_red = self._left_tail_led_device.read(0)
            self._left_tail_green = self._left_tail_led_device.read(1)
            self._left_tail_blue = self._left_tail_led_device.read(2)
            self._right_tail_red = self._right_tail_led_device.read(0)
            self._right_tail_green = self._right_tail_led_device.read(1)
            self._right_tail_blue = self._right_tail_led_device.read(2)
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
            if self._line_tracer_speed_device._is_written():
                self._line_tracer_speed = self._line_tracer_speed_device.read()
                self._line_tracer_speed_written = True
        self._clear_written()

    def _get_sound(self, sound):
        if isinstance(sound, (int, float)):
            sound = int(sound)
            if sound in ZeroneRoboid._SOUNDS:
                return ZeroneRoboid._SOUNDS[sound]
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
            result += self._to_hex(self._left_wheel)
            result += self._to_hex(self._right_wheel)
            self._wheel_pulse = self._pulse
            if self._pulse_written:
                if self._wheel_pulse != 0 or self._wheel_pulse_prev != 0:
                    self._wheel_id = (self._wheel_id % 127) + 1
                if self._wheel_pulse > 0:
                    self._wheel_mode = 0
                    self._wheel_event = 1
                else:
                    self._wheel_event = 0
                self._wheel_pulse_prev = self._wheel_pulse
                self._pulse_written = False
            if self._line_tracer_mode_written:
                if self._line_tracer_mode > 0:
                    self._wheel_mode = 0x80
                    self._wheel_id = (self._wheel_id % 127) + 1
                    self._line_tracer_event = 1
                else:
                    self._line_tracer_event = 0
                self._line_tracer_mode_written = False
            result += self._to_hex(self._wheel_mode | (self._wheel_id & 0x7f))
            if self._wheel_mode == 0:
                result += self._to_hex2(self._wheel_pulse)
            else:
                result += self._to_hex(self._line_tracer_mode & 0x0f)
                result += self._to_hex((self._line_tracer_speed - 1) & 0x07)
            result += self._to_hex(self._left_head_red)
            result += self._to_hex(self._left_head_green)
            result += self._to_hex(self._left_head_blue)
            result += self._to_hex(self._right_head_red)
            result += self._to_hex(self._right_head_green)
            result += self._to_hex(self._right_head_blue)
            result += self._to_hex(self._left_tail_red)
            result += self._to_hex(self._left_tail_green)
            result += self._to_hex(self._left_tail_blue)
            result += self._to_hex(self._right_tail_red)
            result += self._to_hex(self._right_tail_green)
            result += self._to_hex(self._right_tail_blue)
            temp = self._get_sound(self._sound)
            if self._sound_written:
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
                result += self._to_hex2(Util.round(self._buzzer * 10) + 512)
        result += "-"
        result += address
        result += "\r"
        return result

    def _decode_sensory_packet(self, packet):
        packet = str(packet)
        value = int(packet[0:1], 16)
        if value != 1: return False
        
        id = int(packet[2:4], 16)
        if id != self._event_gesture_id:
            if self._event_gesture_id != -1:
                value = int(packet[4:6], 16)
                if value == 1: self._gesture_device._put(1)
                elif value == 2: self._gesture_device._put(0)
                elif value == 3: self._gesture_device._put(3)
                elif value == 4: self._gesture_device._put(2)
                elif value == 5: self._gesture_device._put(4)
                elif value == 6: self._gesture_device._put(5)
                elif value == 7: self._gesture_device._put(6)
                else: self._gesture_device._put(-1)
            self._event_gesture_id = id
        value = int(packet[6:8], 16)
        self._right_proximity_device._put(value)
        value = int(packet[8:10], 16)
        self._left_proximity_device._put(value)
        value = int(packet[10:12], 16)
        self._rear_proximity_device._put(value)
        value = int(packet[12:14], 16)
        self._front_proximity_device._put(value)
        
        r = int(packet[14:16], 16)
        g = int(packet[16:18], 16)
        b = int(packet[18:20], 16)
        self._color_device._put_at(0, r)
        self._color_device._put_at(1, g)
        self._color_device._put_at(2, b)
        
        value = int(packet[20:22], 16)
        id = (value >> 4) & 0x0f
        if id != self._event_color_number_id:
            value = value & 0x0f
            if value == 15: value = -2
            elif value < 0 or value > 8: value = -1
            self._color_number_device._put(value, self._event_color_number_id != -1)
            self._event_color_number_id = id
        
        id = int(packet[22:24], 16)
        if id != self._event_color_pattern_id:
            value = int(packet[24:26], 16)
            value = ((value >> 4) & 0x0f) * 10 + (value & 0x0f)
            if value < 0: value = -1
            self._color_pattern_device._put(value, self._event_color_pattern_id != -1)
            self._event_color_pattern_id = id
        
        value = int(packet[26:28], 16)
        self._floor_device._put(value)
        
        value = int(packet[28:30], 16)
        state = value & 0x01
        if state != self._event_button:
            self._button_device._put(state, self._event_button != -1)
            self._event_button = state
        clicked_id = (value >> 4) & 0x03
        long_pressed_id = (value >> 6) & 0x03
        if self._button_click_id < 0:
            self._button_click_id = clicked_id
        elif clicked_id != self._button_click_id:
            self._button_click_id = clicked_id
            value = (value >> 1) & 0x07
            if value == 1:
                self._clicked_device._put_empty()
            elif value == 2:
                self._double_clicked_device._put_empty()
        if self._button_long_press_id < 0:
            self._button_long_press_id = long_pressed_id
        elif long_pressed_id != self._button_long_press_id:
            self._button_long_press_id = long_pressed_id
            self._long_pressed_device._put_empty()
        
        value = int(packet[30:34], 16)
        if value != self._event_pulse_count:
            self._pulse_count_device._put(value, self._event_pulse_count != -1)
            self._event_pulse_count = value
        
        value = int(packet[34:36], 16)
        id = (value >> 6) & 0x03
        if self._wheel_event == 1:
            if id != self._wheel_state_id and self._wheel_state_id != -1:
                self._wheel_state_device._put_empty()
                self._wheel_event = 0
        self._wheel_state_id = id
        
        id = (value >> 4) & 0x03
        if self._line_tracer_event == 1:
            if id != self._line_tracer_state_id and self._line_tracer_state_id != -1:
                self._line_tracer_state_device._put_empty()
                self._line_tracer_event = 0
        self._line_tracer_state_id = id
        
        id = (value >> 2) & 0x03
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
        
        state = value & 0x03
        if state == 0: state = 2
        elif state == 2: state = 1
        elif state > 2: state = 0
        if state != self._event_battery_state:
            self._battery_state_device._put(state, self._event_battery_state != -1)
            self._event_battery_state = state
        
        value = int(packet[36:38], 16)
        value -= 0x100
        self._signal_strength_device._put(value)
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
