import AsposePDFPython
import AsposePDFPythonWrappers.operators.operator


class FillStroke(AsposePDFPythonWrappers.operators.operator.Operator):
    '''Class representing B operator (fill and stroke path using nonzero winding rule)'''

    def __init__(self):
        '''Initializes operator.'''
        super().__init__(AsposePDFPython.operators_fill_stroke_create())
        
    def __del__(self):
        super().__del__()

