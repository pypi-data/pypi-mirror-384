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

class SensitivityLabel:
    '''Represents the sensitivity label.'''
    
    @property
    def id(self) -> str:
        '''Gets and sets the id of sensitivity label.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : str) -> None:
        '''Gets and sets the id of sensitivity label.'''
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        '''Indicates whether the sensitivity label is enabled'''
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        '''Indicates whether the sensitivity label is enabled'''
        raise NotImplementedError()
    
    @property
    def assignment_type(self) -> aspose.cells.metas.SensitivityLabelAssignmentType:
        '''Gets and sets the assignment method for the sensitivity label.'''
        raise NotImplementedError()
    
    @assignment_type.setter
    def assignment_type(self, value : aspose.cells.metas.SensitivityLabelAssignmentType) -> None:
        '''Gets and sets the assignment method for the sensitivity label.'''
        raise NotImplementedError()
    
    @property
    def site_id(self) -> str:
        '''Represents the Azure Active Directory (Azure AD) site identifier corresponding to the sensitivity label policy which describes the sensitivity label.'''
        raise NotImplementedError()
    
    @site_id.setter
    def site_id(self, value : str) -> None:
        '''Represents the Azure Active Directory (Azure AD) site identifier corresponding to the sensitivity label policy which describes the sensitivity label.'''
        raise NotImplementedError()
    
    @property
    def content_mark_type(self) -> aspose.cells.metas.SensitivityLabelMarkType:
        '''Gets and sets the types of content marking that ought to be applied to a file.'''
        raise NotImplementedError()
    
    @content_mark_type.setter
    def content_mark_type(self, value : aspose.cells.metas.SensitivityLabelMarkType) -> None:
        '''Gets and sets the types of content marking that ought to be applied to a file.'''
        raise NotImplementedError()
    
    @property
    def is_removed(self) -> bool:
        '''Indicates whether the sensitivity label was removed.'''
        raise NotImplementedError()
    
    @is_removed.setter
    def is_removed(self, value : bool) -> None:
        '''Indicates whether the sensitivity label was removed.'''
        raise NotImplementedError()
    

class SensitivityLabelCollection:
    '''Represents the list of sensitivity labels.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.metas.SensitivityLabel]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.metas.SensitivityLabel], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.metas.SensitivityLabel, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.metas.SensitivityLabel, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.metas.SensitivityLabel) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.metas.SensitivityLabel, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.metas.SensitivityLabel, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add(self, id : str, is_enabled : bool, method_type : aspose.cells.metas.SensitivityLabelAssignmentType, site_id : str, mark_type : aspose.cells.metas.SensitivityLabelMarkType) -> int:
        '''Adds a sensitivity label.
        
        :param id: The id of the label.
        :param is_enabled: Indicates whether this sensitivity label is enabled.
        :param method_type: The assignment method type.
        :param site_id: The id of the site.
        :param mark_type: The mark type.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.metas.SensitivityLabel) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class SensitivityLabelAssignmentType:
    '''Represents the assignment method for the sensitivity label.'''
    
    STANDARD : SensitivityLabelAssignmentType
    '''Use for any sensitivity label that was not directly applied by the user.'''
    PRIVILEGED : SensitivityLabelAssignmentType
    '''Use for any sensitivity label that was directly applied by the user.'''

class SensitivityLabelMarkType:
    '''Represents the types of content marking that ought to be applied to a file.'''
    
    NONE : SensitivityLabelMarkType
    '''None'''
    HEADER : SensitivityLabelMarkType
    '''Header'''
    FOOTER : SensitivityLabelMarkType
    '''Footer'''
    WATERMARK : SensitivityLabelMarkType
    '''Watermark'''
    ENCRYPTION : SensitivityLabelMarkType
    '''Encryption'''

