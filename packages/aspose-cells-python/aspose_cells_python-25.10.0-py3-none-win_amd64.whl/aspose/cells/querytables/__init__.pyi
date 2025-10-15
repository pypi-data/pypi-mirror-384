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

class DataMashup:
    '''Represents mashup data.'''
    
    @property
    def power_query_formulas(self) -> aspose.cells.querytables.PowerQueryFormulaCollection:
        '''Gets all power query formulas.'''
        raise NotImplementedError()
    
    @property
    def power_query_formula_parameters(self) -> aspose.cells.querytables.PowerQueryFormulaParameterCollection:
        '''Gets power query formula parameters.'''
        raise NotImplementedError()
    

class PowerQueryFormula:
    '''Represents the definition of power query formula.'''
    
    @property
    def type(self) -> aspose.cells.querytables.PowerQueryFormulaType:
        '''Gets the type of this power query formula.'''
        raise NotImplementedError()
    
    @property
    def group_name(self) -> str:
        '''Gets the name of group which contains this power query formula.'''
        raise NotImplementedError()
    
    @property
    def formula_definition(self) -> str:
        '''Gets the definition of the power query formula.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets and sets the name of the power query formula.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Gets and sets the name of the power query formula.'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''Gets and sets the description of the power query formula.'''
        raise NotImplementedError()
    
    @description.setter
    def description(self, value : str) -> None:
        '''Gets and sets the description of the power query formula.'''
        raise NotImplementedError()
    
    @property
    def power_query_formula_items(self) -> aspose.cells.querytables.PowerQueryFormulaItemCollection:
        '''Gets all items of power query formula.'''
        raise NotImplementedError()
    

class PowerQueryFormulaCollection:
    '''Represents all power query formulas in the mashup data.'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.querytables.PowerQueryFormula]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.querytables.PowerQueryFormula], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.querytables.PowerQueryFormula, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.querytables.PowerQueryFormula, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.querytables.PowerQueryFormula) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.querytables.PowerQueryFormula, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.querytables.PowerQueryFormula, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def get(self, name : str) -> aspose.cells.querytables.PowerQueryFormula:
        '''Gets :py:class:`aspose.cells.querytables.PowerQueryFormula` by the name of the power query formula.
        
        :param name: The name of the item.'''
        raise NotImplementedError()
    
    def remove_by(self, name : str) -> None:
        '''Remove power query formula by name.
        
        :param name: The name of power query formula.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.querytables.PowerQueryFormula) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class PowerQueryFormulaFunction(PowerQueryFormula):
    '''Represents the function of power query.'''
    
    @property
    def type(self) -> aspose.cells.querytables.PowerQueryFormulaType:
        '''Gets the type of power query formula.'''
        raise NotImplementedError()
    
    @property
    def group_name(self) -> str:
        '''Gets the name of group which contains this power query formula.'''
        raise NotImplementedError()
    
    @property
    def formula_definition(self) -> str:
        '''Gets the definition of the power query formula.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets and sets the name of the power query formula.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Gets and sets the name of the power query formula.'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''Gets and sets the description of the power query formula.'''
        raise NotImplementedError()
    
    @description.setter
    def description(self, value : str) -> None:
        '''Gets and sets the description of the power query formula.'''
        raise NotImplementedError()
    
    @property
    def power_query_formula_items(self) -> aspose.cells.querytables.PowerQueryFormulaItemCollection:
        '''Gets all items of power query formula.'''
        raise NotImplementedError()
    
    @property
    def f(self) -> str:
        '''Gets and sets the definition of function.'''
        raise NotImplementedError()
    
    @f.setter
    def f(self, value : str) -> None:
        '''Gets and sets the definition of function.'''
        raise NotImplementedError()
    

class PowerQueryFormulaItem:
    '''Represents the item of the power query formula.'''
    
    @property
    def name(self) -> str:
        '''Gets the name of the item.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        '''Gets the value of the item.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : str) -> None:
        '''Gets the value of the item.'''
        raise NotImplementedError()
    

class PowerQueryFormulaItemCollection:
    '''Represents all item of the power query formula.'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.querytables.PowerQueryFormulaItem]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.querytables.PowerQueryFormulaItem], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.querytables.PowerQueryFormulaItem, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.querytables.PowerQueryFormulaItem, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.querytables.PowerQueryFormulaItem) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.querytables.PowerQueryFormulaItem, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.querytables.PowerQueryFormulaItem, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def get(self, name : str) -> aspose.cells.querytables.PowerQueryFormulaItem:
        '''Gets :py:class:`aspose.cells.querytables.PowerQueryFormulaItem` by the name of the item.
        
        :param name: The name of the item.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.querytables.PowerQueryFormulaItem) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class PowerQueryFormulaParameter(PowerQueryFormula):
    '''Represents the parameter of power query formula.'''
    
    @property
    def type(self) -> aspose.cells.querytables.PowerQueryFormulaType:
        '''Gets the type of power query formula.'''
        raise NotImplementedError()
    
    @property
    def group_name(self) -> str:
        '''Gets the name of group which contains this power query formula.'''
        raise NotImplementedError()
    
    @property
    def formula_definition(self) -> str:
        '''Gets the definition of the parameter.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets and sets the name of the power query formula.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''Gets and sets the name of the power query formula.'''
        raise NotImplementedError()
    
    @property
    def description(self) -> str:
        '''Gets and sets the description of the power query formula.'''
        raise NotImplementedError()
    
    @description.setter
    def description(self, value : str) -> None:
        '''Gets and sets the description of the power query formula.'''
        raise NotImplementedError()
    
    @property
    def power_query_formula_items(self) -> aspose.cells.querytables.PowerQueryFormulaItemCollection:
        '''Gets all items of power query formula.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> str:
        '''Gets the value of parameter.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : str) -> None:
        '''Gets the value of parameter.'''
        raise NotImplementedError()
    
    @property
    def parameter_definition(self) -> str:
        '''Gets the definition of the parameter.'''
        raise NotImplementedError()
    

class PowerQueryFormulaParameterCollection:
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, array : List[aspose.cells.querytables.PowerQueryFormulaParameter]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.querytables.PowerQueryFormulaParameter], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.querytables.PowerQueryFormulaParameter, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.querytables.PowerQueryFormulaParameter, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.querytables.PowerQueryFormulaParameter) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.querytables.PowerQueryFormulaParameter, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.querytables.PowerQueryFormulaParameter, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def get(self, name : str) -> aspose.cells.querytables.PowerQueryFormulaParameter:
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.querytables.PowerQueryFormulaParameter) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class PowerQueryFormulaType:
    '''Represents the type of power query formula.'''
    
    FORMULA : PowerQueryFormulaType
    '''Formula power query formula.'''
    FUNCTION : PowerQueryFormulaType
    '''Function power query formula.'''
    PARAMETER : PowerQueryFormulaType
    '''Parameter power query formula.'''

