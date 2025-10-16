"""
This module contains the Database Element class. 
"""
from typing import Dict, List, Union

import copy

from datablender.database import mode_level

from datablender.base import (
    Connection,
    DataConfiguration,
    DataElement,
    AsyncDataElement,
    AsyncConnection,
    AsyncDataConfiguration
)

class ElementSQL(DataElement):
    """Represent an SQL element, like a database, table, schema, view, a function, a role or an extension.

    When you initiate an element,

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        name (str): Element's name.
        owner (str, optional): Element's owner.
        type (str): Element's type (database, table, schema, view, function, role).
        status (str): Element's status (developpement, test, production).
        data_configuration (DataConfiguration): Data configuration.
        acticvate_data_config (bool): Data configuration.
        is_from_config (bool): Data configuration.
        query_builder (QueryBuilder): Query builder.
        should_exists (bool) : Indicate if element should exists.
        
    Methods:
    ----------
        should_exists(self) -> bool: Check if element should exists according to the element's status (developpement, test, production).
        __hash__(self) -> None: Create the element

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        connection:Connection,
        name:str,
        element_type:str = 'table',
        status:str = 'default',
        data_configuration:DataConfiguration = None,
        acticvate_data_config:bool = False,
        id:int=None,
        content:list=[],
        event_server=None
    ):
        """Initiate the database element.

        Args:
            connection (Connection): Database to manipulate the element
            name (str): Element's name
            element_type (str, optional): Element's type (database, table, schema, view, function, role). Defaults to 'table'.
            owner (str, optional): Element's owner. Defaults to None.
            status (str, optional): Element's status (developpement, test, production). Defaults to 'developpement'.
            data_configuration (DataConfiguration, optional): Data configuration. Defaults to None.
            acticvate_data_config (bool, optional): Data configuration. Defaults to False.
            is_from_config (bool, optional): Data configuration. Defaults to False.
        """

        super(ElementSQL,self).__init__(
            connection,
            name,
            element_type,
            status,
            data_configuration,
            acticvate_data_config,
            id,
            content,
            event_server
        )

        self.db_element:dict = {}                
    
    @property
    def should_exists(self) -> bool:
        """Check if element should exists according to the
        element's status (developpement, test, production).

        Returns:
            bool: Should exists in the database or not.
        """
        
        if self.status in ['inactive','inexistant']:
            return False

        if self.connection.database_name in [
            level for level in mode_level 
            if level not in ['inactive','inexistant']
        ] and self.status !='default':
            
            return mode_level[
                self.status
            ] >= mode_level[
                self.connection.database_name
            ]

        return True

    @property
    def configuration(self) -> None:

        return {
            attribute.get('name'):getattr(
                self,
                attribute.get('name')
            )
            for attribute in self.attributes
            if attribute.get('name') != 'sizes'
        }

    @configuration.setter
    def configuration(
        self,
        new_configuration:Dict[str,any]
    ) -> None:
    
        [
            self.setAttribute(
                attribute_name,
                new_configuration[attribute_name]
            )
            for attribute_name in new_configuration
        ]
        self.manageAttributes()
    
    def setAttribute(
        self,
        attribute_name:str,
        new_value:Union[str,list,List[dict]]
    ) -> None:
        
        old_value = self.setCompareValue(
            getattr(self,attribute_name)
        )
        if isinstance(new_value,list) and isinstance(old_value,list):
            if all([
                isinstance(sub_value,dict)
                for sub_value in new_value
            ]):
                if old_value != self.setCompareValue(new_value):
                    new_values = copy.deepcopy(new_value)
                    new_value = copy.deepcopy(old_value)

                    for new_value_ in new_values:
                        old_values = [
                            {k:v for k,v in old_value_.items() if k in new_value_}
                            for old_value_ in old_value
                        ]
                        if new_value_ not in old_values:
                            new_value.append(new_value_)
    
        setattr(
            self,
            attribute_name,
            new_value
        ) 

    def manageInConfig(self) -> None:
    
        if (
            self.data_configuration.active 
            and self.element_type != 'database'
            and self.manage_from != 'configuration'
        ):
            if self.config_element:

                if self.status == 'inexistant':
                    self.data_configuration.deleteElement(
                        self.id,
                        self.element_type
                    )

                if self.manageAttributes('configuration'):

                    self.data_configuration.putElement(
                        self.id,
                        self.configuration,
                        self.element_type
                    )
     
            elif self.status != 'inexistant':
                
                setattr(
                    self,
                    'id',
                    self.data_configuration.postElement(
                        copy.deepcopy(self.configuration),
                        self.element_type
                    )
                )

    def setManager(
        self,
        manage_from:str,
        new_configuration:dict
    ) -> str:
    
        # If there is a new configuration, it will be updated from the values:
        if new_configuration:
            self.configuration = new_configuration
            self.manage_from = 'values'
        
        elif (
            not self.db_element
            and not self.config_element
        ):
            self.manage_from = 'values'

        elif (
            self.data_configuration.active
            and self.config_element 
            and (
                manage_from == 'configuration'
                or (
                    not self.db_element
                    and manage_from == 'database'
                )
            )
        ):
            self.configuration = self.config_element
            self.manage_from = 'configuration' 
        
        # If db_elements is None, it can not be manage from database
        elif (
            not self.db_element
            and manage_from == 'database'
        ):
            self.manage_from = 'values'
            # Update database and config

        else:
            self.manage_from = manage_from

class DatabaseElement(ElementSQL):
    """Represent a database element

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        name (str): Name of the element.
        element_type (str): Type of the element.
        status (str): Status.
        exists (bool): Indicate if the element exists in the database.
        existsInConfig (bool): Indicate if the element exists in the data configuration.

    Methods:
    ----------
        getDBElements(self) -> None: Get the list of elements in the database.
        getConfigElements(self) -> None: Get the list of elements in the data configuration.

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        connection:Connection,
        name:str,
        element_type:str,
        status:str = 'default',
        data_configuration:DataConfiguration = None,
        acticvate_data_config:bool = False,
        id:int=None,
        content:list=[],
        event_server = None
    ):
        """Initiate a database element

        Args:
            connection (Connection): Connection to a database.
            name (str): Name of the element.
            element_type (str): Type of the element.
            status (str, optional): Status. Defaults to 'developpement'.
        """
        super(DatabaseElement,self).__init__(
            connection,
            name,
            element_type,
            status,
            data_configuration,
            acticvate_data_config,
            id,
            content,
            event_server
        )

        self.manage_elements_from = None
            
        self.data_logging.setElement(
            self.element_type,
            self.name,
            self.id
        )

    def getDBElement(self) -> None:
        """Get element in the database.
        """
        
        self.db_element = next(
            (
                element for element
                in self.query_builder.selectElements(
                    self.element_type
                ).execute().to_dict('records')
                if element.get('name') == self.name
            ),
            {}
        )

class SchemaElement(ElementSQL):
    """Represent a schema element, as a table, view or a function

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        name (str): Element's name.
        type (str): Element's type (database, table, schema, view, function, role).
        schema_name (str): Element's schema name.
        owner (str): Element's owner.
        status (str): Element's status (developpement, test, production).
        query_builder (QueryBuilder): .
        elements_list (pandas.Dataframe): .
        exists (bool) : .
        should_exists (bool) : .

    Methods:
    ----------
        drop (self) -> None: .

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        connection:Connection,
        name:str,
        schema_name:str=  'public',
        element_type:str = 'table',
        owner:str = None,
        status:str = 'default',
        data_configuration:DataConfiguration = None,
        acticvate_data_config:bool = False,
        id:int = None,
        content:list = None,
        event_server = None,
        schema_id:int = None,
        owner_id:int = None,
        is_materialized:bool = None
    ):

        super(SchemaElement,self).__init__(
            connection,
            name,
            element_type,
            status,
            data_configuration,
            acticvate_data_config,
            id,
            content,
            event_server
        )
        
        self.schema_name = schema_name
        self.schema_id = schema_id
        self.owner = owner
        self.owner_id = owner_id
        self.is_materialized = is_materialized

        self.manageAttributes()
        self.getDBElement()
    
        self.data_logging.setElement(
            self.element_type,
            self.name,
            self.id,
            self.schema_id,
            self.schema_name
        )

    def getDBElement(self) -> None:
        """Get element in the database.
        """
        self.db_element = next(
            (
                element for element
                in self.query_builder.selectElements(
                    self.element_type
                ).execute().to_dict('records')
                if (
                    element.get(
                        'schema_name'
                    ) == self.schema_name
                    and element.get(
                        'name'
                    ) == self.name
                )
            ),
            {}
        )

    def drop(
        self,
        exists_condition:bool=False
    ) -> None:
        """Drop the schema element.

        Args:
            exists_condition (bool, optional): Add exists condition. Defaults to False.
        """
                                        
        self.data_logging.logEvent(
            'drop',
            'loading'
        )

        self.query_builder.drop(
            self.name,
            self.element_type,
            self.schema_name,
            exists_condition,
            self.is_materialized
        ).built().execute()

        self.db_element = {}
                                
        self.data_logging.logEvent(
            'drop',
            'loaded'
        )
    
    def rename(
        self,
        new_name:str
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
            self.manage_from = 'values'
            self.manageInConfig()

        self.query_builder.alter(
            self.db_element.get('name'),
            self.element_type,
            self.schema_name,
            self.is_materialized
        ).rename(
            self.name
        ).built().execute()

        self.db_element['name'] = copy.deepcopy(self.name)
                                                
        self.data_logging.logEvent(
            'rename',
            'loaded'
        )

    def setSchema(
        self,
        new_schema:str
    ) -> None:
                                                
        self.data_logging.logEvent(
            'setSchema',
            'loading'
        )

        if new_schema:
            self.schema_name = new_schema
            self.schema_id = None
            self.manageAttributes()
            self.manage_from = 'values'
            self.manageInConfig()
    
        self.query_builder.alter(
            self.name,
            self.element_type,
            self.db_element.get('schema_name'),
            self.is_materialized
        ).schema(
            self.schema_name
        ).built().execute()
        
        self.db_element['schema_name'] = copy.deepcopy(self.schema_name)
                                        
        self.data_logging.logEvent(
            'setSchema',
            'loaded'
        )
   
    def setOwner(
        self,
        owner:str=None
    ) -> None:
        """Set element owner.

        Args:
            owner (str, optional): Owner name. Defaults to None.
        """
                                                       
        self.data_logging.logEvent(
            'owner',
            'loading'
        )
        if owner:
            self.owner=owner
            self.owner_id = None
            self.manageAttributes()
            self.manage_from = 'values'
            self.manageInConfig()

        self.query_builder.alter(
            self.name,
            self.element_type,
            self.schema_name,
            self.is_materialized
        ).owner(
            self.owner
        ).built().execute()

        self.db_element['owner'] = copy.deepcopy(self.owner)
                                                
        self.data_logging.logEvent(
            'owner',
            'loaded'
        )

class AsyncElementSQL(AsyncDataElement):
    """Represent an SQL element, like a database, table, schema, view, a function, a role or an extension.

    When you initiate an element,

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        name (str): Element's name.
        owner (str, optional): Element's owner.
        type (str): Element's type (database, table, schema, view, function, role).
        status (str): Element's status (developpement, test, production).
        data_configuration (DataConfiguration): Data configuration.
        acticvate_data_config (bool): Data configuration.
        is_from_config (bool): Data configuration.
        query_builder (QueryBuilder): Query builder.
        should_exists (bool) : Indicate if element should exists.
        
    Methods:
    ----------
        should_exists(self) -> bool: Check if element should exists according to the element's status (developpement, test, production).
        __hash__(self) -> None: Create the element

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        connection:AsyncConnection,
        name:str,
        element_type:str = 'table',
        status:str = 'default',
        data_configuration:AsyncDataConfiguration = None,
        acticvate_data_config:bool = False,
        id:int=None,
        content:list=[],
        event_server=None
    ):
        """Initiate the database element.

        Args:
            connection (Connection): Database to manipulate the element
            name (str): Element's name
            element_type (str, optional): Element's type (database, table, schema, view, function, role). Defaults to 'table'.
            owner (str, optional): Element's owner. Defaults to None.
            status (str, optional): Element's status (developpement, test, production). Defaults to 'developpement'.
            data_configuration (DataConfiguration, optional): Data configuration. Defaults to None.
            acticvate_data_config (bool, optional): Data configuration. Defaults to False.
            is_from_config (bool, optional): Data configuration. Defaults to False.
        """

        super(AsyncElementSQL,self).__init__(
            connection,
            name,
            element_type,
            status,
            data_configuration,
            acticvate_data_config,
            id,
            content,
            event_server
        )

        self.db_element:dict = {}   
        self.data_logging.element_configuration = self.configuration             
    
    @property
    def should_exists(self) -> bool:
        """Check if element should exists according to the
        element's status (developpement, test, production).

        Returns:
            bool: Should exists in the database or not.
        """
        
        if self.status in ['inactive','inexistant']:
            return False

        if self.connection.database_name in [
            level for level in mode_level 
            if level not in ['inactive','inexistant']
        ] and self.status !='default':
            
            return mode_level[
                self.status
            ] >= mode_level[
                self.connection.database_name
            ]

        return True

    @property
    def configuration(self) -> None:

        return {
            attribute.get('name'):getattr(
                self,
                attribute.get('name')
            )
            for attribute in self.attributes
            if
                attribute.get('name') != 'sizes'
                and hasattr(self,attribute.get('name'))
        }

    @configuration.setter
    def configuration(
        self,
        new_configuration:Dict[str,any]
    ) -> None:
    
        [
            self.setAttribute(
                attribute_name,
                new_configuration[attribute_name]
            )
            for attribute_name in new_configuration
        ]
        #self.manageAttributes()
    
    def setAttribute(
        self,
        attribute_name:str,
        new_value:Union[str,list,List[dict]]
    ) -> None:
        
        old_value = self.setCompareValue(
            getattr(self,attribute_name)
        )
        if isinstance(new_value,list) and isinstance(old_value,list):
            if all([
                isinstance(sub_value,dict)
                for sub_value in new_value
            ]):
                if old_value != self.setCompareValue(new_value):
                    new_values = copy.deepcopy(new_value)
                    new_value = copy.deepcopy(old_value)

                    for new_value_ in new_values:
                        new_value_ = self.setCompareValue(new_value_)
                        old_values = [
                            {k:v for k,v in old_value_.items() if k in new_value_}
                            for old_value_ in old_value
                        ]
                        if new_value_ not in old_values:
                            new_value.append(new_value_)
    
        setattr(
            self,
            attribute_name,
            new_value
        ) 

    async def manageInConfig(self) -> None:
    
        if (
            self.data_configuration.active 
            and self.element_type != 'database'
            and self.manage_from != 'configuration'
        ):
            if self.config_element:

                if self.status == 'inexistant':
                    await self.data_configuration.deleteElement(
                        self.id,
                        self.element_type
                    )

                if await self.manageAttributes('configuration'):

                    await self.data_configuration.putElement(
                        self.id,
                        self.configuration,
                        self.element_type
                    )
     
            elif self.status != 'inexistant':
                
                setattr(
                    self,
                    'id',
                    await self.data_configuration.postElement(
                        copy.deepcopy(self.configuration),
                        self.element_type
                    )
                )

    async def setManager(
        self,
        manage_from:str,
        new_configuration:dict,
        ignore_new_config:bool = False
    ) -> str:
    
        # If there is a new configuration, it will be updated from the values:
        if new_configuration and not ignore_new_config:

            self.configuration = new_configuration
            await self.manageAttributes()
            self.manage_from = 'values'
        
        elif (
            not self.db_element
            and not self.config_element
        ):
            self.manage_from = 'values'

        elif (
            self.data_configuration.active
            and self.config_element 
            and (
                manage_from == 'configuration'
                or (
                    not self.db_element
                    and manage_from == 'database'
                )
            )
        ):
            self.configuration = self.config_element
            await self.manageAttributes()
            self.manage_from = 'configuration' 
        
        # If db_elements is None, it can not be manage from database
        elif (
            not self.db_element
            and manage_from == 'database'
        ):
            self.manage_from = 'values'
            # Update database and config

        else:
            self.manage_from = manage_from

    async def setManageParameters(
        self,
        manage_from:str,
        new_configuration:dict={},
        data_logging_action:dict={},
        ignore_new_config:bool = False
    ) -> None:
        
        await self.setManager(
            manage_from,
            new_configuration,
            ignore_new_config
        )
    
        if data_logging_action:
            self.data_logging.setActionName(
                **data_logging_action
            )

        else:     
            self.data_logging.setActionName(
                'manage',
                self.element_type,
                self.configuration
            )

class AsyncDatabaseElement(AsyncElementSQL):
    """Represent a database element

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        name (str): Name of the element.
        element_type (str): Type of the element.
        status (str): Status.
        exists (bool): Indicate if the element exists in the database.
        existsInConfig (bool): Indicate if the element exists in the data configuration.

    Methods:
    ----------
        getDBElements(self) -> None: Get the list of elements in the database.
        getConfigElements(self) -> None: Get the list of elements in the data configuration.

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        connection:AsyncConnection,
        name:str,
        element_type:str,
        status:str = 'default',
        data_configuration:AsyncDataConfiguration = None,
        acticvate_data_config:bool = False,
        id:int=None,
        content:list=[],
        event_server = None
    ):
        """Initiate a database element

        Args:
            connection (Connection): Connection to a database.
            name (str): Name of the element.
            element_type (str): Type of the element.
            status (str, optional): Status. Defaults to 'developpement'.
        """
        super(AsyncDatabaseElement,self).__init__(
            connection,
            name,
            element_type,
            status,
            data_configuration,
            acticvate_data_config,
            id,
            content,
            event_server
        )
        
    async def getDBElement(self) -> None:
        """Get element in the database.
        """

        db_elements = await self.query_builder.selectElements(
            self.element_type
        ).asyncExecute()
        
        self.db_element = next(
            (
                element for element
                in db_elements.to_dict('records')
                if element.get('name') == self.name
            ),
            {}
        )

class AsyncSchemaElement(AsyncElementSQL):
    """Represent a schema element, as a table, view or a function

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        name (str): Element's name.
        type (str): Element's type (database, table, schema, view, function, role).
        schema_name (str): Element's schema name.
        owner (str): Element's owner.
        status (str): Element's status (developpement, test, production).
        query_builder (QueryBuilder): .
        elements_list (pandas.Dataframe): .
        exists (bool) : .
        should_exists (bool) : .

    Methods:
    ----------
        drop (self) -> None: .

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        connection:AsyncConnection,
        name:str,
        schema_name:str=  'public',
        element_type:str = 'table',
        owner:str = None,
        status:str = 'default',
        data_configuration:AsyncDataConfiguration = None,
        acticvate_data_config:bool = False,
        id:int = None,
        content:list = None,
        event_server = None,
        schema_id:int = None,
        owner_id:int = None,
        is_materialized:bool = None,
        schema_type:int = 'source'
    ):

        super(AsyncSchemaElement,self).__init__(
            connection,
            name,
            element_type,
            status,
            data_configuration,
            acticvate_data_config,
            id,
            content,
            event_server
        )
        
        self.schema_name = schema_name
        self.schema_id = schema_id
        self.schema_type = schema_type
        self.owner = owner if owner else self.connection.user_name
        self.owner_id = owner_id
        self.is_materialized = is_materialized

    async def getDBElement(self) -> None:
        """Get element in the database.
        """
        db_elements = await self.query_builder.selectElements(
            self.element_type
        ).asyncExecute()

        self.db_element = next(
            (
                element for element
                in db_elements.to_dict('records')
                if (
                    element.get(
                        'schema_name'
                    ) == self.schema_name
                    and element.get(
                        'name'
                    ) == self.name
                )
            ),
            {}
        )

    async def drop(
        self,
        exists_condition:bool=False
    ) -> None:
        """Drop the schema element.

        Args:
            exists_condition (bool, optional): Add exists condition. Defaults to False.
        """
                                        
        await self.data_logging.logEvent(
            'drop',
            'loading'
        )

        await self.query_builder.drop(
            self.name,
            self.element_type,
            self.schema_name,
            exists_condition,
            self.is_materialized
        ).built().asyncExecute(
            data_logging=self.data_logging
        )

        self.db_element = {}         
    
    async def rename(
        self,
        new_name:str
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
            self.manage_from = 'values'
            await self.manageInConfig()

        await self.query_builder.alter(
            self.db_element.get('name'),
            self.element_type,
            self.schema_name,
            self.is_materialized
        ).rename(
            self.name
        ).built().asyncExecute(
            data_logging=self.data_logging
        )

        self.db_element['name'] = copy.deepcopy(self.name)        

    async def setSchema(
        self,
        new_schema:str
    ) -> None:
                                                
        await self.data_logging.logEvent(
            'setSchema',
            'loading'
        )

        if new_schema:
            self.schema_name = new_schema
            self.schema_id = None
            await self.manageAttributes()
            self.manage_from = 'values'
            await self.manageInConfig()
    
        await self.query_builder.alter(
            self.name,
            self.element_type,
            self.db_element.get('schema_name'),
            self.is_materialized
        ).schema(
            self.schema_name
        ).built().asyncExecute(
            data_logging=self.data_logging
        )
        
        self.db_element['schema_name'] = copy.deepcopy(self.schema_name)     
   
    async def setOwner(
        self,
        owner:str=None
    ) -> None:
        """Set element owner.

        Args:
            owner (str, optional): Owner name. Defaults to None.
        """
                                                       
        await self.data_logging.logEvent(
            'owner',
            'loading'
        )

        if owner:
            self.owner=owner
            self.owner_id = None
            await self.manageAttributes()
            self.manage_from = 'values'
            await self.manageInConfig()

        await self.query_builder.alter(
            self.name,
            self.element_type,
            self.schema_name,
            self.is_materialized
        ).owner(
            self.owner
        ).built().asyncExecute(
            data_logging=self.data_logging
        )

        self.db_element['owner'] = copy.deepcopy(self.owner)      
