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

class AccentEquationNode(EquationNode):
    '''This class specifies an accent equation, consisting of a base component and a combining diacritic.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    
    @property
    def accent_character(self) -> str:
        '''This attribute specifies the type of combining diacritical mark attached to the base of the accent function. The default accent character is U+0302.
        It is strongly recommended to use attribute AccentType to set accent character.
        Use this property setting if you cannot find the character you need in a known type.'''
        raise NotImplementedError()
    
    @accent_character.setter
    def accent_character(self, value : str) -> None:
        '''This attribute specifies the type of combining diacritical mark attached to the base of the accent function. The default accent character is U+0302.
        It is strongly recommended to use attribute AccentType to set accent character.
        Use this property setting if you cannot find the character you need in a known type.'''
        raise NotImplementedError()
    
    @property
    def accent_character_type(self) -> aspose.cells.drawing.equations.EquationCombiningCharacterType:
        '''Specify combining characters by type value.'''
        raise NotImplementedError()
    
    @accent_character_type.setter
    def accent_character_type(self, value : aspose.cells.drawing.equations.EquationCombiningCharacterType) -> None:
        '''Specify combining characters by type value.'''
        raise NotImplementedError()
    

class ArrayEquationNode(EquationNode):
    '''Specifies the Equation-Array function, an object consisting of one or more equations.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    

class BarEquationNode(EquationNode):
    '''This class specifies the bar equation, consisting of a base argument and an overbar or underbar.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    
    @property
    def bar_position(self) -> aspose.cells.drawing.equations.EquationCharacterPositionType:
        '''This attribute specifies the position of the bar in the bar object'''
        raise NotImplementedError()
    
    @bar_position.setter
    def bar_position(self, value : aspose.cells.drawing.equations.EquationCharacterPositionType) -> None:
        '''This attribute specifies the position of the bar in the bar object'''
        raise NotImplementedError()
    

class BorderBoxEquationNode(EquationNode):
    '''This class specifies the Border Box function, consisting of a border drawn around an equation.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    

class BoxEquationNode(EquationNode):
    '''This class specifies the box function, which is used to group components of an equation.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    

class DelimiterEquationNode(EquationNode):
    '''This class specifies the delimiter equation, consisting of opening and closing delimiters (such as parentheses, braces, brackets, and vertical bars), and a component contained inside.
    The delimiter may have more than one component, with a designated separator character between each component.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    
    @property
    def begin_char(self) -> str:
        '''Delimiter beginning character.'''
        raise NotImplementedError()
    
    @begin_char.setter
    def begin_char(self, value : str) -> None:
        '''Delimiter beginning character.'''
        raise NotImplementedError()
    
    @property
    def end_char(self) -> str:
        '''Delimiter ending character.'''
        raise NotImplementedError()
    
    @end_char.setter
    def end_char(self, value : str) -> None:
        '''Delimiter ending character.'''
        raise NotImplementedError()
    
    @property
    def nary_grow(self) -> bool:
        raise NotImplementedError()
    
    @nary_grow.setter
    def nary_grow(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def separator_char(self) -> str:
        '''Delimiter separator character.'''
        raise NotImplementedError()
    
    @separator_char.setter
    def separator_char(self, value : str) -> None:
        '''Delimiter separator character.'''
        raise NotImplementedError()
    
    @property
    def delimiter_shape(self) -> aspose.cells.drawing.equations.EquationDelimiterShapeType:
        '''Specifies the shape of delimiters in the delimiter object.'''
        raise NotImplementedError()
    
    @delimiter_shape.setter
    def delimiter_shape(self, value : aspose.cells.drawing.equations.EquationDelimiterShapeType) -> None:
        '''Specifies the shape of delimiters in the delimiter object.'''
        raise NotImplementedError()
    

class EquationComponentNode(EquationNode):
    '''This class specifies the components of an equation or mathematical expression.
    Different types of components combined into different equations.
    For example, a fraction consists of two parts, a numerator component and a denominator component.
    For more component types, please refer to \'EquationNodeType\'.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    

class EquationNode(aspose.cells.FontSetting):
    '''Abstract class for deriving other equation nodes.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    

class EquationNodeParagraph(EquationNode):
    '''This class specifies a mathematical paragraph containing one or more MathEquationNode(OMath) elements.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    
    @property
    def justification(self) -> aspose.cells.drawing.equations.EquationHorizontalJustificationType:
        '''This specifies justification of the math paragraph (a series of adjacent equations within the same paragraph). A math paragraph can be Left Justified, Right Justified, Centered, or Centered as Group. By default, the math paragraph is Centered as Group. This means that the equations can be aligned with respect to each other, but the entire group of equations is centered as a whole.'''
        raise NotImplementedError()
    
    @justification.setter
    def justification(self, value : aspose.cells.drawing.equations.EquationHorizontalJustificationType) -> None:
        '''This specifies justification of the math paragraph (a series of adjacent equations within the same paragraph). A math paragraph can be Left Justified, Right Justified, Centered, or Centered as Group. By default, the math paragraph is Centered as Group. This means that the equations can be aligned with respect to each other, but the entire group of equations is centered as a whole.'''
        raise NotImplementedError()
    

class FractionEquationNode(EquationNode):
    '''This class  specifies the fraction equation, consisting of a numerator and denominator separated by a fraction bar. The fraction bar can be horizontal or diagonal, depending on the fraction properties. The fraction equation is also used to represent the stack function, which places one element above another, with no fraction bar.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    
    @property
    def fraction_type(self) -> aspose.cells.drawing.equations.EquationFractionType:
        '''This specifies the type of fraction ; the default is \'Bar\'.'''
        raise NotImplementedError()
    
    @fraction_type.setter
    def fraction_type(self, value : aspose.cells.drawing.equations.EquationFractionType) -> None:
        '''This specifies the type of fraction ; the default is \'Bar\'.'''
        raise NotImplementedError()
    

class FunctionEquationNode(EquationNode):
    '''This class specifies the Function-Apply equation, which consists of a function name and an argument acted upon.
    The types of the name and argument components are \'EquationNodeType.FunctionName\' and \'EquationNodeType.Base\' respectively.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    

class GroupCharacterEquationNode(EquationNode):
    '''This class specifies the Group-Character function, consisting of a character drawn above or below text, often with the purpose of visually grouping items.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    
    @property
    def group_chr(self) -> str:
        '''Specifies a symbol(default U+23DF).
        It is strongly recommended to use attribute ChrType to set accent character.
        Use this property setting if you cannot find the character you need in a known type.'''
        raise NotImplementedError()
    
    @group_chr.setter
    def group_chr(self, value : str) -> None:
        '''Specifies a symbol(default U+23DF).
        It is strongly recommended to use attribute ChrType to set accent character.
        Use this property setting if you cannot find the character you need in a known type.'''
        raise NotImplementedError()
    
    @property
    def chr_type(self) -> aspose.cells.drawing.equations.EquationCombiningCharacterType:
        '''Specify combining characters by type value.'''
        raise NotImplementedError()
    
    @chr_type.setter
    def chr_type(self, value : aspose.cells.drawing.equations.EquationCombiningCharacterType) -> None:
        '''Specify combining characters by type value.'''
        raise NotImplementedError()
    
    @property
    def position(self) -> aspose.cells.drawing.equations.EquationCharacterPositionType:
        '''This attribute specifies the position of the character in the object'''
        raise NotImplementedError()
    
    @position.setter
    def position(self, value : aspose.cells.drawing.equations.EquationCharacterPositionType) -> None:
        '''This attribute specifies the position of the character in the object'''
        raise NotImplementedError()
    
    @property
    def vert_jc(self) -> aspose.cells.drawing.equations.EquationCharacterPositionType:
        '''This attribute, combined with pos of groupChrPr, specifies the vertical layout of the groupChr object. Where pos specifies the position of the grouping character, vertJc specifies the alignment of the object with respect to the baseline.'''
        raise NotImplementedError()
    
    @vert_jc.setter
    def vert_jc(self, value : aspose.cells.drawing.equations.EquationCharacterPositionType) -> None:
        '''This attribute, combined with pos of groupChrPr, specifies the vertical layout of the groupChr object. Where pos specifies the position of the grouping character, vertJc specifies the alignment of the object with respect to the baseline.'''
        raise NotImplementedError()
    

class LimLowUppEquationNode(EquationNode):
    '''This class specifies the limit function.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    

class MathematicalEquationNode(EquationNode):
    '''This class specifies an equation or mathematical expression. All mathematical text of equations or mathematical expressions are contained by this class.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    

class MatrixEquationNode(EquationNode):
    '''This class specifies the Matrix equation, consisting of one or more elements laid out in one or more rows and one or more columns.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    
    @property
    def base_jc(self) -> aspose.cells.drawing.equations.EquationVerticalJustificationType:
        '''This attribute specifies the justification of the matrix. Text outside of the matrix can be aligned with the bottom, top, or center of a matrix function. Default, the matrix assumes center justification.'''
        raise NotImplementedError()
    
    @base_jc.setter
    def base_jc(self, value : aspose.cells.drawing.equations.EquationVerticalJustificationType) -> None:
        '''This attribute specifies the justification of the matrix. Text outside of the matrix can be aligned with the bottom, top, or center of a matrix function. Default, the matrix assumes center justification.'''
        raise NotImplementedError()
    
    @property
    def is_hide_placeholder(self) -> bool:
        '''This attribute specifies the Hide Placeholders property on a matrix. When this property is on, placeholders do not appear in the matrix.Default, placeholders do appear such that the locations where text can be inserted are made visible.'''
        raise NotImplementedError()
    
    @is_hide_placeholder.setter
    def is_hide_placeholder(self, value : bool) -> None:
        '''This attribute specifies the Hide Placeholders property on a matrix. When this property is on, placeholders do not appear in the matrix.Default, placeholders do appear such that the locations where text can be inserted are made visible.'''
        raise NotImplementedError()
    

class NaryEquationNode(EquationNode):
    '''This class specifies an n-ary operator equation consisting of an n-ary operator, a base (or operand), and optional upper and lower bounds.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    
    @property
    def is_hide_subscript(self) -> bool:
        '''Whether to display the lower bound'''
        raise NotImplementedError()
    
    @is_hide_subscript.setter
    def is_hide_subscript(self, value : bool) -> None:
        '''Whether to display the lower bound'''
        raise NotImplementedError()
    
    @property
    def is_hide_superscript(self) -> bool:
        '''Whether to display the upper bound'''
        raise NotImplementedError()
    
    @is_hide_superscript.setter
    def is_hide_superscript(self, value : bool) -> None:
        '''Whether to display the upper bound'''
        raise NotImplementedError()
    
    @property
    def limit_location(self) -> aspose.cells.drawing.equations.EquationLimitLocationType:
        '''This attribute specifies the location of limits in n-ary operators. Limits can be either centered above and below the n-ary operator, or positioned just to the right of the operator.'''
        raise NotImplementedError()
    
    @limit_location.setter
    def limit_location(self, value : aspose.cells.drawing.equations.EquationLimitLocationType) -> None:
        '''This attribute specifies the location of limits in n-ary operators. Limits can be either centered above and below the n-ary operator, or positioned just to the right of the operator.'''
        raise NotImplementedError()
    
    @property
    def nary_operator(self) -> str:
        '''an n-ary operator.e.g "∑".
        It is strongly recommended to use attribute NaryOperatorType to set n-ary operator.
        Use this property setting if you cannot find the character you need in a known type.'''
        raise NotImplementedError()
    
    @nary_operator.setter
    def nary_operator(self, value : str) -> None:
        '''an n-ary operator.e.g "∑".
        It is strongly recommended to use attribute NaryOperatorType to set n-ary operator.
        Use this property setting if you cannot find the character you need in a known type.'''
        raise NotImplementedError()
    
    @property
    def nary_operator_type(self) -> aspose.cells.drawing.equations.EquationMathematicalOperatorType:
        '''an n-ary operator.e.g "∑"'''
        raise NotImplementedError()
    
    @nary_operator_type.setter
    def nary_operator_type(self, value : aspose.cells.drawing.equations.EquationMathematicalOperatorType) -> None:
        '''an n-ary operator.e.g "∑"'''
        raise NotImplementedError()
    
    @property
    def nary_grow(self) -> bool:
        '''This attribute specifies the growth property of n-ary operators at the document level. When off, n-ary operators such as integrals and summations do not grow to match the size of their operand height. When on, the n-ary operator grows vertically to match its operand height.'''
        raise NotImplementedError()
    
    @nary_grow.setter
    def nary_grow(self, value : bool) -> None:
        '''This attribute specifies the growth property of n-ary operators at the document level. When off, n-ary operators such as integrals and summations do not grow to match the size of their operand height. When on, the n-ary operator grows vertically to match its operand height.'''
        raise NotImplementedError()
    

class RadicalEquationNode(EquationNode):
    '''This class specifies the radical equation, consisting of an optional degree deg(EquationNodeType.Degree) and a base.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    
    @property
    def is_deg_hide(self) -> bool:
        '''Whether to hide the degree of radicals.'''
        raise NotImplementedError()
    
    @is_deg_hide.setter
    def is_deg_hide(self, value : bool) -> None:
        '''Whether to hide the degree of radicals.'''
        raise NotImplementedError()
    

class SubSupEquationNode(EquationNode):
    '''This class specifies an equation that can optionally be superscript or subscript.
    There are four main forms of this equation, superscript，subscript，superscript and subscript placed to the left of the base, superscript and subscript placed to the right of the base.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    

class TextRunEquationNode(EquationNode):
    '''This class in the equation node is used to store the actual content(a sequence of mathematical text) of the equation.
    Usually a node object per character.'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    
    @property
    def text(self) -> str:
        '''Set the content of the text node(Usually a node object per character).'''
        raise NotImplementedError()
    
    @text.setter
    def text(self, value : str) -> None:
        '''Set the content of the text node(Usually a node object per character).'''
        raise NotImplementedError()
    

class UnknowEquationNode(EquationNode):
    '''Equation node class of unknown type'''
    
    @overload
    def add_child(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Insert a node of the specified type at the end of the child node list of the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @overload
    def add_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Inserts the specified node at the end of the current node\'s list of child nodes.
        
        :param node: The specified node'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, node : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Removes the specified node from the current node\'s children.
        
        :param node: Node to be deleted.'''
        raise NotImplementedError()
    
    @overload
    def remove_child(self, index : int) -> None:
        '''Removes the node at the specified index from the current node\'s children.
        
        :param index: Index of the node'''
        raise NotImplementedError()
    
    def set_word_art_style(self, style : aspose.cells.drawing.PresetWordArtStyle) -> None:
        '''Sets the preset WordArt style.
        
        :param style: The preset WordArt style.'''
        raise NotImplementedError()
    
    def to_la_te_x(self) -> str:
        '''Convert this equtation to LaTeX expression.'''
        raise NotImplementedError()
    
    def to_math_ml(self) -> str:
        '''Convert this equtation to MathML expression.'''
        raise NotImplementedError()
    
    def insert_child(self, index : int, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts a node of the specified type at the specified index position in the current node\'s child node list.
        
        :param index: index value
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_after(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node after the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def insert_before(self, equation_type : aspose.cells.drawing.equations.EquationNodeType) -> aspose.cells.drawing.equations.EquationNode:
        '''Inserts the specified node before the current node.
        
        :param equation_type: Types of Equation Nodes
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    def get_child(self, index : int) -> aspose.cells.drawing.equations.EquationNode:
        '''Returns the node at the specified index among the children of the current node.
        
        :param index: Index of the node
        :returns: Returns the corresponding node if the specified node exists, otherwise returns null.'''
        raise NotImplementedError()
    
    def remove(self) -> None:
        '''Removes itself from the parent.'''
        raise NotImplementedError()
    
    def remove_all_children(self) -> None:
        '''Removes all the child nodes of the current node.'''
        raise NotImplementedError()
    
    @staticmethod
    def create_node(equation_type : aspose.cells.drawing.equations.EquationNodeType, workbook : aspose.cells.Workbook, parent : aspose.cells.drawing.equations.EquationNode) -> aspose.cells.drawing.equations.EquationNode:
        '''Create a node of the specified type.
        
        :param equation_type: Types of Equation Nodes
        :param workbook: The workbook object associated with the equation
        :param parent: The parent node where this node is located
        :returns: If the specified type exists, the corresponding node is returned, and if the type does not exist, a node of unknown type is returned.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.drawing.texts.TextNodeType:
        '''Represents the type of the node.'''
        raise NotImplementedError()
    
    @property
    def start_index(self) -> int:
        '''Gets the start index of the characters.'''
        raise NotImplementedError()
    
    @property
    def length(self) -> int:
        '''Gets the length of the characters.'''
        raise NotImplementedError()
    
    @property
    def font(self) -> aspose.cells.Font:
        '''Returns the font of this object.'''
        raise NotImplementedError()
    
    @property
    def text_options(self) -> aspose.cells.drawing.texts.TextOptions:
        '''Returns the text options.'''
        raise NotImplementedError()
    
    @property
    def parent_node(self) -> aspose.cells.drawing.equations.EquationNode:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @parent_node.setter
    def parent_node(self, value : aspose.cells.drawing.equations.EquationNode) -> None:
        '''Specifies the parent node of the current node'''
        raise NotImplementedError()
    
    @property
    def equation_type(self) -> aspose.cells.drawing.equations.EquationNodeType:
        '''Get the equation type of the current node'''
        raise NotImplementedError()
    

class EquationCharacterPositionType:
    '''Specifies the position of a particular subobject within its parent'''
    
    TOP : EquationCharacterPositionType
    '''At the top of the parent object'''
    BOTTOM : EquationCharacterPositionType
    '''At the bottom of the parent object'''

class EquationCombiningCharacterType:
    '''Type of combining characters.'''
    
    UNKNOWN : EquationCombiningCharacterType
    '''Use unknown type when not found in existing type.'''
    DOT_ABOVE : EquationCombiningCharacterType
    '''"̇" Unicode: u0307
    Combining Dot Above'''
    DIAERESIS : EquationCombiningCharacterType
    '''"̈" Unicode: u0308
    Combining Diaeresis'''
    THREE_DOTS_ABOVE : EquationCombiningCharacterType
    '''"⃛" Unicode: u20db
    Combining Three Dots Above'''
    CIRCUMFLEX_ACCENT : EquationCombiningCharacterType
    '''"̂" Unicode: u0302
    Combining Circumflex Accent'''
    CARON : EquationCombiningCharacterType
    '''"̌" Unicode: u030c
    Combining Caron'''
    ACUTE_ACCENT : EquationCombiningCharacterType
    '''"́" Unicode: u0301
    Combining Acute Accent'''
    GRAVE_ACCENT : EquationCombiningCharacterType
    '''"̀" Unicode: u0300
    Combining Grave Accent'''
    BREVE : EquationCombiningCharacterType
    '''"̆" Unicode: u0306
    Combining Combining Breve'''
    TILDE : EquationCombiningCharacterType
    '''"̃" Unicode: u0303
    Combining Tilde'''
    OVERLINE : EquationCombiningCharacterType
    '''"̅" Unicode: u0305
    Combining Overline'''
    DOUBLE_OVERLINE : EquationCombiningCharacterType
    '''"̿" Unicode: u033f
    Combining Double Overline'''
    TOP_CURLY_BRACKET : EquationCombiningCharacterType
    '''"⏞" Unicode: u23de
    Combining Top Curly Bracket'''
    BOTTOM_CURLY_BRACKET : EquationCombiningCharacterType
    '''"⏟" Unicode: u23df
    Combining Bottom Curly Bracket'''
    LEFT_ARROW_ABOVE : EquationCombiningCharacterType
    '''"⃖" Unicode: u20d6
    Combining Left Arrow Above'''
    RIGHT_ARROW_ABOVE : EquationCombiningCharacterType
    '''"⃗" Unicode: u20d7
    Combining Right Arrow Above'''
    LEFT_RIGHT_ARROW_ABOVE : EquationCombiningCharacterType
    '''"⃡" Unicode: u20e1
    Combining Left Right Arrow Above'''
    LEFT_HARPOON_ABOVE : EquationCombiningCharacterType
    '''"⃐" Unicode: u20d0
    Combining Left Harpoon Above'''
    RIGHT_HARPOON_ABOVE : EquationCombiningCharacterType
    '''"⃑" Unicode: u20d1
    Combining Right Harpoon Above'''
    LEFTWARDS_ARROW : EquationCombiningCharacterType
    '''"←" Unicode: u2190
    Leftwards Arrow'''
    RIGHTWARDS_ARROW : EquationCombiningCharacterType
    '''"→" Unicode: u2192
    Rightwards Arrow'''
    LEFT_RIGHT_ARROW : EquationCombiningCharacterType
    '''"↔" Unicode: u2194
    Left Right Arrow'''
    LEFTWARDS_DOUBLE_ARROW : EquationCombiningCharacterType
    '''"⇐" Unicode: u21d0
    Leftwards Double Arrow'''
    RIGHTWARDS_DOUBLE_ARROW : EquationCombiningCharacterType
    '''"⇒" Unicode: u21d2
    Rightwards Double Arrow'''
    LEFT_RIGHT_DOUBLE_ARROW : EquationCombiningCharacterType
    '''"⇔" Unicode: u21d4
    Left Right Double Arrow'''

class EquationDelimiterShapeType:
    '''This specifies the shape of delimiters in the delimiter object.'''
    
    CENTERED : EquationDelimiterShapeType
    '''The divider is centered around the entire height of its content.'''
    MATCH : EquationDelimiterShapeType
    '''The divider is altered to exactly match their contents\' height.'''

class EquationFractionType:
    '''This specifies the display style of the fraction bar.'''
    
    BAR : EquationFractionType
    '''This specifies that the numerator is above and the denominator below is separated by a bar in the middle.'''
    NO_BAR : EquationFractionType
    '''This specifies that the numerator is above and the denominator below is not separated by a bar in the middle.'''
    LINEAR : EquationFractionType
    '''This specifies that the numerator is on the left and the denominator is on the right, separated by a \'/\' in between.'''
    SKEWED : EquationFractionType
    '''This specifies that the numerator is on the upper left and the denominator is on the lower right, separated by a "/".'''

class EquationHorizontalJustificationType:
    '''This specifies the default horizontal justification of equations in the document.'''
    
    CENTER : EquationHorizontalJustificationType
    '''Centered'''
    CENTER_GROUP : EquationHorizontalJustificationType
    '''Centered as Group'''
    LEFT : EquationHorizontalJustificationType
    '''Left Justified'''
    RIGHT : EquationHorizontalJustificationType
    '''Right Justified'''

class EquationLimitLocationType:
    '''Specifies the limit location on an operator.'''
    
    UND_OVR : EquationLimitLocationType
    '''Specifies that the limit is centered above or below the operator.'''
    SUB_SUP : EquationLimitLocationType
    '''Specifies that the limit is on the right side of the operator.'''

class EquationMathematicalOperatorType:
    '''Mathematical Operators Type'''
    
    UNKNOWN : EquationMathematicalOperatorType
    '''Use unknown type when not found in existing type.'''
    FOR_ALL : EquationMathematicalOperatorType
    '''"∀" Unicode:\u2200'''
    COMPLEMENT : EquationMathematicalOperatorType
    '''"∁" Unicode:\u2201'''
    PARTIAL_DIFFERENTIAL : EquationMathematicalOperatorType
    '''"∂" Unicode:\u2202'''
    EXISTS : EquationMathematicalOperatorType
    '''"∃" Unicode:\u2203'''
    NOT_EXISTS : EquationMathematicalOperatorType
    '''"∄" Unicode:\u2204'''
    EMPTY_SET : EquationMathematicalOperatorType
    '''"∅" Unicode:\u2205'''
    INCREMENT : EquationMathematicalOperatorType
    '''"∆" Unicode:\u2206'''
    NABLA : EquationMathematicalOperatorType
    '''"∇" Unicode:\u2207'''
    ELEMENT_OF : EquationMathematicalOperatorType
    '''"∈" Unicode:\u2208'''
    NOT_AN_ELEMENT_OF : EquationMathematicalOperatorType
    '''"∉" Unicode:\u2209'''
    SMALL_ELEMENT_OF : EquationMathematicalOperatorType
    '''"∊" Unicode:\u220a'''
    CONTAIN : EquationMathematicalOperatorType
    '''"∋" Unicode:\u220b'''
    NOT_CONTAIN : EquationMathematicalOperatorType
    '''"∌" Unicode:\u220c'''
    SMALL_CONTAIN : EquationMathematicalOperatorType
    '''"∍" Unicode:\u220d'''
    END_OF_PROOF : EquationMathematicalOperatorType
    '''"∎" Unicode:\u220e'''
    NARY_PRODUCT : EquationMathematicalOperatorType
    '''"∏" Unicode:\u220f'''
    NARY_COPRODUCT : EquationMathematicalOperatorType
    '''"∐" Unicode:\u2210'''
    NARY_SUMMATION : EquationMathematicalOperatorType
    '''"∑" Unicode:\u2211'''
    LOGICAL_AND : EquationMathematicalOperatorType
    '''"∧" Unicode:\u2227'''
    LOGICAL_OR : EquationMathematicalOperatorType
    '''"∨" Unicode:\u2228'''
    INTERSECTION : EquationMathematicalOperatorType
    '''"∩" Unicode:\u2229'''
    UNION : EquationMathematicalOperatorType
    '''"∪" Unicode:\u222a'''
    INTEGRAL : EquationMathematicalOperatorType
    '''"∫" Unicode:\u222b'''
    DOUBLE_INTEGRAL : EquationMathematicalOperatorType
    '''"∬" Unicode:\u222c'''
    TRIPLE_INTEGRAL : EquationMathematicalOperatorType
    '''"∭" Unicode:\u222d'''
    CONTOUR_INTEGRAL : EquationMathematicalOperatorType
    '''"∮" Unicode:\u222e'''
    SURFACE_INTEGRAL : EquationMathematicalOperatorType
    '''"∯" Unicode:\u222f'''
    VOLUME_INTEGRAL : EquationMathematicalOperatorType
    '''"∰" Unicode:\u2230'''
    CLOCKWISE : EquationMathematicalOperatorType
    '''"∱" Unicode:\u2231'''
    CLOCKWISE_CONTOUR_INTEGRAL : EquationMathematicalOperatorType
    '''"∲" Unicode:\u2232'''
    ANTICLOCKWISE_CONTOUR_INTEGRAL : EquationMathematicalOperatorType
    '''"∳" Unicode:\u2233'''
    NARY_LOGICAL_AND : EquationMathematicalOperatorType
    '''"⋀" Unicode:\u22c0'''
    NARY_LOGICAL_OR : EquationMathematicalOperatorType
    '''"⋁" Unicode:\u22c1'''
    NARY_INTERSECTION : EquationMathematicalOperatorType
    '''"⋂" Unicode:\u22c2'''
    NARY_UNION : EquationMathematicalOperatorType
    '''"⋃" Unicode:\u22c3'''

class EquationNodeType:
    '''Equation node type.
    Notice:
    (1)[1-99] Currently there is only one node in the scope, and its enumeration value is 1. The node it specifies is used to store mathematical text.
    (2)[100-199] Indicates that the node is a component of some special function nodes.
    (3)[200-] Indicates that the node has some special functions.'''
    
    UN_KNOW : EquationNodeType
    '''UnKnow'''
    TEXT : EquationNodeType
    '''specifies a node that stores math text'''
    BASE : EquationNodeType
    '''Specifies a Base component'''
    DENOMINATOR : EquationNodeType
    '''Specifies a Denominator component'''
    NUMERATOR : EquationNodeType
    '''Specifies a Numerator component'''
    FUNCTION_NAME : EquationNodeType
    '''Specifies a FunctionName component'''
    SUBSCRIPT : EquationNodeType
    '''Specifies a Subscript component'''
    SUPERSCRIPT : EquationNodeType
    '''Specifies a Superscript component'''
    DEGREE : EquationNodeType
    '''Specifies a Degree component'''
    MATRIX_ROW : EquationNodeType
    '''Specifies a MatrixRow component.A single row of the matrix'''
    LIMIT : EquationNodeType
    '''Represents a sub-object of Lower-Limit function or Upper-Limit function'''
    EQUATION_PARAGRAPH : EquationNodeType
    '''Specifies a mathematical paragraph(oMathPara).'''
    MATHEMATICAL_EQUATION : EquationNodeType
    '''Specifies an equation or mathematical expression(OMath).'''
    FRACTION_EQUATION : EquationNodeType
    '''Specifies fractional equation'''
    FUNCTION_EQUATION : EquationNodeType
    '''Specifies function equation'''
    DELIMITER_EQUATION : EquationNodeType
    '''Specifies delimiter equation'''
    NARY_EQUATION : EquationNodeType
    '''Specifies n-ary operator equation'''
    RADICAL_EQUATION : EquationNodeType
    '''Specifies the radical equation'''
    SUPERSCRIPT_EQUATION : EquationNodeType
    '''Specifies superscript equation'''
    SUBSCRIPT_EQUATION : EquationNodeType
    '''Specifies subscript equation'''
    SUB_SUP_EQUATION : EquationNodeType
    '''Specifies an equation with superscripts and subscripts to the right of the operands.'''
    PRE_SUB_SUP_EQUATION : EquationNodeType
    '''Specifies an equation with superscripts and subscripts to the left of the operands.'''
    ACCENT_EQUATION : EquationNodeType
    '''Specifies accent equation'''
    BAR_EQUATION : EquationNodeType
    '''Specifies bar equation'''
    BORDER_BOX_EQUATION : EquationNodeType
    '''Specifies border box equation'''
    BOX_EQUATION : EquationNodeType
    '''Specifies box equation'''
    GROUP_CHARACTER_EQUATION : EquationNodeType
    '''Specifies Group-Character equation'''
    MATRIX_EQUATION : EquationNodeType
    '''Specifies the Matrix equation,'''
    LOWER_LIMIT : EquationNodeType
    '''Specifies the Lower-Limit function'''
    UPPER_LIMIT : EquationNodeType
    '''Specifies the Upper-Limit function'''
    MATHEMATICAL : EquationNodeType
    '''Specifies an equation or mathematical expression(OMath).'''
    FRACTION : EquationNodeType
    '''Specifies fractional equation'''
    FUNCTION : EquationNodeType
    '''Specifies function equation'''
    DELIMITER : EquationNodeType
    '''Specifies delimiter equation'''
    NARY : EquationNodeType
    '''Specifies n-ary operator equation'''
    RADICAL : EquationNodeType
    '''Specifies the radical equation'''
    SUP : EquationNodeType
    '''Specifies superscript equation'''
    SUB : EquationNodeType
    '''Specifies subscript equation'''
    SUB_SUP : EquationNodeType
    '''Specifies an equation with superscripts and subscripts to the right of the operands.'''
    PRE_SUB_SUP : EquationNodeType
    '''Specifies an equation with superscripts and subscripts to the left of the operands.'''
    ACCENT : EquationNodeType
    '''Specifies accent equation'''
    BAR : EquationNodeType
    '''Specifies bar equation'''
    BORDER_BOX : EquationNodeType
    '''Specifies border box equation'''
    BOX : EquationNodeType
    '''Specifies box equation'''
    GROUP_CHR : EquationNodeType
    '''Specifies Group-Character equation'''
    MATRIX : EquationNodeType
    '''Specifies the Matrix equation,'''
    ARRAY_EQUATION : EquationNodeType
    '''Specifies the Equation-Array function. The function consists of one or more equations.'''

class EquationVerticalJustificationType:
    '''This specifies the default vertical justification of equations in the document.'''
    
    TOP : EquationVerticalJustificationType
    '''top'''
    CENTER : EquationVerticalJustificationType
    '''center'''
    BOTTOM : EquationVerticalJustificationType
    '''bottom'''

