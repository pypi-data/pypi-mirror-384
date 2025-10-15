import AsposePDFPython

class Stamp:
    '''An abstract class for various kinds of stamps which come as descendants.'''
    def __init__(self, handle):
        self.handle = handle

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)

    @property
    def background(self) -> bool:
        '''Gets a bool value that indicates the content is stamped as background.
        If the value is true, the stamp content is layed at the bottom.
        By defalt, the value is false, the stamp content is layed at the top.'''
        return AsposePDFPython.stamp_get_background(self.handle)

    @background.setter
    def background(self, value: bool):
        '''Sets a bool value that indicates the content is stamped as background.
        If the value is true, the stamp content is layed at the bottom.
        By defalt, the value is false, the stamp content is layed at the top.'''
        AsposePDFPython.stamp_set_background(self.handle, value)

    @property
    def x_indent(self) -> float:
        '''Horizontal stamp coordinate, starting from the left.'''
        return  AsposePDFPython.stamp_get_x_indent(self.handle)

    @x_indent.setter
    def x_indent(self, value: float):
        '''Horizontal stamp coordinate, starting from the left.'''
        AsposePDFPython.stamp_set_x_indent(self.handle, value)

    @property
    def y_indent(self) -> float:
        '''Vertical stamp coordinate, starting from the bottom.'''
        return AsposePDFPython.stamp_get_y_indent(self.handle)

    @y_indent.setter
    def y_indent(self, value: float):
        '''Vertical stamp coordinate, starting from the bottom.'''
        AsposePDFPython.stamp_set_y_indent(self.handle, value)

    @property
    def width(self) -> float:
        '''Desired width of the stamp on the page.'''
        return AsposePDFPython.stamp_get_width(self.handle)

    @width.setter
    def width(self, value: float):
        '''Desired width of the stamp on the page.'''
        AsposePDFPython.stamp_set_width(self.handle, value)

    @property
    def height(self) -> float:
        '''Desired height of the stamp on the page.'''
        return AsposePDFPython.stamp_get_height(self.handle)

    @height.setter
    def height(self, value: float):
        '''Desired height of the stamp on the page.'''
        AsposePDFPython.stamp_set_height(self.handle, value)

    @property
    def rotate(self) -> AsposePDFPython.Rotation:
        '''Gets the rotation of stamp content according :class:`Rotation` values.
        Note. This property is for set angles which are multiples of 90 degrees (0, 90, 180, 270 degrees).
        To set arbitrary angle use RotateAngle property.
        If angle set by ArbitraryAngle is not multiple of 90 then Rotate property returns Rotation.None.'''
        return AsposePDFPython.stamp_get_rotate(self.handle)

    @rotate.setter
    def rotate(self, value: AsposePDFPython.Rotation):
        '''Sets the rotation of stamp content according :class:`Rotation` values.
        Note. This property is for set angles which are multiples of 90 degrees (0, 90, 180, 270 degrees).
        To set arbitrary angle use RotateAngle property.
        If angle set by ArbitraryAngle is not multiple of 90 then Rotate property returns Rotation.None.'''
        AsposePDFPython.stamp_set_rotate(self.handle, value)

    @property
    def opacity(self) -> float:
        '''Gets a value to indicate the stamp opacity. The value is from 0.0 to 1.0.
        By default the value is 1.0.'''
        return AsposePDFPython.stamp_get_opacity(self.handle)

    @opacity.setter
    def opacity(self, value: float):
        '''Sets a value to indicate the stamp opacity. The value is from 0.0 to 1.0.
        By default the value is 1.0.'''
        AsposePDFPython.stamp_set_opacity(self.handle, value)

    @property
    def zoom_x(self) -> float:
        '''Horizontal zooming factor of the stamp. Allows to scale stamp horizontally.'''
        return AsposePDFPython.stamp_get_zoom_x(self.handle)

    @zoom_x.setter
    def zoom_x(self, value: float):
        '''Horizontal zooming factor of the stamp. Allows to scale stamp horizontally.'''
        AsposePDFPython.stamp_set_zoom_x(self.handle, value)

    @property
    def zoom_y(self) -> float:
        '''Vertical zooming factor of the stamp. Allows to scale stamp vertically.'''
        return AsposePDFPython.stamp_get_zoom_y(self.handle)

    @zoom_y.setter
    def zoom_y(self, value: float):
        '''Horizontal zooming factor of the stamp. Allows to scale stamp horizontally.'''
        AsposePDFPython.stamp_set_zoom_y(self.handle, value)