"""

"""
from __future__ import annotations

import copy

from datablender.base import (
    Connection,
    DataConfiguration,
    AsyncConnection,
    AsyncDataConfiguration
)
from datablender.database.elementSQL import DatabaseElement,AsyncDatabaseElement

class Role(DatabaseElement):
    """Represents a role in the database

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        name (str): Role name.
        role_type (str): Role type.
        status (str): Role status.
        data_configuration (DataConfiguration): Data configuration.
        acticvate_data_config (bool): Activate data configuration.
        id (int): Role id.
        is_from_config (bool): Is configuration from configuration.

    Methods:
    ----------
        manage(self) -> None: Manage role.

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        connection:Connection,
        name:str,
        is_superuser:bool,
        can_create_database:bool,
        status:str='default',
        data_configuration:DataConfiguration=None,
        acticvate_data_config:bool=False,
        id:int=None,
        event_server=None
    ):
        """Initiate role.

        Args:
            connection (Connection): Connection to a database.
            name (str): Role name.
            role_type (str): Role type.
            status (str, optional): Role status. Defaults to 'developpement'.
            data_configuration (DataConfiguration, optional): Data configuration. Defaults to None.
            acticvate_data_config (bool, optional): Activate data configuration. Defaults to False.
            id (int, optional): Role id. Defaults to None.
            is_from_config (bool, optional): Is configuration from configuration. Defaults to False.
        """
        
        super(Role,self).__init__(
            connection,
            name,
            'role',
            status,
            data_configuration,
            acticvate_data_config,
            id,
            event_server=event_server
        )

        self.is_superuser = is_superuser
        self.can_create_database = can_create_database
        
        self.manageAttributes()
        self.getDBElement()

    def manage(
        self,
        manage_from:str='database',
        new_configuration:dict={}
    ) -> Role:
        """Manage the role in the database.

            Manage from the values given at the initiation
        Returns:
            Role: self.
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

    def create(self) -> None:
        """Create role.
        """
        
        self.query_builder.create(
            self.name,
            'role'
        ).roleOptions(
            self.is_superuser,
            self.can_create_database
        ).built().execute()
        
        self.getDBElement()
        
        self.data_logging.logEvent(
            'role',
            self.name,
            'create'
        )

    def drop(
        self,
        exists_condition:bool=False
    ) -> None: 
        """Drop role.
        """
        
        self.query_builder.drop(
            self.name,
            self.element_type,
            exists_condition=exists_condition
        ).built().execute()
        
        self.db_element = {}

        self.data_logging.logEvent(
            'role',
            self.name,
            'drop'
        )
        
    def rename(
        self,
        new_name:str
    ) -> None:
        """Rename the element.

        Args:
            new_name (str): New name.
        """
        
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
            self.element_type,
            self.name,
            'rename'
        )

class AsyncRole(AsyncDatabaseElement):
    """Represents a role in the database

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        name (str): Role name.
        role_type (str): Role type.
        status (str): Role status.
        data_configuration (DataConfiguration): Data configuration.
        acticvate_data_config (bool): Activate data configuration.
        id (int): Role id.
        is_from_config (bool): Is configuration from configuration.

    Methods:
    ----------
        manage(self) -> None: Manage role.

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        connection:AsyncConnection,
        name:str,
        is_superuser:bool,
        can_create_database:bool,
        status:str='default',
        data_configuration:AsyncDataConfiguration=None,
        acticvate_data_config:bool=False,
        id:int=None,
        event_server=None
    ):
        """Initiate role.

        Args:
            connection (Connection): Connection to a database.
            name (str): Role name.
            role_type (str): Role type.
            status (str, optional): Role status. Defaults to 'developpement'.
            data_configuration (DataConfiguration, optional): Data configuration. Defaults to None.
            acticvate_data_config (bool, optional): Activate data configuration. Defaults to False.
            id (int, optional): Role id. Defaults to None.
            is_from_config (bool, optional): Is configuration from configuration. Defaults to False.
        """
        
        super(AsyncRole,self).__init__(
            connection,
            name,
            'role',
            status,
            data_configuration,
            acticvate_data_config,
            id,
            event_server=event_server
        )

        self.is_superuser = is_superuser
        self.can_create_database = can_create_database

    async def initiate(self) -> AsyncRole:
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
        data_logging_action:dict={}
    ) -> AsyncRole:
        """Manage the role in the database.

            Manage from the values given at the initiation
        Returns:
            Role: self.
        """
        
        await self.setManageParameters(
            manage_from,
            new_configuration,
            data_logging_action
        )
        
        self.data_logging.setActionName(
            'manage',
            self.element_type,
            self.configuration
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

    async def create(self) -> None:
        """Create role.
        """
        
        await self.data_logging.logEvent(
            'create',
            'loading'
        )

        await self.query_builder.create(
            self.name,
            'role'
        ).roleOptions(
            self.is_superuser,
            self.can_create_database
        ).built().asyncExecute(
            data_logging = self.data_logging
        )
        
        await self.getDBElement()

    async def drop(
        self,
        exists_condition:bool=False
    ) -> None: 
        """Drop role.
        """
        
        await self.data_logging.logEvent(
            'drop',
            'loading'
        )

        await self.query_builder.drop(
            self.name,
            self.element_type,
            exists_condition=exists_condition
        ).built().asyncExecute(
            data_logging = self.data_logging
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

        await self.query_builder.alter(
            self.db_element.get('name'),
            self.element_type
        ).rename(
            self.name
        ).built().asyncExecute(
            data_logging = self.data_logging
        )

        self.db_element['name'] = copy.deepcopy(self.name)
             
