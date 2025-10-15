import AsposePDFPython


class Stamp:
    '''Class represeting stamp.'''

    def __init__(self):
        '''Construct Stamp object'''
        self.handle = AsposePDFPython.stamp_create()

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)

    def bind_image(self, image_file: str):
        '''Sets image as a stamp.

        :param: image_file: Image file name and path'''
        AsposePDFPython.stamp_bind_image(self.handle, image_file)

    def set_image_size(self, width: int, height: int):
        '''Sets size of image stamp.
           Image will be scaled according to the specified values.

        :param: width: image width
        :param: height: image height'''
        AsposePDFPython.stamp_set_image_size(self.handle, width, height)

    @property
    def rotattion(self) -> float:
        '''Gets rotation of the stamp in degrees.
        :return: rotation of the stamp in degrees'''
        return AsposePDFPython.stamp_get_rotation(self.handle)

    @rotattion.setter
    def rotation(self, value: float):
        '''Sets rotation of the stamp in degrees.
        :param: value: rotation in degrees'''
        AsposePDFPython.stamp_set_rotation(self.handle, value)