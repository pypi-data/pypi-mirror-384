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

class VbaModule:
    '''Represents the module in VBA project.'''
    
    @property
    def name(self) -> str:
        '''Gets and sets the name of Module.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Gets and sets the name of Module.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.vba.VbaModuleType:
        '''Gets the type of module.'''
        raise NotImplementedError()
    
    @property
    def binary_codes(self) -> List[int]:
        '''Gets and sets the binary codes of module.'''
        raise NotImplementedError()
    
    @property
    def codes(self) -> str:
        '''Gets and sets the codes of module.'''
        raise NotImplementedError()
    
    @codes.setter
    def codes(self, value : str) -> None:
        '''Gets and sets the codes of module.'''
        raise NotImplementedError()
    

class VbaModuleCollection:
    '''Represents the list of :py:class:`aspose.cells.vba.VbaModule`'''
    
    @overload
    def add(self, sheet : aspose.cells.Worksheet) -> int:
        '''Adds module for a worksheet.
        
        :param sheet: The worksheet'''
        raise NotImplementedError()
    
    @overload
    def add(self, type : aspose.cells.vba.VbaModuleType, name : str) -> int:
        '''Adds module.
        
        :param type: The type of module.
        :param name: The name of module.'''
        raise NotImplementedError()
    
    @overload
    def get(self, index : int) -> aspose.cells.vba.VbaModule:
        '''Gets :py:class:`aspose.cells.vba.VbaModule` in the list by the index.
        
        :param index: The index.'''
        raise NotImplementedError()
    
    @overload
    def get(self, name : str) -> aspose.cells.vba.VbaModule:
        '''Gets :py:class:`aspose.cells.vba.VbaModule` in the list by the name.
        
        :param name: The name of module.'''
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.vba.VbaModule]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.vba.VbaModule], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.vba.VbaModule, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.vba.VbaModule, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.vba.VbaModule) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.vba.VbaModule, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.vba.VbaModule, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add_designer_storage(self, name : str, data : List[int]) -> None:
        ''''''
        raise NotImplementedError()
    
    def get_designer_storage(self, name : str) -> List[int]:
        '''Represents the data of Designer.'''
        raise NotImplementedError()
    
    def add_user_form(self, name : str, codes : str, designer_storage : List[int]) -> int:
        '''Inser user form into VBA Project.
        
        :param name: The name of user form
        :param codes: The codes for the user form
        :param designer_storage: the designer setting about the user form'''
        raise NotImplementedError()
    
    def remove_by_worksheet(self, sheet : aspose.cells.Worksheet) -> None:
        '''Removes module for a worksheet.
        
        :param sheet: The worksheet'''
        raise NotImplementedError()
    
    def remove_by_name(self, name : str) -> None:
        '''Remove the module by the name'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.vba.VbaModule) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class VbaProject:
    '''Represents the VBA project.'''
    
    def sign(self, digital_signature : aspose.cells.digitalsignatures.DigitalSignature) -> None:
        '''Sign this VBA project by a DigitalSignature
        
        :param digital_signature: DigitalSignature'''
        raise NotImplementedError()
    
    def protect(self, islocked_for_viewing : bool, password : str) -> None:
        '''Protects or unprotects this VBA project.
        
        :param islocked_for_viewing: indicates whether locks project for viewing.
        :param password: If the value is null, unprotects this VBA project, otherwise projects the this VBA project.'''
        raise NotImplementedError()
    
    def copy(self, source : aspose.cells.vba.VbaProject) -> None:
        '''Copy VBA project from other file.'''
        raise NotImplementedError()
    
    def validate_password(self, password : str) -> bool:
        '''Validates protection password.
        
        :param password: the password
        :returns: Whether password is the protection password of this VBA project'''
        raise NotImplementedError()
    
    @property
    def is_valid_signed(self) -> bool:
        '''Indicates whether the signature of VBA project is valid or not.'''
        raise NotImplementedError()
    
    @property
    def cert_raw_data(self) -> List[int]:
        '''Gets certificate raw data if this VBA project is signed.'''
        raise NotImplementedError()
    
    @property
    def encoding(self) -> str:
        '''Gets and sets the encoding of VBA project.'''
        raise NotImplementedError()
    
    @encoding.setter
    def encoding(self, value : str) -> None:
        '''Gets and sets the encoding of VBA project.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets and sets the name of the VBA project.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Gets and sets the name of the VBA project.'''
        raise NotImplementedError()
    
    @property
    def is_signed(self) -> bool:
        '''Indicates whether VBAcode is signed or not.'''
        raise NotImplementedError()
    
    @property
    def is_protected(self) -> bool:
        '''Indicates whether this VBA project is protected.'''
        raise NotImplementedError()
    
    @property
    def islocked_for_viewing(self) -> bool:
        '''Indicates whether this VBA project is locked for viewing.'''
        raise NotImplementedError()
    
    @property
    def modules(self) -> aspose.cells.vba.VbaModuleCollection:
        '''Gets all :py:class:`aspose.cells.vba.VbaModule` objects.'''
        raise NotImplementedError()
    
    @property
    def references(self) -> aspose.cells.vba.VbaProjectReferenceCollection:
        '''Gets all references of VBA project.'''
        raise NotImplementedError()
    

class VbaProjectReference:
    '''Represents the reference of VBA project.'''
    
    def copy(self, source : aspose.cells.vba.VbaProjectReference) -> None:
        ''''''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.vba.VbaProjectReferenceType:
        '''Gets the type of this reference.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets and sets the name of the reference.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Gets and sets the name of the reference.'''
        raise NotImplementedError()
    
    @property
    def libid(self) -> str:
        '''Gets and sets the Libid of the reference.'''
        raise NotImplementedError()
    
    @libid.setter
    def libid(self, value : str) -> None:
        '''Gets and sets the Libid of the reference.'''
        raise NotImplementedError()
    
    @property
    def twiddledlibid(self) -> str:
        '''Gets and sets the twiddled Libid of the reference.'''
        raise NotImplementedError()
    
    @twiddledlibid.setter
    def twiddledlibid(self, value : str) -> None:
        '''Gets and sets the twiddled Libid of the reference.'''
        raise NotImplementedError()
    
    @property
    def extended_libid(self) -> str:
        '''Gets and sets the extended Libid of the reference.'''
        raise NotImplementedError()
    
    @extended_libid.setter
    def extended_libid(self, value : str) -> None:
        '''Gets and sets the extended Libid of the reference.'''
        raise NotImplementedError()
    
    @property
    def relative_libid(self) -> str:
        '''Gets and sets the referenced VBA project\'s identifier with an relative path.'''
        raise NotImplementedError()
    
    @relative_libid.setter
    def relative_libid(self, value : str) -> None:
        '''Gets and sets the referenced VBA project\'s identifier with an relative path.'''
        raise NotImplementedError()
    

class VbaProjectReferenceCollection:
    '''Represents all references of VBA project.'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.vba.VbaProjectReference]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.vba.VbaProjectReference], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.vba.VbaProjectReference, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.vba.VbaProjectReference, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.vba.VbaProjectReference) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.vba.VbaProjectReference, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.vba.VbaProjectReference, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add_registered_reference(self, name : str, libid : str) -> int:
        '''Add a reference to an Automation type library.
        
        :param name: The name of reference.
        :param libid: The identifier of an Automation type library.'''
        raise NotImplementedError()
    
    def add_control_refrernce(self, name : str, libid : str, twiddledlibid : str, extended_libid : str) -> int:
        '''Add a reference to a twiddled type library and its extended type library.
        
        :param name: The name of reference.
        :param libid: The identifier of an Automation type library.
        :param twiddledlibid: The identifier of a twiddled type library
        :param extended_libid: The identifier of an extended type library'''
        raise NotImplementedError()
    
    def add_project_refrernce(self, name : str, absolute_libid : str, relative_libid : str) -> int:
        '''Adds a reference to an external VBA project.
        
        :param name: The name of reference.
        :param absolute_libid: The referenced VBA project\'s identifier with an absolute path.
        :param relative_libid: The referenced VBA project\'s identifier with an relative path.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.vba.VbaProjectReference) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class VbaModuleType:
    '''Represents the type of VBA module.'''
    
    PROCEDURAL : VbaModuleType
    '''Represents a procedural module.'''
    DOCUMENT : VbaModuleType
    '''Represents a document module.'''
    CLASS : VbaModuleType
    '''Represents a class module.'''
    DESIGNER : VbaModuleType
    '''Represents a designer module.'''

class VbaProjectReferenceType:
    '''Represents the type of VBA project reference.'''
    
    REGISTERED : VbaProjectReferenceType
    '''Specifies a reference to an Automation type library.'''
    CONTROL : VbaProjectReferenceType
    '''Specifies a reference to a twiddled type library and its extended type library.'''
    PROJECT : VbaProjectReferenceType
    '''Specifies a reference to an external VBA project.'''

