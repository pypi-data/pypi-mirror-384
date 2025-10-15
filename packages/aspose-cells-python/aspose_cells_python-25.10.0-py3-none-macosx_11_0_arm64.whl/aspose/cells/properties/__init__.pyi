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

class BuiltInDocumentPropertyCollection(DocumentPropertyCollection):
    '''A collection of built-in document properties.'''
    
    @overload
    def get(self, name : int) -> aspose.cells.properties.DocumentProperty:
        '''Returns a :py:class:`aspose.cells.properties.DocumentProperty` object by the name of the property.
        
        :param name: The case-insensitive name of the property to retrieve.'''
        raise NotImplementedError()
    
    @overload
    def get(self, name : str) -> aspose.cells.properties.DocumentProperty:
        '''Returns a :py:class:`aspose.cells.properties.DocumentProperty` object by the name of the property.
        
        :param name: The case-insensitive name of the property to retrieve.'''
        raise NotImplementedError()
    
    @overload
    def index_of(self, name : str) -> int:
        '''Gets the index of a property by name.
        
        :param name: The case-insensitive name of the property.
        :returns: The zero based index. Negative value if not found.'''
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.properties.DocumentProperty, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.properties.DocumentProperty, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.properties.DocumentProperty]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.properties.DocumentProperty], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.properties.DocumentProperty) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.properties.DocumentProperty, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.properties.DocumentProperty, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.properties.DocumentProperty) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def language(self) -> str:
        '''Gets the document\'s language.'''
        raise NotImplementedError()
    
    @language.setter
    def language(self, value : str) -> None:
        '''Sets the document\'s language.'''
        raise NotImplementedError()
    
    @property
    def author(self) -> str:
        '''Gets the name of the document\'s author.'''
        raise NotImplementedError()
    
    @author.setter
    def author(self, value : str) -> None:
        '''Sets the name of the document\'s author.'''
        raise NotImplementedError()
    
    @property
    def bytes(self) -> int:
        '''Represents an estimate of the number of bytes in the document.'''
        raise NotImplementedError()
    
    @bytes.setter
    def bytes(self, value : int) -> None:
        '''Represents an estimate of the number of bytes in the document.'''
        raise NotImplementedError()
    
    @property
    def characters(self) -> int:
        '''Represents an estimate of the number of characters in the document.'''
        raise NotImplementedError()
    
    @characters.setter
    def characters(self, value : int) -> None:
        '''Represents an estimate of the number of characters in the document.'''
        raise NotImplementedError()
    
    @property
    def characters_with_spaces(self) -> int:
        '''Represents an estimate of the number of characters (including spaces) in the document.'''
        raise NotImplementedError()
    
    @characters_with_spaces.setter
    def characters_with_spaces(self, value : int) -> None:
        '''Represents an estimate of the number of characters (including spaces) in the document.'''
        raise NotImplementedError()
    
    @property
    def comments(self) -> str:
        '''Gets the document comments.'''
        raise NotImplementedError()
    
    @comments.setter
    def comments(self, value : str) -> None:
        '''Sets the document comments.'''
        raise NotImplementedError()
    
    @property
    def category(self) -> str:
        '''Gets the category of the document.'''
        raise NotImplementedError()
    
    @category.setter
    def category(self, value : str) -> None:
        '''Sets the category of the document.'''
        raise NotImplementedError()
    
    @property
    def content_type(self) -> str:
        '''Gets the content type of the document.'''
        raise NotImplementedError()
    
    @content_type.setter
    def content_type(self, value : str) -> None:
        '''Sets the content type of the document.'''
        raise NotImplementedError()
    
    @property
    def content_status(self) -> str:
        '''Gets the content status of the document.'''
        raise NotImplementedError()
    
    @content_status.setter
    def content_status(self, value : str) -> None:
        '''Sets the content status of the document.'''
        raise NotImplementedError()
    
    @property
    def company(self) -> str:
        '''Gets the company property.'''
        raise NotImplementedError()
    
    @company.setter
    def company(self, value : str) -> None:
        '''Sets the company property.'''
        raise NotImplementedError()
    
    @property
    def hyperlink_base(self) -> str:
        '''Gets the hyperlinkbase property.'''
        raise NotImplementedError()
    
    @hyperlink_base.setter
    def hyperlink_base(self, value : str) -> None:
        '''Sets the hyperlinkbase property.'''
        raise NotImplementedError()
    
    @property
    def created_time(self) -> datetime:
        '''Gets date of the document creation in local timezone.'''
        raise NotImplementedError()
    
    @created_time.setter
    def created_time(self, value : datetime) -> None:
        '''Sets date of the document creation in local timezone.'''
        raise NotImplementedError()
    
    @property
    def created_universal_time(self) -> datetime:
        '''Gets the Universal time of the document creation.'''
        raise NotImplementedError()
    
    @created_universal_time.setter
    def created_universal_time(self, value : datetime) -> None:
        '''Sets the Universal time of the document creation.'''
        raise NotImplementedError()
    
    @property
    def keywords(self) -> str:
        '''Gets the document keywords.'''
        raise NotImplementedError()
    
    @keywords.setter
    def keywords(self, value : str) -> None:
        '''Sets the document keywords.'''
        raise NotImplementedError()
    
    @property
    def last_printed(self) -> datetime:
        '''Gets the date when the document was last printed in local timezone.'''
        raise NotImplementedError()
    
    @last_printed.setter
    def last_printed(self, value : datetime) -> None:
        '''Sets the date when the document was last printed in local timezone.'''
        raise NotImplementedError()
    
    @property
    def last_printed_universal_time(self) -> datetime:
        '''Gets the Universal time when the document was last printed.'''
        raise NotImplementedError()
    
    @last_printed_universal_time.setter
    def last_printed_universal_time(self, value : datetime) -> None:
        '''Sets the Universal time when the document was last printed.'''
        raise NotImplementedError()
    
    @property
    def last_saved_by(self) -> str:
        '''Gets the name of the last author.'''
        raise NotImplementedError()
    
    @last_saved_by.setter
    def last_saved_by(self, value : str) -> None:
        '''Sets the name of the last author.'''
        raise NotImplementedError()
    
    @property
    def last_saved_time(self) -> datetime:
        '''Gets the time of the last save in local timezone.'''
        raise NotImplementedError()
    
    @last_saved_time.setter
    def last_saved_time(self, value : datetime) -> None:
        '''Sets the time of the last save in local timezone.'''
        raise NotImplementedError()
    
    @property
    def last_saved_universal_time(self) -> datetime:
        '''Gets the universal time of the last save.'''
        raise NotImplementedError()
    
    @last_saved_universal_time.setter
    def last_saved_universal_time(self, value : datetime) -> None:
        '''Sets the universal time of the last save.'''
        raise NotImplementedError()
    
    @property
    def lines(self) -> int:
        '''Represents an estimate of the number of lines in the document.'''
        raise NotImplementedError()
    
    @lines.setter
    def lines(self, value : int) -> None:
        '''Represents an estimate of the number of lines in the document.'''
        raise NotImplementedError()
    
    @property
    def manager(self) -> str:
        '''Gets the manager property.'''
        raise NotImplementedError()
    
    @manager.setter
    def manager(self, value : str) -> None:
        '''Sets the manager property.'''
        raise NotImplementedError()
    
    @property
    def name_of_application(self) -> str:
        '''Gets the name of the application.'''
        raise NotImplementedError()
    
    @name_of_application.setter
    def name_of_application(self, value : str) -> None:
        '''Sets the name of the application.'''
        raise NotImplementedError()
    
    @property
    def pages(self) -> int:
        '''Represents an estimate of the number of pages in the document.'''
        raise NotImplementedError()
    
    @pages.setter
    def pages(self, value : int) -> None:
        '''Represents an estimate of the number of pages in the document.'''
        raise NotImplementedError()
    
    @property
    def paragraphs(self) -> int:
        '''Represents an estimate of the number of paragraphs in the document.'''
        raise NotImplementedError()
    
    @paragraphs.setter
    def paragraphs(self, value : int) -> None:
        '''Represents an estimate of the number of paragraphs in the document.'''
        raise NotImplementedError()
    
    @property
    def revision_number(self) -> str:
        '''Gets the document revision number.'''
        raise NotImplementedError()
    
    @revision_number.setter
    def revision_number(self, value : str) -> None:
        '''Sets the document revision number.'''
        raise NotImplementedError()
    
    @property
    def subject(self) -> str:
        '''Gets the subject of the document.'''
        raise NotImplementedError()
    
    @subject.setter
    def subject(self, value : str) -> None:
        '''Sets the subject of the document.'''
        raise NotImplementedError()
    
    @property
    def template(self) -> str:
        '''Gets the informational name of the document template.'''
        raise NotImplementedError()
    
    @template.setter
    def template(self, value : str) -> None:
        '''Sets the informational name of the document template.'''
        raise NotImplementedError()
    
    @property
    def title(self) -> str:
        '''Gets the title of the document.'''
        raise NotImplementedError()
    
    @title.setter
    def title(self, value : str) -> None:
        '''Sets the title of the document.'''
        raise NotImplementedError()
    
    @property
    def total_editing_time(self) -> float:
        '''Gets the total editing time in minutes.'''
        raise NotImplementedError()
    
    @total_editing_time.setter
    def total_editing_time(self, value : float) -> None:
        '''Sets the total editing time in minutes.'''
        raise NotImplementedError()
    
    @property
    def version(self) -> str:
        '''Represents the version number of the application that created the document.'''
        raise NotImplementedError()
    
    @version.setter
    def version(self, value : str) -> None:
        '''Represents the version number of the application that created the document.'''
        raise NotImplementedError()
    
    @property
    def document_version(self) -> str:
        '''Represents the version of the file.'''
        raise NotImplementedError()
    
    @document_version.setter
    def document_version(self, value : str) -> None:
        '''Represents the version of the file.'''
        raise NotImplementedError()
    
    @property
    def scale_crop(self) -> bool:
        '''Indicates the display mode of the document thumbnail.'''
        raise NotImplementedError()
    
    @scale_crop.setter
    def scale_crop(self, value : bool) -> None:
        '''Indicates the display mode of the document thumbnail.'''
        raise NotImplementedError()
    
    @property
    def links_up_to_date(self) -> bool:
        '''Indicates whether hyperlinks in a document are up-to-date.'''
        raise NotImplementedError()
    
    @links_up_to_date.setter
    def links_up_to_date(self, value : bool) -> None:
        '''Indicates whether hyperlinks in a document are up-to-date.'''
        raise NotImplementedError()
    
    @property
    def words(self) -> int:
        '''Represents an estimate of the number of words in the document.'''
        raise NotImplementedError()
    
    @words.setter
    def words(self, value : int) -> None:
        '''Represents an estimate of the number of words in the document.'''
        raise NotImplementedError()
    

class ContentTypeProperty:
    '''Represents identifier information.'''
    
    @property
    def name(self) -> str:
        '''Returns the name of the object.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Returns or sets the name of the object.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        '''Returns the value of the content type property.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : str) -> None:
        '''Returns or sets the value of the content type property.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> str:
        '''Gets and sets the type of the property.'''
        raise NotImplementedError()
    
    @type.setter
    def type(self, value : str) -> None:
        '''Gets and sets the type of the property.'''
        raise NotImplementedError()
    
    @property
    def is_nillable(self) -> bool:
        '''Indicates whether the value could be empty.'''
        raise NotImplementedError()
    
    @is_nillable.setter
    def is_nillable(self, value : bool) -> None:
        '''Indicates whether the value could be empty.'''
        raise NotImplementedError()
    

class ContentTypePropertyCollection:
    '''A collection of :py:class:`aspose.cells.properties.ContentTypeProperty` objects that represent additional information.'''
    
    @overload
    def add(self, name : str, value : str) -> int:
        '''Adds content type property information.
        
        :param name: The name of the content type property.
        :param value: The value of the content type property.'''
        raise NotImplementedError()
    
    @overload
    def add(self, name : str, value : str, type : str) -> int:
        '''Adds content type property information.
        
        :param name: The name of the content type property.
        :param value: The value of the content type property.
        :param type: The type of the content type property.'''
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.properties.ContentTypeProperty]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.properties.ContentTypeProperty], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.properties.ContentTypeProperty, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.properties.ContentTypeProperty, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.properties.ContentTypeProperty) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.properties.ContentTypeProperty, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.properties.ContentTypeProperty, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def get(self, name : str) -> aspose.cells.properties.ContentTypeProperty:
        '''Gets the content type property by the property name.
        
        :param name: The property name.
        :returns: The content type property'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.properties.ContentTypeProperty) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class CustomDocumentPropertyCollection(DocumentPropertyCollection):
    '''A collection of custom document properties.'''
    
    @overload
    def get(self, name : str) -> aspose.cells.properties.DocumentProperty:
        '''Returns a :py:class:`aspose.cells.properties.DocumentProperty` object by the name of the property.
        
        :param name: The case-insensitive name of the property to retrieve.'''
        raise NotImplementedError()
    
    @overload
    def get(self, index : int) -> aspose.cells.properties.DocumentProperty:
        '''Returns a :py:class:`aspose.cells.properties.DocumentProperty` object by index.
        
        :param index: Zero-based index of the :py:class:`aspose.cells.properties.DocumentProperty` to retrieve.'''
        raise NotImplementedError()
    
    @overload
    def index_of(self, name : str) -> int:
        '''Gets the index of a property by name.
        
        :param name: The case-insensitive name of the property.
        :returns: The zero based index. Negative value if not found.'''
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.properties.DocumentProperty, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.properties.DocumentProperty, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.properties.DocumentProperty]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.properties.DocumentProperty], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.properties.DocumentProperty) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.properties.DocumentProperty, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.properties.DocumentProperty, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def add(self, name : str, value : str) -> aspose.cells.properties.DocumentProperty:
        '''Creates a new custom document property of the **PropertyType.String** data type.
        
        :param name: The name of the property.
        :param value: The value of the property.
        :returns: The newly created property object.'''
        raise NotImplementedError()
    
    @overload
    def add(self, name : str, value : int) -> aspose.cells.properties.DocumentProperty:
        '''Creates a new custom document property of the **PropertyType.Number** data type.
        
        :param name: The name of the property.
        :param value: The value of the property.
        :returns: The newly created property object.'''
        raise NotImplementedError()
    
    @overload
    def add(self, name : str, value : datetime) -> aspose.cells.properties.DocumentProperty:
        '''Creates a new custom document property of the **PropertyType.DateTime** data type.
        
        :param name: The name of the property.
        :param value: The value of the property.
        :returns: The newly created property object.'''
        raise NotImplementedError()
    
    @overload
    def add(self, name : str, value : bool) -> aspose.cells.properties.DocumentProperty:
        '''Creates a new custom document property of the **PropertyType.Boolean** data type.
        
        :param name: The name of the property.
        :param value: The value of the property.
        :returns: The newly created property object.'''
        raise NotImplementedError()
    
    @overload
    def add(self, name : str, value : float) -> aspose.cells.properties.DocumentProperty:
        '''Creates a new custom document property of the **PropertyType.Float** data type.
        
        :param name: The name of the property.
        :param value: The value of the property.
        :returns: The newly created property object.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.properties.DocumentProperty) -> int:
        raise NotImplementedError()
    
    def add_link_to_content(self, name : str, source : str) -> aspose.cells.properties.DocumentProperty:
        '''Creates a new custom document property which links to content.
        
        :param name: The name of the property.
        :param source: The source of the property. It should be the name of named range.
        :returns: The newly created property object.'''
        raise NotImplementedError()
    
    def update_linked_property_value(self) -> None:
        '''Updates values of all custom properties that are linked to content(use
        cell value of linked range to update value of custom property).'''
        raise NotImplementedError()
    
    def update_linked_range(self) -> None:
        '''Updates all ranges that are linked to custom properties(use the value of
        custom document property to update cell value of linked range).'''
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class CustomProperty:
    '''Represents identifier information.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Returns the name of the object.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Returns or sets the name of the object.'''
        raise NotImplementedError()
    
    @property
    def string_value(self) -> str:
        '''Returns the value of the custom property.'''
        raise NotImplementedError()
    
    @string_value.setter
    def string_value(self, value : str) -> None:
        '''Returns or sets the value of the custom property.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        '''Returns the value of the custom property.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : str) -> None:
        '''Returns or sets the value of the custom property.'''
        raise NotImplementedError()
    

class CustomPropertyCollection:
    '''A collection of :py:class:`aspose.cells.properties.CustomProperty` objects that represent additional information.'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.properties.CustomProperty]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.properties.CustomProperty], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.properties.CustomProperty, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.properties.CustomProperty, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.properties.CustomProperty) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.properties.CustomProperty, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.properties.CustomProperty, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def add(self, name : str, value : str) -> int:
        '''Adds custom property information.
        
        :param name: The name of the custom property.
        :param value: The value of the custom property.'''
        raise NotImplementedError()
    
    def get(self, name : str) -> aspose.cells.properties.CustomProperty:
        '''Gets the custom property by the property name.
        
        :param name: The property name.
        :returns: The custom property'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.properties.CustomProperty) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class DocumentProperty:
    '''Represents a custom or built-in document property.'''
    
    def to_int(self) -> int:
        '''Returns the property value as integer.'''
        raise NotImplementedError()
    
    def to_double(self) -> float:
        '''Returns the property value as double.'''
        raise NotImplementedError()
    
    def to_date_time(self) -> datetime:
        '''Returns the property value as DateTime in local timezone.'''
        raise NotImplementedError()
    
    def to_bool(self) -> bool:
        '''Returns the property value as bool.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Returns the name of the property.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> Any:
        '''Gets the value of the property.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : Any) -> None:
        '''Sets the value of the property.'''
        raise NotImplementedError()
    
    @property
    def is_linked_to_content(self) -> bool:
        '''Indicates whether this property is linked to content'''
        raise NotImplementedError()
    
    @property
    def source(self) -> str:
        '''The linked content source.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.properties.PropertyType:
        '''Gets the data type of the property.'''
        raise NotImplementedError()
    
    @property
    def is_generated_name(self) -> bool:
        '''Returns true if this property does not have a name in the OLE2 storage
        and a unique name was generated only for the public API.'''
        raise NotImplementedError()
    

class DocumentPropertyCollection:
    '''Base class for :py:class:`aspose.cells.properties.BuiltInDocumentPropertyCollection` and :py:class:`aspose.cells.properties.CustomDocumentPropertyCollection` collections.'''
    
    @overload
    def get(self, name : str) -> aspose.cells.properties.DocumentProperty:
        '''Returns a :py:class:`aspose.cells.properties.DocumentProperty` object by the name of the property.
        
        :param name: The case-insensitive name of the property to retrieve.'''
        raise NotImplementedError()
    
    @overload
    def get(self, index : int) -> aspose.cells.properties.DocumentProperty:
        '''Returns a :py:class:`aspose.cells.properties.DocumentProperty` object by index.
        
        :param index: Zero-based index of the :py:class:`aspose.cells.properties.DocumentProperty` to retrieve.'''
        raise NotImplementedError()
    
    @overload
    def index_of(self, name : str) -> int:
        '''Gets the index of a property by name.
        
        :param name: The case-insensitive name of the property.
        :returns: The zero based index. Negative value if not found.'''
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.properties.DocumentProperty, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.properties.DocumentProperty, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.properties.DocumentProperty]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.properties.DocumentProperty], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.properties.DocumentProperty) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.properties.DocumentProperty, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.properties.DocumentProperty, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.properties.DocumentProperty) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class PropertyType:
    '''Specifies data type of a document property.'''
    
    BOOLEAN : PropertyType
    '''The property is a boolean value.'''
    DATE_TIME : PropertyType
    '''The property is a date time value.'''
    DOUBLE : PropertyType
    '''The property is a floating number.'''
    NUMBER : PropertyType
    '''The property is an integer number.'''
    STRING : PropertyType
    '''The property is a string value.'''
    BLOB : PropertyType
    '''The property is a byte array.'''

