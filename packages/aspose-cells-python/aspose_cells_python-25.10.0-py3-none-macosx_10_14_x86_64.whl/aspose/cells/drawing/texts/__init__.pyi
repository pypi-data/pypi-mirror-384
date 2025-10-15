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

class AutoNumberedBulletValue:
    '''Represents automatic numbered bullet.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.BulletType:
        '''Gets the type of the bullet.'''
        raise NotImplementedError()
    
    @property
    def start_at(self) -> int:
        '''Gets and sets the starting number of the bullet.'''
        raise NotImplementedError()
    
    @start_at.setter
    def start_at(self, value : int) -> None:
        '''Gets and sets the starting number of the bullet.'''
        raise NotImplementedError()
    
    @property
    def autonumber_scheme(self) -> aspose.cells.drawing.texts.TextAutonumberScheme:
        '''Represents the scheme of automatic number.'''
        raise NotImplementedError()
    
    @autonumber_scheme.setter
    def autonumber_scheme(self, value : aspose.cells.drawing.texts.TextAutonumberScheme) -> None:
        '''Represents the scheme of automatic number.'''
        raise NotImplementedError()
    

class Bullet:
    '''Represents the bullet points should be applied to a paragraph.'''
    
    @property
    def bullet_value(self) -> Aspose.Cells.Drawing.Texts.BulletValue:
        '''Gets the value of bullet.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.BulletType:
        '''Gets and sets the type of bullet.'''
        raise NotImplementedError()
    
    @type.setter
    def type(self, value : aspose.cells.drawing.texts.BulletType) -> None:
        '''Gets and sets the type of bullet.'''
        raise NotImplementedError()
    
    @property
    def font_name(self) -> str:
        '''Get and sets the name of the font.'''
        raise NotImplementedError()
    
    @font_name.setter
    def font_name(self, value : str) -> None:
        '''Get and sets the name of the font.'''
        raise NotImplementedError()
    

class CharacterBulletValue:
    '''Represents the character bullet.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.BulletType:
        '''Gets the type of the bullet.'''
        raise NotImplementedError()
    
    @property
    def character(self) -> System.Char:
        '''Gets and sets character of the bullet.'''
        raise NotImplementedError()
    
    @character.setter
    def character(self, value : System.Char) -> None:
        '''Gets and sets character of the bullet.'''
        raise NotImplementedError()
    

class FontSettingCollection:
    '''Represents the list of :py:class:`aspose.cells.FontSetting`.'''
    
    @overload
    def replace(self, index : int, count : int, text : str) -> None:
        '''Replace the text.
        
        :param index: The start index.
        :param count: The count of characters.
        :param text: The text.'''
        raise NotImplementedError()
    
    @overload
    def replace(self, old_value : str, new_value : str) -> None:
        '''Replace the text.
        
        :param old_value: The old text.
        :param new_value: The new text.'''
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.FontSetting]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.FontSetting], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.FontSetting, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.FontSetting, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.FontSetting) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.FontSetting, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.FontSetting, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def get_paragraph_enumerator(self) -> collections.abc.Iterator[Any]:
        '''Gets the enumerator of the paragraphs.'''
        raise NotImplementedError()
    
    def append_text(self, text : str) -> None:
        '''Appends the text.
        
        :param text: The text.'''
        raise NotImplementedError()
    
    def insert_text(self, index : int, text : str) -> None:
        '''Insert index at the position.
        
        :param index: The start index.
        :param text: The text.'''
        raise NotImplementedError()
    
    def delete_text(self, index : int, count : int) -> None:
        '''Delete some characters.
        
        :param index: The start index.
        :param count: The count of characters.'''
        raise NotImplementedError()
    
    def format(self, start_index : int, length : int, font : aspose.cells.Font, flag : aspose.cells.StyleFlag) -> None:
        '''Format the text with font setting.
        
        :param start_index: The start index.
        :param length: The length.
        :param font: The font.
        :param flag: The flags of the font.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.FontSetting) -> int:
        raise NotImplementedError()
    
    @property
    def text_alignment(self) -> aspose.cells.drawing.texts.ShapeTextAlignment:
        '''Represents the alignment setting of the text body.'''
        raise NotImplementedError()
    
    @property
    def text_paragraphs(self) -> aspose.cells.drawing.texts.TextParagraphCollection:
        '''Gets all paragraphs.'''
        raise NotImplementedError()
    
    @property
    def text(self) -> str:
        '''Gets and sets the text of the shape.'''
        raise NotImplementedError()
    
    @text.setter
    def text(self, value : str) -> None:
        '''Gets and sets the text of the shape.'''
        raise NotImplementedError()
    
    @property
    def html_string(self) -> str:
        '''Gets and sets the html string which contains data and some formats in this shape.'''
        raise NotImplementedError()
    
    @html_string.setter
    def html_string(self, value : str) -> None:
        '''Gets and sets the html string which contains data and some formats in this shape.'''
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class NoneBulletValue:
    '''Represents no bullet.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.BulletType:
        '''Gets the type of the bullet\'s value.'''
        raise NotImplementedError()
    

class PictureBulletValue:
    '''Represents the value of the image bullet.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.BulletType:
        '''Gets the type of the bullet\'s value.'''
        raise NotImplementedError()
    
    @property
    def image_data(self) -> List[int]:
        '''Gets and sets image data of the bullet.'''
        raise NotImplementedError()
    
    @image_data.setter
    def image_data(self, value : List[int]) -> None:
        '''Gets and sets image data of the bullet.'''
        raise NotImplementedError()
    

class ShapeTextAlignment:
    '''Represents the setting of shape\'s text alignment;'''
    
    @property
    def is_text_wrapped(self) -> bool:
        '''Gets the text wrapped type of the shape which contains text.'''
        raise NotImplementedError()
    
    @is_text_wrapped.setter
    def is_text_wrapped(self, value : bool) -> None:
        '''Sets the text wrapped type of the shape which contains text.'''
        raise NotImplementedError()
    
    @property
    def rotate_text_with_shape(self) -> bool:
        '''Indicates whether rotating text with shape.'''
        raise NotImplementedError()
    
    @rotate_text_with_shape.setter
    def rotate_text_with_shape(self, value : bool) -> None:
        '''Indicates whether rotating text with shape.'''
        raise NotImplementedError()
    
    @property
    def text_vertical_overflow(self) -> aspose.cells.drawing.TextOverflowType:
        '''Gets and sets the text vertical overflow type of the text box.'''
        raise NotImplementedError()
    
    @text_vertical_overflow.setter
    def text_vertical_overflow(self, value : aspose.cells.drawing.TextOverflowType) -> None:
        '''Gets and sets the text vertical overflow type of the text box.'''
        raise NotImplementedError()
    
    @property
    def text_horizontal_overflow(self) -> aspose.cells.drawing.TextOverflowType:
        '''Gets and sets the text horizontal overflow type of the text box.'''
        raise NotImplementedError()
    
    @text_horizontal_overflow.setter
    def text_horizontal_overflow(self, value : aspose.cells.drawing.TextOverflowType) -> None:
        '''Gets and sets the text horizontal overflow type of the text box.'''
        raise NotImplementedError()
    
    @property
    def rotation_angle(self) -> float:
        '''Gets and sets the rotation of the shape.'''
        raise NotImplementedError()
    
    @rotation_angle.setter
    def rotation_angle(self, value : float) -> None:
        '''Gets and sets the rotation of the shape.'''
        raise NotImplementedError()
    
    @property
    def text_vertical_type(self) -> aspose.cells.drawing.texts.TextVerticalType:
        '''Gets and sets the text direction.'''
        raise NotImplementedError()
    
    @text_vertical_type.setter
    def text_vertical_type(self, value : aspose.cells.drawing.texts.TextVerticalType) -> None:
        '''Gets and sets the text direction.'''
        raise NotImplementedError()
    
    @property
    def is_locked_text(self) -> bool:
        '''Indicates whether the shape is locked when worksheet is protected.'''
        raise NotImplementedError()
    
    @is_locked_text.setter
    def is_locked_text(self, value : bool) -> None:
        '''Indicates whether the shape is locked when worksheet is protected.'''
        raise NotImplementedError()
    
    @property
    def auto_size(self) -> bool:
        '''Indicates if size of shape is adjusted automatically according to its content.'''
        raise NotImplementedError()
    
    @auto_size.setter
    def auto_size(self, value : bool) -> None:
        '''Indicates if size of shape is adjusted automatically according to its content.'''
        raise NotImplementedError()
    
    @property
    def text_shape_type(self) -> aspose.cells.drawing.AutoShapeType:
        '''Gets and set the transform type of text.'''
        raise NotImplementedError()
    
    @text_shape_type.setter
    def text_shape_type(self, value : aspose.cells.drawing.AutoShapeType) -> None:
        '''Gets and set the transform type of text.'''
        raise NotImplementedError()
    
    @property
    def top_margin_pt(self) -> float:
        '''Returns the top margin in unit of Points'''
        raise NotImplementedError()
    
    @top_margin_pt.setter
    def top_margin_pt(self, value : float) -> None:
        '''Returns the top margin in unit of Points'''
        raise NotImplementedError()
    
    @property
    def bottom_margin_pt(self) -> float:
        '''Returns the bottom margin in unit of Points'''
        raise NotImplementedError()
    
    @bottom_margin_pt.setter
    def bottom_margin_pt(self, value : float) -> None:
        '''Returns the bottom margin in unit of Points'''
        raise NotImplementedError()
    
    @property
    def left_margin_pt(self) -> float:
        '''Returns the left margin in unit of Points'''
        raise NotImplementedError()
    
    @left_margin_pt.setter
    def left_margin_pt(self, value : float) -> None:
        '''Returns the left margin in unit of Points'''
        raise NotImplementedError()
    
    @property
    def right_margin_pt(self) -> float:
        '''Returns the right margin in unit of Points'''
        raise NotImplementedError()
    
    @right_margin_pt.setter
    def right_margin_pt(self, value : float) -> None:
        '''Returns the right margin in unit of Points'''
        raise NotImplementedError()
    
    @property
    def is_auto_margin(self) -> bool:
        '''Indicates whether the margin of the text frame is automatic.'''
        raise NotImplementedError()
    
    @is_auto_margin.setter
    def is_auto_margin(self, value : bool) -> None:
        '''Indicates whether the margin of the text frame is automatic.'''
        raise NotImplementedError()
    
    @property
    def number_of_columns(self) -> int:
        '''Gets and sets the number of columns of text in the bounding rectangle.'''
        raise NotImplementedError()
    
    @number_of_columns.setter
    def number_of_columns(self, value : int) -> None:
        '''Gets and sets the number of columns of text in the bounding rectangle.'''
        raise NotImplementedError()
    

class TextBoxOptions:
    '''Represents the text options of the shape'''
    
    @property
    def shape_text_vertical_alignment(self) -> aspose.cells.drawing.texts.ShapeTextVerticalAlignmentType:
        '''It corresponds to "Format Shape - Text Options - Text Box - Vertical Alignment" in Excel.'''
        raise NotImplementedError()
    
    @shape_text_vertical_alignment.setter
    def shape_text_vertical_alignment(self, value : aspose.cells.drawing.texts.ShapeTextVerticalAlignmentType) -> None:
        '''It corresponds to "Format Shape - Text Options - Text Box - Vertical Alignment" in Excel.'''
        raise NotImplementedError()
    
    @property
    def resize_to_fit_text(self) -> bool:
        '''Indicates whether to resize the shape to fit the text'''
        raise NotImplementedError()
    
    @resize_to_fit_text.setter
    def resize_to_fit_text(self, value : bool) -> None:
        '''Indicates whether to resize the shape to fit the text'''
        raise NotImplementedError()
    
    @property
    def shape_text_direction(self) -> aspose.cells.drawing.texts.TextVerticalType:
        '''Gets the text display direction within a given text body.
        It corresponds to "Format Shape - Text Options - Text Box - Text direction" in Excel'''
        raise NotImplementedError()
    
    @shape_text_direction.setter
    def shape_text_direction(self, value : aspose.cells.drawing.texts.TextVerticalType) -> None:
        '''Sets the text display direction within a given text body.
        It corresponds to "Format Shape - Text Options - Text Box - Text direction" in Excel'''
        raise NotImplementedError()
    
    @property
    def left_margin_pt(self) -> float:
        '''Gets and sets the left margin in unit of Points.'''
        raise NotImplementedError()
    
    @left_margin_pt.setter
    def left_margin_pt(self, value : float) -> None:
        '''Gets and sets the left margin in unit of Points.'''
        raise NotImplementedError()
    
    @property
    def right_margin_pt(self) -> float:
        '''Gets and sets the right margin in unit of Points.'''
        raise NotImplementedError()
    
    @right_margin_pt.setter
    def right_margin_pt(self, value : float) -> None:
        '''Gets and sets the right margin in unit of Points.'''
        raise NotImplementedError()
    
    @property
    def top_margin_pt(self) -> float:
        '''Gets and sets the top margin in unit of Points.'''
        raise NotImplementedError()
    
    @top_margin_pt.setter
    def top_margin_pt(self, value : float) -> None:
        '''Gets and sets the top margin in unit of Points.'''
        raise NotImplementedError()
    
    @property
    def bottom_margin_pt(self) -> float:
        '''Returns the bottom margin in unit of Points'''
        raise NotImplementedError()
    
    @bottom_margin_pt.setter
    def bottom_margin_pt(self, value : float) -> None:
        '''Returns the bottom margin in unit of Points'''
        raise NotImplementedError()
    
    @property
    def allow_text_to_overflow(self) -> bool:
        '''Whether allow text to overflow shape.'''
        raise NotImplementedError()
    
    @allow_text_to_overflow.setter
    def allow_text_to_overflow(self, value : bool) -> None:
        '''Whether allow text to overflow shape.'''
        raise NotImplementedError()
    
    @property
    def wrap_text_in_shape(self) -> bool:
        '''Specifies text wrapping within a shape.
        False - No wrapping will occur on text body.
        True - Wrapping will occur on text body.'''
        raise NotImplementedError()
    
    @wrap_text_in_shape.setter
    def wrap_text_in_shape(self, value : bool) -> None:
        '''Specifies text wrapping within a shape.
        False - No wrapping will occur on text body.
        True - Wrapping will occur on text body.'''
        raise NotImplementedError()
    

class TextOptions(aspose.cells.Font):
    '''Represents the text options.'''
    
    def equals(self, font : aspose.cells.Font) -> bool:
        '''Checks if two fonts are equals.
        
        :param font: Compared font object.
        :returns: True if equal to the compared font object.'''
        raise NotImplementedError()
    
    @property
    def charset(self) -> int:
        '''Represent the character set.'''
        raise NotImplementedError()
    
    @charset.setter
    def charset(self, value : int) -> None:
        '''Represent the character set.'''
        raise NotImplementedError()
    
    @property
    def is_italic(self) -> bool:
        '''Gets a value indicating whether the font is italic.'''
        raise NotImplementedError()
    
    @is_italic.setter
    def is_italic(self, value : bool) -> None:
        '''Sets a value indicating whether the font is italic.'''
        raise NotImplementedError()
    
    @property
    def is_bold(self) -> bool:
        '''Gets a value indicating whether the font is bold.'''
        raise NotImplementedError()
    
    @is_bold.setter
    def is_bold(self, value : bool) -> None:
        '''Sets a value indicating whether the font is bold.'''
        raise NotImplementedError()
    
    @property
    def caps_type(self) -> aspose.cells.TextCapsType:
        '''Gets and sets the text caps type.'''
        raise NotImplementedError()
    
    @caps_type.setter
    def caps_type(self, value : aspose.cells.TextCapsType) -> None:
        '''Gets and sets the text caps type.'''
        raise NotImplementedError()
    
    @property
    def strike_type(self) -> aspose.cells.TextStrikeType:
        '''Gets the strike type of the text.'''
        raise NotImplementedError()
    
    @strike_type.setter
    def strike_type(self, value : aspose.cells.TextStrikeType) -> None:
        '''Gets the strike type of the text.'''
        raise NotImplementedError()
    
    @property
    def is_strikeout(self) -> bool:
        '''Gets a value indicating whether the font is single strikeout.'''
        raise NotImplementedError()
    
    @is_strikeout.setter
    def is_strikeout(self, value : bool) -> None:
        '''Sets a value indicating whether the font is single strikeout.'''
        raise NotImplementedError()
    
    @property
    def script_offset(self) -> float:
        '''Gets and sets the script offset,in unit of percentage'''
        raise NotImplementedError()
    
    @script_offset.setter
    def script_offset(self, value : float) -> None:
        '''Gets and sets the script offset,in unit of percentage'''
        raise NotImplementedError()
    
    @property
    def is_superscript(self) -> bool:
        '''Gets a value indicating whether the font is super script.'''
        raise NotImplementedError()
    
    @is_superscript.setter
    def is_superscript(self, value : bool) -> None:
        '''Sets a value indicating whether the font is super script.'''
        raise NotImplementedError()
    
    @property
    def is_subscript(self) -> bool:
        '''Gets a value indicating whether the font is subscript.'''
        raise NotImplementedError()
    
    @is_subscript.setter
    def is_subscript(self, value : bool) -> None:
        '''Sets a value indicating whether the font is subscript.'''
        raise NotImplementedError()
    
    @property
    def underline(self) -> aspose.cells.FontUnderlineType:
        '''Gets the font underline type.'''
        raise NotImplementedError()
    
    @underline.setter
    def underline(self, value : aspose.cells.FontUnderlineType) -> None:
        '''Sets the font underline type.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets and sets the name of the shape.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Gets and sets the name of the shape.'''
        raise NotImplementedError()
    
    @property
    def double_size(self) -> float:
        '''Gets and sets the double size of the font.'''
        raise NotImplementedError()
    
    @double_size.setter
    def double_size(self, value : float) -> None:
        '''Gets and sets the double size of the font.'''
        raise NotImplementedError()
    
    @property
    def size(self) -> int:
        '''Gets the size of the font.'''
        raise NotImplementedError()
    
    @size.setter
    def size(self, value : int) -> None:
        '''Sets the size of the font.'''
        raise NotImplementedError()
    
    @property
    def theme_color(self) -> aspose.cells.ThemeColor:
        '''Gets and sets the theme color.'''
        raise NotImplementedError()
    
    @theme_color.setter
    def theme_color(self, value : aspose.cells.ThemeColor) -> None:
        '''Gets and sets the theme color.'''
        raise NotImplementedError()
    
    @property
    def color(self) -> aspose.pydrawing.Color:
        '''Gets the :py:class:`aspose.pydrawing.Color` of the font.'''
        raise NotImplementedError()
    
    @color.setter
    def color(self, value : aspose.pydrawing.Color) -> None:
        '''Sets the :py:class:`aspose.pydrawing.Color` of the font.'''
        raise NotImplementedError()
    
    @property
    def argb_color(self) -> int:
        '''Gets and sets the color with a 32-bit ARGB value.'''
        raise NotImplementedError()
    
    @argb_color.setter
    def argb_color(self, value : int) -> None:
        '''Gets and sets the color with a 32-bit ARGB value.'''
        raise NotImplementedError()
    
    @property
    def is_normalize_heights(self) -> bool:
        '''Indicates whether the normalization of height that is to be applied to the text run.'''
        raise NotImplementedError()
    
    @is_normalize_heights.setter
    def is_normalize_heights(self, value : bool) -> None:
        '''Indicates whether the normalization of height that is to be applied to the text run.'''
        raise NotImplementedError()
    
    @property
    def scheme_type(self) -> aspose.cells.FontSchemeType:
        '''Gets and sets the scheme type of the font.'''
        raise NotImplementedError()
    
    @scheme_type.setter
    def scheme_type(self, value : aspose.cells.FontSchemeType) -> None:
        '''Gets and sets the scheme type of the font.'''
        raise NotImplementedError()
    
    @property
    def language_code(self) -> aspose.cells.CountryCode:
        '''Gets and sets the user interface language.'''
        raise NotImplementedError()
    
    @language_code.setter
    def language_code(self, value : aspose.cells.CountryCode) -> None:
        '''Gets and sets the user interface language.'''
        raise NotImplementedError()
    
    @property
    def latin_name(self) -> str:
        '''Gets and sets the latin name.'''
        raise NotImplementedError()
    
    @latin_name.setter
    def latin_name(self, value : str) -> None:
        '''Gets and sets the latin name.'''
        raise NotImplementedError()
    
    @property
    def far_east_name(self) -> str:
        '''Gets and sets the FarEast name.'''
        raise NotImplementedError()
    
    @far_east_name.setter
    def far_east_name(self, value : str) -> None:
        '''Gets and sets the FarEast name.'''
        raise NotImplementedError()
    
    @property
    def fill(self) -> aspose.cells.drawing.FillFormat:
        '''Represents the fill format of the text.'''
        raise NotImplementedError()
    
    @property
    def outline(self) -> aspose.cells.drawing.LineFormat:
        '''Represents the outline format of the text.'''
        raise NotImplementedError()
    
    @property
    def shadow(self) -> aspose.cells.drawing.ShadowEffect:
        '''Represents a :py:class:`aspose.cells.drawing.ShadowEffect` object that specifies shadow effect for the chart element or shape.'''
        raise NotImplementedError()
    
    @property
    def underline_color(self) -> aspose.cells.CellsColor:
        '''Gets the color of underline.'''
        raise NotImplementedError()
    
    @underline_color.setter
    def underline_color(self, value : aspose.cells.CellsColor) -> None:
        '''Sets the color of underline.'''
        raise NotImplementedError()
    
    @property
    def kerning(self) -> float:
        '''Specifies the minimum font size at which character kerning will occur for this text run.'''
        raise NotImplementedError()
    
    @kerning.setter
    def kerning(self, value : float) -> None:
        '''Specifies the minimum font size at which character kerning will occur for this text run.'''
        raise NotImplementedError()
    
    @property
    def spacing(self) -> float:
        '''Specifies the spacing between characters within a text run.'''
        raise NotImplementedError()
    
    @spacing.setter
    def spacing(self, value : float) -> None:
        '''Specifies the spacing between characters within a text run.'''
        raise NotImplementedError()
    

class TextParagraph(aspose.cells.FontSetting):
    '''Represents the text paragraph setting.'''
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Gets the type of text node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def bullet(self) -> aspose.cells.drawing.texts.Bullet:
        '''Gets the bullet.'''
        raise NotImplementedError()
    
    @property
    def line_space_size_type(self) -> aspose.cells.drawing.texts.LineSpaceSizeType:
        '''Gets and sets the amount of vertical white space that will be used within a paragraph.'''
        raise NotImplementedError()
    
    @line_space_size_type.setter
    def line_space_size_type(self, value : aspose.cells.drawing.texts.LineSpaceSizeType) -> None:
        '''Gets and sets the amount of vertical white space that will be used within a paragraph.'''
        raise NotImplementedError()
    
    @property
    def line_space(self) -> float:
        '''Gets and sets the amount of vertical white space that will be used within a paragraph.'''
        raise NotImplementedError()
    
    @line_space.setter
    def line_space(self, value : float) -> None:
        '''Gets and sets the amount of vertical white space that will be used within a paragraph.'''
        raise NotImplementedError()
    
    @property
    def space_after_size_type(self) -> aspose.cells.drawing.texts.LineSpaceSizeType:
        '''Gets and sets the amount of vertical white space that will be present after a paragraph.'''
        raise NotImplementedError()
    
    @space_after_size_type.setter
    def space_after_size_type(self, value : aspose.cells.drawing.texts.LineSpaceSizeType) -> None:
        '''Gets and sets the amount of vertical white space that will be present after a paragraph.'''
        raise NotImplementedError()
    
    @property
    def space_after(self) -> float:
        '''Gets and sets the amount of vertical white space that will be present after a paragraph.'''
        raise NotImplementedError()
    
    @space_after.setter
    def space_after(self, value : float) -> None:
        '''Gets and sets the amount of vertical white space that will be present after a paragraph.'''
        raise NotImplementedError()
    
    @property
    def space_before_size_type(self) -> aspose.cells.drawing.texts.LineSpaceSizeType:
        '''Gets and sets the amount of vertical white space that will be present before a paragraph.'''
        raise NotImplementedError()
    
    @space_before_size_type.setter
    def space_before_size_type(self, value : aspose.cells.drawing.texts.LineSpaceSizeType) -> None:
        '''Gets and sets the amount of vertical white space that will be present before a paragraph.'''
        raise NotImplementedError()
    
    @property
    def space_before(self) -> float:
        '''Gets and sets the amount of vertical white space that will be present before a paragraph.'''
        raise NotImplementedError()
    
    @space_before.setter
    def space_before(self, value : float) -> None:
        '''Gets and sets the amount of vertical white space that will be present before a paragraph.'''
        raise NotImplementedError()
    
    @property
    def stops(self) -> aspose.cells.drawing.texts.TextTabStopCollection:
        '''Gets tab stop list.'''
        raise NotImplementedError()
    
    @property
    def is_latin_line_break(self) -> bool:
        '''Specifies whether a Latin word can be broken in half and wrapped onto the next line without a hyphen being added.'''
        raise NotImplementedError()
    
    @is_latin_line_break.setter
    def is_latin_line_break(self, value : bool) -> None:
        '''Specifies whether a Latin word can be broken in half and wrapped onto the next line without a hyphen being added.'''
        raise NotImplementedError()
    
    @property
    def is_east_asian_line_break(self) -> bool:
        '''Specifies whether an East Asian word can be broken in half and wrapped onto the next line without a hyphen being added.'''
        raise NotImplementedError()
    
    @is_east_asian_line_break.setter
    def is_east_asian_line_break(self, value : bool) -> None:
        '''Specifies whether an East Asian word can be broken in half and wrapped onto the next line without a hyphen being added.'''
        raise NotImplementedError()
    
    @property
    def is_hanging_punctuation(self) -> bool:
        '''Specifies whether punctuation is to be forcefully laid out on a line of text or put on a different line of text.'''
        raise NotImplementedError()
    
    @is_hanging_punctuation.setter
    def is_hanging_punctuation(self, value : bool) -> None:
        '''Specifies whether punctuation is to be forcefully laid out on a line of text or put on a different line of text.'''
        raise NotImplementedError()
    
    @property
    def right_margin(self) -> float:
        '''Specifies the right margin of the paragraph.'''
        raise NotImplementedError()
    
    @right_margin.setter
    def right_margin(self, value : float) -> None:
        '''Specifies the right margin of the paragraph.'''
        raise NotImplementedError()
    
    @property
    def left_margin(self) -> float:
        '''Specifies the left margin of the paragraph.'''
        raise NotImplementedError()
    
    @left_margin.setter
    def left_margin(self, value : float) -> None:
        '''Specifies the left margin of the paragraph.'''
        raise NotImplementedError()
    
    @property
    def first_line_indent(self) -> float:
        '''Specifies the indent size that will be applied to the first line of text in the paragraph.'''
        raise NotImplementedError()
    
    @first_line_indent.setter
    def first_line_indent(self, value : float) -> None:
        '''Specifies the indent size that will be applied to the first line of text in the paragraph.'''
        raise NotImplementedError()
    
    @property
    def font_align_type(self) -> aspose.cells.drawing.texts.TextFontAlignType:
        '''Determines where vertically on a line of text the actual words are positioned. This deals
        with vertical placement of the characters with respect to the baselines.'''
        raise NotImplementedError()
    
    @font_align_type.setter
    def font_align_type(self, value : aspose.cells.drawing.texts.TextFontAlignType) -> None:
        '''Determines where vertically on a line of text the actual words are positioned. This deals
        with vertical placement of the characters with respect to the baselines.'''
        raise NotImplementedError()
    
    @property
    def alignment_type(self) -> aspose.cells.TextAlignmentType:
        '''Gets and sets the text horizontal alignment type of the paragraph.'''
        raise NotImplementedError()
    
    @alignment_type.setter
    def alignment_type(self, value : aspose.cells.TextAlignmentType) -> None:
        '''Gets and sets the text horizontal alignment type of the paragraph.'''
        raise NotImplementedError()
    
    @property
    def default_tab_size(self) -> float:
        '''Gets and sets the default size for a tab character within this paragraph.'''
        raise NotImplementedError()
    
    @default_tab_size.setter
    def default_tab_size(self, value : float) -> None:
        '''Gets and sets the default size for a tab character within this paragraph.'''
        raise NotImplementedError()
    
    @property
    def children(self) -> List[aspose.cells.FontSetting]:
        '''Gets all text runs in this paragraph.
        If this paragraph is empty, return paragraph itself.'''
        raise NotImplementedError()
    

class TextParagraphCollection:
    '''Represents all text paragraph.'''
    
    @property
    def count(self) -> int:
        '''Gets the count of text paragraphs.'''
        raise NotImplementedError()
    
    def __getitem__(self, key : int) -> aspose.cells.drawing.texts.TextParagraph:
        '''Gets the :py:class:`aspose.cells.drawing.texts.TextParagraph` object at specific index.'''
        raise NotImplementedError()
    

class TextTabStop:
    '''Represents tab stop.'''
    
    @property
    def tab_alignment(self) -> aspose.cells.drawing.texts.TextTabAlignmentType:
        '''Specifies the alignment that is to be applied to text using this tab stop.'''
        raise NotImplementedError()
    
    @tab_alignment.setter
    def tab_alignment(self, value : aspose.cells.drawing.texts.TextTabAlignmentType) -> None:
        '''Specifies the alignment that is to be applied to text using this tab stop.'''
        raise NotImplementedError()
    
    @property
    def tab_position(self) -> float:
        '''Specifies the position of the tab stop relative to the left margin.'''
        raise NotImplementedError()
    
    @tab_position.setter
    def tab_position(self, value : float) -> None:
        '''Specifies the position of the tab stop relative to the left margin.'''
        raise NotImplementedError()
    

class TextTabStopCollection:
    '''Represents the list of all tab stops.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.drawing.texts.TextTabStop]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.drawing.texts.TextTabStop], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.drawing.texts.TextTabStop, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.drawing.texts.TextTabStop, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.drawing.texts.TextTabStop) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.drawing.texts.TextTabStop, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.drawing.texts.TextTabStop, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add(self, tab_alignment : aspose.cells.drawing.texts.TextTabAlignmentType, tab_position : float) -> int:
        '''Adds a tab stop.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.drawing.texts.TextTabStop) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class BulletType:
    '''Represents the type of the bullet.'''
    
    NONE : BulletType
    '''No bullet.'''
    CHARACTER : BulletType
    '''Character bullet.'''
    PICTURE : BulletType
    '''Image bullet.'''
    AUTO_NUMBERED : BulletType
    '''Automatic numbered bullet.'''

class LineSpaceSizeType:
    '''Represents the unit type of line space size.'''
    
    PERCENTAGE : LineSpaceSizeType
    '''Represents in unit of a percentage of the text size.'''
    POINTS : LineSpaceSizeType
    '''Represents in unit of points.'''

class ShapeTextVerticalAlignmentType:
    '''It corresponds to "Format Shape - Text Options - Text Box - Vertical Alignment" in Excel.'''
    
    TOP : ShapeTextVerticalAlignmentType
    MIDDLE : ShapeTextVerticalAlignmentType
    BOTTOM : ShapeTextVerticalAlignmentType
    TOP_CENTERED : ShapeTextVerticalAlignmentType
    MIDDLE_CENTERED : ShapeTextVerticalAlignmentType
    BOTTOM_CENTERED : ShapeTextVerticalAlignmentType
    LEFT : ShapeTextVerticalAlignmentType
    CENTER : ShapeTextVerticalAlignmentType
    RIGHT : ShapeTextVerticalAlignmentType
    LEFT_MIDDLE : ShapeTextVerticalAlignmentType
    CENTER_MIDDLE : ShapeTextVerticalAlignmentType
    RIGHT_MIDDLE : ShapeTextVerticalAlignmentType

class TextAutonumberScheme:
    '''Represents all automatic number scheme.'''
    
    NONE : TextAutonumberScheme
    ALPHA_LC_PAREN_BOTH : TextAutonumberScheme
    '''(a), (b), (c), …'''
    ALPHA_LC_PAREN_R : TextAutonumberScheme
    '''a), b), c), …'''
    ALPHA_LC_PERIOD : TextAutonumberScheme
    '''a., b., c., …'''
    ALPHA_UC_PAREN_BOTH : TextAutonumberScheme
    '''(A), (B), (C), …'''
    ALPHA_UC_PAREN_R : TextAutonumberScheme
    '''A), B), C), …'''
    ALPHA_UC_PERIOD : TextAutonumberScheme
    '''A., B., C., …'''
    ARABIC_1_MINUS : TextAutonumberScheme
    '''Bidi Arabic 1 (AraAlpha) with ANSI minus symbol'''
    ARABIC_2_MINUS : TextAutonumberScheme
    '''Bidi Arabic 2 (AraAbjad) with ANSI minus symbol'''
    ARABIC_DB_PERIOD : TextAutonumberScheme
    '''Dbl-byte Arabic numbers w/ double-byte period'''
    ARABIC_DB_PLAIN : TextAutonumberScheme
    '''Dbl-byte Arabic numbers'''
    ARABIC_PAREN_BOTH : TextAutonumberScheme
    '''(1), (2), (3), …'''
    ARABIC_PAREN_R : TextAutonumberScheme
    '''1), 2), 3), …'''
    ARABIC_PERIOD : TextAutonumberScheme
    '''1., 2., 3., …'''
    ARABIC_PLAIN : TextAutonumberScheme
    '''1, 2, 3, …'''
    CIRCLE_NUM_DB_PLAIN : TextAutonumberScheme
    '''Dbl-byte circle numbers (1-10 circle[0x2460-], 11-arabic numbers)'''
    CIRCLE_NUM_WD_BLACK_PLAIN : TextAutonumberScheme
    '''Wingdings black circle numbers'''
    CIRCLE_NUM_WD_WHITE_PLAIN : TextAutonumberScheme
    '''Wingdings white circle numbers (0-10 circle[0x0080-],11- arabic numbers)'''
    EA_1_CHS_PERIOD : TextAutonumberScheme
    '''EA: Simplified Chinese w/ single-byte period'''
    EA_1_CHS_PLAIN : TextAutonumberScheme
    '''EA: Simplified Chinese (TypeA 1-99, TypeC 100-)'''
    EA_1_CHT_PERIOD : TextAutonumberScheme
    '''EA: Traditional Chinese w/ single-byte period'''
    EA_1_CHT_PLAIN : TextAutonumberScheme
    '''EA: Traditional Chinese (TypeA 1-19, TypeC 20-)'''
    EA_1_JPN_CHS_DB_PERIOD : TextAutonumberScheme
    '''EA: Japanese w/ double-byte period'''
    EA_1_JPN_KOR_PERIOD : TextAutonumberScheme
    '''EA: Japanese/Korean w/ single-byte period'''
    EA_1_JPN_KOR_PLAIN : TextAutonumberScheme
    '''EA: Japanese/Korean (TypeC 1-)'''
    HEBREW_2_MINUS : TextAutonumberScheme
    '''Bidi Hebrew 2 with ANSI minus symbol'''
    HINDI_ALPHA_1_PERIOD : TextAutonumberScheme
    '''Hindi alphabet period - consonants'''
    HINDI_ALPHA_PERIOD : TextAutonumberScheme
    '''Hindi alphabet period - vowels'''
    HINDI_NUM_PAREN_R : TextAutonumberScheme
    '''Hindi numerical parentheses - right'''
    HINDI_NUM_PERIOD : TextAutonumberScheme
    '''Hindi numerical period'''
    ROMAN_LC_PAREN_BOTH : TextAutonumberScheme
    '''(i), (ii), (iii), …'''
    ROMAN_LC_PAREN_R : TextAutonumberScheme
    '''i), ii), iii), …'''
    ROMAN_LC_PERIOD : TextAutonumberScheme
    '''i., ii., iii., …'''
    ROMAN_UC_PAREN_BOTH : TextAutonumberScheme
    '''(I), (II), (III), …'''
    ROMAN_UC_PAREN_R : TextAutonumberScheme
    '''I), II), III), …'''
    ROMAN_UC_PERIOD : TextAutonumberScheme
    '''I., II., III., …'''
    THAI_ALPHA_PAREN_BOTH : TextAutonumberScheme
    '''Thai alphabet parentheses - both'''
    THAI_ALPHA_PAREN_R : TextAutonumberScheme
    '''Thai alphabet parentheses - right'''
    THAI_ALPHA_PERIOD : TextAutonumberScheme
    '''Thai alphabet period'''
    THAI_NUM_PAREN_BOTH : TextAutonumberScheme
    '''Thai numerical parentheses - both'''
    THAI_NUM_PAREN_R : TextAutonumberScheme
    '''Thai numerical parentheses - right'''
    THAI_NUM_PERIOD : TextAutonumberScheme
    '''Thai numerical period'''

class TextFontAlignType:
    '''Represents the different types of font alignment.'''
    
    AUTOMATIC : TextFontAlignType
    '''When the text flow is horizontal or simple vertical same as fontBaseline
    but for other vertical modes same as fontCenter.'''
    BOTTOM : TextFontAlignType
    '''The letters are anchored to the very bottom of a single line.'''
    BASELINE : TextFontAlignType
    '''The letters are anchored to the bottom baseline of a single line.'''
    CENTER : TextFontAlignType
    '''The letters are anchored between the two baselines of a single line.'''
    TOP : TextFontAlignType
    '''The letters are anchored to the top baseline of a single line.'''

class TextNodeType:
    '''Represents the node type.'''
    
    TEXT_RUN : TextNodeType
    '''Represents the text node.'''
    TEXT_PARAGRAPH : TextNodeType
    '''Represents the text paragraph.'''
    EQUATION : TextNodeType
    '''Represents the equation text.'''

class TextTabAlignmentType:
    '''Represents the text tab alignment types.'''
    
    CENTER : TextTabAlignmentType
    '''The text at this tab stop is center aligned.'''
    DECIMAL : TextTabAlignmentType
    '''At this tab stop, the decimals are lined up.'''
    LEFT : TextTabAlignmentType
    '''The text at this tab stop is left aligned.'''
    RIGHT : TextTabAlignmentType
    '''The text at this tab stop is right aligned.'''

class TextVerticalType:
    '''Represents the text direct type.'''
    
    VERTICAL : TextVerticalType
    '''East Asian Vertical display.'''
    HORIZONTAL : TextVerticalType
    '''Horizontal text.'''
    VERTICAL_LEFT_TO_RIGHT : TextVerticalType
    '''Displayed vertical and the text flows top down then LEFT to RIGHT'''
    VERTICAL90 : TextVerticalType
    '''Each line is 90 degrees rotated clockwise'''
    VERTICAL270 : TextVerticalType
    '''Each line is 270 degrees rotated clockwise'''
    STACKED : TextVerticalType
    '''Determines if all of the text is vertical'''
    STACKED_RIGHT_TO_LEFT : TextVerticalType
    '''Specifies that vertical WordArt should be shown from right to left rather than left to right.'''

