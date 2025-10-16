import AsposePDFPython
import AsposePDFPythonWrappers.devices.page_device
import AsposePDFPythonWrappers.devices.resolution


class ImageDevice(AsposePDFPythonWrappers.devices.page_device.PageDevice):
    '''An abstract class for image devices.'''

    @property
    def coordinate_type(self) -> AsposePDFPython.PageCoordinateType:
        '''Gets the page coordinate type (Media/Crop boxes). CropBox value is used by default.'''
        return AsposePDFPython.devices_image_device_get_coordinate_type(self.handle)


    @coordinate_type.setter
    def coordinate_type(self, value: AsposePDFPython.PageCoordinateType):
        '''Sets the page coordinate type (Media/Crop boxes). CropBox value is used by default.'''
        AsposePDFPython.devices_image_device_set_coordinate_type(self.handle, value)

    @property
    def resolution(self) -> AsposePDFPythonWrappers.devices.resolution.Resolution:
        '''Gets image resolution.'''
        return AsposePDFPythonWrappers.devices.resolution.Resolution(
            AsposePDFPython.devices_image_device_get_resolution(self.handle))

    @property
    def width(self) -> int:
        '''Gets image output width.'''
        return AsposePDFPython.devices_image_device_get_width(self.handle)

    @property
    def height(self) -> int:
        '''Gets image output height.'''
        return AsposePDFPython.devices_image_device_get_height(self.handle)