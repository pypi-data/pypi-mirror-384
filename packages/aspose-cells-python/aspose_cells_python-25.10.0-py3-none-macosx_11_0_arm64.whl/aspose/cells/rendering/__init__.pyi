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

class CustomRenderSettings:
    '''Represents custom settings during rendering.'''
    
    def __init__(self) -> None:
        '''Ctor.'''
        raise NotImplementedError()
    
    def get_cell_border_width(self, border_type : aspose.cells.CellBorderType) -> float:
        '''Specifies cell border width according to border type.
        
        :param border_type: cell border type
        :returns: cell border width'''
        raise NotImplementedError()
    

class DrawObject:
    '''DrawObject will be initialized and returned when rendering.'''
    
    @property
    def cell(self) -> aspose.cells.Cell:
        '''Indicates the Cell object when rendering.
        All properties of cell can be accessed.'''
        raise NotImplementedError()
    
    @property
    def shape(self) -> aspose.cells.drawing.Shape:
        '''Indicates the Shape object when rendering.
        All properties of shape can be accessed.'''
        raise NotImplementedError()
    
    @property
    def image_bytes(self) -> List[int]:
        '''Indicates image bytes of rendered Chart, Shape when rendering.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.rendering.DrawObjectEnum:
        '''Indicates the type of DrawObject.'''
        raise NotImplementedError()
    
    @property
    def current_page(self) -> int:
        '''Indicates the page index of DrawObject.
        Page index is based on zero.
        One Sheet contains several pages when rendering.'''
        raise NotImplementedError()
    
    @property
    def total_pages(self) -> int:
        '''Indicates total pages in current rendering.'''
        raise NotImplementedError()
    
    @property
    def sheet_index(self) -> int:
        '''Indicates current sheet index of DrawObject.'''
        raise NotImplementedError()
    

class DrawObjectEventHandler:
    '''Interface to get DrawObject and Bound when rendering.'''
    
    def draw(self, draw_object : aspose.cells.rendering.DrawObject, x : float, y : float, width : float, height : float) -> None:
        '''Implements this interface to get DrawObject and Bound when rendering.
        
        :param draw_object: DrawObject will be initialized and returned when rendering
        :param x: Left of DrawObject
        :param y: Top of DrawObject
        :param width: Width of DrawObject
        :param height: Height of DrawObject'''
        raise NotImplementedError()
    

class IPageSavingCallback:
    '''Control/Indicate progress of page saving process.'''
    
    def page_start_saving(self, args : aspose.cells.rendering.PageStartSavingArgs) -> None:
        '''Control/Indicate a page starts to be output.
        
        :param args: Info for a page starts saving process.'''
        raise NotImplementedError()
    
    def page_end_saving(self, args : aspose.cells.rendering.PageEndSavingArgs) -> None:
        '''Control/Indicate a page ends to be output.
        
        :param args: Info for a page ends saving process.'''
        raise NotImplementedError()
    

class ImageOrPrintOptions:
    '''Allows to specify options when rendering worksheet to images, printing worksheet or rendering chart to image.'''
    
    def __init__(self) -> None:
        '''Ctor.'''
        raise NotImplementedError()
    
    @overload
    def set_desired_size(self, desired_width : int, desired_height : int) -> None:
        '''Sets desired width and height of image.
        
        :param desired_width: desired width in pixels
        :param desired_height: desired height in pixels'''
        raise NotImplementedError()
    
    @overload
    def set_desired_size(self, desired_width : int, desired_height : int, keep_aspect_ratio : bool) -> None:
        '''Sets desired width and height of image.
        
        :param desired_width: desired width in pixels
        :param desired_height: desired height in pixels
        :param keep_aspect_ratio: whether to keep aspect ratio of origin image'''
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.cells.SaveFormat:
        '''Gets the output file format type
        Support Tiff/XPS'''
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.cells.SaveFormat) -> None:
        '''Sets the output file format type
        Support Tiff/XPS'''
        raise NotImplementedError()
    
    @property
    def print_with_status_dialog(self) -> bool:
        '''If PrintWithStatusDialog = true , there will be a dialog that shows current print status.
        else no such dialog will show.'''
        raise NotImplementedError()
    
    @print_with_status_dialog.setter
    def print_with_status_dialog(self, value : bool) -> None:
        '''If PrintWithStatusDialog = true , there will be a dialog that shows current print status.
        else no such dialog will show.'''
        raise NotImplementedError()
    
    @property
    def horizontal_resolution(self) -> int:
        '''Gets the horizontal resolution for generated images, in dots per inch.'''
        raise NotImplementedError()
    
    @horizontal_resolution.setter
    def horizontal_resolution(self, value : int) -> None:
        '''Sets the horizontal resolution for generated images, in dots per inch.'''
        raise NotImplementedError()
    
    @property
    def vertical_resolution(self) -> int:
        '''Gets the vertical resolution for generated images, in dots per inch.'''
        raise NotImplementedError()
    
    @vertical_resolution.setter
    def vertical_resolution(self, value : int) -> None:
        '''Sets the vertical resolution for generated images, in dots per inch.'''
        raise NotImplementedError()
    
    @property
    def tiff_compression(self) -> aspose.cells.rendering.TiffCompression:
        '''Gets the type of compression to apply only when saving pages to the ``Tiff`` format.'''
        raise NotImplementedError()
    
    @tiff_compression.setter
    def tiff_compression(self, value : aspose.cells.rendering.TiffCompression) -> None:
        '''Sets the type of compression to apply only when saving pages to the ``Tiff`` format.'''
        raise NotImplementedError()
    
    @property
    def tiff_color_depth(self) -> aspose.cells.rendering.ColorDepth:
        '''Gets bit depth to apply only when saving pages to the ``Tiff`` format.'''
        raise NotImplementedError()
    
    @tiff_color_depth.setter
    def tiff_color_depth(self, value : aspose.cells.rendering.ColorDepth) -> None:
        '''Sets bit depth to apply only when saving pages to the ``Tiff`` format.'''
        raise NotImplementedError()
    
    @property
    def tiff_binarization_method(self) -> aspose.cells.rendering.ImageBinarizationMethod:
        '''Gets method used while converting images to 1 bpp format
        when :py:attr:`aspose.cells.rendering.ImageOrPrintOptions.image_type` is Tiff and :py:attr:`aspose.cells.rendering.ImageOrPrintOptions.tiff_compression` is equal to Ccitt3 or Ccitt4.'''
        raise NotImplementedError()
    
    @tiff_binarization_method.setter
    def tiff_binarization_method(self, value : aspose.cells.rendering.ImageBinarizationMethod) -> None:
        '''Sets method used while converting images to 1 bpp format
        when :py:attr:`aspose.cells.rendering.ImageOrPrintOptions.image_type` is Tiff and :py:attr:`aspose.cells.rendering.ImageOrPrintOptions.tiff_compression` is equal to Ccitt3 or Ccitt4.'''
        raise NotImplementedError()
    
    @property
    def printing_page(self) -> aspose.cells.PrintingPageType:
        '''Indicates which pages will not be printed.'''
        raise NotImplementedError()
    
    @printing_page.setter
    def printing_page(self, value : aspose.cells.PrintingPageType) -> None:
        '''Indicates which pages will not be printed.'''
        raise NotImplementedError()
    
    @property
    def quality(self) -> int:
        '''Gets a value determining the quality of the generated  images
        to apply only when saving pages to the ``Jpeg`` format. The default value is 100'''
        raise NotImplementedError()
    
    @quality.setter
    def quality(self, value : int) -> None:
        '''Sets a value determining the quality of the generated  images
        to apply only when saving pages to the ``Jpeg`` format. The default value is 100'''
        raise NotImplementedError()
    
    @property
    def image_type(self) -> aspose.cells.drawing.ImageType:
        '''Gets the format of the generated images.
        default value: PNG.'''
        raise NotImplementedError()
    
    @image_type.setter
    def image_type(self, value : aspose.cells.drawing.ImageType) -> None:
        '''Sets the format of the generated images.
        default value: PNG.'''
        raise NotImplementedError()
    
    @property
    def is_cell_auto_fit(self) -> bool:
        '''Indicates whether the width and height of the cells is automatically fitted by cell value.
        The default value is false.'''
        raise NotImplementedError()
    
    @is_cell_auto_fit.setter
    def is_cell_auto_fit(self, value : bool) -> None:
        '''Indicates whether the width and height of the cells is automatically fitted by cell value.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def one_page_per_sheet(self) -> bool:
        '''If OnePagePerSheet is true , all content of one sheet will output to only one page in result.
        The paper size of pagesetup will be invalid, and the other settings of pagesetup
        will still take effect.'''
        raise NotImplementedError()
    
    @one_page_per_sheet.setter
    def one_page_per_sheet(self, value : bool) -> None:
        '''If OnePagePerSheet is true , all content of one sheet will output to only one page in result.
        The paper size of pagesetup will be invalid, and the other settings of pagesetup
        will still take effect.'''
        raise NotImplementedError()
    
    @property
    def all_columns_in_one_page_per_sheet(self) -> bool:
        '''If AllColumnsInOnePagePerSheet is true , all column content of one sheet will output to only one page in result.
        The width of paper size of pagesetup will be invalid, and the other settings of pagesetup
        will still take effect.'''
        raise NotImplementedError()
    
    @all_columns_in_one_page_per_sheet.setter
    def all_columns_in_one_page_per_sheet(self, value : bool) -> None:
        '''If AllColumnsInOnePagePerSheet is true , all column content of one sheet will output to only one page in result.
        The width of paper size of pagesetup will be invalid, and the other settings of pagesetup
        will still take effect.'''
        raise NotImplementedError()
    
    @property
    def draw_object_event_handler(self) -> aspose.cells.rendering.DrawObjectEventHandler:
        '''Implements this interface to get DrawObject and Bound when rendering.'''
        raise NotImplementedError()
    
    @draw_object_event_handler.setter
    def draw_object_event_handler(self, value : aspose.cells.rendering.DrawObjectEventHandler) -> None:
        '''Implements this interface to get DrawObject and Bound when rendering.'''
        raise NotImplementedError()
    
    @property
    def chart_image_type(self) -> Any:
        '''Indicate the chart imagetype when converting.
        default value: PNG.'''
        raise NotImplementedError()
    
    @chart_image_type.setter
    def chart_image_type(self, value : Any) -> None:
        '''Indicate the chart imagetype when converting.
        default value: PNG.'''
        raise NotImplementedError()
    
    @property
    def embeded_image_name_in_svg(self) -> str:
        '''Indicate the filename of embedded image in svg.
        This should be full path with directory like "c:\\xpsEmbedded"'''
        raise NotImplementedError()
    
    @embeded_image_name_in_svg.setter
    def embeded_image_name_in_svg(self, value : str) -> None:
        '''Indicate the filename of embedded image in svg.
        This should be full path with directory like "c:\\xpsEmbedded"'''
        raise NotImplementedError()
    
    @property
    def svg_fit_to_view_port(self) -> bool:
        '''if this property is true, the generated svg will fit to view port.'''
        raise NotImplementedError()
    
    @svg_fit_to_view_port.setter
    def svg_fit_to_view_port(self, value : bool) -> None:
        '''if this property is true, the generated svg will fit to view port.'''
        raise NotImplementedError()
    
    @property
    def svg_css_prefix(self) -> str:
        '''Gets and sets the prefix of the css name in svg,the default value is empty string.'''
        raise NotImplementedError()
    
    @svg_css_prefix.setter
    def svg_css_prefix(self, value : str) -> None:
        '''Gets and sets the prefix of the css name in svg,the default value is empty string.'''
        raise NotImplementedError()
    
    @property
    def only_area(self) -> bool:
        '''If this property is true , one Area will be output, and no scale will take effect.'''
        raise NotImplementedError()
    
    @only_area.setter
    def only_area(self, value : bool) -> None:
        '''If this property is true , one Area will be output, and no scale will take effect.'''
        raise NotImplementedError()
    
    @property
    def text_rendering_hint(self) -> Any:
        '''Specifies the quality of text rendering.
        The default value is TextRenderingHint.SystemDefault'''
        raise NotImplementedError()
    
    @text_rendering_hint.setter
    def text_rendering_hint(self, value : Any) -> None:
        '''Specifies the quality of text rendering.
        The default value is TextRenderingHint.SystemDefault'''
        raise NotImplementedError()
    
    @property
    def smoothing_mode(self) -> Any:
        '''Specifies whether smoothing (antialiasing) is applied to lines and curves and the edges of filled areas.
        The default value is SmoothingMode.None'''
        raise NotImplementedError()
    
    @smoothing_mode.setter
    def smoothing_mode(self, value : Any) -> None:
        '''Specifies whether smoothing (antialiasing) is applied to lines and curves and the edges of filled areas.
        The default value is SmoothingMode.None'''
        raise NotImplementedError()
    
    @property
    def transparent(self) -> bool:
        '''Indicates if the background of generated image should be transparent.'''
        raise NotImplementedError()
    
    @transparent.setter
    def transparent(self, value : bool) -> None:
        '''Indicates if the background of generated image should be transparent.'''
        raise NotImplementedError()
    
    @property
    def pixel_format(self) -> Any:
        '''Gets the pixel format for the generated images.'''
        raise NotImplementedError()
    
    @pixel_format.setter
    def pixel_format(self, value : Any) -> None:
        '''Sets the pixel format for the generated images.'''
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
    def page_saving_callback(self) -> aspose.cells.rendering.IPageSavingCallback:
        '''Control/Indicate progress of page saving process.'''
        raise NotImplementedError()
    
    @page_saving_callback.setter
    def page_saving_callback(self, value : aspose.cells.rendering.IPageSavingCallback) -> None:
        '''Control/Indicate progress of page saving process.'''
        raise NotImplementedError()
    
    @property
    def is_font_substitution_char_granularity(self) -> bool:
        '''Indicates whether to only substitute the font of character when the cell font is not compatibility for it.'''
        raise NotImplementedError()
    
    @is_font_substitution_char_granularity.setter
    def is_font_substitution_char_granularity(self, value : bool) -> None:
        '''Indicates whether to only substitute the font of character when the cell font is not compatibility for it.'''
        raise NotImplementedError()
    
    @property
    def page_index(self) -> int:
        '''Gets the 0-based index of the first page to save.'''
        raise NotImplementedError()
    
    @page_index.setter
    def page_index(self, value : int) -> None:
        '''Sets the 0-based index of the first page to save.'''
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        '''Gets the number of pages to save.'''
        raise NotImplementedError()
    
    @page_count.setter
    def page_count(self, value : int) -> None:
        '''Sets the number of pages to save.'''
        raise NotImplementedError()
    
    @property
    def is_optimized(self) -> bool:
        '''Indicates whether to optimize the output elements.'''
        raise NotImplementedError()
    
    @is_optimized.setter
    def is_optimized(self, value : bool) -> None:
        '''Indicates whether to optimize the output elements.'''
        raise NotImplementedError()
    
    @property
    def default_font(self) -> str:
        '''When characters in the Excel are Unicode and not be set with correct font in cell style,
        They may appear as block in pdf,image.
        Set the DefaultFont such as MingLiu or MS Gothic to show these characters.
        If this property is not set, Aspose.Cells will use system default font to show these unicode characters.'''
        raise NotImplementedError()
    
    @default_font.setter
    def default_font(self, value : str) -> None:
        '''When characters in the Excel are Unicode and not be set with correct font in cell style,
        They may appear as block in pdf,image.
        Set the DefaultFont such as MingLiu or MS Gothic to show these characters.
        If this property is not set, Aspose.Cells will use system default font to show these unicode characters.'''
        raise NotImplementedError()
    
    @property
    def check_workbook_default_font(self) -> bool:
        '''When characters in the Excel are Unicode and not be set with correct font in cell style,
        They may appear as block in pdf,image.
        Set this to true to try to use workbook\'s default font to show these characters first.'''
        raise NotImplementedError()
    
    @check_workbook_default_font.setter
    def check_workbook_default_font(self, value : bool) -> None:
        '''When characters in the Excel are Unicode and not be set with correct font in cell style,
        They may appear as block in pdf,image.
        Set this to true to try to use workbook\'s default font to show these characters first.'''
        raise NotImplementedError()
    
    @property
    def output_blank_page_when_nothing_to_print(self) -> bool:
        '''Indicates whether to output a blank page when there is nothing to print.'''
        raise NotImplementedError()
    
    @output_blank_page_when_nothing_to_print.setter
    def output_blank_page_when_nothing_to_print(self, value : bool) -> None:
        '''Indicates whether to output a blank page when there is nothing to print.'''
        raise NotImplementedError()
    
    @property
    def gridline_type(self) -> aspose.cells.GridlineType:
        '''Gets gridline type.'''
        raise NotImplementedError()
    
    @gridline_type.setter
    def gridline_type(self, value : aspose.cells.GridlineType) -> None:
        '''Sets gridline type.'''
        raise NotImplementedError()
    
    @property
    def gridline_color(self) -> aspose.pydrawing.Color:
        '''Gets gridline colr.'''
        raise NotImplementedError()
    
    @gridline_color.setter
    def gridline_color(self, value : aspose.pydrawing.Color) -> None:
        '''Sets gridline colr.'''
        raise NotImplementedError()
    
    @property
    def text_cross_type(self) -> aspose.cells.TextCrossType:
        '''Gets displaying text type when the text width is larger than cell width.'''
        raise NotImplementedError()
    
    @text_cross_type.setter
    def text_cross_type(self, value : aspose.cells.TextCrossType) -> None:
        '''Sets displaying text type when the text width is larger than cell width.'''
        raise NotImplementedError()
    
    @property
    def emf_type(self) -> Any:
        '''Gets an EmfType that specifies the format of the Metafile..'''
        raise NotImplementedError()
    
    @emf_type.setter
    def emf_type(self, value : Any) -> None:
        '''Sets an EmfType that specifies the format of the Metafile..'''
        raise NotImplementedError()
    
    @property
    def default_edit_language(self) -> aspose.cells.DefaultEditLanguage:
        '''Gets default edit language.'''
        raise NotImplementedError()
    
    @default_edit_language.setter
    def default_edit_language(self, value : aspose.cells.DefaultEditLanguage) -> None:
        '''Sets default edit language.'''
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
    def emf_render_setting(self) -> aspose.cells.EmfRenderSetting:
        '''Setting for rendering Emf metafiles in source file.'''
        raise NotImplementedError()
    
    @emf_render_setting.setter
    def emf_render_setting(self, value : aspose.cells.EmfRenderSetting) -> None:
        '''Setting for rendering Emf metafiles in source file.'''
        raise NotImplementedError()
    
    @property
    def custom_render_settings(self) -> aspose.cells.rendering.CustomRenderSettings:
        '''Gets custom settings during rendering.'''
        raise NotImplementedError()
    
    @custom_render_settings.setter
    def custom_render_settings(self, value : aspose.cells.rendering.CustomRenderSettings) -> None:
        '''Sets custom settings during rendering.'''
        raise NotImplementedError()
    

class PageEndSavingArgs(PageSavingArgs):
    '''Info for a page ends saving process.'''
    
    @property
    def page_index(self) -> int:
        '''Current page index, zero based.'''
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        '''Total page count.'''
        raise NotImplementedError()
    
    @property
    def has_more_pages(self) -> bool:
        '''Gets a value indicating whether having more pages to be output.
        The default value is true.'''
        raise NotImplementedError()
    
    @has_more_pages.setter
    def has_more_pages(self, value : bool) -> None:
        '''Sets a value indicating whether having more pages to be output.
        The default value is true.'''
        raise NotImplementedError()
    

class PageSavingArgs:
    '''Info for a page saving process.'''
    
    @property
    def page_index(self) -> int:
        '''Current page index, zero based.'''
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        '''Total page count.'''
        raise NotImplementedError()
    

class PageStartSavingArgs(PageSavingArgs):
    '''Info for a page starts saving process.'''
    
    @property
    def page_index(self) -> int:
        '''Current page index, zero based.'''
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        '''Total page count.'''
        raise NotImplementedError()
    
    @property
    def is_to_output(self) -> bool:
        '''Gets a value indicating whether the page should be output.
        The default value is true.'''
        raise NotImplementedError()
    
    @is_to_output.setter
    def is_to_output(self, value : bool) -> None:
        '''Sets a value indicating whether the page should be output.
        The default value is true.'''
        raise NotImplementedError()
    

class PdfBookmarkEntry:
    '''PdfBookmarkEntry is an entry in pdf bookmark.
    if Text property of current instance is null or "",
    current instance will be hidden and children will be inserted on current level.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def text(self) -> str:
        '''Title of a bookmark.'''
        raise NotImplementedError()
    
    @text.setter
    def text(self, value : str) -> None:
        '''Title of a bookmark.'''
        raise NotImplementedError()
    
    @property
    def destination(self) -> aspose.cells.Cell:
        '''The cell to which the bookmark link.'''
        raise NotImplementedError()
    
    @destination.setter
    def destination(self, value : aspose.cells.Cell) -> None:
        '''The cell to which the bookmark link.'''
        raise NotImplementedError()
    
    @property
    def destination_name(self) -> str:
        '''Gets name of destination.'''
        raise NotImplementedError()
    
    @destination_name.setter
    def destination_name(self, value : str) -> None:
        '''Sets name of destination.'''
        raise NotImplementedError()
    
    @property
    def sub_entry(self) -> List[Any]:
        '''SubEntry of a bookmark.'''
        raise NotImplementedError()
    
    @sub_entry.setter
    def sub_entry(self, value : List[Any]) -> None:
        '''SubEntry of a bookmark.'''
        raise NotImplementedError()
    
    @property
    def is_open(self) -> bool:
        '''When this property is true, the bookmarkentry will expand, otherwise it will collapse.'''
        raise NotImplementedError()
    
    @is_open.setter
    def is_open(self, value : bool) -> None:
        '''When this property is true, the bookmarkentry will expand, otherwise it will collapse.'''
        raise NotImplementedError()
    
    @property
    def is_collapse(self) -> bool:
        '''When this property is true, the bookmarkentry will collapse, otherwise it will expand.'''
        raise NotImplementedError()
    
    @is_collapse.setter
    def is_collapse(self, value : bool) -> None:
        '''When this property is true, the bookmarkentry will collapse, otherwise it will expand.'''
        raise NotImplementedError()
    

class RenderingFont:
    '''Font for rendering.'''
    
    def __init__(self, font_name : str, font_size : float) -> None:
        '''Initializes a new instance of the :py:class:`aspose.cells.rendering.RenderingFont`
        
        :param font_name: font name
        :param font_size: font size in points'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets name of the font.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> float:
        '''Gets size of the font in points.'''
        raise NotImplementedError()
    
    @property
    def bold(self) -> bool:
        '''Gets bold for the font.'''
        raise NotImplementedError()
    
    @bold.setter
    def bold(self, value : bool) -> None:
        '''Sets bold for the font.'''
        raise NotImplementedError()
    
    @property
    def italic(self) -> bool:
        '''Gets italic for the font.'''
        raise NotImplementedError()
    
    @italic.setter
    def italic(self, value : bool) -> None:
        '''Sets italic for the font.'''
        raise NotImplementedError()
    
    @property
    def color(self) -> aspose.pydrawing.Color:
        '''Gets color for the font.'''
        raise NotImplementedError()
    
    @color.setter
    def color(self, value : aspose.pydrawing.Color) -> None:
        '''Sets color for the font.'''
        raise NotImplementedError()
    

class RenderingWatermark:
    '''Watermark for rendering.'''
    
    @overload
    def __init__(self, text : str, rendering_font : aspose.cells.rendering.RenderingFont) -> None:
        '''Creates instance of text watermark.
        
        :param text: watermark text
        :param rendering_font: watermark font'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, image_data : List[int]) -> None:
        '''Creates instance of image watermark.'''
        raise NotImplementedError()
    
    @property
    def rotation(self) -> float:
        '''Gets roation of the watermark in degrees.'''
        raise NotImplementedError()
    
    @rotation.setter
    def rotation(self, value : float) -> None:
        '''Sets roation of the watermark in degrees.'''
        raise NotImplementedError()
    
    @property
    def scale_to_page_percent(self) -> int:
        '''Gets scale relative to target page in percent.'''
        raise NotImplementedError()
    
    @scale_to_page_percent.setter
    def scale_to_page_percent(self, value : int) -> None:
        '''Sets scale relative to target page in percent.'''
        raise NotImplementedError()
    
    @property
    def opacity(self) -> float:
        '''Gets opacity of the watermark in range [0, 1].'''
        raise NotImplementedError()
    
    @opacity.setter
    def opacity(self, value : float) -> None:
        '''Sets opacity of the watermark in range [0, 1].'''
        raise NotImplementedError()
    
    @property
    def is_background(self) -> bool:
        '''Indicates whether the watermark is placed behind page contents.'''
        raise NotImplementedError()
    
    @is_background.setter
    def is_background(self, value : bool) -> None:
        '''Indicates whether the watermark is placed behind page contents.'''
        raise NotImplementedError()
    
    @property
    def text(self) -> str:
        '''Gets text of the watermark.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.rendering.RenderingFont:
        '''Gets font of the watermark.'''
        raise NotImplementedError()
    
    @property
    def image(self) -> List[int]:
        '''Gets image of the watermark.'''
        raise NotImplementedError()
    
    @property
    def h_alignment(self) -> aspose.cells.TextAlignmentType:
        '''Gets horizontal alignment of the watermark to the page.'''
        raise NotImplementedError()
    
    @h_alignment.setter
    def h_alignment(self, value : aspose.cells.TextAlignmentType) -> None:
        '''Sets horizontal alignment of the watermark to the page.'''
        raise NotImplementedError()
    
    @property
    def v_alignment(self) -> aspose.cells.TextAlignmentType:
        '''Gets vertical alignment of the watermark to the page.'''
        raise NotImplementedError()
    
    @v_alignment.setter
    def v_alignment(self, value : aspose.cells.TextAlignmentType) -> None:
        '''Sets vertical alignment of the watermark to the page.'''
        raise NotImplementedError()
    
    @property
    def offset_x(self) -> float:
        '''Gets offset value to :py:attr:`aspose.cells.rendering.RenderingWatermark.h_alignment`'''
        raise NotImplementedError()
    
    @offset_x.setter
    def offset_x(self, value : float) -> None:
        '''Sets offset value to :py:attr:`aspose.cells.rendering.RenderingWatermark.h_alignment`'''
        raise NotImplementedError()
    
    @property
    def offset_y(self) -> float:
        '''Gets offset value to :py:attr:`aspose.cells.rendering.RenderingWatermark.v_alignment`'''
        raise NotImplementedError()
    
    @offset_y.setter
    def offset_y(self, value : float) -> None:
        '''Sets offset value to :py:attr:`aspose.cells.rendering.RenderingWatermark.v_alignment`'''
        raise NotImplementedError()
    

class SheetPrintingPreview:
    '''Worksheet printing preview.'''
    
    def __init__(self, sheet : aspose.cells.Worksheet, options : aspose.cells.rendering.ImageOrPrintOptions) -> None:
        '''The construct of SheetPrintingPreview
        
        :param sheet: Indicate which spreadsheet to be printed.
        :param options: ImageOrPrintOptions contains some property of output'''
        raise NotImplementedError()
    
    @property
    def evaluated_page_count(self) -> int:
        '''Evaluate the total page count of this worksheet'''
        raise NotImplementedError()
    

class SheetRender:
    '''Represents a worksheet render which can render worksheet to various images such as (BMP, PNG, JPEG, TIFF..)
    The constructor of this class , must be used after modification of pagesetup, cell style.'''
    
    def __init__(self, worksheet : aspose.cells.Worksheet, options : aspose.cells.rendering.ImageOrPrintOptions) -> None:
        '''the construct of SheetRender, need worksheet and ImageOrPrintOptions as params
        
        :param worksheet: Indicate which spreadsheet to be rendered.
        :param options: ImageOrPrintOptions contains some property of output image'''
        raise NotImplementedError()
    
    @overload
    def to_image(self, page_index : int, file_name : str) -> None:
        '''Render certain page to a file.
        
        :param page_index: indicate which page is to be converted
        :param file_name: filename of the output image'''
        raise NotImplementedError()
    
    @overload
    def to_image(self, page_index : int, stream : io._IOBase) -> None:
        '''Render certain page to a stream.
        
        :param page_index: indicate which page is to be converted
        :param stream: the stream of the output image'''
        raise NotImplementedError()
    
    @overload
    def to_tiff(self, stream : io._IOBase) -> None:
        '''Render whole worksheet as Tiff Image to stream.
        
        :param stream: the stream of the output image'''
        raise NotImplementedError()
    
    @overload
    def to_tiff(self, filename : str) -> None:
        '''Render whole worksheet as Tiff Image to a file.
        
        :param filename: the filename of the output image'''
        raise NotImplementedError()
    
    @overload
    def to_printer(self, printer_name : str) -> None:
        '''Render worksheet to Printer
        
        :param printer_name: the name of the printer , for example: "Microsoft Office Document Image Writer"'''
        raise NotImplementedError()
    
    @overload
    def to_printer(self, printer_name : str, job_name : str) -> None:
        '''Render worksheet to Printer
        
        :param printer_name: the name of the printer , for example: "Microsoft Office Document Image Writer"
        :param job_name: set the print job name'''
        raise NotImplementedError()
    
    @overload
    def to_printer(self, printer_settings : Any) -> None:
        '''Render worksheet to Printer
        
        :param printer_settings: the settings of printer, e.g. PrinterName, Duplex'''
        raise NotImplementedError()
    
    @overload
    def to_printer(self, printer_settings : Any, job_name : str) -> None:
        '''Render worksheet to Printer
        
        :param printer_settings: the settings of printer, e.g. PrinterName, Duplex
        :param job_name: set the print job name'''
        raise NotImplementedError()
    
    @overload
    def to_printer(self, printer_name : str, print_page_index : int, print_page_count : int) -> None:
        '''Render worksheet to Printer
        
        :param printer_name: the name of the printer , for example: "Microsoft Office Document Image Writer"
        :param print_page_index: the 0-based index of the first page to print, it must be in Range [0, SheetRender.PageCount-1]
        :param print_page_count: the number of pages to print, it must be greater than zero'''
        raise NotImplementedError()
    
    def get_page_size_inch(self, page_index : int) -> List[float]:
        '''Get page size in inch of output image.
        
        :param page_index: The page index is based on zero.
        :returns: Page size of image, [0] for width and [1] for height'''
        raise NotImplementedError()
    
    def custom_print(self, next_page_after_print : bool, print_page_event_args : Any) -> int:
        '''Client can control page setting of printer when print each page using this function.
        
        :param next_page_after_print: If true , printer will go to next page after print current page
        :param print_page_event_args: System.Drawing.Printing.PrintPageEventArgs
        :returns: Indirect next page index,  based on zero'''
        raise NotImplementedError()
    
    def dispose(self) -> None:
        '''Releases resources created and used for rendering.'''
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        '''Gets the total page count of current worksheet.'''
        raise NotImplementedError()
    
    @property
    def page_scale(self) -> float:
        '''Gets calculated page scale of the sheet.
        Returns the set scale if :py:attr:`aspose.cells.PageSetup.zoom` is set. Otherwise, returns the calculated scale according to :py:attr:`aspose.cells.PageSetup.fit_to_pages_wide` and :py:attr:`aspose.cells.PageSetup.fit_to_pages_tall`.'''
        raise NotImplementedError()
    

class SheetSet:
    '''Describes a set of sheets.'''
    
    @overload
    def __init__(self, sheet_indexes : List[int]) -> None:
        '''Creates a sheet set based on exact sheet indexes.
        
        :param sheet_indexes: zero based sheet indexes.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, sheet_names : List[str]) -> None:
        '''Creates a sheet set based on exact sheet names.
        
        :param sheet_names: sheet names.'''
        raise NotImplementedError()
    
    @property
    def active(self) -> aspose.cells.rendering.SheetSet:
        '''Gets a set with active sheet of the workbook.'''
        raise NotImplementedError()

    @property
    def visible(self) -> aspose.cells.rendering.SheetSet:
        '''Gets a set with visible sheets of the workbook in their original order.'''
        raise NotImplementedError()

    @property
    def all(self) -> aspose.cells.rendering.SheetSet:
        '''Gets a set with all sheets of the workbook in their original order.'''
        raise NotImplementedError()


class SvgImageOptions(ImageOrPrintOptions):
    '''Options for generating Svg image.'''
    
    def __init__(self) -> None:
        '''Ctor.'''
        raise NotImplementedError()
    
    @overload
    def set_desired_size(self, desired_width : int, desired_height : int) -> None:
        '''Sets desired width and height of image.
        
        :param desired_width: desired width in pixels
        :param desired_height: desired height in pixels'''
        raise NotImplementedError()
    
    @overload
    def set_desired_size(self, desired_width : int, desired_height : int, keep_aspect_ratio : bool) -> None:
        '''Sets desired width and height of image.
        
        :param desired_width: desired width in pixels
        :param desired_height: desired height in pixels
        :param keep_aspect_ratio: whether to keep aspect ratio of origin image'''
        raise NotImplementedError()
    
    @property
    def save_format(self) -> aspose.cells.SaveFormat:
        '''Gets the output file format type
        Support Tiff/XPS'''
        raise NotImplementedError()
    
    @save_format.setter
    def save_format(self, value : aspose.cells.SaveFormat) -> None:
        '''Sets the output file format type
        Support Tiff/XPS'''
        raise NotImplementedError()
    
    @property
    def print_with_status_dialog(self) -> bool:
        '''If PrintWithStatusDialog = true , there will be a dialog that shows current print status.
        else no such dialog will show.'''
        raise NotImplementedError()
    
    @print_with_status_dialog.setter
    def print_with_status_dialog(self, value : bool) -> None:
        '''If PrintWithStatusDialog = true , there will be a dialog that shows current print status.
        else no such dialog will show.'''
        raise NotImplementedError()
    
    @property
    def horizontal_resolution(self) -> int:
        '''Gets the horizontal resolution for generated images, in dots per inch.'''
        raise NotImplementedError()
    
    @horizontal_resolution.setter
    def horizontal_resolution(self, value : int) -> None:
        '''Sets the horizontal resolution for generated images, in dots per inch.'''
        raise NotImplementedError()
    
    @property
    def vertical_resolution(self) -> int:
        '''Gets the vertical resolution for generated images, in dots per inch.'''
        raise NotImplementedError()
    
    @vertical_resolution.setter
    def vertical_resolution(self, value : int) -> None:
        '''Sets the vertical resolution for generated images, in dots per inch.'''
        raise NotImplementedError()
    
    @property
    def tiff_compression(self) -> aspose.cells.rendering.TiffCompression:
        '''Gets the type of compression to apply only when saving pages to the ``Tiff`` format.'''
        raise NotImplementedError()
    
    @tiff_compression.setter
    def tiff_compression(self, value : aspose.cells.rendering.TiffCompression) -> None:
        '''Sets the type of compression to apply only when saving pages to the ``Tiff`` format.'''
        raise NotImplementedError()
    
    @property
    def tiff_color_depth(self) -> aspose.cells.rendering.ColorDepth:
        '''Gets bit depth to apply only when saving pages to the ``Tiff`` format.'''
        raise NotImplementedError()
    
    @tiff_color_depth.setter
    def tiff_color_depth(self, value : aspose.cells.rendering.ColorDepth) -> None:
        '''Sets bit depth to apply only when saving pages to the ``Tiff`` format.'''
        raise NotImplementedError()
    
    @property
    def tiff_binarization_method(self) -> aspose.cells.rendering.ImageBinarizationMethod:
        '''Gets method used while converting images to 1 bpp format
        when :py:attr:`aspose.cells.rendering.ImageOrPrintOptions.image_type` is Tiff and :py:attr:`aspose.cells.rendering.ImageOrPrintOptions.tiff_compression` is equal to Ccitt3 or Ccitt4.'''
        raise NotImplementedError()
    
    @tiff_binarization_method.setter
    def tiff_binarization_method(self, value : aspose.cells.rendering.ImageBinarizationMethod) -> None:
        '''Sets method used while converting images to 1 bpp format
        when :py:attr:`aspose.cells.rendering.ImageOrPrintOptions.image_type` is Tiff and :py:attr:`aspose.cells.rendering.ImageOrPrintOptions.tiff_compression` is equal to Ccitt3 or Ccitt4.'''
        raise NotImplementedError()
    
    @property
    def printing_page(self) -> aspose.cells.PrintingPageType:
        '''Indicates which pages will not be printed.'''
        raise NotImplementedError()
    
    @printing_page.setter
    def printing_page(self, value : aspose.cells.PrintingPageType) -> None:
        '''Indicates which pages will not be printed.'''
        raise NotImplementedError()
    
    @property
    def quality(self) -> int:
        '''Gets a value determining the quality of the generated  images
        to apply only when saving pages to the ``Jpeg`` format. The default value is 100'''
        raise NotImplementedError()
    
    @quality.setter
    def quality(self, value : int) -> None:
        '''Sets a value determining the quality of the generated  images
        to apply only when saving pages to the ``Jpeg`` format. The default value is 100'''
        raise NotImplementedError()
    
    @property
    def image_type(self) -> aspose.cells.drawing.ImageType:
        '''Gets the format of the generated images.
        default value: PNG.'''
        raise NotImplementedError()
    
    @image_type.setter
    def image_type(self, value : aspose.cells.drawing.ImageType) -> None:
        '''Sets the format of the generated images.
        default value: PNG.'''
        raise NotImplementedError()
    
    @property
    def is_cell_auto_fit(self) -> bool:
        '''Indicates whether the width and height of the cells is automatically fitted by cell value.
        The default value is false.'''
        raise NotImplementedError()
    
    @is_cell_auto_fit.setter
    def is_cell_auto_fit(self, value : bool) -> None:
        '''Indicates whether the width and height of the cells is automatically fitted by cell value.
        The default value is false.'''
        raise NotImplementedError()
    
    @property
    def one_page_per_sheet(self) -> bool:
        '''If OnePagePerSheet is true , all content of one sheet will output to only one page in result.
        The paper size of pagesetup will be invalid, and the other settings of pagesetup
        will still take effect.'''
        raise NotImplementedError()
    
    @one_page_per_sheet.setter
    def one_page_per_sheet(self, value : bool) -> None:
        '''If OnePagePerSheet is true , all content of one sheet will output to only one page in result.
        The paper size of pagesetup will be invalid, and the other settings of pagesetup
        will still take effect.'''
        raise NotImplementedError()
    
    @property
    def all_columns_in_one_page_per_sheet(self) -> bool:
        '''If AllColumnsInOnePagePerSheet is true , all column content of one sheet will output to only one page in result.
        The width of paper size of pagesetup will be invalid, and the other settings of pagesetup
        will still take effect.'''
        raise NotImplementedError()
    
    @all_columns_in_one_page_per_sheet.setter
    def all_columns_in_one_page_per_sheet(self, value : bool) -> None:
        '''If AllColumnsInOnePagePerSheet is true , all column content of one sheet will output to only one page in result.
        The width of paper size of pagesetup will be invalid, and the other settings of pagesetup
        will still take effect.'''
        raise NotImplementedError()
    
    @property
    def draw_object_event_handler(self) -> aspose.cells.rendering.DrawObjectEventHandler:
        '''Implements this interface to get DrawObject and Bound when rendering.'''
        raise NotImplementedError()
    
    @draw_object_event_handler.setter
    def draw_object_event_handler(self, value : aspose.cells.rendering.DrawObjectEventHandler) -> None:
        '''Implements this interface to get DrawObject and Bound when rendering.'''
        raise NotImplementedError()
    
    @property
    def chart_image_type(self) -> Any:
        '''Indicate the chart imagetype when converting.
        default value: PNG.'''
        raise NotImplementedError()
    
    @chart_image_type.setter
    def chart_image_type(self, value : Any) -> None:
        '''Indicate the chart imagetype when converting.
        default value: PNG.'''
        raise NotImplementedError()
    
    @property
    def embeded_image_name_in_svg(self) -> str:
        '''Indicate the filename of embedded image in svg.
        This should be full path with directory like "c:\\xpsEmbedded"'''
        raise NotImplementedError()
    
    @embeded_image_name_in_svg.setter
    def embeded_image_name_in_svg(self, value : str) -> None:
        '''Indicate the filename of embedded image in svg.
        This should be full path with directory like "c:\\xpsEmbedded"'''
        raise NotImplementedError()
    
    @property
    def svg_fit_to_view_port(self) -> bool:
        '''if this property is true, the generated svg will fit to view port.'''
        raise NotImplementedError()
    
    @svg_fit_to_view_port.setter
    def svg_fit_to_view_port(self, value : bool) -> None:
        '''if this property is true, the generated svg will fit to view port.'''
        raise NotImplementedError()
    
    @property
    def svg_css_prefix(self) -> str:
        '''Gets and sets the prefix of the css name in svg,the default value is empty string.'''
        raise NotImplementedError()
    
    @svg_css_prefix.setter
    def svg_css_prefix(self, value : str) -> None:
        '''Gets and sets the prefix of the css name in svg,the default value is empty string.'''
        raise NotImplementedError()
    
    @property
    def only_area(self) -> bool:
        '''If this property is true , one Area will be output, and no scale will take effect.'''
        raise NotImplementedError()
    
    @only_area.setter
    def only_area(self, value : bool) -> None:
        '''If this property is true , one Area will be output, and no scale will take effect.'''
        raise NotImplementedError()
    
    @property
    def text_rendering_hint(self) -> Any:
        '''Specifies the quality of text rendering.
        The default value is TextRenderingHint.SystemDefault'''
        raise NotImplementedError()
    
    @text_rendering_hint.setter
    def text_rendering_hint(self, value : Any) -> None:
        '''Specifies the quality of text rendering.
        The default value is TextRenderingHint.SystemDefault'''
        raise NotImplementedError()
    
    @property
    def smoothing_mode(self) -> Any:
        '''Specifies whether smoothing (antialiasing) is applied to lines and curves and the edges of filled areas.
        The default value is SmoothingMode.None'''
        raise NotImplementedError()
    
    @smoothing_mode.setter
    def smoothing_mode(self, value : Any) -> None:
        '''Specifies whether smoothing (antialiasing) is applied to lines and curves and the edges of filled areas.
        The default value is SmoothingMode.None'''
        raise NotImplementedError()
    
    @property
    def transparent(self) -> bool:
        '''Indicates if the background of generated image should be transparent.'''
        raise NotImplementedError()
    
    @transparent.setter
    def transparent(self, value : bool) -> None:
        '''Indicates if the background of generated image should be transparent.'''
        raise NotImplementedError()
    
    @property
    def pixel_format(self) -> Any:
        '''Gets the pixel format for the generated images.'''
        raise NotImplementedError()
    
    @pixel_format.setter
    def pixel_format(self, value : Any) -> None:
        '''Sets the pixel format for the generated images.'''
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
    def page_saving_callback(self) -> aspose.cells.rendering.IPageSavingCallback:
        '''Control/Indicate progress of page saving process.'''
        raise NotImplementedError()
    
    @page_saving_callback.setter
    def page_saving_callback(self, value : aspose.cells.rendering.IPageSavingCallback) -> None:
        '''Control/Indicate progress of page saving process.'''
        raise NotImplementedError()
    
    @property
    def is_font_substitution_char_granularity(self) -> bool:
        '''Indicates whether to only substitute the font of character when the cell font is not compatibility for it.'''
        raise NotImplementedError()
    
    @is_font_substitution_char_granularity.setter
    def is_font_substitution_char_granularity(self, value : bool) -> None:
        '''Indicates whether to only substitute the font of character when the cell font is not compatibility for it.'''
        raise NotImplementedError()
    
    @property
    def page_index(self) -> int:
        '''Gets the 0-based index of the first page to save.'''
        raise NotImplementedError()
    
    @page_index.setter
    def page_index(self, value : int) -> None:
        '''Sets the 0-based index of the first page to save.'''
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        '''Gets the number of pages to save.'''
        raise NotImplementedError()
    
    @page_count.setter
    def page_count(self, value : int) -> None:
        '''Sets the number of pages to save.'''
        raise NotImplementedError()
    
    @property
    def is_optimized(self) -> bool:
        '''Indicates whether to optimize the output elements.'''
        raise NotImplementedError()
    
    @is_optimized.setter
    def is_optimized(self, value : bool) -> None:
        '''Indicates whether to optimize the output elements.'''
        raise NotImplementedError()
    
    @property
    def default_font(self) -> str:
        '''When characters in the Excel are Unicode and not be set with correct font in cell style,
        They may appear as block in pdf,image.
        Set the DefaultFont such as MingLiu or MS Gothic to show these characters.
        If this property is not set, Aspose.Cells will use system default font to show these unicode characters.'''
        raise NotImplementedError()
    
    @default_font.setter
    def default_font(self, value : str) -> None:
        '''When characters in the Excel are Unicode and not be set with correct font in cell style,
        They may appear as block in pdf,image.
        Set the DefaultFont such as MingLiu or MS Gothic to show these characters.
        If this property is not set, Aspose.Cells will use system default font to show these unicode characters.'''
        raise NotImplementedError()
    
    @property
    def check_workbook_default_font(self) -> bool:
        '''When characters in the Excel are Unicode and not be set with correct font in cell style,
        They may appear as block in pdf,image.
        Set this to true to try to use workbook\'s default font to show these characters first.'''
        raise NotImplementedError()
    
    @check_workbook_default_font.setter
    def check_workbook_default_font(self, value : bool) -> None:
        '''When characters in the Excel are Unicode and not be set with correct font in cell style,
        They may appear as block in pdf,image.
        Set this to true to try to use workbook\'s default font to show these characters first.'''
        raise NotImplementedError()
    
    @property
    def output_blank_page_when_nothing_to_print(self) -> bool:
        '''Indicates whether to output a blank page when there is nothing to print.'''
        raise NotImplementedError()
    
    @output_blank_page_when_nothing_to_print.setter
    def output_blank_page_when_nothing_to_print(self, value : bool) -> None:
        '''Indicates whether to output a blank page when there is nothing to print.'''
        raise NotImplementedError()
    
    @property
    def gridline_type(self) -> aspose.cells.GridlineType:
        '''Gets gridline type.'''
        raise NotImplementedError()
    
    @gridline_type.setter
    def gridline_type(self, value : aspose.cells.GridlineType) -> None:
        '''Sets gridline type.'''
        raise NotImplementedError()
    
    @property
    def gridline_color(self) -> aspose.pydrawing.Color:
        '''Gets gridline colr.'''
        raise NotImplementedError()
    
    @gridline_color.setter
    def gridline_color(self, value : aspose.pydrawing.Color) -> None:
        '''Sets gridline colr.'''
        raise NotImplementedError()
    
    @property
    def text_cross_type(self) -> aspose.cells.TextCrossType:
        '''Gets displaying text type when the text width is larger than cell width.'''
        raise NotImplementedError()
    
    @text_cross_type.setter
    def text_cross_type(self, value : aspose.cells.TextCrossType) -> None:
        '''Sets displaying text type when the text width is larger than cell width.'''
        raise NotImplementedError()
    
    @property
    def emf_type(self) -> Any:
        '''Gets an EmfType that specifies the format of the Metafile..'''
        raise NotImplementedError()
    
    @emf_type.setter
    def emf_type(self, value : Any) -> None:
        '''Sets an EmfType that specifies the format of the Metafile..'''
        raise NotImplementedError()
    
    @property
    def default_edit_language(self) -> aspose.cells.DefaultEditLanguage:
        '''Gets default edit language.'''
        raise NotImplementedError()
    
    @default_edit_language.setter
    def default_edit_language(self, value : aspose.cells.DefaultEditLanguage) -> None:
        '''Sets default edit language.'''
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
    def emf_render_setting(self) -> aspose.cells.EmfRenderSetting:
        '''Setting for rendering Emf metafiles in source file.'''
        raise NotImplementedError()
    
    @emf_render_setting.setter
    def emf_render_setting(self, value : aspose.cells.EmfRenderSetting) -> None:
        '''Setting for rendering Emf metafiles in source file.'''
        raise NotImplementedError()
    
    @property
    def custom_render_settings(self) -> aspose.cells.rendering.CustomRenderSettings:
        '''Gets custom settings during rendering.'''
        raise NotImplementedError()
    
    @custom_render_settings.setter
    def custom_render_settings(self, value : aspose.cells.rendering.CustomRenderSettings) -> None:
        '''Sets custom settings during rendering.'''
        raise NotImplementedError()
    
    @property
    def fit_to_view_port(self) -> bool:
        '''if this property is true, the generated svg will fit to view port.'''
        raise NotImplementedError()
    
    @fit_to_view_port.setter
    def fit_to_view_port(self, value : bool) -> None:
        '''if this property is true, the generated svg will fit to view port.'''
        raise NotImplementedError()
    
    @property
    def css_prefix(self) -> str:
        '''Gets and sets the prefix of the css name in svg,the default value is empty string.'''
        raise NotImplementedError()
    
    @css_prefix.setter
    def css_prefix(self, value : str) -> None:
        '''Gets and sets the prefix of the css name in svg,the default value is empty string.'''
        raise NotImplementedError()
    
    @property
    def embedded_font_type(self) -> aspose.cells.rendering.SvgEmbeddedFontType:
        '''Gets the type of font that embedded in Svg.'''
        raise NotImplementedError()
    
    @embedded_font_type.setter
    def embedded_font_type(self, value : aspose.cells.rendering.SvgEmbeddedFontType) -> None:
        '''Sets the type of font that embedded in Svg.'''
        raise NotImplementedError()
    

class WorkbookPrintingPreview:
    '''Workbook printing preview.'''
    
    def __init__(self, workbook : aspose.cells.Workbook, options : aspose.cells.rendering.ImageOrPrintOptions) -> None:
        '''The construct of WorkbookPrintingPreview
        
        :param workbook: Indicate which workbook to be printed.
        :param options: ImageOrPrintOptions contains some property of output'''
        raise NotImplementedError()
    
    @property
    def evaluated_page_count(self) -> int:
        '''Evaluate the total page count of this workbook'''
        raise NotImplementedError()
    

class WorkbookRender:
    '''Represents a Workbook render.
    The constructor of this class , must be used after modification of pagesetup, cell style.'''
    
    def __init__(self, workbook : aspose.cells.Workbook, options : aspose.cells.rendering.ImageOrPrintOptions) -> None:
        '''The construct of WorkbookRender
        
        :param workbook: Indicate which workbook to be rendered.
        :param options: ImageOrPrintOptions contains some property of output image'''
        raise NotImplementedError()
    
    @overload
    def to_image(self, stream : io._IOBase) -> None:
        '''Render whole workbook as Tiff Image to stream.
        
        :param stream: the stream of the output image'''
        raise NotImplementedError()
    
    @overload
    def to_image(self, filename : str) -> None:
        '''Render whole workbook as Tiff Image to a file.
        
        :param filename: the filename of the output image'''
        raise NotImplementedError()
    
    @overload
    def to_image(self, page_index : int, file_name : str) -> None:
        '''Render certain page to a file.
        
        :param page_index: indicate which page is to be converted
        :param file_name: filename of the output image'''
        raise NotImplementedError()
    
    @overload
    def to_image(self, page_index : int, stream : io._IOBase) -> None:
        '''Render certain page to a stream.
        
        :param page_index: indicate which page is to be converted
        :param stream: the stream of the output image'''
        raise NotImplementedError()
    
    @overload
    def to_printer(self, printer_name : str) -> None:
        '''Render workbook to Printer
        
        :param printer_name: the name of the printer , for example: "Microsoft Office Document Image Writer"'''
        raise NotImplementedError()
    
    @overload
    def to_printer(self, printer_name : str, job_name : str) -> None:
        '''Render workbook to Printer
        
        :param printer_name: the name of the printer , for example: "Microsoft Office Document Image Writer"
        :param job_name: set the print job name'''
        raise NotImplementedError()
    
    @overload
    def to_printer(self, printer_settings : Any) -> None:
        '''Render workbook to Printer
        
        :param printer_settings: the settings of printer, e.g. PrinterName, Duplex'''
        raise NotImplementedError()
    
    @overload
    def to_printer(self, printer_settings : Any, job_name : str) -> None:
        '''Render workbook to Printer
        
        :param printer_settings: the settings of printer, e.g. PrinterName, Duplex
        :param job_name: set the print job name'''
        raise NotImplementedError()
    
    @overload
    def to_printer(self, printer_name : str, print_page_index : int, print_page_count : int) -> None:
        '''Render workbook to Printer
        
        :param printer_name: the name of the printer , for example: "Microsoft Office Document Image Writer"
        :param print_page_index: the 0-based index of the first page to print, it must be in Range [0, WorkbookRender.PageCount-1]
        :param print_page_count: the number of pages to print, it must be greater than zero'''
        raise NotImplementedError()
    
    def get_page_size_inch(self, page_index : int) -> List[float]:
        '''Get page size in inch of output image.
        
        :param page_index: The page index is based on zero.
        :returns: Page size of image, [0] for width and [1] for height'''
        raise NotImplementedError()
    
    def custom_print(self, next_page_after_print : bool, print_page_event_args : Any) -> int:
        '''Client can control page setting of printer when print each page using this function.
        
        :param next_page_after_print: If true , printer will go to next page after print current page
        :param print_page_event_args: System.Drawing.Printing.PrintPageEventArgs
        :returns: Indirect next page index,  based on zero'''
        raise NotImplementedError()
    
    def dispose(self) -> None:
        '''Releases resources created and used for rendering.'''
        raise NotImplementedError()
    
    @property
    def page_count(self) -> int:
        '''Gets the total page count of workbook.'''
        raise NotImplementedError()
    

class ColorDepth:
    '''Enumerates Bit Depth Type for tiff image.'''
    
    DEFAULT : ColorDepth
    '''Default value, not set value.'''
    FORMAT_1BPP : ColorDepth
    '''1 bit per pixel'''
    FORMAT_4BPP : ColorDepth
    '''4 bits per pixel'''
    FORMAT_8BPP : ColorDepth
    '''8 bits per pixel'''
    FORMAT_24BPP : ColorDepth
    '''24 bits per pixel'''
    FORMAT_32BPP : ColorDepth
    '''32 bits per pixel'''

class CommentTitleType:
    '''Represents comment title type while rendering when comment is set to display at end of sheet.'''
    
    CELL : CommentTitleType
    '''Represents comment title cell.'''
    COMMENT : CommentTitleType
    '''Represents comment title comment.'''
    NOTE : CommentTitleType
    '''Represents comment title note.'''
    REPLY : CommentTitleType
    '''Represents comment title reply.'''

class DrawObjectEnum:
    '''Indicate Cell or Image of DrawObject.'''
    
    IMAGE : DrawObjectEnum
    '''Indicate DrawObject is an Image'''
    CELL : DrawObjectEnum
    '''indicate DrawObject is an Cell'''

class HtmlEmbeddedFontType:
    '''Represents the embedded font type in html.'''
    
    NONE : HtmlEmbeddedFontType
    '''Not embed font.'''
    WOFF : HtmlEmbeddedFontType
    '''Embed WOFF font.'''

class ImageBinarizationMethod:
    '''Specifies the method used to binarize image.'''
    
    THRESHOLD : ImageBinarizationMethod
    '''Specifies threshold method.'''
    FLOYD_STEINBERG_DITHERING : ImageBinarizationMethod
    '''Specifies dithering using Floyd-Steinberg error diffusion method.'''

class PdfCompliance:
    '''Allowing user to set PDF conversion\'s Compatibility'''
    
    NONE : PdfCompliance
    '''Pdf format compatible with PDF 1.4'''
    PDF14 : PdfCompliance
    '''Pdf format compatible with PDF 1.4'''
    PDF15 : PdfCompliance
    '''Pdf format compatible with PDF 1.5'''
    PDF16 : PdfCompliance
    '''Pdf format compatible with PDF 1.6'''
    PDF17 : PdfCompliance
    '''Pdf format compatible with PDF 1.7'''
    PDF_A1B : PdfCompliance
    '''Pdf format compatible with PDF/A-1b(ISO 19005-1)'''
    PDF_A1A : PdfCompliance
    '''Pdf format compatible with PDF/A-1a(ISO 19005-1)'''
    PDF_A2B : PdfCompliance
    '''Pdf format compatible with PDF/A-2b(ISO 19005-2)'''
    PDF_A2U : PdfCompliance
    '''Pdf format compatible with PDF/A-2u(ISO 19005-2)'''
    PDF_A2A : PdfCompliance
    '''Pdf format compatible with PDF/A-2a(ISO 19005-2)'''
    PDF_A3B : PdfCompliance
    '''Pdf format compatible with PDF/A-3b(ISO 19005-3)'''
    PDF_A3U : PdfCompliance
    '''Pdf format compatible with PDF/A-3u(ISO 19005-3)'''
    PDF_A3A : PdfCompliance
    '''Pdf format compatible with PDF/A-3a(ISO 19005-3)'''

class PdfCompressionCore:
    '''Specifies a type of compression applied to all content in the PDF file except images.'''
    
    NONE : PdfCompressionCore
    '''None'''
    RLE : PdfCompressionCore
    '''Rle'''
    LZW : PdfCompressionCore
    '''Lzw'''
    FLATE : PdfCompressionCore
    '''Flate'''

class PdfCustomPropertiesExport:
    '''Specifies the way :py:class:`aspose.cells.properties.CustomDocumentPropertyCollection` are exported to PDF file.'''
    
    NONE : PdfCustomPropertiesExport
    '''No custom properties are exported.'''
    STANDARD : PdfCustomPropertiesExport
    '''Custom properties are exported as entries in Info dictionary.'''

class PdfFontEncoding:
    '''Represents pdf embedded font encoding.'''
    
    IDENTITY : PdfFontEncoding
    '''Represents use Identity-H encoding for all embedded fonts in pdf.'''
    ANSI_PREFER : PdfFontEncoding
    '''Represents prefer to use WinAnsiEncoding for TrueType fonts with characters 32-127,
    otherwise, Identity-H encoding will be used for embedded fonts in pdf.'''

class PdfOptimizationType:
    '''Specifies a type of optimization.'''
    
    STANDARD : PdfOptimizationType
    '''High print quality'''
    MINIMUM_SIZE : PdfOptimizationType
    '''File size is more important than print quality'''

class SvgEmbeddedFontType:
    '''Represents the embedded font type in Svg image.'''
    
    NONE : SvgEmbeddedFontType
    '''Not Embed font.'''
    WOFF : SvgEmbeddedFontType
    '''Embed WOFF font.'''

class TiffCompression:
    '''Specifies what type of compression to apply when saving images into TIFF format file.'''
    
    COMPRESSION_NONE : TiffCompression
    '''Specifies no compression.'''
    COMPRESSION_RLE : TiffCompression
    '''Specifies the RLE compression scheme.'''
    COMPRESSION_LZW : TiffCompression
    '''Specifies the LZW compression scheme.'''
    COMPRESSION_CCITT3 : TiffCompression
    '''Specifies the CCITT3 compression scheme.'''
    COMPRESSION_CCITT4 : TiffCompression
    '''Specifies the CCITT4 compression scheme.'''

