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

class Timeline:
    '''Summary description of Timeline View
    Due to MS Excel, Excel 2003 does not support Timeline'''
    
    @property
    def caption(self) -> str:
        '''Returns the caption of the specified Timeline.'''
        raise NotImplementedError()
    
    @caption.setter
    def caption(self, value : str) -> None:
        '''Returns or sets the caption of the specified Timeline.'''
        raise NotImplementedError()
    
    @property
    def shape(self) -> aspose.cells.drawing.TimelineShape:
        '''Returns the :py:class:`aspose.cells.drawing.TimelineShape` object associated with this Timeline. Read-only.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Returns the name of the specified Timeline'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Returns or sets the name of the specified Timeline'''
        raise NotImplementedError()
    
    @property
    def left_pixel(self) -> int:
        '''Returns the horizontal offset of timeline shape from its left column, in pixels.'''
        raise NotImplementedError()
    
    @left_pixel.setter
    def left_pixel(self, value : int) -> None:
        '''Returns or sets the horizontal offset of timeline shape from its left column, in pixels.'''
        raise NotImplementedError()
    
    @property
    def top_pixel(self) -> int:
        '''Returns the vertical offset of timeline shape from its top row, in pixels.'''
        raise NotImplementedError()
    
    @top_pixel.setter
    def top_pixel(self, value : int) -> None:
        '''Returns or sets the vertical offset of timeline shape from its top row, in pixels.'''
        raise NotImplementedError()
    
    @property
    def width_pixel(self) -> int:
        '''Returns the width of the specified timeline, in pixels.'''
        raise NotImplementedError()
    
    @width_pixel.setter
    def width_pixel(self, value : int) -> None:
        '''Returns or sets the width of the specified timeline, in pixels.'''
        raise NotImplementedError()
    
    @property
    def height_pixel(self) -> int:
        '''Returns the height of the specified timeline, in pixels.'''
        raise NotImplementedError()
    
    @height_pixel.setter
    def height_pixel(self, value : int) -> None:
        '''Returns or sets the height of the specified timeline, in pixels.'''
        raise NotImplementedError()
    

class TimelineCollection:
    '''Specifies the collection of all the Timeline objects on the specified worksheet.
    Due to MS Excel, Excel 2003 does not support Timeline.'''
    
    @overload
    def add(self, pivot : aspose.cells.pivot.PivotTable, row : int, column : int, base_field_name : str) -> int:
        '''Add a new Timeline using PivotTable as data source
        
        :param pivot: PivotTable object
        :param row: Row index of the cell in the upper-left corner of the Timeline range.
        :param column: Column index of the cell in the upper-left corner of the Timeline range.
        :param base_field_name: The name of PivotField in PivotTable.BaseFields
        :returns: The new add Timeline index'''
        raise NotImplementedError()
    
    @overload
    def add(self, pivot : aspose.cells.pivot.PivotTable, dest_cell_name : str, base_field_name : str) -> int:
        '''Add a new Timeline using PivotTable as data source
        
        :param pivot: PivotTable object
        :param dest_cell_name: The cell name in the upper-left corner of the Timeline range.
        :param base_field_name: The name of PivotField in PivotTable.BaseFields
        :returns: The new add Timeline index'''
        raise NotImplementedError()
    
    @overload
    def add(self, pivot : aspose.cells.pivot.PivotTable, row : int, column : int, base_field_index : int) -> int:
        '''Add a new Timeline using PivotTable as data source
        
        :param pivot: PivotTable object
        :param row: Row index of the cell in the upper-left corner of the Timeline range.
        :param column: Column index of the cell in the upper-left corner of the Timeline range.
        :param base_field_index: The index of PivotField in PivotTable.BaseFields
        :returns: The new add Timeline index'''
        raise NotImplementedError()
    
    @overload
    def add(self, pivot : aspose.cells.pivot.PivotTable, dest_cell_name : str, base_field_index : int) -> int:
        '''Add a new Timeline using PivotTable as data source
        
        :param pivot: PivotTable object
        :param dest_cell_name: The cell name in the upper-left corner of the Timeline range.
        :param base_field_index: The index of PivotField in PivotTable.BaseFields
        :returns: The new add Timeline index'''
        raise NotImplementedError()
    
    @overload
    def add(self, pivot : aspose.cells.pivot.PivotTable, row : int, column : int, base_field : aspose.cells.pivot.PivotField) -> int:
        '''Add a new Timeline using PivotTable as data source
        
        :param pivot: PivotTable object
        :param row: Row index of the cell in the upper-left corner of the Timeline range.
        :param column: Column index of the cell in the upper-left corner of the Timeline range.
        :param base_field: The PivotField in PivotTable.BaseFields
        :returns: The new add Timeline index'''
        raise NotImplementedError()
    
    @overload
    def add(self, pivot : aspose.cells.pivot.PivotTable, dest_cell_name : str, base_field : aspose.cells.pivot.PivotField) -> int:
        '''Add a new Timeline using PivotTable as data source
        
        :param pivot: PivotTable object
        :param dest_cell_name: The cell name in the upper-left corner of the Timeline range.
        :param base_field: The PivotField in PivotTable.BaseFields
        :returns: The new add Timeline index'''
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.timelines.Timeline]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.timelines.Timeline], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.timelines.Timeline, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.timelines.Timeline, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.timelines.Timeline) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.timelines.Timeline, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.timelines.Timeline, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def get(self, name : str) -> aspose.cells.timelines.Timeline:
        '''Gets the Timeline  by Timeline\'s name.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.timelines.Timeline) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

