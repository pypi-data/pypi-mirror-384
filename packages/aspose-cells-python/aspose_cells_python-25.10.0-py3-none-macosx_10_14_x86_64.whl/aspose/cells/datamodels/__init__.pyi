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

class DataModel:
    '''Represents the data model.'''
    
    @property
    def relationships(self) -> aspose.cells.datamodels.DataModelRelationshipCollection:
        '''Gets all relationships of the tables in the data model.'''
        raise NotImplementedError()
    
    @property
    def tables(self) -> aspose.cells.datamodels.DataModelTableCollection:
        '''Gets all tables in the data model.'''
        raise NotImplementedError()
    

class DataModelRelationship:
    '''Represents a single relationship in the spreadsheet data model.'''
    
    @property
    def foreign_key_table(self) -> str:
        '''Gets the name of the foreign key table for this relationship.'''
        raise NotImplementedError()
    
    @property
    def primary_key_table(self) -> str:
        '''Gets the name of the primary key table for this relationship.'''
        raise NotImplementedError()
    
    @property
    def foreign_key_column(self) -> str:
        '''Gets the name of the foreign key table column for this relationship.'''
        raise NotImplementedError()
    
    @property
    def primary_key_column(self) -> str:
        '''Gets the name of the primary key table column for this relationship.'''
        raise NotImplementedError()
    

class DataModelRelationshipCollection:
    '''Represents the relationships.'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.datamodels.DataModelRelationship]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.datamodels.DataModelRelationship], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.datamodels.DataModelRelationship, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.datamodels.DataModelRelationship, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.datamodels.DataModelRelationship) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.datamodels.DataModelRelationship, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.datamodels.DataModelRelationship, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.datamodels.DataModelRelationship) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class DataModelTable:
    '''Represents properties of a single table in spreadsheet data model.'''
    
    @property
    def id(self) -> str:
        '''Gets the id of the data model table.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the name of the data model table.'''
        raise NotImplementedError()
    
    @property
    def connection_name(self) -> str:
        '''Gets the connection name of the data model table.'''
        raise NotImplementedError()
    

class DataModelTableCollection:
    '''Represents the list of the data model table.'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.datamodels.DataModelTable]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.datamodels.DataModelTable], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.datamodels.DataModelTable, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.datamodels.DataModelTable, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.datamodels.DataModelTable) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.datamodels.DataModelTable, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.datamodels.DataModelTable, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def get(self, name : str) -> aspose.cells.datamodels.DataModelTable:
        '''Gets the data model table by the name.
        
        :param name: The name of data model table.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.datamodels.DataModelTable) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

