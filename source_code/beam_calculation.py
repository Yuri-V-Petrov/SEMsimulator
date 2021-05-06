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
import numpy as np


class Beam():
    '''
    Attributes
    ----------
    z_position: float
        Random distance from the lens to the sample, from 5 to 15 mm.

    pixels_per_mm: float
        Number o pixels per mm, required to convert mm to pixels,
        depends on digital image resolution and magnification.
        Default value: 256/57.15*100
        It corresponds to the resolution of 256x192 and magnificatio of 100x,
        if inital image was projected onto the screen of 3.5x4.5 inches


    astigm_x,y: float
        Random astigmatism of the column, mm of defocus.

    misalign_x,y: float
        Random aperture misalignment, from -0.05 to 0.05 mm.

    focus : float
        Focal length of the lens, in mm. Initial value = 0.1 mm

    stigm_x,y : float
        Astigmatism compensation from stigmator in x or y direction,
        mm of defocus.
        Default value: 0

    align_x,y : float
        Aperture alignment in x or y direction, in mm.
        Default value: 0

    beam_current : float
        Beam current, nA.
        Default value: 1

    center_x,y: integer
        Coordinates of the beam center in sample plane, in pixels

    beam_intensity: 2D numpy array
        Distribution of the beam intensity in sample plane (in pixels)
        to convolve it with the sample.

    beam_widths: tuple=(float,float)
        Beam halfwidth in x and y directions, nanometers

    convergence: float
        Beam convergence angle in radians
    '''

    def __init__(self):

        self.z_position = 15-np.random.random()*10

        self.pixels_per_mm = 256/57.15*100

        self.astigm_x = np.random.random()-0.5
        self.astigm_y = np.random.random()-0.5

        self.misalign_x = 0.4*np.random.random()-0.2
        self.misalign_y = 0.4*np.random.random()-0.2

        self.focus = 0.1
        self.stigm_x = 0
        self.stigm_y = 0
        self.align_x = 0
        self.align_y = 0
        self.beam_current = 1
        self.convergence = 0.01
        self.size = 64

    @ property
    def __defocus(self):
        return self.focus - self.z_position

    @ property
    def center_x(self):
        '''
        Calculates beam center shift in x direction

        Returns
        -------
        integer
            Beam shift in pixels

        '''
        c_x = int((self.align_x - self.misalign_x)*self.__defocus /
                  self.focus*self.pixels_per_mm)
        return min(abs(c_x), 96)*np.sign(c_x)

    @ property
    def center_y(self):
        '''
        Calculates beam center shift in y direction

        Returns
        -------
        integer
            Beam shift in pixels

        '''
        c_y = int((self.align_y - self.misalign_y)*self.__defocus /
                  self.focus*self.pixels_per_mm)
        return min(abs(c_y), 49)*np.sign(c_y)

    @ property
    def __sigma2_x_mm(self):
        return ((self.__defocus + abs(self.align_x - self.misalign_x)*10**-2
                 + abs(self.stigm_x + self.astigm_x))
                * self.convergence)**2 + 10**-16*(1 +
                                                  100*self.beam_current)**3/4

    @ property
    def __sigma2_y_mm(self):
        return ((self.__defocus + abs(self.align_y - self.misalign_y)*10**-2
                 + abs(self.stigm_y + self.astigm_y))
                * self.convergence)**2 + 10**-16*(1 +
                                                  100*self.beam_current)**3/4

    @ property
    def __sigma2_x_px(self):
        return self.__sigma2_x_mm*self.pixels_per_mm**2

    @ property
    def __sigma2_y_px(self):
        return self.__sigma2_y_mm*self.pixels_per_mm**2

    @ property
    def __astig_angle(self):
        return np.arctan((self.stigm_x + self.astigm_x
                          )/(self.stigm_y + self.astigm_y))/2

    @ property
    def beam_intensity(self):
        '''
        Distribution of the beam intensity in sample plane

        Returns
        -------
        2D numpy array
            Beam intensity as a function of pixel number

        '''

        def gauss(i, j):
            '''
            Parameters
            ----------
            i : integer
                Y coordinate.
            j : integer
                X coordinate.

            Returns
            -------
            gauss : float
                Value of rotated 2D-gaussian in point with coordinates j,i.
            '''
            gauss = np.exp(-(j - self.size/2)**2*(
                np.cos(self.__astig_angle)**2/self.__sigma2_x_px +
                np.sin(self.__astig_angle)**2/self.__sigma2_y_px)
                - (i - self.size/2)**2 *
                (np.sin(self.__astig_angle)**2/self.__sigma2_x_px +
                 np.cos(self.__astig_angle)**2/self.__sigma2_y_px) +
                (i - self.size/2)*(j - self.size/2) *
                np.sin(2*self.__astig_angle) *
                (1/self.__sigma2_y_px - 1/self.__sigma2_x_px))

            return gauss

        raw_gauss = np.fromfunction(gauss, (self.size, self.size))
        gauss_intensity = raw_gauss/raw_gauss.sum()

        return gauss_intensity

    @ property
    def beam_widths(self):
        '''
        Beam width in x and y direction, in nanometers
        '''
        return (10**6*self.__sigma2_x_mm**0.5, 10**6*self.__sigma2_y_mm**0.5)
