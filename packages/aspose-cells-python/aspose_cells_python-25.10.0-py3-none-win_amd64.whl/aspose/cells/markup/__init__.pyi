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

class CustomXmlPart:
    '''Represents a Custom XML Data Storage Part (custom XML data within a package).'''
    
    @property
    def data(self) -> List[int]:
        '''Gets the XML content of this Custom XML Data Storage Part.'''
        raise NotImplementedError()
    
    @data.setter
    def data(self, value : List[int]) -> None:
        '''Sets the XML content of this Custom XML Data Storage Part.'''
        raise NotImplementedError()
    
    @property
    def schema_data(self) -> List[int]:
        '''Gets the XML content of this Custom XML Schema Data Storage Part.'''
        raise NotImplementedError()
    
    @schema_data.setter
    def schema_data(self, value : List[int]) -> None:
        '''Sets the XML content of this Custom XML Schema Data Storage Part.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> str:
        '''Gets and sets the id of the custom xml part.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : str) -> None:
        '''Gets and sets the id of the custom xml part.'''
        raise NotImplementedError()
    

class CustomXmlPartCollection:
    '''Represents a Custom XML Data Storage Part (custom XML data within a package).'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.markup.CustomXmlPart]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.markup.CustomXmlPart], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.markup.CustomXmlPart, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.markup.CustomXmlPart, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.markup.CustomXmlPart) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.markup.CustomXmlPart, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.markup.CustomXmlPart, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add(self, data : List[int], shema_data : List[int]) -> int:
        '''Adds an item to the collection.
        
        :param data: The XML content of this Custom XML Data Storage Part.
        :param shema_data: The set of XML schemas that are associated with this custom XML part.'''
        raise NotImplementedError()
    
    def select_by_id(self, id : str) -> aspose.cells.markup.CustomXmlPart:
        '''Gets an item by id.
        
        :param id: Contains the GUID for the custom XML part.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.markup.CustomXmlPart) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class SmartTag:
    '''Represents a smart tag.'''
    
    def set_link(self, uri : str, name : str) -> None:
        '''Change the name and  the namespace URI of the smart tag.
        
        :param uri: The namespace URI of the smart tag.
        :param name: The name of the smart tag.'''
        raise NotImplementedError()
    
    @property
    def deleted(self) -> bool:
        '''Indicates whether the smart tag is deleted.'''
        raise NotImplementedError()
    
    @deleted.setter
    def deleted(self, value : bool) -> None:
        '''Indicates whether the smart tag is deleted.'''
        raise NotImplementedError()
    
    @property
    def properties(self) -> aspose.cells.markup.SmartTagPropertyCollection:
        '''Gets and set the properties of the smart tag.'''
        raise NotImplementedError()
    
    @properties.setter
    def properties(self, value : aspose.cells.markup.SmartTagPropertyCollection) -> None:
        '''Gets and set the properties of the smart tag.'''
        raise NotImplementedError()
    
    @property
    def uri(self) -> str:
        '''Gets the namespace URI of the smart tag.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the name of the smart tag.'''
        raise NotImplementedError()
    

class SmartTagCollection:
    '''Represents all smart tags in the cell.'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.markup.SmartTag]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.markup.SmartTag], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.markup.SmartTag, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.markup.SmartTag, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.markup.SmartTag) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.markup.SmartTag, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.markup.SmartTag, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add(self, uri : str, name : str) -> int:
        '''Adds a smart tag.
        
        :param uri: Specifies the namespace URI of the smart tag
        :param name: Specifies the name of the smart tag.
        :returns: The index of smart tag in the list.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.markup.SmartTag) -> int:
        raise NotImplementedError()
    
    @property
    def row(self) -> int:
        '''Gets the row of the cell smart tags.'''
        raise NotImplementedError()
    
    @property
    def column(self) -> int:
        '''Gets the column of the cell smart tags.'''
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class SmartTagOptions:
    '''Represents the options of the smart tag.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def embed_smart_tags(self) -> bool:
        '''Indicates whether saving smart tags with the workbook.'''
        raise NotImplementedError()
    
    @embed_smart_tags.setter
    def embed_smart_tags(self, value : bool) -> None:
        '''Indicates whether saving smart tags with the workbook.'''
        raise NotImplementedError()
    
    @property
    def show_type(self) -> aspose.cells.markup.SmartTagShowType:
        '''Represents the show type of smart tag.'''
        raise NotImplementedError()
    
    @show_type.setter
    def show_type(self, value : aspose.cells.markup.SmartTagShowType) -> None:
        '''Represents the show type of smart tag.'''
        raise NotImplementedError()
    

class SmartTagProperty:
    '''Represents the property of the cell smart tag.'''
    
    @property
    def name(self) -> str:
        '''Gets and sets the name of the property.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Gets and sets the name of the property.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        '''Gets and sets the value of the property.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : str) -> None:
        '''Gets and sets the value of the property.'''
        raise NotImplementedError()
    

class SmartTagPropertyCollection:
    '''Represents all properties of cell smart tag.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.markup.SmartTagProperty]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.markup.SmartTagProperty], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.markup.SmartTagProperty, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.markup.SmartTagProperty, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.markup.SmartTagProperty) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.markup.SmartTagProperty, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.markup.SmartTagProperty, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def get(self, name : str) -> aspose.cells.markup.SmartTagProperty:
        '''Gets a :py:class:`aspose.cells.markup.SmartTagProperty` object by the name of the property.
        
        :param name: The name of the property.
        :returns: Returns a :py:class:`aspose.cells.markup.SmartTagProperty` object.'''
        raise NotImplementedError()
    
    def add(self, name : str, value : str) -> int:
        '''Adds a property of cell\'s smart tag.
        
        :param name: The name of the property
        :param value: The value of the property.
        :returns: return :py:class:`aspose.cells.markup.SmartTagProperty`'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.markup.SmartTagProperty) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class SmartTagSetting:
    '''Represents all :py:class:`aspose.cells.markup.SmartTagCollection` object in the worksheet.'''
    
    @overload
    def add(self, row : int, column : int) -> int:
        '''Adds a :py:class:`aspose.cells.markup.SmartTagCollection` object to a cell.
        
        :param row: The row of the cell.
        :param column: The column of the cell.
        :returns: Returns index of a :py:class:`aspose.cells.markup.SmartTagCollection` object in the worksheet.'''
        raise NotImplementedError()
    
    @overload
    def add(self, cell_name : str) -> int:
        '''Add a cell smart tags.
        
        :param cell_name: The name of the cell.'''
        raise NotImplementedError()
    
    @overload
    def get(self, row : int, column : int) -> aspose.cells.markup.SmartTagCollection:
        '''Add API for Python Via .Net.since this[int, int] is unsupported
        
        :param row: The row index of the cell.
        :param column: The column index of the cell
        :returns: Returns the :py:class:`aspose.cells.markup.SmartTagCollection` object of the cell.
        Returns null if there is no any smart tags on the cell.'''
        raise NotImplementedError()
    
    @overload
    def get(self, cell_name : str) -> aspose.cells.markup.SmartTagCollection:
        '''Gets the :py:class:`aspose.cells.markup.SmartTagCollection` object of the cell.
        
        :param cell_name: The name of the cell.
        :returns: Returns the :py:class:`aspose.cells.markup.SmartTagCollection` object of the cell.
        Returns null if there is no any smart tags on the cell.'''
        raise NotImplementedError()
    

class SmartTagShowType:
    '''Represents the show type of the smart tag.'''
    
    ALL : SmartTagShowType
    '''Indicates that smart tags are enabled and shown'''
    NO_SMART_TAG_INDICATOR : SmartTagShowType
    '''Indicates that the smart tags are enabled but the indicator not be shown.'''
    NONE : SmartTagShowType
    '''Indicates that smart tags are disabled and not displayed.'''

