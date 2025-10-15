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

class HighlightChangesOptions:
    '''Represents options of highlighting revsions or changes of shared Excel files.'''
    
    def __init__(self, highlight_on_screen : bool, list_on_new_sheet : bool) -> None:
        '''Represents options of highlighting revsions or changes of shared Excel files.
        
        :param highlight_on_screen: Indicates whether highlighting changes on screen.
        :param list_on_new_sheet: Indicates whether listing changes on a new worksheet.'''
        raise NotImplementedError()
    

class RevisionAutoFormat:
    '''represents a revision record of information about a formatting change.'''
    
    @property
    def type(self) -> aspose.cells.revisions.RevisionType:
        '''Gets the type of the revision.'''
        raise NotImplementedError()
    
    @property
    def worksheet(self) -> aspose.cells.Worksheet:
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        raise NotImplementedError()
    
    @property
    def cell_area(self) -> aspose.cells.CellArea:
        '''Gets the location where the formatting was applied.'''
        raise NotImplementedError()
    

class RevisionCellChange:
    '''Represents the revision that changing cells.'''
    
    @property
    def type(self) -> aspose.cells.revisions.RevisionType:
        '''Represents the type of revision.'''
        raise NotImplementedError()
    
    @property
    def worksheet(self) -> aspose.cells.Worksheet:
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        raise NotImplementedError()
    
    @property
    def cell_name(self) -> str:
        '''Gets the name of the cell.'''
        raise NotImplementedError()
    
    @property
    def row(self) -> int:
        '''Gets the row index of the cell.'''
        raise NotImplementedError()
    
    @property
    def column(self) -> int:
        '''Gets the column index of the cell.'''
        raise NotImplementedError()
    
    @property
    def is_new_formatted(self) -> bool:
        '''Indicates whether this cell is new formatted.'''
        raise NotImplementedError()
    
    @property
    def is_old_formatted(self) -> bool:
        '''Indicates whether this cell is old formatted.'''
        raise NotImplementedError()
    
    @property
    def old_formula(self) -> str:
        '''Gets the old formula.'''
        raise NotImplementedError()
    
    @property
    def old_value(self) -> Any:
        '''Gets old value of the cell.'''
        raise NotImplementedError()
    
    @property
    def new_value(self) -> Any:
        '''Gets new value of the cell.'''
        raise NotImplementedError()
    
    @property
    def new_formula(self) -> str:
        '''Gets the old formula.'''
        raise NotImplementedError()
    
    @property
    def new_style(self) -> aspose.cells.Style:
        '''Gets the new style of the cell.'''
        raise NotImplementedError()
    
    @property
    def old_style(self) -> aspose.cells.Style:
        '''Gets the old style of the cell.'''
        raise NotImplementedError()
    

class RevisionCellComment:
    '''Represents a revision record of a cell comment change.'''
    
    @property
    def type(self) -> aspose.cells.revisions.RevisionType:
        '''Gets the type of revision.'''
        raise NotImplementedError()
    
    @property
    def worksheet(self) -> aspose.cells.Worksheet:
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        raise NotImplementedError()
    
    @property
    def row(self) -> int:
        '''Gets the row index of the which contains a comment.'''
        raise NotImplementedError()
    
    @property
    def column(self) -> int:
        '''Gets the column index of the which contains a comment.'''
        raise NotImplementedError()
    
    @property
    def cell_name(self) -> str:
        '''Gets the name of the cell.'''
        raise NotImplementedError()
    
    @cell_name.setter
    def cell_name(self, value : str) -> None:
        '''Gets the name of the cell.'''
        raise NotImplementedError()
    
    @property
    def action_type(self) -> aspose.cells.revisions.RevisionActionType:
        '''Gets the action type of the revision.'''
        raise NotImplementedError()
    
    @property
    def is_old_comment(self) -> bool:
        '''Indicates whether it\'s an  old comment.'''
        raise NotImplementedError()
    
    @property
    def old_length(self) -> int:
        '''Gets Length of the comment text added in this revision.'''
        raise NotImplementedError()
    
    @property
    def new_length(self) -> int:
        '''Gets Length of the comment before this revision was made.'''
        raise NotImplementedError()
    

class RevisionCellMove:
    '''Represents a revision record on a cell(s) that moved.'''
    
    @property
    def type(self) -> aspose.cells.revisions.RevisionType:
        '''Represents the type of revision.'''
        raise NotImplementedError()
    
    @property
    def worksheet(self) -> aspose.cells.Worksheet:
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        raise NotImplementedError()
    
    @property
    def source_area(self) -> aspose.cells.CellArea:
        '''Gets the source area.'''
        raise NotImplementedError()
    
    @property
    def destination_area(self) -> aspose.cells.CellArea:
        '''Gets the destination area.'''
        raise NotImplementedError()
    
    @property
    def source_worksheet(self) -> aspose.cells.Worksheet:
        '''Gets the source worksheet.'''
        raise NotImplementedError()
    

class RevisionCollection:
    '''Represents all revision logs.'''
    
    @overload
    def copy_to(self, array : List[Aspose.Cells.Revisions.Revision]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[Aspose.Cells.Revisions.Revision], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : Aspose.Cells.Revisions.Revision, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : Aspose.Cells.Revisions.Revision, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : Aspose.Cells.Revisions.Revision) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : Aspose.Cells.Revisions.Revision, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : Aspose.Cells.Revisions.Revision, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def binary_search(self, item : Aspose.Cells.Revisions.Revision) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class RevisionCustomView:
    '''Represents a revision record of adding or removing a custom view to the workbook'''
    
    @property
    def type(self) -> aspose.cells.revisions.RevisionType:
        '''Gets the type of revision.'''
        raise NotImplementedError()
    
    @property
    def worksheet(self) -> aspose.cells.Worksheet:
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        raise NotImplementedError()
    
    @property
    def action_type(self) -> aspose.cells.revisions.RevisionActionType:
        '''Gets the type of action.'''
        raise NotImplementedError()
    
    @property
    def guid(self) -> System.Guid:
        '''Gets the globally unique identifier of the custom view.'''
        raise NotImplementedError()
    

class RevisionDefinedName:
    '''Represents a revision record of a defined name change.'''
    
    @property
    def type(self) -> aspose.cells.revisions.RevisionType:
        '''Represents the type of revision.'''
        raise NotImplementedError()
    
    @property
    def worksheet(self) -> aspose.cells.Worksheet:
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        raise NotImplementedError()
    
    @property
    def text(self) -> str:
        '''Gets the text of the defined name.'''
        raise NotImplementedError()
    
    @property
    def old_formula(self) -> str:
        '''Gets the old formula.'''
        raise NotImplementedError()
    
    @property
    def new_formula(self) -> str:
        '''Gets the formula.'''
        raise NotImplementedError()
    

class RevisionFormat:
    '''Represents a revision record of information about a formatting change.'''
    
    @property
    def type(self) -> aspose.cells.revisions.RevisionType:
        '''Gets the type of revision.'''
        raise NotImplementedError()
    
    @property
    def worksheet(self) -> aspose.cells.Worksheet:
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        raise NotImplementedError()
    
    @property
    def areas(self) -> List[aspose.cells.CellArea]:
        '''The range to which this formatting was applied.'''
        raise NotImplementedError()
    
    @property
    def style(self) -> aspose.cells.Style:
        '''Gets the applied style.'''
        raise NotImplementedError()
    

class RevisionHeader:
    '''Represents a list of specific changes that have taken place for this workbook.'''
    
    def __init__(self) -> None:
        raise NotImplementedError()
    
    @property
    def saved_time(self) -> datetime:
        '''Gets and sets rhe date and time when this set of revisions was saved.'''
        raise NotImplementedError()
    
    @saved_time.setter
    def saved_time(self, value : datetime) -> None:
        '''Gets and sets rhe date and time when this set of revisions was saved.'''
        raise NotImplementedError()
    
    @property
    def user_name(self) -> str:
        '''Gets and sets the name of the user making the revision.'''
        raise NotImplementedError()
    
    @user_name.setter
    def user_name(self, value : str) -> None:
        '''Gets and sets the name of the user making the revision.'''
        raise NotImplementedError()
    

class RevisionInsertDelete:
    '''Represents a revision record of a row/column insert/delete action.'''
    
    @property
    def type(self) -> aspose.cells.revisions.RevisionType:
        '''Represents the type of revision.'''
        raise NotImplementedError()
    
    @property
    def worksheet(self) -> aspose.cells.Worksheet:
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        raise NotImplementedError()
    
    @property
    def cell_area(self) -> aspose.cells.CellArea:
        '''Gets the inserting/deleting range.'''
        raise NotImplementedError()
    
    @property
    def action_type(self) -> aspose.cells.revisions.RevisionActionType:
        '''Gets the action type of this revision.'''
        raise NotImplementedError()
    
    @property
    def revisions(self) -> aspose.cells.revisions.RevisionCollection:
        '''Gets revision list by this operation.'''
        raise NotImplementedError()
    

class RevisionInsertSheet:
    '''Represents a revision record of a sheet that was inserted.'''
    
    @property
    def type(self) -> aspose.cells.revisions.RevisionType:
        '''Gets the type of revision.'''
        raise NotImplementedError()
    
    @property
    def worksheet(self) -> aspose.cells.Worksheet:
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        raise NotImplementedError()
    
    @property
    def action_type(self) -> aspose.cells.revisions.RevisionActionType:
        '''Gets the action type of the revision.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''Gets the name of the worksheet.'''
        raise NotImplementedError()
    
    @property
    def sheet_position(self) -> int:
        '''Gets the zero based position of the new sheet in the sheet tab bar.'''
        raise NotImplementedError()
    

class RevisionLog:
    '''Represents the revision log.'''
    
    @property
    def metadata_table(self) -> aspose.cells.revisions.RevisionHeader:
        '''Gets table that contains metadata about a list of specific changes that have taken place
        for this workbook.'''
        raise NotImplementedError()
    
    @property
    def revisions(self) -> aspose.cells.revisions.RevisionCollection:
        '''Gets all revisions in this log.'''
        raise NotImplementedError()
    

class RevisionLogCollection:
    '''Represents all revision logs.'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.revisions.RevisionLog]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.revisions.RevisionLog], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.revisions.RevisionLog, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.revisions.RevisionLog, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.revisions.RevisionLog) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.revisions.RevisionLog, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.revisions.RevisionLog, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def highlight_changes(self, options : aspose.cells.revisions.HighlightChangesOptions) -> None:
        '''Highlights changes of shared workbook.
        
        :param options: Set the options for filtering which changes should be tracked.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.revisions.RevisionLog) -> int:
        raise NotImplementedError()
    
    @property
    def days_preserving_history(self) -> int:
        '''Gets and sets the number of days the spreadsheet application will keep the change history for this workbook.'''
        raise NotImplementedError()
    
    @days_preserving_history.setter
    def days_preserving_history(self, value : int) -> None:
        '''Gets and sets the number of days the spreadsheet application will keep the change history for this workbook.'''
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class RevisionMergeConflict:
    '''Represents a revision record which indicates that there was a merge conflict.'''
    
    @property
    def type(self) -> aspose.cells.revisions.RevisionType:
        '''Gets the type of revision.'''
        raise NotImplementedError()
    
    @property
    def worksheet(self) -> aspose.cells.Worksheet:
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        raise NotImplementedError()
    

class RevisionQueryTable:
    '''Represents a revision of a query table field change.'''
    
    @property
    def type(self) -> aspose.cells.revisions.RevisionType:
        '''Represents the type of the revision.'''
        raise NotImplementedError()
    
    @property
    def worksheet(self) -> aspose.cells.Worksheet:
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        raise NotImplementedError()
    
    @property
    def cell_area(self) -> aspose.cells.CellArea:
        '''Gets the location of the affected query table.'''
        raise NotImplementedError()
    
    @property
    def field_id(self) -> int:
        '''Gets ID of the specific query table field that was removed.'''
        raise NotImplementedError()
    

class RevisionRenameSheet:
    '''Represents a revision of renaming sheet.'''
    
    @property
    def type(self) -> aspose.cells.revisions.RevisionType:
        '''Represents the type of the revision.'''
        raise NotImplementedError()
    
    @property
    def worksheet(self) -> aspose.cells.Worksheet:
        raise NotImplementedError()
    
    @property
    def id(self) -> int:
        raise NotImplementedError()
    
    @property
    def old_name(self) -> str:
        '''Gets the old name of the worksheet.'''
        raise NotImplementedError()
    
    @property
    def new_name(self) -> str:
        '''Gets the new name of the worksheet.'''
        raise NotImplementedError()
    

class RevisionActionType:
    '''Represents the type of revision action.'''
    
    ADD : RevisionActionType
    '''Add revision.'''
    DELETE : RevisionActionType
    '''Delete revision.'''
    DELETE_COLUMN : RevisionActionType
    '''Column delete revision.'''
    DELETE_ROW : RevisionActionType
    '''Row delete revision.'''
    INSERT_COLUMN : RevisionActionType
    '''Column insert revision.'''
    INSERT_ROW : RevisionActionType
    '''Row insert revision.'''

class RevisionType:
    '''Represents the revision type.'''
    
    CUSTOM_VIEW : RevisionType
    '''Custom view.'''
    DEFINED_NAME : RevisionType
    '''Defined name.'''
    CHANGE_CELLS : RevisionType
    '''Cells change.'''
    AUTO_FORMAT : RevisionType
    '''Auto format.'''
    MERGE_CONFLICT : RevisionType
    '''Merge conflict.'''
    COMMENT : RevisionType
    '''Comment.'''
    FORMAT : RevisionType
    '''Format.'''
    INSERT_SHEET : RevisionType
    '''Insert worksheet.'''
    MOVE_CELLS : RevisionType
    '''Move cells.'''
    UNDO : RevisionType
    '''Undo.'''
    QUERY_TABLE : RevisionType
    '''Query table.'''
    INSERT_DELETE : RevisionType
    '''Inserting or deleting.'''
    RENAME_SHEET : RevisionType
    '''Rename worksheet.'''
    UNKNOWN : RevisionType
    '''Unknown.'''

