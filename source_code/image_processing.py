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
from PIL import Image

def image_open(path):
    '''
    This function opens image file as 2D numpy array.
    RGB image is converted into grayscale image.

    Parameters
    ----------
    path : string
        Path to image file.

    Returns
    -------
    img_grey : 2D numpy array
        Image as numpy array with grayscale values.

    '''
    img = np.asarray(Image.open(path))
    if len(img.shape) == 3:
        rgb_weights = [0.2989, 0.5870, 0.1140]
        img_grey = np.rint(np.dot(img[..., :3], rgb_weights)).astype(int)
    else:
        img_grey = img
    return img_grey



def convolution(image, kernel):
    '''
    FFT-based convolution of two numpy arrays: image and kernel

    Parameters
    ----------
    image : 2D numpy array
        Initial image to process.
    kernel : 2D numpy array
        Kernel to convolve initial image with it.
        If its shape is not equal to the one of the image,
        then it will be cropped or padded with zeros.

    Returns
    -------
    result : 2D numpy array
        Resulting array after the convolution.

    '''

    f_1 = np.fft.rfft2(image)
    f_2 = np.fft.rfft2(kernel, image.shape)
    result = np.fft.irfft2(f_1*f_2)
    return result
