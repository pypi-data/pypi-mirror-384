import AsposePDFPython
import AsposePDFPythonWrappers.operators.operator

from typing import overload

class Artifact:
    '''Class represents PDF Artifact object.'''

    @overload
    def __init__(self, handle: AsposePDFPython.artifact_handle):
        '''Construct artifact form handle.'''
        ...

    @overload
    def __init__(self, type: str, sub_type: str):
        '''Constructor of artifact with specified type and subtype

        :param type: Name of artifact type.
        :param sub_type: NAme of artifact subtype.'''
        ...

    def __init__(self, arg0: str | AsposePDFPython.artifact_handle, arg1: str | None = None):
        if isinstance(arg0, str) and isinstance(arg1, str):
            self.handle = AsposePDFPython.artifact_create(arg0, arg1)
        elif isinstance(arg0, AsposePDFPython.artifact_handle) and arg1 is None:
            self.handle = arg0
        else:
            raise TypeError("Invalid number of arguments.")

    @property
    def contents(self) -> list[AsposePDFPythonWrappers.operators.operator.Operator]:
        '''Gets collection of artifact internal operators.'''
        operators_handle_list = AsposePDFPython.artifact_get_contents(self.handle)
        result = []
        for operators_handle in operators_handle_list:
            result.append(AsposePDFPythonWrappers.operator.Operator(operators_handle))

        return result