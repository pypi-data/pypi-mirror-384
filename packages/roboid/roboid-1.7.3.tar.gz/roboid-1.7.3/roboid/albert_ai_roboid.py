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
from roboid.albert_ai import AlbertAi
from roboid.serial_connector import SerialConnector


class AlbertAiConnectionChecker(object):
    def __init__(self, roboid):
        self._roboid = roboid

    def check(self, info):
        return info[1] == "Albert AI" and info[2] == "0A"


class AlbertAiTouchChecker(object):
    def __init__(self):
        self._down = False
        self._clicked = False
        self._long_pressed = False
        self._long_long_pressed = False
        self._check_long_pressed = False
        self._check_long_long_pressed = False
        self._pressed_time = 0

    def reset(self):
        self._down = False
        self._clicked = False
        self._long_pressed = False
        self._long_long_pressed = False
        self._check_long_pressed = False
        self._check_long_long_pressed = False
        self._pressed_time = 0

    def is_clicked(self):
        return self._clicked

    def is_long_pressed(self):
        return self._long_pressed

    def is_long_long_pressed(self):
        return self._long_long_pressed

    def check(self, touched):
        if self._down:
            if touched:
                self._clicked = False
                if self._check_long_pressed:
                    if timer() - self._pressed_time > 1.5:
                        self._check_long_pressed = False
                        self._long_pressed = True
                if self._check_long_long_pressed:
                    if timer() - self._pressed_time > 3:
                        self._check_long_long_pressed = False
                        self._long_long_pressed = True
            else:
                if timer() - self._pressed_time < 0.75:
                    self._clicked = True
                self._long_pressed = False
                self._long_long_pressed = False
                self._check_long_pressed = False
                self._check_long_long_pressed = False
        else:
            self._clicked = False
            self._long_pressed = False
            self._long_long_pressed = False
            if touched:
                self._check_long_pressed = True
                self._check_long_long_pressed = True
                self._pressed_time = timer()
            else:
                self._check_long_pressed = False
                self._check_long_long_pressed = False
        self._down = touched


class AlbertAiRoboid(Roboid):
    _SOUNDS = {
        AlbertAi.SOUND_OFF: 0x00,
        AlbertAi.SOUND_BEEP: 0x01,
        AlbertAi.SOUND_RANDOM_BEEP: 0x05,
        AlbertAi.SOUND_NOISE: 0x07,
        AlbertAi.SOUND_SIREN: 0x10,
        AlbertAi.SOUND_ENGINE: 0x20,
        AlbertAi.SOUND_ROBOT: 0x30
    }

    def __init__(self, index):
        super(AlbertAiRoboid, self).__init__(AlbertAi.ID, "AlbertAi", 0x00a00000)
        self._index = index
        self._connector = None
        self._ready = False
        self._thread = None
        self._thread_lock = threading.Lock()

        self._left_wheel = 0
        self._right_wheel = 0
        self._left_eye_red = 0
        self._left_eye_green = 0
        self._left_eye_blue = 0
        self._right_eye_red = 0
        self._right_eye_green = 0
        self._right_eye_blue = 0
        self._mic_led_red = 0
        self._mic_led_green = 0
        self._mic_led_blue = 0
        self._buzzer = 0
        self._pulse = 0
        self._note = 0
        self._sound = 0
        self._board_width = 0
        self._board_height = 0

        self._pulse_written = False
        self._note_written = False
        self._sound_written = False
        self._board_size_written = False

        self._acceleration_x = [0] * 10
        self._acceleration_y = [0] * 10
        self._acceleration_z = [0] * 10
        self._acceleration_sum_x = 0.0
        self._acceleration_sum_y = 0.0
        self._acceleration_sum_z = 0.0
        self._acceleration_index = 0
        self._acceleration_count = 0

        self._mic_checker = AlbertAiTouchChecker()
        self._volume_up_checker = AlbertAiTouchChecker()
        self._volume_down_checker = AlbertAiTouchChecker()
        self._play_checker = AlbertAiTouchChecker()
        self._back_checker = AlbertAiTouchChecker()

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

        self._event_mic_touch = -1
        self._event_volume_up_touch = -1
        self._event_volume_down_touch = -1
        self._event_play_touch = -1
        self._event_back_touch = -1
        self._event_mic_clicked = False
        self._event_volume_up_clicked = False
        self._event_volume_down_clicked = False
        self._event_play_clicked = False
        self._event_back_clicked = False
        self._event_mic_long_pressed = False
        self._event_volume_up_long_pressed = False
        self._event_volume_down_long_pressed = False
        self._event_play_long_pressed = False
        self._event_back_long_pressed = False
        self._event_mic_long_long_pressed = False
        self._event_volume_up_long_long_pressed = False
        self._event_volume_down_long_long_pressed = False
        self._event_play_long_long_pressed = False
        self._event_back_long_long_pressed = False
        self._event_tap_id = -1
        self._event_oid_mode_id = -1
        self._event_oid = -2
        self._event_lift = -1
        self._event_pulse_count = -1
        self._event_battery_state = -1
        self._event_tilt = -4
        
        self._create_model()

    def _create_model(self):
        from roboid.albert_ai import AlbertAi
        dict = self._device_dict = {}
        dict[AlbertAi.SPEAKER] = self._speaker_device = self._add_device(AlbertAi.SPEAKER, "Speaker", DeviceType.EFFECTOR, DataType.INTEGER, 480, -32768, 32767, 0)
        dict[AlbertAi.VOLUME] = self._volume_device = self._add_device(AlbertAi.VOLUME, "Volume", DeviceType.EFFECTOR, DataType.INTEGER, 1, 0, 300, 100)
        dict[AlbertAi.LIP] = self._lip_device = self._add_device(AlbertAi.LIP, "Lip", DeviceType.EFFECTOR, DataType.INTEGER, 1, 0, 100, 0)
        dict[AlbertAi.LEFT_WHEEL] = self._left_wheel_device = self._add_device(AlbertAi.LEFT_WHEEL, "LeftWheel", DeviceType.EFFECTOR, DataType.FLOAT, 1, -100, 100, 0)
        dict[AlbertAi.RIGHT_WHEEL] = self._right_wheel_device = self._add_device(AlbertAi.RIGHT_WHEEL, "RightWheel", DeviceType.EFFECTOR, DataType.FLOAT, 1, -100, 100, 0)
        dict[AlbertAi.LEFT_EYE] = self._left_eye_device = self._add_device(AlbertAi.LEFT_EYE, "LeftEye", DeviceType.EFFECTOR, DataType.INTEGER, 3, 0, 255, 0)
        dict[AlbertAi.RIGHT_EYE] = self._right_eye_device = self._add_device(AlbertAi.RIGHT_EYE, "RightEye", DeviceType.EFFECTOR, DataType.INTEGER, 3, 0, 255, 0)
        dict[AlbertAi.MIC_LED] = self._mic_led_device = self._add_device(AlbertAi.MIC_LED, "MicLed", DeviceType.EFFECTOR, DataType.INTEGER, 3, 0, 255, 0)
        dict[AlbertAi.BUZZER] = self._buzzer_device = self._add_device(AlbertAi.BUZZER, "Buzzer", DeviceType.EFFECTOR, DataType.FLOAT, 1, 0.0, 6553.5, 0.0)
        dict[AlbertAi.PULSE] = self._pulse_device = self._add_device(AlbertAi.PULSE, "Pulse", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 65535, 0)
        dict[AlbertAi.NOTE] = self._note_device = self._add_device(AlbertAi.NOTE, "Note", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 88, 0)
        dict[AlbertAi.SOUND] = self._sound_device = self._add_device(AlbertAi.SOUND, "Sound", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 127, 0)
        dict[AlbertAi.BOARD_SIZE] = self._board_size_device = self._add_device(AlbertAi.BOARD_SIZE, "BoardSize", DeviceType.COMMAND,DataType.INTEGER, 2, 0, 268435455, 0)
        dict[AlbertAi.SIGNAL_STRENGTH] = self._signal_strength_device = self._add_device(AlbertAi.SIGNAL_STRENGTH, "SignalStrength", DeviceType.SENSOR, DataType.INTEGER, 1, -128, 0, 0)
        dict[AlbertAi.LEFT_PROXIMITY] = self._left_proximity_device = self._add_device(AlbertAi.LEFT_PROXIMITY, "LeftProximity", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[AlbertAi.RIGHT_PROXIMITY] = self._right_proximity_device = self._add_device(AlbertAi.RIGHT_PROXIMITY, "RightProximity", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 255, 0)
        dict[AlbertAi.ACCELERATION] = self._acceleration_device = self._add_device(AlbertAi.ACCELERATION, "Acceleration", DeviceType.SENSOR, DataType.INTEGER, 3, -8192, 8191, 0)
        dict[AlbertAi.POSITION] = self._position_device = self._add_device(AlbertAi.POSITION, "Position", DeviceType.SENSOR, DataType.INTEGER, 2, -1, 268435454, -1)
        dict[AlbertAi.ORIENTATION] = self._orientation_device = self._add_device(AlbertAi.ORIENTATION, "Orientation", DeviceType.SENSOR, DataType.INTEGER, 1, -200, 180, -200)
        dict[AlbertAi.LIGHT] = self._light_device = self._add_device(AlbertAi.LIGHT, "Light", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 65535, 0)
        dict[AlbertAi.BATTERY] = self._battery_device = self._add_device(AlbertAi.BATTERY, "Battery", DeviceType.SENSOR, DataType.INTEGER, 1, 0, 100, 0)
        dict[AlbertAi.MIC_TOUCH] = self._mic_touch_device = self._add_device(AlbertAi.MIC_TOUCH, "MicTouch", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[AlbertAi.VOLUME_UP_TOUCH] = self._volume_up_touch_device = self._add_device(AlbertAi.VOLUME_UP_TOUCH, "VolumeUpTouch", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[AlbertAi.VOLUME_DOWN_TOUCH] = self._volume_down_touch_device = self._add_device(AlbertAi.VOLUME_DOWN_TOUCH, "VolumeDownTouch", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[AlbertAi.PLAY_TOUCH] = self._play_touch_device = self._add_device(AlbertAi.PLAY_TOUCH, "PlayTouch", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[AlbertAi.BACK_TOUCH] = self._back_touch_device = self._add_device(AlbertAi.BACK_TOUCH, "BackTouch", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[AlbertAi.MIC_CLICKED] = self._mic_clicked_device = self._add_device(AlbertAi.MIC_CLICKED, "MicClicked", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[AlbertAi.VOLUME_UP_CLICKED] = self._volume_up_clicked_device = self._add_device(AlbertAi.VOLUME_UP_CLICKED, "VolumeUpClicked", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[AlbertAi.VOLUME_DOWN_CLICKED] = self._volume_down_clicked_device = self._add_device(AlbertAi.VOLUME_DOWN_CLICKED, "VolumeDownClicked", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[AlbertAi.PLAY_CLICKED] = self._play_clicked_device = self._add_device(AlbertAi.PLAY_CLICKED, "PlayClicked", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[AlbertAi.BACK_CLICKED] = self._back_clicked_device = self._add_device(AlbertAi.BACK_CLICKED, "BackClicked", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[AlbertAi.MIC_LONG_PRESSED] = self._mic_long_pressed_device = self._add_device(AlbertAi.MIC_LONG_PRESSED, "MicLongPressed", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[AlbertAi.VOLUME_UP_LONG_PRESSED] = self._volume_up_long_pressed_device = self._add_device(AlbertAi.VOLUME_UP_LONG_PRESSED, "VolumeUpLongPressed", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[AlbertAi.VOLUME_DOWN_LONG_PRESSED] = self._volume_down_long_pressed_device = self._add_device(AlbertAi.VOLUME_DOWN_LONG_PRESSED, "VolumeDownLongPressed", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[AlbertAi.PLAY_LONG_PRESSED] = self._play_long_pressed_device = self._add_device(AlbertAi.PLAY_LONG_PRESSED, "PlayLongPressed", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[AlbertAi.BACK_LONG_PRESSED] = self._back_long_pressed_device = self._add_device(AlbertAi.BACK_LONG_PRESSED, "BackLongPressed", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[AlbertAi.MIC_LONG_LONG_PRESSED] = self._mic_long_long_pressed_device = self._add_device(AlbertAi.MIC_LONG_LONG_PRESSED, "MicLongLongPressed", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[AlbertAi.VOLUME_UP_LONG_LONG_PRESSED] = self._volume_up_long_long_pressed_device = self._add_device(AlbertAi.VOLUME_UP_LONG_LONG_PRESSED, "VolumeUpLongLongPressed", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[AlbertAi.VOLUME_DOWN_LONG_LONG_PRESSED] = self._volume_down_long_long_pressed_device = self._add_device(AlbertAi.VOLUME_DOWN_LONG_LONG_PRESSED, "VolumeDownLongLongPressed", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[AlbertAi.PLAY_LONG_LONG_PRESSED] = self._play_long_long_pressed_device = self._add_device(AlbertAi.PLAY_LONG_LONG_PRESSED, "PlayLongLongPressed", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[AlbertAi.BACK_LONG_LONG_PRESSED] = self._back_long_long_pressed_device = self._add_device(AlbertAi.BACK_LONG_LONG_PRESSED, "BackLongLongPressed", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[AlbertAi.TAP] = self._tap_device = self._add_device(AlbertAi.TAP, "Tap", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[AlbertAi.OID_MODE] = self._oid_mode_device = self._add_device(AlbertAi.OID_MODE, "OidMode", DeviceType.EVENT, DataType.INTEGER, 1, 0, 15, 0)
        dict[AlbertAi.OID] = self._oid_device = self._add_device(AlbertAi.OID, "Oid", DeviceType.EVENT, DataType.INTEGER, 1, -1, 268435455, -1)
        dict[AlbertAi.LIFT] = self._lift_device = self._add_device(AlbertAi.LIFT, "Lift", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[AlbertAi.PULSE_COUNT] = self._pulse_count_device = self._add_device(AlbertAi.PULSE_COUNT, "PulseCount", DeviceType.EVENT, DataType.INTEGER, 1, 0, 65535, 0)
        dict[AlbertAi.WHEEL_STATE] = self._wheel_state_device = self._add_device(AlbertAi.WHEEL_STATE, "WheelState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 3, 0)
        dict[AlbertAi.SOUND_STATE] = self._sound_state_device = self._add_device(AlbertAi.SOUND_STATE, "SoundState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[AlbertAi.BATTERY_STATE] = self._battery_state_device = self._add_device(AlbertAi.BATTERY_STATE, "BatteryState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 2, 2)
        dict[AlbertAi.TILT] = self._tilt_device = self._add_device(AlbertAi.TILT, "Tilt", DeviceType.EVENT, DataType.INTEGER, 1, -3, 3, 0)

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

        tag = "AlbertAi[{}]".format(self._index)
        self._connector = SerialConnector(tag, AlbertAiConnectionChecker(self))
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
            super(AlbertAiRoboid, self)._dispose()
            self._release()

    def _reset(self):
        super(AlbertAiRoboid, self)._reset()

        self._left_wheel = 0
        self._right_wheel = 0
        self._left_eye_red = 0
        self._left_eye_green = 0
        self._left_eye_blue = 0
        self._right_eye_red = 0
        self._right_eye_green = 0
        self._right_eye_blue = 0
        self._mic_led_red = 0
        self._mic_led_green = 0
        self._mic_led_blue = 0
        self._buzzer = 0
        self._pulse = 0
        self._note = 0
        self._sound = 0
        self._board_width = 0
        self._board_height = 0

        self._pulse_written = False
        self._note_written = False
        self._sound_written = False
        self._board_size_written = False

        self._acceleration_sum_x = 0.0
        self._acceleration_sum_y = 0.0
        self._acceleration_sum_z = 0.0
        self._acceleration_index = 0
        self._acceleration_count = 0

        self._mic_checker.reset()
        self._volume_up_checker.reset()
        self._volume_down_checker.reset()
        self._play_checker.reset()
        self._back_checker.reset()

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

        self._event_mic_touch = -1
        self._event_volume_up_touch = -1
        self._event_volume_down_touch = -1
        self._event_play_touch = -1
        self._event_back_touch = -1
        self._event_mic_clicked = False
        self._event_volume_up_clicked = False
        self._event_volume_down_clicked = False
        self._event_play_clicked = False
        self._event_back_clicked = False
        self._event_mic_long_pressed = False
        self._event_volume_up_long_pressed = False
        self._event_volume_down_long_pressed = False
        self._event_play_long_pressed = False
        self._event_back_long_pressed = False
        self._event_mic_long_long_pressed = False
        self._event_volume_up_long_long_pressed = False
        self._event_volume_down_long_long_pressed = False
        self._event_play_long_long_pressed = False
        self._event_back_long_long_pressed = False
        self._event_tap_id = -1
        self._event_oid_mode_id = -1
        self._event_oid = -2
        self._event_lift = -1
        self._event_pulse_count = -1
        self._event_battery_state = -1
        self._event_tilt = -4

    def _request_motoring_data(self):
        with self._thread_lock:
            self._left_wheel = self._left_wheel_device.read()
            self._right_wheel = self._right_wheel_device.read()
            self._left_eye_red = self._left_eye_device.read(0)
            self._left_eye_green = self._left_eye_device.read(1)
            self._left_eye_blue = self._left_eye_device.read(2)
            self._right_eye_red = self._right_eye_device.read(0)
            self._right_eye_green = self._right_eye_device.read(1)
            self._right_eye_blue = self._right_eye_device.read(2)
            self._mic_led_red = self._mic_led_device.read(0)
            self._mic_led_green = self._mic_led_device.read(1)
            self._mic_led_blue = self._mic_led_device.read(2)
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
            if self._board_size_device._is_written():
                self._board_width = self._board_size_device.read(0)
                self._board_height = self._board_size_device.read(1)
                self._board_size_written = True
        self._clear_written()

    def _get_sound(self, sound):
        if isinstance(sound, (int, float)):
            sound = int(sound)
            if sound in AlbertAiRoboid._SOUNDS:
                return AlbertAiRoboid._SOUNDS[sound]
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
            left_wheel = Util.round(self._left_wheel * 1.27)
            if left_wheel > 127: left_wheel = 127
            elif left_wheel < -127: left_wheel = -127
            right_wheel = Util.round(self._right_wheel * 1.27)
            if right_wheel > 127: right_wheel = 127
            elif right_wheel < -127: right_wheel = -127
            if left_wheel == 0 and right_wheel == 0:
                if self._wheel_move:
                    self._wheel_move_count += 1
                    if self._wheel_move_count > 5:
                        self._wheel_move = False
            else:
                self._wheel_move = True
                self._wheel_move_count = 0
            result += self._to_hex(left_wheel)
            result += self._to_hex(right_wheel)
            self._wheel_pulse = self._pulse
            if self._pulse_written:
                if self._wheel_pulse != 0 or self._wheel_pulse_prev != 0:
                    self._wheel_id = (self._wheel_id % 255) + 1
                self._wheel_count = 0
                if self._wheel_pulse > 0:
                    self._wheel_event = 1
                else:
                    self._wheel_event = 0
                self._wheel_pulse_prev = self._wheel_pulse
                self._pulse_written = False
            result += self._to_hex(self._wheel_id)
            result += self._to_hex2(self._wheel_pulse)
            result += self._to_hex(self._mic_led_red)
            result += self._to_hex(self._mic_led_green)
            result += self._to_hex(self._mic_led_blue)
            result += self._to_hex(self._left_eye_red)
            result += self._to_hex(self._left_eye_green)
            result += self._to_hex(self._left_eye_blue)
            result += self._to_hex(self._right_eye_red)
            result += self._to_hex(self._right_eye_green)
            result += self._to_hex(self._right_eye_blue)
            temp = self._get_sound(self._sound)
            if self._sound_written:
                self._sound_count = 0
                if temp > 0:
                    self._sound_flag ^= 0x80
                    self._sound_event = 1
                else:
                    self._sound_flag = 0
                    self._sound_event = 0
                self._sound_written = False
            temp |= self._sound_flag
            result += self._to_hex(temp)
            result += self._to_hex(self._note)
            result += self._to_hex2(Util.round(self._buzzer * 10))
        result += "00-"
        result += address
        result += "\r"
        return result

    def _calc_battery_perc(self, value):
        if value >= 4.11: return 100
        if value >= 3.59: return (100 - 90) * (value - 3.59) / (4.11 - 3.59) + 90
        if value >= 3.55: return (90 - 10) * (value - 3.55) / (3.59 - 3.55) + 10
        if value >= 3.53: return 10 * (value - 3.53) / (3.55 - 3.53)
        return 0

    def _decode_sensory_packet(self, packet):
        packet = str(packet)
        value = int(packet[0:1], 16)
        if value != 1: return False

        value = int(packet[1:2], 16)
        value = (value >> 2) & 0x01
        if value != self._event_tap_id:
            self._tap_device._put_empty(self._event_tap_id != -1 and self._wheel_move == False)
            self._event_tap_id = value
        value = int(packet[36:38], 16)
        value -= 0x100
        self._signal_strength_device._put(value)
        value = int(packet[2:4], 16)
        self._left_proximity_device._put(value)
        value = int(packet[4:6], 16)
        self._right_proximity_device._put(value)
        if self._acceleration_count < 10:
            self._acceleration_count += 1
        else:
            self._acceleration_index %= 10
            self._acceleration_sum_x -= self._acceleration_x[self._acceleration_index]
            self._acceleration_sum_y -= self._acceleration_y[self._acceleration_index]
            self._acceleration_sum_z -= self._acceleration_z[self._acceleration_index]
        value = int(packet[16:18], 16)
        if value > 0x7f: value -= 0x100
        value *= 64
        self._acceleration_sum_x += value
        self._acceleration_x[self._acceleration_index] = value
        value = int(packet[18:20], 16)
        if value > 0x7f: value -= 0x100
        value *= 64
        self._acceleration_sum_y += value
        self._acceleration_y[self._acceleration_index] = value
        value = int(packet[20:22], 16)
        if value > 0x7f: value -= 0x100
        value *= 64
        self._acceleration_sum_z += value
        self._acceleration_z[self._acceleration_index] = value
        self._acceleration_index += 1
        acc_x = int(self._acceleration_sum_x / self._acceleration_count)
        acc_y = int(self._acceleration_sum_y / self._acceleration_count)
        acc_z = int(self._acceleration_sum_z / self._acceleration_count)
        self._acceleration_device._put_at(0, acc_x)
        self._acceleration_device._put_at(1, acc_y)
        self._acceleration_device._put_at(2, acc_z)
        if acc_z < 2048 and acc_x > 2048 and acc_y > -1024 and acc_y < 1024: value = 1
        elif acc_z < 2048 and acc_x < -2048 and acc_y > -1024 and acc_y < 1024: value = -1
        elif acc_z < 2048 and acc_y > 2048 and acc_x > -1024 and acc_x < 1024: value = 2
        elif acc_z < 2048 and acc_y < -2048 and acc_x > -1024 and acc_x < 1024: value = -2
        elif acc_z > 3072 and acc_x > -2048 and acc_x < 2048 and acc_y > -2048 and acc_y < 2048: value = 3
        elif acc_z < -3072 and acc_x > -1024 and acc_x < 1024 and acc_y > -1024 and acc_y < 1024: value = -3
        else: value = 0
        if value != self._event_tilt:
            self._tilt_device._put(value, self._event_tilt != -4)
            self._event_tilt = value
        value = int(packet[6:10], 16)
        self._light_device._put(value)
        value = (int(packet[38:40], 16) + 300) / 100.0
        self._battery_device._put(self._calc_battery_perc(value))
        if value <= 3.55: value = 0
        elif value <= 3.59: value = 1
        else: value = 2
        if value != self._event_battery_state:
            self._battery_state_device._put(value, self._event_battery_state != -1)
            self._event_battery_state = value
        p = int(packet[10:12], 16)
        value = (p >> 7) & 0x01
        if value != self._event_play_touch:
            self._play_touch_device._put(value, self._event_play_touch != -1)
            self._event_play_touch = value
        value = (p >> 6) & 0x01
        if value != self._event_back_touch:
            self._back_touch_device._put(value, self._event_back_touch != -1)
            self._event_back_touch = value
        value = (p >> 2) & 0x01
        if value != self._event_mic_touch:
            self._mic_touch_device._put(value, self._event_mic_touch != -1)
            self._event_mic_touch = value
        value = (p >> 1) & 0x01
        if value != self._event_volume_up_touch:
            self._volume_up_touch_device._put(value, self._event_volume_up_touch != -1)
            self._event_volume_up_touch = value
        value = p & 0x01
        if value != self._event_volume_down_touch:
            self._volume_down_touch_device._put(value, self._event_volume_down_touch != -1)
            self._event_volume_down_touch = value
        self._mic_checker.check(self._event_mic_touch)
        self._volume_up_checker.check(self._event_volume_up_touch)
        self._volume_down_checker.check(self._event_volume_down_touch)
        self._play_checker.check(self._event_play_touch)
        self._back_checker.check(self._event_back_touch)
        value = self._mic_checker.is_clicked()
        if value != self._event_mic_clicked:
            self._mic_clicked_device._put_empty(value)
            self._event_mic_clicked = value
        value = self._volume_up_checker.is_clicked()
        if value != self._event_volume_up_clicked:
            self._volume_up_clicked_device._put_empty(value)
            self._event_volume_up_clicked = value
        value = self._volume_down_checker.is_clicked()
        if value != self._event_volume_down_clicked:
            self._volume_down_clicked_device._put_empty(value)
            self._event_volume_down_clicked = value
        value = self._play_checker.is_clicked()
        if value != self._event_play_clicked:
            self._play_clicked_device._put_empty(value)
            self._event_play_clicked = value
        value = self._back_checker.is_clicked()
        if value != self._event_back_clicked:
            self._back_clicked_device._put_empty(value)
            self._event_back_clicked = value
        value = self._mic_checker.is_long_pressed()
        if value != self._event_mic_long_pressed:
            self._mic_long_pressed_device._put_empty(value)
            self._event_mic_long_pressed = value
        value = self._volume_up_checker.is_long_pressed()
        if value != self._event_volume_up_long_pressed:
            self._volume_up_long_pressed_device._put_empty(value)
            self._event_volume_up_long_pressed = value
        value = self._volume_down_checker.is_long_pressed()
        if value != self._event_volume_down_long_pressed:
            self._volume_down_long_pressed_device._put_empty(value)
            self._event_volume_down_long_pressed = value
        value = self._play_checker.is_long_pressed()
        if value != self._event_play_long_pressed:
            self._play_long_pressed_device._put_empty(value)
            self._event_play_long_pressed = value
        value = self._back_checker.is_long_pressed()
        if value != self._event_back_long_pressed:
            self._back_long_pressed_device._put_empty(value)
            self._event_back_long_pressed = value
        value = self._mic_checker.is_long_long_pressed()
        if value != self._event_mic_long_long_pressed:
            self._mic_long_long_pressed_device._put_empty(value)
            self._event_mic_long_long_pressed = value
        value = self._volume_up_checker.is_long_long_pressed()
        if value != self._event_volume_up_long_long_pressed:
            self._volume_up_long_long_pressed_device._put_empty(value)
            self._event_volume_up_long_long_pressed = value
        value = self._volume_down_checker.is_long_long_pressed()
        if value != self._event_volume_down_long_long_pressed:
            self._volume_down_long_long_pressed_device._put_empty(value)
            self._event_volume_down_long_long_pressed = value
        value = self._play_checker.is_long_long_pressed()
        if value != self._event_play_long_long_pressed:
            self._play_long_long_pressed_device._put_empty(value)
            self._event_play_long_long_pressed = value
        value = self._back_checker.is_long_long_pressed()
        if value != self._event_back_long_long_pressed:
            self._back_long_long_pressed_device._put_empty(value)
            self._event_back_long_long_pressed = value
        value = int(packet[30:32], 16)
        id = (value >> 4) & 0x0f
        oid_mode = value & 0x0f
        if id != self._event_oid_mode_id:
            self._oid_mode_device._put(oid_mode, self._event_oid_mode_id != -1)
            self._event_oid_mode_id = id
        lift = 0
        if oid_mode == 0:
            value = -1
            lift = 1
            self._position_device._put_at(0, -1)
            self._position_device._put_at(1, -1)
            self._orientation_device._put(-200)
        elif oid_mode == 0x0f:
            value = -1
        else:
            if oid_mode == 1:
                value = -1
                self._position_device._put_at(0, int(packet[22:26], 16))
                self._position_device._put_at(1, int(packet[26:30], 16))
            else:
                oid_most = int(packet[22:24], 16)
                oid_high = int(packet[24:26], 16)
                oid_middle = int(packet[26:28], 16)
                oid_low = int(packet[28:30], 16)
                if oid_mode == 2:
                    if oid_most == 0 and (oid_high & 0x40) != 0 and (oid_high & 0x20) == 0:
                        value = ((oid_high & 0x03) << 16) | ((oid_middle & 0xff) << 8) | (oid_low & 0xff)
                        if value < 0x010000:
                            pass
                        elif value < 0x03fff0:
                            value = -1
                        elif value > 0x03fffb and value < 0x040000:
                            value = -1
                    else:
                        value = -2
                elif oid_mode == 3:
                    if (oid_most & 0xf0) == 0:
                        value = ((oid_most & 0x0f) << 24) | ((oid_high & 0xff) << 16) | ((oid_middle & 0xff) << 8) | (oid_low & 0xff)
                    else:
                        value = -2
                else:
                    value = -2
                if value == -2:
                    if self._event_oid == -2:
                        value = -1
                    else:
                        value = self._event_oid
                self._position_device._put_at(0, -1)
                self._position_device._put_at(1, -1)
            orientation = int(packet[32:36], 16)
            if orientation > 180: orientation -= 360
            self._orientation_device._put(orientation)
        if value != self._event_oid:
            self._oid_device._put(value, self._event_oid != -2)
            self._event_oid = value
        if lift != self._event_lift:
            self._lift_device._put(lift, self._event_lift != -1)
            self._event_lift = lift
        value = int(packet[12:16], 16)
        if value != self._event_pulse_count:
            self._pulse_count_device._put(value, self._event_pulse_count != -1)
            self._event_pulse_count = value
        state = (p >> 4) & 0x03
        if self._wheel_event == 1:
            if state == 2:
                self._wheel_count += 1
                if self._wheel_count > 5: self._wheel_event = 2
            elif state == 3:
                self._wheel_event = 2
        if self._wheel_event == 2:
            if state != self._wheel_state or self._wheel_count > 5:
                self._wheel_state = state
                self._wheel_state_device._put(state)
                if state == 2:
                    self._wheel_event = 0
                    self._wheel_count = 0
        if self._wheel_event == -1:
            self._wheel_state = state
            self._wheel_state_device._put(2)
            self._wheel_event = 0
            self._wheel_count = 0
        state = (p >> 3) & 0x01
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
