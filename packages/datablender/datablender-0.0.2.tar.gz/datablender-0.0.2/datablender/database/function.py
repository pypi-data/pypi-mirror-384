"""

"""
from __future__ import annotations

from datablender.base import (
    Connection,
    DataConfiguration,
    File,
    AsyncConnection,
    AsyncDataConfiguration
)
from datablender.database.elementSQL import SchemaElement,AsyncSchemaElement

class Function(SchemaElement):
    """Represent a schema in a database

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        name (str): Element's name.
        schema_name (str): Element's schema name.
        owner (str): Element's owner.
        status (str): Element's status (developpement, test, production).
        query_builder (QueryBuilder): .
        elements_list (pandas.Dataframe): .
        exists (bool) : .
        should_exists (bool) : .

    Methods:
    ----------
        create (self) -> None: Create the element
        drop (self) -> None: 
        setOwner (self) -> None:
        rename (self) -> None:

    """
    def __init__(
        self,
        connection:Connection,
        name:str,
        function_statement:str = None,
        file_function_statement:str = None,
        directory_function_statement:str = None,
        routine_type:str=None,
        schema_name:str = 'public',
        owner:str = 'postgres',
        status:str = 'default',
        data_configuration:DataConfiguration = None,
        acticvate_data_config:bool = False,
        id:int = None,
        content:dict=None,
        event_server=None
    ):
        super(Function,self).__init__(
            connection,
            name,
            schema_name,
            'function',
            owner,
            status,
            data_configuration,
            acticvate_data_config,
            id,
            content,
            event_server
        )
        
        self.function_statement= function_statement
        self.file_function_statement= file_function_statement
        self.directory_function_statement= directory_function_statement
        self.routine_type= routine_type

        self.directory = None#CodeDirectory(self.directory_function_statement,self.schema_name,datablender_structure)

        self.configuration_attributes = [
            'name','status','id','content','function_statement','file_function_statement','directory_function_statement','schema_name'
        ]
        self.database_config_attributes = ['owner','routine_type']
        self.database_attributes = ['owner']

    @property
    def function_statement(self) -> None:
    
        if self.function_statement:
            return self.function_statement
        
        elif self.directory_function_statement and self.file_function_statement:
            return File(self.directory_function_statement,self.file_function_statement+'.sql').read().content

        elif self.file_function_statement:
            return File(self.directory.query_directory.name,self.file_function_statement+'.sql').read().content

    def manage(self,from_values:bool=False) -> Function:
        """Manage the schema in the database and in the configuration.

        Args:
            from_values (bool, optional): Manage from the given values at the initiation. Defaults to False.

        Returns:
            Schema: self.
        """

        self.manageInConfig(False,from_values)
        
        if self.exists and self.should_exists:
            self.setDatabaseAttributes()
            self.manageInConfig(True,False)

        elif not self.exists and self.should_exists:

            self.create()
            self.setOwner()

        elif self.exists and not self.should_exists:
            self.drop()
        
        return self

    def create(self):
        """Create the element.
        """
        self.query_builder.create(
            self.name,
            'function',
            self.schema_name
        ).built().execute()
        self.getDBElements()
        self.data_logging.logEvent('function',self.name,'create',self.schema_name)
    
    def drop(self,exists_condition:bool=False):
        """Drop element

        Args:
            exists_condition (bool, optional): Add exists statement to the . Defaults to False.
        """
        self.query_builder.drop(
            self.name,
            'function',
            self.schema_name,
            exists_condition=exists_condition
        ).built().execute()
        self.getDBElements()
        self.data_logging.logEvent('function',self.name,'drop',self.schema_name)

    def setOwner(self,owner:str=None) -> None:
        """Set element owner.

        Args:
            owner (str, optional): Owner name. Defaults to None.
        """
        if owner:
            self.owner=owner

        self.query_builder.alter(
            self.name,
            self.element_type,
            self.schema_name,
        ).owner(self.owner).built().execute()

        self.data_logging.logEvent(self.element_type,self.name,'owner')

        self.manageInConfig(True,True)

class AsyncFunction(AsyncSchemaElement):
    """Represent a schema in a database

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        name (str): Element's name.
        schema_name (str): Element's schema name.
        owner (str): Element's owner.
        status (str): Element's status (developpement, test, production).
        query_builder (QueryBuilder): .
        elements_list (pandas.Dataframe): .
        exists (bool) : .
        should_exists (bool) : .

    Methods:
    ----------
        create (self) -> None: Create the element
        drop (self) -> None: 
        setOwner (self) -> None:
        rename (self) -> None:

    """
    def __init__(
        self,
        connection:AsyncConnection,
        name:str,
        function_statement:str = None,
        file_function_statement:str = None,
        directory_function_statement:str = None,
        routine_type:str=None,
        schema_name:str = 'public',
        owner:str = 'postgres',
        status:str = 'default',
        data_configuration:AsyncDataConfiguration = None,
        acticvate_data_config:bool = False,
        id:int = None,
        content:dict=None,
        event_server=None
    ):
        super(AsyncFunction,self).__init__(
            connection,
            name,
            schema_name,
            'function',
            owner,
            status,
            data_configuration,
            acticvate_data_config,
            id,
            content,
            event_server
        )
        
        self.function_statement= function_statement
        self.file_function_statement= file_function_statement
        self.directory_function_statement= directory_function_statement
        self.routine_type= routine_type

        self.directory = None#CodeDirectory(self.directory_function_statement,self.schema_name,datablender_structure)

        self.configuration_attributes = [
            'name','status','id','content','function_statement','file_function_statement','directory_function_statement','schema_name'
        ]
        self.database_config_attributes = ['owner','routine_type']
        self.database_attributes = ['owner']

    @property
    def function_statement(self) -> None:
    
        if self.function_statement:
            return self.function_statement
        
        elif self.directory_function_statement and self.file_function_statement:
            return File(self.directory_function_statement,self.file_function_statement+'.sql').read().content

        elif self.file_function_statement:
            return File(self.directory.query_directory.name,self.file_function_statement+'.sql').read().content
    
    async def initiate(self) -> AsyncFunction:
        await self.data_logging.manageTable()
        await self.manageAttributes()
        self.data_logging.updateConfiguration(
            self.configuration,
            self.element_type
        )
        await self.getDBElement()

        return self
    
    async def manage(
        self,
        manage_from:str='database',
        new_configuration:dict={},
        data_logging_action:dict={},
        ignore_new_config:bool = False
    ) -> Function:
        """Manage the schema in the database and in the configuration.

        Args:
            from_values (bool, optional): Manage from the given values at the initiation. Defaults to False.

        Returns:
            Schema: self.
        """

        await self.setManageParameters(
            manage_from,
            new_configuration,
            data_logging_action,
            ignore_new_config
        )
       
        if not self.db_element and self.should_exists:

            await self.manageInConfig()
            self.data_logging.updateConfiguration(
                self.configuration,
                self.element_type
            )
            await self.create()
            await self.manageAttributes('database')

        else:
            self.data_logging.setActionName('manage',self.id)
            if self.db_element and self.should_exists:
            
                await self.manageAttributes(
                    'values'
                    if self.manage_from == 'database'
                    else 'database'
                )
            elif self.db_element and not self.should_exists:
                await self.drop()
        
            await self.manageInConfig()

        return self

    async def create(self):
        """Create the element.
        """
        
        await self.data_logging.logEvent(
            'create',
            'loading'
        )
        
        await self.query_builder.create(
            self.name,
            self.element_type,
            self.schema_name
        ).built().asyncExecute()
            
        await self.getDBElement()
        
        await self.data_logging.logEvent(
            'create',
            'loaded'
        )
