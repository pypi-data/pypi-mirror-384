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

class CheckBoxActiveXControl:
    '''Represents a CheckBox ActiveX control.'''
    
    @property
    def workbook(self) -> aspose.cells.Workbook:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.activexcontrols.ControlType:
        '''Gets the type of the ActiveX control.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_icon(self) -> List[int]:
        raise NotImplementedError()
    
    @mouse_icon.setter
    def mouse_icon(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_pointer(self) -> aspose.cells.drawing.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.cells.drawing.activexcontrols.ControlMousePointerType) -> None:
        raise NotImplementedError()
    
    @property
    def fore_ole_color(self) -> int:
        raise NotImplementedError()
    
    @fore_ole_color.setter
    def fore_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def back_ole_color(self) -> int:
        raise NotImplementedError()
    
    @back_ole_color.setter
    def back_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def shadow(self) -> bool:
        raise NotImplementedError()
    
    @shadow.setter
    def shadow(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def linked_cell(self) -> str:
        raise NotImplementedError()
    
    @linked_cell.setter
    def linked_cell(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def list_fill_range(self) -> str:
        raise NotImplementedError()
    
    @list_fill_range.setter
    def list_fill_range(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def data(self) -> List[int]:
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_locked(self) -> bool:
        raise NotImplementedError()
    
    @is_locked.setter
    def is_locked(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_transparent(self) -> bool:
        raise NotImplementedError()
    
    @is_transparent.setter
    def is_transparent(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_auto_size(self) -> bool:
        raise NotImplementedError()
    
    @is_auto_size.setter
    def is_auto_size(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def ime_mode(self) -> aspose.cells.drawing.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.cells.drawing.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        raise NotImplementedError()
    
    @property
    def text_align(self) -> aspose.cells.TextAlignmentType:
        raise NotImplementedError()
    
    @text_align.setter
    def text_align(self, value : aspose.cells.TextAlignmentType) -> None:
        raise NotImplementedError()
    
    @property
    def group_name(self) -> str:
        '''Gets and sets the group\'s name.'''
        raise NotImplementedError()
    
    @group_name.setter
    def group_name(self, value : str) -> None:
        '''Gets and sets the group\'s name.'''
        raise NotImplementedError()
    
    @property
    def alignment(self) -> aspose.cells.drawing.activexcontrols.ControlCaptionAlignmentType:
        '''Gets and set the position of the Caption relative to the control.'''
        raise NotImplementedError()
    
    @alignment.setter
    def alignment(self, value : aspose.cells.drawing.activexcontrols.ControlCaptionAlignmentType) -> None:
        '''Gets and set the position of the Caption relative to the control.'''
        raise NotImplementedError()
    
    @property
    def is_word_wrapped(self) -> bool:
        '''Indicates whether the contents of the control automatically wrap at the end of a line.'''
        raise NotImplementedError()
    
    @is_word_wrapped.setter
    def is_word_wrapped(self, value : bool) -> None:
        '''Indicates whether the contents of the control automatically wrap at the end of a line.'''
        raise NotImplementedError()
    
    @property
    def caption(self) -> str:
        '''Gets and set the descriptive text that appears on a control.'''
        raise NotImplementedError()
    
    @caption.setter
    def caption(self, value : str) -> None:
        '''Gets and set the descriptive text that appears on a control.'''
        raise NotImplementedError()
    
    @property
    def picture_position(self) -> aspose.cells.drawing.activexcontrols.ControlPicturePositionType:
        '''Gets and set the location of the control\'s picture relative to its caption.'''
        raise NotImplementedError()
    
    @picture_position.setter
    def picture_position(self, value : aspose.cells.drawing.activexcontrols.ControlPicturePositionType) -> None:
        '''Gets and set the location of the control\'s picture relative to its caption.'''
        raise NotImplementedError()
    
    @property
    def special_effect(self) -> aspose.cells.drawing.activexcontrols.ControlSpecialEffectType:
        '''Gets and sets the special effect of the control.'''
        raise NotImplementedError()
    
    @special_effect.setter
    def special_effect(self, value : aspose.cells.drawing.activexcontrols.ControlSpecialEffectType) -> None:
        '''Gets and sets the special effect of the control.'''
        raise NotImplementedError()
    
    @property
    def picture(self) -> List[int]:
        '''Gets and sets the data of the picture.'''
        raise NotImplementedError()
    
    @picture.setter
    def picture(self, value : List[int]) -> None:
        '''Gets and sets the data of the picture.'''
        raise NotImplementedError()
    
    @property
    def accelerator(self) -> System.Char:
        '''Gets and sets the accelerator key for the control.'''
        raise NotImplementedError()
    
    @accelerator.setter
    def accelerator(self, value : System.Char) -> None:
        '''Gets and sets the accelerator key for the control.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> aspose.cells.drawing.CheckValueType:
        '''Indicates if the control is checked or not.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : aspose.cells.drawing.CheckValueType) -> None:
        '''Indicates if the control is checked or not.'''
        raise NotImplementedError()
    
    @property
    def is_triple_state(self) -> bool:
        '''Indicates how the specified control will display Null values.'''
        raise NotImplementedError()
    
    @is_triple_state.setter
    def is_triple_state(self, value : bool) -> None:
        '''Indicates how the specified control will display Null values.'''
        raise NotImplementedError()
    

class ComboBoxActiveXControl:
    '''Represents a ComboBox ActiveX control.'''
    
    @property
    def workbook(self) -> aspose.cells.Workbook:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.activexcontrols.ControlType:
        '''Gets the type of the ActiveX control.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_icon(self) -> List[int]:
        raise NotImplementedError()
    
    @mouse_icon.setter
    def mouse_icon(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_pointer(self) -> aspose.cells.drawing.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.cells.drawing.activexcontrols.ControlMousePointerType) -> None:
        raise NotImplementedError()
    
    @property
    def fore_ole_color(self) -> int:
        raise NotImplementedError()
    
    @fore_ole_color.setter
    def fore_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def back_ole_color(self) -> int:
        raise NotImplementedError()
    
    @back_ole_color.setter
    def back_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def shadow(self) -> bool:
        raise NotImplementedError()
    
    @shadow.setter
    def shadow(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def linked_cell(self) -> str:
        raise NotImplementedError()
    
    @linked_cell.setter
    def linked_cell(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def list_fill_range(self) -> str:
        raise NotImplementedError()
    
    @list_fill_range.setter
    def list_fill_range(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def data(self) -> List[int]:
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_locked(self) -> bool:
        raise NotImplementedError()
    
    @is_locked.setter
    def is_locked(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_transparent(self) -> bool:
        raise NotImplementedError()
    
    @is_transparent.setter
    def is_transparent(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_auto_size(self) -> bool:
        raise NotImplementedError()
    
    @is_auto_size.setter
    def is_auto_size(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def ime_mode(self) -> aspose.cells.drawing.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.cells.drawing.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        raise NotImplementedError()
    
    @property
    def text_align(self) -> aspose.cells.TextAlignmentType:
        raise NotImplementedError()
    
    @text_align.setter
    def text_align(self, value : aspose.cells.TextAlignmentType) -> None:
        raise NotImplementedError()
    
    @property
    def max_length(self) -> int:
        '''Gets and sets the maximum number of characters'''
        raise NotImplementedError()
    
    @max_length.setter
    def max_length(self, value : int) -> None:
        '''Gets and sets the maximum number of characters'''
        raise NotImplementedError()
    
    @property
    def list_width(self) -> float:
        '''Gets and set the width in unit of points.'''
        raise NotImplementedError()
    
    @list_width.setter
    def list_width(self, value : float) -> None:
        '''Gets and set the width in unit of points.'''
        raise NotImplementedError()
    
    @property
    def bound_column(self) -> int:
        '''Represents how the Value property is determined for a ComboBox or ListBox
        when the MultiSelect properties value (fmMultiSelectSingle).'''
        raise NotImplementedError()
    
    @bound_column.setter
    def bound_column(self, value : int) -> None:
        '''Represents how the Value property is determined for a ComboBox or ListBox
        when the MultiSelect properties value (fmMultiSelectSingle).'''
        raise NotImplementedError()
    
    @property
    def text_column(self) -> int:
        '''Represents the column in a ComboBox or ListBox to display to the user.'''
        raise NotImplementedError()
    
    @text_column.setter
    def text_column(self, value : int) -> None:
        '''Represents the column in a ComboBox or ListBox to display to the user.'''
        raise NotImplementedError()
    
    @property
    def column_count(self) -> int:
        '''Represents the number of columns to display in a ComboBox or ListBox.'''
        raise NotImplementedError()
    
    @column_count.setter
    def column_count(self, value : int) -> None:
        '''Represents the number of columns to display in a ComboBox or ListBox.'''
        raise NotImplementedError()
    
    @property
    def list_rows(self) -> int:
        '''Represents the maximum number of rows to display in the list.'''
        raise NotImplementedError()
    
    @list_rows.setter
    def list_rows(self, value : int) -> None:
        '''Represents the maximum number of rows to display in the list.'''
        raise NotImplementedError()
    
    @property
    def match_entry(self) -> aspose.cells.drawing.activexcontrols.ControlMatchEntryType:
        '''Indicates how a ListBox or ComboBox searches its list as the user types.'''
        raise NotImplementedError()
    
    @match_entry.setter
    def match_entry(self, value : aspose.cells.drawing.activexcontrols.ControlMatchEntryType) -> None:
        '''Indicates how a ListBox or ComboBox searches its list as the user types.'''
        raise NotImplementedError()
    
    @property
    def drop_button_style(self) -> aspose.cells.drawing.activexcontrols.DropButtonStyle:
        '''Specifies the symbol displayed on the drop button'''
        raise NotImplementedError()
    
    @drop_button_style.setter
    def drop_button_style(self, value : aspose.cells.drawing.activexcontrols.DropButtonStyle) -> None:
        '''Specifies the symbol displayed on the drop button'''
        raise NotImplementedError()
    
    @property
    def show_drop_button_type_when(self) -> aspose.cells.drawing.activexcontrols.ShowDropButtonType:
        '''Specifies the symbol displayed on the drop button'''
        raise NotImplementedError()
    
    @show_drop_button_type_when.setter
    def show_drop_button_type_when(self, value : aspose.cells.drawing.activexcontrols.ShowDropButtonType) -> None:
        '''Specifies the symbol displayed on the drop button'''
        raise NotImplementedError()
    
    @property
    def list_style(self) -> aspose.cells.drawing.activexcontrols.ControlListStyle:
        '''Gets and sets the visual appearance.'''
        raise NotImplementedError()
    
    @list_style.setter
    def list_style(self, value : aspose.cells.drawing.activexcontrols.ControlListStyle) -> None:
        '''Gets and sets the visual appearance.'''
        raise NotImplementedError()
    
    @property
    def border_style(self) -> aspose.cells.drawing.activexcontrols.ControlBorderType:
        '''Gets and set the type of border used by the control.'''
        raise NotImplementedError()
    
    @border_style.setter
    def border_style(self, value : aspose.cells.drawing.activexcontrols.ControlBorderType) -> None:
        '''Gets and set the type of border used by the control.'''
        raise NotImplementedError()
    
    @property
    def border_ole_color(self) -> int:
        '''Gets and sets the ole color of the background.'''
        raise NotImplementedError()
    
    @border_ole_color.setter
    def border_ole_color(self, value : int) -> None:
        '''Gets and sets the ole color of the background.'''
        raise NotImplementedError()
    
    @property
    def special_effect(self) -> aspose.cells.drawing.activexcontrols.ControlSpecialEffectType:
        '''Gets and sets the special effect of the control.'''
        raise NotImplementedError()
    
    @special_effect.setter
    def special_effect(self, value : aspose.cells.drawing.activexcontrols.ControlSpecialEffectType) -> None:
        '''Gets and sets the special effect of the control.'''
        raise NotImplementedError()
    
    @property
    def is_editable(self) -> bool:
        '''Indicates whether the user can type into the control.'''
        raise NotImplementedError()
    
    @is_editable.setter
    def is_editable(self, value : bool) -> None:
        '''Indicates whether the user can type into the control.'''
        raise NotImplementedError()
    
    @property
    def show_column_heads(self) -> bool:
        '''Indicates whether column headings are displayed.'''
        raise NotImplementedError()
    
    @show_column_heads.setter
    def show_column_heads(self, value : bool) -> None:
        '''Indicates whether column headings are displayed.'''
        raise NotImplementedError()
    
    @property
    def is_drag_behavior_enabled(self) -> bool:
        '''Indicates whether dragging and dropping is enabled for the control.'''
        raise NotImplementedError()
    
    @is_drag_behavior_enabled.setter
    def is_drag_behavior_enabled(self, value : bool) -> None:
        '''Indicates whether dragging and dropping is enabled for the control.'''
        raise NotImplementedError()
    
    @property
    def enter_field_behavior(self) -> bool:
        '''Specifies selection behavior when entering the control.
        True specifies that the selection remains unchanged from last time the control was active.
        False specifies that all the text in the control will be selected when entering the control.'''
        raise NotImplementedError()
    
    @enter_field_behavior.setter
    def enter_field_behavior(self, value : bool) -> None:
        '''Specifies selection behavior when entering the control.
        True specifies that the selection remains unchanged from last time the control was active.
        False specifies that all the text in the control will be selected when entering the control.'''
        raise NotImplementedError()
    
    @property
    def is_auto_word_selected(self) -> bool:
        '''Specifies the basic unit used to extend a selection.
        True specifies that the basic unit is a single character.
        false specifies that the basic unit is a whole word.'''
        raise NotImplementedError()
    
    @is_auto_word_selected.setter
    def is_auto_word_selected(self, value : bool) -> None:
        '''Specifies the basic unit used to extend a selection.
        True specifies that the basic unit is a single character.
        false specifies that the basic unit is a whole word.'''
        raise NotImplementedError()
    
    @property
    def selection_margin(self) -> bool:
        '''Indicates whether the user can select a line of text by clicking in the region to the left of the text.'''
        raise NotImplementedError()
    
    @selection_margin.setter
    def selection_margin(self, value : bool) -> None:
        '''Indicates whether the user can select a line of text by clicking in the region to the left of the text.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        '''Gets and sets the value of the control.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : str) -> None:
        '''Gets and sets the value of the control.'''
        raise NotImplementedError()
    
    @property
    def hide_selection(self) -> bool:
        '''Indicates whether selected text in the control appears highlighted when the control does not have focus.'''
        raise NotImplementedError()
    
    @hide_selection.setter
    def hide_selection(self, value : bool) -> None:
        '''Indicates whether selected text in the control appears highlighted when the control does not have focus.'''
        raise NotImplementedError()
    
    @property
    def column_widths(self) -> float:
        '''Gets and sets the width of the column.'''
        raise NotImplementedError()
    
    @column_widths.setter
    def column_widths(self, value : float) -> None:
        '''Gets and sets the width of the column.'''
        raise NotImplementedError()
    

class CommandButtonActiveXControl:
    '''Represents a command button.'''
    
    @property
    def workbook(self) -> aspose.cells.Workbook:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.activexcontrols.ControlType:
        '''Gets the type of the ActiveX control.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_icon(self) -> List[int]:
        raise NotImplementedError()
    
    @mouse_icon.setter
    def mouse_icon(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_pointer(self) -> aspose.cells.drawing.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.cells.drawing.activexcontrols.ControlMousePointerType) -> None:
        raise NotImplementedError()
    
    @property
    def fore_ole_color(self) -> int:
        raise NotImplementedError()
    
    @fore_ole_color.setter
    def fore_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def back_ole_color(self) -> int:
        raise NotImplementedError()
    
    @back_ole_color.setter
    def back_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def shadow(self) -> bool:
        raise NotImplementedError()
    
    @shadow.setter
    def shadow(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def linked_cell(self) -> str:
        raise NotImplementedError()
    
    @linked_cell.setter
    def linked_cell(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def list_fill_range(self) -> str:
        raise NotImplementedError()
    
    @list_fill_range.setter
    def list_fill_range(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def data(self) -> List[int]:
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_locked(self) -> bool:
        raise NotImplementedError()
    
    @is_locked.setter
    def is_locked(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_transparent(self) -> bool:
        raise NotImplementedError()
    
    @is_transparent.setter
    def is_transparent(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_auto_size(self) -> bool:
        raise NotImplementedError()
    
    @is_auto_size.setter
    def is_auto_size(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def ime_mode(self) -> aspose.cells.drawing.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.cells.drawing.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        raise NotImplementedError()
    
    @property
    def text_align(self) -> aspose.cells.TextAlignmentType:
        raise NotImplementedError()
    
    @text_align.setter
    def text_align(self, value : aspose.cells.TextAlignmentType) -> None:
        raise NotImplementedError()
    
    @property
    def caption(self) -> str:
        '''Gets and set the descriptive text that appears on a control.'''
        raise NotImplementedError()
    
    @caption.setter
    def caption(self, value : str) -> None:
        '''Gets and set the descriptive text that appears on a control.'''
        raise NotImplementedError()
    
    @property
    def picture_position(self) -> aspose.cells.drawing.activexcontrols.ControlPicturePositionType:
        '''Gets and set the location of the control\'s picture relative to its caption.'''
        raise NotImplementedError()
    
    @picture_position.setter
    def picture_position(self, value : aspose.cells.drawing.activexcontrols.ControlPicturePositionType) -> None:
        '''Gets and set the location of the control\'s picture relative to its caption.'''
        raise NotImplementedError()
    
    @property
    def picture(self) -> List[int]:
        '''Gets and sets the data of the picture.'''
        raise NotImplementedError()
    
    @picture.setter
    def picture(self, value : List[int]) -> None:
        '''Gets and sets the data of the picture.'''
        raise NotImplementedError()
    
    @property
    def accelerator(self) -> System.Char:
        '''Gets and sets the accelerator key for the control.'''
        raise NotImplementedError()
    
    @accelerator.setter
    def accelerator(self, value : System.Char) -> None:
        '''Gets and sets the accelerator key for the control.'''
        raise NotImplementedError()
    
    @property
    def take_focus_on_click(self) -> bool:
        '''Indicates whether the control takes the focus when clicked.'''
        raise NotImplementedError()
    
    @take_focus_on_click.setter
    def take_focus_on_click(self, value : bool) -> None:
        '''Indicates whether the control takes the focus when clicked.'''
        raise NotImplementedError()
    
    @property
    def is_word_wrapped(self) -> bool:
        '''Indicates whether the contents of the control automatically wrap at the end of a line.'''
        raise NotImplementedError()
    
    @is_word_wrapped.setter
    def is_word_wrapped(self, value : bool) -> None:
        '''Indicates whether the contents of the control automatically wrap at the end of a line.'''
        raise NotImplementedError()
    

class ImageActiveXControl:
    '''Represents the image control.'''
    
    @property
    def workbook(self) -> aspose.cells.Workbook:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.activexcontrols.ControlType:
        '''Gets the type of the ActiveX control.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_icon(self) -> List[int]:
        raise NotImplementedError()
    
    @mouse_icon.setter
    def mouse_icon(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_pointer(self) -> aspose.cells.drawing.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.cells.drawing.activexcontrols.ControlMousePointerType) -> None:
        raise NotImplementedError()
    
    @property
    def fore_ole_color(self) -> int:
        raise NotImplementedError()
    
    @fore_ole_color.setter
    def fore_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def back_ole_color(self) -> int:
        raise NotImplementedError()
    
    @back_ole_color.setter
    def back_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def shadow(self) -> bool:
        raise NotImplementedError()
    
    @shadow.setter
    def shadow(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def linked_cell(self) -> str:
        raise NotImplementedError()
    
    @linked_cell.setter
    def linked_cell(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def list_fill_range(self) -> str:
        raise NotImplementedError()
    
    @list_fill_range.setter
    def list_fill_range(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def data(self) -> List[int]:
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_locked(self) -> bool:
        raise NotImplementedError()
    
    @is_locked.setter
    def is_locked(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_transparent(self) -> bool:
        raise NotImplementedError()
    
    @is_transparent.setter
    def is_transparent(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_auto_size(self) -> bool:
        '''Indicates whether the control will automatically resize to display its entire contents.'''
        raise NotImplementedError()
    
    @is_auto_size.setter
    def is_auto_size(self, value : bool) -> None:
        '''Indicates whether the control will automatically resize to display its entire contents.'''
        raise NotImplementedError()
    
    @property
    def ime_mode(self) -> aspose.cells.drawing.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.cells.drawing.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        raise NotImplementedError()
    
    @property
    def text_align(self) -> aspose.cells.TextAlignmentType:
        raise NotImplementedError()
    
    @text_align.setter
    def text_align(self, value : aspose.cells.TextAlignmentType) -> None:
        raise NotImplementedError()
    
    @property
    def border_ole_color(self) -> int:
        '''Gets and sets the ole color of the background.'''
        raise NotImplementedError()
    
    @border_ole_color.setter
    def border_ole_color(self, value : int) -> None:
        '''Gets and sets the ole color of the background.'''
        raise NotImplementedError()
    
    @property
    def border_style(self) -> aspose.cells.drawing.activexcontrols.ControlBorderType:
        '''Gets and set the type of border used by the control.'''
        raise NotImplementedError()
    
    @border_style.setter
    def border_style(self, value : aspose.cells.drawing.activexcontrols.ControlBorderType) -> None:
        '''Gets and set the type of border used by the control.'''
        raise NotImplementedError()
    
    @property
    def picture_size_mode(self) -> aspose.cells.drawing.activexcontrols.ControlPictureSizeMode:
        '''Gets and sets how to display the picture.'''
        raise NotImplementedError()
    
    @picture_size_mode.setter
    def picture_size_mode(self, value : aspose.cells.drawing.activexcontrols.ControlPictureSizeMode) -> None:
        '''Gets and sets how to display the picture.'''
        raise NotImplementedError()
    
    @property
    def special_effect(self) -> aspose.cells.drawing.activexcontrols.ControlSpecialEffectType:
        '''Gets and sets the special effect of the control.'''
        raise NotImplementedError()
    
    @special_effect.setter
    def special_effect(self, value : aspose.cells.drawing.activexcontrols.ControlSpecialEffectType) -> None:
        '''Gets and sets the special effect of the control.'''
        raise NotImplementedError()
    
    @property
    def picture(self) -> List[int]:
        '''Gets and sets the data of the picture.'''
        raise NotImplementedError()
    
    @picture.setter
    def picture(self, value : List[int]) -> None:
        '''Gets and sets the data of the picture.'''
        raise NotImplementedError()
    
    @property
    def picture_alignment(self) -> aspose.cells.drawing.activexcontrols.ControlPictureAlignmentType:
        '''Gets and sets the alignment of the picture inside the Form or Image.'''
        raise NotImplementedError()
    
    @picture_alignment.setter
    def picture_alignment(self, value : aspose.cells.drawing.activexcontrols.ControlPictureAlignmentType) -> None:
        '''Gets and sets the alignment of the picture inside the Form or Image.'''
        raise NotImplementedError()
    
    @property
    def is_tiled(self) -> bool:
        '''Indicates whether the picture is tiled across the background.'''
        raise NotImplementedError()
    
    @is_tiled.setter
    def is_tiled(self, value : bool) -> None:
        '''Indicates whether the picture is tiled across the background.'''
        raise NotImplementedError()
    

class LabelActiveXControl:
    '''Represents the label ActiveX control.'''
    
    @property
    def workbook(self) -> aspose.cells.Workbook:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.activexcontrols.ControlType:
        '''Gets the type of the ActiveX control.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_icon(self) -> List[int]:
        raise NotImplementedError()
    
    @mouse_icon.setter
    def mouse_icon(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_pointer(self) -> aspose.cells.drawing.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.cells.drawing.activexcontrols.ControlMousePointerType) -> None:
        raise NotImplementedError()
    
    @property
    def fore_ole_color(self) -> int:
        raise NotImplementedError()
    
    @fore_ole_color.setter
    def fore_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def back_ole_color(self) -> int:
        raise NotImplementedError()
    
    @back_ole_color.setter
    def back_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def shadow(self) -> bool:
        raise NotImplementedError()
    
    @shadow.setter
    def shadow(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def linked_cell(self) -> str:
        raise NotImplementedError()
    
    @linked_cell.setter
    def linked_cell(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def list_fill_range(self) -> str:
        raise NotImplementedError()
    
    @list_fill_range.setter
    def list_fill_range(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def data(self) -> List[int]:
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_locked(self) -> bool:
        raise NotImplementedError()
    
    @is_locked.setter
    def is_locked(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_transparent(self) -> bool:
        raise NotImplementedError()
    
    @is_transparent.setter
    def is_transparent(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_auto_size(self) -> bool:
        raise NotImplementedError()
    
    @is_auto_size.setter
    def is_auto_size(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def ime_mode(self) -> aspose.cells.drawing.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.cells.drawing.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        raise NotImplementedError()
    
    @property
    def text_align(self) -> aspose.cells.TextAlignmentType:
        raise NotImplementedError()
    
    @text_align.setter
    def text_align(self, value : aspose.cells.TextAlignmentType) -> None:
        raise NotImplementedError()
    
    @property
    def caption(self) -> str:
        '''Gets and set the descriptive text that appears on a control.'''
        raise NotImplementedError()
    
    @caption.setter
    def caption(self, value : str) -> None:
        '''Gets and set the descriptive text that appears on a control.'''
        raise NotImplementedError()
    
    @property
    def picture_position(self) -> aspose.cells.drawing.activexcontrols.ControlPicturePositionType:
        '''Gets and set the location of the control\'s picture relative to its caption.'''
        raise NotImplementedError()
    
    @picture_position.setter
    def picture_position(self, value : aspose.cells.drawing.activexcontrols.ControlPicturePositionType) -> None:
        '''Gets and set the location of the control\'s picture relative to its caption.'''
        raise NotImplementedError()
    
    @property
    def border_ole_color(self) -> int:
        '''Gets and sets the ole color of the background.'''
        raise NotImplementedError()
    
    @border_ole_color.setter
    def border_ole_color(self, value : int) -> None:
        '''Gets and sets the ole color of the background.'''
        raise NotImplementedError()
    
    @property
    def border_style(self) -> aspose.cells.drawing.activexcontrols.ControlBorderType:
        '''Gets and set the type of border used by the control.'''
        raise NotImplementedError()
    
    @border_style.setter
    def border_style(self, value : aspose.cells.drawing.activexcontrols.ControlBorderType) -> None:
        '''Gets and set the type of border used by the control.'''
        raise NotImplementedError()
    
    @property
    def special_effect(self) -> aspose.cells.drawing.activexcontrols.ControlSpecialEffectType:
        '''Gets and sets the special effect of the control.'''
        raise NotImplementedError()
    
    @special_effect.setter
    def special_effect(self, value : aspose.cells.drawing.activexcontrols.ControlSpecialEffectType) -> None:
        '''Gets and sets the special effect of the control.'''
        raise NotImplementedError()
    
    @property
    def picture(self) -> List[int]:
        '''Gets and sets the data of the picture.'''
        raise NotImplementedError()
    
    @picture.setter
    def picture(self, value : List[int]) -> None:
        '''Gets and sets the data of the picture.'''
        raise NotImplementedError()
    
    @property
    def accelerator(self) -> System.Char:
        '''Gets and sets the accelerator key for the control.'''
        raise NotImplementedError()
    
    @accelerator.setter
    def accelerator(self, value : System.Char) -> None:
        '''Gets and sets the accelerator key for the control.'''
        raise NotImplementedError()
    
    @property
    def is_word_wrapped(self) -> bool:
        '''Indicates whether the contents of the control automatically wrap at the end of a line.'''
        raise NotImplementedError()
    
    @is_word_wrapped.setter
    def is_word_wrapped(self, value : bool) -> None:
        '''Indicates whether the contents of the control automatically wrap at the end of a line.'''
        raise NotImplementedError()
    

class ListBoxActiveXControl:
    '''Represents a ListBox ActiveX control.'''
    
    @property
    def workbook(self) -> aspose.cells.Workbook:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.activexcontrols.ControlType:
        '''Gets the type of the ActiveX control.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_icon(self) -> List[int]:
        raise NotImplementedError()
    
    @mouse_icon.setter
    def mouse_icon(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_pointer(self) -> aspose.cells.drawing.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.cells.drawing.activexcontrols.ControlMousePointerType) -> None:
        raise NotImplementedError()
    
    @property
    def fore_ole_color(self) -> int:
        raise NotImplementedError()
    
    @fore_ole_color.setter
    def fore_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def back_ole_color(self) -> int:
        raise NotImplementedError()
    
    @back_ole_color.setter
    def back_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def shadow(self) -> bool:
        raise NotImplementedError()
    
    @shadow.setter
    def shadow(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def linked_cell(self) -> str:
        raise NotImplementedError()
    
    @linked_cell.setter
    def linked_cell(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def list_fill_range(self) -> str:
        raise NotImplementedError()
    
    @list_fill_range.setter
    def list_fill_range(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def data(self) -> List[int]:
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_locked(self) -> bool:
        raise NotImplementedError()
    
    @is_locked.setter
    def is_locked(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_transparent(self) -> bool:
        raise NotImplementedError()
    
    @is_transparent.setter
    def is_transparent(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_auto_size(self) -> bool:
        raise NotImplementedError()
    
    @is_auto_size.setter
    def is_auto_size(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def ime_mode(self) -> aspose.cells.drawing.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.cells.drawing.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        raise NotImplementedError()
    
    @property
    def text_align(self) -> aspose.cells.TextAlignmentType:
        raise NotImplementedError()
    
    @text_align.setter
    def text_align(self, value : aspose.cells.TextAlignmentType) -> None:
        raise NotImplementedError()
    
    @property
    def scroll_bars(self) -> aspose.cells.drawing.activexcontrols.ControlScrollBarType:
        '''Indicates specifies whether the control has vertical scroll bars, horizontal scroll bars, both, or neither.'''
        raise NotImplementedError()
    
    @scroll_bars.setter
    def scroll_bars(self, value : aspose.cells.drawing.activexcontrols.ControlScrollBarType) -> None:
        '''Indicates specifies whether the control has vertical scroll bars, horizontal scroll bars, both, or neither.'''
        raise NotImplementedError()
    
    @property
    def list_width(self) -> float:
        '''Gets and set the width in unit of points.'''
        raise NotImplementedError()
    
    @list_width.setter
    def list_width(self, value : float) -> None:
        '''Gets and set the width in unit of points.'''
        raise NotImplementedError()
    
    @property
    def bound_column(self) -> int:
        '''Represents how the Value property is determined for a ComboBox or ListBox
        when the MultiSelect properties value (fmMultiSelectSingle).'''
        raise NotImplementedError()
    
    @bound_column.setter
    def bound_column(self, value : int) -> None:
        '''Represents how the Value property is determined for a ComboBox or ListBox
        when the MultiSelect properties value (fmMultiSelectSingle).'''
        raise NotImplementedError()
    
    @property
    def text_column(self) -> int:
        '''Represents the column in a ComboBox or ListBox to display to the user.'''
        raise NotImplementedError()
    
    @text_column.setter
    def text_column(self, value : int) -> None:
        '''Represents the column in a ComboBox or ListBox to display to the user.'''
        raise NotImplementedError()
    
    @property
    def column_count(self) -> int:
        '''Represents the number of columns to display in a ComboBox or ListBox.'''
        raise NotImplementedError()
    
    @column_count.setter
    def column_count(self, value : int) -> None:
        '''Represents the number of columns to display in a ComboBox or ListBox.'''
        raise NotImplementedError()
    
    @property
    def match_entry(self) -> aspose.cells.drawing.activexcontrols.ControlMatchEntryType:
        '''Indicates how a ListBox or ComboBox searches its list as the user types.'''
        raise NotImplementedError()
    
    @match_entry.setter
    def match_entry(self, value : aspose.cells.drawing.activexcontrols.ControlMatchEntryType) -> None:
        '''Indicates how a ListBox or ComboBox searches its list as the user types.'''
        raise NotImplementedError()
    
    @property
    def list_style(self) -> aspose.cells.drawing.activexcontrols.ControlListStyle:
        '''Gets and sets the visual appearance.'''
        raise NotImplementedError()
    
    @list_style.setter
    def list_style(self, value : aspose.cells.drawing.activexcontrols.ControlListStyle) -> None:
        '''Gets and sets the visual appearance.'''
        raise NotImplementedError()
    
    @property
    def selection_type(self) -> aspose.cells.drawing.SelectionType:
        '''Indicates whether the control permits multiple selections.'''
        raise NotImplementedError()
    
    @selection_type.setter
    def selection_type(self, value : aspose.cells.drawing.SelectionType) -> None:
        '''Indicates whether the control permits multiple selections.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        '''Gets and sets the value of the control.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : str) -> None:
        '''Gets and sets the value of the control.'''
        raise NotImplementedError()
    
    @property
    def border_style(self) -> aspose.cells.drawing.activexcontrols.ControlBorderType:
        '''Gets and set the type of border used by the control.'''
        raise NotImplementedError()
    
    @border_style.setter
    def border_style(self, value : aspose.cells.drawing.activexcontrols.ControlBorderType) -> None:
        '''Gets and set the type of border used by the control.'''
        raise NotImplementedError()
    
    @property
    def border_ole_color(self) -> int:
        '''Gets and sets the ole color of the background.'''
        raise NotImplementedError()
    
    @border_ole_color.setter
    def border_ole_color(self, value : int) -> None:
        '''Gets and sets the ole color of the background.'''
        raise NotImplementedError()
    
    @property
    def special_effect(self) -> aspose.cells.drawing.activexcontrols.ControlSpecialEffectType:
        '''Gets and sets the special effect of the control.'''
        raise NotImplementedError()
    
    @special_effect.setter
    def special_effect(self, value : aspose.cells.drawing.activexcontrols.ControlSpecialEffectType) -> None:
        '''Gets and sets the special effect of the control.'''
        raise NotImplementedError()
    
    @property
    def show_column_heads(self) -> bool:
        '''Indicates whether column headings are displayed.'''
        raise NotImplementedError()
    
    @show_column_heads.setter
    def show_column_heads(self, value : bool) -> None:
        '''Indicates whether column headings are displayed.'''
        raise NotImplementedError()
    
    @property
    def integral_height(self) -> bool:
        '''Indicates whether the control will only show complete lines of text without showing any partial lines.'''
        raise NotImplementedError()
    
    @integral_height.setter
    def integral_height(self, value : bool) -> None:
        '''Indicates whether the control will only show complete lines of text without showing any partial lines.'''
        raise NotImplementedError()
    
    @property
    def column_widths(self) -> float:
        '''Gets and sets the width of the column.'''
        raise NotImplementedError()
    
    @column_widths.setter
    def column_widths(self, value : float) -> None:
        '''Gets and sets the width of the column.'''
        raise NotImplementedError()
    

class RadioButtonActiveXControl(ToggleButtonActiveXControl):
    '''Represents a RadioButton ActiveX control.'''
    
    @property
    def workbook(self) -> aspose.cells.Workbook:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.activexcontrols.ControlType:
        '''Gets the type of the ActiveX control.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_icon(self) -> List[int]:
        raise NotImplementedError()
    
    @mouse_icon.setter
    def mouse_icon(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_pointer(self) -> aspose.cells.drawing.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.cells.drawing.activexcontrols.ControlMousePointerType) -> None:
        raise NotImplementedError()
    
    @property
    def fore_ole_color(self) -> int:
        raise NotImplementedError()
    
    @fore_ole_color.setter
    def fore_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def back_ole_color(self) -> int:
        raise NotImplementedError()
    
    @back_ole_color.setter
    def back_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def shadow(self) -> bool:
        raise NotImplementedError()
    
    @shadow.setter
    def shadow(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def linked_cell(self) -> str:
        raise NotImplementedError()
    
    @linked_cell.setter
    def linked_cell(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def list_fill_range(self) -> str:
        raise NotImplementedError()
    
    @list_fill_range.setter
    def list_fill_range(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def data(self) -> List[int]:
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_locked(self) -> bool:
        raise NotImplementedError()
    
    @is_locked.setter
    def is_locked(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_transparent(self) -> bool:
        raise NotImplementedError()
    
    @is_transparent.setter
    def is_transparent(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_auto_size(self) -> bool:
        raise NotImplementedError()
    
    @is_auto_size.setter
    def is_auto_size(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def ime_mode(self) -> aspose.cells.drawing.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.cells.drawing.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        raise NotImplementedError()
    
    @property
    def text_align(self) -> aspose.cells.TextAlignmentType:
        raise NotImplementedError()
    
    @text_align.setter
    def text_align(self, value : aspose.cells.TextAlignmentType) -> None:
        raise NotImplementedError()
    
    @property
    def caption(self) -> str:
        '''Gets and set the descriptive text that appears on a control.'''
        raise NotImplementedError()
    
    @caption.setter
    def caption(self, value : str) -> None:
        '''Gets and set the descriptive text that appears on a control.'''
        raise NotImplementedError()
    
    @property
    def picture_position(self) -> aspose.cells.drawing.activexcontrols.ControlPicturePositionType:
        '''Gets and set the location of the control\'s picture relative to its caption.'''
        raise NotImplementedError()
    
    @picture_position.setter
    def picture_position(self, value : aspose.cells.drawing.activexcontrols.ControlPicturePositionType) -> None:
        '''Gets and set the location of the control\'s picture relative to its caption.'''
        raise NotImplementedError()
    
    @property
    def special_effect(self) -> aspose.cells.drawing.activexcontrols.ControlSpecialEffectType:
        '''Gets and sets the special effect of the control.'''
        raise NotImplementedError()
    
    @special_effect.setter
    def special_effect(self, value : aspose.cells.drawing.activexcontrols.ControlSpecialEffectType) -> None:
        '''Gets and sets the special effect of the control.'''
        raise NotImplementedError()
    
    @property
    def picture(self) -> List[int]:
        '''Gets and sets the data of the picture.'''
        raise NotImplementedError()
    
    @picture.setter
    def picture(self, value : List[int]) -> None:
        '''Gets and sets the data of the picture.'''
        raise NotImplementedError()
    
    @property
    def accelerator(self) -> System.Char:
        '''Gets and sets the accelerator key for the control.'''
        raise NotImplementedError()
    
    @accelerator.setter
    def accelerator(self, value : System.Char) -> None:
        '''Gets and sets the accelerator key for the control.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> aspose.cells.drawing.CheckValueType:
        '''Indicates if the control is checked or not.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : aspose.cells.drawing.CheckValueType) -> None:
        '''Indicates if the control is checked or not.'''
        raise NotImplementedError()
    
    @property
    def is_triple_state(self) -> bool:
        '''Indicates how the specified control will display Null values.'''
        raise NotImplementedError()
    
    @is_triple_state.setter
    def is_triple_state(self, value : bool) -> None:
        '''Indicates how the specified control will display Null values.'''
        raise NotImplementedError()
    
    @property
    def group_name(self) -> str:
        '''Gets and sets the group\'s name.'''
        raise NotImplementedError()
    
    @group_name.setter
    def group_name(self, value : str) -> None:
        '''Gets and sets the group\'s name.'''
        raise NotImplementedError()
    
    @property
    def alignment(self) -> aspose.cells.drawing.activexcontrols.ControlCaptionAlignmentType:
        '''Gets and set the position of the Caption relative to the control.'''
        raise NotImplementedError()
    
    @alignment.setter
    def alignment(self, value : aspose.cells.drawing.activexcontrols.ControlCaptionAlignmentType) -> None:
        '''Gets and set the position of the Caption relative to the control.'''
        raise NotImplementedError()
    
    @property
    def is_word_wrapped(self) -> bool:
        '''Indicates whether the contents of the control automatically wrap at the end of a line.'''
        raise NotImplementedError()
    
    @is_word_wrapped.setter
    def is_word_wrapped(self, value : bool) -> None:
        '''Indicates whether the contents of the control automatically wrap at the end of a line.'''
        raise NotImplementedError()
    

class ScrollBarActiveXControl(SpinButtonActiveXControl):
    '''Represents the ScrollBar control.'''
    
    @property
    def workbook(self) -> aspose.cells.Workbook:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.activexcontrols.ControlType:
        '''Gets the type of the ActiveX control.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_icon(self) -> List[int]:
        raise NotImplementedError()
    
    @mouse_icon.setter
    def mouse_icon(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_pointer(self) -> aspose.cells.drawing.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.cells.drawing.activexcontrols.ControlMousePointerType) -> None:
        raise NotImplementedError()
    
    @property
    def fore_ole_color(self) -> int:
        raise NotImplementedError()
    
    @fore_ole_color.setter
    def fore_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def back_ole_color(self) -> int:
        raise NotImplementedError()
    
    @back_ole_color.setter
    def back_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def shadow(self) -> bool:
        raise NotImplementedError()
    
    @shadow.setter
    def shadow(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def linked_cell(self) -> str:
        raise NotImplementedError()
    
    @linked_cell.setter
    def linked_cell(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def list_fill_range(self) -> str:
        raise NotImplementedError()
    
    @list_fill_range.setter
    def list_fill_range(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def data(self) -> List[int]:
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_locked(self) -> bool:
        raise NotImplementedError()
    
    @is_locked.setter
    def is_locked(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_transparent(self) -> bool:
        raise NotImplementedError()
    
    @is_transparent.setter
    def is_transparent(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_auto_size(self) -> bool:
        raise NotImplementedError()
    
    @is_auto_size.setter
    def is_auto_size(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def ime_mode(self) -> aspose.cells.drawing.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.cells.drawing.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        raise NotImplementedError()
    
    @property
    def text_align(self) -> aspose.cells.TextAlignmentType:
        raise NotImplementedError()
    
    @text_align.setter
    def text_align(self, value : aspose.cells.TextAlignmentType) -> None:
        raise NotImplementedError()
    
    @property
    def min(self) -> int:
        '''Gets and sets the minimum acceptable value.'''
        raise NotImplementedError()
    
    @min.setter
    def min(self, value : int) -> None:
        '''Gets and sets the minimum acceptable value.'''
        raise NotImplementedError()
    
    @property
    def max(self) -> int:
        '''Gets and sets the maximum acceptable value.'''
        raise NotImplementedError()
    
    @max.setter
    def max(self, value : int) -> None:
        '''Gets and sets the maximum acceptable value.'''
        raise NotImplementedError()
    
    @property
    def position(self) -> int:
        '''Gets and sets the value.'''
        raise NotImplementedError()
    
    @position.setter
    def position(self, value : int) -> None:
        '''Gets and sets the value.'''
        raise NotImplementedError()
    
    @property
    def small_change(self) -> int:
        '''Gets and sets the amount by which the Position property changes'''
        raise NotImplementedError()
    
    @small_change.setter
    def small_change(self, value : int) -> None:
        '''Gets and sets the amount by which the Position property changes'''
        raise NotImplementedError()
    
    @property
    def orientation(self) -> aspose.cells.drawing.activexcontrols.ControlScrollOrientation:
        '''Gets and sets whether the SpinButton or ScrollBar is oriented vertically or horizontally.'''
        raise NotImplementedError()
    
    @orientation.setter
    def orientation(self, value : aspose.cells.drawing.activexcontrols.ControlScrollOrientation) -> None:
        '''Gets and sets whether the SpinButton or ScrollBar is oriented vertically or horizontally.'''
        raise NotImplementedError()
    
    @property
    def large_change(self) -> int:
        '''Gets and sets the amount by which the Position property changes'''
        raise NotImplementedError()
    
    @large_change.setter
    def large_change(self, value : int) -> None:
        '''Gets and sets the amount by which the Position property changes'''
        raise NotImplementedError()
    

class SpinButtonActiveXControl:
    '''Represents the SpinButton control.'''
    
    @property
    def workbook(self) -> aspose.cells.Workbook:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.activexcontrols.ControlType:
        '''Gets the type of the ActiveX control.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_icon(self) -> List[int]:
        raise NotImplementedError()
    
    @mouse_icon.setter
    def mouse_icon(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_pointer(self) -> aspose.cells.drawing.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.cells.drawing.activexcontrols.ControlMousePointerType) -> None:
        raise NotImplementedError()
    
    @property
    def fore_ole_color(self) -> int:
        raise NotImplementedError()
    
    @fore_ole_color.setter
    def fore_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def back_ole_color(self) -> int:
        raise NotImplementedError()
    
    @back_ole_color.setter
    def back_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def shadow(self) -> bool:
        raise NotImplementedError()
    
    @shadow.setter
    def shadow(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def linked_cell(self) -> str:
        raise NotImplementedError()
    
    @linked_cell.setter
    def linked_cell(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def list_fill_range(self) -> str:
        raise NotImplementedError()
    
    @list_fill_range.setter
    def list_fill_range(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def data(self) -> List[int]:
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_locked(self) -> bool:
        raise NotImplementedError()
    
    @is_locked.setter
    def is_locked(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_transparent(self) -> bool:
        raise NotImplementedError()
    
    @is_transparent.setter
    def is_transparent(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_auto_size(self) -> bool:
        raise NotImplementedError()
    
    @is_auto_size.setter
    def is_auto_size(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def ime_mode(self) -> aspose.cells.drawing.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.cells.drawing.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        raise NotImplementedError()
    
    @property
    def text_align(self) -> aspose.cells.TextAlignmentType:
        raise NotImplementedError()
    
    @text_align.setter
    def text_align(self, value : aspose.cells.TextAlignmentType) -> None:
        raise NotImplementedError()
    
    @property
    def min(self) -> int:
        '''Gets and sets the minimum acceptable value.'''
        raise NotImplementedError()
    
    @min.setter
    def min(self, value : int) -> None:
        '''Gets and sets the minimum acceptable value.'''
        raise NotImplementedError()
    
    @property
    def max(self) -> int:
        '''Gets and sets the maximum acceptable value.'''
        raise NotImplementedError()
    
    @max.setter
    def max(self, value : int) -> None:
        '''Gets and sets the maximum acceptable value.'''
        raise NotImplementedError()
    
    @property
    def position(self) -> int:
        '''Gets and sets the value.'''
        raise NotImplementedError()
    
    @position.setter
    def position(self, value : int) -> None:
        '''Gets and sets the value.'''
        raise NotImplementedError()
    
    @property
    def small_change(self) -> int:
        '''Gets and sets the amount by which the Position property changes'''
        raise NotImplementedError()
    
    @small_change.setter
    def small_change(self, value : int) -> None:
        '''Gets and sets the amount by which the Position property changes'''
        raise NotImplementedError()
    
    @property
    def orientation(self) -> aspose.cells.drawing.activexcontrols.ControlScrollOrientation:
        '''Gets and sets whether the SpinButton or ScrollBar is oriented vertically or horizontally.'''
        raise NotImplementedError()
    
    @orientation.setter
    def orientation(self, value : aspose.cells.drawing.activexcontrols.ControlScrollOrientation) -> None:
        '''Gets and sets whether the SpinButton or ScrollBar is oriented vertically or horizontally.'''
        raise NotImplementedError()
    

class TextBoxActiveXControl:
    '''Represents a text box ActiveX control.'''
    
    @property
    def workbook(self) -> aspose.cells.Workbook:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.activexcontrols.ControlType:
        '''Gets the type of the ActiveX control.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_icon(self) -> List[int]:
        raise NotImplementedError()
    
    @mouse_icon.setter
    def mouse_icon(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_pointer(self) -> aspose.cells.drawing.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.cells.drawing.activexcontrols.ControlMousePointerType) -> None:
        raise NotImplementedError()
    
    @property
    def fore_ole_color(self) -> int:
        raise NotImplementedError()
    
    @fore_ole_color.setter
    def fore_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def back_ole_color(self) -> int:
        raise NotImplementedError()
    
    @back_ole_color.setter
    def back_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def shadow(self) -> bool:
        raise NotImplementedError()
    
    @shadow.setter
    def shadow(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def linked_cell(self) -> str:
        raise NotImplementedError()
    
    @linked_cell.setter
    def linked_cell(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def list_fill_range(self) -> str:
        raise NotImplementedError()
    
    @list_fill_range.setter
    def list_fill_range(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def data(self) -> List[int]:
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_locked(self) -> bool:
        raise NotImplementedError()
    
    @is_locked.setter
    def is_locked(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_transparent(self) -> bool:
        raise NotImplementedError()
    
    @is_transparent.setter
    def is_transparent(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_auto_size(self) -> bool:
        raise NotImplementedError()
    
    @is_auto_size.setter
    def is_auto_size(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def ime_mode(self) -> aspose.cells.drawing.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.cells.drawing.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        raise NotImplementedError()
    
    @property
    def text_align(self) -> aspose.cells.TextAlignmentType:
        raise NotImplementedError()
    
    @text_align.setter
    def text_align(self, value : aspose.cells.TextAlignmentType) -> None:
        raise NotImplementedError()
    
    @property
    def border_style(self) -> aspose.cells.drawing.activexcontrols.ControlBorderType:
        '''Gets and set the type of border used by the control.'''
        raise NotImplementedError()
    
    @border_style.setter
    def border_style(self, value : aspose.cells.drawing.activexcontrols.ControlBorderType) -> None:
        '''Gets and set the type of border used by the control.'''
        raise NotImplementedError()
    
    @property
    def border_ole_color(self) -> int:
        '''Gets and sets the ole color of the background.'''
        raise NotImplementedError()
    
    @border_ole_color.setter
    def border_ole_color(self, value : int) -> None:
        '''Gets and sets the ole color of the background.'''
        raise NotImplementedError()
    
    @property
    def special_effect(self) -> aspose.cells.drawing.activexcontrols.ControlSpecialEffectType:
        '''Gets and sets the special effect of the control.'''
        raise NotImplementedError()
    
    @special_effect.setter
    def special_effect(self, value : aspose.cells.drawing.activexcontrols.ControlSpecialEffectType) -> None:
        '''Gets and sets the special effect of the control.'''
        raise NotImplementedError()
    
    @property
    def max_length(self) -> int:
        '''Gets and sets the maximum number of characters'''
        raise NotImplementedError()
    
    @max_length.setter
    def max_length(self, value : int) -> None:
        '''Gets and sets the maximum number of characters'''
        raise NotImplementedError()
    
    @property
    def scroll_bars(self) -> aspose.cells.drawing.activexcontrols.ControlScrollBarType:
        '''Indicates specifies whether the control has vertical scroll bars, horizontal scroll bars, both, or neither.'''
        raise NotImplementedError()
    
    @scroll_bars.setter
    def scroll_bars(self, value : aspose.cells.drawing.activexcontrols.ControlScrollBarType) -> None:
        '''Indicates specifies whether the control has vertical scroll bars, horizontal scroll bars, both, or neither.'''
        raise NotImplementedError()
    
    @property
    def password_char(self) -> System.Char:
        '''Gets and sets a character to be displayed in place of the characters entered.'''
        raise NotImplementedError()
    
    @password_char.setter
    def password_char(self, value : System.Char) -> None:
        '''Gets and sets a character to be displayed in place of the characters entered.'''
        raise NotImplementedError()
    
    @property
    def is_editable(self) -> bool:
        '''Indicates whether the user can type into the control.'''
        raise NotImplementedError()
    
    @is_editable.setter
    def is_editable(self, value : bool) -> None:
        '''Indicates whether the user can type into the control.'''
        raise NotImplementedError()
    
    @property
    def integral_height(self) -> bool:
        '''Indicates whether the control will only show complete lines of text without showing any partial lines.'''
        raise NotImplementedError()
    
    @integral_height.setter
    def integral_height(self, value : bool) -> None:
        '''Indicates whether the control will only show complete lines of text without showing any partial lines.'''
        raise NotImplementedError()
    
    @property
    def is_drag_behavior_enabled(self) -> bool:
        '''Indicates whether dragging and dropping is enabled for the control.'''
        raise NotImplementedError()
    
    @is_drag_behavior_enabled.setter
    def is_drag_behavior_enabled(self, value : bool) -> None:
        '''Indicates whether dragging and dropping is enabled for the control.'''
        raise NotImplementedError()
    
    @property
    def enter_key_behavior(self) -> bool:
        '''Specifies the behavior of the ENTER key.
        True specifies that pressing ENTER will create a new line.
        False specifies that pressing ENTER will move the focus to the next object in the tab order.'''
        raise NotImplementedError()
    
    @enter_key_behavior.setter
    def enter_key_behavior(self, value : bool) -> None:
        '''Specifies the behavior of the ENTER key.
        True specifies that pressing ENTER will create a new line.
        False specifies that pressing ENTER will move the focus to the next object in the tab order.'''
        raise NotImplementedError()
    
    @property
    def enter_field_behavior(self) -> bool:
        '''Specifies selection behavior when entering the control.
        True specifies that the selection remains unchanged from last time the control was active.
        False specifies that all the text in the control will be selected when entering the control.'''
        raise NotImplementedError()
    
    @enter_field_behavior.setter
    def enter_field_behavior(self, value : bool) -> None:
        '''Specifies selection behavior when entering the control.
        True specifies that the selection remains unchanged from last time the control was active.
        False specifies that all the text in the control will be selected when entering the control.'''
        raise NotImplementedError()
    
    @property
    def tab_key_behavior(self) -> bool:
        '''Indicates whether tab characters are allowed in the text of the control.'''
        raise NotImplementedError()
    
    @tab_key_behavior.setter
    def tab_key_behavior(self, value : bool) -> None:
        '''Indicates whether tab characters are allowed in the text of the control.'''
        raise NotImplementedError()
    
    @property
    def hide_selection(self) -> bool:
        '''Indicates whether selected text in the control appears highlighted when the control does not have focus.'''
        raise NotImplementedError()
    
    @hide_selection.setter
    def hide_selection(self, value : bool) -> None:
        '''Indicates whether selected text in the control appears highlighted when the control does not have focus.'''
        raise NotImplementedError()
    
    @property
    def is_auto_tab(self) -> bool:
        '''Indicates whether the focus will automatically move to the next control when the user enters the maximum number of characters.'''
        raise NotImplementedError()
    
    @is_auto_tab.setter
    def is_auto_tab(self, value : bool) -> None:
        '''Indicates whether the focus will automatically move to the next control when the user enters the maximum number of characters.'''
        raise NotImplementedError()
    
    @property
    def is_multi_line(self) -> bool:
        '''Indicates whether the control can display more than one line of text.'''
        raise NotImplementedError()
    
    @is_multi_line.setter
    def is_multi_line(self, value : bool) -> None:
        '''Indicates whether the control can display more than one line of text.'''
        raise NotImplementedError()
    
    @property
    def is_auto_word_selected(self) -> bool:
        '''Specifies the basic unit used to extend a selection.
        True specifies that the basic unit is a single character.
        false specifies that the basic unit is a whole word.'''
        raise NotImplementedError()
    
    @is_auto_word_selected.setter
    def is_auto_word_selected(self, value : bool) -> None:
        '''Specifies the basic unit used to extend a selection.
        True specifies that the basic unit is a single character.
        false specifies that the basic unit is a whole word.'''
        raise NotImplementedError()
    
    @property
    def is_word_wrapped(self) -> bool:
        '''Indicates whether the contents of the control automatically wrap at the end of a line.'''
        raise NotImplementedError()
    
    @is_word_wrapped.setter
    def is_word_wrapped(self, value : bool) -> None:
        '''Indicates whether the contents of the control automatically wrap at the end of a line.'''
        raise NotImplementedError()
    
    @property
    def text(self) -> str:
        '''Gets and set text of the control.'''
        raise NotImplementedError()
    
    @text.setter
    def text(self, value : str) -> None:
        '''Gets and set text of the control.'''
        raise NotImplementedError()
    
    @property
    def drop_button_style(self) -> aspose.cells.drawing.activexcontrols.DropButtonStyle:
        '''Specifies the symbol displayed on the drop button'''
        raise NotImplementedError()
    
    @drop_button_style.setter
    def drop_button_style(self, value : aspose.cells.drawing.activexcontrols.DropButtonStyle) -> None:
        '''Specifies the symbol displayed on the drop button'''
        raise NotImplementedError()
    
    @property
    def show_drop_button_type_when(self) -> aspose.cells.drawing.activexcontrols.ShowDropButtonType:
        '''Specifies the symbol displayed on the drop button'''
        raise NotImplementedError()
    
    @show_drop_button_type_when.setter
    def show_drop_button_type_when(self, value : aspose.cells.drawing.activexcontrols.ShowDropButtonType) -> None:
        '''Specifies the symbol displayed on the drop button'''
        raise NotImplementedError()
    

class ToggleButtonActiveXControl:
    '''Represents a ToggleButton ActiveX control.'''
    
    @property
    def workbook(self) -> aspose.cells.Workbook:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.activexcontrols.ControlType:
        '''Gets the type of the ActiveX control.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_icon(self) -> List[int]:
        raise NotImplementedError()
    
    @mouse_icon.setter
    def mouse_icon(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_pointer(self) -> aspose.cells.drawing.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.cells.drawing.activexcontrols.ControlMousePointerType) -> None:
        raise NotImplementedError()
    
    @property
    def fore_ole_color(self) -> int:
        raise NotImplementedError()
    
    @fore_ole_color.setter
    def fore_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def back_ole_color(self) -> int:
        raise NotImplementedError()
    
    @back_ole_color.setter
    def back_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def shadow(self) -> bool:
        raise NotImplementedError()
    
    @shadow.setter
    def shadow(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def linked_cell(self) -> str:
        raise NotImplementedError()
    
    @linked_cell.setter
    def linked_cell(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def list_fill_range(self) -> str:
        raise NotImplementedError()
    
    @list_fill_range.setter
    def list_fill_range(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def data(self) -> List[int]:
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_locked(self) -> bool:
        raise NotImplementedError()
    
    @is_locked.setter
    def is_locked(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_transparent(self) -> bool:
        raise NotImplementedError()
    
    @is_transparent.setter
    def is_transparent(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_auto_size(self) -> bool:
        raise NotImplementedError()
    
    @is_auto_size.setter
    def is_auto_size(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def ime_mode(self) -> aspose.cells.drawing.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.cells.drawing.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        raise NotImplementedError()
    
    @property
    def text_align(self) -> aspose.cells.TextAlignmentType:
        raise NotImplementedError()
    
    @text_align.setter
    def text_align(self, value : aspose.cells.TextAlignmentType) -> None:
        raise NotImplementedError()
    
    @property
    def caption(self) -> str:
        '''Gets and set the descriptive text that appears on a control.'''
        raise NotImplementedError()
    
    @caption.setter
    def caption(self, value : str) -> None:
        '''Gets and set the descriptive text that appears on a control.'''
        raise NotImplementedError()
    
    @property
    def picture_position(self) -> aspose.cells.drawing.activexcontrols.ControlPicturePositionType:
        '''Gets and set the location of the control\'s picture relative to its caption.'''
        raise NotImplementedError()
    
    @picture_position.setter
    def picture_position(self, value : aspose.cells.drawing.activexcontrols.ControlPicturePositionType) -> None:
        '''Gets and set the location of the control\'s picture relative to its caption.'''
        raise NotImplementedError()
    
    @property
    def special_effect(self) -> aspose.cells.drawing.activexcontrols.ControlSpecialEffectType:
        '''Gets and sets the special effect of the control.'''
        raise NotImplementedError()
    
    @special_effect.setter
    def special_effect(self, value : aspose.cells.drawing.activexcontrols.ControlSpecialEffectType) -> None:
        '''Gets and sets the special effect of the control.'''
        raise NotImplementedError()
    
    @property
    def picture(self) -> List[int]:
        '''Gets and sets the data of the picture.'''
        raise NotImplementedError()
    
    @picture.setter
    def picture(self, value : List[int]) -> None:
        '''Gets and sets the data of the picture.'''
        raise NotImplementedError()
    
    @property
    def accelerator(self) -> System.Char:
        '''Gets and sets the accelerator key for the control.'''
        raise NotImplementedError()
    
    @accelerator.setter
    def accelerator(self, value : System.Char) -> None:
        '''Gets and sets the accelerator key for the control.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> aspose.cells.drawing.CheckValueType:
        '''Indicates if the control is checked or not.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : aspose.cells.drawing.CheckValueType) -> None:
        '''Indicates if the control is checked or not.'''
        raise NotImplementedError()
    
    @property
    def is_triple_state(self) -> bool:
        '''Indicates how the specified control will display Null values.'''
        raise NotImplementedError()
    
    @is_triple_state.setter
    def is_triple_state(self, value : bool) -> None:
        '''Indicates how the specified control will display Null values.'''
        raise NotImplementedError()
    

class UnknownControl:
    '''Unknow control.'''
    
    def get_relationship_data(self, rel_id : str) -> List[int]:
        '''Gets the related data.
        
        :param rel_id: The relationship id.
        :returns: Returns the related data.'''
        raise NotImplementedError()
    
    @property
    def workbook(self) -> aspose.cells.Workbook:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.activexcontrols.ControlType:
        '''Gets the type of the ActiveX control.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def height(self) -> float:
        raise NotImplementedError()
    
    @height.setter
    def height(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_icon(self) -> List[int]:
        raise NotImplementedError()
    
    @mouse_icon.setter
    def mouse_icon(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def mouse_pointer(self) -> aspose.cells.drawing.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.cells.drawing.activexcontrols.ControlMousePointerType) -> None:
        raise NotImplementedError()
    
    @property
    def fore_ole_color(self) -> int:
        raise NotImplementedError()
    
    @fore_ole_color.setter
    def fore_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def back_ole_color(self) -> int:
        raise NotImplementedError()
    
    @back_ole_color.setter
    def back_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def shadow(self) -> bool:
        raise NotImplementedError()
    
    @shadow.setter
    def shadow(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def linked_cell(self) -> str:
        raise NotImplementedError()
    
    @linked_cell.setter
    def linked_cell(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def list_fill_range(self) -> str:
        raise NotImplementedError()
    
    @list_fill_range.setter
    def list_fill_range(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def data(self) -> List[int]:
        '''Gets and sets the binary data of the control.'''
        raise NotImplementedError()
    
    @property
    def is_enabled(self) -> bool:
        raise NotImplementedError()
    
    @is_enabled.setter
    def is_enabled(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_locked(self) -> bool:
        raise NotImplementedError()
    
    @is_locked.setter
    def is_locked(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_transparent(self) -> bool:
        raise NotImplementedError()
    
    @is_transparent.setter
    def is_transparent(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_auto_size(self) -> bool:
        raise NotImplementedError()
    
    @is_auto_size.setter
    def is_auto_size(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def ime_mode(self) -> aspose.cells.drawing.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.cells.drawing.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        raise NotImplementedError()
    
    @property
    def text_align(self) -> aspose.cells.TextAlignmentType:
        raise NotImplementedError()
    
    @text_align.setter
    def text_align(self, value : aspose.cells.TextAlignmentType) -> None:
        raise NotImplementedError()
    

class ActiveXPersistenceType:
    '''Represents the persistence method to persist an ActiveX control.'''
    
    PROPERTY_BAG : ActiveXPersistenceType
    '''The data is stored as xml data.'''
    STORAGE : ActiveXPersistenceType
    '''The data is stored as a storage binary data.'''
    STREAM : ActiveXPersistenceType
    '''The data is stored as a stream binary data.'''
    STREAM_INIT : ActiveXPersistenceType
    '''The data is stored as a streaminit binary data.'''

class ControlBorderType:
    '''Represents the border type of the ActiveX control.'''
    
    NONE : ControlBorderType
    '''No border.'''
    SINGLE : ControlBorderType
    '''The single line.'''

class ControlCaptionAlignmentType:
    '''Represents the position of the Caption relative to the control.'''
    
    LEFT : ControlCaptionAlignmentType
    '''The left of the control.'''
    RIGHT : ControlCaptionAlignmentType
    '''The right of the control.'''

class ControlListStyle:
    '''Represents the visual appearance of the list in a ListBox or ComboBox.'''
    
    PLAIN : ControlListStyle
    '''Displays a list in which the background of an item is highlighted when it is selected.'''
    OPTION : ControlListStyle
    '''Displays a list in which an option button or a checkbox next to each entry displays the selection state of that item.'''

class ControlMatchEntryType:
    '''Represents how a ListBox or ComboBox searches its list as the user types.'''
    
    FIRST_LETTER : ControlMatchEntryType
    '''The control searches for the next entry that starts with the character entered.
    Repeatedly typing the same letter cycles through all entries beginning with that letter.'''
    COMPLETE : ControlMatchEntryType
    '''As each character is typed, the control searches for an entry matching all characters entered.'''
    NONE : ControlMatchEntryType
    '''The list will not be searched when characters are typed.'''

class ControlMousePointerType:
    '''Represents the type of icon displayed as the mouse pointer for the control.'''
    
    DEFAULT : ControlMousePointerType
    '''Standard pointer.'''
    ARROW : ControlMousePointerType
    '''Arrow.'''
    CROSS : ControlMousePointerType
    '''Cross-hair pointer.'''
    I_BEAM : ControlMousePointerType
    '''I-beam.'''
    SIZE_NESW : ControlMousePointerType
    '''Double arrow pointing northeast and southwest.'''
    SIZE_NS : ControlMousePointerType
    '''Double arrow pointing north and south.'''
    SIZE_NWSE : ControlMousePointerType
    '''Double arrow pointing northwest and southeast.'''
    SIZE_WE : ControlMousePointerType
    '''Double arrow pointing west and east.'''
    UP_ARROW : ControlMousePointerType
    '''Up arrow.'''
    HOUR_GLASS : ControlMousePointerType
    '''Hourglass.'''
    NO_DROP : ControlMousePointerType
    '''"Not” symbol (circle with a diagonal line) on top of the object being dragged.'''
    APP_STARTING : ControlMousePointerType
    '''Arrow with an hourglass.'''
    HELP : ControlMousePointerType
    '''Arrow with a question mark.'''
    SIZE_ALL : ControlMousePointerType
    '''"Size-all” cursor (arrows pointing north, south, east, and west).'''
    CUSTOM : ControlMousePointerType
    '''Uses the icon specified by the MouseIcon property.'''

class ControlPictureAlignmentType:
    '''Represents the alignment of the picture inside the Form or Image.'''
    
    TOP_LEFT : ControlPictureAlignmentType
    '''The top left corner.'''
    TOP_RIGHT : ControlPictureAlignmentType
    '''The top right corner.'''
    CENTER : ControlPictureAlignmentType
    '''The center.'''
    BOTTOM_LEFT : ControlPictureAlignmentType
    '''The bottom left corner.'''
    BOTTOM_RIGHT : ControlPictureAlignmentType
    '''The bottom right corner.'''

class ControlPicturePositionType:
    '''Represents the location of the control\'s picture relative to its caption.'''
    
    LEFT_TOP : ControlPicturePositionType
    '''The picture appears to the left of the caption.
    The caption is aligned with the top of the picture.'''
    LEFT_CENTER : ControlPicturePositionType
    '''The picture appears to the left of the caption.
    The caption is centered relative to the picture.'''
    LEFT_BOTTOM : ControlPicturePositionType
    '''The picture appears to the left of the caption.
    The caption is aligned with the bottom of the picture.'''
    RIGHT_TOP : ControlPicturePositionType
    '''The picture appears to the right of the caption.
    The caption is aligned with the top of the picture.'''
    RIGHT_CENTER : ControlPicturePositionType
    '''The picture appears to the right of the caption.
    The caption is centered relative to the picture.'''
    RIGHT_BOTTOM : ControlPicturePositionType
    '''The picture appears to the right of the caption.
    The caption is aligned with the bottom of the picture.'''
    ABOVE_LEFT : ControlPicturePositionType
    '''The picture appears above the caption.
    The caption is aligned with the left edge of the picture.'''
    ABOVE_CENTER : ControlPicturePositionType
    '''The picture appears above the caption.
    The caption is centered below the picture.'''
    ABOVE_RIGHT : ControlPicturePositionType
    '''The picture appears above the caption.
    The caption is aligned with the right edge of the picture.'''
    BELOW_LEFT : ControlPicturePositionType
    '''The picture appears below the caption.
    The caption is aligned with the left edge of the picture.'''
    BELOW_CENTER : ControlPicturePositionType
    '''The picture appears below the caption.
    The caption is centered above the picture.'''
    BELOW_RIGHT : ControlPicturePositionType
    '''The picture appears below the caption.
    The caption is aligned with the right edge of the picture.'''
    CENTER : ControlPicturePositionType
    '''The picture appears in the center of the control.
    The caption is centered horizontally and vertically on top of the picture.'''

class ControlPictureSizeMode:
    '''Represents how to display the picture.'''
    
    CLIP : ControlPictureSizeMode
    '''Crops any part of the picture that is larger than the control\'s boundaries.'''
    STRETCH : ControlPictureSizeMode
    '''Stretches the picture to fill the control\'s area.
    This setting distorts the picture in either the horizontal or vertical direction.'''
    ZOOM : ControlPictureSizeMode
    '''Enlarges the picture, but does not distort the picture in either the horizontal or vertical direction.'''

class ControlScrollBarType:
    '''Represents the type of scroll bar.'''
    
    NONE : ControlScrollBarType
    '''Displays no scroll bars.'''
    HORIZONTAL : ControlScrollBarType
    '''Displays a horizontal scroll bar.'''
    BARS_VERTICAL : ControlScrollBarType
    '''Displays a vertical scroll bar.'''
    BARS_BOTH : ControlScrollBarType
    '''Displays both a horizontal and a vertical scroll bar.'''

class ControlScrollOrientation:
    '''Represents type of scroll orientation'''
    
    AUTO : ControlScrollOrientation
    '''Control is rendered horizontally when the control\'s width is greater than its height.
    Control is rendered vertically otherwise.'''
    VERTICAL : ControlScrollOrientation
    '''Control is rendered vertically.'''
    HORIZONTAL : ControlScrollOrientation
    '''Control is rendered horizontally.'''

class ControlSpecialEffectType:
    '''Represents the type of special effect.'''
    
    FLAT : ControlSpecialEffectType
    '''Flat'''
    RAISED : ControlSpecialEffectType
    '''Raised'''
    SUNKEN : ControlSpecialEffectType
    '''Sunken'''
    ETCHED : ControlSpecialEffectType
    '''Etched'''
    BUMP : ControlSpecialEffectType
    '''Bump'''

class ControlType:
    '''Represents all type of ActiveX control.'''
    
    COMMAND_BUTTON : ControlType
    '''Button'''
    COMBO_BOX : ControlType
    '''ComboBox'''
    CHECK_BOX : ControlType
    '''CheckBox'''
    LIST_BOX : ControlType
    '''ListBox'''
    TEXT_BOX : ControlType
    '''TextBox'''
    SPIN_BUTTON : ControlType
    '''Spinner'''
    RADIO_BUTTON : ControlType
    '''RadioButton'''
    LABEL : ControlType
    '''Label'''
    IMAGE : ControlType
    '''Image'''
    TOGGLE_BUTTON : ControlType
    '''ToggleButton'''
    SCROLL_BAR : ControlType
    '''ScrollBar'''
    BAR_CODE : ControlType
    '''ScrollBar'''
    UNKNOWN : ControlType
    '''Unknown'''

class DropButtonStyle:
    '''Represents the symbol displayed on the drop button.'''
    
    PLAIN : DropButtonStyle
    '''Displays a button with no symbol.'''
    ARROW : DropButtonStyle
    '''Displays a button with a down arrow.'''
    ELLIPSIS : DropButtonStyle
    '''Displays a button with an ellipsis (...).'''
    REDUCE : DropButtonStyle
    '''Displays a button with a horizontal line like an underscore character.'''

class InputMethodEditorMode:
    '''Represents the default run-time mode of the Input Method Editor.'''
    
    NO_CONTROL : InputMethodEditorMode
    '''Does not control IME.'''
    ON : InputMethodEditorMode
    '''IME on.'''
    OFF : InputMethodEditorMode
    '''IME off. English mode.'''
    DISABLE : InputMethodEditorMode
    '''IME off.User can\'t turn on IME by keyboard.'''
    HIRAGANA : InputMethodEditorMode
    '''IME on with Full-width hiragana mode.'''
    KATAKANA : InputMethodEditorMode
    '''IME on with Full-width katakana mode.'''
    KATAKANA_HALF : InputMethodEditorMode
    '''IME on with Half-width katakana mode.'''
    ALPHA_FULL : InputMethodEditorMode
    '''IME on with Full-width Alphanumeric mode.'''
    ALPHA : InputMethodEditorMode
    '''IME on with Half-width Alphanumeric mode.'''
    HANGUL_FULL : InputMethodEditorMode
    '''IME on with Full-width hangul mode.'''
    HANGUL : InputMethodEditorMode
    '''IME on with Half-width hangul mode.'''
    HANZI_FULL : InputMethodEditorMode
    '''IME on with Full-width hanzi mode.'''
    HANZI : InputMethodEditorMode
    '''IME on with Half-width hanzi mode.'''

class ShowDropButtonType:
    '''Specifies when to show the drop button'''
    
    NEVER : ShowDropButtonType
    '''Never show the drop button.'''
    FOCUS : ShowDropButtonType
    '''Show the drop button when the control has the focus.'''
    ALWAYS : ShowDropButtonType
    '''Always show the drop button.'''

