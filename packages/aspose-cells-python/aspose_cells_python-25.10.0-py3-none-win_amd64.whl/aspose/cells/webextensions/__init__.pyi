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

class WebExtension:
    '''Represents an Office Add-in instance.'''
    
    @property
    def id(self) -> str:
        '''Gets and sets the uniquely identifies the Office Add-in instance in the current document.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : str) -> None:
        '''Gets and sets the uniquely identifies the Office Add-in instance in the current document.'''
        raise NotImplementedError()
    
    @property
    def is_frozen(self) -> bool:
        '''Indicates whether the user can interact with the Office Add-in or not.'''
        raise NotImplementedError()
    
    @is_frozen.setter
    def is_frozen(self, value : bool) -> None:
        '''Indicates whether the user can interact with the Office Add-in or not.'''
        raise NotImplementedError()
    
    @property
    def reference(self) -> aspose.cells.webextensions.WebExtensionReference:
        '''Get the primary reference to an Office Add-in.'''
        raise NotImplementedError()
    
    @property
    def alter_references(self) -> aspose.cells.webextensions.WebExtensionReferenceCollection:
        '''Gets a list of alter references.'''
        raise NotImplementedError()
    
    @property
    def properties(self) -> aspose.cells.webextensions.WebExtensionPropertyCollection:
        '''Gets all properties of web extension.'''
        raise NotImplementedError()
    
    @property
    def bindings(self) -> aspose.cells.webextensions.WebExtensionBindingCollection:
        '''Gets all bindings relationship between an Office Add-in and the data in the document.'''
        raise NotImplementedError()
    

class WebExtensionBinding:
    '''Represents a binding relationship between an Office Add-in and the data in the document.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def id(self) -> str:
        '''Gets and sets the binding identifier.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : str) -> None:
        '''Gets and sets the binding identifier.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> str:
        '''Gets and sets the binding type.'''
        raise NotImplementedError()
    
    @type.setter
    def type(self, value : str) -> None:
        '''Gets and sets the binding type.'''
        raise NotImplementedError()
    
    @property
    def appref(self) -> str:
        '''Gets and sets the binding key used to map the binding entry in this list with the bound data in the document.'''
        raise NotImplementedError()
    
    @appref.setter
    def appref(self, value : str) -> None:
        '''Gets and sets the binding key used to map the binding entry in this list with the bound data in the document.'''
        raise NotImplementedError()
    

class WebExtensionBindingCollection:
    '''Represents the list of binding relationships between an Office Add-in and the data in the document.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.webextensions.WebExtensionBinding]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.webextensions.WebExtensionBinding], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.webextensions.WebExtensionBinding, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.webextensions.WebExtensionBinding, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.webextensions.WebExtensionBinding) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.webextensions.WebExtensionBinding, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.webextensions.WebExtensionBinding, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add(self) -> int:
        '''Adds an a binding relationship between an Office Add-in and the data in the document.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.webextensions.WebExtensionBinding) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class WebExtensionCollection:
    '''Represents the list of web extension.'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.webextensions.WebExtension]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.webextensions.WebExtension], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.webextensions.WebExtension, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.webextensions.WebExtension, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.webextensions.WebExtension) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.webextensions.WebExtension, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.webextensions.WebExtension, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add(self) -> int:
        '''Adds a web extension.
        
        :returns: The index.'''
        raise NotImplementedError()
    
    def add_web_video_player(self, url : str, auto_play : bool, start_time : int, end_time : int) -> int:
        '''Add a web video player into exel.
        
        :param auto_play: Indicates whether auto playing the video.
        :param start_time: The start time in unit of seconds.
        :param end_time: The end time in unit of seconds.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.webextensions.WebExtension) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class WebExtensionProperty:
    '''Represents an Office Add-in custom property.'''
    
    @property
    def name(self) -> str:
        '''Gets and set a custom property name.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Gets and set a custom property name.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        '''Gets and sets a custom property value.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : str) -> None:
        '''Gets and sets a custom property value.'''
        raise NotImplementedError()
    

class WebExtensionPropertyCollection:
    '''Represents the list of web extension properties.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.webextensions.WebExtensionProperty]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.webextensions.WebExtensionProperty], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.webextensions.WebExtensionProperty, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.webextensions.WebExtensionProperty, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.webextensions.WebExtensionProperty) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.webextensions.WebExtensionProperty, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.webextensions.WebExtensionProperty, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def get(self, name : str) -> aspose.cells.webextensions.WebExtensionProperty:
        '''Gets the property of web extension.
        
        :param name: The name of property.
        :returns: The property of web extension.'''
        raise NotImplementedError()
    
    def add(self, name : str, value : str) -> int:
        '''Adds web extension property.
        
        :param name: The name of property.
        :param value: The value of property.
        :returns: The index of added property.'''
        raise NotImplementedError()
    
    def remove_at(self, name : str) -> None:
        '''Remove the property by the name.
        
        :param name: The name of the property.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.webextensions.WebExtensionProperty) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class WebExtensionReference:
    '''Represents identify the provider location and version of the extension.'''
    
    @property
    def id(self) -> str:
        '''Gets and sets the identifier associated with the Office Add-in within a catalog provider.
        The identifier MUST be unique within a catalog provider.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : str) -> None:
        '''Gets and sets the identifier associated with the Office Add-in within a catalog provider.
        The identifier MUST be unique within a catalog provider.'''
        raise NotImplementedError()
    
    @property
    def version(self) -> str:
        '''Gets and sets the version.'''
        raise NotImplementedError()
    
    @version.setter
    def version(self, value : str) -> None:
        '''Gets and sets the version.'''
        raise NotImplementedError()
    
    @property
    def store_name(self) -> str:
        '''Gets and sets the instance of the marketplace where the Office Add-in is stored. .'''
        raise NotImplementedError()
    
    @store_name.setter
    def store_name(self, value : str) -> None:
        '''Gets and sets the instance of the marketplace where the Office Add-in is stored. .'''
        raise NotImplementedError()
    
    @property
    def store_type(self) -> aspose.cells.webextensions.WebExtensionStoreType:
        '''Gets and sets the type of marketplace that the store attribute identifies.'''
        raise NotImplementedError()
    
    @store_type.setter
    def store_type(self, value : aspose.cells.webextensions.WebExtensionStoreType) -> None:
        '''Gets and sets the type of marketplace that the store attribute identifies.'''
        raise NotImplementedError()
    

class WebExtensionReferenceCollection:
    '''Represents the list of web extension reference.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.webextensions.WebExtensionReference]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.webextensions.WebExtensionReference], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.webextensions.WebExtensionReference, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.webextensions.WebExtensionReference, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.webextensions.WebExtensionReference) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.webextensions.WebExtensionReference, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.webextensions.WebExtensionReference, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add(self) -> int:
        '''Adds an empty reference of web extension.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.webextensions.WebExtensionReference) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class WebExtensionTaskPane:
    '''Represents a persisted taskpane object.'''
    
    @property
    def web_extension(self) -> aspose.cells.webextensions.WebExtension:
        '''Gets and sets the web extension part associated with the taskpane instance'''
        raise NotImplementedError()
    
    @web_extension.setter
    def web_extension(self, value : aspose.cells.webextensions.WebExtension) -> None:
        '''Gets and sets the web extension part associated with the taskpane instance'''
        raise NotImplementedError()
    
    @property
    def dock_state(self) -> str:
        '''Gets and sets the last-docked location of this taskpane object.'''
        raise NotImplementedError()
    
    @dock_state.setter
    def dock_state(self, value : str) -> None:
        '''Gets and sets the last-docked location of this taskpane object.'''
        raise NotImplementedError()
    
    @property
    def is_visible(self) -> bool:
        '''Indicates whether the Task Pane shows as visible by default when the document opens.'''
        raise NotImplementedError()
    
    @is_visible.setter
    def is_visible(self, value : bool) -> None:
        '''Indicates whether the Task Pane shows as visible by default when the document opens.'''
        raise NotImplementedError()
    
    @property
    def is_locked(self) -> bool:
        '''Indicates whether the taskpane is locked to the document in the UI and cannot be closed by the user.'''
        raise NotImplementedError()
    
    @is_locked.setter
    def is_locked(self, value : bool) -> None:
        '''Indicates whether the taskpane is locked to the document in the UI and cannot be closed by the user.'''
        raise NotImplementedError()
    
    @property
    def width(self) -> float:
        '''Gets and sets the default width value for this taskpane instance.'''
        raise NotImplementedError()
    
    @width.setter
    def width(self, value : float) -> None:
        '''Gets and sets the default width value for this taskpane instance.'''
        raise NotImplementedError()
    
    @property
    def row(self) -> int:
        '''Gets and sets the index, enumerating from the outside to the inside, of this taskpane among other persisted taskpanes docked in the same default location.'''
        raise NotImplementedError()
    
    @row.setter
    def row(self, value : int) -> None:
        '''Gets and sets the index, enumerating from the outside to the inside, of this taskpane among other persisted taskpanes docked in the same default location.'''
        raise NotImplementedError()
    

class WebExtensionTaskPaneCollection:
    '''Represents the list of task pane.'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.webextensions.WebExtensionTaskPane]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.webextensions.WebExtensionTaskPane], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.webextensions.WebExtensionTaskPane, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.webextensions.WebExtensionTaskPane, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.webextensions.WebExtensionTaskPane) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.webextensions.WebExtensionTaskPane, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.webextensions.WebExtensionTaskPane, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add(self) -> int:
        '''Adds task pane.
        
        :returns: The index.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.webextensions.WebExtensionTaskPane) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class WebExtensionStoreType:
    '''Represents the store type of web extension.'''
    
    OMEX : WebExtensionStoreType
    '''Specifies that the store type is Office.com.'''
    SP_CATALOG : WebExtensionStoreType
    '''Specifies that the store type is SharePoint corporate catalog.'''
    SP_APP : WebExtensionStoreType
    '''Specifies that the store type is a SharePoint web application.'''
    EXCHANGE : WebExtensionStoreType
    '''Specifies that the store type is an Exchange server.'''
    FILE_SYSTEM : WebExtensionStoreType
    '''Specifies that the store type is a file system share.'''
    REGISTRY : WebExtensionStoreType
    '''Specifies that the store type is the system registry.'''
    EX_CATALOG : WebExtensionStoreType
    '''Specifies that the store type is Centralized Deployment via Exchange.'''

