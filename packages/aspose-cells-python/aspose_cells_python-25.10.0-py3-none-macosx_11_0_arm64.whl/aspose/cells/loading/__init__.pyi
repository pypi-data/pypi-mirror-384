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

class DbfLoadOptions(aspose.cells.LoadOptions):
    '''Represents the options of loading .dbf file.'''
    
    def __init__(self) -> None:
        '''The options.'''
        raise NotImplementedError()
    
    def set_paper_size(self, type : aspose.cells.PaperSizeType) -> None:
        '''Sets the default print paper size from default printer\'s setting.
        
        :param type: The default paper size.'''
        raise NotImplementedError()
    
    @property
    def load_format(self) -> aspose.cells.LoadFormat:
        '''Gets the load format.'''
        raise NotImplementedError()
    
    @property
    def password(self) -> str:
        '''Gets and set the password of the workbook.'''
        raise NotImplementedError()
    
    @password.setter
    def password(self, value : str) -> None:
        '''Gets and set the password of the workbook.'''
        raise NotImplementedError()
    
    @property
    def parsing_formula_on_open(self) -> bool:
        '''Indicates whether parsing the formula when reading the file.'''
        raise NotImplementedError()
    
    @parsing_formula_on_open.setter
    def parsing_formula_on_open(self, value : bool) -> None:
        '''Indicates whether parsing the formula when reading the file.'''
        raise NotImplementedError()
    
    @property
    def parsing_pivot_cached_records(self) -> bool:
        '''Indicates whether parsing pivot cached records when loading the file.
        The default value is false.'''
        raise NotImplementedError()
    
    @parsing_pivot_cached_records.setter
    def parsing_pivot_cached_records(self, value : bool) -> None:
        '''Indicates whether parsing pivot cached records when loading the file.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def language_code(self) -> aspose.cells.CountryCode:
        '''Gets the user interface language of the Workbook version based on CountryCode that has saved the file.'''
        raise NotImplementedError()
    
    @language_code.setter
    def language_code(self, value : aspose.cells.CountryCode) -> None:
        '''Sets the user interface language of the Workbook version based on CountryCode that has saved the file.'''
        raise NotImplementedError()
    
    @property
    def region(self) -> aspose.cells.CountryCode:
        '''Gets the regional settings used for the Workbook that will be loaded.'''
        raise NotImplementedError()
    
    @region.setter
    def region(self, value : aspose.cells.CountryCode) -> None:
        '''Sets the regional settings used for the Workbook that will be loaded.'''
        raise NotImplementedError()
    
    @property
    def default_style_settings(self) -> aspose.cells.DefaultStyleSettings:
        '''Gets the default style settings for initializing styles of the workbook'''
        raise NotImplementedError()
    
    @property
    def standard_font(self) -> str:
        '''Sets the default standard font name'''
        raise NotImplementedError()
    
    @standard_font.setter
    def standard_font(self, value : str) -> None:
        '''Sets the default standard font name'''
        raise NotImplementedError()
    
    @property
    def standard_font_size(self) -> float:
        '''Sets the default standard font size.'''
        raise NotImplementedError()
    
    @standard_font_size.setter
    def standard_font_size(self, value : float) -> None:
        '''Sets the default standard font size.'''
        raise NotImplementedError()
    
    @property
    def interrupt_monitor(self) -> aspose.cells.AbstractInterruptMonitor:
        '''Gets and sets the interrupt monitor.'''
        raise NotImplementedError()
    
    @interrupt_monitor.setter
    def interrupt_monitor(self, value : aspose.cells.AbstractInterruptMonitor) -> None:
        '''Gets and sets the interrupt monitor.'''
        raise NotImplementedError()
    
    @property
    def ignore_not_printed(self) -> bool:
        '''Ignore the data which are not printed if directly printing the file'''
        raise NotImplementedError()
    
    @ignore_not_printed.setter
    def ignore_not_printed(self, value : bool) -> None:
        '''Ignore the data which are not printed if directly printing the file'''
        raise NotImplementedError()
    
    @property
    def check_data_valid(self) -> bool:
        '''Check whether data is valid in the template file.'''
        raise NotImplementedError()
    
    @check_data_valid.setter
    def check_data_valid(self, value : bool) -> None:
        '''Check whether data is valid in the template file.'''
        raise NotImplementedError()
    
    @property
    def check_excel_restriction(self) -> bool:
        '''Whether check restriction of excel file when user modify cells related objects.
        For example, excel does not allow inputting string value longer than 32K.
        When you input a value longer than 32K such as by Cell.PutValue(string), if this property is true, you will get an Exception.
        If this property is false, we will accept your input string value as the cell\'s value so that later
        you can output the complete string value for other file formats such as CSV.
        However, if you have set such kind of value that is invalid for excel file format,
        you should not save the workbook as excel file format later. Otherwise there may be unexpected error for the generated excel file.'''
        raise NotImplementedError()
    
    @check_excel_restriction.setter
    def check_excel_restriction(self, value : bool) -> None:
        '''Whether check restriction of excel file when user modify cells related objects.
        For example, excel does not allow inputting string value longer than 32K.
        When you input a value longer than 32K such as by Cell.PutValue(string), if this property is true, you will get an Exception.
        If this property is false, we will accept your input string value as the cell\'s value so that later
        you can output the complete string value for other file formats such as CSV.
        However, if you have set such kind of value that is invalid for excel file format,
        you should not save the workbook as excel file format later. Otherwise there may be unexpected error for the generated excel file.'''
        raise NotImplementedError()
    
    @property
    def keep_unparsed_data(self) -> bool:
        '''Whether keep the unparsed data in memory for the Workbook when it is loaded from template file. Default is true.'''
        raise NotImplementedError()
    
    @keep_unparsed_data.setter
    def keep_unparsed_data(self, value : bool) -> None:
        '''Whether keep the unparsed data in memory for the Workbook when it is loaded from template file. Default is true.'''
        raise NotImplementedError()
    
    @property
    def load_filter(self) -> aspose.cells.LoadFilter:
        '''The filter to denote how to load data.'''
        raise NotImplementedError()
    
    @load_filter.setter
    def load_filter(self, value : aspose.cells.LoadFilter) -> None:
        '''The filter to denote how to load data.'''
        raise NotImplementedError()
    
    @property
    def light_cells_data_handler(self) -> aspose.cells.LightCellsDataHandler:
        '''The data handler for processing cells data when reading template file.'''
        raise NotImplementedError()
    
    @light_cells_data_handler.setter
    def light_cells_data_handler(self, value : aspose.cells.LightCellsDataHandler) -> None:
        '''The data handler for processing cells data when reading template file.'''
        raise NotImplementedError()
    
    @property
    def memory_setting(self) -> aspose.cells.MemorySetting:
        '''Gets the memory mode for loaded workbook.'''
        raise NotImplementedError()
    
    @memory_setting.setter
    def memory_setting(self, value : aspose.cells.MemorySetting) -> None:
        '''Sets the memory mode for loaded workbook.'''
        raise NotImplementedError()
    
    @property
    def warning_callback(self) -> aspose.cells.IWarningCallback:
        '''Gets warning callback.'''
        raise NotImplementedError()
    
    @warning_callback.setter
    def warning_callback(self, value : aspose.cells.IWarningCallback) -> None:
        '''Sets warning callback.'''
        raise NotImplementedError()
    
    @property
    def auto_fitter_options(self) -> aspose.cells.AutoFitterOptions:
        '''Gets and sets the auto fitter options'''
        raise NotImplementedError()
    
    @auto_fitter_options.setter
    def auto_fitter_options(self, value : aspose.cells.AutoFitterOptions) -> None:
        '''Gets and sets the auto fitter options'''
        raise NotImplementedError()
    
    @property
    def auto_filter(self) -> bool:
        '''Indicates whether auto filtering the data when loading the files.'''
        raise NotImplementedError()
    
    @auto_filter.setter
    def auto_filter(self, value : bool) -> None:
        '''Indicates whether auto filtering the data when loading the files.'''
        raise NotImplementedError()
    
    @property
    def font_configs(self) -> aspose.cells.IndividualFontConfigs:
        '''Gets and sets individual font configs.
        Only works for the :py:class:`aspose.cells.Workbook` which uses this :py:class:`aspose.cells.LoadOptions` to load.'''
        raise NotImplementedError()
    
    @font_configs.setter
    def font_configs(self, value : aspose.cells.IndividualFontConfigs) -> None:
        '''Gets and sets individual font configs.
        Only works for the :py:class:`aspose.cells.Workbook` which uses this :py:class:`aspose.cells.LoadOptions` to load.'''
        raise NotImplementedError()
    
    @property
    def ignore_useless_shapes(self) -> bool:
        '''Indicates whether ignoring useless shapes.'''
        raise NotImplementedError()
    
    @ignore_useless_shapes.setter
    def ignore_useless_shapes(self, value : bool) -> None:
        '''Indicates whether ignoring useless shapes.'''
        raise NotImplementedError()
    
    @property
    def preserve_padding_spaces_in_formula(self) -> bool:
        '''Indicates whether preserve those spaces and line breaks that are padded between formula tokens
        while getting and setting formulas.
        Default value is false.'''
        raise NotImplementedError()
    
    @preserve_padding_spaces_in_formula.setter
    def preserve_padding_spaces_in_formula(self, value : bool) -> None:
        '''Indicates whether preserve those spaces and line breaks that are padded between formula tokens
        while getting and setting formulas.
        Default value is false.'''
        raise NotImplementedError()
    

class DifLoadOptions(aspose.cells.LoadOptions):
    '''Represents the options of loading .dif file.'''
    
    def __init__(self) -> None:
        '''The options.'''
        raise NotImplementedError()
    
    def set_paper_size(self, type : aspose.cells.PaperSizeType) -> None:
        '''Sets the default print paper size from default printer\'s setting.
        
        :param type: The default paper size.'''
        raise NotImplementedError()
    
    @property
    def load_format(self) -> aspose.cells.LoadFormat:
        '''Gets the load format.'''
        raise NotImplementedError()
    
    @property
    def password(self) -> str:
        '''Gets and set the password of the workbook.'''
        raise NotImplementedError()
    
    @password.setter
    def password(self, value : str) -> None:
        '''Gets and set the password of the workbook.'''
        raise NotImplementedError()
    
    @property
    def parsing_formula_on_open(self) -> bool:
        '''Indicates whether parsing the formula when reading the file.'''
        raise NotImplementedError()
    
    @parsing_formula_on_open.setter
    def parsing_formula_on_open(self, value : bool) -> None:
        '''Indicates whether parsing the formula when reading the file.'''
        raise NotImplementedError()
    
    @property
    def parsing_pivot_cached_records(self) -> bool:
        '''Indicates whether parsing pivot cached records when loading the file.
        The default value is false.'''
        raise NotImplementedError()
    
    @parsing_pivot_cached_records.setter
    def parsing_pivot_cached_records(self, value : bool) -> None:
        '''Indicates whether parsing pivot cached records when loading the file.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def language_code(self) -> aspose.cells.CountryCode:
        '''Gets the user interface language of the Workbook version based on CountryCode that has saved the file.'''
        raise NotImplementedError()
    
    @language_code.setter
    def language_code(self, value : aspose.cells.CountryCode) -> None:
        '''Sets the user interface language of the Workbook version based on CountryCode that has saved the file.'''
        raise NotImplementedError()
    
    @property
    def region(self) -> aspose.cells.CountryCode:
        '''Gets the regional settings used for the Workbook that will be loaded.'''
        raise NotImplementedError()
    
    @region.setter
    def region(self, value : aspose.cells.CountryCode) -> None:
        '''Sets the regional settings used for the Workbook that will be loaded.'''
        raise NotImplementedError()
    
    @property
    def default_style_settings(self) -> aspose.cells.DefaultStyleSettings:
        '''Gets the default style settings for initializing styles of the workbook'''
        raise NotImplementedError()
    
    @property
    def standard_font(self) -> str:
        '''Sets the default standard font name'''
        raise NotImplementedError()
    
    @standard_font.setter
    def standard_font(self, value : str) -> None:
        '''Sets the default standard font name'''
        raise NotImplementedError()
    
    @property
    def standard_font_size(self) -> float:
        '''Sets the default standard font size.'''
        raise NotImplementedError()
    
    @standard_font_size.setter
    def standard_font_size(self, value : float) -> None:
        '''Sets the default standard font size.'''
        raise NotImplementedError()
    
    @property
    def interrupt_monitor(self) -> aspose.cells.AbstractInterruptMonitor:
        '''Gets and sets the interrupt monitor.'''
        raise NotImplementedError()
    
    @interrupt_monitor.setter
    def interrupt_monitor(self, value : aspose.cells.AbstractInterruptMonitor) -> None:
        '''Gets and sets the interrupt monitor.'''
        raise NotImplementedError()
    
    @property
    def ignore_not_printed(self) -> bool:
        '''Ignore the data which are not printed if directly printing the file'''
        raise NotImplementedError()
    
    @ignore_not_printed.setter
    def ignore_not_printed(self, value : bool) -> None:
        '''Ignore the data which are not printed if directly printing the file'''
        raise NotImplementedError()
    
    @property
    def check_data_valid(self) -> bool:
        '''Check whether data is valid in the template file.'''
        raise NotImplementedError()
    
    @check_data_valid.setter
    def check_data_valid(self, value : bool) -> None:
        '''Check whether data is valid in the template file.'''
        raise NotImplementedError()
    
    @property
    def check_excel_restriction(self) -> bool:
        '''Whether check restriction of excel file when user modify cells related objects.
        For example, excel does not allow inputting string value longer than 32K.
        When you input a value longer than 32K such as by Cell.PutValue(string), if this property is true, you will get an Exception.
        If this property is false, we will accept your input string value as the cell\'s value so that later
        you can output the complete string value for other file formats such as CSV.
        However, if you have set such kind of value that is invalid for excel file format,
        you should not save the workbook as excel file format later. Otherwise there may be unexpected error for the generated excel file.'''
        raise NotImplementedError()
    
    @check_excel_restriction.setter
    def check_excel_restriction(self, value : bool) -> None:
        '''Whether check restriction of excel file when user modify cells related objects.
        For example, excel does not allow inputting string value longer than 32K.
        When you input a value longer than 32K such as by Cell.PutValue(string), if this property is true, you will get an Exception.
        If this property is false, we will accept your input string value as the cell\'s value so that later
        you can output the complete string value for other file formats such as CSV.
        However, if you have set such kind of value that is invalid for excel file format,
        you should not save the workbook as excel file format later. Otherwise there may be unexpected error for the generated excel file.'''
        raise NotImplementedError()
    
    @property
    def keep_unparsed_data(self) -> bool:
        '''Whether keep the unparsed data in memory for the Workbook when it is loaded from template file. Default is true.'''
        raise NotImplementedError()
    
    @keep_unparsed_data.setter
    def keep_unparsed_data(self, value : bool) -> None:
        '''Whether keep the unparsed data in memory for the Workbook when it is loaded from template file. Default is true.'''
        raise NotImplementedError()
    
    @property
    def load_filter(self) -> aspose.cells.LoadFilter:
        '''The filter to denote how to load data.'''
        raise NotImplementedError()
    
    @load_filter.setter
    def load_filter(self, value : aspose.cells.LoadFilter) -> None:
        '''The filter to denote how to load data.'''
        raise NotImplementedError()
    
    @property
    def light_cells_data_handler(self) -> aspose.cells.LightCellsDataHandler:
        '''The data handler for processing cells data when reading template file.'''
        raise NotImplementedError()
    
    @light_cells_data_handler.setter
    def light_cells_data_handler(self, value : aspose.cells.LightCellsDataHandler) -> None:
        '''The data handler for processing cells data when reading template file.'''
        raise NotImplementedError()
    
    @property
    def memory_setting(self) -> aspose.cells.MemorySetting:
        '''Gets the memory mode for loaded workbook.'''
        raise NotImplementedError()
    
    @memory_setting.setter
    def memory_setting(self, value : aspose.cells.MemorySetting) -> None:
        '''Sets the memory mode for loaded workbook.'''
        raise NotImplementedError()
    
    @property
    def warning_callback(self) -> aspose.cells.IWarningCallback:
        '''Gets warning callback.'''
        raise NotImplementedError()
    
    @warning_callback.setter
    def warning_callback(self, value : aspose.cells.IWarningCallback) -> None:
        '''Sets warning callback.'''
        raise NotImplementedError()
    
    @property
    def auto_fitter_options(self) -> aspose.cells.AutoFitterOptions:
        '''Gets and sets the auto fitter options'''
        raise NotImplementedError()
    
    @auto_fitter_options.setter
    def auto_fitter_options(self, value : aspose.cells.AutoFitterOptions) -> None:
        '''Gets and sets the auto fitter options'''
        raise NotImplementedError()
    
    @property
    def auto_filter(self) -> bool:
        '''Indicates whether auto filtering the data when loading the files.'''
        raise NotImplementedError()
    
    @auto_filter.setter
    def auto_filter(self, value : bool) -> None:
        '''Indicates whether auto filtering the data when loading the files.'''
        raise NotImplementedError()
    
    @property
    def font_configs(self) -> aspose.cells.IndividualFontConfigs:
        '''Gets and sets individual font configs.
        Only works for the :py:class:`aspose.cells.Workbook` which uses this :py:class:`aspose.cells.LoadOptions` to load.'''
        raise NotImplementedError()
    
    @font_configs.setter
    def font_configs(self, value : aspose.cells.IndividualFontConfigs) -> None:
        '''Gets and sets individual font configs.
        Only works for the :py:class:`aspose.cells.Workbook` which uses this :py:class:`aspose.cells.LoadOptions` to load.'''
        raise NotImplementedError()
    
    @property
    def ignore_useless_shapes(self) -> bool:
        '''Indicates whether ignoring useless shapes.'''
        raise NotImplementedError()
    
    @ignore_useless_shapes.setter
    def ignore_useless_shapes(self, value : bool) -> None:
        '''Indicates whether ignoring useless shapes.'''
        raise NotImplementedError()
    
    @property
    def preserve_padding_spaces_in_formula(self) -> bool:
        '''Indicates whether preserve those spaces and line breaks that are padded between formula tokens
        while getting and setting formulas.
        Default value is false.'''
        raise NotImplementedError()
    
    @preserve_padding_spaces_in_formula.setter
    def preserve_padding_spaces_in_formula(self, value : bool) -> None:
        '''Indicates whether preserve those spaces and line breaks that are padded between formula tokens
        while getting and setting formulas.
        Default value is false.'''
        raise NotImplementedError()
    

