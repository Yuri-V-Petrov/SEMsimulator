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
import numpy as np
from PyQt5 import QtGui, QtCore, uic
from PyQt5.QtWidgets import QFileDialog
from pyqtgraph import ImageItem
from beam_calculation import Beam
from image_processing import convolution, image_open


class Microscope():
    '''
    Main class that includes all function of the microscope and its interface.

    Attributes
    ----------
    screen_width: float
        One half of the width of the screen, which was used for imaging, in mm.
        Corresponds to the width of an image with magnification 1.
        For example, if initial image was projected onto 4.5-inch-wide screen,
        screen_width = 4.5x25.4/2.

    path_to_images : string
            Path to the folder that containes Images folder.

    samples: list
        List of strings - names of sample folders available in Images folder,
        containing detector folders with images.

    sample: string
        Name of the sample folder, current sample under investigation.

    detectors: list
        List of strings - names of detector folders,
        containing magnified images.

    mags: list
        List of strings - available magnifications,
        names of image files in detector folder.

    curr_mag: integer
        Number of element in mags that is currently used.

    images: dict
        Dictionary, where keys are detectors and items are dictionaries,
        which in turn contains magnifications and images:
        {detector (string) : {magnification (integer) : image (numpy array)}.

    resolution: tuple
        Sequence of two integers, meaning number of pixels in image
        in horizontal and vertical directions correspondingly.
        default value: (256,192)

    frame: numpy array
        Numpy array corresponding to current image to be displayed via interface.

    scan_active: bool
        Current state of the scanning process.

    line: integer
        Number of current line, which is being updated during scanning.

    speed: integer
        Number of scan speed, larger number means slower scanning.

    vent: bool
        Vacuum state, True if the system is vented, False if pumped.

    pressure: float
        Pressure in the system.
        default value: 760

    pump_time: integer
        Time step of pressure decrease when pumping.

    beam_on: bool
        Current state of high voltage. True if voltage is turned on,
        False otherwise.

    hv_target: float
        Accelerating voltage to be displayed in datazone.
        default value: 15

    hv: float
        Current value of high voltage.

    beam: Beam class instance
        Beam object from beam_calculation module,
        which is used to convolve it with images and display the result.

    app: QT QApplication
        QT application to be used for user interface.

    window: QT Window instance
        Window loaded from app_interface.ui.

    user_interface: QT User_Interface instance
        User_Interface loaded from app_interface.ui.

    img: pyqtgraph ImageItem instance
        Object, containing frame and sending it to user_interface

    timer: QTimer
        Timer for scanning process.

    wobble_timer: QTimer
        Timer for periodical defocus variation.

    wobble_period: integer
        Period of focus oscillation when wobble active.
        default value:  200

    pump_timer: QTimer
        Timer for pumping process.
        default value: 50

    hv_timer: QTimer
        Timer for high voltage rise.
    '''

    def __init__(self, screen_width, path_to_images,
                 hv_target, pump_time=50,  wobble_period=200):
        '''
        Parameters
        ----------
        screen_width: float
        One half of the width of the screen, which was used for imaging, in mm.
        Corresponds to the width of an image with magnification 1.
        For example, if initial image was projected onto 4.5-inch-wide screen,
        screen_width = 4.5x25.4/2.

        path_to_images : sting
            Path to the folder that containes Images folder.
        '''

        self.path_to_images = path_to_images
        self.samples = os.listdir(f'{self.path_to_images}/Images')
        self.sample = None
        self.detectors = None
        self.mags = [1]
        self.curr_mag = 0
        self.images = {}
        self.screen_width = screen_width
        self.resolution = (256, 192)
        self.frame = np.zeros(self.resolution)
        self.scan_active = False
        self.line = 0
        self.speed = 1
        self.vent = True
        self.pressure = 760
        self.pump_time = pump_time
        self.beam_on = False
        self.hv_target = hv_target
        self.h_v = 0
        self.beam = Beam()

        self.app = QtGui.QApplication([])
        self.window = None
        self.user_interface = None
        self.img = None

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.scanning)

        self.wobble_timer = QtCore.QTimer()
        self.wobble_period = wobble_period
        self.wobble_timer.timeout.connect(self.wobble_defocus)

        self.pump_timer = QtCore.QTimer()
        self.pump_timer.timeout.connect(self.__pump)

        self.hv_timer = QtCore.QTimer()
        self.hv_timer.timeout.connect(self.__hv_rise)

    def create_interface(self):
        '''
        Create user interface from .ui file, choose inital sample to start with,
        add image as ImageItem to the frame, initialilze all timers and
        connect all sliders and buttons to their functions.

        '''

        User_Interface, Window = uic.loadUiType("app_interface.ui")

        self.app.setStyle('Fusion')
        self.user_interface = User_Interface()
        self.window = Window()
        self.user_interface.setupUi(self.window)
        self.window.show()
        self.user_interface.sample.setMaxCount(len(self.samples))
        self.user_interface.sample.insertItems(0, self.samples)
        self.user_interface.sample.activated.connect(self.sample_loading)

        self.sample_loading()

        self.img = ImageItem(border='w')
        self.img.setImage(self.frame, autoLevels=False, levels=(0, 255))
        self.user_interface.screen.setRange(QtCore.QRectF(0, 0,
                                                          *self.resolution),
                                            padding=0)
        self.user_interface.screen.addItem(self.img)

        self.user_interface.vent_pump.clicked.connect(self.vent_pump)

        self.user_interface.beamOn.clicked.connect(self.beam_on_off)

        self.user_interface.resolution.activated.connect(
            self.resolution_choice)

        self.user_interface.speed.activated.connect(self.scan_speed)

        self.user_interface.magnification_Slider.valueChanged.connect(
            self.magnification)

        self.user_interface.beam_current_Slider.valueChanged.connect(
            self.beam_current)

        self.user_interface.Focus_Slider.valueChanged.connect(self.focus)

        self.user_interface.stigmator_x_Slider.valueChanged.connect(
            self.stigm_x)

        self.user_interface.stigmator_y_Slider.valueChanged.connect(
            self.stigm_y)

        self.user_interface.alignment_x_Slider.valueChanged.connect(
            self.align_x)

        self.user_interface.alignment_y_Slider.valueChanged.connect(
            self.align_y)

        self.user_interface.start_stop.clicked.connect(self.start_stop)

        self.user_interface.wobble.stateChanged.connect(self.wobble)

        self.user_interface.actionSave_image.triggered.connect(self.save_image)

        self.app.exec_()

    def sample_loading(self):
        '''
        Prepare images for chosen sample, initialize electron beam as Beam object
        and set electron beam current and image scale.
        Update magnification slider according to the number of images of the sample.
        Update datazone bar in lower part of the frame.

        '''

        if self.scan_active:
            self.start_stop()
        self.sample = self.user_interface.sample.currentText()
        self.prepare_images()

        self.beam.beam_current =\
            self.user_interface.beam_current_Slider.value()/100
        self.beam.pixels_per_mm = self.resolution[0]\
            * self.mags[self.curr_mag]/self.screen_width
        self.user_interface.magnification_Slider.setMaximum(len(self.mags)-1)
        self.update_datazone()

    def prepare_images(self):
        '''
        Read available detectors and update detectors in interface accoringly.
        Create dictionary with images for each detector as first key and
        the magnification as the second key.

        '''
        self.detectors = os.listdir(
            f'{self.path_to_images}/Images/{self.sample}')
        self.user_interface.detector.setMaxCount(len(self.detectors))
        self.user_interface.detector.insertItems(0, self.detectors)
        self.user_interface.detector.setCurrentIndex(len(self.detectors)-1)

        self.beam = Beam()
        if self.detectors:
            self.user_interface.start_stop.setEnabled(True)
            self.mags = sorted([int(x.split('.')[0]) for x in os.listdir(
                f'{self.path_to_images}/Images/{self.sample}/{self.detectors[0]}')])

            for det in self.detectors:
                self.images[det] = {m: image_open(
                    f'{self.path_to_images}/Images/{self.sample}/{det}/{m}.tif')
                    for m in self.mags}
        else:
            self.user_interface.start_stop.setEnabled(False)

    def vent_pump(self):
        '''
        Start pumping or venting procedure.
        If the system is vented, it sets pressure to 760 and starts pump timer.
        After pump_time this timer calls function self.pump, which decreases pressure.
        If the system is pumped, it sets pressure to 760 Torr immediately.
        When the system is vented, 'beam on' button is disabled, when it is pumped,
        sample choice for loadig is disabled.

        '''
        if self.vent:
            self.vent = False
            self.user_interface.vent_pump.setText('Vent')
            self.user_interface.sample.setEnabled(False)
            self.pressure = 760
            self.pump_timer.start(self.pump_time)

        else:
            self.vent = True
            self.pump_timer.stop()
            self.user_interface.vent_pump.setText('Pump')
            self.user_interface.pressure.setText('7.60e+2 Torr')
            self.user_interface.sample.setEnabled(True)
            self.user_interface.beamOn.setEnabled(False)

    def __pump(self):
        '''
        Pumping function that decreases pressure. While pressure is above 1e-5
        it decreases by random factor ranging from 1 to 2 after pump_time,
        then the pumpig is stopped and 'beam on' button is enabled.

        '''
        if self.pressure > 1e-5:
            self.pressure *= 0.5+0.5*np.random.rand()
            self.user_interface.pressure.setText(str(format(self.pressure,
                                                            '.2e')) + ' Torr')
        else:
            self.pump_timer.stop()
            self.user_interface.beamOn.setEnabled(True)

    def beam_on_off(self):
        '''
        Switch electron beam on or swith it off.
        If the beam is on, set high voltage to 0, update datazone and enable
        venting.
        If the beam is off start hv_timer, which calls self.hv_rise after
        hv_time

        '''
        hv_time = 200
        if self.beam_on:
            self.beam_on = False
            self.h_v = 00.0
            self.update_datazone()
            self.user_interface.beamOn.setText('Beam On')
            self.user_interface.vent_pump.setEnabled(True)
        else:
            self.beam_on = True
            self.hv_timer.start(hv_time)

            self.user_interface.vent_pump.setEnabled(False)

    def __hv_rise(self):
        '''
        Increase high voltage by random step while it is less than 15 kV
        and update the datazone.

        '''
        if self.h_v < self.hv_target:
            self.h_v += np.random.rand()
            self.beam.focus = max(0.1,
                                  self.user_interface.Focus_Slider.value()/1000 -
                                  self.hv_target + self.h_v)
            self.update_datazone()
        else:
            self.h_v = self.hv_target
            self.hv_timer.stop()
            self.beam.focus = self.user_interface.Focus_Slider.value()/1000
            self.update_datazone()
            self.user_interface.beamOn.setText('Beam Off')

    def save_image(self):
        '''
        Save the image as .png file and curret microsope parameters as .txt

        '''
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(None, "SaveFile",
                                                   self.path_to_images,
                                                   "PNG Files (*.png);;All Files (*)",
                                                   options=options)

        if file_name:

            if self.scan_active:
                self.start_stop()
            img = self.user_interface.centralwidget.grab(QtCore.QRect(20, 38,
                                                                      768, 621))
            img.save(file_name, 'PNG')

            pars = open(f'{file_name}_params.txt', 'w')
            print(vars(self.beam), '\n', self.beam.beam_widths,
                  file=pars)
            pars.close()

    def start_stop(self):
        '''
        Start or stop scanning process, starting corresponding timer.
        '''

        if self.scan_active:
            self.timer.stop()
            self.scan_active = False
            self.user_interface.start_stop.setText('Start scanning')
        else:
            self.timer.start(self.speed*10)
            self.scan_active = True
            self.user_interface.start_stop.setText('Stop scanning')

    def magnification(self):
        '''
        Update current magnification from current magnification slider value.
        Update pixel size, datazone and scale bar.

        '''
        self.curr_mag = self.user_interface.magnification_Slider.value()
        self.beam.pixels_per_mm = self.resolution[0]\
            * self.mags[self.curr_mag]/self.screen_width
        self.update_datazone()
        self.user_interface.scale_bar_size.setText(
            f'{round(self.screen_width*1000*67.2/768/self.mags[self.curr_mag],2)} mkm')

    def resolution_choice(self):
        '''
        Switch frame resolution to chosen value and start new scan from
        the first line of empty image.

        '''
        self.line = 0
        text = self.user_interface.resolution.currentText()
        self.resolution = tuple(int(i) for i in text.split('x'))
        self.user_interface.screen.setRange(QtCore.QRectF(0, 0,
                                                          *self.resolution),
                                            padding=0)
        self.frame = np.zeros(self.resolution)
        self.img.setImage(self.frame)
        self.beam.size = int(self.resolution[0]/4)
        self.beam.pixels_per_mm = self.resolution[0]\
            * self.mags[self.curr_mag]/self.screen_width

    def scan_speed(self):
        '''
        Update scanning timer interval, when scan speed is changed.

        '''
        self.speed = int(self.user_interface.speed.currentText())
        self.timer.setInterval(self.speed*10)

    def scanning(self):
        '''
        Function updating frame during scanning. It reads scan speed
        and calculates the step for updating the part of the frame from line
        to line+step.
        The convolution of initial image with the beam_intensity of Beam
        is calculated, and then part of this convolution, shifted according
        to beam.center coordinates, is used to update the part of the frame.
        This part of the frame is multiplied by the beam current and some
        random noise is added. The noise depends on beam current and scan speed.
        The result is multiplied by nonlinear function of contrast slider
        value, and then some constant, depending on brightness slider value,
        is added.

        '''

        det = self.user_interface.detector.currentText()
        scale = int(512/self.resolution[0])
        step = (11 - self.speed)
        if self.line < self.resolution[1] - 1 - step:

            self.frame[:, self.line:self.line + step] = self.beam_on *\
                self.h_v/self.hv_target *\
                (convolution(self.images[det][self.mags[self.curr_mag]]
                    [192 + self.beam.center_y: 576+128 + self.beam.center_y: scale,
                     256 + self.beam.center_x: 768+128 + self.beam.center_x:scale],
                    self.beam.beam_intensity).T
                 [int(self.resolution[0]/8):int(9*self.resolution[0]/8),
                 self.line + int(self.resolution[0]/8):
                 self.line + int(self.resolution[0]/8) + step]
                 * self.beam.beam_current
                 + 10*self.beam.beam_current**0.5/self.speed**0.5
                 * np.random.rand(self.resolution[0], step))\
                * (self.user_interface.contrast_Slider.value()/30)**2\
                + self.user_interface.brightness_Slider.value()-250

            self.line += step

        elif self.line < self.resolution[1] - 1:

            self.frame[:, self.line:self.resolution[1]] = self.beam_on *\
                self.h_v/self.hv_target *\
                (convolution(self.images[det][self.mags[self.curr_mag]]
                    [192 + self.beam.center_y: 576+128 + self.beam.center_y: scale,
                     256 + self.beam.center_x: 768+128 + self.beam.center_x: scale],
                    self.beam.beam_intensity).T
                 [int(self.resolution[0]/8):int(9*self.resolution[0]/8),
                 self.line + int(self.resolution[0]/8):
                 self.resolution[1] + int(self.resolution[0]/8)]
                 * self.beam.beam_current
                 + 10*self.beam.beam_current**0.5/self.speed**0.5
                 * np.random.rand(self.resolution[0], self.resolution[1]-self.line))\
                * (self.user_interface.contrast_Slider.value()/30)**2\
                + self.user_interface.brightness_Slider.value()-250

            self.line += step
        else:
            self.line = 0

        self.img.setImage(self.frame, autoLevels=False, levels=(0, 255))

    def wobble(self):
        '''
        Turn on or off wobble of miroscope focus.
        If wobble is checked in interface, wobble_timer is started and calls
        self.wobble_defocus after wobble_period.
        self.wobble_time measures the time from the moment when wobble was checked
        in units of wobble_period.
        '''
        self.wobble_time = 0

        if self.user_interface.wobble.isChecked():
            self.wobble_timer.start(self.wobble_period)
        else:
            self.wobble_timer.stop()
            self.beam.focus = self.user_interface.Focus_Slider.value()/1000

    def wobble_defocus(self):
        '''
        Change beam focus as periodical function of wobble_time, and then
        increase wobble_time. Focus oscillates around the value of focus slider
        with amplitude controlled by wobble amplitude slider.

        '''

        self.beam.focus = self.user_interface.Focus_Slider.value()/1000\
            + self.user_interface.wobble_amp_Slider.value()/100*np.sin(self.wobble_time)

        self.wobble_time += 1

    def focus(self):
        '''
        Update beam focus from focus slider and update datazone.

        '''
        self.beam.focus = self.user_interface.Focus_Slider.value()/1000
        self.update_datazone()

    def stigm_x(self):
        '''
        Update beam stigm_x parameter from stigmator x slider.

        '''
        self.beam.stigm_x = self.user_interface.stigmator_x_Slider.value()/1000

    def stigm_y(self):
        '''
        Update beam stigm_y parameter from stigmator y slider.

        '''
        self.beam.stigm_y = self.user_interface.stigmator_y_Slider.value()/1000

    def align_x(self):
        '''
        Update beam align_x parameter from alignment x slider.

        '''
        self.beam.align_x = self.user_interface.alignment_x_Slider.value()/200

    def align_y(self):
        '''
        Update beam align_y parameter from alignment y slider.

        '''
        self.beam.align_y = self.user_interface.alignment_y_Slider.value()/200

    def beam_current(self):
        '''
        Update beam current from beam current slider and update datazone.

        '''
        self.beam.beam_current =\
            self.user_interface.beam_current_Slider.value()/100
        self.update_datazone()

    def update_datazone(self):
        '''
        Update text in datazone.
        '''
        self.user_interface.data_zone.setText(
            f'HV =  {round(self.h_v, 3)} kV     WD = {round(self.beam.focus,3)} mm\
        Mag = {self.mags[self.curr_mag]}x     Ip = {self.beam.beam_current} nA')


if __name__ == '__main__':

    absolute_path = os.path.abspath(__file__)
    dir_name = os.path.dirname(absolute_path)
    os.chdir(dir_name)

    SCREEN_WIDTH = 57.15


    microscope = Microscope(SCREEN_WIDTH, dir_name,15)
    microscope.create_interface()
