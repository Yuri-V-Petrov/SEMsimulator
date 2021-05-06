# SEMsimulator
## What is SEMsimulator?
It is a Python based simulator of a scanning electron microscope (SEM), developed for educational purposes. It helps to train people to perform simple alignment and focusing of a scanning electron microscope without a microscope. The idea of this script is live processing of previously captured images. Therefore, a set of SEM images (at least one image) is required.
## Requirements:
Screen resolution better than 1200x800.
### Libraries
* numpy
* PIL
* PyQt5
* pyqtgraph

For details see [requirements.txt](/requirements.txt)
## Installation
Just clone this repository or download all files with a source code.
## Image preparation
Since this simulator interactively processes images, previously captured by real scanning electron microscope, folder with images is required as well. 

Images folder should contain folders named as samples to investigate.

Each folder of the sample should contain at least one folder named as available detectors, and each folder of detector in turn should contain images. 
Image files should be named as corresponding magnification values. Each detector folder should contain images for the same set fo magifications. The simulator is optimized for 1024x768 images. Smaller ones may cause errors, using larger ones doesn't make sense, as can be understood from the description below.

File structure example:

```
  |-- Images
        |-- Sample 1
              |-- Detector 1
                    |-- 100.tif
                    |-- 200.tif
                    |-- 500.tif
              |-- Detector 2
                    |-- 100.tif
                    |-- 200.tif
                    |-- 500.tif
        |-- Sample 2
        ... ...
```
By default the script searces for "Images" folder within the folder of its location, but you can specify another location using `PATH_TO_IMAGES` variable in [`simulator_main.py`](/source%20code/simulator_main.py).

Images folder with sample for testing is included.
## Using simulator
### Configuration parameters
In `simulator_main.py`use `PATH_TO_IMAGES` to show, where the images are located, `HV_TARGET` to specify accelerating voltage in kV, which was used for image acquisition, 
and `SCREEN_WIDTH` for the halfwidth of real microscope screen in mm. The last parameter is used for calibration of pixel size in image, by default it equals 57.15 mm that corresponds to 4.5-inch-wide screen.

Besides abovementioned parameters, some other parameters of the microscope can be specified using `Microscope` class of the [`microscope` module](https://github.com/Yuri-V-Petrov/SEMsimulator/blob/main/source%20code/microscope.py) module.

### Running the code
Start `simulator_main.py`script to open microscope main window.

<img src= "/microscope_window.png" width="500">

As one can see, it contains various settings of the scanning electron microscope, which are intuitively clear (at least for people who deal with SEM).

Keep in mind that not whole image is represented during scanning, but its 512x384 part only, which can be shifted from the center because of the column misalignment. Therefore, if images larger than 1024x768 are used, most part of the image is never visible in the simulator.

<img src= "/image.png" width="200">

When focusing is finished, image can be saved using `Save` menu in the top left corner. Besides .PNG image, params.txt file is saved nearby. 
The first line of this .txt file contains attributes of `Beam` class (see [`beam_calculation` module](/source%20code/beam_calculation.py)). The second line contains beam halfwidths in nm.
