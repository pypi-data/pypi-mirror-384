"""

"""
import os
import copy
import json
import logging
import datetime
import time
import socketio
import pandas

from datablender.base import QueryBuilder,Connection,AsyncConnection, File

class DataEventsTable:
    """Table to store data events.

    Attributes:
    ----------
        name

    Methods:
    ----------
        Methods

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        connection:Connection
    ):
        self.connection = connection
        self.query_builder = QueryBuilder(self.connection)
        self.getOtherElementsName()

        self.setConfig(**next(
            (
                config for config in
                self.query_builder.config['elements']['table']['configs']
                if config['name'] == 'data_events'
            ),
            {}
        ))
        self.manage()
    
    def setConfig(
        self,
        columns,
        constraints,
        indexes,
        **kwargs
    ) -> None:
        
        self.columns  = columns
        self.constraints = constraints
        self.indexes = indexes
        
    def getOtherElementsName(self) -> None:
        """Get other element's name in database.
        """
        elements_name = self.query_builder.selectElements('table').execute()
        self.elements_name = elements_name[elements_name['schema_name']=='public']['name'].tolist()

    @property
    def exists(self) -> bool:
        """
        Check if the table exists in the database.

        Returns:
            bool: Exists in the database or not.
        """
        return 'data_events' in self.elements_name

    def manage(self) -> None:
        if not self.exists:
            self.create()
            
    def create(self) -> None:
        """Create a SQL element.

        Args:
            columns (dict, optional): Table colums if it's a table. Defaults to None.
        """

        self.query_builder.create(
            'data_events'
        ).columns(
            self.columns
        ).constraints(
            self.constraints
        ).built().execute()

        if self.indexes:
            for index in self.indexes:
                self.query_builder.create(
                    index['name'],
                    'index'
                ).uniqueIndex(
                    index['is_unique']
                ).onIndex(
                    index['name'],
                    index['schema_name']
                ).built().execute()

        self.elements_name.append('data_events')

    def logEvent(
        self,
        element_type,
        name,
        action,
        schema_name,
        file_id,
        duration,
        **kwargs
    ):
        
        event_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        self.query_builder.insert(
            'data_events'
        ).columns(
            [
               column['name'] for column in self.columns
               if column['name'] != 'id'
            ]
        ).values(
            [
                element_type,
                name,
                action,
                schema_name,
                file_id,
                event_time,
                duration
            ]
        ).built().execute(**kwargs)

class DataLogging:
    """Class to log data events.

    Attributes:
    ----------
        Attributes

    Methods:
    ----------
        Methods

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        connection:Connection,
        event_server:socketio.Server=None,
        initiate_table = True
    ):
        self.connection = connection
        self.event_server = event_server
        self.query_builder = QueryBuilder(self.connection)
        
        self.element_type = None
        self.name = None
        self.id = None
        self.schema_id = None
        self.schema_name = None

        self.start_time = None

        if initiate_table:
            self.initiateTable()

    def setElement(
        self,
        element_type:str,
        name:str,
        id:int =None,
        schema_id = None,
        schema_name = None
    ) -> None:
    
        self.element_type = element_type
        self.name = name
        self.id = id
        self.schema_id = schema_id
        self.schema_name = schema_name

    def initiateTable(self) ->None:
        
        self.table = DataEventsTable(
            self.connection
        )

    def logEvent(
        self,
        action:str,
        status:str,
        file_id:int=None,
        **kwargs
    ):

        actions = {
            'create':'Create',
            'drop':'Drop',
            'owner':'Set owner of',
            'grant':'Grant',
            'rename':'Rename',
            'select':'Select from',
            'update':'Update',
            'insert':'Insert in',
            'delete':'Delete in',
            'copy':'Copy data in',
            'update':'Update data of',
            'extract':'Extract data from',
            'transform':'Transform data from',
            'validate':'Validate data from',
            'save':'Save data from',
            'refresh':'Refresh materialized',
            'index':'Index',
            'columns':'Manage columns',
            'constraints':'Constraint'
        }
        
        logging.basicConfig(
            format='%(asctime)s - %(message)s',
            level=logging.INFO
        )
        
        if status == 'loading':
            self.start_time = time.time()
            logging.info(
                ' '.join([
                    actions[action] if action in actions else action,
                    self.element_type,
                    self.name
                ])+'.'
            )

        elif status == 'loaded':
            duration = round(time.time()-self.start_time, 2)

            self.table.logEvent(
                self.element_type,
                self.name,
                action,
                self.schema_name,
                file_id,
                duration,
                **kwargs
            )
            if duration > 0.5:
                logging.info(
                    '\t Done ({} s).'.format(duration)
                )

            self.start_time = None

        if self.event_server:
            self.event_server.emit(
                'data_event',
                {
                    'element':{
                        'element_type':self.element_type,
                        'id':self.id
                    },
                    'name':action,
                    'status':status,
                    'file_id':int(file_id) if file_id else None
                }
            )

class AsyncDataEventsTable:
    """Table to store data events.

    Attributes:
    ----------
        name

    Methods:
    ----------
        Methods

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        connection:AsyncConnection
    ):
        self.connection = connection
        self.query_builder = QueryBuilder(self.connection)

        self.setConfig(**next(
            (
                config for config in
                self.query_builder.config['elements']['table']['configs']
                if config['name'] == 'data_events'
            ),
            {}
        ))
    
    def setConfig(
        self,
        columns,
        constraints,
        indexes,
        **kwargs
    ) -> None:
        
        self.columns  = columns
        self.constraints = constraints
        self.indexes = indexes
        
    async def getOtherElementsName(self) -> None:
        """Get other element's name in database.
        """
        elements_name = await self.query_builder.selectElements('table').asyncExecute()
        self.elements_name = elements_name[
            elements_name['schema_name']=='public'
        ]['name'].tolist()

    @property
    def exists(self) -> bool:
        """
        Check if the table exists in the database.

        Returns:
            bool: Exists in the database or not.
        """
        return 'data_events' in self.elements_name

    async def manage(self) -> None:
        await self.getOtherElementsName()
        if not self.exists:
            await self.create()
            
    async def create(self) -> None:
        """Create a SQL element.

        Args:
            columns (dict, optional): Table colums if it's a table. Defaults to None.
        """

        await self.query_builder.create(
            'data_events'
        ).columns(
            self.columns
        ).constraints(
            self.constraints
        ).built().asyncExecute()

        if self.indexes:
            for index in self.indexes:
                await self.query_builder.create(
                    index['name'],
                    'index'
                ).uniqueIndex(
                    index['is_unique']
                ).onIndex(
                    index['name'],
                    index['schema_name']
                ).built().asyncExecute()

        self.elements_name.append('data_events')

    async def logEvent(
        self,
        event_name,
        element_type,
        element_configuration:dict,
        duration,
        action_name,
        action_time,
        action_element_type,
        action_element_configuration:dict,
        informations:dict,
        **kwargs
    ):
        
        event_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        await self.query_builder.insert(
            'data_events'
        ).columns(
            [
               column['name'] for column in self.columns
               if column['name'] != 'id'
            ]
        ).values(
            [
                event_name,
                element_type,
                element_configuration.get('id',None),
                element_configuration.get('name',None),
                element_configuration.get('schema_name',None),
                event_time,
                duration,
                action_name,
                action_time if action_name else event_time,
                action_element_type if action_name else None,
                action_element_configuration.get('id',None) if action_name else None,
                action_element_configuration.get('name',None) if action_name else None,
                action_element_configuration.get('schema_name',None) if action_name else None,
                json.dumps(informations)
            ]
        ).built().asyncExecute(**kwargs)

class AsyncDataEventsView:
    """description

    Attributes:
    ----------
        Attributes

    Methods:
    ----------
        Methods

    Examples:
    ----------
        >>> Example

    """
    def __init__(
        self,
        connection:AsyncConnection
    ):
        self.connection = connection
        self.query_builder = QueryBuilder(self.connection)

        self.name = 'data_events_'
        self.schema_name = 'public'
        
    async def getOtherElementsName(self) -> None:
        """Get other element's name in database.
        """
        elements_name = await self.query_builder.selectElements('view').asyncExecute()
        self.elements_name = elements_name[
            elements_name['schema_name']==self.schema_name
        ]['name'].tolist()

    @property
    def exists(self) -> bool:
        """
        Check if the table exists in the database.

        Returns:
            bool: Exists in the database or not.
        """
        return self.name in self.elements_name

    async def manage(self) -> None:
        await self.getOtherElementsName()
        if not self.exists:
            await self.create()
            
    async def create(self) -> None:
        """Create a SQL element.

        Args:
            columns (dict, optional): Table colums if it's a table. Defaults to None.
        """

        query = File(
            path= os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..',
                'postgresql',
                'queries',
                '{}.sql'.format(self.name)
            )
        ).read().content   

        await self.query_builder.create(
            self.name,
            "view",
            self.schema_name
        ).materialized(
            False
        ).sqlStatement(
            query
        ).built().asyncExecute()

        self.elements_name.append(self.name)

    async def selectEvents(self) -> pandas.DataFrame:
        events = await self.query_builder.select(
            self.name,
            schema_name=self.schema_name
        ).built().asyncExecute()
        events['action_time'] = events['action_time'].dt.strftime('%Y-%m-%d %H:%M:%s')
        return events
    
class AsyncDataLogging:
    """Class to log data events.

    Attributes:
    ----------
        Attributes

    Methods:
    ----------
        Methods

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        connection:AsyncConnection,
        element_type:str,
        event_server:socketio.AsyncServer=None
    ):
        self.connection = connection
        self.event_server = event_server
        self.query_builder = QueryBuilder(self.connection)

        self.element_type:str = element_type
        self.element_configuration:dict = None

        self.event_name = None
        self.start_time = None
        self.informations:dict = None

        self.action_name = None
        self.action_element_type = None
        self.action_configuration = None
        self.action_time = None
        
        self.table = AsyncDataEventsTable(
            self.connection
        )
        self.view = AsyncDataEventsView(
            self.connection
        )

    async def manageTable(self) -> None:
    
        await self.table.manage()
        await self.view.manage()

    @property
    def action(self) -> None:
    
        return {
            'name':self.action_name,
            'element_type':self.action_element_type,
            'configuration':self.action_configuration,
            'action_time':self.action_time
        }
            
    def setActionName(
        self,
        name:str,
        element_type:str,
        configuration:dict,
        action_time:str=None
    ) -> None:
        
        self.action_name = copy.deepcopy(name)
        self.action_element_type = element_type
        self.action_configuration = configuration
        
        self.action_time = action_time if action_time is not None else datetime.datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

    def updateConfiguration(
        self,
        configuration:dict,
        element_type:str
    ) -> None:

        self.element_configuration = configuration
    
        if (
            self.action_configuration is not None
            and self.action_element_type is not None
            and self.action_element_type == element_type
            and self.action_configuration.get('name') == configuration.get('name')
        ):
            self.action_configuration = configuration
        
    async def logEvent(
        self,
        event_name:str = None,
        status:str=None,
        error:Exception = None,
        informations:dict = {},
        **kwargs
    ):
        
        duration = None

        if event_name is not None:
            self.event_name = event_name 
            self.informations = informations
        
        if error is not None:
            status = 'error'
        elif status is None:
            status = 'loaded'

        actions = {
            'create':'Create',
            'drop':'Drop',
            'owner':'Set owner of',
            'grant':'Grant',
            'rename':'Rename',
            'select':'Select from',
            'update':'Update',
            'insert':'Insert in',
            'delete':'Delete in',
            'copy':'Copy data in',
            'update':'Update data of',
            'extract':'Extract data from',
            'transform':'Transform data from',
            'validate':'Validate data from',
            'save':'Save data from',
            'refresh':'Refresh materialized',
            'index':'Index',
            'columns':'Manage columns',
            'constraints':'Constraint'
        }
        
        logging.basicConfig(
            format='%(asctime)s - %(message)s',
            level=logging.INFO
        )
        
        if status == 'loading':
            self.start_time = time.time()
            logging.info(
                ' '.join([
                    actions[self.event_name] if self.event_name in actions else self.event_name,
                    self.element_type,
                    self.element_configuration.get('name')
                ])+'.'
            )

        elif status == 'loaded':
            duration = round(time.time()-self.start_time, 2)

            await self.table.logEvent(
                self.event_name,
                self.element_type,
                self.element_configuration,
                duration,
                self.action_name,
                self.action_time,
                self.action_element_type,
                self.action_configuration,
                self.informations,
                **kwargs
            )
            if duration > 0.5:
                logging.info(
                    '\t Done ({} s).'.format(duration)
                )

        elif status == 'error':
            logging.error(error)  # ERROR:root:division by zero
            
        event =  {
            'element':{
                'element_type':self.element_type,
                **self.element_configuration
            },
            'action':{
                'name':self.action_name,
                'time':self.action_time,
                'element':{
                    'element_type':self.action_element_type,
                    **self.action_configuration
                }
            } if self.action_name else {},
            'name':self.event_name,
            'status':status,
            'error':{
                'name':type(error).__name__,
                'description':str(error)
            } if error is not None else None,
            'duration':duration,
            'time':self.start_time,
            'informations':self.informations
        }
        
        # if self.event_server is not None:
        #     await self.event_server.emit(
        #         'data_event',
        #         event
        #     )
