import AsposePDFPython
import AsposePDFPythonWrappers.artifact


class ArtifactCollection:
    '''Class represents artifact collection.'''

    def __init__(self, handle: AsposePDFPython.artifact_collection_handle):
        self.handle = handle

    def __getitem__(self, index: int) -> AsposePDFPythonWrappers.artifact.Artifact:
        '''Gets artifact by index. Index is started from 1.

        :param index: Index of the artifact.
        :returns: Artifact on the page.'''
        return AsposePDFPythonWrappers.artifact.Artifact(
            AsposePDFPython.artifact_collection_idx_get(self.hanlde, index))

    def add(self, artifact: AsposePDFPythonWrappers.artifact.Artifact):
        '''Adds artifacts to the collection.

        :param artifact Artifact which sould be added to collection.'''
        AsposePDFPython.artifact_collection_add(self.handle, artifact.handle)
