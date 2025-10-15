from typing import List, Optional, Dict, Iterable, Any, overload
import io
import collections.abc
from collections.abc import Sequence
from datetime import datetime
from aspose.pyreflection import Type
import aspose.pycore
import aspose.pydrawing
from uuid import UUID
import aspose.cells
import aspose.cells.charts
import aspose.cells.datamodels
import aspose.cells.digitalsignatures
import aspose.cells.drawing
import aspose.cells.drawing.activexcontrols
import aspose.cells.drawing.equations
import aspose.cells.drawing.texts
import aspose.cells.externalconnections
import aspose.cells.json
import aspose.cells.loading
import aspose.cells.lowcode
import aspose.cells.markdown
import aspose.cells.markup
import aspose.cells.metadata
import aspose.cells.metas
import aspose.cells.numbers
import aspose.cells.ods
import aspose.cells.pivot
import aspose.cells.properties
import aspose.cells.querytables
import aspose.cells.rendering
import aspose.cells.rendering.pdfsecurity
import aspose.cells.revisions
import aspose.cells.saving
import aspose.cells.settings
import aspose.cells.slicers
import aspose.cells.slides
import aspose.cells.tables
import aspose.cells.timelines
import aspose.cells.utility
import aspose.cells.vba
import aspose.cells.webextensions

class MetadataOptions:
    '''Represents the options of loading metadata of the file.'''
    
    def __init__(self, metadata_type : aspose.cells.metadata.MetadataType) -> None:
        '''Creates an options of loading the metadata.
        
        :param metadata_type: The type of metadata.'''
        raise NotImplementedError()
    
    @property
    def metadata_type(self) -> aspose.cells.metadata.MetadataType:
        '''Gets and sets the type of the metadata which is loading.'''
        raise NotImplementedError()
    
    @property
    def password(self) -> str:
        '''Represents Workbook file encryption password.'''
        raise NotImplementedError()
    
    @password.setter
    def password(self, value : str) -> None:
        '''Represents Workbook file encryption password.'''
        raise NotImplementedError()
    
    @property
    def key_length(self) -> int:
        '''The key length.'''
        raise NotImplementedError()
    
    @key_length.setter
    def key_length(self, value : int) -> None:
        '''The key length.'''
        raise NotImplementedError()
    

class WorkbookMetadata:
    '''Represents the meta data.'''
    
    @overload
    def __init__(self, file_name : str, options : aspose.cells.metadata.MetadataOptions) -> None:
        '''Create the meta data object.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, stream : io._IOBase, options : aspose.cells.metadata.MetadataOptions) -> None:
        '''Create the meta data object.'''
        raise NotImplementedError()
    
    @overload
    def save(self, file_name : str) -> None:
        '''Save the modified metadata to the file.
        
        :param file_name: The file name.'''
        raise NotImplementedError()
    
    @overload
    def save(self, stream : io._IOBase) -> None:
        '''Save the modified metadata to the stream.
        
        :param stream: The stream.'''
        raise NotImplementedError()
    
    @property
    def options(self) -> aspose.cells.metadata.MetadataOptions:
        '''Gets the options of the metadata.'''
        raise NotImplementedError()
    
    @property
    def built_in_document_properties(self) -> aspose.cells.properties.BuiltInDocumentPropertyCollection:
        '''Returns a :py:class:`aspose.cells.properties.DocumentProperty` collection that represents all the  built-in document properties of the spreadsheet.'''
        raise NotImplementedError()
    
    @property
    def custom_document_properties(self) -> aspose.cells.properties.CustomDocumentPropertyCollection:
        '''Returns a :py:class:`aspose.cells.properties.DocumentProperty` collection that represents all the custom document properties of the spreadsheet.'''
        raise NotImplementedError()
    

class MetadataType:
    '''Represents the type of metadata.'''
    
    ENCRYPTION : MetadataType
    '''Encrypts the file.'''
    DECRYPTION : MetadataType
    '''Decrypts the file.'''
    DOCUMENT_PROPERTIES : MetadataType
    '''Load the properties of the file.'''

