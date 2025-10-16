import AsposePDFPython
import AsposePDFPythonWrappers.sys.drawing.pattern_color_space
import AsposePDFPythonWrappers.color
import AsposePDFPythonWrappers.point

from typing import overload


class GradientRadialShading(AsposePDFPythonWrappers.sys.drawing.pattern_color_space.PatternColorSpace):
    '''Represents gradient radial shading type.'''

    @overload
    def __init__(self):
        '''Initializes a new instance of the :class:`GradientRadialShading` class.'''
        ...

    @overload
    def __init__(self, start_color: AsposePDFPythonWrappers.color.Color, end_color: AsposePDFPythonWrappers.color.Color):
        '''Initializes a new instance of the :class:`GradientRadialShading` class.

        :param start_color: The starting circle color.
        :param end_color: The ending circle color.'''
        ...

    def __init__(self, *args):
        if len(args) == 0:
            super().__init__(AsposePDFPython.gradient_radial_shading_create())
        else:
            super().__init__(AsposePDFPython.gradient_radial_shading_create_from_colors(args[0].handle, args[1].handle))

    def __del__(self):
        super().__del__()

    @property
    def start(self) -> AsposePDFPythonWrappers.point.Point:
        '''Gets or sets starting circle center point.'''
        return AsposePDFPythonWrappers.point.Point(AsposePDFPython.gradient_radial_shading_get_start(self.handle))

    @start.setter
    def start(self, value: AsposePDFPythonWrappers.point.Point):
        AsposePDFPython.gradient_radial_shading_set_start(self.handle, value.handle)

    @property
    def end(self) -> AsposePDFPythonWrappers.point.Point:
        '''Gets or sets ending circle center point.'''
        return AsposePDFPythonWrappers.point.Point(AsposePDFPython.gradient_radial_shading_get_end(self.handle))

    @end.setter
    def end(self, value: AsposePDFPythonWrappers.point.Point):
        AsposePDFPython.gradient_radial_shading_set_end(self.handle, value.handle)

    @property
    def starting_radius(self) -> float:
        '''Gets or sets starting circle radius.'''
        return AsposePDFPython.gradient_radial_shading_get_starting_radius(self.handle)

    @starting_radius.setter
    def starting_radius(self, value: float):
        AsposePDFPython.gradient_radial_shading_set_starting_radius(self.handle, value)

    @property
    def ending_radius(self) -> float:
        '''Gets or sets ending circle radius.'''
        return AsposePDFPython.gradient_radial_shading_get_ending_radius(self.handle)

    @ending_radius.setter
    def ending_radius(self, value: float):
        AsposePDFPython.gradient_radial_shading_set_ending_radius(self.handle, value)

    @property
    def start_color(self) -> AsposePDFPythonWrappers.color.Color:
        '''Gets or sets start color.'''
        return AsposePDFPythonWrappers.color.Color(AsposePDFPython.gradient_radial_shading_get_start_color(self.handle))

    @start_color.setter
    def start_color(self, value: AsposePDFPythonWrappers.color.Color):
        AsposePDFPython.gradient_radial_shading_set_start_color(self.handle, value.handle)

    @property
    def end_color(self) -> AsposePDFPythonWrappers.color.Color:
        '''Gets or sets end color.'''
        return AsposePDFPythonWrappers.color.Color(AsposePDFPython.gradient_radial_shading_get_end_color(self.handle))

    @end_color.setter
    def end_color(self, value: AsposePDFPythonWrappers.color.Color):
        AsposePDFPython.gradient_radial_shading_set_end_color(self.handle, value.handle)
