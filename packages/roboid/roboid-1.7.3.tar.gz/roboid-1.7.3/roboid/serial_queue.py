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


class WriteQueue(object):
    def __init__(self, size):
        self.set_size(size)
        self._output = [0] * 19

    def set_size(self, size):
        self._buffer = bytearray(size)
        self._mask = size - 1
        self._provider = 0
        self._consumer = 0

    def reset(self):
        self._provider = 0
        self._consumer = 0

    def push(self, text, line):
        buffer = self._buffer
        mask = self._mask
        provider = self._provider
        consumer = self._consumer

        text = text.encode()
        length = len(text)
        if length > 0:
            for i in range(length):
                if ((provider - consumer) & mask) == mask:
                    consumer = (consumer + 1) & mask
                buffer[provider] = text[i]
                provider = (provider + 1) & mask
        if line:
            if ((provider - consumer) & mask) == mask:
                consumer = (consumer + 1) & mask
            buffer[provider] = ord("\r")
            provider = (provider + 1) & mask
        self._provider = provider
        self._consumer = consumer

    def pop(self):
        provider = self._provider
        consumer = self._consumer
        if provider == consumer: return None

        buffer = self._buffer
        mask = self._mask
        output = self._output
        length = (provider - consumer) & mask
        if length > 18: length = 18

        output[0] = length
        start = length + 1
        for i in range(1, length + 1):
            if provider == consumer:
                start = i
                break
            output[i] = buffer[consumer]
            consumer = (consumer + 1) & mask
        if start < 19:
            for i in range(start, 19):
                output[i] = 0
        self._consumer = consumer
        return output


class ReadQueue(object):
    def __init__(self, size):
        self.set_size(size)

    def set_size(self, size):
        self._buffer = bytearray(size)
        self._mask = size - 1
        self._provider = 0
        self._consumer = 0

    def reset(self):
        self._provider = 0
        self._consumer = 0

    def push(self, packet, offset=0):
        length = packet[offset]
        if length > 0:
            if length > 18: length = 18
            buffer = self._buffer
            mask = self._mask
            provider = self._provider
            consumer = self._consumer
            end = length + offset
            for i in range(1 + offset, end + 1):
                if ((provider - consumer) & mask) == mask:
                    consumer = (consumer + 1) & mask
                buffer[provider] = packet[i]
                provider = (provider + 1) & mask
            self._provider = provider
            self._consumer = consumer

    def pop(self, delimiter):
        provider = self._provider
        consumer = self._consumer
        if provider == consumer: return None

        buffer = self._buffer
        mask = self._mask
        if delimiter == 0:
            output = bytearray()
            while consumer != provider:
                output.append(buffer[consumer])
                consumer = (consumer + 1) & mask
            self._consumer = consumer
            return output.decode("utf-8")
        else:
            found = -1
            while consumer != provider:
                if buffer[consumer] == delimiter:
                    found = consumer
                    break
                consumer = (consumer + 1) & mask
            if found >= 0:
                consumer = self._consumer
                output = bytearray()
                while consumer != found:
                    output.append(buffer[consumer])
                    consumer = (consumer + 1) & mask
                self._consumer = (consumer + 1) & mask
                return output.decode("utf-8")
        return None
