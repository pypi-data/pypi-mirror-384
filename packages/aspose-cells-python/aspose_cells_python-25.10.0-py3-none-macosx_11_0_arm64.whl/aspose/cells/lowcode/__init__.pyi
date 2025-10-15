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

class AbstractLowCodeLoadOptionsProvider:
    '''Implementation to provide multiple load options for processes
    that use multiple inputs(such as template files).'''
    
    def move_next(self) -> bool:
        '''Checks whether there is more input.'''
        raise NotImplementedError()
    
    def finish(self, part : aspose.cells.lowcode.LowCodeLoadOptions) -> None:
        '''Releases resources after processing currently part of input.
        
        :param part: the load options used for currently split part.'''
        raise NotImplementedError()
    
    @property
    def current(self) -> aspose.cells.lowcode.LowCodeLoadOptions:
        '''Gets the load options from which to load data of currently processed part.'''
        raise NotImplementedError()
    

class AbstractLowCodeProtectionProvider:
    '''Implementation to provide protection settings'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def get_open_password(self) -> str:
        '''Gets the password to open spread sheet file.
        
        :returns: Password to open spread sheet file. Empty means no protection for openning the filel.'''
        raise NotImplementedError()
    
    def get_write_password(self) -> str:
        '''Gets the password to modify spread sheet file.
        
        :returns: Password to modify the spread sheet file.
        Empty means no protection for modifying the file.'''
        raise NotImplementedError()
    
    def get_workbook_password(self) -> str:
        '''Gets the password to protect the workbook with specified protection type.
        
        :returns: Password to protect the workbook.'''
        raise NotImplementedError()
    
    def get_workbook_protection_type(self) -> aspose.cells.ProtectionType:
        '''Gets the protection type to protect the workbook.
        
        :returns: Protection type to protect the workbook.
        :py:attr:`aspose.cells.ProtectionType.NONE` means no protection for the workbook.'''
        raise NotImplementedError()
    
    def get_worksheet_password(self, sheet_name : str) -> str:
        '''Gets the password to protect the specified worksheet.
        
        :returns: Password to protect the specified worksheet.'''
        raise NotImplementedError()
    
    def get_worksheet_protection_type(self, sheet_name : str) -> aspose.cells.ProtectionType:
        '''Gets the protection type to protect the specified worksheet.
        
        :returns: Protection type to protect the specified worksheet.
        :py:attr:`aspose.cells.ProtectionType.NONE` means no protection for the worksheet.'''
        raise NotImplementedError()
    

class AbstractLowCodeSaveOptionsProvider:
    '''Implementation to provide multiple save options for processes
    that require multiple outputs. For example,
    :py:class:`aspose.cells.lowcode.SpreadsheetSplitter` feature requires multiple destinations
    to save the split files.'''
    
    def get_save_options(self, part : aspose.cells.lowcode.SplitPartInfo) -> aspose.cells.lowcode.LowCodeSaveOptions:
        '''Gets the save options from which to get the output settings for currently split part.
        Returning null denotes to skip given part.'''
        raise NotImplementedError()
    
    def finish(self, part : aspose.cells.lowcode.LowCodeSaveOptions) -> None:
        '''Releases resources after processing currently split part.
        
        :param part: the save options used for currently split part.'''
        raise NotImplementedError()
    

class HtmlConverter:
    '''Converter for conversion between html files(html or mht) and other spreadsheet file formats.'''
    
    @overload
    @staticmethod
    def process(template_file : str, result_file : str) -> None:
        '''Converts given template file between html and other formats.
        
        :param template_file: The template file to be converted
        :param result_file: The resultant file'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def process(load_options : aspose.cells.lowcode.LowCodeLoadOptions, save_options : aspose.cells.lowcode.LowCodeSaveOptions) -> None:
        '''Converts file between html and other spreadsheet file formats.
        
        :param load_options: Options for input and loading
        :param save_options: Options for output and saving'''
        raise NotImplementedError()
    

class ImageConverter:
    '''Converter for converting template file to images.'''
    
    @overload
    @staticmethod
    def process(template_file : str, result_file : str) -> None:
        '''Converts template file to images.
        
        :param template_file: The template file to be converted to images.
        :param result_file: The resultant file(name pattern) for generated images.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def process(load_options : aspose.cells.lowcode.LowCodeLoadOptions, save_options : aspose.cells.lowcode.LowCodeSaveOptions) -> None:
        '''Converts template file to images
        
        :param load_options: Options for input and loading
        :param save_options: Options for output and saving'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def process(load_options : aspose.cells.lowcode.LowCodeLoadOptions, save_options : aspose.cells.lowcode.LowCodeSaveOptions, provider : aspose.cells.lowcode.AbstractLowCodeSaveOptionsProvider) -> None:
        '''Converts template file to images
        
        :param load_options: Options for input and loading
        :param save_options: Options for saving.
        Its output(:py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_file` or :py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_stream`)
        takes no effect because all outputs will be specified by the "provider" parameter
        :param provider: Provider of save options for saving the generated images'''
        raise NotImplementedError()
    

class JsonConverter:
    '''Converter for conversion between json data structure and other spreadsheet file formats.'''
    
    @overload
    @staticmethod
    def process(template_file : str, result_file : str) -> None:
        '''Converts given template file between json and other formats.
        
        :param template_file: The template file to be converted
        :param result_file: The resultant file'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def process(load_options : aspose.cells.lowcode.LowCodeLoadOptions, save_options : aspose.cells.lowcode.LowCodeSaveOptions) -> None:
        '''Converts between json data and other spreadsheet file formats.
        
        :param load_options: Options for input and loading
        :param save_options: Options for output and saving'''
        raise NotImplementedError()
    

class LowCodeHtmlSaveOptions(LowCodeSaveOptions):
    '''Options for saving html in low code way.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def output_file(self) -> str:
        '''Gets and sets the file(with path if needed) for saving the generated data.
        When setting this property with value other than null or empty string, :py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_stream` will be ignored.'''
        raise NotImplementedError()
    
    @output_file.setter
    def output_file(self, value : str) -> None:
        '''Gets and sets the file(with path if needed) for saving the generated data.
        When setting this property with value other than null or empty string, :py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_stream` will be ignored.'''
        raise NotImplementedError()
    
    @property
    def output_stream(self) -> io._IOBase:
        '''Gets and sets the Stream for writing the generated data to.
        When setting this property with value other than null, :py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_file` will be ignored.'''
        raise NotImplementedError()
    
    @output_stream.setter
    def output_stream(self, value : io._IOBase) -> None:
        '''Gets and sets the Stream for writing the generated data to.
        When setting this property with value other than null, :py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_file` will be ignored.'''
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.cells.SaveFormat:
        '''Gets and sets the format of spreadsheet.'''
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.cells.SaveFormat) -> None:
        '''Gets and sets the format of spreadsheet.'''
        raise NotImplementedError()
    
    @property
    def html_options(self) -> aspose.cells.HtmlSaveOptions:
        '''The general options for saving html.'''
        raise NotImplementedError()
    
    @html_options.setter
    def html_options(self, value : aspose.cells.HtmlSaveOptions) -> None:
        '''The general options for saving html.'''
        raise NotImplementedError()
    

class LowCodeImageSaveOptions(LowCodeSaveOptions):
    '''Options for saving image in low code way.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def output_file(self) -> str:
        '''Gets and sets the file(with path if needed) for saving the generated data.
        When setting this property with value other than null or empty string, :py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_stream` will be ignored.'''
        raise NotImplementedError()
    
    @output_file.setter
    def output_file(self, value : str) -> None:
        '''Gets and sets the file(with path if needed) for saving the generated data.
        When setting this property with value other than null or empty string, :py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_stream` will be ignored.'''
        raise NotImplementedError()
    
    @property
    def output_stream(self) -> io._IOBase:
        '''Gets and sets the Stream for writing the generated data to.
        When setting this property with value other than null, :py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_file` will be ignored.'''
        raise NotImplementedError()
    
    @output_stream.setter
    def output_stream(self, value : io._IOBase) -> None:
        '''Gets and sets the Stream for writing the generated data to.
        When setting this property with value other than null, :py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_file` will be ignored.'''
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.cells.SaveFormat:
        '''Gets the save format.'''
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.cells.SaveFormat) -> None:
        '''Sets the save format.'''
        raise NotImplementedError()
    
    @property
    def image_options(self) -> aspose.cells.rendering.ImageOrPrintOptions:
        '''The options for rendering images.'''
        raise NotImplementedError()
    
    @image_options.setter
    def image_options(self, value : aspose.cells.rendering.ImageOrPrintOptions) -> None:
        '''The options for rendering images.'''
        raise NotImplementedError()
    
    @property
    def save_options_provider(self) -> aspose.cells.lowcode.AbstractLowCodeSaveOptionsProvider:
        '''Provider of save options for saving generated images.'''
        raise NotImplementedError()
    
    @save_options_provider.setter
    def save_options_provider(self, value : aspose.cells.lowcode.AbstractLowCodeSaveOptionsProvider) -> None:
        '''Provider of save options for saving generated images.'''
        raise NotImplementedError()
    

class LowCodeLoadOptions:
    '''Options for loading template file.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def input_file(self) -> str:
        '''Gets and sets the file(with path if needed) of the template.'''
        raise NotImplementedError()
    
    @input_file.setter
    def input_file(self, value : str) -> None:
        '''Gets and sets the file(with path if needed) of the template.'''
        raise NotImplementedError()
    
    @property
    def input_stream(self) -> io._IOBase:
        '''Gets and sets the Stream of the template.'''
        raise NotImplementedError()
    
    @input_stream.setter
    def input_stream(self, value : io._IOBase) -> None:
        '''Gets and sets the Stream of the template.'''
        raise NotImplementedError()
    

class LowCodeMergeOptions:
    '''Options for merging multiple template files into one.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def save_options(self) -> aspose.cells.lowcode.LowCodeSaveOptions:
        '''Save options for saving the split parts.'''
        raise NotImplementedError()
    
    @save_options.setter
    def save_options(self, value : aspose.cells.lowcode.LowCodeSaveOptions) -> None:
        '''Save options for saving the split parts.'''
        raise NotImplementedError()
    
    @property
    def load_options_provider(self) -> aspose.cells.lowcode.AbstractLowCodeLoadOptionsProvider:
        '''Provider of save options for saving the split parts.'''
        raise NotImplementedError()
    
    @load_options_provider.setter
    def load_options_provider(self, value : aspose.cells.lowcode.AbstractLowCodeLoadOptionsProvider) -> None:
        '''Provider of save options for saving the split parts.'''
        raise NotImplementedError()
    

class LowCodePdfSaveOptions(LowCodeSaveOptions):
    '''Options for saving pdf in low code way.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def output_file(self) -> str:
        '''Gets and sets the file(with path if needed) for saving the generated data.
        When setting this property with value other than null or empty string, :py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_stream` will be ignored.'''
        raise NotImplementedError()
    
    @output_file.setter
    def output_file(self, value : str) -> None:
        '''Gets and sets the file(with path if needed) for saving the generated data.
        When setting this property with value other than null or empty string, :py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_stream` will be ignored.'''
        raise NotImplementedError()
    
    @property
    def output_stream(self) -> io._IOBase:
        '''Gets and sets the Stream for writing the generated data to.
        When setting this property with value other than null, :py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_file` will be ignored.'''
        raise NotImplementedError()
    
    @output_stream.setter
    def output_stream(self, value : io._IOBase) -> None:
        '''Gets and sets the Stream for writing the generated data to.
        When setting this property with value other than null, :py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_file` will be ignored.'''
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.cells.SaveFormat:
        '''The save format for the output.
        For converting to pdf, it can only be :py:attr:`aspose.cells.SaveFormat.PDF`.'''
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.cells.SaveFormat) -> None:
        '''The save format for the output.
        For converting to pdf, it can only be :py:attr:`aspose.cells.SaveFormat.PDF`.'''
        raise NotImplementedError()
    
    @property
    def pdf_options(self) -> aspose.cells.PdfSaveOptions:
        '''The options for saving Pdf file.'''
        raise NotImplementedError()
    
    @pdf_options.setter
    def pdf_options(self, value : aspose.cells.PdfSaveOptions) -> None:
        '''The options for saving Pdf file.'''
        raise NotImplementedError()
    

class LowCodeSaveOptions:
    '''Options for saving generated results in low code way.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def output_file(self) -> str:
        '''Gets and sets the file(with path if needed) for saving the generated data.
        When setting this property with value other than null or empty string, :py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_stream` will be ignored.'''
        raise NotImplementedError()
    
    @output_file.setter
    def output_file(self, value : str) -> None:
        '''Gets and sets the file(with path if needed) for saving the generated data.
        When setting this property with value other than null or empty string, :py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_stream` will be ignored.'''
        raise NotImplementedError()
    
    @property
    def output_stream(self) -> io._IOBase:
        '''Gets and sets the Stream for writing the generated data to.
        When setting this property with value other than null, :py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_file` will be ignored.'''
        raise NotImplementedError()
    
    @output_stream.setter
    def output_stream(self, value : io._IOBase) -> None:
        '''Gets and sets the Stream for writing the generated data to.
        When setting this property with value other than null, :py:attr:`aspose.cells.lowcode.LowCodeSaveOptions.output_file` will be ignored.'''
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.cells.SaveFormat:
        '''Gets and sets the save format for the output.
        Generally, for specific process in low code way, only some specific formats are allowed.
        Please specify the correct format for corresponding process, otherwise unexpected result
        or even exception may be caused.'''
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.cells.SaveFormat) -> None:
        '''Gets and sets the save format for the output.
        Generally, for specific process in low code way, only some specific formats are allowed.
        Please specify the correct format for corresponding process, otherwise unexpected result
        or even exception may be caused.'''
        raise NotImplementedError()
    

class LowCodeSaveOptionsProviderOfAssembling(AbstractLowCodeSaveOptionsProvider):
    '''Implementation to provide save options which save split parts to files
    and the path of resultant file are named as(it may contains directories):
    :py:attr:`aspose.cells.lowcode.LowCodeSaveOptionsProviderOfAssembling.path_header`+:py:attr:`aspose.cells.lowcode.LowCodeSaveOptionsProviderOfAssembling.sheet_prefix`+SheetIndex(or SheetName)
    +:py:attr:`aspose.cells.lowcode.LowCodeSaveOptionsProviderOfAssembling.split_part_prefix`+SplitPartIndex+:py:attr:`aspose.cells.lowcode.LowCodeSaveOptionsProviderOfAssembling.path_tail`.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def get_save_options(self, part : aspose.cells.lowcode.SplitPartInfo) -> aspose.cells.lowcode.LowCodeSaveOptions:
        '''Gets the save options from which to get the output settings for currently split part.'''
        raise NotImplementedError()
    
    def finish(self, part : aspose.cells.lowcode.LowCodeSaveOptions) -> None:
        '''Releases resources after processing currently split part.
        
        :param part: the save options used for currently split part.'''
        raise NotImplementedError()
    
    @property
    def path_header(self) -> str:
        '''Header part(before added content of sheet and split part) of file path.'''
        raise NotImplementedError()
    
    @path_header.setter
    def path_header(self, value : str) -> None:
        '''Header part(before added content of sheet and split part) of file path.'''
        raise NotImplementedError()
    
    @property
    def path_tail(self) -> str:
        '''Tailing part(after sequence numbers) of file path.
        It should include extension of file name.'''
        raise NotImplementedError()
    
    @path_tail.setter
    def path_tail(self, value : str) -> None:
        '''Tailing part(after sequence numbers) of file path.
        It should include extension of file name.'''
        raise NotImplementedError()
    
    @property
    def use_sheet_name(self) -> bool:
        '''Whether builds the file path with sheet name instead of sheet index. Default value is false.'''
        raise NotImplementedError()
    
    @use_sheet_name.setter
    def use_sheet_name(self, value : bool) -> None:
        '''Whether builds the file path with sheet name instead of sheet index. Default value is false.'''
        raise NotImplementedError()
    
    @property
    def sheet_prefix(self) -> str:
        '''Prefix for the index of worksheet.'''
        raise NotImplementedError()
    
    @sheet_prefix.setter
    def sheet_prefix(self, value : str) -> None:
        '''Prefix for the index of worksheet.'''
        raise NotImplementedError()
    
    @property
    def split_part_prefix(self) -> str:
        '''Prefix for the index of split part.'''
        raise NotImplementedError()
    
    @split_part_prefix.setter
    def split_part_prefix(self, value : str) -> None:
        '''Prefix for the index of split part.'''
        raise NotImplementedError()
    
    @property
    def sheet_index_offset(self) -> int:
        '''Offset of sheet\'s index between what used in file path
        and its actual value(:py:attr:`aspose.cells.lowcode.SplitPartInfo.sheet_index`).'''
        raise NotImplementedError()
    
    @sheet_index_offset.setter
    def sheet_index_offset(self, value : int) -> None:
        '''Offset of sheet\'s index between what used in file path
        and its actual value(:py:attr:`aspose.cells.lowcode.SplitPartInfo.sheet_index`).'''
        raise NotImplementedError()
    
    @property
    def split_part_index_offset(self) -> int:
        '''Offset of split part\'s index between what used in file path
        and its actual value(:py:attr:`aspose.cells.lowcode.SplitPartInfo.part_index`).'''
        raise NotImplementedError()
    
    @split_part_index_offset.setter
    def split_part_index_offset(self, value : int) -> None:
        '''Offset of split part\'s index between what used in file path
        and its actual value(:py:attr:`aspose.cells.lowcode.SplitPartInfo.part_index`).'''
        raise NotImplementedError()
    
    @property
    def build_path_with_sheet_always(self) -> bool:
        '''Whether add sheet index or name to file path always.
        Default value is false, that is, when there is only one sheet,
        the sheet index(or name) and corresponding prefix will not be added to the file path.'''
        raise NotImplementedError()
    
    @build_path_with_sheet_always.setter
    def build_path_with_sheet_always(self, value : bool) -> None:
        '''Whether add sheet index or name to file path always.
        Default value is false, that is, when there is only one sheet,
        the sheet index(or name) and corresponding prefix will not be added to the file path.'''
        raise NotImplementedError()
    
    @property
    def build_path_with_split_part_always(self) -> bool:
        '''Whether add split part index to file path always.
        Default value is false, that is, when there is only one split part,
        the split part index and corresponding prefix will not be added to the file path.'''
        raise NotImplementedError()
    
    @build_path_with_split_part_always.setter
    def build_path_with_split_part_always(self, value : bool) -> None:
        '''Whether add split part index to file path always.
        Default value is false, that is, when there is only one split part,
        the split part index and corresponding prefix will not be added to the file path.'''
        raise NotImplementedError()
    
    @property
    def save_options_template(self) -> aspose.cells.lowcode.LowCodeSaveOptions:
        '''The template for creating instance of save options in :py:func:`aspose.cells.lowcode.LowCodeSaveOptionsProviderOfAssembling.get_save_options`.'''
        raise NotImplementedError()
    
    @save_options_template.setter
    def save_options_template(self, value : aspose.cells.lowcode.LowCodeSaveOptions) -> None:
        '''The template for creating instance of save options in :py:func:`aspose.cells.lowcode.LowCodeSaveOptionsProviderOfAssembling.get_save_options`.'''
        raise NotImplementedError()
    

class LowCodeSaveOptionsProviderOfPlaceHolders(AbstractLowCodeSaveOptionsProvider):
    '''Implementation to provide save options which save split parts to files
    and the path of resultant file are defined with placeholders.'''
    
    def __init__(self, path_template : str) -> None:
        '''Instantiates an instance to provide save options according to specified templates.
        
        :param path_template: The template of the resultant file path.'''
        raise NotImplementedError()
    
    def get_save_options(self, part : aspose.cells.lowcode.SplitPartInfo) -> aspose.cells.lowcode.LowCodeSaveOptions:
        '''Gets the save options from which to get the output settings for currently split part.'''
        raise NotImplementedError()
    
    def finish(self, part : aspose.cells.lowcode.LowCodeSaveOptions) -> None:
        '''Releases resources after processing currently split part.
        
        :param part: the save options used for currently split part.'''
        raise NotImplementedError()
    
    @property
    def sheet_index_offset(self) -> int:
        '''Offset of sheet\'s index between what used in file path
        and its actual value(:py:attr:`aspose.cells.lowcode.SplitPartInfo.sheet_index`).'''
        raise NotImplementedError()
    
    @sheet_index_offset.setter
    def sheet_index_offset(self, value : int) -> None:
        '''Offset of sheet\'s index between what used in file path
        and its actual value(:py:attr:`aspose.cells.lowcode.SplitPartInfo.sheet_index`).'''
        raise NotImplementedError()
    
    @property
    def split_part_index_offset(self) -> int:
        '''Offset of split part\'s index between what used in file path
        and its actual value(:py:attr:`aspose.cells.lowcode.SplitPartInfo.part_index`).'''
        raise NotImplementedError()
    
    @split_part_index_offset.setter
    def split_part_index_offset(self, value : int) -> None:
        '''Offset of split part\'s index between what used in file path
        and its actual value(:py:attr:`aspose.cells.lowcode.SplitPartInfo.part_index`).'''
        raise NotImplementedError()
    
    @property
    def build_path_with_sheet_always(self) -> bool:
        '''Whether add sheet index or name to file path always.
        Default value is false, that is, when there is only one sheet,
        the sheet index and name and corresponding prefix(:py:attr:`aspose.cells.lowcode.LowCodeSaveOptionsProviderOfPlaceHolders.sheet_name_prefix`)
        will not be added to the file path.'''
        raise NotImplementedError()
    
    @build_path_with_sheet_always.setter
    def build_path_with_sheet_always(self, value : bool) -> None:
        '''Whether add sheet index or name to file path always.
        Default value is false, that is, when there is only one sheet,
        the sheet index and name and corresponding prefix(:py:attr:`aspose.cells.lowcode.LowCodeSaveOptionsProviderOfPlaceHolders.sheet_name_prefix`)
        will not be added to the file path.'''
        raise NotImplementedError()
    
    @property
    def build_path_with_split_part_always(self) -> bool:
        '''Whether add split part index to file path always.
        Default value is false, that is, when there is only one split part,
        the split part index and corresponding prefix(:py:attr:`aspose.cells.lowcode.LowCodeSaveOptionsProviderOfPlaceHolders.split_part_prefix`)
        will not be added to the file path.'''
        raise NotImplementedError()
    
    @build_path_with_split_part_always.setter
    def build_path_with_split_part_always(self, value : bool) -> None:
        '''Whether add split part index to file path always.
        Default value is false, that is, when there is only one split part,
        the split part index and corresponding prefix(:py:attr:`aspose.cells.lowcode.LowCodeSaveOptionsProviderOfPlaceHolders.split_part_prefix`)
        will not be added to the file path.'''
        raise NotImplementedError()
    
    @property
    def sheet_name_prefix(self) -> str:
        '''Prefix for the index of worksheet.'''
        raise NotImplementedError()
    
    @sheet_name_prefix.setter
    def sheet_name_prefix(self, value : str) -> None:
        '''Prefix for the index of worksheet.'''
        raise NotImplementedError()
    
    @property
    def sheet_index_prefix(self) -> str:
        '''Prefix for the index of worksheet.'''
        raise NotImplementedError()
    
    @sheet_index_prefix.setter
    def sheet_index_prefix(self, value : str) -> None:
        '''Prefix for the index of worksheet.'''
        raise NotImplementedError()
    
    @property
    def split_part_prefix(self) -> str:
        '''Prefix for the index of split part.'''
        raise NotImplementedError()
    
    @split_part_prefix.setter
    def split_part_prefix(self, value : str) -> None:
        '''Prefix for the index of split part.'''
        raise NotImplementedError()
    
    @property
    def save_options_template(self) -> aspose.cells.lowcode.LowCodeSaveOptions:
        '''The template for creating instance of save options in :py:func:`aspose.cells.lowcode.LowCodeSaveOptionsProviderOfPlaceHolders.get_save_options`.'''
        raise NotImplementedError()
    
    @save_options_template.setter
    def save_options_template(self, value : aspose.cells.lowcode.LowCodeSaveOptions) -> None:
        '''The template for creating instance of save options in :py:func:`aspose.cells.lowcode.LowCodeSaveOptionsProviderOfPlaceHolders.get_save_options`.'''
        raise NotImplementedError()
    

class LowCodeSplitOptions:
    '''Options for splitting spreadsheet.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def load_options(self) -> aspose.cells.lowcode.LowCodeLoadOptions:
        '''Load options for loading the spreadsheet that will be split.'''
        raise NotImplementedError()
    
    @load_options.setter
    def load_options(self, value : aspose.cells.lowcode.LowCodeLoadOptions) -> None:
        '''Load options for loading the spreadsheet that will be split.'''
        raise NotImplementedError()
    
    @property
    def save_options(self) -> aspose.cells.lowcode.LowCodeSaveOptions:
        '''Save options for saving the split parts.'''
        raise NotImplementedError()
    
    @save_options.setter
    def save_options(self, value : aspose.cells.lowcode.LowCodeSaveOptions) -> None:
        '''Save options for saving the split parts.'''
        raise NotImplementedError()
    
    @property
    def save_options_provider(self) -> aspose.cells.lowcode.AbstractLowCodeSaveOptionsProvider:
        '''Provider of save options for saving the split parts.'''
        raise NotImplementedError()
    
    @save_options_provider.setter
    def save_options_provider(self, value : aspose.cells.lowcode.AbstractLowCodeSaveOptionsProvider) -> None:
        '''Provider of save options for saving the split parts.'''
        raise NotImplementedError()
    

class PdfConverter:
    '''Converter for converting template file to pdf.'''
    
    @overload
    @staticmethod
    def process(template_file : str, result_file : str) -> None:
        '''Converts given template file to pdf.
        
        :param template_file: The template file to be converted
        :param result_file: The resultant file, it must be pdf file.'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def process(load_options : aspose.cells.lowcode.LowCodeLoadOptions, save_options : aspose.cells.lowcode.LowCodeSaveOptions) -> None:
        '''Converts template file to pdf
        
        :param load_options: Options for input and loading
        :param save_options: Options for output and saving'''
        raise NotImplementedError()
    

class SplitPartInfo:
    '''Represents the information of one input/output for multiple inputs/outputs,
    such as current page to be rendered when converting spreadsheet to image.'''
    
    @property
    def part_index(self) -> int:
        '''Index of current part in sequence(0 based).
        -1 means there are no multiple parts so the result is single.'''
        raise NotImplementedError()
    
    @property
    def sheet_index(self) -> int:
        '''Index of the sheet where current part is in. -1 denotes there is only one sheet.'''
        raise NotImplementedError()
    
    @property
    def sheet_name(self) -> str:
        '''Name of the sheet where current part is in.'''
        raise NotImplementedError()
    

class SpreadsheetConverter:
    '''Converter for conversion between different spreadsheet file formats, such as xls, xlsx, xlsb, spreadsheet ml...'''
    
    @overload
    @staticmethod
    def process(template_file : str, result_file : str) -> None:
        '''Converts given template file between spreadsheet file formats.
        
        :param template_file: The template file to be converted
        :param result_file: The resultant file'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def process(load_options : aspose.cells.lowcode.LowCodeLoadOptions, save_options : aspose.cells.lowcode.LowCodeSaveOptions) -> None:
        '''Converts between different spreadsheet file formats.
        
        :param load_options: Options for input and loading
        :param save_options: Options for output and saving'''
        raise NotImplementedError()
    

class SpreadsheetLocker:
    '''Low code api to lock spreadsheet file.'''
    
    @overload
    @staticmethod
    def process(template_file : str, result_file : str, open_password : str, write_password : str) -> None:
        '''Locks spreadsheet file with specified settings.
        
        :param template_file: The template file to be locked
        :param result_file: The resultant file
        :param open_password: Password for file encryption
        :param write_password: Password for protection of modifying spreadsheet'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def process(load_options : aspose.cells.lowcode.LowCodeLoadOptions, save_options : aspose.cells.lowcode.LowCodeSaveOptions, open_password : str, write_password : str) -> None:
        '''Locks spreadsheet file with specified settings.
        
        :param load_options: Options for input and loading
        :param save_options: Options for output and saving
        :param open_password: Password for file encryption
        :param write_password: Password for protection of modifying spreadsheet'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def process(load_options : aspose.cells.lowcode.LowCodeLoadOptions, save_options : aspose.cells.lowcode.LowCodeSaveOptions, open_password : str, write_password : str, workbook_password : str, workbook_type : aspose.cells.ProtectionType) -> None:
        '''Locks spreadsheet file with specified settings.
        
        :param load_options: Options for input and loading
        :param save_options: Options for output and saving
        :param open_password: Password for file encryption
        :param write_password: Password for protection of modifying spreadsheet
        :param workbook_password: Password for protection of the workbook
        :param workbook_type: Protection type to protect the workbook'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def process(load_options : aspose.cells.lowcode.LowCodeLoadOptions, save_options : aspose.cells.lowcode.LowCodeSaveOptions, provider : aspose.cells.lowcode.AbstractLowCodeProtectionProvider) -> None:
        '''Locks spreadsheet file with specified settings.
        
        :param load_options: Options for input and loading
        :param save_options: Options for output and saving
        :param provider: Implementation to provide protections settings'''
        raise NotImplementedError()
    

class SpreadsheetMerger:
    '''Merges multiple template files into one.'''
    
    @overload
    @staticmethod
    def process(template_files : List[str], result_file : str) -> None:
        '''Merge given template files.
        
        :param template_files: The template files to be merged
        :param result_file: The resultant file'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def process(options : aspose.cells.lowcode.LowCodeMergeOptions) -> None:
        '''Merges multiple template files into one.
        
        :param options: Options for merging files'''
        raise NotImplementedError()
    

class SpreadsheetSplitter:
    '''Splits spreadsheet file into multiple parts.'''
    
    @overload
    @staticmethod
    def process(template_file : str, result_file : str) -> None:
        '''Splits given template file into multiple parts.
        
        :param template_file: The template file to be split
        :param result_file: The resultant file(name pattern)'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def process(options : aspose.cells.lowcode.LowCodeSplitOptions) -> None:
        '''Splits spreadsheet file into multiple parts.
        
        :param options: Options for splitting spreadsheet'''
        raise NotImplementedError()
    

class TextConverter:
    '''Converter for conversion between text based formats(csv, tsv, dif...) and other spreadsheet file formats.'''
    
    @overload
    @staticmethod
    def process(template_file : str, result_file : str) -> None:
        '''Converts given template file between text based files and other formats.
        
        :param template_file: The template file to be converted
        :param result_file: The resultant file'''
        raise NotImplementedError()
    
    @overload
    @staticmethod
    def process(load_options : aspose.cells.lowcode.LowCodeLoadOptions, save_options : aspose.cells.lowcode.LowCodeSaveOptions) -> None:
        '''Converts file format between text based formats and other spreadsheet file formats
        
        :param load_options: Options for input and loading
        :param save_options: Options for output and saving'''
        raise NotImplementedError()
    

