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

class DbfSaveOptions(aspose.cells.SaveOptions):
    '''Represents the options of saving dbf file'''
    
    def __init__(self) -> None:
        '''The options of saving .dbf file.'''
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.cells.SaveFormat:
        '''Gets the save file format.'''
        raise NotImplementedError()
    
    @property
    def clear_data(self) -> bool:
        '''Make the workbook empty after saving the file.'''
        raise NotImplementedError()
    
    @clear_data.setter
    def clear_data(self, value : bool) -> None:
        '''Make the workbook empty after saving the file.'''
        raise NotImplementedError()
    
    @property
    def cached_file_folder(self) -> str:
        '''The folder for temporary files that may be used as data cache.'''
        raise NotImplementedError()
    
    @cached_file_folder.setter
    def cached_file_folder(self, value : str) -> None:
        '''The folder for temporary files that may be used as data cache.'''
        raise NotImplementedError()
    
    @property
    def validate_merged_areas(self) -> bool:
        '''Indicates whether validate merged cells before saving the file.'''
        raise NotImplementedError()
    
    @validate_merged_areas.setter
    def validate_merged_areas(self, value : bool) -> None:
        '''Indicates whether validate merged cells before saving the file.'''
        raise NotImplementedError()
    
    @property
    def merge_areas(self) -> bool:
        '''Indicates whether merge the areas of conditional formatting and validation before saving the file.'''
        raise NotImplementedError()
    
    @merge_areas.setter
    def merge_areas(self, value : bool) -> None:
        '''Indicates whether merge the areas of conditional formatting and validation before saving the file.'''
        raise NotImplementedError()
    
    @property
    def create_directory(self) -> bool:
        '''If true and the directory does not exist, the directory will be automatically created before saving the file.'''
        raise NotImplementedError()
    
    @create_directory.setter
    def create_directory(self, value : bool) -> None:
        '''If true and the directory does not exist, the directory will be automatically created before saving the file.'''
        raise NotImplementedError()
    
    @property
    def sort_names(self) -> bool:
        '''Indicates whether sorting defined names before saving file.'''
        raise NotImplementedError()
    
    @sort_names.setter
    def sort_names(self, value : bool) -> None:
        '''Indicates whether sorting defined names before saving file.'''
        raise NotImplementedError()
    
    @property
    def sort_external_names(self) -> bool:
        '''Indicates whether sorting external defined names before saving file.'''
        raise NotImplementedError()
    
    @sort_external_names.setter
    def sort_external_names(self, value : bool) -> None:
        '''Indicates whether sorting external defined names before saving file.'''
        raise NotImplementedError()
    
    @property
    def refresh_chart_cache(self) -> bool:
        '''Indicates whether refreshing chart cache data'''
        raise NotImplementedError()
    
    @refresh_chart_cache.setter
    def refresh_chart_cache(self, value : bool) -> None:
        '''Indicates whether refreshing chart cache data'''
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
    def check_excel_restriction(self) -> bool:
        '''Whether check restriction of excel file when user modify cells related objects.
        For example, excel does not allow inputting string value longer than 32K.
        When you input a value longer than 32K, it will be truncated.'''
        raise NotImplementedError()
    
    @check_excel_restriction.setter
    def check_excel_restriction(self, value : bool) -> None:
        '''Whether check restriction of excel file when user modify cells related objects.
        For example, excel does not allow inputting string value longer than 32K.
        When you input a value longer than 32K, it will be truncated.'''
        raise NotImplementedError()
    
    @property
    def update_smart_art(self) -> bool:
        '''Indicates whether updating smart art setting.
        The default value is false.'''
        raise NotImplementedError()
    
    @update_smart_art.setter
    def update_smart_art(self, value : bool) -> None:
        '''Indicates whether updating smart art setting.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def encrypt_document_properties(self) -> bool:
        '''Indicates whether encrypt document properties when saving as .xls file.
        The default value is true.'''
        raise NotImplementedError()
    
    @encrypt_document_properties.setter
    def encrypt_document_properties(self, value : bool) -> None:
        '''Indicates whether encrypt document properties when saving as .xls file.
        The default value is true.'''
        raise NotImplementedError()
    
    @property
    def export_as_string(self) -> bool:
        '''Indicates whether exporting as string value'''
        raise NotImplementedError()
    
    @export_as_string.setter
    def export_as_string(self, value : bool) -> None:
        '''Indicates whether exporting as string value'''
        raise NotImplementedError()
    

class EbookSaveOptions(aspose.cells.HtmlSaveOptions):
    '''Represents the options for saving ebook file.'''
    
    @overload
    def __init__(self) -> None:
        '''Creates options for saving ebook file.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, save_format : aspose.cells.SaveFormat) -> None:
        '''Creates options for saving ebook file.
        
        :param save_format: The file format.
        It should be :py:attr:`aspose.cells.SaveFormat.EPUB` or :py:attr:`aspose.cells.SaveFormat.AZW3`.'''
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.cells.SaveFormat:
        '''Gets the save file format.'''
        raise NotImplementedError()
    
    @property
    def clear_data(self) -> bool:
        '''Make the workbook empty after saving the file.'''
        raise NotImplementedError()
    
    @clear_data.setter
    def clear_data(self, value : bool) -> None:
        '''Make the workbook empty after saving the file.'''
        raise NotImplementedError()
    
    @property
    def cached_file_folder(self) -> str:
        '''The folder for temporary files that may be used as data cache.'''
        raise NotImplementedError()
    
    @cached_file_folder.setter
    def cached_file_folder(self, value : str) -> None:
        '''The folder for temporary files that may be used as data cache.'''
        raise NotImplementedError()
    
    @property
    def validate_merged_areas(self) -> bool:
        '''Indicates whether validate merged cells before saving the file.'''
        raise NotImplementedError()
    
    @validate_merged_areas.setter
    def validate_merged_areas(self, value : bool) -> None:
        '''Indicates whether validate merged cells before saving the file.'''
        raise NotImplementedError()
    
    @property
    def merge_areas(self) -> bool:
        '''Indicates whether merge the areas of conditional formatting and validation before saving the file.'''
        raise NotImplementedError()
    
    @merge_areas.setter
    def merge_areas(self, value : bool) -> None:
        '''Indicates whether merge the areas of conditional formatting and validation before saving the file.'''
        raise NotImplementedError()
    
    @property
    def create_directory(self) -> bool:
        '''If true and the directory does not exist, the directory will be automatically created before saving the file.'''
        raise NotImplementedError()
    
    @create_directory.setter
    def create_directory(self, value : bool) -> None:
        '''If true and the directory does not exist, the directory will be automatically created before saving the file.'''
        raise NotImplementedError()
    
    @property
    def sort_names(self) -> bool:
        '''Indicates whether sorting defined names before saving file.'''
        raise NotImplementedError()
    
    @sort_names.setter
    def sort_names(self, value : bool) -> None:
        '''Indicates whether sorting defined names before saving file.'''
        raise NotImplementedError()
    
    @property
    def sort_external_names(self) -> bool:
        '''Indicates whether sorting external defined names before saving file.'''
        raise NotImplementedError()
    
    @sort_external_names.setter
    def sort_external_names(self, value : bool) -> None:
        '''Indicates whether sorting external defined names before saving file.'''
        raise NotImplementedError()
    
    @property
    def refresh_chart_cache(self) -> bool:
        '''Indicates whether refreshing chart cache data'''
        raise NotImplementedError()
    
    @refresh_chart_cache.setter
    def refresh_chart_cache(self, value : bool) -> None:
        '''Indicates whether refreshing chart cache data'''
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
    def check_excel_restriction(self) -> bool:
        '''Whether check restriction of excel file when user modify cells related objects.
        For example, excel does not allow inputting string value longer than 32K.
        When you input a value longer than 32K, it will be truncated.'''
        raise NotImplementedError()
    
    @check_excel_restriction.setter
    def check_excel_restriction(self, value : bool) -> None:
        '''Whether check restriction of excel file when user modify cells related objects.
        For example, excel does not allow inputting string value longer than 32K.
        When you input a value longer than 32K, it will be truncated.'''
        raise NotImplementedError()
    
    @property
    def update_smart_art(self) -> bool:
        '''Indicates whether updating smart art setting.
        The default value is false.'''
        raise NotImplementedError()
    
    @update_smart_art.setter
    def update_smart_art(self, value : bool) -> None:
        '''Indicates whether updating smart art setting.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def encrypt_document_properties(self) -> bool:
        '''Indicates whether encrypt document properties when saving as .xls file.
        The default value is true.'''
        raise NotImplementedError()
    
    @encrypt_document_properties.setter
    def encrypt_document_properties(self, value : bool) -> None:
        '''Indicates whether encrypt document properties when saving as .xls file.
        The default value is true.'''
        raise NotImplementedError()
    
    @property
    def ignore_invisible_shapes(self) -> bool:
        '''Indicate whether exporting those not visible shapes'''
        raise NotImplementedError()
    
    @ignore_invisible_shapes.setter
    def ignore_invisible_shapes(self, value : bool) -> None:
        '''Indicate whether exporting those not visible shapes'''
        raise NotImplementedError()
    
    @property
    def page_title(self) -> str:
        '''The title of the html page.
        Only for saving to html stream.'''
        raise NotImplementedError()
    
    @page_title.setter
    def page_title(self, value : str) -> None:
        '''The title of the html page.
        Only for saving to html stream.'''
        raise NotImplementedError()
    
    @property
    def attached_files_directory(self) -> str:
        '''The directory that the attached files will be saved to.
        Only for saving to html stream.'''
        raise NotImplementedError()
    
    @attached_files_directory.setter
    def attached_files_directory(self, value : str) -> None:
        '''The directory that the attached files will be saved to.
        Only for saving to html stream.'''
        raise NotImplementedError()
    
    @property
    def attached_files_url_prefix(self) -> str:
        '''Specify the Url prefix of attached files such as image in the html file.
        Only for saving to html stream.'''
        raise NotImplementedError()
    
    @attached_files_url_prefix.setter
    def attached_files_url_prefix(self, value : str) -> None:
        '''Specify the Url prefix of attached files such as image in the html file.
        Only for saving to html stream.'''
        raise NotImplementedError()
    
    @property
    def default_font_name(self) -> str:
        '''Specify the default font name for exporting html, the default font will be used  when the font of style is not existing,
        If this property is null, Aspose.Cells will use universal font which have the same family with the original font,
        the default value is null.'''
        raise NotImplementedError()
    
    @default_font_name.setter
    def default_font_name(self, value : str) -> None:
        '''Specify the default font name for exporting html, the default font will be used  when the font of style is not existing,
        If this property is null, Aspose.Cells will use universal font which have the same family with the original font,
        the default value is null.'''
        raise NotImplementedError()
    
    @property
    def add_generic_font(self) -> bool:
        '''Indicates whether to add a generic font to CSS font-family.
        The default value is true'''
        raise NotImplementedError()
    
    @add_generic_font.setter
    def add_generic_font(self, value : bool) -> None:
        '''Indicates whether to add a generic font to CSS font-family.
        The default value is true'''
        raise NotImplementedError()
    
    @property
    def worksheet_scalable(self) -> bool:
        '''Indicates if zooming in or out the html via worksheet zoom level when saving file to html, the default value is false.'''
        raise NotImplementedError()
    
    @worksheet_scalable.setter
    def worksheet_scalable(self, value : bool) -> None:
        '''Indicates if zooming in or out the html via worksheet zoom level when saving file to html, the default value is false.'''
        raise NotImplementedError()
    
    @property
    def is_export_comments(self) -> bool:
        '''Indicates if exporting comments when saving file to html, the default value is false.'''
        raise NotImplementedError()
    
    @is_export_comments.setter
    def is_export_comments(self, value : bool) -> None:
        '''Indicates if exporting comments when saving file to html, the default value is false.'''
        raise NotImplementedError()
    
    @property
    def export_comments_type(self) -> aspose.cells.PrintCommentsType:
        '''Represents type of exporting comments to html files.'''
        raise NotImplementedError()
    
    @export_comments_type.setter
    def export_comments_type(self, value : aspose.cells.PrintCommentsType) -> None:
        '''Represents type of exporting comments to html files.'''
        raise NotImplementedError()
    
    @property
    def disable_downlevel_revealed_comments(self) -> bool:
        '''Indicates if disable Downlevel-revealed conditional comments when exporting file to html, the default value is false.'''
        raise NotImplementedError()
    
    @disable_downlevel_revealed_comments.setter
    def disable_downlevel_revealed_comments(self, value : bool) -> None:
        '''Indicates if disable Downlevel-revealed conditional comments when exporting file to html, the default value is false.'''
        raise NotImplementedError()
    
    @property
    def is_exp_image_to_temp_dir(self) -> bool:
        '''Indicates whether exporting image files to temp directory.
        Only for saving to html stream.'''
        raise NotImplementedError()
    
    @is_exp_image_to_temp_dir.setter
    def is_exp_image_to_temp_dir(self, value : bool) -> None:
        '''Indicates whether exporting image files to temp directory.
        Only for saving to html stream.'''
        raise NotImplementedError()
    
    @property
    def image_scalable(self) -> bool:
        '''Indicates whether using scalable unit to describe the image width
        when using scalable unit to describe the column width.
        The default value is true.'''
        raise NotImplementedError()
    
    @image_scalable.setter
    def image_scalable(self, value : bool) -> None:
        '''Indicates whether using scalable unit to describe the image width
        when using scalable unit to describe the column width.
        The default value is true.'''
        raise NotImplementedError()
    
    @property
    def width_scalable(self) -> bool:
        '''Indicates whether exporting column width in unit of scale to html.
        The default value is false.'''
        raise NotImplementedError()
    
    @width_scalable.setter
    def width_scalable(self, value : bool) -> None:
        '''Indicates whether exporting column width in unit of scale to html.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def export_single_tab(self) -> bool:
        '''Indicates whether exporting the single tab when the file only has one worksheet.
        The default value is false.'''
        raise NotImplementedError()
    
    @export_single_tab.setter
    def export_single_tab(self, value : bool) -> None:
        '''Indicates whether exporting the single tab when the file only has one worksheet.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def export_images_as_base64(self) -> bool:
        '''Specifies whether images are saved in Base64 format to HTML, MHTML or EPUB.'''
        raise NotImplementedError()
    
    @export_images_as_base64.setter
    def export_images_as_base64(self, value : bool) -> None:
        '''Specifies whether images are saved in Base64 format to HTML, MHTML or EPUB.'''
        raise NotImplementedError()
    
    @property
    def export_active_worksheet_only(self) -> bool:
        '''Indicates if only exporting the active worksheet to html file.
        If true then only the active worksheet will be exported to html file;
        If false then the whole workbook will be exported to html file.
        The default value is false.'''
        raise NotImplementedError()
    
    @export_active_worksheet_only.setter
    def export_active_worksheet_only(self, value : bool) -> None:
        '''Indicates if only exporting the active worksheet to html file.
        If true then only the active worksheet will be exported to html file;
        If false then the whole workbook will be exported to html file.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def export_print_area_only(self) -> bool:
        '''Indicates if only exporting the print area to html file. The default value is false.'''
        raise NotImplementedError()
    
    @export_print_area_only.setter
    def export_print_area_only(self, value : bool) -> None:
        '''Indicates if only exporting the print area to html file. The default value is false.'''
        raise NotImplementedError()
    
    @property
    def export_area(self) -> aspose.cells.CellArea:
        '''Gets or Sets the exporting CellArea of current active Worksheet.
        If you set this attribute, the print area of current active Worksheet will be omitted.
        Only the specified area will be exported when saving the file to html.'''
        raise NotImplementedError()
    
    @export_area.setter
    def export_area(self, value : aspose.cells.CellArea) -> None:
        '''Gets or Sets the exporting CellArea of current active Worksheet.
        If you set this attribute, the print area of current active Worksheet will be omitted.
        Only the specified area will be exported when saving the file to html.'''
        raise NotImplementedError()
    
    @property
    def parse_html_tag_in_cell(self) -> bool:
        '''Indicates whether html tag(such as ``<div></div>``) in cell should be parsed as cell value or preserved as it is.
        The default value is true.'''
        raise NotImplementedError()
    
    @parse_html_tag_in_cell.setter
    def parse_html_tag_in_cell(self, value : bool) -> None:
        '''Indicates whether html tag(such as ``<div></div>``) in cell should be parsed as cell value or preserved as it is.
        The default value is true.'''
        raise NotImplementedError()
    
    @property
    def html_cross_string_type(self) -> aspose.cells.HtmlCrossType:
        '''Indicates if a cross-cell string will be displayed in the same way as MS Excel when saving an Excel file in html format.
        By default the value is Default, so, for cross-cell strings, there is little difference between the html files created by Aspose.Cells and MS Excel.
        But the performance for creating large html files,setting the value to Cross would be several times faster than setting it to Default or Fit2Cell.'''
        raise NotImplementedError()
    
    @html_cross_string_type.setter
    def html_cross_string_type(self, value : aspose.cells.HtmlCrossType) -> None:
        '''Indicates if a cross-cell string will be displayed in the same way as MS Excel when saving an Excel file in html format.
        By default the value is Default, so, for cross-cell strings, there is little difference between the html files created by Aspose.Cells and MS Excel.
        But the performance for creating large html files,setting the value to Cross would be several times faster than setting it to Default or Fit2Cell.'''
        raise NotImplementedError()
    
    @property
    def hidden_col_display_type(self) -> aspose.cells.HtmlHiddenColDisplayType:
        '''Hidden column(the width of this column is 0) in excel,before save this into html format,
        if HtmlHiddenColDisplayType is "Remove",the hidden column would not been output,
        if the value is "Hidden", the column would been output,but was hidden,the default value is "Hidden"'''
        raise NotImplementedError()
    
    @hidden_col_display_type.setter
    def hidden_col_display_type(self, value : aspose.cells.HtmlHiddenColDisplayType) -> None:
        '''Hidden column(the width of this column is 0) in excel,before save this into html format,
        if HtmlHiddenColDisplayType is "Remove",the hidden column would not been output,
        if the value is "Hidden", the column would been output,but was hidden,the default value is "Hidden"'''
        raise NotImplementedError()
    
    @property
    def hidden_row_display_type(self) -> aspose.cells.HtmlHiddenRowDisplayType:
        '''Hidden row(the height of this row is 0) in excel,before save this into html format,
        if HtmlHiddenRowDisplayType is "Remove",the hidden row would not been output,
        if the value is "Hidden", the row would been output,but was hidden,the default value is "Hidden"'''
        raise NotImplementedError()
    
    @hidden_row_display_type.setter
    def hidden_row_display_type(self, value : aspose.cells.HtmlHiddenRowDisplayType) -> None:
        '''Hidden row(the height of this row is 0) in excel,before save this into html format,
        if HtmlHiddenRowDisplayType is "Remove",the hidden row would not been output,
        if the value is "Hidden", the row would been output,but was hidden,the default value is "Hidden"'''
        raise NotImplementedError()
    
    @property
    def encoding(self) -> str:
        '''If not set,use Encoding.UTF8 as default enconding type.'''
        raise NotImplementedError()
    
    @encoding.setter
    def encoding(self, value : str) -> None:
        '''If not set,use Encoding.UTF8 as default enconding type.'''
        raise NotImplementedError()
    
    @property
    def export_object_listener(self) -> aspose.cells.IExportObjectListener:
        '''Gets the ExportObjectListener for exporting objects.'''
        raise NotImplementedError()
    
    @export_object_listener.setter
    def export_object_listener(self, value : aspose.cells.IExportObjectListener) -> None:
        '''Sets the ExportObjectListener for exporting objects.'''
        raise NotImplementedError()
    
    @property
    def file_path_provider(self) -> aspose.cells.IFilePathProvider:
        '''Gets the IFilePathProvider for exporting Worksheet to html separately.'''
        raise NotImplementedError()
    
    @file_path_provider.setter
    def file_path_provider(self, value : aspose.cells.IFilePathProvider) -> None:
        '''Sets the IFilePathProvider for exporting Worksheet to html separately.'''
        raise NotImplementedError()
    
    @property
    def stream_provider(self) -> aspose.cells.IStreamProvider:
        '''Gets the IStreamProvider for exporting objects.'''
        raise NotImplementedError()
    
    @stream_provider.setter
    def stream_provider(self, value : aspose.cells.IStreamProvider) -> None:
        '''Sets the IStreamProvider for exporting objects.'''
        raise NotImplementedError()
    
    @property
    def image_options(self) -> aspose.cells.rendering.ImageOrPrintOptions:
        '''Get the ImageOrPrintOptions object before exporting'''
        raise NotImplementedError()
    
    @property
    def save_as_single_file(self) -> bool:
        '''Indicates whether save the html as single file.
        The default value is false.'''
        raise NotImplementedError()
    
    @save_as_single_file.setter
    def save_as_single_file(self, value : bool) -> None:
        '''Indicates whether save the html as single file.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def show_all_sheets(self) -> bool:
        '''Indicates whether showing all sheets when saving  as a single html file.'''
        raise NotImplementedError()
    
    @show_all_sheets.setter
    def show_all_sheets(self, value : bool) -> None:
        '''Indicates whether showing all sheets when saving  as a single html file.'''
        raise NotImplementedError()
    
    @property
    def export_page_headers(self) -> bool:
        '''Indicates whether exporting page headers.'''
        raise NotImplementedError()
    
    @export_page_headers.setter
    def export_page_headers(self, value : bool) -> None:
        '''Indicates whether exporting page headers.'''
        raise NotImplementedError()
    
    @property
    def export_page_footers(self) -> bool:
        '''Indicates whether exporting page headers.'''
        raise NotImplementedError()
    
    @export_page_footers.setter
    def export_page_footers(self, value : bool) -> None:
        '''Indicates whether exporting page headers.'''
        raise NotImplementedError()
    
    @property
    def export_hidden_worksheet(self) -> bool:
        '''Indicating if exporting the hidden worksheet content.The default value is true.'''
        raise NotImplementedError()
    
    @export_hidden_worksheet.setter
    def export_hidden_worksheet(self, value : bool) -> None:
        '''Indicating if exporting the hidden worksheet content.The default value is true.'''
        raise NotImplementedError()
    
    @property
    def presentation_preference(self) -> bool:
        '''Indicating if html or mht file is presentation preference.
        The default value is false.
        if you want to get more beautiful presentation,please set the value to true.'''
        raise NotImplementedError()
    
    @presentation_preference.setter
    def presentation_preference(self, value : bool) -> None:
        '''Indicating if html or mht file is presentation preference.
        The default value is false.
        if you want to get more beautiful presentation,please set the value to true.'''
        raise NotImplementedError()
    
    @property
    def cell_css_prefix(self) -> str:
        '''Gets and sets the prefix of the css name,the default value is "".'''
        raise NotImplementedError()
    
    @cell_css_prefix.setter
    def cell_css_prefix(self, value : str) -> None:
        '''Gets and sets the prefix of the css name,the default value is "".'''
        raise NotImplementedError()
    
    @property
    def table_css_id(self) -> str:
        '''Gets and sets the prefix of the type css name such as tr,col,td and so on, they are contained in the table element
        which has the specific TableCssId attribute. The default value is "".'''
        raise NotImplementedError()
    
    @table_css_id.setter
    def table_css_id(self, value : str) -> None:
        '''Gets and sets the prefix of the type css name such as tr,col,td and so on, they are contained in the table element
        which has the specific TableCssId attribute. The default value is "".'''
        raise NotImplementedError()
    
    @property
    def is_full_path_link(self) -> bool:
        '''Indicating whether using full path link in sheet00x.htm,filelist.xml and tabstrip.htm.
        The default value is false.'''
        raise NotImplementedError()
    
    @is_full_path_link.setter
    def is_full_path_link(self, value : bool) -> None:
        '''Indicating whether using full path link in sheet00x.htm,filelist.xml and tabstrip.htm.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def export_worksheet_css_separately(self) -> bool:
        '''Indicating whether export the worksheet css separately.The default value is false.'''
        raise NotImplementedError()
    
    @export_worksheet_css_separately.setter
    def export_worksheet_css_separately(self, value : bool) -> None:
        '''Indicating whether export the worksheet css separately.The default value is false.'''
        raise NotImplementedError()
    
    @property
    def export_similar_border_style(self) -> bool:
        '''Indicating whether exporting the similar border style when the border style is not supported by browsers.
        If you want to import the html or mht file to excel, please keep the default value.
        The default value is false.'''
        raise NotImplementedError()
    
    @export_similar_border_style.setter
    def export_similar_border_style(self, value : bool) -> None:
        '''Indicating whether exporting the similar border style when the border style is not supported by browsers.
        If you want to import the html or mht file to excel, please keep the default value.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def merge_empty_td_forcely(self) -> bool:
        '''Indicates whether merging empty TD element forcedly when exporting file to html.
        The size of html file will be reduced significantly after setting value to true. The default value is false.
        If you want to import the html file to excel or export perfect grid lines when saving file to html,
        please keep the default value.'''
        raise NotImplementedError()
    
    @merge_empty_td_forcely.setter
    def merge_empty_td_forcely(self, value : bool) -> None:
        '''Indicates whether merging empty TD element forcedly when exporting file to html.
        The size of html file will be reduced significantly after setting value to true. The default value is false.
        If you want to import the html file to excel or export perfect grid lines when saving file to html,
        please keep the default value.'''
        raise NotImplementedError()
    
    @property
    def merge_empty_td_type(self) -> aspose.cells.MergeEmptyTdType:
        '''The option to merge contiguous empty cells(empty td elements)
        The default value is MergeEmptyTdType.Default.'''
        raise NotImplementedError()
    
    @merge_empty_td_type.setter
    def merge_empty_td_type(self, value : aspose.cells.MergeEmptyTdType) -> None:
        '''The option to merge contiguous empty cells(empty td elements)
        The default value is MergeEmptyTdType.Default.'''
        raise NotImplementedError()
    
    @property
    def export_cell_coordinate(self) -> bool:
        '''Indicates whether exporting excel coordinate of nonblank cells when saving file to html. The default value is false.
        If you want to import the output html to excel, please keep the default value.'''
        raise NotImplementedError()
    
    @export_cell_coordinate.setter
    def export_cell_coordinate(self, value : bool) -> None:
        '''Indicates whether exporting excel coordinate of nonblank cells when saving file to html. The default value is false.
        If you want to import the output html to excel, please keep the default value.'''
        raise NotImplementedError()
    
    @property
    def export_extra_headings(self) -> bool:
        '''Indicates whether exporting extra headings when the length of text is longer than max display column.
        The default value is false. If you want to import the html file to excel, please keep the default value.'''
        raise NotImplementedError()
    
    @export_extra_headings.setter
    def export_extra_headings(self, value : bool) -> None:
        '''Indicates whether exporting extra headings when the length of text is longer than max display column.
        The default value is false. If you want to import the html file to excel, please keep the default value.'''
        raise NotImplementedError()
    
    @property
    def export_headings(self) -> bool:
        '''Indicates whether exports sheet\'s row and column headings when saving to HTML files.'''
        raise NotImplementedError()
    
    @export_headings.setter
    def export_headings(self, value : bool) -> None:
        '''Indicates whether exports sheet\'s row and column headings when saving to HTML files.'''
        raise NotImplementedError()
    
    @property
    def export_row_column_headings(self) -> bool:
        '''Indicates whether exports sheet\'s row and column headings when saving to HTML files.'''
        raise NotImplementedError()
    
    @export_row_column_headings.setter
    def export_row_column_headings(self, value : bool) -> None:
        '''Indicates whether exports sheet\'s row and column headings when saving to HTML files.'''
        raise NotImplementedError()
    
    @property
    def export_formula(self) -> bool:
        '''Indicates whether exporting formula when saving file to html. The default value is true.
        If you want to import the output html to excel, please keep the default value.'''
        raise NotImplementedError()
    
    @export_formula.setter
    def export_formula(self, value : bool) -> None:
        '''Indicates whether exporting formula when saving file to html. The default value is true.
        If you want to import the output html to excel, please keep the default value.'''
        raise NotImplementedError()
    
    @property
    def add_tooltip_text(self) -> bool:
        '''Indicates whether adding tooltip text when the data can\'t be fully displayed.
        The default value is false.'''
        raise NotImplementedError()
    
    @add_tooltip_text.setter
    def add_tooltip_text(self, value : bool) -> None:
        '''Indicates whether adding tooltip text when the data can\'t be fully displayed.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def export_grid_lines(self) -> bool:
        '''Indicating whether exporting the gridlines.The default value is false.'''
        raise NotImplementedError()
    
    @export_grid_lines.setter
    def export_grid_lines(self, value : bool) -> None:
        '''Indicating whether exporting the gridlines.The default value is false.'''
        raise NotImplementedError()
    
    @property
    def export_bogus_row_data(self) -> bool:
        '''Indicating whether exporting bogus bottom row data. The default value is true.If you want to import the html or mht file
        to excel, please keep the default value.'''
        raise NotImplementedError()
    
    @export_bogus_row_data.setter
    def export_bogus_row_data(self, value : bool) -> None:
        '''Indicating whether exporting bogus bottom row data. The default value is true.If you want to import the html or mht file
        to excel, please keep the default value.'''
        raise NotImplementedError()
    
    @property
    def exclude_unused_styles(self) -> bool:
        '''Indicating whether excludes unused styles.
        For the generated html files, excluding unused styles can make the file size smaller
        without affecting the visual effects. So the default value of this property is true.
        If user needs to keep all styles in the workbook for the generated html(such as the scenario that user
        needs to restore the workbook from the generated html later), please set this property as false.'''
        raise NotImplementedError()
    
    @exclude_unused_styles.setter
    def exclude_unused_styles(self, value : bool) -> None:
        '''Indicating whether excludes unused styles.
        For the generated html files, excluding unused styles can make the file size smaller
        without affecting the visual effects. So the default value of this property is true.
        If user needs to keep all styles in the workbook for the generated html(such as the scenario that user
        needs to restore the workbook from the generated html later), please set this property as false.'''
        raise NotImplementedError()
    
    @property
    def export_document_properties(self) -> bool:
        '''Indicating whether exporting document properties.The default value is true.If you want to import
        the html or mht file to excel, please keep the default value.'''
        raise NotImplementedError()
    
    @export_document_properties.setter
    def export_document_properties(self, value : bool) -> None:
        '''Indicating whether exporting document properties.The default value is true.If you want to import
        the html or mht file to excel, please keep the default value.'''
        raise NotImplementedError()
    
    @property
    def export_worksheet_properties(self) -> bool:
        '''Indicating whether exporting worksheet properties.The default value is true.If you want to import
        the html or mht file to excel, please keep the default value.'''
        raise NotImplementedError()
    
    @export_worksheet_properties.setter
    def export_worksheet_properties(self, value : bool) -> None:
        '''Indicating whether exporting worksheet properties.The default value is true.If you want to import
        the html or mht file to excel, please keep the default value.'''
        raise NotImplementedError()
    
    @property
    def export_workbook_properties(self) -> bool:
        '''Indicating whether exporting workbook properties.The default value is true.If you want to import
        the html or mht file to excel, please keep the default value.'''
        raise NotImplementedError()
    
    @export_workbook_properties.setter
    def export_workbook_properties(self, value : bool) -> None:
        '''Indicating whether exporting workbook properties.The default value is true.If you want to import
        the html or mht file to excel, please keep the default value.'''
        raise NotImplementedError()
    
    @property
    def export_frame_scripts_and_properties(self) -> bool:
        '''Indicating whether exporting frame scripts and document properties. The default value is true.If you want to import the html or mht file
        to excel, please keep the default value.'''
        raise NotImplementedError()
    
    @export_frame_scripts_and_properties.setter
    def export_frame_scripts_and_properties(self, value : bool) -> None:
        '''Indicating whether exporting frame scripts and document properties. The default value is true.If you want to import the html or mht file
        to excel, please keep the default value.'''
        raise NotImplementedError()
    
    @property
    def export_data_options(self) -> aspose.cells.HtmlExportDataOptions:
        '''Indicating the rule of exporting html file data.The default value is All.'''
        raise NotImplementedError()
    
    @export_data_options.setter
    def export_data_options(self, value : aspose.cells.HtmlExportDataOptions) -> None:
        '''Indicating the rule of exporting html file data.The default value is All.'''
        raise NotImplementedError()
    
    @property
    def link_target_type(self) -> aspose.cells.HtmlLinkTargetType:
        '''Indicating the type of target attribute in ``<a>`` link. The default value is HtmlLinkTargetType.Parent.'''
        raise NotImplementedError()
    
    @link_target_type.setter
    def link_target_type(self, value : aspose.cells.HtmlLinkTargetType) -> None:
        '''Indicating the type of target attribute in ``<a>`` link. The default value is HtmlLinkTargetType.Parent.'''
        raise NotImplementedError()
    
    @property
    def is_ie_compatible(self) -> bool:
        '''Indicating whether the output HTML is compatible with IE browser.
        The defalut value is false'''
        raise NotImplementedError()
    
    @is_ie_compatible.setter
    def is_ie_compatible(self, value : bool) -> None:
        '''Indicating whether the output HTML is compatible with IE browser.
        The defalut value is false'''
        raise NotImplementedError()
    
    @property
    def format_data_ignore_column_width(self) -> bool:
        '''Indicating whether show the whole formatted data of cell when overflowing the column.
        If true then ignore the column width and the whole data of cell will be exported.
        If false then the data will be exported same as Excel.
        The default value is false.'''
        raise NotImplementedError()
    
    @format_data_ignore_column_width.setter
    def format_data_ignore_column_width(self, value : bool) -> None:
        '''Indicating whether show the whole formatted data of cell when overflowing the column.
        If true then ignore the column width and the whole data of cell will be exported.
        If false then the data will be exported same as Excel.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def calculate_formula(self) -> bool:
        '''Indicates whether to calculate formulas before saving html file.'''
        raise NotImplementedError()
    
    @calculate_formula.setter
    def calculate_formula(self, value : bool) -> None:
        '''Indicates whether to calculate formulas before saving html file.'''
        raise NotImplementedError()
    
    @property
    def is_js_browser_compatible(self) -> bool:
        '''Indicates whether JavaScript is compatible with browsers that do not support JavaScript.
        The default value is true.'''
        raise NotImplementedError()
    
    @is_js_browser_compatible.setter
    def is_js_browser_compatible(self, value : bool) -> None:
        '''Indicates whether JavaScript is compatible with browsers that do not support JavaScript.
        The default value is true.'''
        raise NotImplementedError()
    
    @property
    def is_mobile_compatible(self) -> bool:
        '''Indicates whether the output HTML is compatible with mobile devices.
        The default value is false.'''
        raise NotImplementedError()
    
    @is_mobile_compatible.setter
    def is_mobile_compatible(self, value : bool) -> None:
        '''Indicates whether the output HTML is compatible with mobile devices.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def css_styles(self) -> str:
        '''Gets the additional css styles for the formatter.
        Only works when :py:attr:`aspose.cells.HtmlSaveOptions.save_as_single_file` is True.'''
        raise NotImplementedError()
    
    @css_styles.setter
    def css_styles(self, value : str) -> None:
        '''Sets the additional css styles for the formatter.
        Only works when :py:attr:`aspose.cells.HtmlSaveOptions.save_as_single_file` is True.'''
        raise NotImplementedError()
    
    @property
    def hide_overflow_wrapped_text(self) -> bool:
        '''Indicates whether to hide overflow text when the cell format is set to wrap text.
        The default value is false'''
        raise NotImplementedError()
    
    @hide_overflow_wrapped_text.setter
    def hide_overflow_wrapped_text(self, value : bool) -> None:
        '''Indicates whether to hide overflow text when the cell format is set to wrap text.
        The default value is false'''
        raise NotImplementedError()
    
    @property
    def is_border_collapsed(self) -> bool:
        '''Indicates whether the table borders are collapsed.
        The default value is true.'''
        raise NotImplementedError()
    
    @is_border_collapsed.setter
    def is_border_collapsed(self, value : bool) -> None:
        '''Indicates whether the table borders are collapsed.
        The default value is true.'''
        raise NotImplementedError()
    
    @property
    def encode_entity_as_code(self) -> bool:
        '''Indicates whether the html character entities are replaced with decimal code.
        (e.g. "&nbsp;" is replaced with "&#160;").
        The default value is false.'''
        raise NotImplementedError()
    
    @encode_entity_as_code.setter
    def encode_entity_as_code(self, value : bool) -> None:
        '''Indicates whether the html character entities are replaced with decimal code.
        (e.g. "&nbsp;" is replaced with "&#160;").
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def office_math_output_mode(self) -> aspose.cells.HtmlOfficeMathOutputType:
        '''Indicates how export OfficeMath objects to HTML, Default value is Image.'''
        raise NotImplementedError()
    
    @office_math_output_mode.setter
    def office_math_output_mode(self, value : aspose.cells.HtmlOfficeMathOutputType) -> None:
        '''Indicates how export OfficeMath objects to HTML, Default value is Image.'''
        raise NotImplementedError()
    
    @property
    def cell_name_attribute(self) -> str:
        '''Specifies the attribute that indicates the CellName to be written.
        (e.g. If the value is "id", then for cell "A1", the output will be:<td id=\'A1\'>).
        The default value is null.'''
        raise NotImplementedError()
    
    @cell_name_attribute.setter
    def cell_name_attribute(self, value : str) -> None:
        '''Specifies the attribute that indicates the CellName to be written.
        (e.g. If the value is "id", then for cell "A1", the output will be:<td id=\'A1\'>).
        The default value is null.'''
        raise NotImplementedError()
    
    @property
    def disable_css(self) -> bool:
        '''Indicates whether only inline styles are applied, without relying on CSS.
        The default value is false.'''
        raise NotImplementedError()
    
    @disable_css.setter
    def disable_css(self, value : bool) -> None:
        '''Indicates whether only inline styles are applied, without relying on CSS.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def enable_css_custom_properties(self) -> bool:
        '''Optimize the output of html by using CSS custom properties. For example, for the scenario that there are multiple occurences for one base64 image, with custom property the image data only needs to be saved once so the performance of the resultant html can be improved.
        The default value is false.'''
        raise NotImplementedError()
    
    @enable_css_custom_properties.setter
    def enable_css_custom_properties(self, value : bool) -> None:
        '''Optimize the output of html by using CSS custom properties. For example, for the scenario that there are multiple occurences for one base64 image, with custom property the image data only needs to be saved once so the performance of the resultant html can be improved.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def html_version(self) -> aspose.cells.HtmlVersion:
        '''Specifies version of HTML standard that should be used when saving the HTML format.
        Default value is HtmlVersion.Default.'''
        raise NotImplementedError()
    
    @html_version.setter
    def html_version(self, value : aspose.cells.HtmlVersion) -> None:
        '''Specifies version of HTML standard that should be used when saving the HTML format.
        Default value is HtmlVersion.Default.'''
        raise NotImplementedError()
    
    @property
    def sheet_set(self) -> aspose.cells.rendering.SheetSet:
        '''Gets the sheets to render. Default is all visible sheets in the workbook: :py:attr:`aspose.cells.rendering.SheetSet.visible`.'''
        raise NotImplementedError()
    
    @sheet_set.setter
    def sheet_set(self, value : aspose.cells.rendering.SheetSet) -> None:
        '''Sets the sheets to render. Default is all visible sheets in the workbook: :py:attr:`aspose.cells.rendering.SheetSet.visible`.'''
        raise NotImplementedError()
    
    @property
    def embedded_font_type(self) -> aspose.cells.rendering.HtmlEmbeddedFontType:
        '''Gets the type of font that embedded in html.
        Default value is :py:attr:`aspose.cells.rendering.HtmlEmbeddedFontType.NONE` which indicates that it will not embed font in html.'''
        raise NotImplementedError()
    
    @embedded_font_type.setter
    def embedded_font_type(self, value : aspose.cells.rendering.HtmlEmbeddedFontType) -> None:
        '''Sets the type of font that embedded in html.
        Default value is :py:attr:`aspose.cells.rendering.HtmlEmbeddedFontType.NONE` which indicates that it will not embed font in html.'''
        raise NotImplementedError()
    

class SqlScriptColumnTypeMap:
    '''Represents column type map.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    def get_string_type(self) -> str:
        '''Gets string type in the database.'''
        raise NotImplementedError()
    
    def get_numberic_type(self) -> str:
        '''Gets numeric type in the database.'''
        raise NotImplementedError()
    

class SqlScriptSaveOptions(aspose.cells.SaveOptions):
    '''Represents the options of saving sql.'''
    
    def __init__(self) -> None:
        '''Creates options for saving sql file.'''
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.cells.SaveFormat:
        '''Gets the save file format.'''
        raise NotImplementedError()
    
    @property
    def clear_data(self) -> bool:
        '''Make the workbook empty after saving the file.'''
        raise NotImplementedError()
    
    @clear_data.setter
    def clear_data(self, value : bool) -> None:
        '''Make the workbook empty after saving the file.'''
        raise NotImplementedError()
    
    @property
    def cached_file_folder(self) -> str:
        '''The folder for temporary files that may be used as data cache.'''
        raise NotImplementedError()
    
    @cached_file_folder.setter
    def cached_file_folder(self, value : str) -> None:
        '''The folder for temporary files that may be used as data cache.'''
        raise NotImplementedError()
    
    @property
    def validate_merged_areas(self) -> bool:
        '''Indicates whether validate merged cells before saving the file.'''
        raise NotImplementedError()
    
    @validate_merged_areas.setter
    def validate_merged_areas(self, value : bool) -> None:
        '''Indicates whether validate merged cells before saving the file.'''
        raise NotImplementedError()
    
    @property
    def merge_areas(self) -> bool:
        '''Indicates whether merge the areas of conditional formatting and validation before saving the file.'''
        raise NotImplementedError()
    
    @merge_areas.setter
    def merge_areas(self, value : bool) -> None:
        '''Indicates whether merge the areas of conditional formatting and validation before saving the file.'''
        raise NotImplementedError()
    
    @property
    def create_directory(self) -> bool:
        '''If true and the directory does not exist, the directory will be automatically created before saving the file.'''
        raise NotImplementedError()
    
    @create_directory.setter
    def create_directory(self, value : bool) -> None:
        '''If true and the directory does not exist, the directory will be automatically created before saving the file.'''
        raise NotImplementedError()
    
    @property
    def sort_names(self) -> bool:
        '''Indicates whether sorting defined names before saving file.'''
        raise NotImplementedError()
    
    @sort_names.setter
    def sort_names(self, value : bool) -> None:
        '''Indicates whether sorting defined names before saving file.'''
        raise NotImplementedError()
    
    @property
    def sort_external_names(self) -> bool:
        '''Indicates whether sorting external defined names before saving file.'''
        raise NotImplementedError()
    
    @sort_external_names.setter
    def sort_external_names(self, value : bool) -> None:
        '''Indicates whether sorting external defined names before saving file.'''
        raise NotImplementedError()
    
    @property
    def refresh_chart_cache(self) -> bool:
        '''Indicates whether refreshing chart cache data'''
        raise NotImplementedError()
    
    @refresh_chart_cache.setter
    def refresh_chart_cache(self, value : bool) -> None:
        '''Indicates whether refreshing chart cache data'''
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
    def check_excel_restriction(self) -> bool:
        '''Whether check restriction of excel file when user modify cells related objects.
        For example, excel does not allow inputting string value longer than 32K.
        When you input a value longer than 32K, it will be truncated.'''
        raise NotImplementedError()
    
    @check_excel_restriction.setter
    def check_excel_restriction(self, value : bool) -> None:
        '''Whether check restriction of excel file when user modify cells related objects.
        For example, excel does not allow inputting string value longer than 32K.
        When you input a value longer than 32K, it will be truncated.'''
        raise NotImplementedError()
    
    @property
    def update_smart_art(self) -> bool:
        '''Indicates whether updating smart art setting.
        The default value is false.'''
        raise NotImplementedError()
    
    @update_smart_art.setter
    def update_smart_art(self, value : bool) -> None:
        '''Indicates whether updating smart art setting.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def encrypt_document_properties(self) -> bool:
        '''Indicates whether encrypt document properties when saving as .xls file.
        The default value is true.'''
        raise NotImplementedError()
    
    @encrypt_document_properties.setter
    def encrypt_document_properties(self, value : bool) -> None:
        '''Indicates whether encrypt document properties when saving as .xls file.
        The default value is true.'''
        raise NotImplementedError()
    
    @property
    def check_if_table_exists(self) -> bool:
        '''Check if the table name exists before creating'''
        raise NotImplementedError()
    
    @check_if_table_exists.setter
    def check_if_table_exists(self, value : bool) -> None:
        '''Check if the table name exists before creating'''
        raise NotImplementedError()
    
    @property
    def column_type_map(self) -> aspose.cells.saving.SqlScriptColumnTypeMap:
        '''Gets and sets the map of column type for different database.'''
        raise NotImplementedError()
    
    @column_type_map.setter
    def column_type_map(self, value : aspose.cells.saving.SqlScriptColumnTypeMap) -> None:
        '''Gets and sets the map of column type for different database.'''
        raise NotImplementedError()
    
    @property
    def check_all_data_for_column_type(self) -> bool:
        '''Check all data to find columns\' data type.'''
        raise NotImplementedError()
    
    @check_all_data_for_column_type.setter
    def check_all_data_for_column_type(self, value : bool) -> None:
        '''Check all data to find columns\' data type.'''
        raise NotImplementedError()
    
    @property
    def add_blank_line_between_rows(self) -> bool:
        '''Insert blank line between each data.'''
        raise NotImplementedError()
    
    @add_blank_line_between_rows.setter
    def add_blank_line_between_rows(self, value : bool) -> None:
        '''Insert blank line between each data.'''
        raise NotImplementedError()
    
    @property
    def separator(self) -> System.Char:
        '''Gets and sets character separator of sql script.'''
        raise NotImplementedError()
    
    @separator.setter
    def separator(self, value : System.Char) -> None:
        '''Gets and sets character separator of sql script.'''
        raise NotImplementedError()
    
    @property
    def operator_type(self) -> aspose.cells.saving.SqlScriptOperatorType:
        '''Gets and sets the operator type of sql.'''
        raise NotImplementedError()
    
    @operator_type.setter
    def operator_type(self, value : aspose.cells.saving.SqlScriptOperatorType) -> None:
        '''Gets and sets the operator type of sql.'''
        raise NotImplementedError()
    
    @property
    def primary_key(self) -> int:
        '''Represents which column is primary key of the data table.'''
        raise NotImplementedError()
    
    @primary_key.setter
    def primary_key(self, value : int) -> None:
        '''Represents which column is primary key of the data table.'''
        raise NotImplementedError()
    
    @property
    def create_table(self) -> bool:
        '''Indicates whether exporting sql of creating table.'''
        raise NotImplementedError()
    
    @create_table.setter
    def create_table(self, value : bool) -> None:
        '''Indicates whether exporting sql of creating table.'''
        raise NotImplementedError()
    
    @property
    def id_name(self) -> str:
        '''Gets and sets the name of id column.'''
        raise NotImplementedError()
    
    @id_name.setter
    def id_name(self, value : str) -> None:
        '''Gets and sets the name of id column.'''
        raise NotImplementedError()
    
    @property
    def start_id(self) -> int:
        '''Gets and sets the start id.'''
        raise NotImplementedError()
    
    @start_id.setter
    def start_id(self, value : int) -> None:
        '''Gets and sets the start id.'''
        raise NotImplementedError()
    
    @property
    def table_name(self) -> str:
        '''Gets and sets the table name.'''
        raise NotImplementedError()
    
    @table_name.setter
    def table_name(self, value : str) -> None:
        '''Gets and sets the table name.'''
        raise NotImplementedError()
    
    @property
    def export_as_string(self) -> bool:
        '''Indicates whether exporting all data as string value.'''
        raise NotImplementedError()
    
    @export_as_string.setter
    def export_as_string(self, value : bool) -> None:
        '''Indicates whether exporting all data as string value.'''
        raise NotImplementedError()
    
    @property
    def sheet_indexes(self) -> List[int]:
        '''Represents the indexes of exported sheets.'''
        raise NotImplementedError()
    
    @sheet_indexes.setter
    def sheet_indexes(self, value : List[int]) -> None:
        '''Represents the indexes of exported sheets.'''
        raise NotImplementedError()
    
    @property
    def export_area(self) -> aspose.cells.CellArea:
        '''Gets the exporting range.'''
        raise NotImplementedError()
    
    @export_area.setter
    def export_area(self, value : aspose.cells.CellArea) -> None:
        '''Sets the exporting range.'''
        raise NotImplementedError()
    
    @property
    def has_header_row(self) -> bool:
        '''Indicates whether the range contains header row.'''
        raise NotImplementedError()
    
    @has_header_row.setter
    def has_header_row(self, value : bool) -> None:
        '''Indicates whether the range contains header row.'''
        raise NotImplementedError()
    

class SaveElementType:
    '''Represents what kind of elements should be saved.'''
    
    ALL : SaveElementType
    '''All data.'''
    CHART : SaveElementType
    '''Only charts.'''

class SqlScriptOperatorType:
    '''Represents the type of operating data.'''
    
    INSERT : SqlScriptOperatorType
    '''Insert data.'''
    UPDATE : SqlScriptOperatorType
    '''Update data.'''
    DELETE : SqlScriptOperatorType
    '''Delete data.'''

