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

class Slicer:
    '''summary description of Slicer View'''
    
    def add_pivot_connection(self, pivot : aspose.cells.pivot.PivotTable) -> None:
        '''Adds PivotTable connection.
        
        :param pivot: The PivotTable object'''
        raise NotImplementedError()
    
    def remove_pivot_connection(self, pivot : aspose.cells.pivot.PivotTable) -> None:
        '''Removes PivotTable connection.
        
        :param pivot: The PivotTable object'''
        raise NotImplementedError()
    
    def refresh(self) -> None:
        '''Refreshing the slicer.Meanwhile, Refreshing and Calculating  relative PivotTables.'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Specifies the title of the current Slicer object.'''
        raise NotImplementedError()
    
    @title.setter
    def title(self, value : str) -> None:
        '''Specifies the title of the current Slicer object.'''
        raise NotImplementedError()
    
    @property
    def alternative_text(self) -> str:
        '''Returns the descriptive (alternative) text string of the Slicer object.'''
        raise NotImplementedError()
    
    @alternative_text.setter
    def alternative_text(self, value : str) -> None:
        '''Returns or sets the descriptive (alternative) text string of the Slicer object.'''
        raise NotImplementedError()
    
    @property
    def is_printable(self) -> bool:
        '''Indicates whether the slicer object is printable.'''
        raise NotImplementedError()
    
    @is_printable.setter
    def is_printable(self, value : bool) -> None:
        '''Indicates whether the slicer object is printable.'''
        raise NotImplementedError()
    
    @property
    def is_locked(self) -> bool:
        '''Indicates whether the slicer shape is locked.'''
        raise NotImplementedError()
    
    @is_locked.setter
    def is_locked(self, value : bool) -> None:
        '''Indicates whether the slicer shape is locked.'''
        raise NotImplementedError()
    
    @property
    def placement(self) -> aspose.cells.drawing.PlacementType:
        '''Represents the way the drawing object is attached to the cells below it.
        The property controls the placement of an object on a worksheet.'''
        raise NotImplementedError()
    
    @placement.setter
    def placement(self, value : aspose.cells.drawing.PlacementType) -> None:
        '''Represents the way the drawing object is attached to the cells below it.
        The property controls the placement of an object on a worksheet.'''
        raise NotImplementedError()
    
    @property
    def locked_aspect_ratio(self) -> bool:
        '''Indicates whether locking aspect ratio.'''
        raise NotImplementedError()
    
    @locked_aspect_ratio.setter
    def locked_aspect_ratio(self, value : bool) -> None:
        '''Indicates whether locking aspect ratio.'''
        raise NotImplementedError()
    
    @property
    def locked_position(self) -> bool:
        '''Indicates whether the specified slicer can be moved or resized by using the user interface.'''
        raise NotImplementedError()
    
    @locked_position.setter
    def locked_position(self, value : bool) -> None:
        '''Indicates whether the specified slicer can be moved or resized by using the user interface.'''
        raise NotImplementedError()
    
    @property
    def shape(self) -> aspose.cells.drawing.SlicerShape:
        '''Returns the Shape object associated with the specified slicer. Read-only.'''
        raise NotImplementedError()
    
    @property
    def slicer_cache(self) -> aspose.cells.slicers.SlicerCache:
        '''Returns the SlicerCache object associated with the slicer. Read-only.'''
        raise NotImplementedError()
    
    @property
    def parent(self) -> aspose.cells.Worksheet:
        '''Returns the :py:class:`aspose.cells.Worksheet` object which contains this slicer. Read-only.'''
        raise NotImplementedError()
    
    @property
    def style_type(self) -> aspose.cells.slicers.SlicerStyleType:
        '''Specify the type of Built-in slicer style
        the default type is SlicerStyleLight1'''
        raise NotImplementedError()
    
    @style_type.setter
    def style_type(self, value : aspose.cells.slicers.SlicerStyleType) -> None:
        '''Specify the type of Built-in slicer style
        the default type is SlicerStyleLight1'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Returns the name of the specified slicer'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Returns or sets the name of the specified slicer'''
        raise NotImplementedError()
    
    @property
    def caption(self) -> str:
        '''Returns the caption of the specified slicer.'''
        raise NotImplementedError()
    
    @caption.setter
    def caption(self, value : str) -> None:
        '''Returns or sets the caption of the specified slicer.'''
        raise NotImplementedError()
    
    @property
    def caption_visible(self) -> bool:
        '''Returns whether the header that displays the slicer Caption is visible
        the default value is true'''
        raise NotImplementedError()
    
    @caption_visible.setter
    def caption_visible(self, value : bool) -> None:
        '''Returns or sets whether the header that displays the slicer Caption is visible
        the default value is true'''
        raise NotImplementedError()
    
    @property
    def number_of_columns(self) -> int:
        '''Returns the number of columns in the specified slicer.'''
        raise NotImplementedError()
    
    @number_of_columns.setter
    def number_of_columns(self, value : int) -> None:
        '''Returns or sets the number of columns in the specified slicer.'''
        raise NotImplementedError()
    
    @property
    def left_pixel(self) -> int:
        '''Returns the horizontal offset of slicer shape from its left column, in pixels.'''
        raise NotImplementedError()
    
    @left_pixel.setter
    def left_pixel(self, value : int) -> None:
        '''Returns or sets the horizontal offset of slicer shape from its left column, in pixels.'''
        raise NotImplementedError()
    
    @property
    def top_pixel(self) -> int:
        '''Returns the vertical offset of slicer shape from its top row, in pixels.'''
        raise NotImplementedError()
    
    @top_pixel.setter
    def top_pixel(self, value : int) -> None:
        '''Returns or sets the vertical offset of slicer shape from its top row, in pixels.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        '''Returns the width of the specified slicer, in points.'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        '''Returns or sets the width of the specified slicer, in points.'''
        raise NotImplementedError()
    
    @property
    def width_pixel(self) -> int:
        '''Returns the width of the specified slicer, in pixels.'''
        raise NotImplementedError()
    
    @width_pixel.setter
    def width_pixel(self, value : int) -> None:
        '''Returns or sets the width of the specified slicer, in pixels.'''
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        '''Returns the height of the specified slicer, in points.'''
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        '''Returns or sets the height of the specified slicer, in points.'''
        raise NotImplementedError()
    
    @property
    def height_pixel(self) -> int:
        '''Returns the height of the specified slicer, in pixels.'''
        raise NotImplementedError()
    
    @height_pixel.setter
    def height_pixel(self, value : int) -> None:
        '''Returns or sets the height of the specified slicer, in pixels.'''
        raise NotImplementedError()
    
    @property
    def column_width_pixel(self) -> int:
        '''Gets the width of each column in the slicer, in unit of pixels.'''
        raise NotImplementedError()
    
    @column_width_pixel.setter
    def column_width_pixel(self, value : int) -> None:
        '''Sets the width of each column in the slicer, in unit of pixels.'''
        raise NotImplementedError()
    
    @property
    def column_width(self) -> float:
        '''Returns the width, in points, of each column in the slicer.'''
        raise NotImplementedError()
    
    @column_width.setter
    def column_width(self, value : float) -> None:
        '''Returns or sets the width, in points, of each column in the slicer.'''
        raise NotImplementedError()
    
    @property
    def row_height_pixel(self) -> int:
        '''Returns the height, in pixels, of each row in the specified slicer.'''
        raise NotImplementedError()
    
    @row_height_pixel.setter
    def row_height_pixel(self, value : int) -> None:
        '''Returns or sets the height, in pixels, of each row in the specified slicer.'''
        raise NotImplementedError()
    
    @property
    def row_height(self) -> float:
        '''Returns the height, in points, of each row in the specified slicer.'''
        raise NotImplementedError()
    
    @row_height.setter
    def row_height(self, value : float) -> None:
        '''Returns or sets the height, in points, of each row in the specified slicer.'''
        raise NotImplementedError()
    

class SlicerCache:
    '''Represent summary description of slicer cache'''
    
    @property
    def cross_filter_type(self) -> aspose.cells.slicers.SlicerCacheCrossFilterType:
        '''Returns whether a slicer is participating in cross filtering with other slicers
        that share the same slicer cache, and how cross filtering is displayed. Read/write'''
        raise NotImplementedError()
    
    @cross_filter_type.setter
    def cross_filter_type(self, value : aspose.cells.slicers.SlicerCacheCrossFilterType) -> None:
        '''Returns or sets whether a slicer is participating in cross filtering with other slicers
        that share the same slicer cache, and how cross filtering is displayed. Read/write'''
        raise NotImplementedError()
    
    @property
    def list(self) -> bool:
        '''Returns whether the slicer associated with the specified slicer cache is based on an Non-OLAP data source. Read-only'''
        raise NotImplementedError()
    
    @property
    def slicer_cache_items(self) -> aspose.cells.slicers.SlicerCacheItemCollection:
        '''Returns a SlicerCacheItem collection that contains the collection of all items in the slicer cache. Read-only'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Returns the name of the slicer cache.'''
        raise NotImplementedError()
    
    @property
    def source_name(self) -> str:
        '''Returns the name of this slicer cache.'''
        raise NotImplementedError()
    

class SlicerCacheItem:
    '''Represent slicer data source item'''
    
    @property
    def selected(self) -> bool:
        '''Specifies whether the SlicerItem is selected or not.'''
        raise NotImplementedError()
    
    @selected.setter
    def selected(self, value : bool) -> None:
        '''Specifies whether the SlicerItem is selected or not.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        '''Returns the label text for the slicer item. Read-only.'''
        raise NotImplementedError()
    

class SlicerCacheItemCollection:
    '''Represent the collection of SlicerCacheItem'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.slicers.SlicerCacheItem]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.slicers.SlicerCacheItem], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.slicers.SlicerCacheItem, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.slicers.SlicerCacheItem, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.slicers.SlicerCacheItem) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.slicers.SlicerCacheItem, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.slicers.SlicerCacheItem, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.slicers.SlicerCacheItem) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class SlicerCollection:
    '''Specifies the collection of all the Slicer objects on the specified worksheet.'''
    
    @overload
    def add(self, pivot : aspose.cells.pivot.PivotTable, dest_cell_name : str, base_field_name : str) -> int:
        '''Add a new Slicer using PivotTable as data source
        
        :param pivot: PivotTable object
        :param dest_cell_name: The cell in the upper-left corner of the Slicer range.
        :param base_field_name: The name of PivotField in PivotTable.BaseFields
        :returns: The new add Slicer index'''
        raise NotImplementedError()
    
    @overload
    def add(self, pivot : aspose.cells.pivot.PivotTable, row : int, column : int, base_field_name : str) -> int:
        '''Add a new Slicer using PivotTable as data source
        
        :param pivot: PivotTable object
        :param row: Row index of the cell in the upper-left corner of the Slicer range.
        :param column: Column index of the cell in the upper-left corner of the Slicer range.
        :param base_field_name: The name of PivotField in PivotTable.BaseFields
        :returns: The new add Slicer index'''
        raise NotImplementedError()
    
    @overload
    def add(self, pivot : aspose.cells.pivot.PivotTable, row : int, column : int, base_field_index : int) -> int:
        '''Add a new Slicer using PivotTable as data source
        
        :param pivot: PivotTable object
        :param row: Row index of the cell in the upper-left corner of the Slicer range.
        :param column: Column index of the cell in the upper-left corner of the Slicer range.
        :param base_field_index: The index of PivotField in PivotTable.BaseFields
        :returns: The new add Slicer index'''
        raise NotImplementedError()
    
    @overload
    def add(self, pivot : aspose.cells.pivot.PivotTable, dest_cell_name : str, base_field_index : int) -> int:
        '''Add a new Slicer using PivotTable as data source
        
        :param pivot: PivotTable object
        :param dest_cell_name: The cell in the upper-left corner of the Slicer range.
        :param base_field_index: The index of PivotField in PivotTable.BaseFields
        :returns: The new add Slicer index'''
        raise NotImplementedError()
    
    @overload
    def add(self, pivot : aspose.cells.pivot.PivotTable, row : int, column : int, base_field : aspose.cells.pivot.PivotField) -> int:
        '''Add a new Slicer using PivotTable as data source
        
        :param pivot: PivotTable object
        :param row: Row index of the cell in the upper-left corner of the Slicer range.
        :param column: Column index of the cell in the upper-left corner of the Slicer range.
        :param base_field: The PivotField in PivotTable.BaseFields
        :returns: The new add Slicer index'''
        raise NotImplementedError()
    
    @overload
    def add(self, pivot : aspose.cells.pivot.PivotTable, dest_cell_name : str, base_field : aspose.cells.pivot.PivotField) -> int:
        '''Add a new Slicer using PivotTable as data source
        
        :param pivot: PivotTable object
        :param dest_cell_name: The cell in the upper-left corner of the Slicer range.
        :param base_field: The PivotField in PivotTable.BaseFields
        :returns: The new add Slicer index'''
        raise NotImplementedError()
    
    @overload
    def add(self, table : aspose.cells.tables.ListObject, index : int, dest_cell_name : str) -> int:
        '''Add a new Slicer using ListObjet as data source
        
        :param table: ListObject object
        :param index: The index of ListColumn in ListObject.ListColumns
        :param dest_cell_name: The cell in the upper-left corner of the Slicer range.
        :returns: The new add Slicer index'''
        raise NotImplementedError()
    
    @overload
    def add(self, table : aspose.cells.tables.ListObject, list_column : aspose.cells.tables.ListColumn, dest_cell_name : str) -> int:
        '''Add a new Slicer using ListObjet as data source
        
        :param table: ListObject object
        :param list_column: The ListColumn in ListObject.ListColumns
        :param dest_cell_name: The cell in the upper-left corner of the Slicer range.
        :returns: The new add Slicer index'''
        raise NotImplementedError()
    
    @overload
    def add(self, table : aspose.cells.tables.ListObject, list_column : aspose.cells.tables.ListColumn, row : int, column : int) -> int:
        '''Add a new Slicer using ListObjet as data source
        
        :param table: ListObject object
        :param list_column: The ListColumn in ListObject.ListColumns
        :param row: Row index of the cell in the upper-left corner of the Slicer range.
        :param column: Column index of the cell in the upper-left corner of the Slicer range.
        :returns: The new add Slicer index'''
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.slicers.Slicer]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.slicers.Slicer], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.slicers.Slicer, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.slicers.Slicer, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.slicers.Slicer) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.slicers.Slicer, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.slicers.Slicer, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def get(self, name : str) -> aspose.cells.slicers.Slicer:
        '''Gets the Slicer  by slicer\'s name.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.slicers.Slicer) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class SlicerCacheCrossFilterType:
    '''Represent the type of SlicerCacheCrossFilterType'''
    
    NONE : SlicerCacheCrossFilterType
    '''The table style element of the slicer style for slicer items
    with no data is not applied to slicer items with no data, and slicer items
    with no data are not sorted separately in the list of slicer items in the slicer view'''
    SHOW_ITEMS_WITH_DATA_AT_TOP : SlicerCacheCrossFilterType
    '''The table style element of the slicer style for slicer items with
    no data is applied to slicer items with no data, and slicer items
    with no data are sorted at the bottom in the list of slicer items in the slicer view'''
    SHOW_ITEMS_WITH_NO_DATA : SlicerCacheCrossFilterType
    '''The table style element of the slicer style for slicer items with no data
    is applied to slicer items with no data, and slicer items with no data
    are not sorted separately in the list of slicer items in the slicer view.'''

class SlicerCacheItemSortType:
    '''Specify the sort type of SlicerCacheItem'''
    
    NATURAL : SlicerCacheItemSortType
    '''Original data order.'''
    ASCENDING : SlicerCacheItemSortType
    '''Ascending sort type'''
    DESCENDING : SlicerCacheItemSortType
    '''Descending sort type'''

class SlicerStyleType:
    '''Specify the style of slicer view'''
    
    SLICER_STYLE_LIGHT1 : SlicerStyleType
    '''built-in light style one'''
    SLICER_STYLE_LIGHT2 : SlicerStyleType
    '''built-in light style two'''
    SLICER_STYLE_LIGHT3 : SlicerStyleType
    '''built-in light style three'''
    SLICER_STYLE_LIGHT4 : SlicerStyleType
    '''built-in light style four'''
    SLICER_STYLE_LIGHT5 : SlicerStyleType
    '''built-in light style five'''
    SLICER_STYLE_LIGHT6 : SlicerStyleType
    '''built-in light style six'''
    SLICER_STYLE_OTHER1 : SlicerStyleType
    '''built-in style other one'''
    SLICER_STYLE_OTHER2 : SlicerStyleType
    '''built-in style other two'''
    SLICER_STYLE_DARK1 : SlicerStyleType
    '''built-in dark style one'''
    SLICER_STYLE_DARK2 : SlicerStyleType
    '''built-in dark style tow'''
    SLICER_STYLE_DARK3 : SlicerStyleType
    '''built-in dark style three'''
    SLICER_STYLE_DARK4 : SlicerStyleType
    '''built-in dark style four'''
    SLICER_STYLE_DARK5 : SlicerStyleType
    '''built-in dark style five'''
    SLICER_STYLE_DARK6 : SlicerStyleType
    '''built-in dark style six'''
    CUSTOM : SlicerStyleType
    '''user-defined style, unsupported for now'''

