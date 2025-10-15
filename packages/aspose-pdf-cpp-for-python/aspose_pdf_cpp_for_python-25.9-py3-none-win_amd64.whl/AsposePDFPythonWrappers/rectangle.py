from __future__ import annotations

import AsposePDFPython
import AsposePDFPythonWrappers.point

from typing import overload

class Rectangle:
    '''Class represents rectangle.'''

    @overload
    def __init__(self, handle: AsposePDFPython.rectangle_handle):
        '''Initializes PageCollection with handle.'''
        ...

    @overload
    def __init__(self, llx: float, lly: float, urx: float, ury: float, normalize_coordinates: bool):
        '''Constructor of Rectangle.

       :param llx: X of lower left corner.
       :param lly: Y of lower left corner.
       :param urx: X of upper right corner.
       :param ury: Y of upper right corner.
       :param normalize_coordinates: Normalize coordinates of rectangle.'''
        ...

    def __init__(self, arg0: AsposePDFPython.rectangle_handle | float
                     , arg1: float | None = None
                     , arg2: float | None = None
                     , arg3: float | None = None
                     , arg4: bool | None = None):
        if isinstance(arg0, AsposePDFPython.rectangle_handle) and arg1 is None and arg2 is None and arg3 is None:
            self.handle = arg0
        elif (isinstance(arg0, float)
              and isinstance(arg1, float)
              and isinstance(arg2, float)
              and isinstance(arg3, float) and isinstance(arg4, bool)):
            self.handle = AsposePDFPython.rectangle_create(arg0, arg1, arg2, arg3, arg4)
        else:
            raise TypeError("Invalid number of arguments.")

    def __del__(self):
        '''Close handle.'''
        AsposePDFPython.close_handle(self.handle)

    @property
    def width(self) -> float:
        '''Width of rectangle.'''
        return AsposePDFPython.rectangle_get_width(self.handle)

    @property
    def height(self) -> float:
        '''Height of rectangle.'''
        return AsposePDFPython.rectangle_get_height(self.handle)

    @property
    def llx(self) -> float:
        '''Get X-coordinate of lower - left corner.'''
        return  AsposePDFPython.rectangle_get_LLX(self.handle)

    @llx.setter
    def llx(self, value: float):
        '''Set X-coordinate of lower - left corner.'''
        AsposePDFPython.rectangle_set_LLX(self.handle, value)

    @property
    def lly(self) -> float:
        '''Get Y - coordinate of lower-left corner.'''
        return AsposePDFPython.rectangle_get_LLY(self.handle)

    @lly.setter
    def lly(self, value: float):
        '''Set Y - coordinate of lower-left corner.'''
        AsposePDFPython.rectangle_set_LLY(self.handle, value)

    @property
    def urx(self) -> float:
        '''Get X - coordinate of upper-right corner.'''
        return AsposePDFPython.rectangle_get_URX(self.handle)

    @urx.setter
    def urx(self, value: float):
        '''Get X - coordinate of upper-right corner.'''
        AsposePDFPython.rectangle_set_URX(self, value)

    @property
    def ury(self) -> float:
        '''Get Y - coordinate of upper-right corner.'''
        return AsposePDFPython.rectangle_get_URY(self.handle)

    @ury.setter
    def ury(self, value: float):
        '''Set Y - coordinate of upper-right corner.'''
        AsposePDFPython.rectangle_set_URY(self.handle, value)

    @staticmethod
    def trivial() -> AsposePDFPythonWrappers.rectangle.Rectangle:
        '''Initializes trivial rectangle i.e. rectangle with zero position and size.'''
        return Rectangle(AsposePDFPython.rectangle_get_trivial())

    @property
    def is_trivial(self) -> bool:
        '''Checks if rectangle is trivial i.e. has zero size and position.'''
        return AsposePDFPython.rectangle_is_trivial(self.handle)

    @property
    def is_empty(self) -> bool:
        '''Checks if rectangle is empty.'''
        return AsposePDFPython.rectangle_is_empty(self.handle)

    @property
    def is_point(self) -> bool:
        '''Checks if rectangle is point i.e. LLX is equal URX and LLY is equal URY.'''
        return AsposePDFPython.rectangle_is_point(self.handle)

    def __eq__(self, other_rect: AsposePDFPythonWrappers.rectangle.Rectangle):
        '''Compare two Rectangle's.

        :param other_rect: Rectangle to compare.
        :return: True if rectangles are eqals, false otherwise.'''
        return AsposePDFPython.rectangle_is_equal(self.handle, other_rect.handle)

    def is_near_equal(self, other_rect: AsposePDFPythonWrappers.rectangle.Rectangle, delta: float):
        '''Compare two Rectangle's with delta precision.

        :param other_rect: Rectangle to compare.
        :param delta: Precision.
        :return: True if rectangles are eqals, false otherwise.'''
        return AsposePDFPython.rectangle_is_near_equal(self.handle, other_rect.handle, delta)

    def intersect(self, other_rect: AsposePDFPythonWrappers.rectangle.Rectangle) \
            -> AsposePDFPythonWrappers.rectangle.Rectangle:
        '''Intersects to rectangles.

        :param other_rect: Rectangle to which this recatangle be intersected.
        :returns: Intersection of rectangles; null if rectangles are not intersected.'''
        return AsposePDFPythonWrappers.rectangle.Rectangle(AsposePDFPython.rectangle_intersect(self.handle, other_rect.handle))

    def join(self, other_rect: AsposePDFPythonWrappers.rectangle.Rectangle) \
            -> AsposePDFPythonWrappers.rectangle.Rectangle:
        '''Joins rectangles.

        :param other_rect: Rectangle to which this recatangle be joined.
        :returns: Described rectangle.'''
        return Rectangle(AsposePDFPython.rectangle_join(self.handle, other_rect.handle))

    def is_intersect(self, other_rect: Rectangle) -> bool:
        '''Determines whether this rectangle intersects with other rectangle.

        :param other_rect: Intersection will be tested with specified rectangle.
        :returns: True if this rectangle intersects with specified rectangle. Otherwise false.'''
        return AsposePDFPython.rectangle_is_intersect(self.handle, other_rect.handle)

    def contains(self, point: AsposePDFPythonWrappers.point.Point) -> bool:
        '''Determinces whether given point is inside of the rectangle.

        :param point: Point to check.
        :returns: True if point is inside of the recatngle.'''
        return AsposePDFPython.rectangle_contains(self.handle, point.handle)

    def center(self) -> AsposePDFPythonWrappers.point.Point:
        '''Returncs coordinates of center of the rectangle.

        :returns: Point which is center of the rectangle.'''
        return AsposePDFPythonWrappers.point.Point(AsposePDFPython.rectangle_center(self.handle))

    @overload
    def rotate(self, angle: AsposePDFPython.Rotation) -> None:
        '''Rotate rectangle by the specified angle.

        :param angle: Angle of rotation. Member of Rotation enumeration.'''
        ...

    @overload
    def rotate(self, angle: int) -> None:
        '''Rotate rectangle by the specified angle.

        :param angle: Angle of rotation in degrees between 0 and 360.'''
        ...

    def rotate(self, arg0: AsposePDFPython.Rotation | int) -> None:
        if isinstance(arg0, AsposePDFPython.Rotation):
            AsposePDFPython.rectangle_rotate(self.handle, arg0)
        elif isinstance(arg0, int):
            AsposePDFPython.rectangle_rotate_arbitrary(self.handle, arg0)
        else:
            raise TypeError("Invalid number of arguments.")