import AsposePDFPython
import AsposePDFPythonWrappers.devices.resolution
import AsposePDFPythonWrappers.devices.image_device
import AsposePDFPythonWrappers.page

from typing import overload

class PngDevice(AsposePDFPythonWrappers.devices.image_device.ImageDevice):
    '''Represents image device that helps to save pdf document pages into png. '''

    @overload
    def __init__(self):
        '''Initializes a new instance of the PngDevice class with default resolution.'''
        ...

    @overload
    def __init__(self, resolution: AsposePDFPythonWrappers.devices.resolution.Resolution):
        '''Initializes a new instance of the :class:`PngDevice` class.

        :param resolution: Resolution for the result image file, see :class:`Resolution` class.'''
        ...

    @overload
    def __init__(self, width: int, height: int, resolution: AsposePDFPythonWrappers.devices.resolution.Resolution):
        '''Initializes a new instance of the :class:`PngDevice` class with provided image dimensions and
        resolution.

        :param width: Image output width.
        :param height: Image output height.
        :param resolution: Resolution for the result image file, see :class:`Resolution` class.'''
        ...

    def __init__(self, *args):
        if len(args) == 0:
            super().__init__(AsposePDFPython.devices_png_device_create())
        elif len(args) == 1 and isinstance(args[0], AsposePDFPythonWrappers.devices.resolution.Resolution):
            super().__init__(AsposePDFPython.devices_png_device_create_from_resolution(args[0].handle))
        elif len(args) == 3 and isinstance(args[0], int) and isinstance(args[1], int) and \
                isinstance(args[2], AsposePDFPythonWrappers.devices.resolution.Resolution):
            super().__init__(AsposePDFPython.devices_png_device_create_from_width_height_resolution(args[2], args[0], args[1].handle))

    def __del__(self):
        super().__del__()