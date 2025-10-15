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

class ConnectionParameter:
    '''Specifies properties about any parameters used with external data connections
    Parameters are valid for ODBC and web queries.'''
    
    @property
    def sql_type(self) -> aspose.cells.externalconnections.SqlDataType:
        '''SQL data type of the parameter. Only valid for ODBC sources.'''
        raise NotImplementedError()
    
    @sql_type.setter
    def sql_type(self, value : aspose.cells.externalconnections.SqlDataType) -> None:
        '''SQL data type of the parameter. Only valid for ODBC sources.'''
        raise NotImplementedError()
    
    @property
    def refresh_on_change(self) -> bool:
        '''Flag indicating whether the query should automatically refresh when the contents of a
        cell that provides the parameter value changes. If true, then external data is refreshed
        using the new parameter value every time there\'s a change. If false, then external data
        is only refreshed when requested by the user, or some other event triggers refresh (e.g., workbook opened).'''
        raise NotImplementedError()
    
    @refresh_on_change.setter
    def refresh_on_change(self, value : bool) -> None:
        '''Flag indicating whether the query should automatically refresh when the contents of a
        cell that provides the parameter value changes. If true, then external data is refreshed
        using the new parameter value every time there\'s a change. If false, then external data
        is only refreshed when requested by the user, or some other event triggers refresh (e.g., workbook opened).'''
        raise NotImplementedError()
    
    @property
    def prompt(self) -> str:
        '''Prompt string for the parameter. Presented to the spreadsheet user along with input UI
        to collect the parameter value before refreshing the external data. Used only when
        parameterType = prompt.'''
        raise NotImplementedError()
    
    @prompt.setter
    def prompt(self, value : str) -> None:
        '''Prompt string for the parameter. Presented to the spreadsheet user along with input UI
        to collect the parameter value before refreshing the external data. Used only when
        parameterType = prompt.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.externalconnections.ConnectionParameterType:
        '''Type of parameter used.
        If the parameterType=value, then the value from boolean, double, integer,
        or string will be used.  In this case, it is expected that only one of
        {boolean, double, integer, or string} will be specified.'''
        raise NotImplementedError()
    
    @type.setter
    def type(self, value : aspose.cells.externalconnections.ConnectionParameterType) -> None:
        '''Type of parameter used.
        If the parameterType=value, then the value from boolean, double, integer,
        or string will be used.  In this case, it is expected that only one of
        {boolean, double, integer, or string} will be specified.'''
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        '''The name of the parameter.'''
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        '''The name of the parameter.'''
        raise NotImplementedError()
    
    @property
    def cell_reference(self) -> str:
        '''Cell reference indicating which cell\'s value to use for the query parameter. Used only when parameterType is cell.'''
        raise NotImplementedError()
    
    @cell_reference.setter
    def cell_reference(self, value : str) -> None:
        '''Cell reference indicating which cell\'s value to use for the query parameter. Used only when parameterType is cell.'''
        raise NotImplementedError()
    
    @property
    def value(self) -> Any:
        '''Non-integer numeric value,Integer value,String value or Boolean value
        to use as the query parameter. Used only when parameterType is value.'''
        raise NotImplementedError()
    
    @value.setter
    def value(self, value : Any) -> None:
        '''Non-integer numeric value,Integer value,String value or Boolean value
        to use as the query parameter. Used only when parameterType is value.'''
        raise NotImplementedError()
    

class ConnectionParameterCollection:
    '''Specifies the :py:class:`aspose.cells.externalconnections.ConnectionParameter` collection'''
    
    @overload
    def copy_to(self, array : List[aspose.cells.externalconnections.ConnectionParameter]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[aspose.cells.externalconnections.ConnectionParameter], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.externalconnections.ConnectionParameter, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : aspose.cells.externalconnections.ConnectionParameter, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.externalconnections.ConnectionParameter) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.externalconnections.ConnectionParameter, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : aspose.cells.externalconnections.ConnectionParameter, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def get(self, conn_param_name : str) -> aspose.cells.externalconnections.ConnectionParameter:
        '''Gets the :py:class:`aspose.cells.externalconnections.ConnectionParameter` element with the specified name.
        
        :param conn_param_name: connection parameter name
        :returns: The element with the specified name.'''
        raise NotImplementedError()
    
    def binary_search(self, item : aspose.cells.externalconnections.ConnectionParameter) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class DBConnection:
    '''Specifies all properties associated with an ODBC or OLE DB external data connection.'''
    
    @property
    def id(self) -> int:
        raise NotImplementedError()
    
    @property
    def connection_id(self) -> int:
        raise NotImplementedError()
    
    @property
    def class_type(self) -> aspose.cells.externalconnections.ExternalConnectionClassType:
        '''Gets the type of this :py:class:`Aspose.Cells.ExternalConnections.ExternalConnection` object.'''
        raise NotImplementedError()
    
    @property
    def power_query_formula(self) -> aspose.cells.querytables.PowerQueryFormula:
        '''Gets the definition of power query formula.'''
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.externalconnections.ConnectionDataSourceType:
        raise NotImplementedError()
    
    @type.setter
    def type(self, value : aspose.cells.externalconnections.ConnectionDataSourceType) -> None:
        raise NotImplementedError()
    
    @property
    def source_type(self) -> aspose.cells.externalconnections.ConnectionDataSourceType:
        raise NotImplementedError()
    
    @source_type.setter
    def source_type(self, value : aspose.cells.externalconnections.ConnectionDataSourceType) -> None:
        raise NotImplementedError()
    
    @property
    def sso_id(self) -> str:
        raise NotImplementedError()
    
    @sso_id.setter
    def sso_id(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def save_password(self) -> bool:
        raise NotImplementedError()
    
    @save_password.setter
    def save_password(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def save_data(self) -> bool:
        raise NotImplementedError()
    
    @save_data.setter
    def save_data(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def refresh_on_load(self) -> bool:
        raise NotImplementedError()
    
    @refresh_on_load.setter
    def refresh_on_load(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def reconnection_method_type(self) -> aspose.cells.externalconnections.ReConnectionMethodType:
        raise NotImplementedError()
    
    @reconnection_method_type.setter
    def reconnection_method_type(self, value : aspose.cells.externalconnections.ReConnectionMethodType) -> None:
        raise NotImplementedError()
    
    @property
    def reconnection_method(self) -> aspose.cells.externalconnections.ReConnectionMethodType:
        raise NotImplementedError()
    
    @reconnection_method.setter
    def reconnection_method(self, value : aspose.cells.externalconnections.ReConnectionMethodType) -> None:
        raise NotImplementedError()
    
    @property
    def only_use_connection_file(self) -> bool:
        raise NotImplementedError()
    
    @only_use_connection_file.setter
    def only_use_connection_file(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def odc_file(self) -> str:
        raise NotImplementedError()
    
    @odc_file.setter
    def odc_file(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def source_file(self) -> str:
        raise NotImplementedError()
    
    @source_file.setter
    def source_file(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def connection_file(self) -> str:
        raise NotImplementedError()
    
    @property
    def is_new(self) -> bool:
        raise NotImplementedError()
    
    @is_new.setter
    def is_new(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def keep_alive(self) -> bool:
        raise NotImplementedError()
    
    @keep_alive.setter
    def keep_alive(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def refresh_internal(self) -> int:
        raise NotImplementedError()
    
    @refresh_internal.setter
    def refresh_internal(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def connection_description(self) -> str:
        raise NotImplementedError()
    
    @connection_description.setter
    def connection_description(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def is_deleted(self) -> bool:
        raise NotImplementedError()
    
    @is_deleted.setter
    def is_deleted(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def credentials_method_type(self) -> aspose.cells.externalconnections.CredentialsMethodType:
        raise NotImplementedError()
    
    @credentials_method_type.setter
    def credentials_method_type(self, value : aspose.cells.externalconnections.CredentialsMethodType) -> None:
        raise NotImplementedError()
    
    @property
    def credentials(self) -> aspose.cells.externalconnections.CredentialsMethodType:
        raise NotImplementedError()
    
    @credentials.setter
    def credentials(self, value : aspose.cells.externalconnections.CredentialsMethodType) -> None:
        raise NotImplementedError()
    
    @property
    def background_refresh(self) -> bool:
        raise NotImplementedError()
    
    @background_refresh.setter
    def background_refresh(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def parameters(self) -> aspose.cells.externalconnections.ConnectionParameterCollection:
        raise NotImplementedError()
    
    @property
    def command(self) -> str:
        '''The string containing the database command to pass to the data provider API that will
        interact with the external source in order to retrieve data'''
        raise NotImplementedError()
    
    @command.setter
    def command(self, value : str) -> None:
        '''The string containing the database command to pass to the data provider API that will
        interact with the external source in order to retrieve data'''
        raise NotImplementedError()
    
    @property
    def command_type(self) -> aspose.cells.externalconnections.OLEDBCommandType:
        '''Specifies the OLE DB command type.
        1. Query specifies a cube name
        2. Query specifies a SQL statement
        3. Query specifies a table name
        4. Query specifies that default information has been given, and it is up to the provider how to interpret.
        5. Query is against a web based List Data Provider.'''
        raise NotImplementedError()
    
    @command_type.setter
    def command_type(self, value : aspose.cells.externalconnections.OLEDBCommandType) -> None:
        '''Specifies the OLE DB command type.
        1. Query specifies a cube name
        2. Query specifies a SQL statement
        3. Query specifies a table name
        4. Query specifies that default information has been given, and it is up to the provider how to interpret.
        5. Query is against a web based List Data Provider.'''
        raise NotImplementedError()
    
    @property
    def connection_string(self) -> str:
        '''The connection information string is used to make contact with an OLE DB or ODBC data source.'''
        raise NotImplementedError()
    
    @connection_string.setter
    def connection_string(self, value : str) -> None:
        '''The connection information string is used to make contact with an OLE DB or ODBC data source.'''
        raise NotImplementedError()
    
    @property
    def second_command(self) -> str:
        '''Specifies a second command text string that is persisted when PivotTable server-based
        page fields are in use.
        For ODBC connections, serverCommand is usually a broader query than command (no
        WHERE clause is present in the former). Based on these 2 commands(Command and ServerCommand),
        parameter UI can be populated and parameterized queries can be constructed'''
        raise NotImplementedError()
    
    @second_command.setter
    def second_command(self, value : str) -> None:
        '''Specifies a second command text string that is persisted when PivotTable server-based
        page fields are in use.
        For ODBC connections, serverCommand is usually a broader query than command (no
        WHERE clause is present in the former). Based on these 2 commands(Command and ServerCommand),
        parameter UI can be populated and parameterized queries can be constructed'''
        raise NotImplementedError()
    
    @property
    def connection_info(self) -> str:
        '''The connection information string is used to make contact with an OLE DB or ODBC data source.'''
        raise NotImplementedError()
    
    @connection_info.setter
    def connection_info(self, value : str) -> None:
        '''The connection information string is used to make contact with an OLE DB or ODBC data source.'''
        raise NotImplementedError()
    
    @property
    def sever_command(self) -> str:
        '''Specifies a second command text string that is persisted when PivotTable server-based
        page fields are in use.
        For ODBC connections, serverCommand is usually a broader query than command (no
        WHERE clause is present in the former). Based on these 2 commands(Command and ServerCommand),
        parameter UI can be populated and parameterized queries can be constructed'''
        raise NotImplementedError()
    
    @sever_command.setter
    def sever_command(self, value : str) -> None:
        '''Specifies a second command text string that is persisted when PivotTable server-based
        page fields are in use.
        For ODBC connections, serverCommand is usually a broader query than command (no
        WHERE clause is present in the former). Based on these 2 commands(Command and ServerCommand),
        parameter UI can be populated and parameterized queries can be constructed'''
        raise NotImplementedError()
    

class DataModelConnection:
    '''Specifies a data model connection'''
    
    @property
    def id(self) -> int:
        raise NotImplementedError()
    
    @property
    def connection_id(self) -> int:
        raise NotImplementedError()
    
    @property
    def class_type(self) -> aspose.cells.externalconnections.ExternalConnectionClassType:
        '''Gets the type of this :py:class:`Aspose.Cells.ExternalConnections.ExternalConnection` object.'''
        raise NotImplementedError()
    
    @property
    def power_query_formula(self) -> aspose.cells.querytables.PowerQueryFormula:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.externalconnections.ConnectionDataSourceType:
        raise NotImplementedError()
    
    @type.setter
    def type(self, value : aspose.cells.externalconnections.ConnectionDataSourceType) -> None:
        raise NotImplementedError()
    
    @property
    def source_type(self) -> aspose.cells.externalconnections.ConnectionDataSourceType:
        raise NotImplementedError()
    
    @source_type.setter
    def source_type(self, value : aspose.cells.externalconnections.ConnectionDataSourceType) -> None:
        raise NotImplementedError()
    
    @property
    def sso_id(self) -> str:
        raise NotImplementedError()
    
    @sso_id.setter
    def sso_id(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def save_password(self) -> bool:
        raise NotImplementedError()
    
    @save_password.setter
    def save_password(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def save_data(self) -> bool:
        raise NotImplementedError()
    
    @save_data.setter
    def save_data(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def refresh_on_load(self) -> bool:
        raise NotImplementedError()
    
    @refresh_on_load.setter
    def refresh_on_load(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def reconnection_method_type(self) -> aspose.cells.externalconnections.ReConnectionMethodType:
        raise NotImplementedError()
    
    @reconnection_method_type.setter
    def reconnection_method_type(self, value : aspose.cells.externalconnections.ReConnectionMethodType) -> None:
        raise NotImplementedError()
    
    @property
    def reconnection_method(self) -> aspose.cells.externalconnections.ReConnectionMethodType:
        raise NotImplementedError()
    
    @reconnection_method.setter
    def reconnection_method(self, value : aspose.cells.externalconnections.ReConnectionMethodType) -> None:
        raise NotImplementedError()
    
    @property
    def only_use_connection_file(self) -> bool:
        raise NotImplementedError()
    
    @only_use_connection_file.setter
    def only_use_connection_file(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def odc_file(self) -> str:
        raise NotImplementedError()
    
    @odc_file.setter
    def odc_file(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def source_file(self) -> str:
        raise NotImplementedError()
    
    @source_file.setter
    def source_file(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def connection_file(self) -> str:
        raise NotImplementedError()
    
    @property
    def is_new(self) -> bool:
        raise NotImplementedError()
    
    @is_new.setter
    def is_new(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def keep_alive(self) -> bool:
        raise NotImplementedError()
    
    @keep_alive.setter
    def keep_alive(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def refresh_internal(self) -> int:
        raise NotImplementedError()
    
    @refresh_internal.setter
    def refresh_internal(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def connection_description(self) -> str:
        raise NotImplementedError()
    
    @connection_description.setter
    def connection_description(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def is_deleted(self) -> bool:
        raise NotImplementedError()
    
    @is_deleted.setter
    def is_deleted(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def credentials_method_type(self) -> aspose.cells.externalconnections.CredentialsMethodType:
        raise NotImplementedError()
    
    @credentials_method_type.setter
    def credentials_method_type(self, value : aspose.cells.externalconnections.CredentialsMethodType) -> None:
        raise NotImplementedError()
    
    @property
    def credentials(self) -> aspose.cells.externalconnections.CredentialsMethodType:
        raise NotImplementedError()
    
    @credentials.setter
    def credentials(self, value : aspose.cells.externalconnections.CredentialsMethodType) -> None:
        raise NotImplementedError()
    
    @property
    def background_refresh(self) -> bool:
        raise NotImplementedError()
    
    @background_refresh.setter
    def background_refresh(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def parameters(self) -> aspose.cells.externalconnections.ConnectionParameterCollection:
        raise NotImplementedError()
    
    @property
    def command(self) -> str:
        '''The string containing the database command to pass to the data provider API that will
        interact with the external source in order to retrieve data'''
        raise NotImplementedError()
    
    @command.setter
    def command(self, value : str) -> None:
        '''The string containing the database command to pass to the data provider API that will
        interact with the external source in order to retrieve data'''
        raise NotImplementedError()
    
    @property
    def command_type(self) -> aspose.cells.externalconnections.OLEDBCommandType:
        '''Returns :py:class:`aspose.cells.externalconnections.OLEDBCommandType` type.'''
        raise NotImplementedError()
    
    @command_type.setter
    def command_type(self, value : aspose.cells.externalconnections.OLEDBCommandType) -> None:
        '''Returns :py:class:`aspose.cells.externalconnections.OLEDBCommandType` type.'''
        raise NotImplementedError()
    
    @property
    def connection_string(self) -> str:
        '''The connection information string is used to make contact with an OLE DB or ODBC data source.'''
        raise NotImplementedError()
    
    @connection_string.setter
    def connection_string(self, value : str) -> None:
        '''The connection information string is used to make contact with an OLE DB or ODBC data source.'''
        raise NotImplementedError()
    
    @property
    def second_command(self) -> str:
        raise NotImplementedError()
    
    @second_command.setter
    def second_command(self, value : str) -> None:
        raise NotImplementedError()
    

class ExternalConnectionCollection:
    '''Specifies the :py:class:`Aspose.Cells.ExternalConnections.ExternalConnection` collection'''
    
    @overload
    def copy_to(self, array : List[Aspose.Cells.ExternalConnections.ExternalConnection]) -> None:
        raise NotImplementedError()
    
    @overload
    def copy_to(self, index : int, array : List[Aspose.Cells.ExternalConnections.ExternalConnection], array_index : int, count : int) -> None:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : Aspose.Cells.ExternalConnections.ExternalConnection, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def index_of(self, item : Aspose.Cells.ExternalConnections.ExternalConnection, index : int, count : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : Aspose.Cells.ExternalConnections.ExternalConnection) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : Aspose.Cells.ExternalConnections.ExternalConnection, index : int) -> int:
        raise NotImplementedError()
    
    @overload
    def last_index_of(self, item : Aspose.Cells.ExternalConnections.ExternalConnection, index : int, count : int) -> int:
        raise NotImplementedError()
    
    def get(self, connection_name : str) -> Aspose.Cells.ExternalConnections.ExternalConnection:
        '''Gets the :py:class:`Aspose.Cells.ExternalConnections.ExternalConnection` element with the specified name.
        
        :param connection_name: the name of data connection
        :returns: The element with the specified name.'''
        raise NotImplementedError()
    
    def get_external_connection_by_id(self, conn_id : int) -> Aspose.Cells.ExternalConnections.ExternalConnection:
        '''Gets the :py:class:`Aspose.Cells.ExternalConnections.ExternalConnection` element with the specified id.
        
        :param conn_id: external connection id
        :returns: The element with the specified id.'''
        raise NotImplementedError()
    
    def binary_search(self, item : Aspose.Cells.ExternalConnections.ExternalConnection) -> int:
        raise NotImplementedError()
    
    @property
    def capacity(self) -> int:
        raise NotImplementedError()
    
    @capacity.setter
    def capacity(self, value : int) -> None:
        raise NotImplementedError()
    

class WebQueryConnection:
    '''Specifies the properties for a web query source. A web query will retrieve data from HTML tables,
    and can also supply HTTP "Get" parameters to be processed by the web server in generating the HTML by
    including the parameters and parameter elements.'''
    
    @property
    def id(self) -> int:
        raise NotImplementedError()
    
    @property
    def connection_id(self) -> int:
        raise NotImplementedError()
    
    @property
    def class_type(self) -> aspose.cells.externalconnections.ExternalConnectionClassType:
        '''Gets the type of this :py:class:`Aspose.Cells.ExternalConnections.ExternalConnection` object.'''
        raise NotImplementedError()
    
    @property
    def power_query_formula(self) -> aspose.cells.querytables.PowerQueryFormula:
        raise NotImplementedError()
    
    @property
    def type(self) -> aspose.cells.externalconnections.ConnectionDataSourceType:
        raise NotImplementedError()
    
    @type.setter
    def type(self, value : aspose.cells.externalconnections.ConnectionDataSourceType) -> None:
        raise NotImplementedError()
    
    @property
    def source_type(self) -> aspose.cells.externalconnections.ConnectionDataSourceType:
        raise NotImplementedError()
    
    @source_type.setter
    def source_type(self, value : aspose.cells.externalconnections.ConnectionDataSourceType) -> None:
        raise NotImplementedError()
    
    @property
    def sso_id(self) -> str:
        raise NotImplementedError()
    
    @sso_id.setter
    def sso_id(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def save_password(self) -> bool:
        raise NotImplementedError()
    
    @save_password.setter
    def save_password(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def save_data(self) -> bool:
        raise NotImplementedError()
    
    @save_data.setter
    def save_data(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def refresh_on_load(self) -> bool:
        raise NotImplementedError()
    
    @refresh_on_load.setter
    def refresh_on_load(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def reconnection_method_type(self) -> aspose.cells.externalconnections.ReConnectionMethodType:
        raise NotImplementedError()
    
    @reconnection_method_type.setter
    def reconnection_method_type(self, value : aspose.cells.externalconnections.ReConnectionMethodType) -> None:
        raise NotImplementedError()
    
    @property
    def reconnection_method(self) -> aspose.cells.externalconnections.ReConnectionMethodType:
        raise NotImplementedError()
    
    @reconnection_method.setter
    def reconnection_method(self, value : aspose.cells.externalconnections.ReConnectionMethodType) -> None:
        raise NotImplementedError()
    
    @property
    def only_use_connection_file(self) -> bool:
        raise NotImplementedError()
    
    @only_use_connection_file.setter
    def only_use_connection_file(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def odc_file(self) -> str:
        raise NotImplementedError()
    
    @odc_file.setter
    def odc_file(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def source_file(self) -> str:
        raise NotImplementedError()
    
    @source_file.setter
    def source_file(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def connection_file(self) -> str:
        '''Gets the connection file.'''
        raise NotImplementedError()
    
    @property
    def is_new(self) -> bool:
        raise NotImplementedError()
    
    @is_new.setter
    def is_new(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def name(self) -> str:
        raise NotImplementedError()
    
    @name.setter
    def name(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def keep_alive(self) -> bool:
        raise NotImplementedError()
    
    @keep_alive.setter
    def keep_alive(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def refresh_internal(self) -> int:
        raise NotImplementedError()
    
    @refresh_internal.setter
    def refresh_internal(self, value : int) -> None:
        raise NotImplementedError()
    
    @property
    def connection_description(self) -> str:
        raise NotImplementedError()
    
    @connection_description.setter
    def connection_description(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def is_deleted(self) -> bool:
        raise NotImplementedError()
    
    @is_deleted.setter
    def is_deleted(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def credentials_method_type(self) -> aspose.cells.externalconnections.CredentialsMethodType:
        raise NotImplementedError()
    
    @credentials_method_type.setter
    def credentials_method_type(self, value : aspose.cells.externalconnections.CredentialsMethodType) -> None:
        raise NotImplementedError()
    
    @property
    def credentials(self) -> aspose.cells.externalconnections.CredentialsMethodType:
        raise NotImplementedError()
    
    @credentials.setter
    def credentials(self, value : aspose.cells.externalconnections.CredentialsMethodType) -> None:
        raise NotImplementedError()
    
    @property
    def background_refresh(self) -> bool:
        raise NotImplementedError()
    
    @background_refresh.setter
    def background_refresh(self, value : bool) -> None:
        raise NotImplementedError()
    
    @property
    def parameters(self) -> aspose.cells.externalconnections.ConnectionParameterCollection:
        raise NotImplementedError()
    
    @property
    def command(self) -> str:
        raise NotImplementedError()
    
    @command.setter
    def command(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def command_type(self) -> aspose.cells.externalconnections.OLEDBCommandType:
        raise NotImplementedError()
    
    @command_type.setter
    def command_type(self, value : aspose.cells.externalconnections.OLEDBCommandType) -> None:
        raise NotImplementedError()
    
    @property
    def connection_string(self) -> str:
        raise NotImplementedError()
    
    @connection_string.setter
    def connection_string(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def second_command(self) -> str:
        raise NotImplementedError()
    
    @second_command.setter
    def second_command(self, value : str) -> None:
        raise NotImplementedError()
    
    @property
    def is_xml(self) -> bool:
        '''true if the web query source is XML (versus HTML), otherwise false.'''
        raise NotImplementedError()
    
    @is_xml.setter
    def is_xml(self, value : bool) -> None:
        '''true if the web query source is XML (versus HTML), otherwise false.'''
        raise NotImplementedError()
    
    @property
    def is_xl97(self) -> bool:
        '''This flag exists for backward compatibility with older existing spreadsheet files, and is set
        to true if this web query was created in Microsoft Excel 97.
        This is an optional attribute that can be ignored.'''
        raise NotImplementedError()
    
    @is_xl97.setter
    def is_xl97(self, value : bool) -> None:
        '''This flag exists for backward compatibility with older existing spreadsheet files, and is set
        to true if this web query was created in Microsoft Excel 97.
        This is an optional attribute that can be ignored.'''
        raise NotImplementedError()
    
    @property
    def is_xl2000(self) -> bool:
        '''This flag exists for backward compatibility with older existing spreadsheet files, and is set
        to true if this web query was refreshed in a spreadsheet application newer than or equal
        to Microsoft Excel 2000.
        This is an optional attribute that can be ignored.'''
        raise NotImplementedError()
    
    @is_xl2000.setter
    def is_xl2000(self, value : bool) -> None:
        '''This flag exists for backward compatibility with older existing spreadsheet files, and is set
        to true if this web query was refreshed in a spreadsheet application newer than or equal
        to Microsoft Excel 2000.
        This is an optional attribute that can be ignored.'''
        raise NotImplementedError()
    
    @property
    def url(self) -> str:
        '''URL to use to refresh external data.'''
        raise NotImplementedError()
    
    @url.setter
    def url(self, value : str) -> None:
        '''URL to use to refresh external data.'''
        raise NotImplementedError()
    
    @property
    def is_text_dates(self) -> bool:
        '''Flag indicating whether dates should be imported into cells in the worksheet as text rather than dates.'''
        raise NotImplementedError()
    
    @is_text_dates.setter
    def is_text_dates(self, value : bool) -> None:
        '''Flag indicating whether dates should be imported into cells in the worksheet as text rather than dates.'''
        raise NotImplementedError()
    
    @property
    def is_xml_source_data(self) -> bool:
        '''Flag indicating that XML source data should be imported instead of the HTML table itself.'''
        raise NotImplementedError()
    
    @is_xml_source_data.setter
    def is_xml_source_data(self, value : bool) -> None:
        '''Flag indicating that XML source data should be imported instead of the HTML table itself.'''
        raise NotImplementedError()
    
    @property
    def post(self) -> str:
        '''Returns the string used with the post method of inputting data into a web server
        to return data from a web query.'''
        raise NotImplementedError()
    
    @post.setter
    def post(self, value : str) -> None:
        '''Returns or sets the string used with the post method of inputting data into a web server
        to return data from a web query.'''
        raise NotImplementedError()
    
    @property
    def is_parse_pre(self) -> bool:
        '''Flag indicating whether data contained within HTML PRE tags in the web page is
        parsed into columns when you import the page into a query table.'''
        raise NotImplementedError()
    
    @is_parse_pre.setter
    def is_parse_pre(self, value : bool) -> None:
        '''Flag indicating whether data contained within HTML PRE tags in the web page is
        parsed into columns when you import the page into a query table.'''
        raise NotImplementedError()
    
    @property
    def is_html_tables(self) -> bool:
        '''Flag indicating whether web queries should only work on HTML tables.'''
        raise NotImplementedError()
    
    @is_html_tables.setter
    def is_html_tables(self, value : bool) -> None:
        '''Flag indicating whether web queries should only work on HTML tables.'''
        raise NotImplementedError()
    
    @property
    def html_format(self) -> aspose.cells.externalconnections.HtmlFormatHandlingType:
        '''How to handle formatting from the HTML source when bringing web query data into the
        worksheet. Relevant when sourceData is True.'''
        raise NotImplementedError()
    
    @html_format.setter
    def html_format(self, value : aspose.cells.externalconnections.HtmlFormatHandlingType) -> None:
        '''How to handle formatting from the HTML source when bringing web query data into the
        worksheet. Relevant when sourceData is True.'''
        raise NotImplementedError()
    
    @property
    def is_same_settings(self) -> bool:
        '''Flag indicating whether to parse all tables inside a PRE block with the same width settings
        as the first row.'''
        raise NotImplementedError()
    
    @is_same_settings.setter
    def is_same_settings(self, value : bool) -> None:
        '''Flag indicating whether to parse all tables inside a PRE block with the same width settings
        as the first row.'''
        raise NotImplementedError()
    
    @property
    def edit_web_page(self) -> str:
        '''The URL of the user-facing web page showing the web query data. This URL is persisted
        in the case that sourceData="true" and url has been redirected to reference an XML file.
        Then the user-facing page can be shown in the UI, and the XML data can be retrieved
        behind the scenes.'''
        raise NotImplementedError()
    
    @edit_web_page.setter
    def edit_web_page(self, value : str) -> None:
        '''The URL of the user-facing web page showing the web query data. This URL is persisted
        in the case that sourceData="true" and url has been redirected to reference an XML file.
        Then the user-facing page can be shown in the UI, and the XML data can be retrieved
        behind the scenes.'''
        raise NotImplementedError()
    
    @property
    def edit_page(self) -> str:
        '''The URL of the user-facing web page showing the web query data. This URL is persisted
        in the case that sourceData="true" and url has been redirected to reference an XML file.
        Then the user-facing page can be shown in the UI, and the XML data can be retrieved
        behind the scenes.'''
        raise NotImplementedError()
    
    @edit_page.setter
    def edit_page(self, value : str) -> None:
        '''The URL of the user-facing web page showing the web query data. This URL is persisted
        in the case that sourceData="true" and url has been redirected to reference an XML file.
        Then the user-facing page can be shown in the UI, and the XML data can be retrieved
        behind the scenes.'''
        raise NotImplementedError()
    
    @property
    def is_consecutive(self) -> bool:
        '''Flag indicating whether consecutive delimiters should be treated as just one delimiter.'''
        raise NotImplementedError()
    
    @is_consecutive.setter
    def is_consecutive(self, value : bool) -> None:
        '''Flag indicating whether consecutive delimiters should be treated as just one delimiter.'''
        raise NotImplementedError()
    

class ConnectionDataSourceType:
    '''Specifies external database source type'''
    
    ODBC_BASED_SOURCE : ConnectionDataSourceType
    '''ODBC-based source'''
    DAO_BASED_SOURCE : ConnectionDataSourceType
    '''DAO-based source'''
    FILE_BASED_DATA_BASE_SOURCE : ConnectionDataSourceType
    '''File based database source'''
    WEB_QUERY : ConnectionDataSourceType
    '''Web query'''
    OLEDB_BASED_SOURCE : ConnectionDataSourceType
    '''OLE DB-based source'''
    TEXT_BASED_SOURCE : ConnectionDataSourceType
    '''Text-based source'''
    ADO_RECORD_SET : ConnectionDataSourceType
    '''ADO record set'''
    DSP : ConnectionDataSourceType
    '''DSP'''
    OLEDB_DATA_MODEL : ConnectionDataSourceType
    '''OLE DB data source created by the Spreadsheet Data Model.'''
    DATA_FEED_DATA_MODEL : ConnectionDataSourceType
    '''Data feed data source created by the Spreadsheet Data Model.'''
    WORKSHEET_DATA_MODEL : ConnectionDataSourceType
    '''Worksheet data source created by the Spreadsheet Data Model.'''
    TABLE : ConnectionDataSourceType
    '''Worksheet data source created by the Spreadsheet Data Model.'''
    TEXT_DATA_MODEL : ConnectionDataSourceType
    '''Text data source created by the Spreadsheet Data Model.'''
    UNKNOWN : ConnectionDataSourceType
    '''Text data source created by the Spreadsheet Data Model.'''

class ConnectionParameterType:
    '''Specifies the parameter type of external connection'''
    
    CELL : ConnectionParameterType
    '''Get the parameter value from a cell on each refresh.'''
    PROMPT : ConnectionParameterType
    '''Prompt the user on each refresh for a parameter value.'''
    VALUE : ConnectionParameterType
    '''Use a constant value on each refresh for the parameter value.'''

class CredentialsMethodType:
    '''Specifies Credentials method used for server access.'''
    
    INTEGRATED : CredentialsMethodType
    '''Integrated Authentication'''
    NONE : CredentialsMethodType
    '''No Credentials'''
    PROMPT : CredentialsMethodType
    '''Prompt Credentials'''
    STORED : CredentialsMethodType
    '''Stored Credentials'''

class ExternalConnectionClassType:
    '''Represents the type of connection'''
    
    DATABASE : ExternalConnectionClassType
    '''ODBC or OLE DB'''
    WEB_QUERY : ExternalConnectionClassType
    '''Web query'''
    TEXT_BASED : ExternalConnectionClassType
    '''Based on text'''
    DATA_MODEL : ExternalConnectionClassType
    '''Data model'''
    UNKOWN : ExternalConnectionClassType

class HtmlFormatHandlingType:
    '''Specifies how to handle formatting from the HTML source'''
    
    ALL : HtmlFormatHandlingType
    '''Transfer all HTML formatting into the worksheet along with data.'''
    NONE : HtmlFormatHandlingType
    '''Bring data in as unformatted text (setting data types still occurs).'''
    RTF : HtmlFormatHandlingType
    '''Translate HTML formatting to rich text formatting on the data brought into the worksheet.'''

class OLEDBCommandType:
    '''Specifies the OLE DB command type.'''
    
    NONE : OLEDBCommandType
    '''The command type is not specified.'''
    CUBE_NAME : OLEDBCommandType
    '''Specifies a cube name'''
    SQL_STATEMENT : OLEDBCommandType
    '''Specifies a SQL statement'''
    TABLE_NAME : OLEDBCommandType
    '''Specifies a table name'''
    DEFAULT_INFORMATION : OLEDBCommandType
    '''Specifies that default information has been given, and it is up to the provider how to interpret.'''
    WEB_BASED_LIST : OLEDBCommandType
    '''Specifies a query which is against a web based List Data Provider.'''
    TABLE_COLLECTION : OLEDBCommandType
    '''Specifies the table list.'''

class ReConnectionMethodType:
    '''Specifies what the spreadsheet application should do when a connection fails.'''
    
    REQUIRED : ReConnectionMethodType
    '''On refresh use the existing connection information and if it ends up being invalid
    then get updated connection information, if available from the external connection file.'''
    ALWAYS : ReConnectionMethodType
    '''On every refresh get updated connection information from the external connection file,
    if available, and use that instead of the existing connection information.
    In this case the data refresh will fail if the external connection file is unavailable.'''
    NEVER : ReConnectionMethodType
    '''Never get updated connection information from the external connection file
    even if it is available and even if the existing connection information is invalid'''

class SqlDataType:
    '''Specifies SQL data type of the parameter. Only valid for ODBC sources.'''
    
    SQL_UNSIGNED_OFFSET : SqlDataType
    '''sql unsigned offset'''
    SQL_SIGNED_OFFSET : SqlDataType
    '''sql signed offset'''
    SQL_GUID : SqlDataType
    '''sql guid'''
    SQL_W_LONG_VARCHAR : SqlDataType
    '''sql wide long variable char'''
    SQL_W_VARCHAR : SqlDataType
    '''sql wide variable char'''
    SQL_W_CHAR : SqlDataType
    '''sql wide char'''
    SQL_BIT : SqlDataType
    '''sql bit'''
    SQL_TINY_INT : SqlDataType
    '''sql tiny int'''
    SQL_BIG_INT : SqlDataType
    '''sql big int'''
    SQL_LONG_VAR_BINARY : SqlDataType
    '''sql long variable binary'''
    SQL_VAR_BINARY : SqlDataType
    '''sql variable binary'''
    SQL_BINARY : SqlDataType
    '''sql binary'''
    SQL_LONG_VAR_CHAR : SqlDataType
    '''sql long variable char'''
    SQL_UNKNOWN_TYPE : SqlDataType
    '''sql unknown type'''
    SQL_CHAR : SqlDataType
    '''sql char'''
    SQL_NUMERIC : SqlDataType
    '''sql numeric'''
    SQL_DECIMAL : SqlDataType
    '''sql decimal'''
    SQL_INTEGER : SqlDataType
    '''sql integer'''
    SQL_SMALL_INT : SqlDataType
    '''sql small int'''
    SQL_FLOAT : SqlDataType
    '''sql float'''
    SQL_REAL : SqlDataType
    '''sql real'''
    SQL_DOUBLE : SqlDataType
    '''sql double'''
    SQL_TYPE_DATE : SqlDataType
    '''sql date type'''
    SQL_TYPE_TIME : SqlDataType
    '''sql time type'''
    SQL_TYPE_TIMESTAMP : SqlDataType
    '''sql timestamp type'''
    SQL_VAR_CHAR : SqlDataType
    '''sql variable char'''
    SQL_INTERVAL_YEAR : SqlDataType
    '''sql interval year'''
    SQL_INTERVAL_MONTH : SqlDataType
    '''sql interval month'''
    SQL_INTERVAL_DAY : SqlDataType
    '''sql interval day'''
    SQL_INTERVAL_HOUR : SqlDataType
    '''sql interval hour'''
    SQL_INTERVAL_MINUTE : SqlDataType
    '''sql interval minute'''
    SQL_INTERVAL_SECOND : SqlDataType
    '''sql interval second'''
    SQL_INTERVAL_YEAR_TO_MONTH : SqlDataType
    '''sql interval year to month'''
    SQL_INTERVAL_DAY_TO_HOUR : SqlDataType
    '''sql interval day to hour'''
    SQL_INTERVAL_DAY_TO_MINUTE : SqlDataType
    '''sql interval day to minute'''
    SQL_INTERVAL_DAY_TO_SECOND : SqlDataType
    '''sql interval day to second'''
    SQL_INTERVAL_HOUR_TO_MINUTE : SqlDataType
    '''sql interval hour to minute'''
    SQL_INTERVAL_HOUR_TO_SECOND : SqlDataType
    '''sql interval hour to second'''
    SQL_INTERVAL_MINUTE_TO_SECOND : SqlDataType
    '''sql interval minute to second'''

