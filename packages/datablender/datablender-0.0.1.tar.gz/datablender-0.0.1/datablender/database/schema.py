"""

"""
from __future__ import annotations
from typing import Union, List

import copy

from datablender.base import Connection,DataConfiguration,Data
from datablender.database.elementSQL import DatabaseElement,AsyncDatabaseElement
from datablender.database.table import Table,AsyncTable
from datablender.database.view import View,AsyncView
from datablender.database.function import Function,AsyncFunction

class Schema(DatabaseElement):
    """Represent a schema in a database.

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
        data_configuration (DataConfiguration) : .

    Methods:
    ----------
        manage (self) -> None: Manage the schema.
        create (self) -> None: Create the schema.
        drop (self) -> None: 
        setOwner (self) -> None:
        rename (self) -> None:

    Examples:
    ----------
        
        Retrieve an existing schema, like the public one, and get the schema info.

        >>> import datablender
        >>> public_schema = datablender.Schema()
        >>> public_schema.manage()
        >>> public_schema.setOwner('new_owner_name')
        >>> public_schema.size
        223543
        >>> public_schema.grants


        Create a new schema.

        >>> import datablender
        >>> my_schema = datablender.Schema(name='new_schema_name',owner='my_user_name').manage()
        >>> my_schema.manage()

        Reinitiate a schema from the data configuration.

        >>> import datablender
        >>> my_schema = datablender.Schema(name='new_schema_name')
        >>> my_schema.reinitiateFromConfig()


    """
    def __init__(
        self,
        connection:Connection,
        name:str = 'public',
        owner:str = 'postgres',
        status:str = 'default',
        data_configuration:DataConfiguration = None,
        acticvate_data_config:bool = False,
        id:int = None,
        content:dict = None,
        schema_type:str = 'source',
        grants:List[dict] = [
            {
              "privilege": "usage",
              "user_name": "postgres"
            },
            {
              "privilege": "create",
              "user_name": "postgres"
            }
        ],
        size:int=0,
        event_server=None,
        owner_id:int = None
    ):
        if name == 'public':
            status = 'production'

        super(Schema,self).__init__(
            connection,
            name,
            'schema',
            status,
            data_configuration,
            acticvate_data_config,
            id,
            content,
            event_server
        )

        self.owner = owner
        self.owner_id = owner_id
        self.schema_type = schema_type
        self.grants = grants
        self.size = size

        self.table:List[Table] = []
        self.view:List[View] = []
        self.function:List[Function] = []

        self.manageAttributes()
        self.getDBElement()

    def manage(
        self,
        manage_from:str='database',
        new_configuration:dict={}
    ) -> Schema:
        """Manage the schema in the database and in the configuration.

        Args:
            manage_from (str, optional): Manage the schema from. Defaults to False.

        Returns:
            Schema: self.
        """

        self.setManager(
            manage_from,
            new_configuration
        )

        if not self.db_element and self.should_exists:
            self.manageInConfig()
            self.create()
            self.manageAttributes('database')

        else:

            if self.db_element and self.should_exists:
            
                self.manageAttributes(
                    'values'
                    if self.manage_from == 'database'
                    else 'database'
                )
                
            elif self.db_element and not self.should_exists:
                self.drop()
        
            self.manageInConfig()

        return self

    def create(self):
        """Create schema.
        """
        
        self.data_logging.logEvent(
            'create',
            'loading'
        )

        self.query_builder.create(
            self.name,
            'schema'
        ).built().execute()
        
        self.getDBElement()
        self.data_logging.logEvent(
            'create',
            'loaded'
        )
    
    def drop(
        self,
        exists_condition:bool=False
    ):
        """Drop schema.

        Args:
            exists_condition (bool, optional): Add exists statement to the . Defaults to False.
        """
                
        self.data_logging.logEvent(
            'drop',
            'loading'
        )
        
        self.query_builder.drop(
            self.name,
            'schema',
            exists_condition = exists_condition
        ).built().execute()

        self.db_element = {}

        self.data_logging.logEvent(
            'drop',
            'loaded'
        )
        
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
        """Set schema owner.

        Args:
            owner (str, optional): Owner name. Defaults to None.
        """
                                
        self.data_logging.logEvent(
            'owner',
            'loading'
        )

        if owner:
            self.owner = owner
            self.owner_id = None
            self.manageAttributes()
            self.manage_from = 'values'
            self.manageInConfig()

        self.query_builder.alter(
            self.name,
            'schema'
        ).owner(
            self.owner
        ).built().execute()
        
        self.db_element['owner'] = copy.deepcopy(self.owner)
                        
        self.data_logging.logEvent(
            'owner',
            'loaded'
        )
    
    def manageGrants(self):
        """Grant privileges on schema.
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
        element_type:str
    ) -> None:
        """Get a list of the elements (tables, views,functions)
        from the database in the schema.

        Args:
            element_type (str): type of the element (table, view,function).
        """

        self.data_configuration.getElements(element_type)    

        elements = [
            element for element in self.query_builder.selectElements(
                element_type
            ).execute().to_dict('records')
            if element.get('schema_name') == self.name
        ]

        if self.data_configuration.active:
            for element in getattr(
                self.data_configuration,
                element_type,
                []
            ):
                if element['schema_id'] == self.id:

                    element_index = next((
                        i for i, item in enumerate(elements)
                        if item.get('name') == element.get('name')
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

    def initiateElement(
        self,
        configuration:dict,
        element_type:str
    ) -> Union[
        Table,View,Function
    ]:
        if element_type== 'table':

            return Table(
                self.connection,
                data_configuration=self.data_configuration,
                event_server=self.data_logging.event_server,
                **configuration
            )
        
        elif element_type== 'view':

            return View(
                self.connection,
                data_configuration=self.data_configuration,
                event_server=self.data_logging.event_server,
                **configuration
            )
        
        elif element_type== 'function':

            return Function(
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
        Table,View,Function,None
    ]:
        for attribute_name in ['id','name']:

            attribute_value = configuration.get(attribute_name)
            
            element = next((
                element for element in getattr(self,element_type)
                if getattr(element,attribute_name) == attribute_value),
                None
            ) if attribute_name in configuration and attribute_value else None
            
            if element:
                return element

    def manageElement(
        self,
        configuration:dict,
        element_type:str,
        manage_from:str='database',
        default_configuration:dict = {},
        **kwargs
    ) -> Union[
        Table,View,Function
    ]:
        """Manage an element.

        Args:
            configuration (dict): configuration.
            element_type (str): type of the element (table, view,function).
            from_values (bool, optional): manage elements from values in elements to set. Defaults to False.

        Returns:
            Union[Table,View,Function]: the element.
        """
        # Check if element exists in the list of elements
        element = self.getElement(
            configuration if configuration else default_configuration,
            element_type
        )
        
        # If it does not, initiate it, add it to the elements list and manage it
        if not element:
                
            element = self.initiateElement(
                default_configuration if default_configuration else configuration,
                element_type
            )
            configuration = {}
            getattr(self,element_type).append(element)

        # If it exists, then it already has been initialize,
        # so it is manage with the new configuraion
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
    
    def executeDataAction(
        self,
        element:dict,
        action_name:str,
        **kwargs
    ) -> Union[None,Data]:
        
        element_type = element.pop('element_type')

        return self.manageElement(
            element,
            element_type
        ).executeDataAction(
            action_name,
            **kwargs
        )

    def manageForeignAttributes(
        self
    ) -> None:
        self.manageAttributes()
        
        for table in self.table:
            table.manageAttributes()
        
        for view in self.view:
            view.manageAttributes()
        
        for function in self.function:
            function.manageAttributes()

class AsyncSchema(AsyncDatabaseElement):
    """Represent a schema in a database.

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
        data_configuration (DataConfiguration) : .

    Methods:
    ----------
        manage (self) -> None: Manage the schema.
        create (self) -> None: Create the schema.
        drop (self) -> None: 
        setOwner (self) -> None:
        rename (self) -> None:

    Examples:
    ----------
        
        Retrieve an existing schema, like the public one, and get the schema info.

        >>> import datablender
        >>> public_schema = datablender.Schema()
        >>> public_schema.manage()
        >>> public_schema.setOwner('new_owner_name')
        >>> public_schema.size
        223543
        >>> public_schema.grants


        Create a new schema.

        >>> import datablender
        >>> my_schema = datablender.Schema(name='new_schema_name',owner='my_user_name').manage()
        >>> my_schema.manage()

        Reinitiate a schema from the data configuration.

        >>> import datablender
        >>> my_schema = datablender.Schema(name='new_schema_name')
        >>> my_schema.reinitiateFromConfig()


    """
    def __init__(
        self,
        connection:Connection,
        name:str = 'public',
        owner:str = None,
        status:str = 'default',
        data_configuration:DataConfiguration = None,
        acticvate_data_config:bool = False,
        id:int = None,
        content:dict = None,
        schema_type:str = 'source',
        grants:List[dict] = [],
        size:int=0,
        event_server=None,
        owner_id:int = None
    ):
        if name == 'public':
            status = 'production'

        super(AsyncSchema,self).__init__(
            connection,
            name,
            'schema',
            status,
            data_configuration,
            acticvate_data_config,
            id,
            content,
            event_server
        )

        self.owner = owner if owner else self.connection.user_name
        self.owner_id = owner_id
        self.schema_type = schema_type
        self.grants = grants if grants else [
            {
              "privilege": "usage",
              "user_name": self.connection.user_name
            },
            {
              "privilege": "create",
              "user_name": self.connection.user_name
            }
        ]
        self.size = size

        self.table:List[Table] = []
        self.view:List[View] = []
        self.function:List[Function] = []

    async def initiate(self) -> AsyncSchema:
        """
        Initiates the schema by managing the data logging table, attributes, 
        updating the configuration, and retrieving the database element.
        Returns:
            AsyncSchema: The initiated schema instance.
        """
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
        **kwargs
    ) -> AsyncSchema:
        """Manage the schema in the database and in the configuration.

        Args:
            manage_from (str, optional): Manage the schema from. Defaults to False.

        Returns:
            Schema: self.
        """

        await self.setManageParameters(
            manage_from,
            new_configuration,
            data_logging_action
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
        """Create schema.
        """
        
        await self.data_logging.logEvent(
            'create',
            'loading'
        )

        await self.query_builder.create(
            self.name,
            'schema'
        ).built().asyncExecute(
            data_logging=self.data_logging
        )
        
        await self.getDBElement()
    
    async def drop(
        self,
        exists_condition:bool=False
    ):
        """Drop schema.

        Args:
            exists_condition (bool, optional): Add exists statement to the . Defaults to False.
        """
                
        await self.data_logging.logEvent(
            'drop',
            'loading'
        )
        
        await self.query_builder.drop(
            self.name,
            'schema',
            exists_condition = exists_condition
        ).built().asyncExecute(
            data_logging=self.data_logging
        )

        self.db_element = {}
        
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
            data_logging=self.data_logging
        )

        self.db_element['name'] = copy.deepcopy(self.name)

    async def setOwner(
        self,
        owner:str=None
    ) -> None:
        """Set schema owner.

        Args:
            owner (str, optional): Owner name. Defaults to None.
        """
                                
        await self.data_logging.logEvent(
            'owner',
            'loading',
            informations = {
                'name':self.owner
            }
        )

        if owner:
            self.owner = owner
            self.owner_id = None
            await self.manageAttributes()
            self.manage_from = 'values'
            await self.manageInConfig()

        await self.query_builder.alter(
            self.name,
            'schema'
        ).owner(
            self.owner
        ).built().asyncExecute(
            data_logging = self.data_logging
        )
        
        self.db_element['owner'] = copy.deepcopy(self.owner)
    
    async def manageGrants(self):
        """Grant privileges on schema.
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
                    informations =grant
                )   
                await self.query_builder.grant(
                    self.name,
                    self.element_type,
                    **grant
                ).built().asyncExecute(
                    data_logging=self.data_logging
                )

        for revoke in db_grants:
            
            await self.data_logging.logEvent(
                'revoke',
                'loading',
                informations = revoke
            )  
            await self.query_builder.revoke(
                self.name,
                self.element_type,
                **revoke   
            ).built().asyncExecute(
                data_logging=self.data_logging
            )

        self.db_element['grants'] = copy.deepcopy(self.grants)  
   
    async def manageElements( 
        self,
        element_type:str
    ) -> None:
        """Get a list of the elements (tables, views,functions)
        from the database in the schema.

        Args:
            element_type (str): type of the element (table, view,function).
        """

        await self.data_configuration.getElements(element_type)    

        elements = await self.query_builder.selectElements(
            element_type
        ).asyncExecute()
        
        elements = [
            element for element in elements.to_dict('records')
            if element.get('schema_name') == self.name
        ]

        if self.data_configuration.active:
            for element in getattr(
                self.data_configuration,
                element_type,
                []
            ):
                if element['schema_id'] == self.id:

                    element_index = next((
                        i for i, item in enumerate(elements)
                        if item.get('name') == element.get('name')
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

    async def initiateElement(
        self,
        configuration:dict,
        element_type:str
    ) -> Union[
        AsyncTable,AsyncView,AsyncFunction
    ]:
        if element_type== 'table':

            return await AsyncTable(
                self.connection,
                data_configuration=self.data_configuration,
                event_server=self.data_logging.event_server,
                **configuration
            ).initiate()
        
        elif element_type== 'view':

            return await AsyncView(
                self.connection,
                data_configuration=self.data_configuration,
                event_server=self.data_logging.event_server,
                **configuration
            ).initiate()
        
        elif element_type== 'function':

            return await AsyncFunction(
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
        AsyncTable,AsyncView,AsyncFunction,None
    ]:
        for attribute_name in ['id','name']:

            attribute_value = configuration.get(attribute_name)
            
            element = next((
                element for element in getattr(self,element_type)
                if getattr(element,attribute_name) == attribute_value),
                None
            ) if attribute_name in configuration and attribute_value else None
            
            if element:
                return element

    async def manageElement(
        self,
        configuration:dict,
        element_type:str,
        manage_from:str='database',
        **kwargs
    ) -> Union[
        AsyncTable,AsyncView,AsyncFunction
    ]:
        """Manage an element.

        Args:
            configuration (dict): configuration.
            element_type (str): type of the element (table, view,function).
            from_values (bool, optional): manage elements from values in elements to set. Defaults to False.

        Returns:
            Union[Table,View,Function]: the element.
        """
        # Check if element exists in the list of elements
        element = self.getElement(
            configuration,
            element_type
        )
        
        # If it does not, initiate it, add it to the elements list and manage it
        if not element:
                
            element = await self.initiateElement(
                configuration,
                element_type
            )
            configuration = {}
            getattr(self,element_type).append(element)

        # If it exists, then it already has been initialize,
        # so it is manage with the new configuraion
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
    
    async def executeDataAction(
        self,
        element:dict,
        action_name:str,
        refresh=False,
        **kwargs
    ) -> Union[None,Data]:
        
        element_type = element.pop('element_type')

        db_element = await self.manageElement(
            element,
            element_type,
            ignore_new_config = True,
            refresh = refresh
        )
        
        if action_name != 'manage':
            return await db_element.executeDataAction(
                action_name,
                **kwargs
            )

    async def manageForeignAttributes(
        self
    ) -> None:
        await self.manageAttributes()
        
        for table in self.table:
            await table.manageAttributes()
        
        for view in self.view:
            await view.manageAttributes()
        
        for function in self.function:
            await function.manageAttributes()
