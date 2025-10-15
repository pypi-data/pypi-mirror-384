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

class DigitalSignature:
    '''Signature in file.'''
    
    @overload
    def __init__(self, certificate : Any, comments : str, sign_time : datetime) -> None:
        '''Constructor of digitalSignature. Uses .Net implementation.
        
        :param certificate: Certificate object that was used to sign the document.
        :param comments: The purpose to signature.
        :param sign_time: The utc time when the document was signed.'''
        raise NotImplementedError()
    
    @overload
    def __init__(self, raw_data : List[int], password : str, comments : str, sign_time : datetime) -> None:
        '''Constructor of digitalSignature. Uses Bouncy Castle implementation.
        
        :param raw_data: A byte array containing data from an X.509 certificate.
        :param password: The password required to access the X.509 certificate data.
        :param comments: The purpose to signature.
        :param sign_time: The utc time when the document was signed.'''
        raise NotImplementedError()
    
    @property
    def certificate(self) -> Any:
        '''Certificate object that was used to sign the document.'''
        raise NotImplementedError()
    
    @certificate.setter
    def certificate(self, value : Any) -> None:
        '''Certificate object that was used to sign the document.'''
        raise NotImplementedError()
    
    @property
    def comments(self) -> str:
        '''The purpose to signature.'''
        raise NotImplementedError()
    
    @comments.setter
    def comments(self, value : str) -> None:
        '''The purpose to signature.'''
        raise NotImplementedError()
    
    @property
    def sign_time(self) -> datetime:
        '''The time when the document was signed.'''
        raise NotImplementedError()
    
    @sign_time.setter
    def sign_time(self, value : datetime) -> None:
        '''The time when the document was signed.'''
        raise NotImplementedError()
    
    @property
    def id(self) -> System.Guid:
        '''Specifies a GUID which can be cross-referenced with the GUID of the signature line stored in the document content.
        Default value is Empty (all zeroes) Guid.'''
        raise NotImplementedError()
    
    @id.setter
    def id(self, value : System.Guid) -> None:
        '''Specifies a GUID which can be cross-referenced with the GUID of the signature line stored in the document content.
        Default value is Empty (all zeroes) Guid.'''
        raise NotImplementedError()
    
    @property
    def text(self) -> str:
        '''Specifies the text of actual signature in the digital signature.
        Default value is Empty.'''
        raise NotImplementedError()
    
    @text.setter
    def text(self, value : str) -> None:
        '''Specifies the text of actual signature in the digital signature.
        Default value is Empty.'''
        raise NotImplementedError()
    
    @property
    def image(self) -> List[int]:
        '''Specifies an image for the digital signature.
        Default value is null.'''
        raise NotImplementedError()
    
    @image.setter
    def image(self, value : List[int]) -> None:
        '''Specifies an image for the digital signature.
        Default value is null.'''
        raise NotImplementedError()
    
    @property
    def provider_id(self) -> System.Guid:
        '''Specifies the class ID of the signature provider.
        Default value is Empty (all zeroes) Guid.'''
        raise NotImplementedError()
    
    @provider_id.setter
    def provider_id(self, value : System.Guid) -> None:
        '''Specifies the class ID of the signature provider.
        Default value is Empty (all zeroes) Guid.'''
        raise NotImplementedError()
    
    @property
    def is_valid(self) -> bool:
        '''If this digital signature is valid and the document has not been tampered with,
        this value will be true.'''
        raise NotImplementedError()
    
    @property
    def x_ad_es_type(self) -> aspose.cells.digitalsignatures.XAdESType:
        '''XAdES type.
        Default value is None(XAdES is off).'''
        raise NotImplementedError()
    
    @x_ad_es_type.setter
    def x_ad_es_type(self, value : aspose.cells.digitalsignatures.XAdESType) -> None:
        '''XAdES type.
        Default value is None(XAdES is off).'''
        raise NotImplementedError()
    

class DigitalSignatureCollection:
    '''Provides a collection of digital signatures attached to a document.'''
    
    def __init__(self) -> None:
        '''The constructor of DigitalSignatureCollection.'''
        raise NotImplementedError()
    
    def add(self, digital_signature : aspose.cells.digitalsignatures.DigitalSignature) -> None:
        '''Add one signature to DigitalSignatureCollection.
        
        :param digital_signature: Digital signature in collection.'''
        raise NotImplementedError()
    

class XAdESType:
    '''Type of XML Advanced Electronic Signature (XAdES).'''
    
    NONE : XAdESType
    '''XAdES is off.'''
    X_AD_ES : XAdESType
    '''Basic XAdES.'''

