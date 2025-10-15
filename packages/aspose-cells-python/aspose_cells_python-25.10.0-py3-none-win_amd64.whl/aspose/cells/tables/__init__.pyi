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

class ListColumn:
    '''Represents a column in a Table.'''
    
    def get_custom_totals_row_formula(self, is_r1c1 : bool, is_local : bool) -> str:
        '''Gets the formula of totals row of this list column.
        
        :param is_r1c1: Whether the formula needs to be formatted as R1C1.
        :param is_local: Whether the formula needs to be formatted by locale.
        :returns: The formula of this list column.'''
        raise NotImplementedError()
    
    def set_custom_totals_row_formula(self, formula : str, is_r1c1 : bool, is_local : bool) -> None:
        '''Gets the formula of totals row of this list column.
        
        :param formula: the formula for this list column.
        :param is_r1c1: Whether the formula needs to be formatted as R1C1.
        :param is_local: Whether the formula needs to be formatted by locale.'''
        raise NotImplementedError()
    
    def get_custom_calculated_formula(self, is_r1c1 : bool, is_local : bool) -> str:
        '''Gets the formula of this list column.
        
        :param is_r1c1: Whether the formula needs to be formatted as R1C1.
        :param is_local: Whether the formula needs to be formatted by locale.
        :returns: The formula of this list column.'''
        raise NotImplementedError()
    
    def set_custom_calculated_formula(self, formula : str, is_r1c1 : bool, is_local : bool) -> None:
        '''Sets the formula for this list column.
        
        :param formula: the formula for this list column.
        :param is_r1c1: Whether the formula needs to be formatted as R1C1.
        :param is_local: Whether the formula needs to be formatted by locale.'''
        raise NotImplementedError()
    
    def get_data_style(self) -> aspose.cells.Style:
        '''Gets the style of the data in this column of the table.'''
        raise NotImplementedError()
    
    def set_data_style(self, style : aspose.cells.Style) -> None:
        '''Sets the style of the data in this column of the table.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets and sets the name of the column.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Gets and sets the name of the column.'''
        raise NotImplementedError()
    
    @property
    def totals_calculation(self) -> aspose.cells.tables.TotalsCalculation:
        '''Gets and sets the type of calculation in the Totals row of the list column.'''
        raise NotImplementedError()
    
    @totals_calculation.setter
    def totals_calculation(self, value : aspose.cells.tables.TotalsCalculation) -> None:
        '''Gets and sets the type of calculation in the Totals row of the list column.'''
        raise NotImplementedError()
    
    @property
    def range(self) -> aspose.cells.Range:
        '''Gets the range of this list column.'''
        raise NotImplementedError()
    
    @property
    def is_array_formula(self) -> bool:
        '''Indicates whether the fomula is array formula.'''
        raise NotImplementedError()
    
    @property
    def formula(self) -> str:
        '''Gets and sets the formula of the list column.'''
        raise NotImplementedError()
    
    @formula.setter
    def formula(self, value : str) -> None:
        '''Gets and sets the formula of the list column.'''
        raise NotImplementedError()
    
    @property
    def totals_row_label(self) -> str:
        '''Gets and sets the display labels of total row.'''
        raise NotImplementedError()
    
    @totals_row_label.setter
    def totals_row_label(self, value : str) -> None:
        '''Gets and sets the display labels of total row.'''
        raise NotImplementedError()
    

class ListColumnCollection:
    '''Represents A collection of all the :py:class:`aspose.cells.tables.ListColumn` objects in the specified ListObject object.'''
    
    @overload
    def get(self, index : int) -> aspose.cells.tables.ListColumn:
        '''Add API for Python Via .Net.since this[int] is unsupported'''
        raise NotImplementedError()
    
    @overload
    def get(self, name : str) -> aspose.cells.tables.ListColumn:
        '''Add API for Python Via .Net.since this[string] is unsupported
        
        :param name: The name of the ListColumn'''
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.tables.ListColumn]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.tables.ListColumn], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.tables.ListColumn, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.tables.ListColumn, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.tables.ListColumn) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.tables.ListColumn, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.tables.ListColumn, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.tables.ListColumn) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class ListObject:
    '''Represents a list object on a worksheet.
    The ListObject object is a member of the ListObjects collection.
    The ListObjects collection contains all the list objects on a worksheet.'''
    
    @overload
    def put_cell_value(self, row_offset : int, column_offset : int, value : Any) -> None:
        '''Put the value to the cell.
        
        :param row_offset: The row offset in the table.
        :param column_offset: The column offset in the table.
        :param value: The cell value.'''
        raise NotImplementedError()
    
    @overload
    def put_cell_value(self, row_offset : int, column_offset : int, value : Any, is_totals_row_label : bool) -> None:
        '''Put the value to the cell.
        
        :param row_offset: The row offset in the table.
        :param column_offset: The column offset in the table.
        :param value: The cell value.
        :param is_totals_row_label: Indicates whether it is a label for total row,only works for total row.
        If False and this row is total row, a new row will be inserted.'''
        raise NotImplementedError()
    
    @overload
    def put_cell_formula(self, row_offset : int, column_offset : int, formula : str) -> None:
        '''Put the formula to the cell in the table.
        
        :param row_offset: The row offset in the table.
        :param column_offset: The column offset in the table.
        :param formula: The formula of the cell.'''
        raise NotImplementedError()
    
    @overload
    def put_cell_formula(self, row_offset : int, column_offset : int, formula : str, is_totals_row_formula : bool) -> None:
        '''Put the formula to the cell in the table.
        
        :param row_offset: The row offset in the table.
        :param column_offset: The column offset in the table.
        :param formula: The formula of the cell.'''
        raise NotImplementedError()
    
    @overload
    def convert_to_range(self) -> None:
        '''Convert the table to range.'''
        raise NotImplementedError()
    
    @overload
    def convert_to_range(self, options : aspose.cells.tables.TableToRangeOptions) -> None:
        '''Convert the table to range.
        
        :param options: the options when converting table to range.'''
        raise NotImplementedError()
    
    def resize(self, start_row : int, start_column : int, end_row : int, end_column : int, has_headers : bool) -> None:
        '''Resize the range of the list object.
        
        :param start_row: The start row index of the new range.
        :param start_column: The start column index of the new range.
        :param end_row: The end row index of the new range.
        :param end_column: The end column index of the new range.
        :param has_headers: Whether this table has headers.'''
        raise NotImplementedError()
    
    def update_column_name(self) -> None:
        '''Updates all list columns\' name from the worksheet.'''
        raise NotImplementedError()
    
    def filter(self) -> aspose.cells.AutoFilter:
        '''Filter the table.'''
        raise NotImplementedError()
    
    def apply_style_to_range(self) -> None:
        '''Apply the table style to the range.'''
        raise NotImplementedError()
    
    @property
    def start_row(self) -> int:
        '''Gets the start row of the range.'''
        raise NotImplementedError()
    
    @property
    def start_column(self) -> int:
        '''Gets the start column of the range.'''
        raise NotImplementedError()
    
    @property
    def end_row(self) -> int:
        '''Gets the end  row of the range.'''
        raise NotImplementedError()
    
    @property
    def end_column(self) -> int:
        '''Gets the end column of the range.'''
        raise NotImplementedError()
    
    @property
    def list_columns(self) -> aspose.cells.tables.ListColumnCollection:
        '''Gets ListColumns of the ListObject.'''
        raise NotImplementedError()
    
    @property
    def show_header_row(self) -> bool:
        '''Gets and sets whether this ListObject show header row.'''
        raise NotImplementedError()
    
    @show_header_row.setter
    def show_header_row(self, value : bool) -> None:
        '''Gets and sets whether this ListObject show header row.'''
        raise NotImplementedError()
    
    @property
    def show_totals(self) -> bool:
        '''Gets and sets whether this ListObject show total row.'''
        raise NotImplementedError()
    
    @show_totals.setter
    def show_totals(self, value : bool) -> None:
        '''Gets and sets whether this ListObject show total row.'''
        raise NotImplementedError()
    
    @property
    def data_range(self) -> aspose.cells.Range:
        '''Gets the data range of the ListObject.'''
        raise NotImplementedError()
    
    @property
    def query_table(self) -> aspose.cells.QueryTable:
        '''Gets the linked QueryTable.'''
        raise NotImplementedError()
    
    @property
    def data_source_type(self) -> aspose.cells.tables.TableDataSourceType:
        '''Gets the data source type of the table.'''
        raise NotImplementedError()
    
    @property
    def auto_filter(self) -> aspose.cells.AutoFilter:
        '''Gets auto filter.'''
        raise NotImplementedError()
    
    @property
    def display_name(self) -> str:
        '''Gets and sets the display name.'''
        raise NotImplementedError()
    
    @display_name.setter
    def display_name(self, value : str) -> None:
        '''Gets and sets the display name.'''
        raise NotImplementedError()
    
    @property
    def comment(self) -> str:
        '''Gets and sets the comment of the table.'''
        raise NotImplementedError()
    
    @comment.setter
    def comment(self, value : str) -> None:
        '''Gets and sets the comment of the table.'''
        raise NotImplementedError()
    
    @property
    def show_table_style_first_column(self) -> bool:
        '''Indicates whether the first column in the table should have the style applied.'''
        raise NotImplementedError()
    
    @show_table_style_first_column.setter
    def show_table_style_first_column(self, value : bool) -> None:
        '''Indicates whether the first column in the table should have the style applied.'''
        raise NotImplementedError()
    
    @property
    def show_table_style_last_column(self) -> bool:
        '''Indicates whether the last column in the table should have the style applied.'''
        raise NotImplementedError()
    
    @show_table_style_last_column.setter
    def show_table_style_last_column(self, value : bool) -> None:
        '''Indicates whether the last column in the table should have the style applied.'''
        raise NotImplementedError()
    
    @property
    def show_table_style_row_stripes(self) -> bool:
        '''Indicates whether row stripe formatting is applied.'''
        raise NotImplementedError()
    
    @show_table_style_row_stripes.setter
    def show_table_style_row_stripes(self, value : bool) -> None:
        '''Indicates whether row stripe formatting is applied.'''
        raise NotImplementedError()
    
    @property
    def show_table_style_column_stripes(self) -> bool:
        '''Indicates whether column stripe formatting is applied.'''
        raise NotImplementedError()
    
    @show_table_style_column_stripes.setter
    def show_table_style_column_stripes(self, value : bool) -> None:
        '''Indicates whether column stripe formatting is applied.'''
        raise NotImplementedError()
    
    @property
    def table_style_type(self) -> aspose.cells.tables.TableStyleType:
        '''Gets and the built-in table style.'''
        raise NotImplementedError()
    
    @table_style_type.setter
    def table_style_type(self, value : aspose.cells.tables.TableStyleType) -> None:
        '''Gets and the built-in table style.'''
        raise NotImplementedError()
    
    @property
    def table_style_name(self) -> str:
        '''Gets and sets the table style name.'''
        raise NotImplementedError()
    
    @table_style_name.setter
    def table_style_name(self, value : str) -> None:
        '''Gets and sets the table style name.'''
        raise NotImplementedError()
    
    @property
    def xml_map(self) -> aspose.cells.XmlMap:
        '''Gets an :py:attr:`aspose.cells.tables.ListObject.xml_map` used for this list.'''
        raise NotImplementedError()
    
    @property
    def alternative_text(self) -> str:
        '''Gets and sets the alternative text.'''
        raise NotImplementedError()
    
    @alternative_text.setter
    def alternative_text(self, value : str) -> None:
        '''Gets and sets the alternative text.'''
        raise NotImplementedError()
    
    @property
    def alternative_description(self) -> str:
        '''Gets and sets the alternative description.'''
        raise NotImplementedError()
    
    @alternative_description.setter
    def alternative_description(self, value : str) -> None:
        '''Gets and sets the alternative description.'''
        raise NotImplementedError()
    

class ListObjectCollection:
    '''Represents a collection of :py:class:`aspose.cells.tables.ListObject` objects in the worksheet.'''
    
    @overload
    def get(self, index : int) -> aspose.cells.tables.ListObject:
        '''Add API for Python Via .Net.since this[int] is unsupported'''
        raise NotImplementedError()
    
    @overload
    def get(self, table_name : str) -> aspose.cells.tables.ListObject:
        '''Add API for Python Via .Net.since this[string] is unsupported
        
        :param table_name: ListObject name'''
        raise NotImplementedError()
    
    @overload
    def add(self, start_row : int, start_column : int, end_row : int, end_column : int, has_headers : bool) -> int:
        '''Adds a ListObject to the worksheet.
        
        :param start_row: The start row of the list range.
        :param start_column: The start row of the list range.
        :param end_row: The start row of the list range.
        :param end_column: The start row of the list range.
        :param has_headers: Whether the range has headers.
        :returns: The index of the new ListObject'''
        raise NotImplementedError()
    
    @overload
    def add(self, start_cell : str, end_cell : str, has_headers : bool) -> int:
        '''Adds a ListObject to the worksheet.
        
        :param start_cell: The start cell of the list range.
        :param end_cell: The end cell of the list range.
        :param has_headers: Whether the range has headers.
        :returns: The index of the new ListObject'''
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.tables.ListObject]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.tables.ListObject], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.tables.ListObject, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.tables.ListObject, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.tables.ListObject) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.tables.ListObject, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.tables.ListObject, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def update_column_name(self) -> None:
        '''Update all column name of the tables.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.tables.ListObject) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class TableStyle:
    '''Represents the table style.'''
    
    @property
    def name(self) -> str:
        '''Gets the name of table style.'''
        raise NotImplementedError()
    
    @property
    def table_style_elements(self) -> aspose.cells.tables.TableStyleElementCollection:
        '''Gets all elements of the table style.'''
        raise NotImplementedError()
    

class TableStyleCollection:
    '''Represents all custom table styles.'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.tables.TableStyle]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.tables.TableStyle], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.tables.TableStyle, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.tables.TableStyle, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.tables.TableStyle) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.tables.TableStyle, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.tables.TableStyle, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add_table_style(self, name : str) -> int:
        '''Adds a custom table style.
        
        :param name: The table style name.
        :returns: The index of the table style.'''
        raise NotImplementedError()
    
    def add_pivot_table_style(self, name : str) -> int:
        '''Adds a custom pivot table style.
        
        :param name: The pivot table style name.
        :returns: The index of the pivot table style.'''
        raise NotImplementedError()
    
    def get(self, name : str) -> aspose.cells.tables.TableStyle:
        '''Gets the table style by the name.
        
        :param name: The table style name.
        :returns: The table style object.'''
        raise NotImplementedError()
    
    def get_builtin_table_style(self, type : aspose.cells.tables.TableStyleType) -> aspose.cells.tables.TableStyle:
        '''Gets the builtin table style
        
        :param type: The builtin table style type.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.tables.TableStyle) -> int:
        raise NotImplementedError()
    
    @property
    def default_table_style_name(self) -> str:
        '''Gets and sets the default style name of the table.'''
        raise NotImplementedError()
    
    @default_table_style_name.setter
    def default_table_style_name(self, value : str) -> None:
        '''Gets and sets the default style name of the table.'''
        raise NotImplementedError()
    
    @property
    def default_pivot_style_name(self) -> str:
        '''Gets and sets the  default style name of pivot table .'''
        raise NotImplementedError()
    
    @default_pivot_style_name.setter
    def default_pivot_style_name(self, value : str) -> None:
        '''Gets and sets the  default style name of pivot table .'''
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class TableStyleElement:
    '''Represents the element of the table style.'''
    
    def get_element_style(self) -> aspose.cells.Style:
        '''Gets the element style.
        
        :returns: Returns the :py:class:`aspose.cells.Style` object.'''
        raise NotImplementedError()
    
    def set_element_style(self, style : aspose.cells.Style) -> None:
        '''Sets the element style.
        
        :param style: The element style.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Number of rows or columns in a single band of striping.
        Applies only when type is firstRowStripe, secondRowStripe, firstColumnStripe, or secondColumnStripe.'''
        raise NotImplementedError()
    
    @size.setter
    def size(self, value : int) -> None:
        '''Number of rows or columns in a single band of striping.
        Applies only when type is firstRowStripe, secondRowStripe, firstColumnStripe, or secondColumnStripe.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.tables.TableStyleElementType:
        '''Gets the element type.'''
        raise NotImplementedError()
    

class TableStyleElementCollection:
    '''Represents all elements of the table style.'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.tables.TableStyleElement]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.tables.TableStyleElement], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.tables.TableStyleElement, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.tables.TableStyleElement, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.tables.TableStyleElement) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.tables.TableStyleElement, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.tables.TableStyleElement, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add(self, type : aspose.cells.tables.TableStyleElementType) -> int:
        '''Adds an element.
        
        :param type: The type of the element
        :returns: Returns the index of the element in the list.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.tables.TableStyleElement) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class TableToRangeOptions:
    '''Represents the options when converting table to range.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def last_row(self) -> int:
        '''Gets and sets the last row index of the table.'''
        raise NotImplementedError()
    
    @last_row.setter
    def last_row(self, value : int) -> None:
        '''Gets and sets the last row index of the table.'''
        raise NotImplementedError()
    

class TableDataSourceType:
    '''Represents the table\'s data source type.'''
    
    WORKSHEET : TableDataSourceType
    '''Excel Worksheet Table'''
    SHARE_POINT : TableDataSourceType
    '''Read-write SharePoint linked List'''
    XML : TableDataSourceType
    '''XML mapper Table'''
    QUERY_TABLE : TableDataSourceType
    '''Query Table'''

class TableStyleElementType:
    '''Represents the Table or PivotTable style element type.'''
    
    BLANK_ROW : TableStyleElementType
    '''Table style element that applies to PivotTable\'s blank rows.'''
    FIRST_COLUMN : TableStyleElementType
    '''Table style element that applies to table\'s first column.'''
    FIRST_COLUMN_STRIPE : TableStyleElementType
    '''Table style element that applies to table\'s first column stripes.'''
    FIRST_COLUMN_SUBHEADING : TableStyleElementType
    '''Table style element that applies to PivotTable\'s first column subheading.'''
    FIRST_HEADER_CELL : TableStyleElementType
    '''Table style element that applies to table\'s first header row cell.'''
    FIRST_ROW_STRIPE : TableStyleElementType
    '''Table style element that applies to table\'s first row stripes.'''
    FIRST_ROW_SUBHEADING : TableStyleElementType
    '''Table style element that applies to PivotTable\'s first row subheading.'''
    FIRST_SUBTOTAL_COLUMN : TableStyleElementType
    '''Table style element that applies to PivotTable\'s first subtotal column.'''
    FIRST_SUBTOTAL_ROW : TableStyleElementType
    '''Table style element that applies to pivot table\'s first subtotal row.'''
    GRAND_TOTAL_COLUMN : TableStyleElementType
    '''Table style element that applies to pivot table\'s grand total column.'''
    GRAND_TOTAL_ROW : TableStyleElementType
    '''Table style element that applies to pivot table\'s grand total row.'''
    FIRST_TOTAL_CELL : TableStyleElementType
    '''Table style element that applies to table\'s first total row cell.'''
    HEADER_ROW : TableStyleElementType
    '''Table style element that applies to table\'s header row.'''
    LAST_COLUMN : TableStyleElementType
    '''Table style element that applies to table\'s last column.'''
    LAST_HEADER_CELL : TableStyleElementType
    '''Table style element that applies to table\'s last header row cell.'''
    LAST_TOTAL_CELL : TableStyleElementType
    '''Table style element that applies to table\'s last total row cell.'''
    PAGE_FIELD_LABELS : TableStyleElementType
    '''Table style element that applies to pivot table\'s page field labels.'''
    PAGE_FIELD_VALUES : TableStyleElementType
    '''Table style element that applies to pivot table\'s page field values.'''
    SECOND_COLUMN_STRIPE : TableStyleElementType
    '''Table style element that applies to table\'s second column stripes.'''
    SECOND_COLUMN_SUBHEADING : TableStyleElementType
    '''Table style element that applies to pivot table\'s second column subheading.'''
    SECOND_ROW_STRIPE : TableStyleElementType
    '''Table style element that applies to table\'s second row stripes.'''
    SECOND_ROW_SUBHEADING : TableStyleElementType
    '''Table style element that applies to pivot table\'s second row subheading.'''
    SECOND_SUBTOTAL_COLUMN : TableStyleElementType
    '''Table style element that applies to PivotTable\'s second subtotal column.'''
    SECOND_SUBTOTAL_ROW : TableStyleElementType
    '''Table style element that applies to PivotTable\'s second subtotal row.'''
    THIRD_COLUMN_SUBHEADING : TableStyleElementType
    '''Table style element that applies to PivotTable\'s third column subheading.'''
    THIRD_ROW_SUBHEADING : TableStyleElementType
    '''Table style element that applies to PivotTable\'s third row subheading.'''
    THIRD_SUBTOTAL_COLUMN : TableStyleElementType
    '''Table style element that applies to pivot table\'s third subtotal column.'''
    THIRD_SUBTOTAL_ROW : TableStyleElementType
    '''Table style element that applies to PivotTable\'s third subtotal row.'''
    TOTAL_ROW : TableStyleElementType
    '''Table style element that applies to table\'s total row.'''
    WHOLE_TABLE : TableStyleElementType
    '''Table style element that applies to table\'s entire content.'''

class TableStyleType:
    '''Represents the built-in table style type.'''
    
    NONE : TableStyleType
    TABLE_STYLE_LIGHT1 : TableStyleType
    TABLE_STYLE_LIGHT2 : TableStyleType
    TABLE_STYLE_LIGHT3 : TableStyleType
    TABLE_STYLE_LIGHT4 : TableStyleType
    TABLE_STYLE_LIGHT5 : TableStyleType
    TABLE_STYLE_LIGHT6 : TableStyleType
    TABLE_STYLE_LIGHT7 : TableStyleType
    TABLE_STYLE_LIGHT8 : TableStyleType
    TABLE_STYLE_LIGHT9 : TableStyleType
    TABLE_STYLE_LIGHT10 : TableStyleType
    TABLE_STYLE_LIGHT11 : TableStyleType
    TABLE_STYLE_LIGHT12 : TableStyleType
    TABLE_STYLE_LIGHT13 : TableStyleType
    TABLE_STYLE_LIGHT14 : TableStyleType
    TABLE_STYLE_LIGHT15 : TableStyleType
    TABLE_STYLE_LIGHT16 : TableStyleType
    TABLE_STYLE_LIGHT17 : TableStyleType
    TABLE_STYLE_LIGHT18 : TableStyleType
    TABLE_STYLE_LIGHT19 : TableStyleType
    TABLE_STYLE_LIGHT20 : TableStyleType
    TABLE_STYLE_LIGHT21 : TableStyleType
    TABLE_STYLE_MEDIUM1 : TableStyleType
    TABLE_STYLE_MEDIUM2 : TableStyleType
    TABLE_STYLE_MEDIUM3 : TableStyleType
    TABLE_STYLE_MEDIUM4 : TableStyleType
    TABLE_STYLE_MEDIUM5 : TableStyleType
    TABLE_STYLE_MEDIUM6 : TableStyleType
    TABLE_STYLE_MEDIUM7 : TableStyleType
    TABLE_STYLE_MEDIUM8 : TableStyleType
    TABLE_STYLE_MEDIUM9 : TableStyleType
    TABLE_STYLE_MEDIUM10 : TableStyleType
    TABLE_STYLE_MEDIUM11 : TableStyleType
    TABLE_STYLE_MEDIUM12 : TableStyleType
    TABLE_STYLE_MEDIUM13 : TableStyleType
    TABLE_STYLE_MEDIUM14 : TableStyleType
    TABLE_STYLE_MEDIUM15 : TableStyleType
    TABLE_STYLE_MEDIUM16 : TableStyleType
    TABLE_STYLE_MEDIUM17 : TableStyleType
    TABLE_STYLE_MEDIUM18 : TableStyleType
    TABLE_STYLE_MEDIUM19 : TableStyleType
    TABLE_STYLE_MEDIUM20 : TableStyleType
    TABLE_STYLE_MEDIUM21 : TableStyleType
    TABLE_STYLE_MEDIUM22 : TableStyleType
    TABLE_STYLE_MEDIUM23 : TableStyleType
    TABLE_STYLE_MEDIUM24 : TableStyleType
    TABLE_STYLE_MEDIUM25 : TableStyleType
    TABLE_STYLE_MEDIUM26 : TableStyleType
    TABLE_STYLE_MEDIUM27 : TableStyleType
    TABLE_STYLE_MEDIUM28 : TableStyleType
    TABLE_STYLE_DARK1 : TableStyleType
    TABLE_STYLE_DARK2 : TableStyleType
    TABLE_STYLE_DARK3 : TableStyleType
    TABLE_STYLE_DARK4 : TableStyleType
    TABLE_STYLE_DARK5 : TableStyleType
    TABLE_STYLE_DARK6 : TableStyleType
    TABLE_STYLE_DARK7 : TableStyleType
    TABLE_STYLE_DARK8 : TableStyleType
    TABLE_STYLE_DARK9 : TableStyleType
    TABLE_STYLE_DARK10 : TableStyleType
    TABLE_STYLE_DARK11 : TableStyleType
    CUSTOM : TableStyleType

class TotalsCalculation:
    '''Determines the type of calculation in the Totals row of the list column.'''
    
    SUM : TotalsCalculation
    '''Represents Sum totals calculation.'''
    COUNT : TotalsCalculation
    '''Represents Count totals calculation.'''
    AVERAGE : TotalsCalculation
    '''Represents Average totals calculation.'''
    MAX : TotalsCalculation
    '''Represents Max totals calculation.'''
    MIN : TotalsCalculation
    '''Represents Min totals calculation.'''
    VAR : TotalsCalculation
    '''Represents Var totals calculation.'''
    COUNT_NUMS : TotalsCalculation
    '''Represents Count Nums totals calculation.'''
    STD_DEV : TotalsCalculation
    '''Represents StdDev totals calculation.'''
    NONE : TotalsCalculation
    '''Represents No totals calculation.'''
    CUSTOM : TotalsCalculation
    '''Represents custom calculation.'''

