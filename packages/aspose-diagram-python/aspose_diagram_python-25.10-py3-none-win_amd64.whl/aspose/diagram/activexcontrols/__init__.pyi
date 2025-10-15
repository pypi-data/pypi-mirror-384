from typing import List, Optional, Dict, Iterable, Any, overload
import io
import collections.abc
from collections.abc import Sequence
from datetime import datetime
from aspose.pyreflection import Type
import aspose.pycore
import aspose.pydrawing
from uuid import UUID
import aspose.diagram
import aspose.diagram.activexcontrols
import aspose.diagram.autolayout
import aspose.diagram.manipulation
import aspose.diagram.printing
import aspose.diagram.properties
import aspose.diagram.saving
import aspose.diagram.vba

class ActiveXControl(ActiveXControlBase):
    
    @property
    def type(self) -> aspose.diagram.activexcontrols.ControlType:
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
    def mouse_pointer(self) -> aspose.diagram.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.diagram.activexcontrols.ControlMousePointerType) -> None:
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
    def ime_mode(self) -> aspose.diagram.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.diagram.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    

class ActiveXControlBase:
    
    @property
    def type(self) -> aspose.diagram.activexcontrols.ControlType:
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
    def mouse_pointer(self) -> aspose.diagram.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.diagram.activexcontrols.ControlMousePointerType) -> None:
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
    def data(self) -> List[int]:
        raise NotImplementedError()
    

class CheckBoxActiveXControl(ActiveXControl):
    
    @property
    def type(self) -> aspose.diagram.activexcontrols.ControlType:
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
    def mouse_pointer(self) -> aspose.diagram.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.diagram.activexcontrols.ControlMousePointerType) -> None:
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
    def ime_mode(self) -> aspose.diagram.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.diagram.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def group_name(self) -> str:
        raise NotImplementedError()
    
    @group_name.setter
    def group_name(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def alignment(self) -> aspose.diagram.activexcontrols.ControlCaptionAlignmentType:
        raise NotImplementedError()
    
    @alignment.setter
    def alignment(self, value : aspose.diagram.activexcontrols.ControlCaptionAlignmentType) -> None:
        raise NotImplementedError()
    
    @property
    def is_word_wrapped(self) -> bool:
        raise NotImplementedError()
    
    @is_word_wrapped.setter
    def is_word_wrapped(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def caption(self) -> str:
        raise NotImplementedError()
    
    @caption.setter
    def caption(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def picture_position(self) -> aspose.diagram.activexcontrols.ControlPicturePositionType:
        raise NotImplementedError()
    
    @picture_position.setter
    def picture_position(self, value : aspose.diagram.activexcontrols.ControlPicturePositionType) -> None:
        raise NotImplementedError()
    
    @property
    def special_effect(self) -> aspose.diagram.activexcontrols.ControlSpecialEffectType:
        raise NotImplementedError()
    
    @special_effect.setter
    def special_effect(self, value : aspose.diagram.activexcontrols.ControlSpecialEffectType) -> None:
        raise NotImplementedError()
    
    @property
    def picture(self) -> List[int]:
        raise NotImplementedError()
    
    @picture.setter
    def picture(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def accelerator(self) -> str:
        raise NotImplementedError()
    
    @accelerator.setter
    def accelerator(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def value(self) -> aspose.diagram.activexcontrols.CheckValueType:
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : aspose.diagram.activexcontrols.CheckValueType) -> None:
        raise NotImplementedError()
    
    @property
    def is_triple_state(self) -> bool:
        raise NotImplementedError()
    
    @is_triple_state.setter
    def is_triple_state(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_checked(self) -> bool:
        raise NotImplementedError()
    
    @is_checked.setter
    def is_checked(self, value : bool) -> None:
        raise NotImplementedError()
    

class ComboBoxActiveXControl(ActiveXControl):
    
    @property
    def type(self) -> aspose.diagram.activexcontrols.ControlType:
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
    def mouse_pointer(self) -> aspose.diagram.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.diagram.activexcontrols.ControlMousePointerType) -> None:
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
    def ime_mode(self) -> aspose.diagram.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.diagram.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def max_length(self) -> int:
        raise NotImplementedError()
    
    @max_length.setter
    def max_length(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def list_width(self) -> float:
        raise NotImplementedError()
    
    @list_width.setter
    def list_width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def bound_column(self) -> int:
        raise NotImplementedError()
    
    @bound_column.setter
    def bound_column(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def text_column(self) -> int:
        raise NotImplementedError()
    
    @text_column.setter
    def text_column(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def column_count(self) -> int:
        raise NotImplementedError()
    
    @column_count.setter
    def column_count(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def list_rows(self) -> int:
        raise NotImplementedError()
    
    @list_rows.setter
    def list_rows(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def match_entry(self) -> aspose.diagram.activexcontrols.ControlMatchEntryType:
        raise NotImplementedError()
    
    @match_entry.setter
    def match_entry(self, value : aspose.diagram.activexcontrols.ControlMatchEntryType) -> None:
        raise NotImplementedError()
    
    @property
    def drop_button_style(self) -> aspose.diagram.activexcontrols.DropButtonStyle:
        raise NotImplementedError()
    
    @drop_button_style.setter
    def drop_button_style(self, value : aspose.diagram.activexcontrols.DropButtonStyle) -> None:
        raise NotImplementedError()
    
    @property
    def show_drop_button_type_when(self) -> aspose.diagram.activexcontrols.ShowDropButtonType:
        raise NotImplementedError()
    
    @show_drop_button_type_when.setter
    def show_drop_button_type_when(self, value : aspose.diagram.activexcontrols.ShowDropButtonType) -> None:
        raise NotImplementedError()
    
    @property
    def list_style(self) -> aspose.diagram.activexcontrols.ControlListStyle:
        raise NotImplementedError()
    
    @list_style.setter
    def list_style(self, value : aspose.diagram.activexcontrols.ControlListStyle) -> None:
        raise NotImplementedError()
    
    @property
    def border_style(self) -> aspose.diagram.activexcontrols.ControlBorderType:
        raise NotImplementedError()
    
    @border_style.setter
    def border_style(self, value : aspose.diagram.activexcontrols.ControlBorderType) -> None:
        raise NotImplementedError()
    
    @property
    def border_ole_color(self) -> int:
        raise NotImplementedError()
    
    @border_ole_color.setter
    def border_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def special_effect(self) -> aspose.diagram.activexcontrols.ControlSpecialEffectType:
        raise NotImplementedError()
    
    @special_effect.setter
    def special_effect(self, value : aspose.diagram.activexcontrols.ControlSpecialEffectType) -> None:
        raise NotImplementedError()
    
    @property
    def is_editable(self) -> bool:
        raise NotImplementedError()
    
    @is_editable.setter
    def is_editable(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def show_column_heads(self) -> bool:
        raise NotImplementedError()
    
    @show_column_heads.setter
    def show_column_heads(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_drag_behavior_enabled(self) -> bool:
        raise NotImplementedError()
    
    @is_drag_behavior_enabled.setter
    def is_drag_behavior_enabled(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def enter_field_behavior(self) -> bool:
        raise NotImplementedError()
    
    @enter_field_behavior.setter
    def enter_field_behavior(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_auto_word_selected(self) -> bool:
        raise NotImplementedError()
    
    @is_auto_word_selected.setter
    def is_auto_word_selected(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def selection_margin(self) -> bool:
        raise NotImplementedError()
    
    @selection_margin.setter
    def selection_margin(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def hide_selection(self) -> bool:
        raise NotImplementedError()
    
    @hide_selection.setter
    def hide_selection(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def column_widths(self) -> float:
        raise NotImplementedError()
    
    @column_widths.setter
    def column_widths(self, value : float) -> None:
        raise NotImplementedError()
    

class CommandButtonActiveXControl(ActiveXControl):
    
    @property
    def type(self) -> aspose.diagram.activexcontrols.ControlType:
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
    def mouse_pointer(self) -> aspose.diagram.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.diagram.activexcontrols.ControlMousePointerType) -> None:
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
    def ime_mode(self) -> aspose.diagram.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.diagram.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def caption(self) -> str:
        raise NotImplementedError()
    
    @caption.setter
    def caption(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def picture_position(self) -> aspose.diagram.activexcontrols.ControlPicturePositionType:
        raise NotImplementedError()
    
    @picture_position.setter
    def picture_position(self, value : aspose.diagram.activexcontrols.ControlPicturePositionType) -> None:
        raise NotImplementedError()
    
    @property
    def picture(self) -> List[int]:
        raise NotImplementedError()
    
    @picture.setter
    def picture(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def accelerator(self) -> str:
        raise NotImplementedError()
    
    @accelerator.setter
    def accelerator(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def take_focus_on_click(self) -> bool:
        raise NotImplementedError()
    
    @take_focus_on_click.setter
    def take_focus_on_click(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_word_wrapped(self) -> bool:
        raise NotImplementedError()
    
    @is_word_wrapped.setter
    def is_word_wrapped(self, value : bool) -> None:
        raise NotImplementedError()
    

class ImageActiveXControl(ActiveXControl):
    
    @property
    def type(self) -> aspose.diagram.activexcontrols.ControlType:
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
    def mouse_pointer(self) -> aspose.diagram.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.diagram.activexcontrols.ControlMousePointerType) -> None:
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
    def ime_mode(self) -> aspose.diagram.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.diagram.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def border_ole_color(self) -> int:
        raise NotImplementedError()
    
    @border_ole_color.setter
    def border_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def border_style(self) -> aspose.diagram.activexcontrols.ControlBorderType:
        raise NotImplementedError()
    
    @border_style.setter
    def border_style(self, value : aspose.diagram.activexcontrols.ControlBorderType) -> None:
        raise NotImplementedError()
    
    @property
    def picture_size_mode(self) -> aspose.diagram.activexcontrols.ControlPictureSizeMode:
        raise NotImplementedError()
    
    @picture_size_mode.setter
    def picture_size_mode(self, value : aspose.diagram.activexcontrols.ControlPictureSizeMode) -> None:
        raise NotImplementedError()
    
    @property
    def special_effect(self) -> aspose.diagram.activexcontrols.ControlSpecialEffectType:
        raise NotImplementedError()
    
    @special_effect.setter
    def special_effect(self, value : aspose.diagram.activexcontrols.ControlSpecialEffectType) -> None:
        raise NotImplementedError()
    
    @property
    def picture(self) -> List[int]:
        raise NotImplementedError()
    
    @picture.setter
    def picture(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def picture_alignment(self) -> aspose.diagram.activexcontrols.ControlPictureAlignmentType:
        raise NotImplementedError()
    
    @picture_alignment.setter
    def picture_alignment(self, value : aspose.diagram.activexcontrols.ControlPictureAlignmentType) -> None:
        raise NotImplementedError()
    
    @property
    def is_tiled(self) -> bool:
        raise NotImplementedError()
    
    @is_tiled.setter
    def is_tiled(self, value : bool) -> None:
        raise NotImplementedError()
    

class LabelActiveXControl(ActiveXControl):
    
    @property
    def type(self) -> aspose.diagram.activexcontrols.ControlType:
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
    def mouse_pointer(self) -> aspose.diagram.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.diagram.activexcontrols.ControlMousePointerType) -> None:
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
    def ime_mode(self) -> aspose.diagram.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.diagram.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def caption(self) -> str:
        raise NotImplementedError()
    
    @caption.setter
    def caption(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def picture_position(self) -> aspose.diagram.activexcontrols.ControlPicturePositionType:
        raise NotImplementedError()
    
    @picture_position.setter
    def picture_position(self, value : aspose.diagram.activexcontrols.ControlPicturePositionType) -> None:
        raise NotImplementedError()
    
    @property
    def border_ole_color(self) -> int:
        raise NotImplementedError()
    
    @border_ole_color.setter
    def border_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def border_style(self) -> aspose.diagram.activexcontrols.ControlBorderType:
        raise NotImplementedError()
    
    @border_style.setter
    def border_style(self, value : aspose.diagram.activexcontrols.ControlBorderType) -> None:
        raise NotImplementedError()
    
    @property
    def special_effect(self) -> aspose.diagram.activexcontrols.ControlSpecialEffectType:
        raise NotImplementedError()
    
    @special_effect.setter
    def special_effect(self, value : aspose.diagram.activexcontrols.ControlSpecialEffectType) -> None:
        raise NotImplementedError()
    
    @property
    def picture(self) -> List[int]:
        raise NotImplementedError()
    
    @picture.setter
    def picture(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def accelerator(self) -> str:
        raise NotImplementedError()
    
    @accelerator.setter
    def accelerator(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def is_word_wrapped(self) -> bool:
        raise NotImplementedError()
    
    @is_word_wrapped.setter
    def is_word_wrapped(self, value : bool) -> None:
        raise NotImplementedError()
    

class ListBoxActiveXControl(ActiveXControl):
    
    @property
    def type(self) -> aspose.diagram.activexcontrols.ControlType:
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
    def mouse_pointer(self) -> aspose.diagram.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.diagram.activexcontrols.ControlMousePointerType) -> None:
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
    def ime_mode(self) -> aspose.diagram.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.diagram.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def scroll_bars(self) -> aspose.diagram.activexcontrols.ControlScrollBarType:
        raise NotImplementedError()
    
    @scroll_bars.setter
    def scroll_bars(self, value : aspose.diagram.activexcontrols.ControlScrollBarType) -> None:
        raise NotImplementedError()
    
    @property
    def list_width(self) -> float:
        raise NotImplementedError()
    
    @list_width.setter
    def list_width(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def bound_column(self) -> int:
        raise NotImplementedError()
    
    @bound_column.setter
    def bound_column(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def text_column(self) -> int:
        raise NotImplementedError()
    
    @text_column.setter
    def text_column(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def column_count(self) -> int:
        raise NotImplementedError()
    
    @column_count.setter
    def column_count(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def match_entry(self) -> aspose.diagram.activexcontrols.ControlMatchEntryType:
        raise NotImplementedError()
    
    @match_entry.setter
    def match_entry(self, value : aspose.diagram.activexcontrols.ControlMatchEntryType) -> None:
        raise NotImplementedError()
    
    @property
    def list_style(self) -> aspose.diagram.activexcontrols.ControlListStyle:
        raise NotImplementedError()
    
    @list_style.setter
    def list_style(self, value : aspose.diagram.activexcontrols.ControlListStyle) -> None:
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def border_style(self) -> aspose.diagram.activexcontrols.ControlBorderType:
        raise NotImplementedError()
    
    @border_style.setter
    def border_style(self, value : aspose.diagram.activexcontrols.ControlBorderType) -> None:
        raise NotImplementedError()
    
    @property
    def border_ole_color(self) -> int:
        raise NotImplementedError()
    
    @border_ole_color.setter
    def border_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def special_effect(self) -> aspose.diagram.activexcontrols.ControlSpecialEffectType:
        raise NotImplementedError()
    
    @special_effect.setter
    def special_effect(self, value : aspose.diagram.activexcontrols.ControlSpecialEffectType) -> None:
        raise NotImplementedError()
    
    @property
    def show_column_heads(self) -> bool:
        raise NotImplementedError()
    
    @show_column_heads.setter
    def show_column_heads(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def integral_height(self) -> bool:
        raise NotImplementedError()
    
    @integral_height.setter
    def integral_height(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def column_widths(self) -> float:
        raise NotImplementedError()
    
    @column_widths.setter
    def column_widths(self, value : float) -> None:
        raise NotImplementedError()
    

class RadioButtonActiveXControl(ToggleButtonActiveXControl):
    
    @property
    def type(self) -> aspose.diagram.activexcontrols.ControlType:
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
    def mouse_pointer(self) -> aspose.diagram.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.diagram.activexcontrols.ControlMousePointerType) -> None:
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
    def ime_mode(self) -> aspose.diagram.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.diagram.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def caption(self) -> str:
        raise NotImplementedError()
    
    @caption.setter
    def caption(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def picture_position(self) -> aspose.diagram.activexcontrols.ControlPicturePositionType:
        raise NotImplementedError()
    
    @picture_position.setter
    def picture_position(self, value : aspose.diagram.activexcontrols.ControlPicturePositionType) -> None:
        raise NotImplementedError()
    
    @property
    def special_effect(self) -> aspose.diagram.activexcontrols.ControlSpecialEffectType:
        raise NotImplementedError()
    
    @special_effect.setter
    def special_effect(self, value : aspose.diagram.activexcontrols.ControlSpecialEffectType) -> None:
        raise NotImplementedError()
    
    @property
    def picture(self) -> List[int]:
        raise NotImplementedError()
    
    @picture.setter
    def picture(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def accelerator(self) -> str:
        raise NotImplementedError()
    
    @accelerator.setter
    def accelerator(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def value(self) -> aspose.diagram.activexcontrols.CheckValueType:
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : aspose.diagram.activexcontrols.CheckValueType) -> None:
        raise NotImplementedError()
    
    @property
    def is_triple_state(self) -> bool:
        raise NotImplementedError()
    
    @is_triple_state.setter
    def is_triple_state(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def group_name(self) -> str:
        raise NotImplementedError()
    
    @group_name.setter
    def group_name(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def alignment(self) -> aspose.diagram.activexcontrols.ControlCaptionAlignmentType:
        raise NotImplementedError()
    
    @alignment.setter
    def alignment(self, value : aspose.diagram.activexcontrols.ControlCaptionAlignmentType) -> None:
        raise NotImplementedError()
    
    @property
    def is_word_wrapped(self) -> bool:
        raise NotImplementedError()
    
    @is_word_wrapped.setter
    def is_word_wrapped(self, value : bool) -> None:
        raise NotImplementedError()
    

class ScrollBarActiveXControl(SpinButtonActiveXControl):
    
    @property
    def type(self) -> aspose.diagram.activexcontrols.ControlType:
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
    def mouse_pointer(self) -> aspose.diagram.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.diagram.activexcontrols.ControlMousePointerType) -> None:
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
    def ime_mode(self) -> aspose.diagram.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.diagram.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def min(self) -> int:
        raise NotImplementedError()
    
    @min.setter
    def min(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def max(self) -> int:
        raise NotImplementedError()
    
    @max.setter
    def max(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def position(self) -> int:
        raise NotImplementedError()
    
    @position.setter
    def position(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def small_change(self) -> int:
        raise NotImplementedError()
    
    @small_change.setter
    def small_change(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def orientation(self) -> aspose.diagram.activexcontrols.ControlScrollOrientation:
        raise NotImplementedError()
    
    @orientation.setter
    def orientation(self, value : aspose.diagram.activexcontrols.ControlScrollOrientation) -> None:
        raise NotImplementedError()
    
    @property
    def large_change(self) -> int:
        raise NotImplementedError()
    
    @large_change.setter
    def large_change(self, value : int) -> None:
        raise NotImplementedError()
    

class SpinButtonActiveXControl(ActiveXControl):
    
    @property
    def type(self) -> aspose.diagram.activexcontrols.ControlType:
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
    def mouse_pointer(self) -> aspose.diagram.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.diagram.activexcontrols.ControlMousePointerType) -> None:
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
    def ime_mode(self) -> aspose.diagram.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.diagram.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def min(self) -> int:
        raise NotImplementedError()
    
    @min.setter
    def min(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def max(self) -> int:
        raise NotImplementedError()
    
    @max.setter
    def max(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def position(self) -> int:
        raise NotImplementedError()
    
    @position.setter
    def position(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def small_change(self) -> int:
        raise NotImplementedError()
    
    @small_change.setter
    def small_change(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def orientation(self) -> aspose.diagram.activexcontrols.ControlScrollOrientation:
        raise NotImplementedError()
    
    @orientation.setter
    def orientation(self, value : aspose.diagram.activexcontrols.ControlScrollOrientation) -> None:
        raise NotImplementedError()
    

class TextBoxActiveXControl(ActiveXControl):
    
    @property
    def type(self) -> aspose.diagram.activexcontrols.ControlType:
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
    def mouse_pointer(self) -> aspose.diagram.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.diagram.activexcontrols.ControlMousePointerType) -> None:
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
    def ime_mode(self) -> aspose.diagram.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.diagram.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def border_style(self) -> aspose.diagram.activexcontrols.ControlBorderType:
        raise NotImplementedError()
    
    @border_style.setter
    def border_style(self, value : aspose.diagram.activexcontrols.ControlBorderType) -> None:
        raise NotImplementedError()
    
    @property
    def border_ole_color(self) -> int:
        raise NotImplementedError()
    
    @border_ole_color.setter
    def border_ole_color(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def special_effect(self) -> aspose.diagram.activexcontrols.ControlSpecialEffectType:
        raise NotImplementedError()
    
    @special_effect.setter
    def special_effect(self, value : aspose.diagram.activexcontrols.ControlSpecialEffectType) -> None:
        raise NotImplementedError()
    
    @property
    def max_length(self) -> int:
        raise NotImplementedError()
    
    @max_length.setter
    def max_length(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def scroll_bars(self) -> aspose.diagram.activexcontrols.ControlScrollBarType:
        raise NotImplementedError()
    
    @scroll_bars.setter
    def scroll_bars(self, value : aspose.diagram.activexcontrols.ControlScrollBarType) -> None:
        raise NotImplementedError()
    
    @property
    def password_char(self) -> str:
        raise NotImplementedError()
    
    @password_char.setter
    def password_char(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def is_editable(self) -> bool:
        raise NotImplementedError()
    
    @is_editable.setter
    def is_editable(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def integral_height(self) -> bool:
        raise NotImplementedError()
    
    @integral_height.setter
    def integral_height(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_drag_behavior_enabled(self) -> bool:
        raise NotImplementedError()
    
    @is_drag_behavior_enabled.setter
    def is_drag_behavior_enabled(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def enter_key_behavior(self) -> bool:
        raise NotImplementedError()
    
    @enter_key_behavior.setter
    def enter_key_behavior(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def enter_field_behavior(self) -> bool:
        raise NotImplementedError()
    
    @enter_field_behavior.setter
    def enter_field_behavior(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def tab_key_behavior(self) -> bool:
        raise NotImplementedError()
    
    @tab_key_behavior.setter
    def tab_key_behavior(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def hide_selection(self) -> bool:
        raise NotImplementedError()
    
    @hide_selection.setter
    def hide_selection(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_auto_tab(self) -> bool:
        raise NotImplementedError()
    
    @is_auto_tab.setter
    def is_auto_tab(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_multi_line(self) -> bool:
        raise NotImplementedError()
    
    @is_multi_line.setter
    def is_multi_line(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_auto_word_selected(self) -> bool:
        raise NotImplementedError()
    
    @is_auto_word_selected.setter
    def is_auto_word_selected(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def is_word_wrapped(self) -> bool:
        raise NotImplementedError()
    
    @is_word_wrapped.setter
    def is_word_wrapped(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def text(self) -> str:
        raise NotImplementedError()
    
    @text.setter
    def text(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def drop_button_style(self) -> aspose.diagram.activexcontrols.DropButtonStyle:
        raise NotImplementedError()
    
    @drop_button_style.setter
    def drop_button_style(self, value : aspose.diagram.activexcontrols.DropButtonStyle) -> None:
        raise NotImplementedError()
    
    @property
    def show_drop_button_type_when(self) -> aspose.diagram.activexcontrols.ShowDropButtonType:
        raise NotImplementedError()
    
    @show_drop_button_type_when.setter
    def show_drop_button_type_when(self, value : aspose.diagram.activexcontrols.ShowDropButtonType) -> None:
        raise NotImplementedError()
    

class ToggleButtonActiveXControl(ActiveXControl):
    
    @property
    def type(self) -> aspose.diagram.activexcontrols.ControlType:
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
    def mouse_pointer(self) -> aspose.diagram.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.diagram.activexcontrols.ControlMousePointerType) -> None:
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
    def ime_mode(self) -> aspose.diagram.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.diagram.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def caption(self) -> str:
        raise NotImplementedError()
    
    @caption.setter
    def caption(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def picture_position(self) -> aspose.diagram.activexcontrols.ControlPicturePositionType:
        raise NotImplementedError()
    
    @picture_position.setter
    def picture_position(self, value : aspose.diagram.activexcontrols.ControlPicturePositionType) -> None:
        raise NotImplementedError()
    
    @property
    def special_effect(self) -> aspose.diagram.activexcontrols.ControlSpecialEffectType:
        raise NotImplementedError()
    
    @special_effect.setter
    def special_effect(self, value : aspose.diagram.activexcontrols.ControlSpecialEffectType) -> None:
        raise NotImplementedError()
    
    @property
    def picture(self) -> List[int]:
        raise NotImplementedError()
    
    @picture.setter
    def picture(self, value : List[int]) -> None:
        raise NotImplementedError()
    
    @property
    def accelerator(self) -> str:
        raise NotImplementedError()
    
    @accelerator.setter
    def accelerator(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def value(self) -> aspose.diagram.activexcontrols.CheckValueType:
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : aspose.diagram.activexcontrols.CheckValueType) -> None:
        raise NotImplementedError()
    
    @property
    def is_triple_state(self) -> bool:
        raise NotImplementedError()
    
    @is_triple_state.setter
    def is_triple_state(self, value : bool) -> None:
        raise NotImplementedError()
    

class UnknownControl(ActiveXControl):
    
    def get_relationship_data(self, rel_id : str) -> List[int]:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.diagram.activexcontrols.ControlType:
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
    def mouse_pointer(self) -> aspose.diagram.activexcontrols.ControlMousePointerType:
        raise NotImplementedError()
    
    @mouse_pointer.setter
    def mouse_pointer(self, value : aspose.diagram.activexcontrols.ControlMousePointerType) -> None:
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
    def ime_mode(self) -> aspose.diagram.activexcontrols.InputMethodEditorMode:
        raise NotImplementedError()
    
    @ime_mode.setter
    def ime_mode(self, value : aspose.diagram.activexcontrols.InputMethodEditorMode) -> None:
        raise NotImplementedError()
    
    @property
    def persistence_type(self) -> aspose.diagram.activexcontrols.ActiveXPersistenceType:
        raise NotImplementedError()
    

class ActiveXPersistenceType:
    
    PROPERTY_BAG : ActiveXPersistenceType
    STORAGE : ActiveXPersistenceType
    STREAM : ActiveXPersistenceType
    STREAM_INIT : ActiveXPersistenceType

class CheckValueType:
    
    UN_CHECKED : CheckValueType
    CHECKED : CheckValueType
    MIXED : CheckValueType

class ControlBorderType:
    
    NONE : ControlBorderType
    SINGLE : ControlBorderType

class ControlCaptionAlignmentType:
    
    LEFT : ControlCaptionAlignmentType
    RIGHT : ControlCaptionAlignmentType

class ControlListStyle:
    
    PLAIN : ControlListStyle
    OPTION : ControlListStyle

class ControlMatchEntryType:
    
    FIRST_LETTER : ControlMatchEntryType
    COMPLETE : ControlMatchEntryType
    NONE : ControlMatchEntryType

class ControlMousePointerType:
    
    DEFAULT : ControlMousePointerType
    ARROW : ControlMousePointerType
    CROSS : ControlMousePointerType
    I_BEAM : ControlMousePointerType
    SIZE_NESW : ControlMousePointerType
    SIZE_NS : ControlMousePointerType
    SIZE_NWSE : ControlMousePointerType
    SIZE_WE : ControlMousePointerType
    UP_ARROW : ControlMousePointerType
    HOUR_GLASS : ControlMousePointerType
    NO_DROP : ControlMousePointerType
    APP_STARTING : ControlMousePointerType
    HELP : ControlMousePointerType
    SIZE_ALL : ControlMousePointerType
    CUSTOM : ControlMousePointerType

class ControlPictureAlignmentType:
    
    TOP_LEFT : ControlPictureAlignmentType
    TOP_RIGHT : ControlPictureAlignmentType
    CENTER : ControlPictureAlignmentType
    BOTTOM_LEFT : ControlPictureAlignmentType
    BOTTOM_RIGHT : ControlPictureAlignmentType

class ControlPicturePositionType:
    
    LEFT_TOP : ControlPicturePositionType
    LEFT_CENTER : ControlPicturePositionType
    LEFT_BOTTOM : ControlPicturePositionType
    RIGHT_TOP : ControlPicturePositionType
    RIGHT_CENTER : ControlPicturePositionType
    RIGHT_BOTTOM : ControlPicturePositionType
    ABOVE_LEFT : ControlPicturePositionType
    ABOVE_CENTER : ControlPicturePositionType
    ABOVE_RIGHT : ControlPicturePositionType
    BELOW_LEFT : ControlPicturePositionType
    BELOW_CENTER : ControlPicturePositionType
    BELOW_RIGHT : ControlPicturePositionType
    CENTER : ControlPicturePositionType

class ControlPictureSizeMode:
    
    CLIP : ControlPictureSizeMode
    STRETCH : ControlPictureSizeMode
    ZOOM : ControlPictureSizeMode

class ControlScrollBarType:
    
    NONE : ControlScrollBarType
    HORIZONTAL : ControlScrollBarType
    BARS_VERTICAL : ControlScrollBarType
    BARS_BOTH : ControlScrollBarType

class ControlScrollOrientation:
    
    AUTO : ControlScrollOrientation
    VERTICAL : ControlScrollOrientation
    HORIZONTAL : ControlScrollOrientation

class ControlSpecialEffectType:
    
    FLAT : ControlSpecialEffectType
    RAISED : ControlSpecialEffectType
    SUNKEN : ControlSpecialEffectType
    ETCHED : ControlSpecialEffectType
    BUMP : ControlSpecialEffectType

class ControlType:
    
    COMMAND_BUTTON : ControlType
    COMBO_BOX : ControlType
    CHECK_BOX : ControlType
    LIST_BOX : ControlType
    TEXT_BOX : ControlType
    SPIN_BUTTON : ControlType
    RADIO_BUTTON : ControlType
    LABEL : ControlType
    IMAGE : ControlType
    TOGGLE_BUTTON : ControlType
    SCROLL_BAR : ControlType
    UNKNOWN : ControlType

class DropButtonStyle:
    
    PLAIN : DropButtonStyle
    ARROW : DropButtonStyle
    ELLIPSIS : DropButtonStyle
    REDUCE : DropButtonStyle

class InputMethodEditorMode:
    
    NO_CONTROL : InputMethodEditorMode
    ON : InputMethodEditorMode
    OFF : InputMethodEditorMode
    DISABLE : InputMethodEditorMode
    HIRAGANA : InputMethodEditorMode
    KATAKANA : InputMethodEditorMode
    KATAKANA_HALF : InputMethodEditorMode
    ALPHA_FULL : InputMethodEditorMode
    ALPHA : InputMethodEditorMode
    HANGUL_FULL : InputMethodEditorMode
    HANGUL : InputMethodEditorMode
    HANZI_FULL : InputMethodEditorMode
    HANZI : InputMethodEditorMode

class ShowDropButtonType:
    
    NEVER : ShowDropButtonType
    FOCUS : ShowDropButtonType
    ALWAYS : ShowDropButtonType

