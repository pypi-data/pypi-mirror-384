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
from roboid.model import DeviceType
from roboid.model import DataType
from roboid.model import Roboid
from roboid.connector import Result
from roboid.raccoon import Raccoon
from roboid.serial_connector import SerialConnector


class RaccoonConnectionChecker(object):
    def __init__(self, roboid):
        self._roboid = roboid

    def check(self, info):
        return info[1].startswith("Raccoon") and info[2] == "30"


class RaccoonRoboid(Roboid):
    _SOUNDS = {
        Raccoon.SOUND_OFF: 0x00,
        Raccoon.SOUND_BEEP: 0x01,
        Raccoon.SOUND_RANDOM_BEEP: 0x05,
        Raccoon.SOUND_NOISE: 0x07,
        Raccoon.SOUND_SIREN: 0x09,
        Raccoon.SOUND_ENGINE: 0x0b,
        Raccoon.SOUND_CHOP: 0x12,
        Raccoon.SOUND_ROBOT: 0x15,
        Raccoon.SOUND_DIBIDIBIDIP: 0x21,
        Raccoon.SOUND_GOOD_JOB: 0x22,
        Raccoon.SOUND_RANDOM_MELODY: 0x14,
        Raccoon.SOUND_WAKE_UP: 0x23,
        Raccoon.SOUND_START: 0x24,
        Raccoon.SOUND_BYE: 0x25
    }
    _STEP_TO_DEG = 360.0 / 4096.0
    _DEG_TO_STEP = 4096.0 / 360.0
    _PACKET_NORMAL = 1
    _PACKET_EXT = 2

    def __init__(self, index):
        super(RaccoonRoboid, self).__init__(Raccoon.ID, "Raccoon", 0x03000000)
        self._index = index
        self._connector = None
        self._ready = False
        self._thread = None
        self._thread_lock = threading.Lock()

        self._joint_velocity = [0, 0, 0, 0]
        self._joint_speed = 100
        self._joint_angle = [0, 0, 0, 0]
        self._note = 0
        self._sound = 0
        self._joint_mode = 0
        self._write_ext = [0x30, 0, 0, 0, 0, 0, 0, 0]

        self._joint_angle_written = False
        self._note_written = False
        self._sound_written = False
        self._joint_mode_written = False
        self._write_ext_written = False

        self._joint_angle_id = 0
        self._current_sound = 0
        self._sound_repeat = 1
        self._sound_id = 0
        self._sound_event = 0
        self._sound_state_id = -1

        self._event_teach_button = -1
        self._event_playback_button = -1
        self._event_delete_button = -1
        self._event_teach_clicked_id = -1
        self._event_playback_clicked_id = -1
        self._event_delete_clicked_id = -1
        self._event_teach_long_pressed_id = -1
        self._event_playback_long_pressed_id = -1
        self._event_delete_long_pressed_id = -1
        
        self._event_warning = -1
        self._event_moving = -1
        self._event_collision_1_id = -1
        self._event_collision_2_id = -1
        self._event_collision_3_id = -1
        self._event_collision_4_id = -1
        self._event_joint_state_id = -1
        self._event_battery_state = -1
        self._event_charge_state = -1
        
        self._packet_sent = 0
        self._packet_received = 0

        self._create_model()

    def _create_model(self):
        from roboid.raccoon import Raccoon
        dict = self._device_dict = {}
        dict[Raccoon.JOINT_VELOCITY] = self._joint_velocity_device = self._add_device(Raccoon.JOINT_VELOCITY, "JointVelocity", DeviceType.EFFECTOR, DataType.INTEGER, 4, -100, 100, 0)
        dict[Raccoon.JOINT_SPEED] = self._joint_speed_device = self._add_device(Raccoon.JOINT_SPEED, "JointSpeed", DeviceType.EFFECTOR, DataType.INTEGER, 1, 0, 100, 100)
        dict[Raccoon.JOINT_ANGLE] = self._joint_angle_device = self._add_device(Raccoon.JOINT_ANGLE, "JointAngle", DeviceType.COMMAND, DataType.INTEGER, 4, -180, 179, 0)
        dict[Raccoon.NOTE] = self._note_device = self._add_device(Raccoon.NOTE, "Note", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 88, 0)
        dict[Raccoon.SOUND] = self._sound_device = self._add_device(Raccoon.SOUND, "Sound", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 127, 0)
        dict[Raccoon.JOINT_MODE] = self._joint_mode_device = self._add_device(Raccoon.JOINT_MODE, "JointMode", DeviceType.COMMAND, DataType.INTEGER, 1, 0, 255, 0)
        dict[Raccoon.WRITE_EXT] = self._write_ext_device = self._add_device(Raccoon.WRITE_EXT, "WriteExt", DeviceType.COMMAND, DataType.INTEGER, 8, 0, 255, 0)
        dict[Raccoon.SIGNAL_STRENGTH] = self._signal_strength_device = self._add_device(Raccoon.SIGNAL_STRENGTH, "SignalStrength", DeviceType.SENSOR, DataType.INTEGER, 1, -128, 0, 0)
        dict[Raccoon.ENCODER] = self._encoder_device = self._add_device(Raccoon.ENCODER, "Encoder", DeviceType.SENSOR, DataType.INTEGER, 4, -180, 179, 0)
        dict[Raccoon.TEACH_BUTTON] = self._teach_button_device = self._add_device(Raccoon.TEACH_BUTTON, "TeachButton", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Raccoon.PLAYBACK_BUTTON] = self._playback_button_device = self._add_device(Raccoon.PLAYBACK_BUTTON, "PlaybackButton", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Raccoon.DELETE_BUTTON] = self._delete_button_device = self._add_device(Raccoon.DELETE_BUTTON, "DeleteButton", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Raccoon.TEACH_CLICKED] = self._teach_clicked_device = self._add_device(Raccoon.TEACH_CLICKED, "TeachClicked", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Raccoon.PLAYBACK_CLICKED] = self._playback_clicked_device = self._add_device(Raccoon.PLAYBACK_CLICKED, "PlaybackClicked", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Raccoon.DELETE_CLICKED] = self._delete_clicked_device = self._add_device(Raccoon.DELETE_CLICKED, "DeleteClicked", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Raccoon.TEACH_LONG_PRESSED] = self._teach_long_pressed_device = self._add_device(Raccoon.TEACH_LONG_PRESSED, "TeachLongPressed", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Raccoon.PLAYBACK_LONG_PRESSED] = self._playback_long_pressed_device = self._add_device(Raccoon.PLAYBACK_LONG_PRESSED, "PlaybackLongPressed", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Raccoon.DELETE_LONG_PRESSED] = self._delete_long_pressed_device = self._add_device(Raccoon.DELETE_LONG_PRESSED, "DeleteLongPressed", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Raccoon.WARNING] = self._warning_device = self._add_device(Raccoon.WARNING, "Warning", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Raccoon.MOVING] = self._moving_device = self._add_device(Raccoon.MOVING, "Moving", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Raccoon.COLLISION_1] = self._collision_1_device = self._add_device(Raccoon.COLLISION_1, "Collision1", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Raccoon.COLLISION_2] = self._collision_2_device = self._add_device(Raccoon.COLLISION_2, "Collision2", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Raccoon.COLLISION_3] = self._collision_3_device = self._add_device(Raccoon.COLLISION_3, "Collision3", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Raccoon.COLLISION_4] = self._collision_4_device = self._add_device(Raccoon.COLLISION_4, "Collision4", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Raccoon.JOINT_STATE] = self._joint_state_device = self._add_device(Raccoon.JOINT_STATE, "JointState", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Raccoon.SOUND_STATE] = self._sound_state_device = self._add_device(Raccoon.SOUND_STATE, "SoundState", DeviceType.EVENT, DataType.INTEGER, 0, 0, 0, 0)
        dict[Raccoon.BATTERY_STATE] = self._battery_state_device = self._add_device(Raccoon.BATTERY_STATE, "BatteryState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 2, 2)
        dict[Raccoon.CHARGE_STATE] = self._charge_state_device = self._add_device(Raccoon.CHARGE_STATE, "ChargeState", DeviceType.EVENT, DataType.INTEGER, 1, 0, 1, 0)
        dict[Raccoon.READ_EXT] = self._read_ext_device = self._add_device(Raccoon.READ_EXT, "ReadExt", DeviceType.EVENT, DataType.INTEGER, 8, 0, 255, 0)
        
        self._joint_angle_device.write((0, -10, -140, 60))

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

        tag = "Raccoon[{}]".format(self._index)
        self._connector = SerialConnector(tag, RaccoonConnectionChecker(self))
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
            super(RaccoonRoboid, self)._dispose()
            self._release()

    def _reset(self):
        super(RaccoonRoboid, self)._reset()

        self._joint_velocity = [0, 0, 0, 0]
        self._joint_speed = 100
        self._joint_angle = [0, 0, 0, 0]
        self._note = 0
        self._sound = 0
        self._joint_mode = 0
        self._write_ext = [0x30, 0, 0, 0, 0, 0, 0, 0]

        self._joint_angle_written = False
        self._note_written = False
        self._sound_written = False
        self._joint_mode_written = False
        self._write_ext_written = False

        self._current_sound = 0
        self._sound_repeat = 1
        self._sound_event = 0
        self._sound_state_id = -1

        self._event_teach_button = -1
        self._event_playback_button = -1
        self._event_delete_button = -1
        self._event_teach_clicked_id = -1
        self._event_playback_clicked_id = -1
        self._event_delete_clicked_id = -1
        self._event_teach_long_pressed_id = -1
        self._event_playback_long_pressed_id = -1
        self._event_delete_long_pressed_id = -1
        self._event_warning = -1
        self._event_moving = -1
        self._event_collision_1_id = -1
        self._event_collision_2_id = -1
        self._event_collision_3_id = -1
        self._event_collision_4_id = -1
        self._event_joint_state_id = -1
        self._event_battery_state = -1
        self._event_charge_state = -1
        
        self._packet_sent = 0
        self._packet_received = 0

    def _request_motoring_data(self):
        with self._thread_lock:
            self._joint_velocity_device.read(self._joint_velocity)
            self._joint_speed = self._joint_speed_device.read()
            if self._joint_angle_device._is_written():
                self._joint_angle_device.read(self._joint_angle)
                self._joint_angle_written = True
            if self._note_device._is_written():
                self._note = self._note_device.read()
                self._note_written = True
            if self._sound_device._is_written():
                self._sound = self._sound_device.read()
                self._sound_written = True
            if self._joint_mode_device._is_written():
                self._joint_mode = self._joint_mode_device.read()
                self._joint_mode_written = True
            if self._write_ext_device._is_written():
                self._write_ext_device.read(self._write_ext)
                self._write_ext_written = True
        self._clear_written()

    def _get_sound(self, sound):
        if isinstance(sound, (int, float)):
            sound = int(sound)
            if sound in RaccoonRoboid._SOUNDS:
                return RaccoonRoboid._SOUNDS[sound]
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

    def _verify_velocity(self, vel):
        if int(vel) == 0: return 127
        elif vel < -100: return -100
        elif vel > 100: return 100
        return vel

    def _deg_to_step(self, index, deg):
        if index == 0:
            if deg < -120: return -120
            elif deg > 120: return 120
        elif index == 1:
            if deg < -90: return -90
            elif deg > 30: return 30
        elif index == 2:
            if deg < -150: return -150
            elif deg > 0: return 0
        elif index == 3:
            if deg < -105: return -105
            elif deg > 105: return 105
        step = round(deg * RaccoonRoboid._DEG_TO_STEP)
        if step < -2048: return -2048
        elif step > 2047: return 2047
        return step

    def _verify_speed(self, speed):
        if speed < 0: return 0
        elif speed > 100: return 100
        return speed

    def _encode_motoring_packet(self, address):
        result = ""
        with self._thread_lock:
            if self._joint_mode == Raccoon.JOINT_MODE_ANGLE or self._joint_mode == Raccoon.JOINT_MODE_ANGLE_HORZ or self._joint_mode == Raccoon.JOINT_MODE_ANGLE_VERT: # angle mode
                if self._joint_mode == Raccoon.JOINT_MODE_ANGLE_HORZ:
                    result = "1C"
                elif self._joint_mode == Raccoon.JOINT_MODE_ANGLE_VERT:
                    result = "1D"
                else:
                    result = "11"
                if self._joint_angle_written:
                    self._joint_angle_id = (self._joint_angle_id % 255) + 1
                self._joint_angle_written = False
                result += self._to_hex(self._joint_angle_id)
                result += self._to_hex2(self._deg_to_step(0, self._joint_angle[0]))
                result += self._to_hex2(self._deg_to_step(1, self._joint_angle[1]))
                result += self._to_hex2(self._deg_to_step(2, self._joint_angle[2]))
                result += self._to_hex2(self._deg_to_step(3, self._joint_angle[3]))
                result += self._to_hex(self._verify_speed(self._joint_speed))
                result += '00'
            else: # velocity
                if self._joint_mode == Raccoon.JOINT_MODE_VELOCITY_HORZ:
                    result = "1A"
                elif self._joint_mode == Raccoon.JOINT_MODE_VELOCITY_VERT:
                    result = "1B"
                else:
                    result = "10"
                for i in range(4):
                    result += self._to_hex(self._verify_velocity(self._joint_velocity[i]))
                result += '00000000000000'
            
            if self._packet_sent != RaccoonRoboid._PACKET_NORMAL:
                self._packet_sent = RaccoonRoboid._PACKET_NORMAL
                result += '0000000000'
                
                temp = self._get_sound(self._sound)
                if self._note_written or self._sound_written:
                    self._sound_id = (self._sound_id % 255) + 1
                if self._sound_written:
                    if temp > 0:
                        self._sound_event = 1
                    else:
                        self._sound_event = 0
                result += self._to_hex(self._sound_id)
                if temp > 0:
                    result += self._to_hex(temp + 128)
                elif self._note > 0:
                    result += self._to_hex(self._note & 0x7f)
                else:
                    result += '00'
                self._note_written = False
                self._sound_written = False
                result += '00'
            else:
                self._packet_sent = RaccoonRoboid._PACKET_EXT
                for i in range(8):
                    result += self._to_hex(self._write_ext[i])
            result += "-"
            result += address
            result += "\r"
            return result

    def _decode_sensory_packet(self, packet):
        self._packet_received = 0
        
        packet = str(packet)
        value = int(packet[0:1], 16)
        if value != 1: return False
        
        value = int(packet[2:6], 16)
        if value > 0x7fff: value -= 0x10000
        self._encoder_device._put_at(0, value * RaccoonRoboid._STEP_TO_DEG)
        value = int(packet[6:10], 16)
        if value > 0x7fff: value -= 0x10000
        self._encoder_device._put_at(1, value * RaccoonRoboid._STEP_TO_DEG)
        value = int(packet[10:14], 16)
        if value > 0x7fff: value -= 0x10000
        self._encoder_device._put_at(2, value * RaccoonRoboid._STEP_TO_DEG)
        value = int(packet[14:18], 16)
        if value > 0x7fff: value -= 0x10000
        self._encoder_device._put_at(3, value * RaccoonRoboid._STEP_TO_DEG)
        
        value = int(packet[20:22], 16)
        state = (value >> 7) & 0x01
        if state != self._event_warning:
            self._warning_device._put(state, self._event_warning != -1)
            self._event_warning = state
        
        state = (value >> 6) & 0x01
        if state != self._event_moving:
            self._moving_device._put(state, self._event_moving != -1)
            self._event_moving = state
        
        id = (value >> 4) & 0x03
        if id != self._event_joint_state_id and self._event_joint_state_id != -1:
            self._joint_state_device._put_empty()
        self._event_joint_state_id = id
        
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
        
        state = (value >> 1) & 0x01
        if state != self._event_charge_state:
            self._charge_state_device._put(state, self._event_charge_state != -1)
            self._event_charge_state = state
        
        value = int(packet[22:24], 16)
        id = (value >> 6) & 0x03
        if id != self._event_collision_4_id and self._event_collision_4_id != -1:
            self._collision_4_device._put_empty()
        self._event_collision_4_id = id
        id = (value >> 4) & 0x03
        if id != self._event_collision_3_id and self._event_collision_3_id != -1:
            self._collision_3_device._put_empty()
        self._event_collision_3_id = id
        id = (value >> 2) & 0x03
        if id != self._event_collision_2_id and self._event_collision_2_id != -1:
            self._collision_2_device._put_empty()
        self._event_collision_2_id = id
        id = value & 0x03
        if id != self._event_collision_1_id and self._event_collision_1_id != -1:
            self._collision_1_device._put_empty()
        self._event_collision_1_id = id
        
        value = int(packet[24:26], 16)
        slot = (value >> 4) & 0x0f
        dev_id = value & 0x0f
        
        if slot == 0:
            value = int(packet[26:28], 16)
            state = value & 0x01
            if state != self._event_teach_button:
                self._teach_button_device._put(state, self._event_teach_button != -1)
                self._event_teach_button = state
            state = (value >> 1) & 0x01
            if state != self._event_playback_button:
                self._playback_button_device._put(state, self._event_playback_button != -1)
                self._event_playback_button = state
            state = (value >> 3) & 0x01
            if state != self._event_delete_button:
                self._delete_button_device._put(state, self._event_delete_button != -1)
                self._event_delete_button = state
            value = int(packet[28:30], 16)
            id = value & 0x03
            if id != self._event_teach_clicked_id and self._event_teach_clicked_id != -1:
                self._teach_clicked_device._put_empty()
            self._event_teach_clicked_id = id
            id = (value >> 2) & 0x03
            if id != self._event_playback_clicked_id and self._event_playback_clicked_id != -1:
                self._playback_clicked_device._put_empty()
            self._event_playback_clicked_id = id
            id = (value >> 6) & 0x03
            if id != self._event_delete_clicked_id and self._event_delete_clicked_id != -1:
                self._delete_clicked_device._put_empty()
            self._event_delete_clicked_id = id
            value = int(packet[30:32], 16)
            id = value & 0x03
            if id != self._event_teach_long_pressed_id and self._event_teach_long_pressed_id != -1:
                self._teach_long_pressed_device._put_empty()
            self._event_teach_long_pressed_id = id
            id = (value >> 2) & 0x03
            if id != self._event_playback_long_pressed_id and self._event_playback_long_pressed_id != -1:
                self._playback_long_pressed_device._put_empty()
            self._event_playback_long_pressed_id = id
            id = (value >> 6) & 0x03
            if id != self._event_delete_long_pressed_id and self._event_delete_long_pressed_id != -1:
                self._delete_long_pressed_device._put_empty()
            self._event_delete_long_pressed_id = id
            
            value = int(packet[36:38], 16)
            value -= 0x100
            self._signal_strength_device._put(value)
            
            value = int(packet[38:40], 16)
            value = (value + 200) / 100.0
            state = 2
            if value < 3.25: state = 0
            elif value < 3.45: state = 1
            if state != self._event_battery_state:
                self._battery_state_device._put(state, self._event_battery_state != -1)
                self._event_battery_state = state
            self._packet_received = RaccoonRoboid._PACKET_NORMAL
        else:
            self._packet_received = RaccoonRoboid._PACKET_EXT
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
