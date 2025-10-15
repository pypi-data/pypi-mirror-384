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

class CustomPiovtFieldGroupItem:
    '''Represents an item of custom grouped field.'''
    
    def __init__(self, name : str, item_indexes : List[int]) -> None:
        '''The constructor of custom group item of pivot field.
        
        :param name: The name of group item
        :param item_indexes: All indexes to the items of base pivot field.'''
        raise NotImplementedError()
    

class PivotArea:
    '''Presents the selected area of the PivotTable.'''
    
    def __init__(self, table : aspose.cells.pivot.PivotTable) -> None:
        '''Presents the selected area of the PivotTable.'''
        raise NotImplementedError()
    
    @overload
    def select_field(self, axis_type : aspose.cells.pivot.PivotFieldType, field_name : str) -> None:
        '''Select a field in the region as an area.
        
        :param axis_type: The region type.
        :param field_name: The name of pivot field.'''
        raise NotImplementedError()
    
    @overload
    def select_field(self, axis_type : aspose.cells.pivot.PivotFieldType, field : aspose.cells.pivot.PivotField) -> None:
        '''Select a field in the region as an area.
        
        :param axis_type: The region type.
        :param field: The pivot field.'''
        raise NotImplementedError()
    
    def select(self, axis_type : aspose.cells.pivot.PivotFieldType, field_position : int, selection_type : aspose.cells.pivot.PivotTableSelectionType) -> None:
        '''Select the area with filters.
        
        :param axis_type: The region of the PivotTable to which this rule applies.
        :param field_position: Position of the field within the axis to which this rule applies.
        :param selection_type: Specifies what can be selected in a PivotTable during a structured selection.'''
        raise NotImplementedError()
    
    def get_cell_areas(self) -> List[aspose.cells.CellArea]:
        '''Gets cell areas of this pivot area.'''
        raise NotImplementedError()
    
    @property
    def filters(self) -> aspose.cells.pivot.PivotAreaFilterCollection:
        '''Gets all filters for this PivotArea.'''
        raise NotImplementedError()
    
    @property
    def only_data(self) -> bool:
        '''Indicates whether only the data values (in the data area of the view) for an item
        selection are selected and does not include the item labels.'''
        raise NotImplementedError()
    
    @only_data.setter
    def only_data(self, value : bool) -> None:
        '''Indicates whether only the data values (in the data area of the view) for an item
        selection are selected and does not include the item labels.'''
        raise NotImplementedError()
    
    @property
    def only_label(self) -> bool:
        '''Indicates whether only the data labels for an item selection are selected.'''
        raise NotImplementedError()
    
    @only_label.setter
    def only_label(self, value : bool) -> None:
        '''Indicates whether only the data labels for an item selection are selected.'''
        raise NotImplementedError()
    
    @property
    def is_row_grand_included(self) -> bool:
        '''Indicates whether the row grand total is included.'''
        raise NotImplementedError()
    
    @is_row_grand_included.setter
    def is_row_grand_included(self, value : bool) -> None:
        '''Indicates whether the row grand total is included.'''
        raise NotImplementedError()
    
    @property
    def is_column_grand_included(self) -> bool:
        '''Indicates whether the column grand total is included.'''
        raise NotImplementedError()
    
    @is_column_grand_included.setter
    def is_column_grand_included(self, value : bool) -> None:
        '''Indicates whether the column grand total is included.'''
        raise NotImplementedError()
    
    @property
    def axis_type(self) -> aspose.cells.pivot.PivotFieldType:
        '''Gets and sets the region of the PivotTable to which this rule applies.'''
        raise NotImplementedError()
    
    @axis_type.setter
    def axis_type(self, value : aspose.cells.pivot.PivotFieldType) -> None:
        '''Gets and sets the region of the PivotTable to which this rule applies.'''
        raise NotImplementedError()
    
    @property
    def rule_type(self) -> aspose.cells.pivot.PivotAreaType:
        '''Gets and sets the type of selection rule.'''
        raise NotImplementedError()
    
    @rule_type.setter
    def rule_type(self, value : aspose.cells.pivot.PivotAreaType) -> None:
        '''Gets and sets the type of selection rule.'''
        raise NotImplementedError()
    
    @property
    def is_outline(self) -> bool:
        '''Indicates whether the rule refers to an area that is in outline mode.'''
        raise NotImplementedError()
    
    @is_outline.setter
    def is_outline(self, value : bool) -> None:
        '''Indicates whether the rule refers to an area that is in outline mode.'''
        raise NotImplementedError()
    

class PivotAreaCollection:
    '''Represents a list of pivot area.'''
    
    @overload
    def add(self, pivot_area : aspose.cells.pivot.PivotArea) -> int:
        '''Adds pivot area.
        
        :param pivot_area: The pivot area.'''
        raise NotImplementedError()
    
    @overload
    def add(self, cell_area : aspose.cells.CellArea) -> None:
        '''Adds an area based on pivot table view.
        
        :param cell_area: The area based on pivot table view.'''
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.pivot.PivotArea]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.pivot.PivotArea], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.pivot.PivotArea, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.pivot.PivotArea, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotArea) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotArea, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotArea, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.pivot.PivotArea) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class PivotAreaFilter:
    '''Represents the filter of :py:class:`aspose.cells.pivot.PivotArea` for :py:class:`aspose.cells.pivot.PivotTable`.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def is_subtotal_set(self, subtotal_type : aspose.cells.pivot.PivotFieldSubtotalType) -> bool:
        '''Gets which subtotal is set for this filter.
        
        :param subtotal_type: The subtotal function type.'''
        raise NotImplementedError()
    
    def set_subtotals(self, subtotal_type : aspose.cells.pivot.PivotFieldSubtotalType, shown : bool) -> None:
        '''Subtotal for the filter.
        
        :param subtotal_type: The subtotal function.
        :param shown: Indicates if showing this subtotal data.'''
        raise NotImplementedError()
    
    @property
    def selected(self) -> bool:
        '''Indicates whether this field has selection.
        Only works when the PivotTable is in Outline view.'''
        raise NotImplementedError()
    
    @selected.setter
    def selected(self, value : bool) -> None:
        '''Indicates whether this field has selection.
        Only works when the PivotTable is in Outline view.'''
        raise NotImplementedError()
    

class PivotAreaFilterCollection:
    '''Represents the list of filters for :py:class:`aspose.cells.pivot.PivotArea`'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.pivot.PivotAreaFilter]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.pivot.PivotAreaFilter], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.pivot.PivotAreaFilter, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.pivot.PivotAreaFilter, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotAreaFilter) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotAreaFilter, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotAreaFilter, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.pivot.PivotAreaFilter) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class PivotConditionalFormat:
    '''Represents a PivotTable Format Condition in PivotFormatCondition Collection.'''
    
    @overload
    def add_field_area(self, axis_type : aspose.cells.pivot.PivotFieldType, field_name : str) -> None:
        '''Adds an area of pivot field.
        
        :param axis_type: The region type.
        :param field_name: The name of pivot field.'''
        raise NotImplementedError()
    
    @overload
    def add_field_area(self, axis_type : aspose.cells.pivot.PivotFieldType, field : aspose.cells.pivot.PivotField) -> None:
        '''Adds an area of pivot field.
        
        :param axis_type: The region type.
        :param field: The pivot field.'''
        raise NotImplementedError()
    
    def get_cell_areas(self) -> List[aspose.cells.CellArea]:
        '''Gets all cell areas where this conditional format applies to.'''
        raise NotImplementedError()
    
    def add_cell_area(self, ca : aspose.cells.CellArea) -> None:
        '''Adds an area based on pivot table view.
        
        :param ca: The cell area.'''
        raise NotImplementedError()
    
    def apply_to(self, row : int, column : int, scope : aspose.cells.pivot.PivotConditionFormatScopeType) -> None:
        '''Applies the conditional format to range.
        Only for the data region.
        
        :param row: The selected row.
        :param column: The selected column.
        :param scope: The scope'''
        raise NotImplementedError()
    
    @property
    def pivot_areas(self) -> aspose.cells.pivot.PivotAreaCollection:
        '''Gets all pivot areas.'''
        raise NotImplementedError()
    
    @property
    def format_conditions(self) -> aspose.cells.FormatConditionCollection:
        '''Get conditions for the pivot table conditional format .'''
        raise NotImplementedError()
    
    @property
    def scope_type(self) -> aspose.cells.pivot.PivotConditionFormatScopeType:
        '''Get and set scope type for the pivot table conditional format .'''
        raise NotImplementedError()
    
    @scope_type.setter
    def scope_type(self, value : aspose.cells.pivot.PivotConditionFormatScopeType) -> None:
        '''Get and set scope type for the pivot table conditional format .'''
        raise NotImplementedError()
    
    @property
    def rule_type(self) -> aspose.cells.pivot.PivotConditionFormatRuleType:
        '''Get and set rule type for the pivot table condition format .'''
        raise NotImplementedError()
    
    @rule_type.setter
    def rule_type(self, value : aspose.cells.pivot.PivotConditionFormatRuleType) -> None:
        '''Get and set rule type for the pivot table condition format .'''
        raise NotImplementedError()
    

class PivotConditionalFormatCollection:
    '''Represents all conditional formats of pivot table.'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.pivot.PivotConditionalFormat]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.pivot.PivotConditionalFormat], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.pivot.PivotConditionalFormat, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.pivot.PivotConditionalFormat, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotConditionalFormat) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotConditionalFormat, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotConditionalFormat, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add(self) -> int:
        '''Adds a pivot FormatCondition to the collection.
        
        :returns: pivot FormatCondition object index.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.pivot.PivotConditionalFormat) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class PivotDateTimeRangeGroupSettings(PivotFieldGroupSettings):
    '''Represents the field grouped by date time range.'''
    
    def is_grouped_by(self, type : aspose.cells.pivot.PivotGroupByType) -> bool:
        '''Check whether the field is grouped by the type.
        
        :param type: The group type'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.pivot.PivotFieldGroupType:
        '''Gets the data time group type.'''
        raise NotImplementedError()
    
    @property
    def start(self) -> datetime:
        '''Gets the start date time of the group.'''
        raise NotImplementedError()
    
    @property
    def end(self) -> datetime:
        '''Gets the end date time of the group.'''
        raise NotImplementedError()
    
    @property
    def interval(self) -> float:
        '''Gets the internal of the group.'''
        raise NotImplementedError()
    
    @property
    def group_by_types(self) -> List[aspose.cells.pivot.PivotGroupByType]:
        '''Gets the types of grouping by date time.'''
        raise NotImplementedError()
    

class PivotDiscreteGroupSettings(PivotFieldGroupSettings):
    '''Rrepsents the discrete group of pivot field'''
    
    @property
    def type(self) -> aspose.cells.pivot.PivotFieldGroupType:
        '''Gets the group type.'''
        raise NotImplementedError()
    
    @property
    def items(self) -> List[aspose.cells.pivot.CustomPiovtFieldGroupItem]:
        '''Gets the discrete items.'''
        raise NotImplementedError()
    

class PivotField:
    '''Represents a field in a PivotTable report.'''
    
    @overload
    def group_by(self, interval : float, new_field : bool) -> None:
        '''Automatically group the field with internal
        
        :param interval: The internal of group.
        Automatic value will be assigned if it\'s zero,
        :param new_field: Indicates whether adding a new field to the pivottable.'''
        raise NotImplementedError()
    
    @overload
    def group_by(self, start : datetime, end : datetime, groups : List[aspose.cells.pivot.PivotGroupByType], interval : float, first_as_new_field : bool) -> bool:
        '''Group the file by the date group types.
        
        :param start: The start datetime
        :param end: The end of datetime
        :param groups: Group types
        :param interval: The interval
        :param first_as_new_field: Indicates whether adding a new field to the pivottable.
        Only for the first group item.
        :returns: False means this field could not be grouped by date time.'''
        raise NotImplementedError()
    
    @overload
    def group_by(self, start : float, end : float, interval : float, new_field : bool) -> bool:
        '''Group the file by number.
        
        :param start: The start value
        :param end: The end of value
        :param interval: The interval
        :param new_field: Indicates whether adding a new field to the pivottable
        :returns: False means this field could not be grouped by date time.'''
        raise NotImplementedError()
    
    @overload
    def group_by(self, custom_group_items : List[aspose.cells.pivot.CustomPiovtFieldGroupItem], new_field : bool) -> bool:
        '''Custom group the field.
        
        :param custom_group_items: The custom group items.
        :param new_field: Indicates whether adding a new field to the pivottable
        :returns: False means this field could not be grouped by date time.'''
        raise NotImplementedError()
    
    @overload
    def sort_by(self, sort_type : aspose.cells.SortOrder, field_sorted_by : int) -> None:
        '''Sorts this pivot field.
        
        :param sort_type: The type of sorting this field.
        :param field_sorted_by: The index of pivot field sorted by.
        -1 means sorting by data labels of this field, others mean the index of data field sorted by.'''
        raise NotImplementedError()
    
    @overload
    def sort_by(self, sort_type : aspose.cells.SortOrder, field_sorted_by : int, data_type : aspose.cells.pivot.PivotLineType, cell_name : str) -> None:
        '''Sorts this pivot field.
        
        :param sort_type: The type of sorting this field.
        :param field_sorted_by: The index of pivot field sorted by.
        -1 means sorting by data labels of this field, others mean the index of data field sorted by.
        :param data_type: The type of data sorted by.
        :param cell_name: Sort by values in the row or column'''
        raise NotImplementedError()
    
    @overload
    def hide_item(self, index : int, is_hidden : bool) -> None:
        '''Sets whether the specific PivotItem in a data field is hidden.
        
        :param index: the index of the pivotItem in the pivotField.
        :param is_hidden: whether the specific PivotItem is hidden'''
        raise NotImplementedError()
    
    @overload
    def hide_item(self, item_value : str, is_hidden : bool) -> None:
        '''Sets whether the specific PivotItem in a data field is hidden.
        
        :param item_value: the value of the pivotItem in the pivotField.
        :param is_hidden: whether the specific PivotItem is hidden'''
        raise NotImplementedError()
    
    def init_pivot_items(self) -> None:
        '''Init the pivot items of the pivot field'''
        raise NotImplementedError()
    
    def ungroup(self) -> None:
        '''Ungroup the pivot field.'''
        raise NotImplementedError()
    
    def get_pivot_filter_by_type(self, type : aspose.cells.pivot.PivotFilterType) -> aspose.cells.pivot.PivotFilter:
        '''Gets the pivot filter of the pivot field by type'''
        raise NotImplementedError()
    
    def get_pivot_filters(self) -> List[Any]:
        '''Gets the pivot filters of the pivot field'''
        raise NotImplementedError()
    
    def get_filters(self) -> List[aspose.cells.pivot.PivotFilter]:
        '''Gets all pivot filters of this pivot field.'''
        raise NotImplementedError()
    
    def clear_filter(self) -> None:
        '''Clears filter setting on this pivot field.'''
        raise NotImplementedError()
    
    def filter_top10(self, value_field_index : int, type : aspose.cells.pivot.PivotFilterType, is_top : bool, item_count : int) -> aspose.cells.pivot.PivotFilter:
        '''Filters by values of data pivot field.
        
        :param value_field_index: The index of data field  in the data region.
        :param type: The type of filtering data. Only can be Count,Sum and Percent.
        :param is_top: Indicates whether filter from top or bottom
        :param item_count: The item count'''
        raise NotImplementedError()
    
    def filter_by_value(self, value_field_index : int, type : aspose.cells.pivot.PivotFilterType, value1 : float, value2 : float) -> aspose.cells.pivot.PivotFilter:
        '''Filters by values of data pivot field.
        
        :param value_field_index: The index of value field in the value region.
        :param type: The type of filtering data.
        :param value1: The value of filter condition
        :param value2: The upper-bound value of between filter condition'''
        raise NotImplementedError()
    
    def filter_by_label(self, type : aspose.cells.pivot.PivotFilterType, label1 : str, label2 : str) -> aspose.cells.pivot.PivotFilter:
        '''Filters by captions of row or column pivot field.
        
        :param type: The type of filtering data.
        :param label1: The label of filter condition
        :param label2: The upper-bound label of between filter condition'''
        raise NotImplementedError()
    
    def filter_by_date(self, type : aspose.cells.pivot.PivotFilterType, date_time1 : datetime, date_time2 : datetime) -> aspose.cells.pivot.PivotFilter:
        '''Filters by date setting of row or column pivot field.
        
        :param type: The type of filtering data.
        :param date_time1: The date label of filter condition
        :param date_time2: The upper-bound date label of between filter condition'''
        raise NotImplementedError()
    
    def get_calculated_field_formula(self) -> str:
        '''Get the formula string of the specified calculated field .'''
        raise NotImplementedError()
    
    def get_formula(self) -> str:
        '''Gets formula of the calculated field .'''
        raise NotImplementedError()
    
    def set_subtotals(self, subtotal_type : aspose.cells.pivot.PivotFieldSubtotalType, shown : bool) -> None:
        '''Sets whether the specified field shows that subtotals.
        
        :param subtotal_type: subtotals type.
        :param shown: whether the specified field shows that subtotals.'''
        raise NotImplementedError()
    
    def get_subtotals(self, subtotal_type : aspose.cells.pivot.PivotFieldSubtotalType) -> bool:
        '''Indicates whether showing specified subtotal.
        
        :param subtotal_type: subtotal type.
        :returns: Returns whether showing specified subtotal.'''
        raise NotImplementedError()
    
    def show_values_as(self, display_format : aspose.cells.pivot.PivotFieldDataDisplayFormat, base_field : int, base_item_position_type : aspose.cells.pivot.PivotItemPositionType, base_item : int) -> None:
        '''Shows values of data field as different display format when the ShowDataAs calculation is in use.
        
        :param display_format: The data display format type.
        :param base_field: The index to the field which ShowDataAs calculation bases on.
        :param base_item_position_type: The position type of base iteam.
        :param base_item: The index to the base item which ShowDataAs calculation bases on.
        Only works when baseItemPositionType is custom.'''
        raise NotImplementedError()
    
    def is_hidden_item(self, index : int) -> bool:
        '''Gets whether the specific PivotItem is hidden.
        
        :param index: The index of the pivotItem in the pivotField.
        :returns: whether the specific PivotItem is hidden'''
        raise NotImplementedError()
    
    def is_hidden_item_detail(self, index : int) -> bool:
        '''Gets whether hidding the detail of  the specific PivotItem..
        
        :param index: The index of the pivotItem in the pivotField.
        :returns: whether the specific PivotItem is hidden detail'''
        raise NotImplementedError()
    
    def hide_item_detail(self, index : int, is_hidden_detail : bool) -> None:
        '''Sets whether the specific PivotItem in a pivot field is hidden detail.
        
        :param index: the index of the pivotItem in the pivotField.
        :param is_hidden_detail: whether the specific PivotItem is hidden'''
        raise NotImplementedError()
    
    def hide_detail(self, is_hidden_detail : bool) -> None:
        '''Sets whether the PivotItems in a pivot field is hidden detail.That is collapse/expand this field.
        
        :param is_hidden_detail: Whether hide the detail of the pivot field.'''
        raise NotImplementedError()
    
    def add_calculated_item(self, name : str, formula : str) -> None:
        '''Add a calculated formula item to the pivot field.
        
        :param name: The item\'s name.
        :param formula: The formula of pivot item.'''
        raise NotImplementedError()
    
    @property
    def pivot_items(self) -> aspose.cells.pivot.PivotItemCollection:
        '''Gets the pivot items of the pivot field'''
        raise NotImplementedError()
    
    @property
    def range(self) -> aspose.cells.pivot.SxRng:
        '''Gets the group range of the pivot field'''
        raise NotImplementedError()
    
    @property
    def group_settings(self) -> aspose.cells.pivot.PivotFieldGroupSettings:
        '''Gets the group settings of the pivot field.'''
        raise NotImplementedError()
    
    @property
    def is_calculated_field(self) -> bool:
        '''Indicates whether the specified PivotTable field is calculated field.'''
        raise NotImplementedError()
    
    @property
    def is_value_fields(self) -> bool:
        '''Indicates whether this field represents values fields.'''
        raise NotImplementedError()
    
    @property
    def base_index(self) -> int:
        '''Represents the PivotField index in the base PivotFields.'''
        raise NotImplementedError()
    
    @base_index.setter
    def base_index(self, value : int) -> None:
        '''Represents the PivotField index in the base PivotFields.'''
        raise NotImplementedError()
    
    @property
    def position(self) -> int:
        '''Represents the index of :py:class:`aspose.cells.pivot.PivotField` in the region.'''
        raise NotImplementedError()
    
    @property
    def region_type(self) -> aspose.cells.pivot.PivotFieldType:
        '''Specifies the region of the PivotTable that this field is displayed.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Represents the name of PivotField.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Represents the name of PivotField.'''
        raise NotImplementedError()
    
    @property
    def display_name(self) -> str:
        '''Represents the PivotField display name.'''
        raise NotImplementedError()
    
    @display_name.setter
    def display_name(self, value : str) -> None:
        '''Represents the PivotField display name.'''
        raise NotImplementedError()
    
    @property
    def is_auto_subtotals(self) -> bool:
        '''Indicates whether the specified field shows automatic subtotals. Default is true.'''
        raise NotImplementedError()
    
    @is_auto_subtotals.setter
    def is_auto_subtotals(self, value : bool) -> None:
        '''Indicates whether the specified field shows automatic subtotals. Default is true.'''
        raise NotImplementedError()
    
    @property
    def drag_to_column(self) -> bool:
        '''Indicates whether the specified field can be dragged to the column position.
        The default value is true.'''
        raise NotImplementedError()
    
    @drag_to_column.setter
    def drag_to_column(self, value : bool) -> None:
        '''Indicates whether the specified field can be dragged to the column position.
        The default value is true.'''
        raise NotImplementedError()
    
    @property
    def drag_to_hide(self) -> bool:
        '''Indicates whether the specified field can be dragged to the hide position.
        The default value is true.'''
        raise NotImplementedError()
    
    @drag_to_hide.setter
    def drag_to_hide(self, value : bool) -> None:
        '''Indicates whether the specified field can be dragged to the hide position.
        The default value is true.'''
        raise NotImplementedError()
    
    @property
    def drag_to_row(self) -> bool:
        '''Indicates whether the specified field can be dragged to the row position.
        The default value is true.'''
        raise NotImplementedError()
    
    @drag_to_row.setter
    def drag_to_row(self, value : bool) -> None:
        '''Indicates whether the specified field can be dragged to the row position.
        The default value is true.'''
        raise NotImplementedError()
    
    @property
    def drag_to_page(self) -> bool:
        '''Indicates whether the specified field can be dragged to the page position.
        The default value is true.'''
        raise NotImplementedError()
    
    @drag_to_page.setter
    def drag_to_page(self, value : bool) -> None:
        '''Indicates whether the specified field can be dragged to the page position.
        The default value is true.'''
        raise NotImplementedError()
    
    @property
    def drag_to_data(self) -> bool:
        '''Indicates whether the specified field can be dragged to the data position.
        The default value is true.'''
        raise NotImplementedError()
    
    @drag_to_data.setter
    def drag_to_data(self, value : bool) -> None:
        '''Indicates whether the specified field can be dragged to the data position.
        The default value is true.'''
        raise NotImplementedError()
    
    @property
    def is_multiple_item_selection_allowed(self) -> bool:
        '''indicates whether the field can have multiple items
        selected in the page field
        The default value is false.'''
        raise NotImplementedError()
    
    @is_multiple_item_selection_allowed.setter
    def is_multiple_item_selection_allowed(self, value : bool) -> None:
        '''indicates whether the field can have multiple items
        selected in the page field
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def is_repeat_item_labels(self) -> bool:
        '''Indicates whether repeating labels of the field in the region.
        The default value is false.'''
        raise NotImplementedError()
    
    @is_repeat_item_labels.setter
    def is_repeat_item_labels(self, value : bool) -> None:
        '''Indicates whether repeating labels of the field in the region.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def is_include_new_items_in_filter(self) -> bool:
        '''Indicates whether including new items to the field in manual filter.
        The default value is false.'''
        raise NotImplementedError()
    
    @is_include_new_items_in_filter.setter
    def is_include_new_items_in_filter(self, value : bool) -> None:
        '''Indicates whether including new items to the field in manual filter.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def is_insert_page_breaks_between_items(self) -> bool:
        '''Indicates whether inserting page breaks after each item.
        The default value is false.'''
        raise NotImplementedError()
    
    @is_insert_page_breaks_between_items.setter
    def is_insert_page_breaks_between_items(self, value : bool) -> None:
        '''Indicates whether inserting page breaks after each item.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def show_all_items(self) -> bool:
        '''Indicates whether all items displays in the PivotTable report,
        even if they don\'t contain summary data.
        show items with no data
        The default value is false.'''
        raise NotImplementedError()
    
    @show_all_items.setter
    def show_all_items(self, value : bool) -> None:
        '''Indicates whether all items displays in the PivotTable report,
        even if they don\'t contain summary data.
        show items with no data
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def non_auto_sort_default(self) -> bool:
        '''Indicates whether a sort operation that will be applied to this pivot field is an autosort operation or a simple data sort.'''
        raise NotImplementedError()
    
    @non_auto_sort_default.setter
    def non_auto_sort_default(self, value : bool) -> None:
        '''Indicates whether a sort operation that will be applied to this pivot field is an autosort operation or a simple data sort.'''
        raise NotImplementedError()
    
    @property
    def is_auto_sort(self) -> bool:
        '''Indicates whether the specified PivotTable field is automatically sorted.'''
        raise NotImplementedError()
    
    @is_auto_sort.setter
    def is_auto_sort(self, value : bool) -> None:
        '''Indicates whether the specified PivotTable field is automatically sorted.'''
        raise NotImplementedError()
    
    @property
    def is_ascend_sort(self) -> bool:
        '''Indicates whether the specified PivotTable field is autosorted ascending.'''
        raise NotImplementedError()
    
    @is_ascend_sort.setter
    def is_ascend_sort(self, value : bool) -> None:
        '''Indicates whether the specified PivotTable field is autosorted ascending.'''
        raise NotImplementedError()
    
    @property
    def sort_setting(self) -> aspose.cells.pivot.PivotFieldSortSetting:
        '''Gets all settings of auto sorting'''
        raise NotImplementedError()
    
    @property
    def auto_sort_field(self) -> int:
        '''Represents the index of field which is auto sorted.
        -1 means PivotField itself,others means the position of the data fields.'''
        raise NotImplementedError()
    
    @auto_sort_field.setter
    def auto_sort_field(self, value : int) -> None:
        '''Represents the index of field which is auto sorted.
        -1 means PivotField itself,others means the position of the data fields.'''
        raise NotImplementedError()
    
    @property
    def is_auto_show(self) -> bool:
        '''Indicates whether the specified PivotTable field is automatically shown,only valid for excel 2003.'''
        raise NotImplementedError()
    
    @is_auto_show.setter
    def is_auto_show(self, value : bool) -> None:
        '''Indicates whether the specified PivotTable field is automatically shown,only valid for excel 2003.'''
        raise NotImplementedError()
    
    @property
    def is_ascend_show(self) -> bool:
        '''Indicates whether the specified PivotTable field is autoshown ascending.'''
        raise NotImplementedError()
    
    @is_ascend_show.setter
    def is_ascend_show(self, value : bool) -> None:
        '''Indicates whether the specified PivotTable field is autoshown ascending.'''
        raise NotImplementedError()
    
    @property
    def auto_show_count(self) -> int:
        '''Represent the number of top or bottom items
        that are automatically shown in the specified PivotTable field.'''
        raise NotImplementedError()
    
    @auto_show_count.setter
    def auto_show_count(self, value : int) -> None:
        '''Represent the number of top or bottom items
        that are automatically shown in the specified PivotTable field.'''
        raise NotImplementedError()
    
    @property
    def auto_show_field(self) -> int:
        '''Represents auto show field index. -1 means PivotField itself.
        It should be the index of the data fields.'''
        raise NotImplementedError()
    
    @auto_show_field.setter
    def auto_show_field(self, value : int) -> None:
        '''Represents auto show field index. -1 means PivotField itself.
        It should be the index of the data fields.'''
        raise NotImplementedError()
    
    @property
    def function(self) -> aspose.cells.ConsolidationFunction:
        '''Represents the function used to summarize the PivotTable data field.'''
        raise NotImplementedError()
    
    @function.setter
    def function(self, value : aspose.cells.ConsolidationFunction) -> None:
        '''Represents the function used to summarize the PivotTable data field.'''
        raise NotImplementedError()
    
    @property
    def show_values_setting(self) -> aspose.cells.pivot.PivotShowValuesSetting:
        '''Gets the settings of showing values as when the ShowDataAs calculation is in use.'''
        raise NotImplementedError()
    
    @property
    def data_display_format(self) -> aspose.cells.pivot.PivotFieldDataDisplayFormat:
        '''Represents how to display the values in a data field of the pivot report.'''
        raise NotImplementedError()
    
    @data_display_format.setter
    def data_display_format(self, value : aspose.cells.pivot.PivotFieldDataDisplayFormat) -> None:
        '''Represents how to display the values in a data field of the pivot report.'''
        raise NotImplementedError()
    
    @property
    def base_field_index(self) -> int:
        '''Represents the base field for a custom calculation when the ShowDataAs calculation is in use.'''
        raise NotImplementedError()
    
    @base_field_index.setter
    def base_field_index(self, value : int) -> None:
        '''Represents the base field for a custom calculation when the ShowDataAs calculation is in use.'''
        raise NotImplementedError()
    
    @property
    def base_item_position(self) -> aspose.cells.pivot.PivotItemPosition:
        '''Represents the item in the base field for a custom calculation when the ShowDataAs calculation is in use.
        Valid only for data fields.
        Because PivotItemPosition.Custom is only for read,if you need to set PivotItemPosition.Custom,
        please set PivotField.BaseItemIndex attribute.'''
        raise NotImplementedError()
    
    @base_item_position.setter
    def base_item_position(self, value : aspose.cells.pivot.PivotItemPosition) -> None:
        '''Represents the item in the base field for a custom calculation when the ShowDataAs calculation is in use.
        Valid only for data fields.
        Because PivotItemPosition.Custom is only for read,if you need to set PivotItemPosition.Custom,
        please set PivotField.BaseItemIndex attribute.'''
        raise NotImplementedError()
    
    @property
    def base_item_index(self) -> int:
        '''Represents the item in the base field for a custom calculation when the ShowDataAs calculation is in use.
        Valid only for data fields.'''
        raise NotImplementedError()
    
    @base_item_index.setter
    def base_item_index(self, value : int) -> None:
        '''Represents the item in the base field for a custom calculation when the ShowDataAs calculation is in use.
        Valid only for data fields.'''
        raise NotImplementedError()
    
    @property
    def current_page_item(self) -> int:
        '''Represents the current page item showing for the page field (valid only for page fields).'''
        raise NotImplementedError()
    
    @current_page_item.setter
    def current_page_item(self, value : int) -> None:
        '''Represents the current page item showing for the page field (valid only for page fields).'''
        raise NotImplementedError()
    
    @property
    def number(self) -> int:
        '''Represents the built-in display format of numbers and dates.'''
        raise NotImplementedError()
    
    @number.setter
    def number(self, value : int) -> None:
        '''Represents the built-in display format of numbers and dates.'''
        raise NotImplementedError()
    
    @property
    def insert_blank_row(self) -> bool:
        '''Indicates whether inserting blank line after each item.'''
        raise NotImplementedError()
    
    @insert_blank_row.setter
    def insert_blank_row(self, value : bool) -> None:
        '''Indicates whether inserting blank line after each item.'''
        raise NotImplementedError()
    
    @property
    def show_subtotal_at_top(self) -> bool:
        '''when ShowInOutlineForm is true, then display subtotals at the top of the list of items instead of at the bottom'''
        raise NotImplementedError()
    
    @show_subtotal_at_top.setter
    def show_subtotal_at_top(self, value : bool) -> None:
        '''when ShowInOutlineForm is true, then display subtotals at the top of the list of items instead of at the bottom'''
        raise NotImplementedError()
    
    @property
    def show_in_outline_form(self) -> bool:
        '''Indicates whether layout this field in outline form on the Pivot Table view'''
        raise NotImplementedError()
    
    @show_in_outline_form.setter
    def show_in_outline_form(self, value : bool) -> None:
        '''Indicates whether layout this field in outline form on the Pivot Table view'''
        raise NotImplementedError()
    
    @property
    def number_format(self) -> str:
        '''Represents the custom display format of numbers and dates.'''
        raise NotImplementedError()
    
    @number_format.setter
    def number_format(self, value : str) -> None:
        '''Represents the custom display format of numbers and dates.'''
        raise NotImplementedError()
    
    @property
    def items(self) -> List[str]:
        '''Get all labels of pivot items in this field.'''
        raise NotImplementedError()
    
    @property
    def original_items(self) -> List[str]:
        '''Get the original base items;'''
        raise NotImplementedError()
    
    @property
    def item_count(self) -> int:
        '''Gets the count of the base items in this pivot field.'''
        raise NotImplementedError()
    
    @property
    def show_compact(self) -> bool:
        '''Indicates whether display labels from the next field in the same column on the Pivot Table view'''
        raise NotImplementedError()
    
    @show_compact.setter
    def show_compact(self, value : bool) -> None:
        '''Indicates whether display labels from the next field in the same column on the Pivot Table view'''
        raise NotImplementedError()
    

class PivotFieldCollection:
    '''Represents a collection of all the PivotField objects
    in the PivotTable\'s specific PivotFields type.'''
    
    def get(self, name : str) -> aspose.cells.pivot.PivotField:
        '''Gets the PivotField Object of the specific name.'''
        raise NotImplementedError()
    
    def add_by_base_index(self, base_field_index : int) -> int:
        '''Adds a PivotField Object to the specific type PivotFields.
        
        :param base_field_index: field index in the base PivotFields.
        :returns: the index of  the PivotField Object in this PivotFields.'''
        raise NotImplementedError()
    
    def add(self, pivot_field : aspose.cells.pivot.PivotField) -> int:
        '''Adds a PivotField Object to the specific type PivotFields.
        
        :param pivot_field: a PivotField Object.
        :returns: the index of  the PivotField Object in this PivotFields.'''
        raise NotImplementedError()
    
    def clear(self) -> None:
        '''clear all fields of PivotFieldCollection'''
        raise NotImplementedError()
    
    def move(self, curr_pos : int, dest_pos : int) -> None:
        '''Moves the PivotField from current position to destination position
        
        :param curr_pos: Current position of PivotField based on zero
        :param dest_pos: Destination position of PivotField based on zero'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.pivot.PivotFieldType:
        '''Gets the PivotFields type.'''
        raise NotImplementedError()
    
    @property
    def count(self) -> int:
        '''Gets the count of the pivotFields.'''
        raise NotImplementedError()
    
    def __getitem__(self, key : int) -> aspose.cells.pivot.PivotField:
        '''Gets the PivotField Object at the specific index.'''
        raise NotImplementedError()
    

class PivotFieldGroupSettings:
    '''Represents the group setting of pivot field.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.pivot.PivotFieldGroupType:
        '''Gets the group type of pivot field.'''
        raise NotImplementedError()
    

class PivotFieldSortSetting:
    '''Represents the setting of sorting pivot fields.'''
    
    @property
    def sort_type(self) -> aspose.cells.SortOrder:
        '''Represents the :py:class:`aspose.cells.SortOrder`.'''
        raise NotImplementedError()
    
    @property
    def is_sort_by_labels(self) -> bool:
        '''Indicates whether sorting the field by itself or data field.'''
        raise NotImplementedError()
    
    @property
    def field_index(self) -> int:
        '''Represents the index of the field sorted by.
        -1 means sorting the PivotField by the labels,others means sorting by the data field.'''
        raise NotImplementedError()
    
    @property
    def line_type_sorted_by(self) -> aspose.cells.pivot.PivotLineType:
        '''The pivot line type sorted by.'''
        raise NotImplementedError()
    
    @property
    def is_simple_sort(self) -> bool:
        '''Indicates whether a simple data sort operation will be applied.'''
        raise NotImplementedError()
    
    @property
    def cell(self) -> str:
        '''Sorts by the values in which row or column.'''
        raise NotImplementedError()
    

class PivotFilter:
    '''Represents a PivotFilter in PivotFilter Collection.'''
    
    def get_top_10_value(self) -> aspose.cells.Top10Filter:
        '''Gets top 10 setting of the filter.'''
        raise NotImplementedError()
    
    def get_labels(self) -> List[str]:
        '''Gets labels of the caption filter.'''
        raise NotImplementedError()
    
    def get_number_values(self) -> List[float]:
        '''Gets values of the number filter.'''
        raise NotImplementedError()
    
    def get_date_time_values(self) -> List[datetime]:
        '''Gets values of the number filter.'''
        raise NotImplementedError()
    
    @property
    def use_whole_day(self) -> bool:
        '''Indicates whether uses whole days in its filtering criteria.'''
        raise NotImplementedError()
    
    @use_whole_day.setter
    def use_whole_day(self, value : bool) -> None:
        '''Indicates whether uses whole days in its filtering criteria.'''
        raise NotImplementedError()
    
    @property
    def auto_filter(self) -> aspose.cells.AutoFilter:
        '''Gets the autofilter of the pivot filter.'''
        raise NotImplementedError()
    
    @property
    def filter_type(self) -> aspose.cells.pivot.PivotFilterType:
        '''Gets the autofilter type of the pivot filter.'''
        raise NotImplementedError()
    
    @property
    def field_index(self) -> int:
        '''Gets the index of source field which this pivot filter is applied to.'''
        raise NotImplementedError()
    
    @property
    def filter_category(self) -> aspose.cells.FilterCategory:
        '''Gets the category of this filter.'''
        raise NotImplementedError()
    
    @property
    def value1(self) -> str:
        '''Gets the string value1 of the label pivot filter.'''
        raise NotImplementedError()
    
    @value1.setter
    def value1(self, value : str) -> None:
        '''Gets the string value1 of the label pivot filter.'''
        raise NotImplementedError()
    
    @property
    def value2(self) -> str:
        '''Gets the string value2 of the label pivot filter.'''
        raise NotImplementedError()
    
    @value2.setter
    def value2(self, value : str) -> None:
        '''Gets the string value2 of the label pivot filter.'''
        raise NotImplementedError()
    
    @property
    def measure_fld_index(self) -> int:
        '''Gets the measure field index of the pivot filter.'''
        raise NotImplementedError()
    
    @measure_fld_index.setter
    def measure_fld_index(self, value : int) -> None:
        '''Gets the measure field index of the pivot filter.'''
        raise NotImplementedError()
    
    @property
    def value_field_index(self) -> int:
        '''Gets the index of value field in the value region.'''
        raise NotImplementedError()
    
    @value_field_index.setter
    def value_field_index(self, value : int) -> None:
        '''Gets the index of value field in the value region.'''
        raise NotImplementedError()
    
    @property
    def measure_cube_field_index(self) -> int:
        '''Specifies the index of the measure cube field.
        this property is used only by filters in OLAP pivots and specifies on which measure a value filter should apply.'''
        raise NotImplementedError()
    
    @property
    def member_property_field_index(self) -> int:
        '''Gets the member property field index of the pivot filter.'''
        raise NotImplementedError()
    
    @member_property_field_index.setter
    def member_property_field_index(self, value : int) -> None:
        '''Gets the member property field index of the pivot filter.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the name of the pivot filter.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Gets the name of the pivot filter.'''
        raise NotImplementedError()
    
    @property
    def evaluation_order(self) -> int:
        '''Gets the Evaluation Order of the pivot filter.'''
        raise NotImplementedError()
    
    @evaluation_order.setter
    def evaluation_order(self, value : int) -> None:
        '''Gets the Evaluation Order of the pivot filter.'''
        raise NotImplementedError()
    

class PivotFilterCollection:
    '''Represents a collection of all the PivotFilter objects'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.pivot.PivotFilter]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.pivot.PivotFilter], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.pivot.PivotFilter, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.pivot.PivotFilter, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotFilter) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotFilter, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotFilter, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add(self, field_index : int, type : aspose.cells.pivot.PivotFilterType) -> int:
        '''Adds a PivotFilter Object to the specific type
        
        :param field_index: the PivotField index
        :param type: the PivotFilter type
        :returns: the index of  the PivotFilter Object in this PivotFilterCollection.'''
        raise NotImplementedError()
    
    def add_top_10_filter(self, base_field_index : int, value_field_index : int, type : aspose.cells.pivot.PivotFilterType, is_top : bool, item_count : int) -> aspose.cells.pivot.PivotFilter:
        '''Filters by values of data pivot field.
        
        :param base_field_index: The index of field in the source.
        :param value_field_index: The index of data field  in the data region.
        :param type: The type of filtering data. Only can be Count,Sum and Percent.
        :param is_top: Indicates whether filter from top or bottom
        :param item_count: The item count'''
        raise NotImplementedError()
    
    def add_value_filter(self, base_field_index : int, value_field_index : int, type : aspose.cells.pivot.PivotFilterType, value1 : float, value2 : float) -> aspose.cells.pivot.PivotFilter:
        '''Filters by values of data pivot field.
        
        :param base_field_index: The index of field in the source.
        :param value_field_index: The index of value field in the value region.
        :param type: The type of filtering data.
        :param value1: The value of filter condition
        :param value2: The upper-bound value of between filter condition'''
        raise NotImplementedError()
    
    def add_label_filter(self, base_field_index : int, type : aspose.cells.pivot.PivotFilterType, label1 : str, label2 : str) -> aspose.cells.pivot.PivotFilter:
        '''Filters by captions of row or column pivot field.
        
        :param base_field_index: The index of field in the source.
        :param type: The type of filtering data.
        :param label1: The label of filter condition
        :param label2: The upper-bound label of between filter condition'''
        raise NotImplementedError()
    
    def add_date_filter(self, base_field_index : int, type : aspose.cells.pivot.PivotFilterType, date_time1 : datetime, date_time2 : datetime) -> aspose.cells.pivot.PivotFilter:
        '''Filters by date setting of row or column pivot field.
        
        :param base_field_index: The index of field in the source.
        :param type: The type of filtering data.
        :param date_time1: The date label of filter condition
        :param date_time2: The upper-bound date label of between filter condition'''
        raise NotImplementedError()
    
    def clear_filter(self, field_index : int) -> None:
        '''Clear PivotFilter from the specific PivotField
        
        :param field_index: the PivotField index'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.pivot.PivotFilter) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class PivotFormatCondition:
    
    @overload
    def add_data_area_condition(self, field_name : str) -> None:
        raise NotImplementedError()
    
    @overload
    def add_data_area_condition(self, data_field : aspose.cells.pivot.PivotField) -> None:
        raise NotImplementedError()
    
    @overload
    def add_row_area_condition(self, field_name : str) -> None:
        raise NotImplementedError()
    
    @overload
    def add_row_area_condition(self, row_field : aspose.cells.pivot.PivotField) -> None:
        raise NotImplementedError()
    
    @overload
    def add_column_area_condition(self, field_name : str) -> None:
        raise NotImplementedError()
    
    @overload
    def add_column_area_condition(self, column_field : aspose.cells.pivot.PivotField) -> None:
        raise NotImplementedError()
    
    def set_conditional_areas(self) -> None:
        raise NotImplementedError()
    
    @property
    def scope_type(self) -> aspose.cells.pivot.PivotConditionFormatScopeType:
        raise NotImplementedError()
    
    @scope_type.setter
    def scope_type(self, value : aspose.cells.pivot.PivotConditionFormatScopeType) -> None:
        raise NotImplementedError()
    
    @property
    def rule_type(self) -> aspose.cells.pivot.PivotConditionFormatRuleType:
        raise NotImplementedError()
    
    @rule_type.setter
    def rule_type(self, value : aspose.cells.pivot.PivotConditionFormatRuleType) -> None:
        raise NotImplementedError()
    
    @property
    def format_conditions(self) -> aspose.cells.FormatConditionCollection:
        raise NotImplementedError()
    

class PivotFormatConditionCollection:
    
    @overload
    def copy_to(self, array : List[aspose.cells.pivot.PivotFormatCondition]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.pivot.PivotFormatCondition], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.pivot.PivotFormatCondition, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.pivot.PivotFormatCondition, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotFormatCondition) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotFormatCondition, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotFormatCondition, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add(self) -> int:
        raise NotImplementedError()
    
    def get(self, index : int) -> aspose.cells.pivot.PivotFormatCondition:
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.pivot.PivotFormatCondition) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class PivotItem:
    '''Represents a item in a PivotField report.'''
    
    def move(self, count : int, is_same_parent : bool) -> None:
        '''Moves the item up or down
        
        :param count: The number of moving up or down.
        Move the item up if this is less than zero;
        Move the item down if this is greater than zero.
        :param is_same_parent: Specifying whether moving operation is in the same parent node or not'''
        raise NotImplementedError()
    
    def get_formula(self) -> str:
        '''Gets the formula of this calculated item.
        Only works when this item is calculated item.'''
        raise NotImplementedError()
    
    def get_string_value(self) -> str:
        '''Gets the string value of the pivot item
        If the value is null, it will return ""'''
        raise NotImplementedError()
    
    def get_double_value(self) -> float:
        '''Gets the double value of the pivot item
        If the value is null or not number ,it will return 0'''
        raise NotImplementedError()
    
    def get_date_time_value(self) -> datetime:
        '''Gets the date time value of the pivot item
        If the value is null ,it will return DateTime.MinValue'''
        raise NotImplementedError()
    
    @property
    def is_hidden(self) -> bool:
        '''Gets and Sets whether the pivot item is hidden.'''
        raise NotImplementedError()
    
    @is_hidden.setter
    def is_hidden(self, value : bool) -> None:
        '''Gets and Sets whether the pivot item is hidden.'''
        raise NotImplementedError()
    
    @property
    def position(self) -> int:
        '''Specifying the position index in all the PivotItems,not the PivotItems under the same parent node.'''
        raise NotImplementedError()
    
    @position.setter
    def position(self, value : int) -> None:
        '''Specifying the position index in all the PivotItems,not the PivotItems under the same parent node.'''
        raise NotImplementedError()
    
    @property
    def position_in_same_parent_node(self) -> int:
        '''Specifying the position index in the PivotItems under the same parent node.'''
        raise NotImplementedError()
    
    @position_in_same_parent_node.setter
    def position_in_same_parent_node(self, value : int) -> None:
        '''Specifying the position index in the PivotItems under the same parent node.'''
        raise NotImplementedError()
    
    @property
    def is_hide_detail(self) -> bool:
        '''Gets and sets whether the pivot item hides detail.'''
        raise NotImplementedError()
    
    @is_hide_detail.setter
    def is_hide_detail(self, value : bool) -> None:
        '''Gets and sets whether the pivot item hides detail.'''
        raise NotImplementedError()
    
    @property
    def is_detail_hidden(self) -> bool:
        '''Gets and sets whether the detail of this pivot item is hidden.'''
        raise NotImplementedError()
    
    @is_detail_hidden.setter
    def is_detail_hidden(self, value : bool) -> None:
        '''Gets and sets whether the detail of this pivot item is hidden.'''
        raise NotImplementedError()
    
    @property
    def is_calculated_item(self) -> bool:
        '''Indicates whether this pivot item is a calculated formula item.'''
        raise NotImplementedError()
    
    @property
    def is_formula(self) -> bool:
        '''Indicates whether this pivot item is a calculated formula item.'''
        raise NotImplementedError()
    
    @is_formula.setter
    def is_formula(self, value : bool) -> None:
        '''Indicates whether this pivot item is a calculated formula item.'''
        raise NotImplementedError()
    
    @property
    def is_missing(self) -> bool:
        '''Indicates whether the item is removed from the data source.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> Any:
        '''Gets the value of the pivot item'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the name of the pivot item.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Gets the name of the pivot item.'''
        raise NotImplementedError()
    
    @property
    def index(self) -> int:
        '''Gets the index of the pivot item in cache field.'''
        raise NotImplementedError()
    
    @index.setter
    def index(self, value : int) -> None:
        '''Gets the index of the pivot item in cache field.'''
        raise NotImplementedError()
    

class PivotItemCollection:
    '''Represents all the :py:class:`aspose.cells.pivot.PivotItem` objects in the PivotField.'''
    
    def get(self, item_value : str) -> aspose.cells.pivot.PivotItem:
        '''Gets the :py:class:`aspose.cells.pivot.PivotItem` by the specific name.'''
        raise NotImplementedError()
    
    def changeitems_order(self, source_index : int, dest_index : int) -> None:
        '''Directly changes the orders of the two items.
        
        :param source_index: The current index
        :param dest_index: The dest index'''
        raise NotImplementedError()
    
    def swap_item(self, index1 : int, index2 : int) -> None:
        '''Directly swap two items.'''
        raise NotImplementedError()
    
    @property
    def count(self) -> int:
        '''Gets the count of the pivot items.'''
        raise NotImplementedError()
    
    def __getitem__(self, key : int) -> aspose.cells.pivot.PivotItem:
        '''Gets the PivotItem Object at the specific index.'''
        raise NotImplementedError()
    

class PivotNumbericRangeGroupSettings(PivotFieldGroupSettings):
    '''Represents the numberic range group of the pivot field.'''
    
    @property
    def type(self) -> aspose.cells.pivot.PivotFieldGroupType:
        '''Gets the group type.'''
        raise NotImplementedError()
    
    @property
    def start(self) -> float:
        '''Gets the start number of the group.'''
        raise NotImplementedError()
    
    @property
    def end(self) -> float:
        '''Gets the end number of the group.'''
        raise NotImplementedError()
    
    @property
    def interval(self) -> float:
        '''Gets the interval of the group.'''
        raise NotImplementedError()
    

class PivotPageFields:
    '''Represents the pivot page field items
    if the pivot table data source is consolidation ranges.
    It only can contain up to 4 fields.'''
    
    def __init__(self) -> None:
        '''Represents the pivot page field items.'''
        raise NotImplementedError()
    
    def add_page_field(self, page_items : List[str]) -> None:
        '''Adds a page field.
        
        :param page_items: Page field item label'''
        raise NotImplementedError()
    
    def add_identify(self, range_index : int, page_item_index : List[int]) -> None:
        '''Sets which item label in each page field to use to identify the data range.
        The pageItemIndex.Length must be equal to PageFieldCount, so please add the page field first.
        
        :param range_index: The consolidation data range index.
        :param page_item_index: The page item index in the each page field.
        pageItemIndex[2] = 1 means the second item in the third field to use to identify this range.
        pageItemIndex[1] = -1 means no item in the second field to use to identify this range
        and MS will auto create "blank" item in the second field  to identify this range.'''
        raise NotImplementedError()
    
    @property
    def page_field_count(self) -> int:
        '''Gets the number of page fields.'''
        raise NotImplementedError()
    

class PivotShowValuesSetting:
    '''Represents the settings about showing values as when the ShowDataAs calculation is in use.'''
    
    @property
    def calculation_type(self) -> aspose.cells.pivot.PivotFieldDataDisplayFormat:
        '''Represents how to show values of a data field in the pivot report.'''
        raise NotImplementedError()
    
    @calculation_type.setter
    def calculation_type(self, value : aspose.cells.pivot.PivotFieldDataDisplayFormat) -> None:
        '''Represents how to show values of a data field in the pivot report.'''
        raise NotImplementedError()
    
    @property
    def base_field_index(self) -> int:
        '''Represents the base field for a ShowDataAs calculation when the ShowDataAs calculation is in use.'''
        raise NotImplementedError()
    
    @base_field_index.setter
    def base_field_index(self, value : int) -> None:
        '''Represents the base field for a ShowDataAs calculation when the ShowDataAs calculation is in use.'''
        raise NotImplementedError()
    
    @property
    def base_item_position_type(self) -> aspose.cells.pivot.PivotItemPositionType:
        '''Represents type of the base pivot item in the base field when the ShowDataAs calculation is in use.
        Valid only for data fields.
        Because PivotItemPosition.Custom is only for read,if you need to set PivotItemPosition.Custom,
        please set PivotField.BaseItemIndex attribute.'''
        raise NotImplementedError()
    
    @base_item_position_type.setter
    def base_item_position_type(self, value : aspose.cells.pivot.PivotItemPositionType) -> None:
        '''Represents type of the base pivot item in the base field when the ShowDataAs calculation is in use.
        Valid only for data fields.
        Because PivotItemPosition.Custom is only for read,if you need to set PivotItemPosition.Custom,
        please set PivotField.BaseItemIndex attribute.'''
        raise NotImplementedError()
    
    @property
    def base_item_index(self) -> int:
        '''Represents the custom index of the pivot item in the base field when the ShowDataAs calculation is in use.
        Valid only for data fields.'''
        raise NotImplementedError()
    
    @base_item_index.setter
    def base_item_index(self, value : int) -> None:
        '''Represents the custom index of the pivot item in the base field when the ShowDataAs calculation is in use.
        Valid only for data fields.'''
        raise NotImplementedError()
    

class PivotTable:
    '''Summary description for PivotTable.'''
    
    @overload
    def remove_field(self, field_type : aspose.cells.pivot.PivotFieldType, field_name : str) -> None:
        '''Removes a field from specific field area
        
        :param field_type: The fields area type.
        :param field_name: The name in the base fields.'''
        raise NotImplementedError()
    
    @overload
    def remove_field(self, field_type : aspose.cells.pivot.PivotFieldType, base_field_index : int) -> None:
        '''Removes a field from specific field area
        
        :param field_type: The fields area type.
        :param base_field_index: The field index in the base fields.'''
        raise NotImplementedError()
    
    @overload
    def remove_field(self, field_type : aspose.cells.pivot.PivotFieldType, pivot_field : aspose.cells.pivot.PivotField) -> None:
        '''Remove field from specific field area
        
        :param field_type: the fields area type.
        :param pivot_field: the field in the base fields.'''
        raise NotImplementedError()
    
    @overload
    def add_field_to_area(self, field_type : aspose.cells.pivot.PivotFieldType, field_name : str) -> int:
        '''Adds the field to the specific area.
        
        :param field_type: The fields area type.
        :param field_name: The name in the base fields.
        :returns: The field position in the specific fields.If there is no field named as it, return -1.'''
        raise NotImplementedError()
    
    @overload
    def add_field_to_area(self, field_type : aspose.cells.pivot.PivotFieldType, base_field_index : int) -> int:
        '''Adds the field to the specific area.
        
        :param field_type: The fields area type.
        :param base_field_index: The field index in the base fields.
        :returns: The field position in the specific fields.'''
        raise NotImplementedError()
    
    @overload
    def add_field_to_area(self, field_type : aspose.cells.pivot.PivotFieldType, pivot_field : aspose.cells.pivot.PivotField) -> int:
        '''Adds the field to the specific area.
        
        :param field_type: the fields area type.
        :param pivot_field: the field in the base fields.
        :returns: the field position in the specific fields.'''
        raise NotImplementedError()
    
    @overload
    def add_calculated_field(self, name : str, formula : str, drag_to_data_area : bool) -> None:
        '''Adds a calculated field to pivot field.
        
        :param name: The name of the calculated field
        :param formula: The formula of the calculated field.
        :param drag_to_data_area: True,drag this field to data area immediately'''
        raise NotImplementedError()
    
    @overload
    def add_calculated_field(self, name : str, formula : str) -> None:
        '''Adds a calculated field to pivot field and drag it to data area.
        
        :param name: The name of the calculated field
        :param formula: The formula of the calculated field.'''
        raise NotImplementedError()
    
    @overload
    def move(self, row : int, column : int) -> None:
        '''Moves the PivotTable to a different location in the worksheet.
        
        :param row: row index.
        :param column: column index.'''
        raise NotImplementedError()
    
    @overload
    def move(self, dest_cell_name : str) -> None:
        '''Moves the PivotTable to a different location in the worksheet.
        
        :param dest_cell_name: the dest cell name.'''
        raise NotImplementedError()
    
    @overload
    def move_to(self, row : int, column : int) -> None:
        '''Moves the PivotTable to a different location in the worksheet.
        
        :param row: row index.
        :param column: column index.'''
        raise NotImplementedError()
    
    @overload
    def move_to(self, dest_cell_name : str) -> None:
        '''Moves the PivotTable to a different location in the worksheet.
        
        :param dest_cell_name: the dest cell name.'''
        raise NotImplementedError()
    
    @overload
    def get_source(self) -> List[str]:
        '''Get pivottable\'s source data.'''
        raise NotImplementedError()
    
    @overload
    def get_source(self, is_original : bool) -> List[str]:
        '''Get pivottable\'s source data.
        
        :param is_original: Indicates whether to return original or display data source'''
        raise NotImplementedError()
    
    @overload
    def refresh_data(self) -> aspose.cells.pivot.PivotRefreshState:
        '''Refreshes pivottable\'s data and setting from it\'s data source.'''
        raise NotImplementedError()
    
    @overload
    def refresh_data(self, option : aspose.cells.pivot.PivotTableRefreshOption) -> aspose.cells.pivot.PivotRefreshState:
        '''Refreshes pivottable\'s data and setting from it\'s data source with options.
        
        :param option: The options for refreshing data source of pivot table.'''
        raise NotImplementedError()
    
    @overload
    def calculate_data(self) -> None:
        '''Calculates pivottable\'s data to cells.'''
        raise NotImplementedError()
    
    @overload
    def calculate_data(self, option : aspose.cells.pivot.PivotTableCalculateOption) -> None:
        '''Calculating pivot tables with options'''
        raise NotImplementedError()
    
    @overload
    def format(self, pivot_area : aspose.cells.pivot.PivotArea, style : aspose.cells.Style) -> None:
        '''Formats selected area of the PivotTable.
        
        :param pivot_area: The selected pivot view area.
        :param style: The formatted setting.'''
        raise NotImplementedError()
    
    @overload
    def format(self, ca : aspose.cells.CellArea, style : aspose.cells.Style) -> None:
        '''Formats selected area of the PivotTable.
        
        :param ca: The range of the cells.
        :param style: The style'''
        raise NotImplementedError()
    
    @overload
    def format(self, row : int, column : int, style : aspose.cells.Style) -> None:
        '''Format the cell in the pivottable area
        
        :param row: Row Index of the cell
        :param column: Column index of the cell
        :param style: Style which is to format the cell'''
        raise NotImplementedError()
    
    @overload
    def set_auto_group_field(self, base_field_index : int) -> None:
        '''Sets auto field group by the PivotTable.
        
        :param base_field_index: The row or column field index in the base fields'''
        raise NotImplementedError()
    
    @overload
    def set_auto_group_field(self, pivot_field : aspose.cells.pivot.PivotField) -> None:
        '''Sets auto field group by the PivotTable.
        
        :param pivot_field: The row or column field in the specific fields'''
        raise NotImplementedError()
    
    @overload
    def set_manual_group_field(self, base_field_index : int, start_val : float, end_val : float, group_by_list : List[Any], interval_num : float) -> None:
        '''Sets manual field group by the PivotTable.
        
        :param base_field_index: The row or column field index in the base fields
        :param start_val: Specifies the starting value for numeric grouping.
        :param end_val: Specifies the ending value for numeric grouping.
        :param group_by_list: Specifies the grouping type list. Specified by PivotTableGroupType
        :param interval_num: Specifies the interval number group by  numeric grouping.'''
        raise NotImplementedError()
    
    @overload
    def set_manual_group_field(self, pivot_field : aspose.cells.pivot.PivotField, start_val : float, end_val : float, group_by_list : List[Any], interval_num : float) -> None:
        '''Sets manual field group by the PivotTable.
        
        :param pivot_field: The row or column field in the base fields
        :param start_val: Specifies the starting value for numeric grouping.
        :param end_val: Specifies the ending value for numeric grouping.
        :param group_by_list: Specifies the grouping type list. Specified by PivotTableGroupType
        :param interval_num: Specifies the interval number group by numeric grouping.'''
        raise NotImplementedError()
    
    @overload
    def set_manual_group_field(self, base_field_index : int, start_val : datetime, end_val : datetime, group_by_list : List[Any], interval_num : int) -> None:
        '''Sets manual field group by the PivotTable.
        
        :param base_field_index: The row or column field index in the base fields
        :param start_val: Specifies the starting value for date grouping.
        :param end_val: Specifies the ending value for date grouping.
        :param group_by_list: Specifies the grouping type list. Specified by PivotTableGroupType
        :param interval_num: Specifies the interval number group by in days grouping.The number of days must be positive integer of nonzero'''
        raise NotImplementedError()
    
    @overload
    def set_manual_group_field(self, pivot_field : aspose.cells.pivot.PivotField, start_val : datetime, end_val : datetime, group_by_list : List[Any], interval_num : int) -> None:
        '''Sets manual field group by the PivotTable.
        
        :param pivot_field: The row or column field in the base fields
        :param start_val: Specifies the starting value for date grouping.
        :param end_val: Specifies the ending value for date grouping.
        :param group_by_list: Specifies the grouping type list. Specified by PivotTableGroupType
        :param interval_num: Specifies the interval number group by in days grouping.The number of days must be positive integer of nonzero'''
        raise NotImplementedError()
    
    @overload
    def set_ungroup(self, base_field_index : int) -> None:
        '''Sets ungroup by the PivotTable
        
        :param base_field_index: The row or column field index in the base fields'''
        raise NotImplementedError()
    
    @overload
    def set_ungroup(self, pivot_field : aspose.cells.pivot.PivotField) -> None:
        '''Sets ungroup by the PivotTable
        
        :param pivot_field: The row or column field in the base fields'''
        raise NotImplementedError()
    
    def copy_style(self, pivot_table : aspose.cells.pivot.PivotTable) -> None:
        '''Copies named style from another pivot table.
        
        :param pivot_table: Source pivot table.'''
        raise NotImplementedError()
    
    def show_report_filter_page(self, page_field : aspose.cells.pivot.PivotField) -> None:
        '''Show all the report filter pages according to PivotField, the PivotField must be located in the PageFields.
        
        :param page_field: The PivotField object'''
        raise NotImplementedError()
    
    def show_report_filter_page_by_name(self, field_name : str) -> None:
        '''Show all the report filter pages according to PivotField\'s name, the PivotField must be located in the PageFields.
        
        :param field_name: The name of PivotField'''
        raise NotImplementedError()
    
    def show_report_filter_page_by_index(self, pos_index : int) -> None:
        '''Show all the report filter pages according to the position index in the PageFields
        
        :param pos_index: The position index in the PageFields'''
        raise NotImplementedError()
    
    def get_fields(self, field_type : aspose.cells.pivot.PivotFieldType) -> aspose.cells.pivot.PivotFieldCollection:
        '''Gets the specific pivot field list by the region.
        
        :param field_type: the region type.
        :returns: the specific pivot field collection'''
        raise NotImplementedError()
    
    def fields(self, field_type : aspose.cells.pivot.PivotFieldType) -> aspose.cells.pivot.PivotFieldCollection:
        '''Gets the specific fields by the field type.
        
        :param field_type: the field type.
        :returns: the specific field collection'''
        raise NotImplementedError()
    
    def get_source_data_connections(self) -> List[aspose.cells.externalconnections.ExternalConnection]:
        '''Gets the external connection data sources.'''
        raise NotImplementedError()
    
    def get_names_of_source_data_connections(self) -> List[str]:
        '''Gets the name of external source data connections.'''
        raise NotImplementedError()
    
    def change_data_source(self, source : List[str]) -> None:
        '''Set pivottable\'s source data.'''
        raise NotImplementedError()
    
    def clear_data(self) -> None:
        '''Clear PivotTable\'s data and formatting'''
        raise NotImplementedError()
    
    def calculate_range(self) -> None:
        '''Calculates pivottable\'s range.'''
        raise NotImplementedError()
    
    def format_all(self, style : aspose.cells.Style) -> None:
        '''Format all the cell in the pivottable area
        
        :param style: Style which is to format'''
        raise NotImplementedError()
    
    def format_row(self, row : int, style : aspose.cells.Style) -> None:
        '''Format the row data in the pivottable area
        
        :param row: Row Index of the Row object
        :param style: Style which is to format'''
        raise NotImplementedError()
    
    def select_area(self, ca : aspose.cells.CellArea) -> aspose.cells.pivot.PivotAreaCollection:
        '''Select an area of pivot table view.
        
        :param ca: The cell area.'''
        raise NotImplementedError()
    
    def show_detail(self, row_offset : int, column_offset : int, new_sheet : bool, dest_row : int, dest_column : int) -> None:
        '''Show the detail of one item in the data region to a new Table.
        
        :param row_offset: Offset to the first data row in the data region.
        :param column_offset: Offset to the first data column in the data region.
        :param new_sheet: Show the detail to a new worksheet.
        :param dest_row: The target row.
        :param dest_column: The target column.'''
        raise NotImplementedError()
    
    def get_horizontal_page_breaks(self) -> List[int]:
        '''Gets horizontal page breaks of this pivot table.'''
        raise NotImplementedError()
    
    def get_horizontal_breaks(self) -> List[Any]:
        '''Gets pivot table row index list of horizontal page breaks'''
        raise NotImplementedError()
    
    def show_in_compact_form(self) -> None:
        '''Layouts the PivotTable in compact form.'''
        raise NotImplementedError()
    
    def show_in_outline_form(self) -> None:
        '''Layouts the PivotTable in outline form.'''
        raise NotImplementedError()
    
    def show_in_tabular_form(self) -> None:
        '''Layouts the PivotTable in tabular form.'''
        raise NotImplementedError()
    
    def get_cell_by_display_name(self, display_name : str) -> aspose.cells.Cell:
        '''Gets the :py:class:`aspose.cells.Cell` object by the display name of PivotField.
        
        :param display_name: the DisplayName of PivotField
        :returns: the Cell object'''
        raise NotImplementedError()
    
    def get_children(self) -> List[aspose.cells.pivot.PivotTable]:
        '''Gets the Children Pivot Tables which use this PivotTable data as data source.
        
        :returns: the PivotTable array object'''
        raise NotImplementedError()
    
    @property
    def is_excel_2003_compatible(self) -> bool:
        '''Specifies whether the PivotTable is compatible for Excel2003 when refreshing PivotTable,
        if true, a string must be less than or equal to 255 characters, so if the string is greater than 255 characters,
        it will be truncated. if false, a string will not have the aforementioned restriction.
        The default value is true.'''
        raise NotImplementedError()
    
    @is_excel_2003_compatible.setter
    def is_excel_2003_compatible(self, value : bool) -> None:
        '''Specifies whether the PivotTable is compatible for Excel2003 when refreshing PivotTable,
        if true, a string must be less than or equal to 255 characters, so if the string is greater than 255 characters,
        it will be truncated. if false, a string will not have the aforementioned restriction.
        The default value is true.'''
        raise NotImplementedError()
    
    @property
    def refreshed_by_who(self) -> str:
        '''Gets the name of the last user who refreshed this PivotTable'''
        raise NotImplementedError()
    
    @property
    def refresh_date(self) -> datetime:
        '''Gets the last date time when the PivotTable was refreshed.'''
        raise NotImplementedError()
    
    @property
    def pivot_table_style_name(self) -> str:
        '''Gets and sets the pivottable style name.'''
        raise NotImplementedError()
    
    @pivot_table_style_name.setter
    def pivot_table_style_name(self, value : str) -> None:
        '''Gets and sets the pivottable style name.'''
        raise NotImplementedError()
    
    @property
    def pivot_table_style_type(self) -> aspose.cells.pivot.PivotTableStyleType:
        '''Gets and sets the built-in pivot table style.'''
        raise NotImplementedError()
    
    @pivot_table_style_type.setter
    def pivot_table_style_type(self, value : aspose.cells.pivot.PivotTableStyleType) -> None:
        '''Gets and sets the built-in pivot table style.'''
        raise NotImplementedError()
    
    @property
    def column_fields(self) -> aspose.cells.pivot.PivotFieldCollection:
        '''Returns a PivotFields object that are currently shown as column fields.'''
        raise NotImplementedError()
    
    @property
    def row_fields(self) -> aspose.cells.pivot.PivotFieldCollection:
        '''Returns a PivotFields object that are currently shown as row fields.'''
        raise NotImplementedError()
    
    @property
    def page_fields(self) -> aspose.cells.pivot.PivotFieldCollection:
        '''Returns a PivotFields object that are currently shown as page fields.'''
        raise NotImplementedError()
    
    @property
    def data_fields(self) -> aspose.cells.pivot.PivotFieldCollection:
        '''Gets a PivotField object that represents all the data fields in a PivotTable.
        Read-only.It would be init only when there are two or more data fields in the DataPiovtFiels.
        It only use to add DataPivotField to the PivotTable row/column area . Default is in row area.'''
        raise NotImplementedError()
    
    @property
    def data_field(self) -> aspose.cells.pivot.PivotField:
        '''Gets a :py:class:`aspose.cells.pivot.PivotField` object that represents all the data fields in a PivotTable.
        Read-only.
        It would only be created when there are two or more data fields in the Data region.
        Defaultly it is in row region. You can drag it to the row/column region with PivotTable.AddFieldToArea() method .'''
        raise NotImplementedError()
    
    @property
    def base_fields(self) -> aspose.cells.pivot.PivotFieldCollection:
        '''Returns all base pivot fields in the PivotTable.'''
        raise NotImplementedError()
    
    @property
    def pivot_filters(self) -> aspose.cells.pivot.PivotFilterCollection:
        '''Returns all filters of pivot fields in the pivot table.'''
        raise NotImplementedError()
    
    @property
    def column_range(self) -> aspose.cells.CellArea:
        '''Returns a CellArea object that represents the range
        that contains the column area in the PivotTable report. Read-only.'''
        raise NotImplementedError()
    
    @property
    def row_range(self) -> aspose.cells.CellArea:
        '''Returns a CellArea object that represents the range
        that contains the row area in the PivotTable report. Read-only.'''
        raise NotImplementedError()
    
    @property
    def data_body_range(self) -> aspose.cells.CellArea:
        '''Returns a :py:class:`aspose.cells.CellArea` object that represents the range that contains the data area
        in the list between the header row and the insert row. Read-only.'''
        raise NotImplementedError()
    
    @property
    def table_range1(self) -> aspose.cells.CellArea:
        '''Returns a CellArea object that represents the range containing the entire PivotTable report,
        but doesn\'t include page fields. Read-only.'''
        raise NotImplementedError()
    
    @property
    def table_range2(self) -> aspose.cells.CellArea:
        '''Returns a CellArea object that represents the range containing the entire PivotTable report,
        includes page fields. Read-only.'''
        raise NotImplementedError()
    
    @property
    def is_grid_drop_zones(self) -> bool:
        '''Indicates whether the PivotTable report displays classic pivottable layout.
        (enables dragging fields in the grid)'''
        raise NotImplementedError()
    
    @is_grid_drop_zones.setter
    def is_grid_drop_zones(self, value : bool) -> None:
        '''Indicates whether the PivotTable report displays classic pivottable layout.
        (enables dragging fields in the grid)'''
        raise NotImplementedError()
    
    @property
    def show_column_grand_totals(self) -> bool:
        '''Indicates whether to show grand totals for columns of this pivot table.'''
        raise NotImplementedError()
    
    @show_column_grand_totals.setter
    def show_column_grand_totals(self, value : bool) -> None:
        '''Indicates whether to show grand totals for columns of this pivot table.'''
        raise NotImplementedError()
    
    @property
    def show_row_grand_totals(self) -> bool:
        '''Indicates whether to show grand totals for rows of the pivot table.'''
        raise NotImplementedError()
    
    @show_row_grand_totals.setter
    def show_row_grand_totals(self, value : bool) -> None:
        '''Indicates whether to show grand totals for rows of the pivot table.'''
        raise NotImplementedError()
    
    @property
    def column_grand(self) -> bool:
        '''Indicates whether the PivotTable report shows grand totals for columns.'''
        raise NotImplementedError()
    
    @column_grand.setter
    def column_grand(self, value : bool) -> None:
        '''Indicates whether the PivotTable report shows grand totals for columns.'''
        raise NotImplementedError()
    
    @property
    def row_grand(self) -> bool:
        '''Indicates whether to show grand totals for rows of this pivot table.'''
        raise NotImplementedError()
    
    @row_grand.setter
    def row_grand(self, value : bool) -> None:
        '''Indicates whether to show grand totals for rows of this pivot table.'''
        raise NotImplementedError()
    
    @property
    def display_null_string(self) -> bool:
        '''Indicates whether the PivotTable report displays a custom string if the value is null.'''
        raise NotImplementedError()
    
    @display_null_string.setter
    def display_null_string(self, value : bool) -> None:
        '''Indicates whether the PivotTable report displays a custom string if the value is null.'''
        raise NotImplementedError()
    
    @property
    def null_string(self) -> str:
        '''Gets the string displayed in cells that contain null values
        when the DisplayNullString property is true.The default value is an empty string.'''
        raise NotImplementedError()
    
    @null_string.setter
    def null_string(self, value : str) -> None:
        '''Gets the string displayed in cells that contain null values
        when the DisplayNullString property is true.The default value is an empty string.'''
        raise NotImplementedError()
    
    @property
    def display_error_string(self) -> bool:
        '''Indicates whether the PivotTable report displays a custom string in cells that contain errors.'''
        raise NotImplementedError()
    
    @display_error_string.setter
    def display_error_string(self, value : bool) -> None:
        '''Indicates whether the PivotTable report displays a custom string in cells that contain errors.'''
        raise NotImplementedError()
    
    @property
    def data_field_header_name(self) -> str:
        '''Gets and sets the name of the value area field header in the PivotTable.'''
        raise NotImplementedError()
    
    @data_field_header_name.setter
    def data_field_header_name(self, value : str) -> None:
        '''Gets and sets the name of the value area field header in the PivotTable.'''
        raise NotImplementedError()
    
    @property
    def error_string(self) -> str:
        '''Gets the string displayed in cells that contain errors
        when the DisplayErrorString property is true.The default value is an empty string.'''
        raise NotImplementedError()
    
    @error_string.setter
    def error_string(self, value : str) -> None:
        '''Gets the string displayed in cells that contain errors
        when the DisplayErrorString property is true.The default value is an empty string.'''
        raise NotImplementedError()
    
    @property
    def is_auto_format(self) -> bool:
        '''Indicates whether the PivotTable report is automatically formatted.
        Checkbox "autoformat table " which is in pivottable option for Excel 2003'''
        raise NotImplementedError()
    
    @is_auto_format.setter
    def is_auto_format(self, value : bool) -> None:
        '''Indicates whether the PivotTable report is automatically formatted.
        Checkbox "autoformat table " which is in pivottable option for Excel 2003'''
        raise NotImplementedError()
    
    @property
    def autofit_column_width_on_update(self) -> bool:
        '''Indicates whether autofitting column width on update'''
        raise NotImplementedError()
    
    @autofit_column_width_on_update.setter
    def autofit_column_width_on_update(self, value : bool) -> None:
        '''Indicates whether autofitting column width on update'''
        raise NotImplementedError()
    
    @property
    def auto_format_type(self) -> aspose.cells.pivot.PivotTableAutoFormatType:
        '''Gets and sets the auto format type of PivotTable.'''
        raise NotImplementedError()
    
    @auto_format_type.setter
    def auto_format_type(self, value : aspose.cells.pivot.PivotTableAutoFormatType) -> None:
        '''Gets and sets the auto format type of PivotTable.'''
        raise NotImplementedError()
    
    @property
    def has_blank_rows(self) -> bool:
        '''Indicates whether to add blank rows.
        This property only applies for the PivotTable auto format types which needs to add blank rows.'''
        raise NotImplementedError()
    
    @has_blank_rows.setter
    def has_blank_rows(self, value : bool) -> None:
        '''Indicates whether to add blank rows.
        This property only applies for the PivotTable auto format types which needs to add blank rows.'''
        raise NotImplementedError()
    
    @property
    def merge_labels(self) -> bool:
        '''True if the specified PivotTable report\'s outer-row item, column item, subtotal, and grand total labels use merged cells.'''
        raise NotImplementedError()
    
    @merge_labels.setter
    def merge_labels(self, value : bool) -> None:
        '''True if the specified PivotTable report\'s outer-row item, column item, subtotal, and grand total labels use merged cells.'''
        raise NotImplementedError()
    
    @property
    def preserve_formatting(self) -> bool:
        '''Indicates whether formatting is preserved when the PivotTable is refreshed or recalculated.'''
        raise NotImplementedError()
    
    @preserve_formatting.setter
    def preserve_formatting(self, value : bool) -> None:
        '''Indicates whether formatting is preserved when the PivotTable is refreshed or recalculated.'''
        raise NotImplementedError()
    
    @property
    def show_drill(self) -> bool:
        '''Gets and sets whether showing expand/collapse buttons.'''
        raise NotImplementedError()
    
    @show_drill.setter
    def show_drill(self, value : bool) -> None:
        '''Gets and sets whether showing expand/collapse buttons.'''
        raise NotImplementedError()
    
    @property
    def enable_drilldown(self) -> bool:
        '''Gets whether drilldown is enabled.'''
        raise NotImplementedError()
    
    @enable_drilldown.setter
    def enable_drilldown(self, value : bool) -> None:
        '''Gets whether drilldown is enabled.'''
        raise NotImplementedError()
    
    @property
    def enable_field_dialog(self) -> bool:
        '''Indicates whether the PivotTable Field dialog box is available
        when the user double-clicks the PivotTable field.'''
        raise NotImplementedError()
    
    @enable_field_dialog.setter
    def enable_field_dialog(self, value : bool) -> None:
        '''Indicates whether the PivotTable Field dialog box is available
        when the user double-clicks the PivotTable field.'''
        raise NotImplementedError()
    
    @property
    def enable_field_list(self) -> bool:
        '''Indicates whether the field list for the PivotTable is available on the view of Excel.'''
        raise NotImplementedError()
    
    @enable_field_list.setter
    def enable_field_list(self, value : bool) -> None:
        '''Indicates whether the field list for the PivotTable is available on the view of Excel.'''
        raise NotImplementedError()
    
    @property
    def enable_wizard(self) -> bool:
        '''Indicates whether the PivotTable Wizard is available.'''
        raise NotImplementedError()
    
    @enable_wizard.setter
    def enable_wizard(self, value : bool) -> None:
        '''Indicates whether the PivotTable Wizard is available.'''
        raise NotImplementedError()
    
    @property
    def subtotal_hidden_page_items(self) -> bool:
        '''Indicates whether hidden page field items in the PivotTable report
        are included in row and column subtotals, block totals, and grand totals.
        The default value is False.'''
        raise NotImplementedError()
    
    @subtotal_hidden_page_items.setter
    def subtotal_hidden_page_items(self, value : bool) -> None:
        '''Indicates whether hidden page field items in the PivotTable report
        are included in row and column subtotals, block totals, and grand totals.
        The default value is False.'''
        raise NotImplementedError()
    
    @property
    def grand_total_name(self) -> str:
        '''Returns the label that is displayed in the grand total column or row heading.
        The default value is the string "Grand Total".'''
        raise NotImplementedError()
    
    @grand_total_name.setter
    def grand_total_name(self, value : str) -> None:
        '''Returns the label that is displayed in the grand total column or row heading.
        The default value is the string "Grand Total".'''
        raise NotImplementedError()
    
    @property
    def manual_update(self) -> bool:
        '''Indicates whether the PivotTable report is recalculated only at the user\'s request.'''
        raise NotImplementedError()
    
    @manual_update.setter
    def manual_update(self, value : bool) -> None:
        '''Indicates whether the PivotTable report is recalculated only at the user\'s request.'''
        raise NotImplementedError()
    
    @property
    def is_multiple_field_filters(self) -> bool:
        '''Specifies a boolean value that indicates whether the fields of a PivotTable can have multiple filters set on them.'''
        raise NotImplementedError()
    
    @is_multiple_field_filters.setter
    def is_multiple_field_filters(self, value : bool) -> None:
        '''Specifies a boolean value that indicates whether the fields of a PivotTable can have multiple filters set on them.'''
        raise NotImplementedError()
    
    @property
    def allow_multiple_filters_per_field(self) -> bool:
        '''Specifies a boolean value that indicates whether the fields of a PivotTable can have multiple filters set on them.'''
        raise NotImplementedError()
    
    @allow_multiple_filters_per_field.setter
    def allow_multiple_filters_per_field(self, value : bool) -> None:
        '''Specifies a boolean value that indicates whether the fields of a PivotTable can have multiple filters set on them.'''
        raise NotImplementedError()
    
    @property
    def missing_items_limit(self) -> aspose.cells.pivot.PivotMissingItemLimitType:
        '''Specifies a boolean value that indicates whether the fields of a PivotTable can have multiple filters set on them.'''
        raise NotImplementedError()
    
    @missing_items_limit.setter
    def missing_items_limit(self, value : aspose.cells.pivot.PivotMissingItemLimitType) -> None:
        '''Specifies a boolean value that indicates whether the fields of a PivotTable can have multiple filters set on them.'''
        raise NotImplementedError()
    
    @property
    def enable_data_value_editing(self) -> bool:
        '''Specifies a boolean value that indicates whether the user is allowed to edit the cells in the data area of the pivottable.
        Enable cell editing in the values area'''
        raise NotImplementedError()
    
    @enable_data_value_editing.setter
    def enable_data_value_editing(self, value : bool) -> None:
        '''Specifies a boolean value that indicates whether the user is allowed to edit the cells in the data area of the pivottable.
        Enable cell editing in the values area'''
        raise NotImplementedError()
    
    @property
    def show_data_tips(self) -> bool:
        '''Specifies a boolean value that indicates whether tooltips should be displayed for PivotTable data cells.'''
        raise NotImplementedError()
    
    @show_data_tips.setter
    def show_data_tips(self, value : bool) -> None:
        '''Specifies a boolean value that indicates whether tooltips should be displayed for PivotTable data cells.'''
        raise NotImplementedError()
    
    @property
    def show_member_property_tips(self) -> bool:
        '''Specifies a boolean value that indicates whether member property information should be omitted from PivotTable tooltips.'''
        raise NotImplementedError()
    
    @show_member_property_tips.setter
    def show_member_property_tips(self, value : bool) -> None:
        '''Specifies a boolean value that indicates whether member property information should be omitted from PivotTable tooltips.'''
        raise NotImplementedError()
    
    @property
    def show_values_row(self) -> bool:
        '''Indicates whether showing values row.'''
        raise NotImplementedError()
    
    @show_values_row.setter
    def show_values_row(self, value : bool) -> None:
        '''Indicates whether showing values row.'''
        raise NotImplementedError()
    
    @property
    def show_empty_col(self) -> bool:
        '''Indicates whether to include empty columns in the table'''
        raise NotImplementedError()
    
    @show_empty_col.setter
    def show_empty_col(self, value : bool) -> None:
        '''Indicates whether to include empty columns in the table'''
        raise NotImplementedError()
    
    @property
    def show_empty_row(self) -> bool:
        '''Indicates whether to include empty rows in the table.'''
        raise NotImplementedError()
    
    @show_empty_row.setter
    def show_empty_row(self, value : bool) -> None:
        '''Indicates whether to include empty rows in the table.'''
        raise NotImplementedError()
    
    @property
    def field_list_sort_ascending(self) -> bool:
        '''Indicates whether fields in the PivotTable are sorted in non-default order in the field list.'''
        raise NotImplementedError()
    
    @field_list_sort_ascending.setter
    def field_list_sort_ascending(self, value : bool) -> None:
        '''Indicates whether fields in the PivotTable are sorted in non-default order in the field list.'''
        raise NotImplementedError()
    
    @property
    def print_drill(self) -> bool:
        '''Specifies a boolean value that indicates whether drill indicators should be printed.
        print expand/collapse buttons when displayed on pivottable.'''
        raise NotImplementedError()
    
    @print_drill.setter
    def print_drill(self, value : bool) -> None:
        '''Specifies a boolean value that indicates whether drill indicators should be printed.
        print expand/collapse buttons when displayed on pivottable.'''
        raise NotImplementedError()
    
    @property
    def alt_text_title(self) -> str:
        '''Gets and sets the title of the alter text.'''
        raise NotImplementedError()
    
    @alt_text_title.setter
    def alt_text_title(self, value : str) -> None:
        '''Gets and sets the title of the alter text.'''
        raise NotImplementedError()
    
    @property
    def alt_text_description(self) -> str:
        '''Gets the description of the alt text.'''
        raise NotImplementedError()
    
    @alt_text_description.setter
    def alt_text_description(self, value : str) -> None:
        '''Gets the description of the alt text.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the name of the PivotTable'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Gets the name of the PivotTable'''
        raise NotImplementedError()
    
    @property
    def column_header_caption(self) -> str:
        '''Gets the Column Header Caption of the PivotTable.'''
        raise NotImplementedError()
    
    @column_header_caption.setter
    def column_header_caption(self, value : str) -> None:
        '''Gets the Column Header Caption of the PivotTable.'''
        raise NotImplementedError()
    
    @property
    def indent(self) -> int:
        '''Specifies the indentation increment for compact axis and can be used to set the Report Layout to Compact Form.'''
        raise NotImplementedError()
    
    @indent.setter
    def indent(self, value : int) -> None:
        '''Specifies the indentation increment for compact axis and can be used to set the Report Layout to Compact Form.'''
        raise NotImplementedError()
    
    @property
    def row_header_caption(self) -> str:
        '''Gets the Row Header Caption of the PivotTable.'''
        raise NotImplementedError()
    
    @row_header_caption.setter
    def row_header_caption(self, value : str) -> None:
        '''Gets the Row Header Caption of the PivotTable.'''
        raise NotImplementedError()
    
    @property
    def show_row_header_caption(self) -> bool:
        '''Indicates whether row header caption is shown in the PivotTable report
        Indicates whether Display field captions and filter drop downs'''
        raise NotImplementedError()
    
    @show_row_header_caption.setter
    def show_row_header_caption(self, value : bool) -> None:
        '''Indicates whether row header caption is shown in the PivotTable report
        Indicates whether Display field captions and filter drop downs'''
        raise NotImplementedError()
    
    @property
    def custom_list_sort(self) -> bool:
        '''Indicates whether consider built-in custom list when sort data'''
        raise NotImplementedError()
    
    @custom_list_sort.setter
    def custom_list_sort(self, value : bool) -> None:
        '''Indicates whether consider built-in custom list when sort data'''
        raise NotImplementedError()
    
    @property
    def pivot_format_conditions(self) -> aspose.cells.pivot.PivotFormatConditionCollection:
        '''Gets the Format Conditions of the pivot table.'''
        raise NotImplementedError()
    
    @property
    def conditional_formats(self) -> aspose.cells.pivot.PivotConditionalFormatCollection:
        '''Gets the conditional formats of the pivot table.'''
        raise NotImplementedError()
    
    @property
    def page_field_order(self) -> aspose.cells.PrintOrderType:
        '''Gets and sets the order in which page fields are added to the PivotTable report\'s layout.'''
        raise NotImplementedError()
    
    @page_field_order.setter
    def page_field_order(self, value : aspose.cells.PrintOrderType) -> None:
        '''Gets and sets the order in which page fields are added to the PivotTable report\'s layout.'''
        raise NotImplementedError()
    
    @property
    def page_field_wrap_count(self) -> int:
        '''Gets the number of page fields in each column or row in the PivotTable report.'''
        raise NotImplementedError()
    
    @page_field_wrap_count.setter
    def page_field_wrap_count(self, value : int) -> None:
        '''Gets the number of page fields in each column or row in the PivotTable report.'''
        raise NotImplementedError()
    
    @property
    def tag(self) -> str:
        '''Gets a string saved with the PivotTable report.'''
        raise NotImplementedError()
    
    @tag.setter
    def tag(self, value : str) -> None:
        '''Gets a string saved with the PivotTable report.'''
        raise NotImplementedError()
    
    @property
    def save_data(self) -> bool:
        '''Indicates whether data for the PivotTable report is saved with the workbook.'''
        raise NotImplementedError()
    
    @save_data.setter
    def save_data(self, value : bool) -> None:
        '''Indicates whether data for the PivotTable report is saved with the workbook.'''
        raise NotImplementedError()
    
    @property
    def refresh_data_on_opening_file(self) -> bool:
        '''Indicates whether Refresh Data when Opening File.'''
        raise NotImplementedError()
    
    @refresh_data_on_opening_file.setter
    def refresh_data_on_opening_file(self, value : bool) -> None:
        '''Indicates whether Refresh Data when Opening File.'''
        raise NotImplementedError()
    
    @property
    def refresh_data_flag(self) -> bool:
        '''Indicates whether Refreshing Data or not.'''
        raise NotImplementedError()
    
    @refresh_data_flag.setter
    def refresh_data_flag(self, value : bool) -> None:
        '''Indicates whether Refreshing Data or not.'''
        raise NotImplementedError()
    
    @property
    def source_type(self) -> aspose.cells.pivot.PivotTableSourceType:
        '''Gets the data source type of the pivot table.'''
        raise NotImplementedError()
    
    @property
    def external_connection_data_source(self) -> aspose.cells.externalconnections.ExternalConnection:
        '''Gets the external connection data source.'''
        raise NotImplementedError()
    
    @property
    def data_source(self) -> List[str]:
        '''Gets and sets the data source of the pivot table.'''
        raise NotImplementedError()
    
    @data_source.setter
    def data_source(self, value : List[str]) -> None:
        '''Gets and sets the data source of the pivot table.'''
        raise NotImplementedError()
    
    @property
    def pivot_formats(self) -> aspose.cells.pivot.PivotTableFormatCollection:
        '''Gets the collection of formats applied to PivotTable.'''
        raise NotImplementedError()
    
    @property
    def item_print_titles(self) -> bool:
        '''Indicates whether PivotItem names should be repeated at the top of each printed page.'''
        raise NotImplementedError()
    
    @item_print_titles.setter
    def item_print_titles(self, value : bool) -> None:
        '''Indicates whether PivotItem names should be repeated at the top of each printed page.'''
        raise NotImplementedError()
    
    @property
    def repeat_items_on_each_printed_page(self) -> bool:
        '''Indicates whether pivot item captions on the row area are repeated on each printed page for pivot fields in tabular form.'''
        raise NotImplementedError()
    
    @repeat_items_on_each_printed_page.setter
    def repeat_items_on_each_printed_page(self, value : bool) -> None:
        '''Indicates whether pivot item captions on the row area are repeated on each printed page for pivot fields in tabular form.'''
        raise NotImplementedError()
    
    @property
    def print_titles(self) -> bool:
        '''Indicates whether the print titles for the worksheet are set based
        on the PivotTable report. The default value is false.'''
        raise NotImplementedError()
    
    @print_titles.setter
    def print_titles(self, value : bool) -> None:
        '''Indicates whether the print titles for the worksheet are set based
        on the PivotTable report. The default value is false.'''
        raise NotImplementedError()
    
    @property
    def display_immediate_items(self) -> bool:
        '''Indicates whether items in the row and column areas are visible
        when the data area of the PivotTable is empty. The default value is true.'''
        raise NotImplementedError()
    
    @display_immediate_items.setter
    def display_immediate_items(self, value : bool) -> None:
        '''Indicates whether items in the row and column areas are visible
        when the data area of the PivotTable is empty. The default value is true.'''
        raise NotImplementedError()
    
    @property
    def is_selected(self) -> bool:
        '''Indicates whether this PivotTable is selected.'''
        raise NotImplementedError()
    
    @is_selected.setter
    def is_selected(self, value : bool) -> None:
        '''Indicates whether this PivotTable is selected.'''
        raise NotImplementedError()
    
    @property
    def show_pivot_style_row_header(self) -> bool:
        '''Indicates whether the row header in the pivot table should have the style applied.'''
        raise NotImplementedError()
    
    @show_pivot_style_row_header.setter
    def show_pivot_style_row_header(self, value : bool) -> None:
        '''Indicates whether the row header in the pivot table should have the style applied.'''
        raise NotImplementedError()
    
    @property
    def show_pivot_style_column_header(self) -> bool:
        '''Indicates whether the column header in the pivot table should have the style applied.'''
        raise NotImplementedError()
    
    @show_pivot_style_column_header.setter
    def show_pivot_style_column_header(self, value : bool) -> None:
        '''Indicates whether the column header in the pivot table should have the style applied.'''
        raise NotImplementedError()
    
    @property
    def show_pivot_style_row_stripes(self) -> bool:
        '''Indicates whether row stripe formatting is applied.'''
        raise NotImplementedError()
    
    @show_pivot_style_row_stripes.setter
    def show_pivot_style_row_stripes(self, value : bool) -> None:
        '''Indicates whether row stripe formatting is applied.'''
        raise NotImplementedError()
    
    @property
    def show_pivot_style_column_stripes(self) -> bool:
        '''Indicates whether stripe formatting is applied for column.'''
        raise NotImplementedError()
    
    @show_pivot_style_column_stripes.setter
    def show_pivot_style_column_stripes(self, value : bool) -> None:
        '''Indicates whether stripe formatting is applied for column.'''
        raise NotImplementedError()
    
    @property
    def show_pivot_style_last_column(self) -> bool:
        '''Indicates whether the column formatting is applied.'''
        raise NotImplementedError()
    
    @show_pivot_style_last_column.setter
    def show_pivot_style_last_column(self, value : bool) -> None:
        '''Indicates whether the column formatting is applied.'''
        raise NotImplementedError()
    

class PivotTableCalculateOption:
    '''Rerepsents the options of calcuating the pivot table.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def refresh_data(self) -> bool:
        '''Indicates whether refreshing data source of the pivottable.'''
        raise NotImplementedError()
    
    @refresh_data.setter
    def refresh_data(self, value : bool) -> None:
        '''Indicates whether refreshing data source of the pivottable.'''
        raise NotImplementedError()
    
    @property
    def refresh_charts(self) -> bool:
        '''Indicates whether refreshing charts are based on this pivot table.'''
        raise NotImplementedError()
    
    @refresh_charts.setter
    def refresh_charts(self, value : bool) -> None:
        '''Indicates whether refreshing charts are based on this pivot table.'''
        raise NotImplementedError()
    
    @property
    def reserve_missing_pivot_item_type(self) -> aspose.cells.pivot.ReserveMissingPivotItemType:
        '''Represents how to reserve missing pivot items.'''
        raise NotImplementedError()
    
    @reserve_missing_pivot_item_type.setter
    def reserve_missing_pivot_item_type(self, value : aspose.cells.pivot.ReserveMissingPivotItemType) -> None:
        '''Represents how to reserve missing pivot items.'''
        raise NotImplementedError()
    

class PivotTableCollection:
    '''Represents the collection of all the PivotTable objects on the specified worksheet.'''
    
    @overload
    def add(self, source_data : str, dest_cell_name : str, table_name : str) -> int:
        '''Adds a new PivotTable.
        
        :param source_data: The data for the new PivotTable cache.
        :param dest_cell_name: The cell in the upper-left corner of the PivotTable report\'s destination range.
        :param table_name: The name of the new PivotTable report.
        :returns: The new added cache index.'''
        raise NotImplementedError()
    
    @overload
    def add(self, source_data : str, dest_cell_name : str, table_name : str, use_same_source : bool) -> int:
        '''Adds a new PivotTable.
        
        :param source_data: The data for the new PivotTable cache.
        :param dest_cell_name: The cell in the upper-left corner of the PivotTable report\'s destination range.
        :param table_name: The name of the new PivotTable report.
        :param use_same_source: Indicates whether using same data source when another existing pivot table has used this data source.
        If the property is true, it will save memory.
        :returns: The new added cache index.'''
        raise NotImplementedError()
    
    @overload
    def add(self, source_data : str, row : int, column : int, table_name : str) -> int:
        '''Adds a new PivotTable.
        
        :param source_data: The data cell range for the new PivotTable.Example : Sheet1!A1:C8
        :param row: Row index of the cell in the upper-left corner of the PivotTable report\'s destination range.
        :param column: Column index of the cell in the upper-left corner of the PivotTable report\'s destination range.
        :param table_name: The name of the new PivotTable report.
        :returns: The new added cache index.'''
        raise NotImplementedError()
    
    @overload
    def add(self, source_data : str, row : int, column : int, table_name : str, use_same_source : bool) -> int:
        '''Adds a new PivotTable.
        
        :param source_data: The data cell range for the new PivotTable.Example : Sheet1!A1:C8
        :param row: Row index of the cell in the upper-left corner of the PivotTable report\'s destination range.
        :param column: Column index of the cell in the upper-left corner of the PivotTable report\'s destination range.
        :param table_name: The name of the new PivotTable report.
        :param use_same_source: Indicates whether using same data source when another existing pivot table has used this data source.
        If the property is true, it will save memory.
        :returns: The new added cache index.'''
        raise NotImplementedError()
    
    @overload
    def add(self, source_data : str, row : int, column : int, table_name : str, use_same_source : bool, is_xls_classic : bool) -> int:
        '''Adds a new PivotTable.
        
        :param source_data: The data cell range for the new PivotTable.Example : Sheet1!A1:C8
        :param row: Row index of the cell in the upper-left corner of the PivotTable report\'s destination range.
        :param column: Column index of the cell in the upper-left corner of the PivotTable report\'s destination range.
        :param table_name: The name of the new PivotTable report.
        :param use_same_source: Indicates whether using same data source when another existing pivot table has used this data source.
        If the property is true, it will save memory.
        :param is_xls_classic: Indicates whether add classic pivot table of Excel 97-2003.
        :returns: The new added cache index.'''
        raise NotImplementedError()
    
    @overload
    def add(self, source_data : str, cell : str, table_name : str, use_same_source : bool, is_xls_classic : bool) -> int:
        '''Adds a new PivotTable.
        
        :param source_data: The data cell range for the new PivotTable.Example : Sheet1!A1:C8
        :param cell: The cell in the upper-left corner of the PivotTable report\'s destination range.
        :param table_name: The name of the new PivotTable report.
        :param use_same_source: Indicates whether using same data source when another existing pivot table has used this data source.
        If the property is true, it will save memory.
        :param is_xls_classic: Indicates whether add classic pivot table of Excel 97-2003.
        :returns: The new added cache index.'''
        raise NotImplementedError()
    
    @overload
    def add(self, pivot_table : aspose.cells.pivot.PivotTable, dest_cell_name : str, table_name : str) -> int:
        '''Adds a new PivotTable based on another PivotTable.
        
        :param pivot_table: The source pivotTable.
        :param dest_cell_name: The cell in the upper-left corner of the PivotTable report\'s destination range.
        :param table_name: The name of the new PivotTable report.
        :returns: The new added PivotTable index.'''
        raise NotImplementedError()
    
    @overload
    def add(self, pivot_table : aspose.cells.pivot.PivotTable, row : int, column : int, table_name : str) -> int:
        '''Adds a new PivotTable based on another PivotTable.
        
        :param pivot_table: The source pivotTable.
        :param row: Row index of the cell in the upper-left corner of the PivotTable report\'s destination range.
        :param column: Column index of the cell in the upper-left corner of the PivotTable report\'s destination range.
        :param table_name: The name of the new PivotTable report.
        :returns: The new added PivotTable index.'''
        raise NotImplementedError()
    
    @overload
    def add(self, source_data : List[str], is_auto_page : bool, page_fields : aspose.cells.pivot.PivotPageFields, dest_cell_name : str, table_name : str) -> int:
        '''Adds a new PivotTable Object to the collection with multiple consolidation ranges as data source.
        
        :param source_data: The multiple consolidation ranges,such as {"Sheet1!A1:C8","Sheet2!A1:B8"}
        :param is_auto_page: Whether auto create a single page field.
        If true,the following param pageFields will be ignored.
        :param page_fields: The pivot page field items.
        :param dest_cell_name: destCellName The name of the new PivotTable report.
        :param table_name: the name of the new PivotTable report.
        :returns: The new added PivotTable index.'''
        raise NotImplementedError()
    
    @overload
    def add(self, source_data : List[str], is_auto_page : bool, page_fields : aspose.cells.pivot.PivotPageFields, row : int, column : int, table_name : str) -> int:
        '''Adds a new PivotTable Object to the collection with multiple consolidation ranges as data source.
        
        :param source_data: The multiple consolidation ranges,such as {"Sheet1!A1:C8","Sheet2!A1:B8"}
        :param is_auto_page: Whether auto create a single page field.
        If true,the following param pageFields will be ignored
        :param page_fields: The pivot page field items.
        :param row: Row index of the cell in the upper-left corner of the PivotTable report\'s destination range.
        :param column: Column index of the cell in the upper-left corner of the PivotTable report\'s destination range.
        :param table_name: The name of the new PivotTable report.
        :returns: The new added PivotTable index.'''
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.pivot.PivotTable]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.pivot.PivotTable], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.pivot.PivotTable, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.pivot.PivotTable, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotTable) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotTable, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotTable, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def get(self, name : str) -> aspose.cells.pivot.PivotTable:
        '''Gets the PivotTable report by pivottable\'s name.'''
        raise NotImplementedError()
    
    def remove_pivot_table(self, pivot_table : aspose.cells.pivot.PivotTable) -> None:
        '''Deletes the specified PivotTable and delete the PivotTable data
        
        :param pivot_table: PivotTable object'''
        raise NotImplementedError()
    
    def remove_pivot_table_data(self, pivot_table : aspose.cells.pivot.PivotTable, keep_data : bool) -> None:
        '''Deletes the specified PivotTable
        
        :param pivot_table: PivotTable object
        :param keep_data: Whether to keep the PivotTable data'''
        raise NotImplementedError()
    
    def remove_by_index(self, index : int) -> None:
        '''Deletes the PivotTable at the specified index and delete the PivotTable data
        
        :param index: the position index in PivotTable collection'''
        raise NotImplementedError()
    
    def remove_at(self, index : int, keep_data : bool) -> None:
        '''Deletes the PivotTable at the specified index
        
        :param index: the position index in PivotTable collection
        :param keep_data: Whether to keep the PivotTable data'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.pivot.PivotTable) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class PivotTableFormat:
    '''Represents the format defined in the PivotTable.'''
    
    def get_style(self) -> aspose.cells.Style:
        '''Gets the formatted style.'''
        raise NotImplementedError()
    
    def set_style(self, style : aspose.cells.Style) -> None:
        '''Sets the style of the pivot area.'''
        raise NotImplementedError()
    
    @property
    def pivot_area(self) -> aspose.cells.pivot.PivotArea:
        '''Gets the pivot area.'''
        raise NotImplementedError()
    

class PivotTableFormatCollection:
    '''Represents the collection of formats applied to PivotTable.'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.pivot.PivotTableFormat]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.pivot.PivotTableFormat], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.pivot.PivotTableFormat, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.pivot.PivotTableFormat, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotTableFormat) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotTableFormat, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.pivot.PivotTableFormat, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add(self) -> int:
        '''Add a :py:class:`aspose.cells.pivot.PivotTableFormat`.
        
        :returns: The index of new format.'''
        raise NotImplementedError()
    
    def format_area(self, axis_type : aspose.cells.pivot.PivotFieldType, field_position : int, subtotal_type : aspose.cells.pivot.PivotFieldSubtotalType, selection_type : aspose.cells.pivot.PivotTableSelectionType, is_grand_row : bool, is_grand_column : bool, style : aspose.cells.Style) -> aspose.cells.pivot.PivotTableFormat:
        '''Formats selected area.
        
        :param axis_type: The region of the PivotTable to which this rule applies.
        :param field_position: Position of the field within the axis to which this rule applies.
        :param subtotal_type: The subtotal filter type of the pivot field
        :param selection_type: Indicates how to select data.
        :param is_grand_row: Indicates whether selecting grand total rows.
        :param is_grand_column: Indicates whether selecting grand total columns.
        :param style: The style which appies to the area of the pivot table.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.pivot.PivotTableFormat) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class PivotTableRefreshOption:
    '''Represents the options of refreshing data source of the pivot table.'''
    
    def __init__(self) -> None:
        '''Represents the options of refreshing data source of the pivot table.'''
        raise NotImplementedError()
    
    @property
    def reserve_missing_pivot_item_type(self) -> aspose.cells.pivot.ReserveMissingPivotItemType:
        '''Represents how to reserve missing pivot items.'''
        raise NotImplementedError()
    
    @reserve_missing_pivot_item_type.setter
    def reserve_missing_pivot_item_type(self, value : aspose.cells.pivot.ReserveMissingPivotItemType) -> None:
        '''Represents how to reserve missing pivot items.'''
        raise NotImplementedError()
    

class SxRng:
    
    @property
    def is_auto_start(self) -> Any:
        raise NotImplementedError()
    
    @property
    def is_auto_end(self) -> Any:
        raise NotImplementedError()
    
    @property
    def start(self) -> Any:
        raise NotImplementedError()
    
    @property
    def end(self) -> Any:
        raise NotImplementedError()
    
    @property
    def by(self) -> Any:
        raise NotImplementedError()
    
    @property
    def group_by_types(self) -> List[bool]:
        raise NotImplementedError()
    

class PivotAreaType:
    '''Indicates the type of rule being used to describe an area or aspect of the PivotTable.'''
    
    NONE : PivotAreaType
    '''No Pivot area.'''
    NORMAL : PivotAreaType
    '''Represents a header or item.'''
    DATA : PivotAreaType
    '''Represents something in the data area.'''
    ALL : PivotAreaType
    '''Represents the whole PivotTable.'''
    ORIGIN : PivotAreaType
    '''Represents the blank cells at the top-left of the PivotTable (top-right for RTL sheets).'''
    BUTTON : PivotAreaType
    '''Represents a field button.'''
    TOP_RIGHT : PivotAreaType
    '''Represents the blank cells at the top-right of the PivotTable (top-left for RTL sheets).'''

class PivotConditionFormatRuleType:
    '''Represents PivotTable condition formatting rule type.'''
    
    NONE : PivotConditionFormatRuleType
    '''Indicates that Top N conditional formatting is not evaluated'''
    ALL : PivotConditionFormatRuleType
    '''Indicates that Top N conditional formatting is
    evaluated across the entire scope range.'''
    ROW : PivotConditionFormatRuleType
    '''Indicates that Top N conditional formatting is evaluated for each row.'''
    COLUMN : PivotConditionFormatRuleType
    '''Indicates that Top N conditional formatting is
    evaluated for each column.'''

class PivotConditionFormatScopeType:
    '''Represents PivotTable condition formatting scope type.'''
    
    DATA : PivotConditionFormatScopeType
    '''Indicates that conditional formatting is applied to the selected data fields.'''
    FIELD : PivotConditionFormatScopeType
    '''Indicates that conditional formatting is applied to the selected PivotTable field intersections.'''
    SELECTION : PivotConditionFormatScopeType
    '''Indicates that conditional formatting is applied to the selected cells.'''

class PivotFieldDataDisplayFormat:
    '''Represents data display format in the PivotTable data field.'''
    
    NORMAL : PivotFieldDataDisplayFormat
    '''Represents normal display format.'''
    DIFFERENCE_FROM : PivotFieldDataDisplayFormat
    '''Represents difference from display format.'''
    PERCENTAGE_OF : PivotFieldDataDisplayFormat
    '''Represents percentage of display format.'''
    PERCENTAGE_DIFFERENCE_FROM : PivotFieldDataDisplayFormat
    '''Represents percentage difference from  display format.'''
    RUNNING_TOTAL_IN : PivotFieldDataDisplayFormat
    '''Represents running total in display format.'''
    PERCENTAGE_OF_ROW : PivotFieldDataDisplayFormat
    '''Represents percentage of row display format.'''
    PERCENTAGE_OF_COLUMN : PivotFieldDataDisplayFormat
    '''Represents percentage of column display format.'''
    PERCENTAGE_OF_TOTAL : PivotFieldDataDisplayFormat
    '''Represents percentage of total display format.'''
    INDEX : PivotFieldDataDisplayFormat
    '''Represents index display format.'''
    PERCENTAGE_OF_PARENT_ROW_TOTAL : PivotFieldDataDisplayFormat
    '''Represents percentage of parent row total display format.'''
    PERCENTAGE_OF_PARENT_COLUMN_TOTAL : PivotFieldDataDisplayFormat
    '''Represents percentage of parent column total display format.'''
    PERCENTAGE_OF_PARENT_TOTAL : PivotFieldDataDisplayFormat
    '''Represents percentage of parent total display format.'''
    PERCENTAGE_OF_RUNNING_TOTAL_IN : PivotFieldDataDisplayFormat
    '''Represents percentage of running total in display format.'''
    RANK_SMALLEST_TO_LARGEST : PivotFieldDataDisplayFormat
    '''Represents smallest to largest display format.'''
    RANK_LARGEST_TO_SMALLEST : PivotFieldDataDisplayFormat
    '''Represents largest to smallest display format.'''

class PivotFieldGroupType:
    '''Represents the group type of pivot field.'''
    
    NONE : PivotFieldGroupType
    '''No group'''
    DATE_TIME_RANGE : PivotFieldGroupType
    '''Grouped by DateTime range.'''
    NUMBERIC_RANGE : PivotFieldGroupType
    '''Grouped by numberic range.'''
    DISCRETE : PivotFieldGroupType
    '''Grouped by discrete points.'''

class PivotFieldSubtotalType:
    '''Summary description for PivotFieldSubtotalType.'''
    
    NONE : PivotFieldSubtotalType
    '''Represents None subtotal type.'''
    AUTOMATIC : PivotFieldSubtotalType
    '''Represents Automatic subtotal type.'''
    SUM : PivotFieldSubtotalType
    '''Represents Sum subtotal type.'''
    COUNT : PivotFieldSubtotalType
    '''Represents Count subtotal type.'''
    AVERAGE : PivotFieldSubtotalType
    '''Represents Average subtotal type.'''
    MAX : PivotFieldSubtotalType
    '''Represents Max subtotal type.'''
    MIN : PivotFieldSubtotalType
    '''Represents Min subtotal type.'''
    PRODUCT : PivotFieldSubtotalType
    '''Represents Product subtotal type.'''
    COUNT_NUMS : PivotFieldSubtotalType
    '''Represents Count Nums subtotal type.'''
    STDEV : PivotFieldSubtotalType
    '''Represents Stdev subtotal type.'''
    STDEVP : PivotFieldSubtotalType
    '''Represents Stdevp subtotal type.'''
    VAR : PivotFieldSubtotalType
    '''Represents Var subtotal type.'''
    VARP : PivotFieldSubtotalType
    '''Represents Varp subtotal type.'''

class PivotFieldType:
    '''Represents PivotTable field type.'''
    
    UNDEFINED : PivotFieldType
    '''Presents base pivot field type.'''
    ROW : PivotFieldType
    '''Presents row pivot field type.'''
    COLUMN : PivotFieldType
    '''Presents column pivot field type.'''
    PAGE : PivotFieldType
    '''Presents page pivot field type.'''
    DATA : PivotFieldType
    '''Presents data pivot field type.'''

class PivotFilterType:
    '''Represents PivotTable Filter type.'''
    
    CAPTION_BEGINS_WITH : PivotFilterType
    '''Indicates the "begins with" filter for field captions.'''
    CAPTION_BETWEEN : PivotFilterType
    '''Indicates the "is between" filter for field captions.'''
    CAPTION_CONTAINS : PivotFilterType
    '''Indicates the "contains" filter for field captions.'''
    CAPTION_ENDS_WITH : PivotFilterType
    '''Indicates the "ends with" filter for field captions.'''
    CAPTION_EQUAL : PivotFilterType
    '''Indicates the "equal" filter for field captions.'''
    CAPTION_GREATER_THAN : PivotFilterType
    '''Indicates the "is greater than" filter for field captions.'''
    CAPTION_GREATER_THAN_OR_EQUAL : PivotFilterType
    '''Indicates the "is greater than or equal to" filter for field captions.'''
    CAPTION_LESS_THAN : PivotFilterType
    '''Indicates the "is less than" filter for field captions.'''
    CAPTION_LESS_THAN_OR_EQUAL : PivotFilterType
    '''Indicates the "is less than or equal to" filter for field captions.'''
    CAPTION_NOT_BEGINS_WITH : PivotFilterType
    '''Indicates the "does not begin with" filter for field captions.'''
    CAPTION_NOT_BETWEEN : PivotFilterType
    '''Indicates the "is not between" filter for field captions.'''
    CAPTION_NOT_CONTAINS : PivotFilterType
    '''Indicates the "does not contain" filter for field captions.'''
    CAPTION_NOT_ENDS_WITH : PivotFilterType
    '''Indicates the "does not end with" filter for field captions.'''
    CAPTION_NOT_EQUAL : PivotFilterType
    '''Indicates the "not equal" filter for field captions.'''
    COUNT : PivotFilterType
    '''Indicates the "count" filter.'''
    DATE_BETWEEN : PivotFilterType
    '''Indicates the "between" filter for date values.'''
    DATE_EQUAL : PivotFilterType
    '''Indicates the "equals" filter for date values.'''
    DATE_NEWER_THAN : PivotFilterType
    '''Indicates the "after" filter for date values.'''
    DATE_AFTER : PivotFilterType
    '''Indicates the "after" filter for date values.'''
    DATE_NEWER_THAN_OR_EQUAL : PivotFilterType
    '''Indicates the "after or equal to" filter for date values.'''
    DATE_AFTER_OR_EQUAL : PivotFilterType
    '''Indicates the "after or equal to" filter for date values.'''
    DATE_NOT_BETWEEN : PivotFilterType
    '''Indicates the "not between" filter for date values.'''
    DATE_NOT_EQUAL : PivotFilterType
    '''Indicates the "does not equal" filter for date values.'''
    DATE_OLDER_THAN : PivotFilterType
    '''Indicates the "before" filter for date values.'''
    DATE_BEFORE : PivotFilterType
    '''Indicates the "before" filter for date values.'''
    DATE_OLDER_THAN_OR_EQUAL : PivotFilterType
    '''Indicates the "before or equal to" filter for date values.'''
    DATE_BEFORE_OR_EQUAL : PivotFilterType
    '''Indicates the "before or equal to" filter for date values.'''
    LAST_MONTH : PivotFilterType
    '''Indicates the "last month" filter for date values.'''
    LAST_QUARTER : PivotFilterType
    '''Indicates the "last quarter" filter for date values.'''
    LAST_WEEK : PivotFilterType
    '''Indicates the "last week" filter for date values.'''
    LAST_YEAR : PivotFilterType
    '''Indicates the "last year" filter for date values.'''
    M1 : PivotFilterType
    '''Indicates the "January" filter for date values.'''
    JANUARY : PivotFilterType
    '''Indicates the "January" filter for date values.'''
    M2 : PivotFilterType
    '''Indicates the "February" filter for date values.'''
    FEBRUARY : PivotFilterType
    '''Indicates the "February" filter for date values.'''
    M3 : PivotFilterType
    '''Indicates the "March" filter for date values.'''
    MARCH : PivotFilterType
    '''Indicates the "March" filter for date values.'''
    M4 : PivotFilterType
    '''Indicates the "April" filter for date values.'''
    APRIL : PivotFilterType
    '''Indicates the "April" filter for date values.'''
    M5 : PivotFilterType
    '''Indicates the "May" filter for date values.'''
    MAY : PivotFilterType
    '''Indicates the "May" filter for date values.'''
    M6 : PivotFilterType
    '''Indicates the "June" filter for date values.'''
    JUNE : PivotFilterType
    '''Indicates the "June" filter for date values.'''
    M7 : PivotFilterType
    '''Indicates the "July" filter for date values.'''
    JULY : PivotFilterType
    '''Indicates the "July" filter for date values.'''
    M8 : PivotFilterType
    '''Indicates the "August" filter for date values.'''
    AUGUST : PivotFilterType
    '''Indicates the "August" filter for date values.'''
    M9 : PivotFilterType
    '''Indicates the "September" filter for date values.'''
    SEPTEMBER : PivotFilterType
    '''Indicates the "September" filter for date values.'''
    M10 : PivotFilterType
    '''Indicates the "October" filter for date values.'''
    OCTOBER : PivotFilterType
    '''Indicates the "October" filter for date values.'''
    M11 : PivotFilterType
    '''Indicates the "November" filter for date values.'''
    NOVEMBER : PivotFilterType
    '''Indicates the "November" filter for date values.'''
    M12 : PivotFilterType
    '''Indicates the "December" filter for date values.'''
    DECEMBER : PivotFilterType
    '''Indicates the "December" filter for date values.'''
    NEXT_MONTH : PivotFilterType
    '''Indicates the "next month" filter for date values.'''
    NEXT_QUARTER : PivotFilterType
    '''Indicates the "next quarter" for date values.'''
    NEXT_WEEK : PivotFilterType
    '''Indicates the "next week" for date values.'''
    NEXT_YEAR : PivotFilterType
    '''Indicates the "next year" filter for date values.'''
    PERCENT : PivotFilterType
    '''Indicates the "percent" filter for numeric values.'''
    Q1 : PivotFilterType
    '''Indicates the "first quarter" filter for date values.'''
    QUARTER1 : PivotFilterType
    '''Indicates the "first quarter" filter for date values.'''
    Q2 : PivotFilterType
    '''Indicates the "second quarter" filter for date values.'''
    QUARTER2 : PivotFilterType
    '''Indicates the "second quarter" filter for date values.'''
    Q3 : PivotFilterType
    '''Indicates the "third quarter" filter for date values.'''
    QUARTER3 : PivotFilterType
    '''Indicates the "third quarter" filter for date values.'''
    Q4 : PivotFilterType
    '''Indicates the "fourth quarter" filter for date values.'''
    QUARTER4 : PivotFilterType
    '''Indicates the "fourth quarter" filter for date values.'''
    SUM : PivotFilterType
    '''Indicates the "sum" filter for numeric values.'''
    THIS_MONTH : PivotFilterType
    '''Indicates the "this month" filter for date values.'''
    THIS_QUARTER : PivotFilterType
    '''Indicates the "this quarter" filter for date values.'''
    THIS_WEEK : PivotFilterType
    '''Indicates the "this week" filter for date values.'''
    THIS_YEAR : PivotFilterType
    '''Indicate the "this year" filter for date values.'''
    TODAY : PivotFilterType
    '''Indicates the "today" filter for date values.'''
    TOMORROW : PivotFilterType
    '''Indicates the "tomorrow" filter for date values.'''
    UNKNOWN : PivotFilterType
    '''Indicates the PivotTable filter is unknown to the application.'''
    VALUE_BETWEEN : PivotFilterType
    '''Indicates the "Value between" filter for text and numeric values.'''
    VALUE_EQUAL : PivotFilterType
    '''Indicates the "value equal" filter for text and numeric values.'''
    VALUE_GREATER_THAN : PivotFilterType
    '''Indicates the "value greater than" filter for text and numeric values.'''
    VALUE_GREATER_THAN_OR_EQUAL : PivotFilterType
    '''Indicates the "value greater than or equal to" filter for text and numeric values.'''
    VALUE_LESS_THAN : PivotFilterType
    '''Indicates the "value less than" filter for text and numeric values.'''
    VALUE_LESS_THAN_OR_EQUAL : PivotFilterType
    '''Indicates the "value less than or equal to" filter for text and numeric values.'''
    VALUE_NOT_BETWEEN : PivotFilterType
    '''Indicates the "value not between" filter for text and numeric values.'''
    VALUE_NOT_EQUAL : PivotFilterType
    '''Indicates the "value not equal" filter for text and numeric values.'''
    YEAR_TO_DATE : PivotFilterType
    '''Indicates the "year-to-date" filter for date values.'''
    YESTERDAY : PivotFilterType
    '''Indicates the "yesterday" filter for date values.'''
    NONE : PivotFilterType
    '''No filter.'''

class PivotGroupByType:
    '''Represents group by type.'''
    
    RANGE_OF_VALUES : PivotGroupByType
    '''Group by numbers.'''
    NUMBERS : PivotGroupByType
    '''Group by numbers.'''
    SECONDS : PivotGroupByType
    '''Presents Seconds groupby type.'''
    MINUTES : PivotGroupByType
    '''Presents Minutes groupby type.'''
    HOURS : PivotGroupByType
    '''Presents Hours groupby type.'''
    DAYS : PivotGroupByType
    '''Presents Days groupby type.'''
    MONTHS : PivotGroupByType
    '''Presents Months groupby type.'''
    QUARTERS : PivotGroupByType
    '''Presents Quarters groupby type.'''
    YEARS : PivotGroupByType
    '''Presents Years groupby type.'''

class PivotItemPosition:
    
    PREVIOUS : PivotItemPosition
    NEXT : PivotItemPosition
    CUSTOM : PivotItemPosition

class PivotItemPositionType:
    '''Represents the position type of the pivot base item in the base field when the ShowDataAs calculation is in use.'''
    
    PREVIOUS : PivotItemPositionType
    '''Represents the previous pivot item in the PivotField.'''
    NEXT : PivotItemPositionType
    '''Represents the next pivot item in the PivotField.'''
    CUSTOM : PivotItemPositionType
    '''Shows values as the different format based the index of pivot item in the PivotField.'''

class PivotLineType:
    '''Specifies the type of the PivotLine.'''
    
    REGULAR : PivotLineType
    '''Regular PivotLine with pivot items.'''
    SUBTOTAL : PivotLineType
    '''Subtotal line.'''
    GRAND_TOTAL : PivotLineType
    '''Grand Total line.'''
    BLANK : PivotLineType
    '''Blank line after each group.'''

class PivotMissingItemLimitType:
    '''Represents number of items to retain per field.'''
    
    AUTOMATIC : PivotMissingItemLimitType
    '''The default number of unique items per PivotField allowed.'''
    MAX : PivotMissingItemLimitType
    '''The maximum number of unique items per PivotField allowed (>32,500).'''
    NONE : PivotMissingItemLimitType
    '''No unique items per PivotField allowed.'''

class PivotRefreshState:
    '''The state for refreshing pivot tables.'''
    
    SUCCESS : PivotRefreshState
    '''Successfully refreshed'''
    UNSUPPORTED_EXTERNAL_DATA_SOURCE : PivotRefreshState
    '''Refresh failed because the data source is external.'''

class PivotTableAutoFormatType:
    '''Represents PivotTable auto format type.'''
    
    NONE : PivotTableAutoFormatType
    '''Represents None format type.'''
    CLASSIC : PivotTableAutoFormatType
    '''Represents Classic auto format type.'''
    REPORT1 : PivotTableAutoFormatType
    '''Represents Report1 format type.'''
    REPORT2 : PivotTableAutoFormatType
    '''Represents Report2 format type.'''
    REPORT3 : PivotTableAutoFormatType
    '''Represents Report3 format type.'''
    REPORT4 : PivotTableAutoFormatType
    '''Represents Report4 format type.'''
    REPORT5 : PivotTableAutoFormatType
    '''Represents Report5 format type.'''
    REPORT6 : PivotTableAutoFormatType
    '''Represents Report6 format type.'''
    REPORT7 : PivotTableAutoFormatType
    '''Represents Report7 format type.'''
    REPORT8 : PivotTableAutoFormatType
    '''Represents Report8 format type.'''
    REPORT9 : PivotTableAutoFormatType
    '''Represents Report9 format type.'''
    REPORT10 : PivotTableAutoFormatType
    '''Represents Report10 format type.'''
    TABLE1 : PivotTableAutoFormatType
    '''Represents Table1 format type.'''
    TABLE2 : PivotTableAutoFormatType
    '''Represents Table2 format type.'''
    TABLE3 : PivotTableAutoFormatType
    '''Represents Table3 format type.'''
    TABLE4 : PivotTableAutoFormatType
    '''Represents Table4 format type.'''
    TABLE5 : PivotTableAutoFormatType
    '''Represents Table5 format type.'''
    TABLE6 : PivotTableAutoFormatType
    '''Represents Table6 format type.'''
    TABLE7 : PivotTableAutoFormatType
    '''Represents Table7 format type.'''
    TABLE8 : PivotTableAutoFormatType
    '''Represents Table8 format type.'''
    TABLE9 : PivotTableAutoFormatType
    '''Represents Table9 format type.'''
    TABLE10 : PivotTableAutoFormatType
    '''Represents Table10 format type.'''

class PivotTableSelectionType:
    '''Specifies what can be selected in a PivotTable during a structured selection.
    These constants can be combined to select multiple types.'''
    
    DATA_AND_LABEL : PivotTableSelectionType
    '''Data and labels'''
    DATA_ONLY : PivotTableSelectionType
    '''Only selects data'''
    LABEL_ONLY : PivotTableSelectionType
    '''Only selects labels'''

class PivotTableSourceType:
    '''Represents data source type of the pivot table.'''
    
    SHEET : PivotTableSourceType
    '''Specifies that the source data is a range.'''
    EXTERNAL : PivotTableSourceType
    '''Specifies that external source data is used.'''
    CONSOLIDATION : PivotTableSourceType
    '''Specifies that multiple consolidation ranges are used as the source data.'''
    SCENARIO : PivotTableSourceType
    '''The source data is populated from a temporary internal structure.'''
    UNKNOWN : PivotTableSourceType
    '''Unknown data source.'''

class PivotTableStyleType:
    '''Represents the pivot table style type.'''
    
    NONE : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT1 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT2 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT3 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT4 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT5 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT6 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT7 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT8 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT9 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT10 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT11 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT12 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT13 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT14 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT15 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT16 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT17 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT18 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT19 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT20 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT21 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT22 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT23 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT24 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT25 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT26 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT27 : PivotTableStyleType
    PIVOT_TABLE_STYLE_LIGHT28 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM1 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM2 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM3 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM4 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM5 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM6 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM7 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM8 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM9 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM10 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM11 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM12 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM13 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM14 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM15 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM16 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM17 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM18 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM19 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM20 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM21 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM22 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM23 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM24 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM25 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM26 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM27 : PivotTableStyleType
    PIVOT_TABLE_STYLE_MEDIUM28 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK1 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK2 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK3 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK4 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK5 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK6 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK7 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK8 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK9 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK10 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK11 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK12 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK13 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK14 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK15 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK16 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK17 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK18 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK19 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK20 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK21 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK22 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK23 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK24 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK25 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK26 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK27 : PivotTableStyleType
    PIVOT_TABLE_STYLE_DARK28 : PivotTableStyleType
    CUSTOM : PivotTableStyleType

class ReserveMissingPivotItemType:
    '''Represents how to keep the missing pivot items.'''
    
    DEFAULT : ReserveMissingPivotItemType
    '''Removes old missint pivot items and reserves visible items which the current data source does not contain as missing items.'''
    ALL : ReserveMissingPivotItemType
    '''Reserves all missing items.'''
    NONE : ReserveMissingPivotItemType
    '''Removes all missing pivot items.'''

