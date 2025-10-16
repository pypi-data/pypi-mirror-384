"""
Server class for data

When the dataserver is initialize, if there is elements in the 
"""
from typing import  Union, List

import os
import copy
import socketio
import shutil

from datablender.base import (
    DataConfiguration,
    Connection,
    QueryBuilder
)

from datablender.database import (
    Database,
    Role,
    Schema,
    Extension,
    Table,
    View,
    Function,
    mode_level
)

from datablender.data.dataProcess import DataProcess
from datablender.data.dataSource import DataSource

class DataServer:
    """A server that contains databases

    Attributes:
    ----------
        host (str): Server's host.
        port (str): Server's port.
        dialect (str) : Host of the server

    Methods:
    ----------
        getConnection(self) -> None : Get default database

    Examples:
    ----------
        >>> import datablender
        
    """
    def __init__(
        self,
        host:str = 'localhost',
        port:int = 5432,
        user_name:str = 'postgres',
        password:str = None,
        activate_data_config:bool = True,
        data_configuration_host:str = 'localhost',
        data_configuration_port:int = None,
        event_server:socketio.Server = None
    ):

        self.host=os.getenv('database_host',host)
        self.port=os.getenv('database_port',port)
        self.user_name=os.getenv('username',user_name)
        self.password=os.getenv('password',password)
        
        self.data_directory = os.getenv('data_directory')

        self.data_configuration = DataConfiguration(
            data_configuration_host,
            data_configuration_port,
            active=activate_data_config
        )

        self.event_server = event_server

        self.database: List[Database] = []
        self.role: List[Role] = []
        self.data_source: List[DataSource] = []
        self.data_process: List[DataProcess] = []
    
        self.connection = self.getConnection()
        
        self.query_builder = QueryBuilder(
            self.connection
        )

        self.manageDefaultsElements()

        self.data_configuration.getAllElements()

        for element_type in [
            'database',
            'role',
            'data_source',
            'data_process'
        ]:
            self.manageElements(element_type)

        self.disconnect()

    def connect(self) -> None:
        
        if self.connection:
            self.connection.connect()
        {
            database.connection.connect()
            for database in self.database
        }
    
    def disconnect(self) -> None:
        """Disconnect from data server.
        """
        
        {
            database.connection.close()
            for database in self.database
        }

        if self.connection:
            self.connection.close()

        for data_source in self.data_source:

            for temporary_directory in data_source.core.temporary_main_files:
                shutil.rmtree(temporary_directory.get(
                    'temporary_directory_name'
                ))
                
            data_source.core.temporary_main_files = []
    
    def getConnection(
        self,
        database_name:str='postgres'
    ) -> Connection:
        """Get connection to the data server.

        Raises:
            Exception: Error if there's no default database.

        Returns:
            Connection: Connection to a database
        """
        return Connection(
            self.host,
            self.port,
            database_name,
            self.user_name,
            self.password,
            'postgres'
        )

    def manageElements(
        self,
        element_type:str,
        **kwargs
    ) -> None:

        if element_type in ['role','data_source','data_process','database']:
            if not self.data_configuration.active:
                elements = self.query_builder.selectElements(
                    element_type
                ).execute().to_dict('records')

            elif element_type == 'database':
                elements = [
                    {'name':level} for level in mode_level
                    if level not in ['inactive','inexistant']
                ]
          
            else:
                elements = copy.deepcopy(getattr(
                    self.data_configuration,
                    element_type,
                    []
                ))

            [
                self.manageElement(element,element_type)
                for element in elements
            ]

        else:
            for database in self.database:
                database.manageElements(
                    element_type,
                    **kwargs
                )

    def getElements(
        self,
        element_type:str,
        **kwargs
    ) -> List[dict]:
        
        self.manageElements(
            element_type,
            **kwargs
        )

        if self.data_configuration.active:
            elements = copy.deepcopy(getattr(
                self.data_configuration.getElements(
                    element_type,
                    **kwargs
                ),
                element_type
            ))

            if element_type in ['schema','table','view']:
                return [
                    self.getSizes(element,element_type)
                    for element in elements
                ]
            
            return elements   
                    
        else:
            pass
    
    def getSizes(
        self,
        element:dict,
        element_type:str
    ) -> dict:
        
        if element_type in ['schema','table','view']:
            
            element['sizes']= {}
            
            for database in self.database:
                
                if element_type =='schema':
                    element['sizes'][database.name] = next(
                        (
                            schema.size
                            for schema in database.schema
                            if schema.name == element['name']
                        ),
                        None
                    )
                
                else:

                    for schema in database.schema:
                        element['sizes'][database.name] = next(
                            (
                                db_element.size
                                for db_element in getattr(schema,element_type)
                                if db_element.name == element['name'] and element['schema_id'] == schema.id
                            ),
                            None
                        )
        return element

    def initiateElement(
        self,
        configuration:dict,
        element_type:str
    ) -> Union[Role,Database,DataSource,DataProcess]:
        
        if element_type== 'database':
            return Database(
                self.getConnection(),
                data_configuration=self.data_configuration,
                event_server = self.event_server,
                **configuration
            )
        
        elif element_type== 'role':

            return Role(
                self.connection,
                data_configuration=self.data_configuration,
                event_server = self.event_server,
                **configuration
            )
        
        elif element_type== 'data_source':
            
            database = next(
                database for database in self.database
                if database.name == configuration.get('status')
            )

            return DataSource(
                database.connection,
                self.data_configuration,
                event_server=self.event_server,
                database = database,
                **configuration
            )
    
        elif element_type== 'data_process':
            
            database = next(
                database for database in self.database
                if database.name == configuration.get('status')
            )

            return DataProcess(
                database.connection,
                database = database,
                data_configuration=self.data_configuration,
                event_server=self.event_server,
                **configuration
            )
        
    def getElement(
        self,
        element_type:str,
        configuration:dict
    ) -> Union[
        Database,
        Schema,
        Extension,
        Role,
        Table,
        View,
        Function,
        None
    ]:
        if element_type in ['data_source','role','data_process','database']:
            for attribute_name in ['id','name']:

                attribute_value = configuration.get(attribute_name)

                element = next(
                    (
                        element for element in getattr(self,element_type)
                        if getattr(element,attribute_name) == attribute_value
                    ),
                    None
                ) if attribute_name in configuration and attribute_value else None

                if element is not None:
                    return element
        else:

            return self.database[0].getElement(
                configuration,
                element_type
            )

    def manageElement(
        self,
        configuration:dict,
        element_type:str,
        manage_from:str='database'
    ) -> Union[
        Schema,
        Extension,Table,View,
        Function,DataSource,DataProcess
    ]:
        """Manage an element in the dataserver. The element is search by
        the name or the id in the configuration.

        If it is not found, the element is initialize.

        Args:
            configuration (dict): configuration.
            element_type (str): type of the element (table, extension).
            manage_from (str, optional): indicate from what the element is manage 
                either from the database, the data configuration or the values.
                Defaults to False.

        Returns:
            Union[Schema,Extension]: the element.
        """

        ## When data source or data process is managed, change the database if necessary

        if element_type in ['data_source','role','data_process','database']:
            # Check if element exists in the list of elements
            element = self.getElement(
                element_type,
                configuration
            )

            # If it does not, initiate it, add it to the elements list and manage it
            if element is None:

                element = self.initiateElement(
                    configuration,
                    element_type
                )
                configuration = {}
                getattr(self,element_type).append(element)
            
            # Manage the element
            element.manage(
                manage_from,
                configuration
            )

            if element.status == 'inexistant':
                setattr(
                    self,
                    element_type,
                    [
                        element_ for element_ in getattr(self,element_type)
                        if getattr(element,'id') != getattr(element_,'id')
                    ]
                )

        else:
            configuration.pop('sizes',None)

            for database in self.database:
                element = database.manageElement(
                    configuration,
                    element_type,
                    manage_from
                )

        self.manageForeignAttributes()

        if (
            self.data_configuration.active
            and element_type == 'table'
            and element.status == 'inexistant'
        ):
            for data_source in self.data_source:
                index = next((
                    i for i, table in enumerate(data_source.core.tables)
                    if table.id == element.id
                ), None)
                if index is not None:
                    del data_source.core.tables[index]

                data_source.manage(manage_from='values')

        return element
    
    def manageForeignAttributes(self) -> None:
        if self.data_configuration.active:

            [
                role.manageAttributes()
                for role in self.role
            ]
            [
                data_source.core.manageAttributes()
                for data_source in self.data_source
            ]

            for database in self.database:
                database.manageForeignAttributes()

    def dataSourceAction(
        self,
        id:int = None,
        **kwargs
    ):
        return getattr(
            self.getElement(
                'data_source',
                {'id':id}
            ),
            kwargs.pop('action_name')
        )(**kwargs) if id else None

    def process(
        self,
        id:int = None,
        **kwargs
    ) -> None:
        return getattr(
            self.getElement(
                'data_process',
                {'id':id}
            ),
            kwargs.pop('action_name')
        )(**kwargs) if id else None
    
    def manageDefaultsElements(self) -> None:
        elements = self.query_builder.config['elements']

        for element_type in elements:
            if 'defaults' in elements[element_type] and element_type =='role':
                for default in elements[element_type]['defaults']:
                    self.manageElement(
                        default,
                        element_type
                    )

        self.manageForeignAttributes()
