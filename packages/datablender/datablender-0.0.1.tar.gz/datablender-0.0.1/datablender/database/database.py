"""

"""
from __future__ import annotations
from typing import List,Union

import copy

from datablender.base import (
    Connection,
    DataLogging,
    DataConfiguration,
    Data,
    AsyncConnection,
    AsyncDataConfiguration,
    AsyncDataLogging
)

from datablender.database import mode_level
from datablender.database.elementSQL import DatabaseElement, AsyncDatabaseElement
from datablender.database.schema import Schema, AsyncSchema
from datablender.database.extension import Extension, AsyncExtension
from datablender.database.table import Table,AsyncTable
from datablender.database.view import View,AsyncView
from datablender.database.function import Function,AsyncFunction

class Database(DatabaseElement):
    """Represent a single database.

    When you initiate a database,

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        name (str): Element's name.
        owner (str): Element's owner.
        status (str): Element's status (developpement, test, production).
        query_builder (QueryBuilder): .
        databases (pandas.Dataframe): .
        exists (bool) : .
        should_exists (bool) : .
        grants (list): Privileges to grant to the database.

    Methods:
    ----------
        manage (self) -> None: Manage the database, create it or delete it depending on whether it exists and if it should exist .
        create (self) -> None: Create the database.
        drop (self) -> None: Drop the database.
        setOwner (self) -> None: Set database owner.
        rename (self) -> None: Rename the database.
        createSchemas (self) -> None: Create schemas.
        createTables (self) -> None: Create tables.

    Examples:
    ----------
        >>> import datablender
        
    """
    def __init__(
        self,
        connection:Connection,
        name:str = 'postgres',
        owner:str = 'postgres',
        status:str = 'default',
        data_configuration:DataConfiguration = None,
        acticvate_data_config:bool = False,
        grants:list = [],
        event_server=None,
        owner_id:int = None
    ):
        """Initiate the database by checking  if it exists, and creating schemas, roles, tables, views and functions

        Args:
            connection (Connection): Connection to a database.
            name (str, optional): Database name. Defaults to 'postgres'.
            owner (str, optional): Database owner. Defaults to 'postgres'.
            status (str, optional): Database status. Defaults to 'developpement'.
            connect (bool, optional): Change the connection database to this database. Defaults to False.
            data_configuration (DataConfiguration, optional): Data configuration. Defaults to None.
            acticvate_data_config (bool, optional): Is the data configuration is active. Defaults to False.
            grants (list, optional): Privileges to grant to the database. Defaults to [].
        """
        # If the name of the database is developpement, test or production,
        # then the status is change accorrding to the database name
        if name in [level for level in mode_level if level != 'inactive']:
            status=copy.deepcopy(name)

        super(Database,self).__init__(
            connection,
            name,
            'database',
            status,
            data_configuration,
            acticvate_data_config,
            event_server=event_server
        )
        
        self.owner = owner
        self.owner_id = owner_id
        self.grants = grants

        self.schema: List[Schema] = []
        self.extension: List[Extension] = []

        self.manageAttributes()
        self.getDBElement()

    @property
    def connected(self) -> bool:
        """Check if database is connected.

        Returns:
            bool: indicate if it's connected.
        """
        return (
            self.name == self.connection.database_name 
            and self.connection.connection.closed == 0
        )

    def manage(
        self,
        manage_from:str='database',
        new_configuration:dict={},
        connect:bool=True
    ) -> Database:
        """Manage the database.
        """ 

        manage_from=self.setManager(
            manage_from,
            None
        )

        if not self.db_element and self.should_exists:
            self.create()

            if connect and not self.connected:
                self.connection.setDatabase(self.name)
                self.manageDefaultsElements()
                
                self.data_logging = DataLogging(
                    self.connection,
                    self.data_logging.event_server
                )
                self.data_logging.setElement(
                    'database',
                    self.name
                )

            self.manageAttributes('database')

        elif self.db_element and self.should_exists:

            if connect and not self.connected:
                self.connection.setDatabase(self.name)

                self.manageDefaultsElements()
                
                self.data_logging = DataLogging(
                    self.connection,
                    self.data_logging.event_server
                )
                self.data_logging.setElement(
                    'database',
                    self.name
                )
   
            self.manageAttributes(
                'database'if self.manage_from != 'database' else 'values'
            )
            
        elif self.db_element and not self.should_exists:
            self.drop()

        return self

    def create(self) -> None:
        """Create the database.
        """
        self.data_logging.logEvent(
            'create',
            'loading'
        )
        self.connection.setIsolationLevel('auto')
        
        self.query_builder.create(
            self.name,
            'database'
        ).built().execute(False)
        
        self.connection.setIsolationLevel()

        self.getDBElement()      
        
        self.data_logging.logEvent(
            'create',
            'loaded'
        )
    
    def drop(
        self,
        exists_condition:bool=False
    ) -> None:
        """Drop the database.

        Args:
            exists_condition (bool, optional): Add exists statement to the . Defaults to False.
        """
        
        self.data_logging.logEvent(
            'drop',
            'loading'
        )
        self.connection.getDefaultConnection()
        self.connection.setIsolationLevel('auto')
        self.query_builder.drop(
            self.name,
            'database',
            exists_condition=exists_condition
        ).built().execute(False)
        
        self.db_element = {}   
        self.data_logging.logEvent(
            'drop',
            'loaded'
        )  
        self.connection.close()

    def rename(
        self,
        new_name:str=None
    ) -> None:
        """Rename the element.

        Args:
            new_name (str): New name.
        """

        self.data_logging.logEvent(
            'rename',
            'loading'
        )
        if new_name:
            self.name = new_name
        
        self.query_builder.alter(
            self.db_element.get('name'),
            self.element_type
        ).rename(
            self.name
        ).built().execute()

        self.db_element['name'] = copy.deepcopy(self.name)

        self.data_logging.logEvent(
            'rename',
            'loaded'
        )
    
    def setOwner(
        self,
        owner:str=None
    ) -> None:
        """Set element owner

        Args:
            owner (str, optional): Owner name. Defaults to None.
        """
        self.data_logging.logEvent(
            'owner',
            'loading'
        )
        if owner:
            self.owner=owner

        self.query_builder.alter(
            self.name,
            self.element_type,
        ).owner(
            self.owner
        ).built().execute()

        self.db_element['owner'] = copy.deepcopy(self.owner)
        self.data_logging.logEvent(
            'owner',
            'loaded'
        )

    def manageGrants(self):
        """Grant database privileges.
        """
        self.data_logging.logEvent(
            'grant',
            'loading'
        )
        db_grants:List[dict] = copy.deepcopy(
            self.db_element.get('grants')
        )

        for grant in self.grants:
            if grant in db_grants:
                db_grants.remove(grant)
            else:
                self.query_builder.grant(
                    self.name,
                    self.element_type,
                    **grant
                ).built().execute()

        for revoke in db_grants:
            self.query_builder.revoke(
                self.name,
                self.element_type,
                **revoke   
            ).built().execute()

        self.db_element['grants'] = copy.deepcopy(self.grants)
        self.data_logging.logEvent(
            'grant',
            'loaded'
        )

    def manageElements(
        self,
        element_type:str,
        **kwargs:dict
    ) -> None:
        
        self.data_configuration.getElements(element_type)
        
        if element_type in ['schema','extension']:
            elements = self.query_builder.selectElements(
                element_type
            ).execute().to_dict('records')

            if self.data_configuration.active:

                for element in getattr(
                    self.data_configuration,
                    element_type,
                    []
                ):                    
                    element_index = next((
                        i for i, item in enumerate(elements)
                        if item.get('id') == 'specific_id'
                    ), None)

                    if element_index is not None:
                        elements[element_index] = {
                            **copy.deepcopy(element),
                            **copy.deepcopy(elements[element_index])
                        }
                    else:
                        elements.append(element)

            [
                self.manageElement(element,element_type)
                for element in elements
            ]

        else:
            schema_id = kwargs.pop('schema_id',None)

            if schema_id is None:
                self.manageElements('schema')

                for schema in self.schema:
                    schema.manageElements(element_type)
            
            else:
                
                schema = self.getElement(
                    {'id':schema_id},
                    'schema'
                )

                if not schema:
                    schema = self.manageElement(
                        {'id':schema_id},
                        'schema'
                    )

                schema.manageElements(element_type)
            
    def initiateElement(
        self,
        configuration:dict,
        element_type:str
    ) -> Union[Schema,Extension]:
        
        if element_type== 'schema':

            return Schema(
                self.connection,
                data_configuration=self.data_configuration,
                event_server=self.data_logging.event_server,
                **configuration
            )
        
        elif element_type== 'extension':
            return Extension(
                self.connection,
                data_configuration=self.data_configuration,
                event_server=self.data_logging.event_server,
                **configuration
            )
        
    def getElement(
        self,
        configuration:dict,
        element_type:str
    ) -> Union[
        Schema,Extension,Table,View,Function,None
    ]:
        if element_type in ['schema','extension']:
            for attribute_name in ['id','name']:

                attribute_value = configuration.get(attribute_name)

                element = next((
                    element for element in getattr(self,element_type)
                    if getattr(element,attribute_name) == attribute_value),
                    None
                ) if attribute_name in configuration and attribute_value else None

                if element is not None:
                    return element

        else:
            schema_configuration = {
                'name':configuration.get('schema_name','public'),
                'id':configuration.get('schema_id',None),
                'status':configuration.get('status','developpement')
            }

            schema = self.getElement(
                schema_configuration,
                'schema'
            )
        
            return schema.getElement(
                configuration,
                element_type
            )
 
    def manageElement(
        self,
        configuration:dict,
        element_type:str,
        manage_from:str='database',
        default_configuration:dict = {},
        **kwargs
    ) -> Union[
        Schema,
        Extension,
        Table,
        View,
        Function
    ]:
        """Manage an element.

        Args:
            configuration (dict): configuration.
            element_type (str): type of the element (table, extension).
            from_values (bool, optional): manage elements from values in elements to set. Defaults to False.

        Returns:
            Union[Schema,Extension]: the element.
        """

        if element_type in ['schema','extension']:
            # Check if element exists in the list of elements
            element = self.getElement(
                configuration,
                element_type
            )

            # If it does not, initiate it, add it to the elements list
            if not element:

                element = self.initiateElement(
                    configuration,
                    element_type
                )
                configuration = {}
                getattr(self,element_type).append(element)

            element.manage(
                manage_from,
                configuration,
                **kwargs
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
                
            return element
        
        else:
            schema_configuration = {
                'name':configuration.get('schema_name','public'),
                'id':configuration.get('schema_id',None),
                'status':configuration.get('status','developpement')
            }

            schema = self.getElement(
                schema_configuration,
                'schema'
            )

            if not schema:
                schema = self.manageElement(
                    schema_configuration,
                    'schema'
                )

            return schema.manageElement(
                configuration,
                element_type,
                manage_from,
                default_configuration,
                **kwargs
            )

    def executeDataAction(
        self,
        element:dict,
        action_name:str,
        **kwargs
    ) -> Union[Data,None]:
        
        return self.manageElement(
            {'name':element.get('schema_name')},
            'schema'
        ).executeDataAction(
            element,action_name,**kwargs
        )
    
    def manageForeignAttributes(self) -> None:
        self.manageAttributes()
        
        [
            schema.manageForeignAttributes()
            for schema in self.schema
        ]
        [
            extension.manageAttributes()
            for extension in self.extension
        ]

    def manageDefaultsElements(self) -> None:
        elements = self.query_builder.config['elements']

        for element_type in elements:
            if 'defaults' in elements[element_type] and element_type !='role':
                for default in elements[element_type]['defaults']:
                    self.manageElement(
                        default,
                        element_type
                    )

        self.manageForeignAttributes()
                
class AsyncDatabase(AsyncDatabaseElement):
    """Represent a single database.

    When you initiate a database,

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        name (str): Element's name.
        owner (str): Element's owner.
        status (str): Element's status (developpement, test, production).
        query_builder (QueryBuilder): .
        databases (pandas.Dataframe): .
        exists (bool) : .
        should_exists (bool) : .
        grants (list): Privileges to grant to the database.

    Methods:
    ----------
        manage (self) -> None: Manage the database, create it or delete it depending on whether it exists and if it should exist .
        create (self) -> None: Create the database.
        drop (self) -> None: Drop the database.
        setOwner (self) -> None: Set database owner.
        rename (self) -> None: Rename the database.
        createSchemas (self) -> None: Create schemas.
        createTables (self) -> None: Create tables.

    Examples:
    ----------
        >>> import datablender
        
    """
    def __init__(
        self,
        connection:AsyncConnection,
        name:str = 'postgres',
        owner:str = 'postgres',
        status:str = 'default',
        data_configuration:AsyncDataConfiguration = None,
        acticvate_data_config:bool = False,
        grants:list = [],
        event_server=None,
        owner_id:int = None
    ):
        """Initiate the database by checking  if it exists, and creating schemas, roles, tables, views and functions

        Args:
            connection (Connection): Connection to a database.
            name (str, optional): Database name. Defaults to 'postgres'.
            owner (str, optional): Database owner. Defaults to 'postgres'.
            status (str, optional): Database status. Defaults to 'developpement'.
            connect (bool, optional): Change the connection database to this database. Defaults to False.
            data_configuration (DataConfiguration, optional): Data configuration. Defaults to None.
            acticvate_data_config (bool, optional): Is the data configuration is active. Defaults to False.
            grants (list, optional): Privileges to grant to the database. Defaults to [].
        """
        # If the name of the database is developpement, test or production,
        # then the status is change accorrding to the database name
        if name in [level for level in mode_level if level != 'inactive']:
            status=copy.deepcopy(name)

        super(AsyncDatabase,self).__init__(
            connection,
            name,
            'database',
            status,
            data_configuration,
            acticvate_data_config,
            event_server=event_server
        )
        
        self.owner = owner
        self.owner_id = owner_id
        self.grants = grants

        self.schema: List[Schema] = []
        self.extension: List[Extension] = []

    async def initiate(self) -> AsyncDatabase:
        await self.manageAttributes()
        await self.getDBElement()

        return self

    @property
    def connected(self) -> bool:
        """Check if database is connected.

        Returns:
            bool: indicate if it's connected.
        """
        return (
            self.name == self.connection.database_name 
            and not self.connection.connection.is_closed()
        )

    async def manage(
        self,
        manage_from:str='database',
        new_configuration:dict={},
        connect:bool=True,
        data_logging_action:dict={}
    ) -> AsyncDatabase:
        """Manage the database.
        """ 

        await self.setManageParameters(
            manage_from,
            None,
            data_logging_action
        )

        if not self.db_element and self.should_exists:
            await self.create()

            if connect and not self.connected:
                await self.connection.setDatabase(self.name)
                await self.manageDefaultsElements()
                await self.setDataLogging()

            await self.manageAttributes('database')

        elif self.db_element and self.should_exists:

            if connect and not self.connected:
                await self.connection.setDatabase(self.name)
                await self.manageDefaultsElements()
                await self.setDataLogging()

            await self.manageAttributes(
                'database'if self.manage_from != 'database' else 'values'
            )
            
        elif self.db_element and not self.should_exists:
            await self.drop()

        self.data_logging.action_name = None
        return self

    async def setDataLogging(self) -> None:
    
        self.data_logging = AsyncDataLogging(
            self.connection,
            self.element_type,
            self.data_logging.event_server
        )
        self.data_logging.element_configuration = self.configuration
        self.data_logging.setActionName(
            'manage',
            self.element_type,
            self.configuration
        )
        await self.data_logging.manageTable()

    async def create(self) -> None:
        """Create the database.
        """
        await self.data_logging.logEvent(
            'create',
            'loading'
        )

        await self.query_builder.create(
            self.name,
            'database'
        ).built().asyncExecute(
            False,
            False,
            data_logging = self.data_logging
        )

        await self.getDBElement()      
    
    async def drop(
        self,
        exists_condition:bool=False
    ) -> None:
        """Drop the database.

        Args:
            exists_condition (bool, optional): Add exists statement to the . Defaults to False.
        """
        
        await self.data_logging.logEvent(
            'drop',
            'loading'
        )
        await self.connection.getDefaultConnection()
        
        await self.query_builder.drop(
            self.name,
            'database',
            exists_condition=exists_condition
        ).built().asyncExecute(
            False,
            False,
            data_logging = self.data_logging
        )

        self.db_element = {}   
        await self.connection.close()

    async def rename(
        self,
        new_name:str=None
    ) -> None:
        """Rename the element.

        Args:
            new_name (str): New name.
        """

        await self.data_logging.logEvent(
            'rename',
            'loading'
        )
        if new_name:
            self.name = new_name
        
        await self.query_builder.alter(
            self.db_element.get('name'),
            self.element_type
        ).rename(
            self.name
        ).built().asyncExecute(
            data_logging = self.data_logging
        )

        self.db_element['name'] = copy.deepcopy(self.name)
    
    async def setOwner(
        self,
        owner:str=None
    ) -> None:
        """Set element owner

        Args:
            owner (str, optional): Owner name. Defaults to None.
        """
        await self.data_logging.logEvent(
            'owner',
            'loading'
        )
        if owner:
            self.owner=owner

        await self.query_builder.alter(
            self.name,
            self.element_type,
        ).owner(
            self.owner
        ).built().asyncExecute(
            data_logging = self.data_logging
        )

        self.db_element['owner'] = copy.deepcopy(self.owner)

    async def manageGrants(self):
        """Grant database privileges.
        """

        db_grants:List[dict] = copy.deepcopy(
            self.db_element.get('grants')
        )

        for grant in self.grants:
            if grant in db_grants:
                db_grants.remove(grant)
            else:
                await self.data_logging.logEvent(
                    'grant',
                    'loading',
                    informations=grant
                )
                await self.query_builder.grant(
                    self.name,
                    self.element_type,
                    **grant
                ).built().asyncExecute(
                    data_logging = self.data_logging
                )

        for revoke in db_grants:
            
            await self.data_logging.logEvent(
                'revoke',
                'loading',
                informations=revoke
            )
            await self.query_builder.revoke(
                self.name,
                self.element_type,
                **revoke   
            ).built().asyncExecute(
                data_logging = self.data_logging
            )

        self.db_element['grants'] = copy.deepcopy(self.grants)

    async def manageElements(
        self,
        element_type:str,
        **kwargs:dict
    ) -> None:
        
        await self.data_configuration.getElements(element_type)
        
        if element_type in ['schema','extension']:

            elements = await self.query_builder.selectElements(
                element_type
            ).asyncExecute()

            elements = elements.to_dict('records')

            if self.data_configuration.active:
                for element in getattr(
                    self.data_configuration,
                    element_type,
                    []
                ):                    
                    element_index = next((
                        i for i, item in enumerate(elements)
                        if item.get('id') == 'specific_id'
                    ), None)

                    if element_index is not None:
                        elements[element_index] = {
                            **copy.deepcopy(element),
                            **copy.deepcopy(elements[element_index])
                        }
                    else:
                        elements.append(element)

            [
                await self.manageElement(element,element_type)
                for element in elements
            ]

        else:
            schema_id = kwargs.pop('schema_id',None)

            if schema_id is None:
                await self.manageElements('schema')

                for schema in self.schema:
                    await schema.manageElements(element_type)
            
            else:
                
                schema = self.getElement(
                    {'id':schema_id},
                    'schema'
                )

                if not schema:
                    schema = await self.manageElement(
                        {'id':schema_id},
                        'schema'
                    )

                await schema.manageElements(element_type)
            
    async def initiateElement(
        self,
        configuration:dict,
        element_type:str
    ) -> Union[AsyncSchema,AsyncExtension]:
        
        if element_type== 'schema':

            return await AsyncSchema(
                self.connection,
                data_configuration=self.data_configuration,
                event_server=self.data_logging.event_server,
                **configuration
            ).initiate()
        
        elif element_type== 'extension':
            return await AsyncExtension(
                self.connection,
                data_configuration=self.data_configuration,
                event_server=self.data_logging.event_server,
                **configuration
            ).initiate()
        
    def getElement(
        self,
        configuration:dict,
        element_type:str
    ) -> Union[
        AsyncSchema,AsyncExtension,AsyncTable,AsyncView,AsyncFunction,None
    ]:
        if element_type in ['schema','extension']:
            for attribute_name in ['id','name']:

                attribute_value = configuration.get(attribute_name)

                element = next((
                    element for element in getattr(self,element_type)
                    if getattr(element,attribute_name) == attribute_value),
                    None
                ) if attribute_name in configuration and attribute_value else None

                if element is not None:
                    return element

        else:
            schema_configuration = {
                'name':configuration.get('schema_name','public'),
                'id':configuration.get('schema_id',None),
                'status':configuration.get('status','developpement')
            }

            schema = self.getElement(
                schema_configuration,
                'schema'
            )
        
            return schema.getElement(
                configuration,
                element_type
            )
 
    async def manageElement(
        self,
        configuration:dict,
        element_type:str,
        manage_from:str='database',
        **kwargs
    ) -> Union[
        AsyncSchema,
        AsyncExtension,
        AsyncTable,
        AsyncView,
        AsyncFunction
    ]:
        """
        Manage an element.
        This asynchronous method manages an element based on the provided configuration and element type.
        It supports managing schemas, extensions, tables, views, and functions.
            configuration (dict): The configuration dictionary for the element.
            element_type (str): The type of the element (e.g., 'schema', 'extension', 'table', 'view', 'function').
            manage_from (str, optional): The source from which to manage the element. Defaults to 'database'.
            **kwargs: Additional keyword arguments to pass to the element's manage method.

        Returns:
            Union[AsyncSchema, AsyncExtension, AsyncTable, AsyncView, AsyncFunction]: The managed element.
        Raises:
            ValueError: If the element type is not supported.
        Notes:
            - If the element type is 'schema' or 'extension', it checks if the element exists in the list of elements.
              If it does not exist, it initiates the element and adds it to the elements list.
            - If the element's status is 'inexistant', it removes the element from the list.
            - For other element types, it manages the element within the context of its schema.

        """
        
        if element_type in ['schema','extension']:
            # Check if element exists in the list of elements
            element = self.getElement(
                configuration,
                element_type
            )

            # If it does not, initiate it, add it to the elements list
            if not element:

                element = await self.initiateElement(
                    configuration,
                    element_type
                )

                configuration = {}
                getattr(self,element_type).append(element)

            await element.manage(
                manage_from,
                configuration,
                **kwargs
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
                
            return element
        
        else:
            schema_configuration = {
                'name':configuration.get('schema_name','public'),
                'id':configuration.get('schema_id',None),
                'status':configuration.get('status','developpement'),
                'schema_type':configuration.get('schema_type','source')
            }

            schema = self.getElement(
                schema_configuration,
                'schema'
            )

            if not schema:
                schema = await self.manageElement(
                    schema_configuration,
                    'schema',
                    **kwargs
                )


            if 'dependences' in configuration:
                checks = []

                for dependence in configuration.get('dependences',[]):

                    dependence_schema = next((
                        s for s in self.schema if s.name == dependence['schema_name']),
                        None
                    )
                    
                    checks.append(dependence['name'] in [
                        s.name for s in getattr(dependence_schema,dependence['element_type']) if s.db_element
                    ] if dependence_schema else False)
                
                dependance_exists = all(checks)
                    
            else:
                dependance_exists = True

            return await schema.manageElement(
                configuration,
                element_type,
                manage_from,
                dependance_exists=dependance_exists,
                **kwargs
            )

    async def executeDataAction(
        self,
        element:dict,
        action_name:str,
        **kwargs
    ) -> Union[Data,None]:
        schema = await self.manageElement(
            {'name':element.get('schema_name')},
            'schema'
        )
        return await schema.executeDataAction(
            element,action_name,**kwargs
        )
    
    async def manageForeignAttributes(self) -> None:
        await self.manageAttributes()
        
        [
            await schema.manageForeignAttributes()
            for schema in self.schema
        ]
        [
            await extension.manageAttributes()
            for extension in self.extension
        ]

    async def manageDefaultsElements(self) -> None:
        elements = self.query_builder.config['elements']

        for element_type in elements:
            if 'defaults' in elements[element_type] and element_type !='role':
                for default in elements[element_type]['defaults']:
                    await self.manageElement(
                        default,
                        element_type
                    )

        await self.manageForeignAttributes()
  
