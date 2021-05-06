# -*- coding: utf-8 -*-
'''
    Copyright (C) 2021  Yuri Petrov

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
'''
import os
import sys

dir_name = os.path.dirname(os.path.abspath(__file__))
os.chdir(dir_name)
sys.path.append(dir_name)
from microscope import Microscope

SCREEN_WIDTH = 57.15
PATH_TO_IMAGES = dir_name
HV_TARGET = 15


microscope = Microscope(SCREEN_WIDTH, PATH_TO_IMAGES, HV_TARGET)
microscope.create_interface()
