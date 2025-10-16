"""
This module contains the Database Element class. 
"""
from __future__ import annotations
from typing import Union, List

import copy, pandas

from datablender.base import (
    Connection,
    DataConfiguration,
    Data,
    manageQuery,
    AsyncConnection,
    AsyncDataConfiguration
)
from datablender.database.elementSQL import SchemaElement,AsyncSchemaElement

class View(SchemaElement):
    """Represent a view.

    When you initiate an element,

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        name (str): Element's name.
        schema_name (str): Element's schema name.
        owner (str): Element's owner.
        status (str): Element's status (developpement, test, production).
        query_builder (QueryBuilder): .
        elements_list (pandas.Dataframe): .
        db_element (dict) : .
        should_exists (bool) : .

    Methods:
    ----------
        create (self) -> None: Create the element

    Examples:
    ----------
        >>> import datablender
        >>> my_view = datablender.View(
        >>>     datablender.Connection(),
        >>>     my_view_name,
        >>>     'select * from spatial_ref_sys'
        >>> )
        
        >>> my_view = datablender.View(
        >>>     datablender.Connection(),
        >>>     my_view_name,
        >>>     file_query = 'my_view_query',
        >>>     directory_query = 'path/to/my/view'
        >>> )
        
        >>> my_view = datablender.View(
        >>>     datablender.Connection(),
        >>>     my_view_name,
        >>>     file_query = 'my_view_query'
        >>> )
        
        >>> my_view = datablender.View(
        >>>     datablender.Connection(),
        >>>     my_view_name,
        >>>     file_query = 'my_view_query'
        >>> )

    """
    def __init__(
        self,
        connection:Connection,
        name:str,
        query:str = None,
        file_query:str = None,
        directory_query:str = None,
        schema_name:str = 'public',
        is_materialized:bool = False,
        owner:str = 'postgres',
        content:list = None,
        indexes:List[dict] = [],
        status:str = 'default',
        data_configuration:DataConfiguration = None,
        acticvate_data_config:bool = False,
        id:int = None,
        grants:List[dict] = [],
        size:int=0,
        event_server=None,
        schema_id:int = None,
        owner_id:int = None,
        columns:list = [],
        schema_type:str = 'source',
        is_database_saved:bool  = False
    ):
        super(View,self).__init__(
            connection,
            name,
            schema_name,
            'view',
            owner,
            status,
            data_configuration,
            acticvate_data_config,
            id,
            content,
            event_server,
            schema_id,
            owner_id,
            is_materialized
        )

        self.indexes=indexes
        self.grants=grants

        self.schema_type = schema_type
        self.size = size
        self.columns = columns
        self.is_database_saved = True if self.db_element else is_database_saved

        self.query = query
        self.file_query = file_query
        self.directory_query = directory_query

    def manage(
        self,
        manage_from:str='database',
        new_configuration:dict={}
    ) -> View:
        """Manage the view in the database.

        Returns:
            View: self.
        """
        
        manage_from=self.setManager(
            manage_from,
            new_configuration
        )
        
        if not self.db_element and self.should_exists:

            self.manageInConfig()
            self.query,self.file_query,self.directory_query = manageQuery(
                self.name,
                self.query,
                self.file_query,
                self.directory_query,
                self.schema_name,
                self.schema_type,
                self.data_configuration.active
            )
            self.manageInConfig()
            if self.is_database_saved:
                self.create()
                self.manageAttributes('database')

        elif self.db_element and self.should_exists:

            if self.manage_from == 'database':

                if self.data_configuration.active:
                    self.manageInConfig()
                    self.configuration = self.config_element
                else:
                    self.manageAttributes('values')

            else: 
                self.manageAttributes('database')
                self.manageInConfig() 

        elif self.db_element and not self.should_exists:
            self.drop()
            self.manageInConfig()
        
        elif not self.db_element and not self.should_exists:
            self.manageInConfig()

        return self

    def create(self):
        """Create the view.
        """
        
        self.data_logging.logEvent(
            'create',
            'loading'
        )
        
        self.query_builder.create(
            self.name,
            "view",
            self.schema_name
        ).materialized(
            self.is_materialized
        ).sqlStatement(
            self.query
        ).built().execute()
            
        self.getDBElement()

        
        self.data_logging.logEvent(
            'create',
            'loaded'
        )
    
    def select(
        self,
        where_statement:list=None,
        columns:list=None,
        limit:int=None,
        **kwargs
    ) -> View:
        """Select data.

        Args:
            where_statement (list, optional): Where conditions. Defaults to None.
            columns (list, optional): Columns to select. Defaults to None.
        """
        
        self.data_logging.logEvent(
            'select',
            'loading'
        )

        if self.is_database_saved:
            self.data = Data(
                self.query_builder.select(
                    self.name,
                    schema_name=self.schema_name,
                    limit = limit
                ).columns(
                    columns if columns else self.columns
                ).where(
                    where_statement
                ).built().execute(**kwargs),
                meta_columns=[],
                columns = self.columns
            )
        else:
            self.data = Data(
                self.query_builder.select().sqlStatement(
                    self.query,
                    definition='select'
                ).where(
                    where_statement
                ).built().execute(),
                meta_columns=[],
                columns=[]
            )
        
        self.data_logging.logEvent(
            'select',
            'loaded'
        )

        return self
   
    def manageGrants(self) :
        """Grant privileges on schema.
        """
        
        if self.is_database_saved:
        
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
                        self.schema_name,
                        **grant
                    ).built().execute()

            for revoke in db_grants:
                self.query_builder.revoke(
                    self.name,
                    self.element_type,
                    self.schema_name,
                    **revoke   
                ).built().execute()

            self.db_element['grants'] = copy.deepcopy(self.grants)

            self.data_logging.logEvent(
                'grant',
                'loaded'
            )
    
    def manageIndexes(self) -> None:
        """Create indexes.
        """
        
        self.data_logging.logEvent(
            'index',
            'loading'
        )
                
        db_indexes:List[dict] = copy.deepcopy(
            self.db_element.get('indexes')
        )

        for index in self.indexes:
            if (
                index not in db_indexes 
                and not index.get('constraint_type')
            ):
 
                self.query_builder.create(
                    index.get('name'),
                    'index'
                ).uniqueIndex(
                    index.get('is_unique')
                ).onIndex(
                    index.get('name'),
                    index.get('schema_name')
                ).usingIndex(
                    index.get('method'),
                    index.get('columns')
                ).built().execute()
            
            else:
                db_indexes.remove(index)

        for index in db_indexes:
            if not index.get('constraint_type'):
                self.query_builder.drop(
                    index.get('name'),
                    'index',
                    exists_condition=True
                ).built().execute()

        self.db_element['indexes'] = copy.deepcopy(self.indexes)

        self.data_logging.logEvent(
            'index',
            'loaded'
        )

    def replace(self) -> None:
        
        self.query_builder.create(
            self.name,
            "view",
            self.schema_name
        ).replace().sqlStatement(
            self.query,
            self.directory_query,
            self.file_query
        ).built().execute()

    def transform(
        self,
        transformations
    ) -> None:
        
        self.data.transform(transformations)

    def setData(
        self,
        data:Union[Data,pandas.DataFrame,None]
    ) -> None:
    
        if data is not None:
            if isinstance(data,Data):
                self.data = data
            elif isinstance(data,pandas.DataFrame):
                if hasattr(self,data):
                    self.data.frame = data
                else:
                    self.data = Data(data)
        return self

    def getData(self) -> Data:
        return copy.deepcopy(self.data)

    def executeDataAction(
        self,
        action_name:str,
        **kwargs
    ) -> Union[None,Data]:
        
        return getattr(self,action_name)(**kwargs)

    def refresh(self) -> None:
            
        self.data_logging.logEvent(
            'refresh',
            'loading'
        )
          
        self.query_builder.refresh(
            self.name,
            self.schema_name
        ).built().execute()
        
        self.data_logging.logEvent(
            'refresh',
            'loaded'
        )

class AsyncView(AsyncSchemaElement):
    """Represent a view.

    When you initiate an element,

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        name (str): Element's name.
        schema_name (str): Element's schema name.
        owner (str): Element's owner.
        status (str): Element's status (developpement, test, production).
        query_builder (QueryBuilder): .
        elements_list (pandas.Dataframe): .
        db_element (dict) : .
        should_exists (bool) : .

    Methods:
    ----------
        create (self) -> None: Create the element

    Examples:
    ----------
        >>> import datablender
        >>> my_view = datablender.View(
        >>>     datablender.Connection(),
        >>>     my_view_name,
        >>>     'select * from spatial_ref_sys'
        >>> )
        
        >>> my_view = datablender.View(
        >>>     datablender.Connection(),
        >>>     my_view_name,
        >>>     file_query = 'my_view_query',
        >>>     directory_query = 'path/to/my/view'
        >>> )
        
        >>> my_view = datablender.View(
        >>>     datablender.Connection(),
        >>>     my_view_name,
        >>>     file_query = 'my_view_query'
        >>> )
        
        >>> my_view = datablender.View(
        >>>     datablender.Connection(),
        >>>     my_view_name,
        >>>     file_query = 'my_view_query'
        >>> )

    """
    def __init__(
        self,
        connection:AsyncConnection,
        name:str,
        query:Union[dict,str] = None,
        file_query:str = None,
        directory_query:str = None,
        schema_name:str = 'public',
        is_materialized:bool = False,
        owner:str = None,
        content:list = None,
        indexes:List[dict] = [],
        status:str = 'default',
        data_configuration:AsyncDataConfiguration = None,
        acticvate_data_config:bool = False,
        id:int = None,
        grants:List[dict] = None,
        size:int=0,
        event_server=None,
        schema_id:int = None,
        owner_id:int = None,
        columns:list = [],
        schema_type:str = 'source',
        is_database_saved:bool  = False,
        **kwargs
    ):
        super(AsyncView,self).__init__(
            connection,
            name,
            schema_name,
            'view',
            owner,
            status,
            data_configuration,
            acticvate_data_config,
            id,
            content,
            event_server,
            schema_id,
            owner_id,
            is_materialized
        )

        self.indexes=indexes
        self.grants=grants

        self.schema_type = schema_type
        self.size = size
        self.columns = columns
        self.is_database_saved = True if self.db_element else is_database_saved

        self.query = query
        self.file_query = file_query
        self.directory_query = directory_query
    
    async def initiate(self) -> AsyncView:
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
        ignore_new_config:bool = False,
        refresh:bool = False,
        dependance_exists = True
    ) -> AsyncView:
        """Manage the view in the database.

        Returns:
            View: self.
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

            self.query,self.file_query,self.directory_query = manageQuery(
                self.name,
                self.query,
                self.file_query,
                self.directory_query,
                self.schema_name,
                self.schema_type,
                self.data_configuration.active
            )
            
            await self.manageInConfig()
            
            if self.is_database_saved and dependance_exists:
                await self.create()
                await self.manageAttributes('database')

        else:
            
            if self.db_element and self.should_exists:
            
                await self.manageAttributes(
                    'values'
                    if self.manage_from == 'database'
                    else 'database'
                )

                if self.is_materialized and refresh:
                    await self.refresh()

            elif self.db_element and not self.should_exists:
                await self.drop()
        
            await self.manageInConfig()

        return self

    async def create(self):
        """Create the view.
        """
        
        await self.data_logging.logEvent(
            'create',
            'loading'
        )
        
        await self.query_builder.create(
            self.name,
            "view",
            self.schema_name
        ).materialized(
            self.is_materialized
        ).sqlStatement(
            self.query
        ).built().asyncExecute(
            data_logging = self.data_logging
        )
            
        await self.getDBElement()

        if self.grants is None:
            self.grants = self.db_element.get('grants')
            
    async def select(
        self,
        where_statement:list=None,
        columns:list=None,
        limit:int=None,
        loaded_rows:int = None,
        **kwargs
    ) -> View:
        """Select data.

        Args:
            where_statement (list, optional): Where conditions. Defaults to None.
            columns (list, optional): Columns to select. Defaults to None.
        """
        
        await self.data_logging.logEvent(
            'select',
            'loading'
        )

        if self.is_database_saved:
            self.data = Data(
                await self.query_builder.select(
                    self.name,
                    schema_name=self.schema_name,
                    limit = limit
                ).columns(
                    columns if columns else self.columns
                ).where(
                    where_statement
                ).built().asyncExecute(
                    data_logging = self.data_logging,
                    **kwargs
                ),
                meta_columns=[],
                columns = self.columns,
                geometry_saved_type='text',
                name = self.name,
                loaded_rows= loaded_rows
            )
        else:
            self.data = Data(
                await self.query_builder.select().sqlStatement(
                    self.query,
                    definition='select'
                ).where(
                    where_statement
                ).built().asyncExecute(
                    data_logging = self.data_logging,
                    **kwargs
                ),
                meta_columns=[],
                columns=[],
                geometry_saved_type='text',
                name = self.name,
                loaded_rows= loaded_rows
            )

        return self
   
    async def manageGrants(self) :
        """Grant privileges on schema.
        """
        
        if self.is_database_saved:
        
            await self.data_logging.logEvent(
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
                    await self.query_builder.grant(
                        self.name,
                        self.element_type,
                        self.schema_name,
                        **grant
                    ).built().asyncExecute(
                        data_logging = self.data_logging
                    )

            for revoke in db_grants:
                await self.query_builder.revoke(
                    self.name,
                    self.element_type,
                    self.schema_name,
                    **revoke   
                ).built().asyncExecute(
                    data_logging = self.data_logging
                )

            self.db_element['grants'] = copy.deepcopy(self.grants)
    
    async def manageIndexes(self) -> None:
        """Create indexes.
        """
        
        await self.data_logging.logEvent(
            'index',
            'loading'
        )
                
        db_indexes:List[dict] = copy.deepcopy(
            self.db_element.get('indexes')
        )

        for index in self.indexes:
            if (
                index not in db_indexes 
                and not index.get('constraint_type')
            ):
 
                await self.query_builder.create(
                    index.get('name'),
                    'index'
                ).uniqueIndex(
                    index.get('is_unique')
                ).onIndex(
                    self.name,
                    self.schema_name
                ).usingIndex(
                    index.get('method'),
                    index.get('columns')
                ).built().asyncExecute(
                    data_logging = self.data_logging
                )
            
            else:
                db_indexes.remove(index)

        for index in db_indexes:
            if not index.get('constraint_type'):
                await self.query_builder.drop(
                    index.get('name'),
                    'index',
                    exists_condition=True
                ).built().asyncExecute(
                    data_logging = self.data_logging
                )

        self.db_element['indexes'] = copy.deepcopy(self.indexes)
        await self.data_logging.logEvent()

    async def replace(self) -> None:
        
        await self.data_logging.logEvent(
            'replace',
            'loading'
        )
            
        await self.query_builder.create(
            self.name,
            "view",
            self.schema_name
        ).replace().sqlStatement(
            self.query,
            self.directory_query,
            self.file_query
        ).built().asyncExecute(
            data_logging = self.data_logging
        )
        
        await self.data_logging.logEvent()

    def transform(
        self,
        transformations
    ) -> None:
        
        self.data.transform(transformations)

    def setData(
        self,
        data:Union[Data,pandas.DataFrame,None]
    ) -> None:
    
        if data is not None:
            if isinstance(data,Data):
                self.data = data
            elif isinstance(data,pandas.DataFrame):
                if hasattr(self,data):
                    self.data.frame = data
                else:
                    self.data = Data(data)
        return self

    async def get(
        self,
        to_get:str='self'
    ) -> Union[View,Data]:
        if to_get == 'self':
            return self
        
        if to_get == 'data':
            return copy.deepcopy(self.data)
        
        return getattr(self,to_get)
    
    async def executeDataAction(
        self,
        action_name:str,
        **kwargs
    ) -> Union[None,Data]:
        
        return await getattr(self,action_name)(**kwargs)

    async def refresh(self) -> None:
            
        await self.data_logging.logEvent(
            'refresh',
            'loading'
        )
          
        await self.query_builder.refresh(
            self.name,
            self.schema_name
        ).built().asyncExecute()
        
        await self.data_logging.logEvent(
            'refresh',
            'loaded'
        )
