import AsposePDFPython
import AsposePDFPythonWrappers.operators.operator

class ClosePathFillStroke(AsposePDFPythonWrappers.operators.operator.Operator):
    '''Class representing b operator (close, fill and stroke path with nonzer winding rule).'''

    def __init__(self):
        '''Initializes operator.'''
        super().__init__(AsposePDFPython.operators_fill_stroke_create())

    def __del__(self):
        super().__del__()