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

class LayoutOptions:
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def layout_style(self) -> aspose.diagram.autolayout.LayoutStyle:
        raise NotImplementedError()
    
    @layout_style.setter
    def layout_style(self, value : aspose.diagram.autolayout.LayoutStyle) -> None:
        raise NotImplementedError()
    
    @property
    def direction(self) -> aspose.diagram.autolayout.LayoutDirection:
        raise NotImplementedError()
    
    @direction.setter
    def direction(self, value : aspose.diagram.autolayout.LayoutDirection) -> None:
        raise NotImplementedError()
    
    @property
    def space_shapes(self) -> float:
        raise NotImplementedError()
    
    @space_shapes.setter
    def space_shapes(self, value : float) -> None:
        raise NotImplementedError()
    
    @property
    def enlarge_page(self) -> bool:
        raise NotImplementedError()
    
    @enlarge_page.setter
    def enlarge_page(self, value : bool) -> None:
        raise NotImplementedError()
    

class LayoutDirection:
    
    TOP_TO_BOTTOM : LayoutDirection
    BOTTOM_TO_TOP : LayoutDirection
    LEFT_TO_RIGHT : LayoutDirection
    RIGHT_TO_LEFT : LayoutDirection
    DOWN_THEN_RIGHT : LayoutDirection
    RIGHT_THEN_DOWN : LayoutDirection
    LEFT_THEN_DOWN : LayoutDirection
    DOWN_THEN_LEFT : LayoutDirection

class LayoutStyle:
    
    FLOW_CHART : LayoutStyle
    COMPACT_TREE : LayoutStyle
    RADIAL : LayoutStyle
    CIRCULAR : LayoutStyle

