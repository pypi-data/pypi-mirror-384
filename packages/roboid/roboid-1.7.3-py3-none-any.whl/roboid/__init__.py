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

import signal

from roboid.scanner import Scanner
from roboid.keyboard import Keyboard
from roboid.runner import Runner
from roboid.model import DeviceType
from roboid.model import DataType
from roboid.hamster import Hamster
from roboid.hamster_s import HamsterS
from roboid.turtle import Turtle
from roboid.albert_ai import AlbertAi
from roboid.zerone import Zerone
from roboid.beagle import Beagle
from roboid.pio import Pio
from roboid.raccoon import Raccoon
from roboid.grid import GridHamster
from roboid.grid import GridHamsterS
from roboid.grid import GridTurtle
from roboid.grid import GridAlbertAi
from roboid.grid import GridZerone

__version__ = "1.7.3"

__all__ = ["DeviceType", "DataType", "Hamster", "GridHamster", "HamsterS", "GridHamsterS", "Turtle", "GridTurtle", "AlbertAi", "GridAlbertAi", "Zerone", "GridZerone", "Beagle", "Pio", "Raccoon", "Keyboard", "scan", "dispose", "set_executable", "wait", "wait_until_ready", "wait_until", "when_do", "while_do", "parallel"]

def scan():
    Scanner.scan()

def dispose():
    Runner.dispose_all()

def set_executable(execute):
    Runner.set_executable(execute)

def wait(milliseconds):
    Runner.wait(milliseconds)

def wait_until_ready():
    Runner.wait_until_ready()

def wait_until(condition, args=None):
    Runner.wait_until(condition, args)

def when_do(condition, do, args=None):
    Runner.when_do(condition, do, args)

def while_do(condition, do, args=None):
    Runner.while_do(condition, do, args)

def parallel(*functions):
    Runner.parallel(functions)

def _handle_signal(signal, frame):
    Runner.shutdown()
    raise SystemExit

signal.signal(signal.SIGINT, _handle_signal)
