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

class DocumentProperty:
    
    def to_int(self) -> int:
        raise NotImplementedError()
    
    def to_double(self) -> float:
        raise NotImplementedError()
    
    def to_date_time(self) -> datetime:
        raise NotImplementedError()
    
    def to_bool(self) -> bool:
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        raise NotImplementedError()
    
    @property
    def value(self) -> Any:
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : Any) -> None:
        raise NotImplementedError()
    
    @property
    def is_linked_to_content(self) -> bool:
        raise NotImplementedError()
    
    @property
    def source(self) -> str:
        raise NotImplementedError()
    
    @property
    def is_generated_name(self) -> bool:
        raise NotImplementedError()
    

class DocumentPropertyCollection:
    
    def contains(self, name : str) -> bool:
        raise NotImplementedError()
    
    def index_of(self, name : str) -> int:
        raise NotImplementedError()
    
    def remove_at(self, index : int) -> None:
        raise NotImplementedError()
    
    def clear(self) -> None:
        raise NotImplementedError()
    
    @property
    def count(self) -> int:
        raise NotImplementedError()
    
    def __getitem__(self, key : int) -> aspose.diagram.properties.DocumentProperty:
        raise NotImplementedError()
    

