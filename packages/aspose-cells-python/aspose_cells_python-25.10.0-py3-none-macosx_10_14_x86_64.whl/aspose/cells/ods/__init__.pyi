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

class OdsCellField:
    '''Represents the cell field of ods.'''
    
    @property
    def custom_format(self) -> str:
        '''Represents the custom format of the field\'s value.'''
        raise NotImplementedError()
    
    @custom_format.setter
    def custom_format(self, value : str) -> None:
        '''Represents the custom format of the field\'s value.'''
        raise NotImplementedError()
    
    @property
    def field_type(self) -> aspose.cells.ods.OdsCellFieldType:
        '''Gets and sets the type of the field.'''
        raise NotImplementedError()
    
    @field_type.setter
    def field_type(self, value : aspose.cells.ods.OdsCellFieldType) -> None:
        '''Gets and sets the type of the field.'''
        raise NotImplementedError()
    
    @property
    def row(self) -> int:
        '''Get and sets the row index of the cell.'''
        raise NotImplementedError()
    
    @row.setter
    def row(self, value : int) -> None:
        '''Get and sets the row index of the cell.'''
        raise NotImplementedError()
    
    @property
    def column(self) -> int:
        '''Get and sets the column index of the cell.'''
        raise NotImplementedError()
    
    @column.setter
    def column(self, value : int) -> None:
        '''Get and sets the column index of the cell.'''
        raise NotImplementedError()
    

class OdsCellFieldCollection:
    '''Represents the fields of ODS.'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.ods.OdsCellField]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.ods.OdsCellField], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.ods.OdsCellField, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.ods.OdsCellField, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.ods.OdsCellField) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.ods.OdsCellField, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.ods.OdsCellField, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add(self, row : int, column : int, field_type : aspose.cells.ods.OdsCellFieldType, format : str) -> int:
        '''Adds a field.
        
        :param row: The row index.
        :param column: The column index.
        :param field_type: The type of the field.
        :param format: The number format of the field.'''
        raise NotImplementedError()
    
    def update_fields_value(self) -> None:
        '''Update fields value to the cells.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.ods.OdsCellField) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class OdsPageBackground:
    '''Represents the page background of ods.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.ods.OdsPageBackgroundType:
        '''Gets and sets the page background type.'''
        raise NotImplementedError()
    
    @type.setter
    def type(self, value : aspose.cells.ods.OdsPageBackgroundType) -> None:
        '''Gets and sets the page background type.'''
        raise NotImplementedError()
    
    @property
    def color(self) -> aspose.pydrawing.Color:
        '''Gets and sets the color of background.'''
        raise NotImplementedError()
    
    @color.setter
    def color(self, value : aspose.pydrawing.Color) -> None:
        '''Gets and sets the color of background.'''
        raise NotImplementedError()
    
    @property
    def graphic_type(self) -> aspose.cells.ods.OdsPageBackgroundGraphicType:
        '''Gets and sets the page background graphic type.'''
        raise NotImplementedError()
    
    @graphic_type.setter
    def graphic_type(self, value : aspose.cells.ods.OdsPageBackgroundGraphicType) -> None:
        '''Gets and sets the page background graphic type.'''
        raise NotImplementedError()
    
    @property
    def graphic_position_type(self) -> aspose.cells.ods.OdsPageBackgroundGraphicPositionType:
        '''Gets and set the background graphic position.'''
        raise NotImplementedError()
    
    @graphic_position_type.setter
    def graphic_position_type(self, value : aspose.cells.ods.OdsPageBackgroundGraphicPositionType) -> None:
        '''Gets and set the background graphic position.'''
        raise NotImplementedError()
    
    @property
    def is_link(self) -> bool:
        '''Indicates whether it\'s a linked graphic.'''
        raise NotImplementedError()
    
    @property
    def linked_graphic(self) -> str:
        '''Gets and sets the linked graphic path.'''
        raise NotImplementedError()
    
    @linked_graphic.setter
    def linked_graphic(self, value : str) -> None:
        '''Gets and sets the linked graphic path.'''
        raise NotImplementedError()
    
    @property
    def graphic_data(self) -> List[int]:
        '''Gets and sets the graphic data.'''
        raise NotImplementedError()
    
    @graphic_data.setter
    def graphic_data(self, value : List[int]) -> None:
        '''Gets and sets the graphic data.'''
        raise NotImplementedError()
    

class OdsCellFieldType:
    '''Represents the cell field type of ods.'''
    
    DATE : OdsCellFieldType
    '''Current date.'''
    SHEET_NAME : OdsCellFieldType
    '''The name of the sheet.'''
    TITLE : OdsCellFieldType
    '''The name of the file.'''

class OdsGeneratorType:
    '''Represents the type of ODS generator.'''
    
    LIBRE_OFFICE : OdsGeneratorType
    '''Libre Office'''
    OPEN_OFFICE : OdsGeneratorType
    '''Open Office'''

class OdsPageBackgroundGraphicPositionType:
    '''Represents the position.'''
    
    TOP_LEFT : OdsPageBackgroundGraphicPositionType
    '''Top left.'''
    TOP_CENTER : OdsPageBackgroundGraphicPositionType
    '''Top center.'''
    TOP_RIGHT : OdsPageBackgroundGraphicPositionType
    '''Top right.'''
    CENTER_LEFT : OdsPageBackgroundGraphicPositionType
    '''Center left.'''
    CENTER_CENTER : OdsPageBackgroundGraphicPositionType
    '''Center.'''
    CENTER_RIGHT : OdsPageBackgroundGraphicPositionType
    '''Center right.'''
    BOTTOM_LEFT : OdsPageBackgroundGraphicPositionType
    '''Bottom left.'''
    BOTTOM_CENTER : OdsPageBackgroundGraphicPositionType
    '''Bottom center.'''
    BOTTOM_RIGHT : OdsPageBackgroundGraphicPositionType
    '''Bottom right.'''

class OdsPageBackgroundGraphicType:
    '''Represents the type of formatting page background with image.'''
    
    POSITION : OdsPageBackgroundGraphicType
    '''Set the image at specific position.'''
    AREA : OdsPageBackgroundGraphicType
    '''Stretch the image.'''
    TILE : OdsPageBackgroundGraphicType
    '''Repeat and repeat the image.'''

class OdsPageBackgroundType:
    '''Represents the page background type of ods.'''
    
    NONE : OdsPageBackgroundType
    '''No background.'''
    COLOR : OdsPageBackgroundType
    '''Formats the background with color.'''
    GRAPHIC : OdsPageBackgroundType
    '''Formats the background with image.'''

class OpenDocumentFormatVersionType:
    '''Open Document Format version type.'''
    
    NONE : OpenDocumentFormatVersionType
    '''None strict.'''
    ODF11 : OpenDocumentFormatVersionType
    '''ODF Version 1.1'''
    ODF12 : OpenDocumentFormatVersionType
    '''ODF Version 1.2'''
    ODF13 : OpenDocumentFormatVersionType
    '''ODF Version 1.3'''

