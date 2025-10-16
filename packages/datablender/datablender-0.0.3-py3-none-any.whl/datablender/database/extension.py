"""

"""
from __future__ import annotations

from datablender.base import (
    Connection,
    DataConfiguration,
    AsyncConnection,
    AsyncDataConfiguration
)

from datablender.database.elementSQL import DatabaseElement,AsyncDatabaseElement

class Extension(DatabaseElement):
    """Represents a role in the database

    Attributes:
    ----------
        Attributes

    Methods:
    ----------
        Methods

    """
    def __init__(
        self,
        connection:Connection,
        name:str,
        status:str = 'default',
        data_configuration:DataConfiguration = None,
        acticvate_data_config:bool = False,
        id:int=None,
        event_server=None
    ):
        super(Extension,self).__init__(
            connection,
            name,
            'extension',
            status,
            data_configuration,
            acticvate_data_config,
            id,
            event_server=event_server
        )

        self.manageAttributes()
        self.getDBElement()

    def manage(
        self,
        manage_from:str='database',
        new_configuration:dict={}
    ) -> Extension:
        """Manage the extension in the database and in the configuration.

        Args:
            from_values (bool, optional): Manage from the given values at the initiation. Defaults to False.

        Returns:
            Extension: self.
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
        """Create the extension.
        """
        
        self.data_logging.logEvent(
            'create',
            'loading'
        )
        self.query_builder.create(
            self.name,
            'extension'
        ).built().execute()

        self.getDBElement()
        
        if self.name == 'postgis':
            self.data_logging.initiateTable()
        
        
        self.data_logging.logEvent(
            'create',
            'loaded'
        )

    def drop(self,exists_condition:bool=False) -> None: 
        """Drop extension.
        """
        
        self.data_logging.logEvent(
            'drop',
            'loading'
        )
        self.query_builder.drop(
            self.name,
            self.element_type,
            exists_condition=exists_condition
        ).built().execute()
        self.db_element = {}
        
        
        self.data_logging.logEvent(
            'drop',
            'loaded'
        )

class AsyncExtension(AsyncDatabaseElement):
    """Represents a role in the database

    Attributes:
    ----------
        Attributes

    Methods:
    ----------
        Methods

    """
    def __init__(
        self,
        connection:AsyncConnection,
        name:str,
        status:str = 'default',
        data_configuration:AsyncDataConfiguration = None,
        acticvate_data_config:bool = False,
        id:int=None,
        event_server=None
    ):
        super(AsyncExtension,self).__init__(
            connection,
            name,
            'extension',
            status,
            data_configuration,
            acticvate_data_config,
            id,
            event_server=event_server
        )

    async def initiate(self) -> AsyncExtension:
        if self.name != 'postgis':
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
    ) -> AsyncExtension:
        """Manage the extension in the database and in the configuration.

        Args:
            from_values (bool, optional): Manage from the given values at the initiation. Defaults to False.

        Returns:
            Extension: self.
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

    async def create(self) -> None:
        """Create the extension.
        """
        
        await self.data_logging.logEvent(
            'create',
            'loading'
        )
        await self.query_builder.create(
            self.name,
            'extension'
        ).built().asyncExecute(
            data_logging = self.data_logging
        )

        await self.getDBElement()
        
        if self.name == 'postgis':
            await self.data_logging.manageTable()        

    async def drop(self,exists_condition:bool=False) -> None: 
        """Drop extension.
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
     
