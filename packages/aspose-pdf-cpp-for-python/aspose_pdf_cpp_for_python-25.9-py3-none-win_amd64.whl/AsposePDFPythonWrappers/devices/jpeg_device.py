import AsposePDFPython
import AsposePDFPythonWrappers.devices.resolution
import AsposePDFPythonWrappers.devices.image_device

class JpegDevice(AsposePDFPythonWrappers.devices.image_device.ImageDevice):
    '''Represents image device that helps to save pdf document pages into jpeg.'''

    def __init__(self, width: int, height: int, resolution: AsposePDFPythonWrappers.devices.resolution.Resolution):
        '''Initializes a new instance of the :class:`JpegDevice` class with provided image dimensions,
        resolution and maximum quality.

        :param width: Image output width.
        :param height: Image output height.
        :param resolution: Resolution for the result image file, see :class:`Resolution` class.'''
        super().__init__(AsposePDFPython.devices_jpeg_device_create_from_width_height_resolution(width, height, resolution.handle))

    def __del__(self):
        super().__del__()
