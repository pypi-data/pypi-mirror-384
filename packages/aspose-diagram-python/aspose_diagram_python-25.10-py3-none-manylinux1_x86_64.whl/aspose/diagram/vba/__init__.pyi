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

class VbaModule:
    
    @property
    def name(self) -> str:
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.diagram.vba.VbaModuleType:
        raise NotImplementedError()
    
    @property
    def codes(self) -> str:
        raise NotImplementedError()
    
    @codes.setter
    def codes(self, value : str) -> None:
        raise NotImplementedError()
    

class VbaModuleCollection:
    
    @overload
    def add(self, page : aspose.diagram.Page) -> int:
        raise NotImplementedError()
    
    @overload
    def add(self, type : aspose.diagram.vba.VbaModuleType, name : str) -> int:
        raise NotImplementedError()
    

class VbaProject:
    
    @property
    def name(self) -> str:
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def is_signed(self) -> bool:
        raise NotImplementedError()
    
    @property
    def modules(self) -> aspose.diagram.vba.VbaModuleCollection:
        raise NotImplementedError()
    
    @property
    def references(self) -> aspose.diagram.vba.VbaProjectReferenceCollection:
        raise NotImplementedError()
    

class VbaProjectReference:
    
    @property
    def type(self) -> aspose.diagram.vba.VbaProjectReferenceType:
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def libid(self) -> str:
        raise NotImplementedError()
    
    @libid.setter
    def libid(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def twiddledlibid(self) -> str:
        raise NotImplementedError()
    
    @twiddledlibid.setter
    def twiddledlibid(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def extended_libid(self) -> str:
        raise NotImplementedError()
    
    @extended_libid.setter
    def extended_libid(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def relative_libid(self) -> str:
        raise NotImplementedError()
    
    @relative_libid.setter
    def relative_libid(self, value : str) -> None:
        raise NotImplementedError()
    

class VbaProjectReferenceCollection:
    
    def add_registered_reference(self, name : str, libid : str) -> int:
        raise NotImplementedError()
    
    def add_control_refrernce(self, name : str, libid : str, twiddledlibid : str, extended_libid : str) -> int:
        raise NotImplementedError()
    
    def add_project_refrernce(self, name : str, absolute_libid : str, relative_libid : str) -> int:
        raise NotImplementedError()
    

class VbaModuleType:
    
    PROCEDURAL : VbaModuleType
    DOCUMENT : VbaModuleType
    CLASS : VbaModuleType
    DESIGNER : VbaModuleType

class VbaProjectReferenceType:
    
    REGISTERED : VbaProjectReferenceType
    CONTROL : VbaProjectReferenceType
    PROJECT : VbaProjectReferenceType

