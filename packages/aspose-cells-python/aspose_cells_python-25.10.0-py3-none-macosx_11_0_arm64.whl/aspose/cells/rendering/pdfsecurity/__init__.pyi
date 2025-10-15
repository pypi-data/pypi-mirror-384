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

class PdfSecurityOptions:
    '''Options for encrypting and access permissions for a PDF document.
    PDF/A does not allow security setting.'''
    
    def __init__(self) -> None:
        '''The constructor of PdfSecurityOptions'''
        raise NotImplementedError()
    
    @property
    def user_password(self) -> str:
        '''Gets the user password required for opening the encrypted PDF document.'''
        raise NotImplementedError()
    
    @user_password.setter
    def user_password(self, value : str) -> None:
        '''Sets the user password required for opening the encrypted PDF document.'''
        raise NotImplementedError()
    
    @property
    def owner_password(self) -> str:
        '''Gets the owner password for the encrypted PDF document.'''
        raise NotImplementedError()
    
    @owner_password.setter
    def owner_password(self, value : str) -> None:
        '''Sets the owner password for the encrypted PDF document.'''
        raise NotImplementedError()
    
    @property
    def print_permission(self) -> bool:
        '''Indicates whether to allow to print the document.'''
        raise NotImplementedError()
    
    @print_permission.setter
    def print_permission(self, value : bool) -> None:
        '''Indicates whether to allow to print the document.'''
        raise NotImplementedError()
    
    @property
    def modify_document_permission(self) -> bool:
        '''Indicates whether to allow to modify the contents of the document by operations other than those controlled
        by :py:attr:`aspose.cells.rendering.pdfsecurity.PdfSecurityOptions.annotations_permission`, :py:attr:`aspose.cells.rendering.pdfsecurity.PdfSecurityOptions.fill_forms_permission` and :py:attr:`aspose.cells.rendering.pdfsecurity.PdfSecurityOptions.assemble_document_permission`.'''
        raise NotImplementedError()
    
    @modify_document_permission.setter
    def modify_document_permission(self, value : bool) -> None:
        '''Indicates whether to allow to modify the contents of the document by operations other than those controlled
        by :py:attr:`aspose.cells.rendering.pdfsecurity.PdfSecurityOptions.annotations_permission`, :py:attr:`aspose.cells.rendering.pdfsecurity.PdfSecurityOptions.fill_forms_permission` and :py:attr:`aspose.cells.rendering.pdfsecurity.PdfSecurityOptions.assemble_document_permission`.'''
        raise NotImplementedError()
    
    @property
    def extract_content_permission_obsolete(self) -> bool:
        '''Permission to copy or extract content Obsoleted according to PDF reference.'''
        raise NotImplementedError()
    
    @extract_content_permission_obsolete.setter
    def extract_content_permission_obsolete(self, value : bool) -> None:
        '''Permission to copy or extract content Obsoleted according to PDF reference.'''
        raise NotImplementedError()
    
    @property
    def annotations_permission(self) -> bool:
        '''Indicates whether to allow to add or modify text annotations, fill in interactive form fields.'''
        raise NotImplementedError()
    
    @annotations_permission.setter
    def annotations_permission(self, value : bool) -> None:
        '''Indicates whether to allow to add or modify text annotations, fill in interactive form fields.'''
        raise NotImplementedError()
    
    @property
    def fill_forms_permission(self) -> bool:
        '''Indicates whether to allow to fill in existing interactive form fields (including signature fields),
        even if :py:attr:`aspose.cells.rendering.pdfsecurity.PdfSecurityOptions.modify_document_permission` is clear.'''
        raise NotImplementedError()
    
    @fill_forms_permission.setter
    def fill_forms_permission(self, value : bool) -> None:
        '''Indicates whether to allow to fill in existing interactive form fields (including signature fields),
        even if :py:attr:`aspose.cells.rendering.pdfsecurity.PdfSecurityOptions.modify_document_permission` is clear.'''
        raise NotImplementedError()
    
    @property
    def extract_content_permission(self) -> bool:
        '''Indicates whether to allow to copy or otherwise extract text and graphics from the document
        by operations other than that controlled by :py:attr:`aspose.cells.rendering.pdfsecurity.PdfSecurityOptions.accessibility_extract_content`.'''
        raise NotImplementedError()
    
    @extract_content_permission.setter
    def extract_content_permission(self, value : bool) -> None:
        '''Indicates whether to allow to copy or otherwise extract text and graphics from the document
        by operations other than that controlled by :py:attr:`aspose.cells.rendering.pdfsecurity.PdfSecurityOptions.accessibility_extract_content`.'''
        raise NotImplementedError()
    
    @property
    def accessibility_extract_content(self) -> bool:
        '''Indicates whether to allow to extract text and graphics (in support of accessibility to users with disabilities or for other purposes).'''
        raise NotImplementedError()
    
    @accessibility_extract_content.setter
    def accessibility_extract_content(self, value : bool) -> None:
        '''Indicates whether to allow to extract text and graphics (in support of accessibility to users with disabilities or for other purposes).'''
        raise NotImplementedError()
    
    @property
    def assemble_document_permission(self) -> bool:
        '''Indicates whether to allow to assemble the document (insert, rotate, or delete pages and create bookmarks or thumbnail images),
        even if :py:attr:`aspose.cells.rendering.pdfsecurity.PdfSecurityOptions.modify_document_permission` is clear.'''
        raise NotImplementedError()
    
    @assemble_document_permission.setter
    def assemble_document_permission(self, value : bool) -> None:
        '''Indicates whether to allow to assemble the document (insert, rotate, or delete pages and create bookmarks or thumbnail images),
        even if :py:attr:`aspose.cells.rendering.pdfsecurity.PdfSecurityOptions.modify_document_permission` is clear.'''
        raise NotImplementedError()
    
    @property
    def full_quality_print_permission(self) -> bool:
        '''Indicates whether to allow to print the document to a representation from
        which a faithful digital copy of the PDF content could be generated.'''
        raise NotImplementedError()
    
    @full_quality_print_permission.setter
    def full_quality_print_permission(self, value : bool) -> None:
        '''Indicates whether to allow to print the document to a representation from
        which a faithful digital copy of the PDF content could be generated.'''
        raise NotImplementedError()
    

