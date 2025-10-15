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

class PivotGlobalizationSettings:
    '''Represents the globalization settings for pivot tables.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def get_text_of_total(self) -> str:
        '''Gets the text of "Total" label in the PivotTable.
        You need to override this method when the PivotTable contains two or more PivotFields in the data area.
        
        :returns: The text of "Total" label'''
        raise NotImplementedError()
    
    def get_text_of_grand_total(self) -> str:
        '''Gets the text of "Grand Total" label in the PivotTable.
        
        :returns: The text of "Grand Total" label'''
        raise NotImplementedError()
    
    def get_text_of_multiple_items(self) -> str:
        '''Gets the text of "(Multiple Items)" label in the PivotTable.
        
        :returns: The text of "(Multiple Items)" label'''
        raise NotImplementedError()
    
    def get_text_of_all(self) -> str:
        '''Gets the text of "(All)" label in the PivotTable.
        
        :returns: The text of "(All)" label'''
        raise NotImplementedError()
    
    def get_text_of_protection(self) -> str:
        '''Gets the protection name in the PivotTable.
        
        :returns: The protection name of PivotTable'''
        raise NotImplementedError()
    
    def get_text_of_protected_name(self, protected_name : str) -> str:
        '''Gets the text for specified protected name.
        
        :param protected_name: The protected name in PivotTable.
        :returns: The local prorected names of PivotTable.'''
        raise NotImplementedError()
    
    def get_text_of_column_labels(self) -> str:
        '''Gets the text of "Column Labels" label in the PivotTable.
        
        :returns: The text of column labels'''
        raise NotImplementedError()
    
    def get_text_of_row_labels(self) -> str:
        '''Gets the text of "Row Labels" label in the PivotTable.
        
        :returns: The text of row labels'''
        raise NotImplementedError()
    
    def get_text_of_empty_data(self) -> str:
        '''Gets the text of "(blank)" label in the PivotTable.
        
        :returns: The text of empty data'''
        raise NotImplementedError()
    
    def get_text_of_data_field_header(self) -> str:
        '''Gets the the text of the value area field header in the PivotTable.
        
        :returns: The text of data field header name'''
        raise NotImplementedError()
    
    def get_short_text_of_12_months(self) -> List[str]:
        '''Gets all short formatted string of 12 months.'''
        raise NotImplementedError()
    
    def get_text_of_4_quaters(self) -> List[str]:
        '''Gets the local text of 4 Quaters.'''
        raise NotImplementedError()
    
    def get_text_of_years(self) -> str:
        '''Gets the local text of "Years".'''
        raise NotImplementedError()
    
    def get_text_of_quarters(self) -> str:
        '''Get the local text of "Quarters".'''
        raise NotImplementedError()
    
    def get_text_of_months(self) -> str:
        '''Gets the local text of "Months".'''
        raise NotImplementedError()
    
    def get_text_of_days(self) -> str:
        '''Gets the local text of "Days".'''
        raise NotImplementedError()
    
    def get_text_of_hours(self) -> str:
        '''Gets the local text of "Hours".'''
        raise NotImplementedError()
    
    def get_text_of_minutes(self) -> str:
        '''Gets the local text of "Minutes".'''
        raise NotImplementedError()
    
    def get_text_of_seconds(self) -> str:
        '''Gets the local text of "Seconds"'''
        raise NotImplementedError()
    
    def get_text_of_range(self) -> str:
        '''Gets the local text of "Range"'''
        raise NotImplementedError()
    
    def get_text_of_all_periods(self) -> str:
        '''Gets the localized text of "All Periods".'''
        raise NotImplementedError()
    
    def get_text_of_sub_total(self, sub_total_type : aspose.cells.pivot.PivotFieldSubtotalType) -> str:
        '''Gets the text of :py:class:`aspose.cells.pivot.PivotFieldSubtotalType` type in the PivotTable.
        
        :param sub_total_type: The :py:class:`aspose.cells.pivot.PivotFieldSubtotalType`
        :returns: The text of given type'''
        raise NotImplementedError()
    

