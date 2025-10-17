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
from timeit import default_timer as timer

from roboid.runner import Runner
from roboid.util import Util
from roboid.model import DeviceType
from roboid.model import DataType
from roboid.model import Roboid
from roboid.connector import Result
from roboid.pio import Pio
from roboid.serial_connector import SerialConnector


class PioConnectionChecker(object):
    def __init__(self, roboid):
        self._roboid = roboid

    def check(self, info):
        return info[1] == "Pio" and info[2] == "20"


class PioButtonChecker(object):
    def __init__(self):
        self._state = 0
        self._press_time = 0
        self._clicked = False
        self._clicked_fired = False
        self._clicked_event = False
        self._long_pressed = False
        self._long_pressed_fired = False
        self._long_pressed_event = False

    def reset(self):
        self._state = 0
        self._press_time = 0
        self._clicked = False
        self._clicked_fired = False
        self._clicked_event = False
        self._long_pressed = False
        self._long_pressed_fired = False
        self._long_pressed_event = False

    def check(self, pressed):
        self._clicked = False
        self._long_pressed = False
        if self._state == 0: # ready state and wait for press
            if pressed:
                self._press_time = timer()
                self._state = 1
        elif self._state == 1: # check how long button is pressed
            if pressed:
                if timer() - self._press_time > 1.5:
                    self._long_pressed = True
                    self._state = 2
            else:
                if timer() - self._press_time < 0.75:
                    self._clicked = True
                self._state = 0
        elif self._state == 2: # check release of long-click
            if not pressed: self._state = 0
        if self._clicked: self._clicked_fired = True
        if self._long_pressed: self._long_pressed_fired = True

    def is_clicked(self):
        return self._clicked_event

    def is_long_pressed(self):
        return self._long_pressed_event

    def update_state(self):
        self._clicked_event = self._clicked_fired
        self._clicked_fired = False
        self._long_pressed_event = self._long_pressed_fired
        self._long_pressed_fired = False


class PioRoboid(Roboid):
    _SOUNDS = {
        Pio.SOUND_OFF: 0x00,
        Pio.SOUND_BEEP: 0x01,
        Pio.SOUND_RANDOM_BEEP: 0x05,
        Pio.SOUND_NOISE: 0x07,
        Pio.SOUND_SIREN: 0x09,
        Pio.SOUND_ENGINE: 0x0b,
        Pio.SOUND_CHOP: 0x12,
        Pio.SOUND_ROBOT: 0x15,
        Pio.SOUND_DIBIDIBIDIP: 0x27,
        Pio.SOUND_GOOD_JOB: 0x28,
        Pio.SOUND_RANDOM_MELODY: 0x14,
        Pio.SOUND_POOP: 0x29,
        Pio.SOUND_HAPPY: 0x21,
        Pio.SOUND_ANGRY: 0x22,
        Pio.SOUND_SAD: 0x23,
        Pio.SOUND_SLEEP: 0x24,
        Pio.SOUND_MARCH: 0x25,
        Pio.SOUND_BIRTHDAY: 0x26,
        Pio.SOUND_BATH: 0x2a
    }

    def __init__(self, index):
        super(PioRoboid, self).__init__(Pio.ID, "Pio", 0x02000000)
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
        self._turbo = 0
        self._pulse = 0
        self._neck_speed = 4
        self._neck_angle = 0
        self._eye_pattern = 0
        self._note = 0
        self._sound = 0

        self._turbo_written = False
        self._pulse_written = False
        self._neck_speed_written = False
        self._neck_angle_written = False
        self._eye_pattern_written = False
        self._note_written = False
        self._sound_written = False

        self._forward_button_checker = PioButtonChecker()
        self._backward_button_checker = PioButtonChecker()
        self._left_button_checker = PioButtonChecker()
        self._right_button_checker = PioButtonChecker()
        self._run_button_checker = PioButtonChecker()
        self._behavior_button_checker = PioButtonChecker()
        self._repeat_button_checker = PioButtonChecker()
        self._clear_button_checker = PioButtonChecker()

        self._wheel_id = 0
        self._wheel_pulse = 0
        self._wheel_pulse_prev = -1
        self._wheel_event = 0
        self._wheel_state_id = -1

        self._neck_id = 0
        self._neck_event = 0
        self._neck_state_id = -1

        self._eye_id = 0
        self._eye_event = 0
        self._eye_state_id = -1

        self._current_sound = 0
        self._sound_repeat = 1
        self._sound_id = 0
        self._sound_prev = 0
        self._sound_event = 0
        self._sound_state_id = -1

        self._event_forward_button = -1
        self._event_backward_button = -1
        self._event_left_button = -1
        self._event_right_button = -1
        self._event_run_button = -1
        self._event_behavior_button = -1
        self._event_repeat_button = -1
        self._event_clear_button = -1
        self._event_pulse_count = -1
        self._event_neck_encoder = -46
        self._event_key_state_id = -1
        self._event_battery_state = -1
        self._event_usb_state = -1
        self._event_charge_state = -1

        self._create_model()

    def _create_model(self):
        from roboid.pio import Pio
        dict = self._device_dict = {}
        dict[Pio.LEFT_WHEEL] = self._left_wheel_device = self._add_device(Pio.LEFT_WHEEL, "LeftWheel", DeviceType.EFFECTOR, DataType.INTEGER, 1, -100, 100, 0)
        dict[Pio.RIGHT_WHEEL] = self._right_wheel_device = self._add_device(Pio.RIGHT_WHEEL, "RightWheel", DeviceType.EFFECTOR, DataType.INTEGER, 1, -100, 100, 0)
        dict[Pio.LEFT_EYE] = self._left_eye_device = self._add_device(Pio.LEFT_EYE, "LeftEye", DeviceType.EFFECTOR, DataType.INTEGER, 3, 0, 255, 0)
        dict[Pio.RIGHT_EYE] = self._right_eye_device = self._add_device(Pio.RIGHT_EYE, "RightEye", DeviceType.EFFECTOR, DataType.INTEGER, 3, 0, 255, 0)
        dict[Pio.BUZZER] = self._buzzer_device = self._add_device(Pio.BUZZER, "Buzzer", DeviceType.EFFECTOR, DataType.FLOAT, 1, 0, 6553.5, 0)
        dict[Pio.TURBO] = self._turbo_device = self._add_device(Pio.TURBO, "Turbo", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 1, 0)
        dict[Pio.PULSE] = self._pulse_device = self._add_device(Pio.PULSE, "Pulse", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 65535, 0)
        dict[Pio.NECK_SPEED] = self._neck_speed_device = self._add_device(Pio.NECK_SPEED, "NeckSpeed", DeviceType.COMMAND, DataType.INTEGER, 1, 1, 6, 4)
        dict[Pio.NECK_ANGLE] = self._neck_angle_device = self._add_device(Pio.NECK_ANGLE, "NeckAngle", DeviceType.COMMAND, DataType.INTEGER, 1, -90, 90, 0)
        dict[Pio.EYE_PATTERN] = self._eye_pattern_device = self._add_device(Pio.EYE_PATTERN, "EyePattern", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 65535, 0)
        dict[Pio.NOTE] = self._note_device = self._add_device(Pio.NOTE, "Note", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 88, 0)
        dict[Pio.SOUND] = self._sound_device = self._add_device(Pio.SOUND, "Sound", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 127, 0)
        dict[Pio.SIGNAL_STRENGTH] = self._signal_strength_device = self._add_device(Pio.SIGNAL_STRENGTH, "SignalStrength", DeviceType.SENSOR, DataType.INTEGER, 1, -128, 0, 0)
        dict[Pio.FORWARD_BUTTON] = self._forward_button_device = self._add_device(Pio.FORWARD_BUTTON, "ForwardButton", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Pio.BACKWARD_BUTTON] = self._backward_button_device = self._add_device(Pio.BACKWARD_BUTTON, "BackwardButton", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Pio.LEFT_BUTTON] = self._left_button_device = self._add_device(Pio.LEFT_BUTTON, "LeftButton", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Pio.RIGHT_BUTTON] = self._right_button_device = self._add_device(Pio.RIGHT_BUTTON, "RightButton", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Pio.RUN_BUTTON] = self._run_button_device = self._add_device(Pio.RUN_BUTTON, "RunButton", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Pio.BEHAVIOR_BUTTON] = self._behavior_button_device = self._add_device(Pio.BEHAVIOR_BUTTON, "BehaviorButton", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Pio.REPEAT_BUTTON] = self._repeat_button_device = self._add_device(Pio.REPEAT_BUTTON, "RepeatButton", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Pio.CLEAR_BUTTON] = self._clear_button_device = self._add_device(Pio.CLEAR_BUTTON, "ClearButton", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Pio.PULSE_COUNT] = self._pulse_count_device = self._add_device(Pio.PULSE_COUNT, "PulseCount", DeviceType.EVENT, DataType.INTEGER, 1, 0, 65535, 0)
        dict[Pio.WHEEL_STATE] = self._wheel_state_device = self._add_device(Pio.WHEEL_STATE, "WheelState", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Pio.NECK_ENCODER] = self._neck_encoder_device = self._add_device(Pio.NECK_ENCODER, "NeckEncoder", DeviceType.EVENT, DataType.INTEGER, 1, -45, 45, 0)
        dict[Pio.NECK_STATE] = self._neck_state_device = self._add_device(Pio.NECK_STATE, "NeckState", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Pio.EYE_STATE] = self._eye_state_device = self._add_device(Pio.EYE_STATE, "EyeState", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Pio.SOUND_STATE] = self._sound_state_device = self._add_device(Pio.SOUND_STATE, "SoundState", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Pio.KEY_STATE] = self._key_state_device = self._add_device(Pio.KEY_STATE, "KeyState", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Pio.BATTERY_STATE] = self._battery_state_device = self._add_device(Pio.BATTERY_STATE, "BatteryState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 3, 3)
        dict[Pio.USB_STATE] = self._usb_state_device = self._add_device(Pio.USB_STATE, "UsbState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Pio.CHARGE_STATE] = self._charge_state_device = self._add_device(Pio.CHARGE_STATE, "ChargeState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)

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

        tag = "Pio[{}]".format(self._index)
        self._connector = SerialConnector(tag, PioConnectionChecker(self))
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
            super(PioRoboid, self)._dispose()
            self._release()

    def _reset(self):
        super(PioRoboid, self)._reset()

        self._left_wheel = 0
        self._right_wheel = 0
        self._left_red = 0
        self._left_green = 0
        self._left_blue = 0
        self._right_red = 0
        self._right_green = 0
        self._right_blue = 0
        self._buzzer = 0
        self._turbo = 0
        self._pulse = 0
        self._neck_speed = 4
        self._neck_angle = 0
        self._eye_pattern = 0
        self._note = 0
        self._sound = 0

        self._turbo_written = False
        self._pulse_written = False
        self._neck_speed_written = False
        self._neck_angle_written = False
        self._eye_pattern_written = False
        self._note_written = False
        self._sound_written = False

        self._forward_button_checker.reset()
        self._backward_button_checker.reset()
        self._left_button_checker.reset()
        self._right_button_checker.reset()
        self._run_button_checker.reset()
        self._behavior_button_checker.reset()
        self._repeat_button_checker.reset()
        self._clear_button_checker.reset()

        self._wheel_pulse = 0
        self._wheel_pulse_prev = -1
        self._wheel_event = 0
        self._wheel_state_id = -1

        self._neck_event = 0
        self._neck_state_id = -1

        self._eye_event = 0
        self._eye_state_id = -1

        self._current_sound = 0
        self._sound_repeat = 1
        self._sound_prev = 0
        self._sound_event = 0
        self._sound_state_id = -1

        self._event_forward_button = -1
        self._event_backward_button = -1
        self._event_left_button = -1
        self._event_right_button = -1
        self._event_run_button = -1
        self._event_behavior_button = -1
        self._event_repeat_button = -1
        self._event_clear_button = -1
        self._event_pulse_count = -1
        self._event_neck_encoder = -46
        self._event_key_state_id = -1
        self._event_battery_state = -1
        self._event_usb_state = -1
        self._event_charge_state = -1

    def _request_motoring_data(self):
        with self._thread_lock:
            self._left_wheel = self._left_wheel_device.read()
            self._right_wheel = self._right_wheel_device.read()
            self._left_red = self._left_eye_device.read(0)
            self._left_green = self._left_eye_device.read(1)
            self._left_blue = self._left_eye_device.read(2)
            self._right_red = self._right_eye_device.read(0)
            self._right_green = self._right_eye_device.read(1)
            self._right_blue = self._right_eye_device.read(2)
            self._buzzer = self._buzzer_device.read()
            if self._turbo_device._is_written():
                self._turbo = self._turbo_device.read()
                self._turbo_written = True
            if self._pulse_device._is_written():
                self._pulse = self._pulse_device.read()
                self._pulse_written = True
            if self._neck_speed_device._is_written():
                self._neck_speed = self._neck_speed_device.read()
                self._neck_speed_written = True
            if self._neck_angle_device._is_written():
                self._neck_angle = self._neck_angle_device.read()
                self._neck_angle_written = True
            if self._eye_pattern_device._is_written():
                self._eye_pattern = self._eye_pattern_device.read()
                self._eye_pattern_written = True
            if self._note_device._is_written():
                self._note = self._note_device.read()
                self._note_written = True
            if self._sound_device._is_written():
                self._sound = self._sound_device.read()
                self._sound_written = True
        self._clear_written()

    def _get_sound(self, sound):
        if isinstance(sound, (int, float)):
            sound = int(sound)
            if sound in PioRoboid._SOUNDS:
                return PioRoboid._SOUNDS[sound]
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
            if self._turbo == 1:
                result = "11"
            self._wheel_pulse = self._pulse
            if self._pulse_written:
                if self._pulse != 0 or self._wheel_pulse_prev != 0:
                    self._wheel_id = (self._wheel_id % 15) + 1
                if self._pulse > 0:
                    self._wheel_event = 1
                else:
                    self._wheel_event = 0
                self._wheel_pulse_prev = self._pulse
                self._pulse_written = False
            if self._wheel_event == 0:
                result += self._to_hex(self._wheel_id)
            else:
                result += self._to_hex(0x10 | self._wheel_id)
            result += self._to_hex(self._left_wheel)
            result += self._to_hex(self._right_wheel)
            result += self._to_hex2(self._pulse)
            if self._neck_angle_written:
                self._neck_id = (self._neck_id % 15) + 1
                self._neck_event = 1
                self._neck_angle_written = False
            if self._neck_event == 0:
                result += self._to_hex(self._neck_id)
            else:
                result += self._to_hex(0x30 | self._neck_id)
            result += self._to_hex(self._neck_speed)
            result += self._to_hex(self._neck_angle)
            if self._eye_pattern_written:
                self._eye_id = (self._eye_id % 3) + 1
                self._eye_event = 1
                self._eye_pattern_written = False
            if self._eye_event == 0:
                result += self._to_hex((self._eye_id << 4) | self._eye_id)
                result += self._to_hex(self._left_red)
                result += self._to_hex(self._left_green)
                result += self._to_hex(self._left_blue)
                result += self._to_hex(self._right_red)
                result += self._to_hex(self._right_green)
                result += self._to_hex(self._right_blue)
            else:
                result += self._to_hex(0x80 | (self._eye_id << 4) | (self._eye_pattern & 0x0f))
                result += '000000000000'
            result += '00'
            temp = self._get_sound(self._sound)
            if self._sound_written:
                if temp > 0:
                    self._sound_id = (self._sound_id % 15) + 1
                    self._sound_event = 1
                else:
                    self._sound_event = 0
            if temp > 0:
                if self._sound_written and self._sound_prev == temp:
                    result += '000000'
                else:
                    if temp > 0x20:
                        result += self._to_hex(0x30 | self._sound_id)
                        result += self._to_hex(temp - 0x20)
                    else:
                        result += self._to_hex(0x20 | self._sound_id)
                        result += self._to_hex(temp)
                    result += self._to_hex(0)
                self._sound_prev = temp
            elif self._note > 0:
                result += self._to_hex(0x10 | self._sound_id)
                result += self._to_hex(self._note)
                result += self._to_hex(0)
            else:
                result += self._to_hex(self._sound_id)
                result += self._to_hex2(Util.round(self._buzzer * 10))
            self._sound_written = False
            result += "-"
            result += address
            result += "\r"
            return result

    def _decode_sensory_packet(self, packet):
        packet = str(packet)
        value = int(packet[0:1], 16)
        if value != 1: return False
        
        value = int(packet[2:6], 16)
        if value != self._event_pulse_count:
            self._pulse_count_device._put(value, self._event_pulse_count != -1)
            self._event_pulse_count = value
        
        value = int(packet[6:8], 16)
        if value != self._event_neck_encoder:
            self._neck_encoder_device._put(value, self._event_neck_encoder != -46)
            self._event_neck_encoder = value
        
        value = int(packet[8:10], 16)
        state = (value >> 1) & 0x01
        if state != self._event_forward_button:
            self._forward_button_device._put(state, self._event_forward_button != -1)
            self._event_forward_button = state
        state = (value >> 2) & 0x01
        if state != self._event_backward_button:
            self._backward_button_device._put(state, self._event_backward_button != -1)
            self._event_backward_button = state
        state = (value >> 3) & 0x01
        if state != self._event_left_button:
            self._left_button_device._put(state, self._event_left_button != -1)
            self._event_left_button = state
        state = (value >> 4) & 0x01
        if state != self._event_right_button:
            self._right_button_device._put(state, self._event_right_button != -1)
            self._event_right_button = state
        state = value & 0x01
        if state != self._event_run_button:
            self._run_button_device._put(state, self._event_run_button != -1)
            self._event_run_button = state
        state = (value >> 5) & 0x01
        if state != self._event_behavior_button:
            self._behavior_button_device._put(state, self._event_behavior_button != -1)
            self._event_behavior_button = state
        state = (value >> 6) & 0x01
        if state != self._event_repeat_button:
            self._repeat_button_device._put(state, self._event_repeat_button != -1)
            self._event_repeat_button = state
        state = (value >> 7) & 0x01
        if state != self._event_clear_button:
            self._clear_button_device._put(state, self._event_clear_button != -1)
            self._event_clear_button = state
        
        self._forward_button_checker.check(self._event_forward_button)
        self._backward_button_checker.check(self._event_backward_button)
        self._left_button_checker.check(self._event_left_button)
        self._right_button_checker.check(self._event_right_button)
        self._run_button_checker.check(self._event_run_button)
        self._behavior_button_checker.check(self._event_behavior_button)
        self._repeat_button_checker.check(self._event_repeat_button)
        self._clear_button_checker.check(self._event_clear_button)
        
        value = int(packet[10:12], 16)
        id = (value >> 6) & 0x03
        if self._wheel_event == 1:
            if id != self._wheel_state_id and self._wheel_state_id != -1:
                self._wheel_state_device._put_empty()
                self._wheel_event = 0
        self._wheel_state_id = id
        
        id = (value >> 4) & 0x03
        if self._neck_event == 1:
            if id != self._neck_state_id and self._neck_state_id != -1:
                self._neck_state_device._put_empty()
                self._neck_event = 0
        self._neck_state_id = id
        
        id = (value >> 2) & 0x03
        if self._eye_event == 1:
            if id != self._eye_state_id and self._eye_state_id != -1:
                self._eye_state_device._put_empty()
                self._eye_event = 0
        self._eye_state_id = id
        
        value = int(packet[12:14], 16)
        id = (value >> 6) & 0x03
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
        
        id = (value >> 4) & 0x03
        if id != self._event_key_state_id and self._event_key_state_id != -1:
            self._key_state_device._put_empty()
        self._event_key_state_id = id
        
        state = (value >> 1) & 0x01
        if state != self._event_usb_state:
            self._usb_state_device._put(state, self._event_usb_state != -1)
            self._event_usb_state = state
        
        state = value & 0x01
        state = 1 - state
        if state != self._event_charge_state:
            self._charge_state_device._put(state, self._event_charge_state != -1)
            self._event_charge_state = state
        
        value = int(packet[36:38], 16)
        value = (value + 200) / 100.0
        state = 3
        if value < 3.35: state = 0
        elif value < 3.40: state = 1
        elif value < 3.50: state = 2
        if state != self._event_battery_state:
            self._battery_state_device._put(state, self._event_battery_state != -1)
            self._event_battery_state = state
        
        value = int(packet[38:40], 16)
        value -= 0x100
        self._signal_strength_device._put(value)
        return True

    def _update_sensory_device_state(self):
        super(PioRoboid, self)._update_sensory_device_state()
        self._forward_button_checker.update_state()
        self._backward_button_checker.update_state()
        self._left_button_checker.update_state()
        self._right_button_checker.update_state()
        self._run_button_checker.update_state()
        self._behavior_button_checker.update_state()
        self._repeat_button_checker.update_state()
        self._clear_button_checker.update_state()

    def _is_forward_button_clicked(self):
        return self._forward_button_checker.is_clicked()

    def _is_forward_button_long_pressed(self):
        return self._forward_button_checker.is_long_pressed()

    def _is_backward_button_clicked(self):
        return self._backward_button_checker.is_clicked()

    def _is_backward_button_long_pressed(self):
        return self._backward_button_checker.is_long_pressed()

    def _is_left_button_clicked(self):
        return self._left_button_checker.is_clicked()

    def _is_left_button_long_pressed(self):
        return self._left_button_checker.is_long_pressed()

    def _is_right_button_clicked(self):
        return self._right_button_checker.is_clicked()

    def _is_right_button_long_pressed(self):
        return self._right_button_checker.is_long_pressed()

    def _is_run_button_clicked(self):
        return self._run_button_checker.is_clicked()

    def _is_run_button_long_pressed(self):
        return self._run_button_checker.is_long_pressed()

    def _is_behavior_button_clicked(self):
        return self._behavior_button_checker.is_clicked()

    def _is_behavior_button_long_pressed(self):
        return self._behavior_button_checker.is_long_pressed()

    def _is_repeat_button_clicked(self):
        return self._repeat_button_checker.is_clicked()

    def _is_repeat_button_long_pressed(self):
        return self._repeat_button_checker.is_long_pressed()

    def _is_clear_button_clicked(self):
        return self._clear_button_checker.is_clicked()

    def _is_clear_button_long_pressed(self):
        return self._clear_button_checker.is_long_pressed()

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
