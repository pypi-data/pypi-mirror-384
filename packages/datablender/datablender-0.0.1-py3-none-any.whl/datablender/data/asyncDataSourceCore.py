"""

"""

from __future__ import annotations
from typing import Union, Dict,List

import os
import re
import copy
import time
import datetime
import aiohttp
import pandas
import random

from smb.SMBConnection import SMBConnection

from datablender.base import (
    DataConfiguration,
    Connection,
    File,
    DataLogging,
    Data,
    getFunction,
    Request,
    Bot,
    DataElement,
    Directory,
    AsyncRequest,
    AsyncDataLogging,
    AsyncConnection,
    AsyncDataConfiguration,
    AsyncDataElement
)
from datablender.database import (
    AsyncTable,
    AsyncDatabase,
    mode_level
)

from datablender.data.directoryElementController import DirectoryElementController
from datablender.data.dataVersion import AsyncDataVersion
from datablender.data.filesTable import AsyncFilesTable

class AsyncRawDataFile(File):
    """A file containing raw data from the source.

    Attributes:
    ----------
        name (str): File name.
        directory_name (str): Directory name in which the file will be saved.
        rename_parameters (dict): Parameters to rename the saved file after downloading.

    Methods:
    ----------
        stUrl() -> str: Set the url to fetch the file from web.
        setDirectoryName(directory_name,set_from,method,values,value) -> str: Get file new name after downloading and before saving.

    Examples:
    ----------
        >>> import datablender
        >>> files = [
        >>>     datablender.RawDataFile(**file,directory_name=directory_name,**file_params)
        >>>     for file in files
        >>> ]
    """
    def __init__(
        self,
        is_secure:bool = True,
        domain_name:str = None,
        host:str = None,
        port:int = None,
        url:str=None,
        directory_name:str=None,
        downloading_name:str=None,
        rename_parameters:dict={},
        directory_name_setter:dict={},
        data_logging:AsyncDataLogging = None,
        file_server:SMBConnection = None
    ):
        """Initiate the raw data file.

        Args:
            url (str, optional): Full initial file url. Defaults to None.
            directory_name (str, optional): Base directory name in which the file will be saved. Defaults to None.
            downloading_name (str, optional): Initial file name at the moment of downloading. Defaults to None.
            rename_parameters (dict, optional): Parameters to rename the saved file after downloading. Defaults to {}.
            directory_name_setter (dict, optional): Parameters to set the directory name in which the file will be saved. Defaults to {}.
        """

        self.host = host
        self.port = port
        self.rename_parameters = rename_parameters

        self.data_logging = data_logging

        self.download_status = 'existant'
        
        if 'http' in url:
            if 'https' in url:
                self.is_secure = True                
                url = url.replace('https://','')
            else:
                self.is_secure = False
                url = url.replace('http://','')

            self.setName(url)

            self.domain_name,self.url_path = (
                os.path.dirname(
                    url
                ) if self.file_included else url
            ).split('/',1)

        else:
            self.is_secure = is_secure
            self.domain_name = domain_name
            self.setName(url)
            
            self.url_path = os.path.dirname(
                url
            ) if self.file_included else url

        if self.name or downloading_name:
            super(AsyncRawDataFile,self).__init__(
                self.setDirectoryName(
                    directory_name,
                    **directory_name_setter
                ) if directory_name_setter else directory_name,
                downloading_name if downloading_name else self.name,
                file_server=file_server
            )
        
        elif directory_name:
            self.directory_name = directory_name

    @property
    def informations(self) -> dict:

        return {
            'name':self.name,
            'directory_name':self.directory_name,
            'download_status':self.download_status
        }
        
    def setName(
        self,
        url:str
    ) -> None:
        last_url_element = url.split('/',-1)[-1]#DonneesOuvertes2023_12.zip
           
        self.file_included = (
            '.' in last_url_element
            and len(last_url_element.split('.',-1)[-1])<31
        )
        self.name = os.path.basename(url) if self.file_included else None

    def setDirectoryName(
        self,
        directory_name:str,
        set_from:str=None,
        method:str=None,
        values:dict=None,
        value:str=None
    ) -> str:
        """Set the directory name in which the files will be saved. A base directory name is provided, and a specified value
        is join to this base directory name. The value can come from a list and can be unique.

        Args:
            directory_name (str): Base directory name.
            set_from (str, optional): Attribute from which the name will be set. Defaults to None.
            method (str, optional): Method to set the directory name. Defaults to None.
            values (dict, optional): List of values to chose from according to the source. Defaults to None.
            value (str, optional): Unique value to join to the directory name. Defaults to None.

        Returns:
            str: Full directory name.
        """
        
        source:str = getattr(self,set_from) if set_from else None

        if method == 'contain':
            for value in values:
                if value in source:
                    return os.path.join(
                        directory_name,
                        values[value]
                    )

        elif method == 'set':
            return os.path.join(
                directory_name,
                value
            )

    def getNewName(
        self,
        rename_from:str=None,
        method:str=None,
        character:str=None,
        position:str=None,
        add_time:bool = False
    ) -> str:
        """Get file new name after downloading and before saving.

        Args:
            rename_from (str, optional): File attribute name to use to rename the file. Defaults to None.
            method (str, optional): Method to get the new name from the file attribute. Defaults to None.
            character (str, optional): Character use to split the file attribute. Defaults to None.
            position (str, optional): Position of the sub string after the split. Defaults to None.

        Returns:
            str: The new file name.
        """
        
        source:str = getattr(self,rename_from)
        
        if method == 'split':

            source_split = source.split(
                character
            )


            if source_split[position[-1]] == 'latest':
                new_name =  '{}_{}'.format(source_split[position[0]],'20231231')

            elif isinstance(position,list):
                new_name =  '_'.join((source_split[p] for p in position))
            
            else:
                new_name =  source_split[position]
        
            if add_time:
                return '{}{}{}'.format(
                    new_name,
                    str(round((int(source_split[3])/2000)*24)).zfill(2),
                    str(round((int(source_split[3])/2000)*60)).zfill(2)
                )
            return new_name
        
        return self.name

    async def download(
        self,
        session
    ) -> None:
        """Download file from the web.
        """
        
        await self.data_logging.logEvent(
            'download',
            'loading',
            informations = {
                'name':self.name,
                'directory_element':self.directory_name
            }
        )

        try:

            self.request = AsyncRequest(
                self.is_secure,
                self.host,
                self.port,
                self.domain_name,
                session = session
            )

            self.request.addElement(self.url_path)

            self.request.addElement(
                self.name
            ) if self.file_included else None
            
            async with self.request.session.get(
                self.request.url,
                allow_redirects=True
            ) as response:
                assert response.status == 200
                
                if self.name is None and "content-disposition" in response.headers:
                    header = response.headers["content-disposition"]
                    self.name = header.split("filename=")[1]


                    if (
                        (
                            Directory(self.directory_name,self.file_server).checkIfExists(self.name)
                            and not self.rename_parameters
                        ) or (
                            self.rename_parameters
                            and Directory(self.directory_name,self.file_server).checkIfExists(self.getNewName(
                                **self.rename_parameters
                            ))
                        )
                    ):
                        return

                if(
                    (
                        Directory(self.directory_name,self.file_server).checkIfExists(self.name)
                        and not self.rename_parameters
                    ) or (
                        self.rename_parameters
                        and Directory(self.directory_name,self.file_server).checkIfExists(self.getNewName(
                            **self.rename_parameters
                        )+'.'+self.extension)
                    )
                ):
                    return

                chunk = await response.content.read()
                self.write(chunk)

            if self.rename_parameters:
                self.rename(
                    self.getNewName(
                        **self.rename_parameters
                    )
                )

        except Exception as error:
            await self.data_logging.logEvent(
                error=error
            )
        else:
            await self.data_logging.logEvent()

    def setStatus(
        self,
        elements:List[dict],
        directory_name:str
    ) -> None:
    
        if (
            self.name is not None
            and os.path.abspath(
                self.directory_name
            ) == os.path.abspath(
                directory_name
            )
        ):            
            self.download_status = 'new' if self.name not in [
                element.get('name')
                for element in elements
            ] else 'existant'
        elif not elements or self.name is None:
            self.download_status = 'new'

class AsyncDataFetcher:
    """Class to fetch data.

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
        is_secure:bool = True,
        domain_name:str = None,
        host:str = None,
        port:int = None,
        directory_name:str = None,
        bot_actions:list = [],
        downloading_name:str = None,
        rename_parameters:str = None,
        directory_name_setter:dict = {},
        files:list = [],
        request_params:dict=[],
        data_logging:AsyncDataLogging=None,
        loop =None,
        actions:List[dict] = [],
        file_server:SMBConnection = None,
        schema_name:str =None
    ):

        self.is_secure=is_secure
        self.host=host
        self.port=port
        self.domain_name=domain_name
        self.directory_name=directory_name
        self.file_server=file_server
        self.schema_name=schema_name

        self.downloading_name=downloading_name
        self.rename_parameters=rename_parameters
        self.directory_name_setter=directory_name_setter

        self.files = files
        self.bot_actions = bot_actions
        self.actions = actions
        self.request_params = request_params

        self.data_logging = data_logging
        self.loop = loop

        self.raw_files:List[AsyncRawDataFile]=[]
        self.raw_data= None

        self.access_token = None

    @property
    def configuration(self) -> None:
    
        return {
            'is_secure': self.is_secure,
            'domain_name': self.domain_name,
            'host': self.host,
            'port': self.port,
            'downloading_name': self.downloading_name,
            'rename_parameters': self.rename_parameters,
            'directory_name_setter': self.directory_name_setter,
            'bot_actions': self.bot_actions,
            'files': self.files,
            'request_params':self.request_params
        }

    def setRawFiles(
        self,
        files:List[str] = [],
        is_multi_fetcher:bool =False
    ) -> None:
        if not files:
            files = self.files

        if is_multi_fetcher and self.domain_name and '.' in self.domain_name:
            directory_name = os.path.join(
                self.directory_name,
                self.domain_name.split('.')[0]
            )

            Directory(
                directory_name,
                self.file_server
            ).manage()

        else:
            directory_name = self.directory_name


        self.raw_files = [
            AsyncRawDataFile(
                self.is_secure,
                self.domain_name,
                self.host,
                self.port,
                directory_name = directory_name,
                rename_parameters=self.rename_parameters,
                directory_name_setter=self.directory_name_setter,
                data_logging=self.data_logging,
                file_server=self.file_server,
                **(copy.deepcopy(file) if isinstance(file,dict) else {
                    'url':file,
                    'downloading_name':self.downloading_name
                })
            )
            for file in files
        ] 

    async def fetchFiles(
        self,
        is_multi_fetcher:bool =False
    ):

        await self.data_logging.logEvent(
            'fetchFiles',
            'loading',
            informations={
                'directory_name':self.directory_name
            }
        )

        try: 
            if self.files:
                self.setRawFiles()

            elif self.bot_actions:

                bot = Bot(
                    is_secure=self.is_secure,
                    domain_name=self.domain_name,
                    host=self.host,
                    port=self.port,
                    schema_name=self.schema_name,
                    directory_name=self.directory_name
                )

                bot.open()
                bot.executeActions(
                    copy.deepcopy(self.bot_actions)
                )

                bot.close()
                self.setRawFiles(
                    list(set(bot.results)),
                    is_multi_fetcher
                )

            elif self.actions:
                await self.executeActions(is_multi_fetcher)

        except Exception as error:
            await self.data_logging.logEvent(
                error = error
            )
        else:
            await self.data_logging.logEvent()
          
    async def downloadFiles(self):
        async with aiohttp.ClientSession(
            loop=self.loop,
            connector=aiohttp.TCPConnector(verify_ssl=False)
        ) as session:
            [
                await file.download(session)
                for file in self.raw_files
                if file.download_status == 'new'
            ]
            
    async def fetchDataFromRequest(self) -> None:
        await self.data_logging.logEvent(
            'fetch',
            'loading'
        )

        try:
            async with aiohttp.ClientSession(loop=self.loop) as session:

                request = AsyncRequest(
                    self.is_secure,
                    self.host,
                    self.port,
                    self.domain_name,
                    session=session
                )
                        
                for element in self.request_params.get('elements'):
                    request.addElement(element)

                if isinstance(self.request_params.get('params'),list):
                    self.raw_data = []
                    for params in self.request_params.get('params'):

                        async with request.session.get(
                            request.url,
                            params=params
                        ) as response:
                            assert response.status == 200
                            data = await response.json()
                            self.raw_data = [
                                *self.raw_data,
                                *data[self.request_params.get('data_attribute')]
                            ]

                elif isinstance(self.request_params.get('params'),dict):
                    async with request.session.get(
                        request.url,
                        params=self.request_params.get('params')
                    ) as response:
                        assert response.status == 200
                        data = await response.json()
                        self.raw_data = data[
                            self.request_params.get('data_attribute')
                        ] 
                    
        except Exception as error:
            await self.data_logging.logEvent(
                error
            )
        else:
            await self.data_logging.logEvent()

    async def executeActions(
        self,
        is_multi_fetcher:bool =False
    ) -> None:
        for action in self.actions:
            await getattr(self,action.pop('name'))(
                is_multi_fetcher=is_multi_fetcher,
                **action
            )

    async def setToken(self,is_multi_fetcher) -> None:
        ## Token
        token_file = File(
            os.getenv('code_directory'),
            'token.json'
        )
        
        refresh = False
        if token_file.exists:
            token_file.read()
            if (
                datetime.datetime.now(datetime.timezone.utc) >
                datetime.datetime.fromisoformat(
                    token_file.content.get('expiration_datetime_utc').replace('Z', '+00:00')
                )
            ):
                refresh= True
            else:
                self.access_token = token_file.content
        else:
            refresh= True
        
        if refresh:
            async with aiohttp.ClientSession(loop=self.loop) as session:
                token_request = AsyncRequest(
                    self.is_secure,
                    self.host,
                    self.port,
                    self.domain_name,
                    session=session
                )
                token_request.addElement('v1')
                token_request.addElement('tokens')

                async with token_request.session.post(
                    token_request.url,
                    json = {
                        "refresh_token": os.getenv('token')
                    }
                ) as response:
                    assert response.status == 200
                    self.access_token = await response.json()
                    token_file.write(self.access_token)

    async def get(
        self,
        url_elements:List[str],
        params:dict = {},
        to_get:str = None,
        list_element:dict = None,
        date:str =None,
        is_multi_fetcher:bool = False
    ) -> None:
        # List of feeds     
        async with aiohttp.ClientSession(loop=self.loop) as session:
            request = AsyncRequest(
                self.is_secure,
                self.host,
                self.port,
                self.domain_name,
                session=session
            )

            for element in url_elements:
                if isinstance(element,dict):
                    element = list_element[element.get('key')]
                    
                request.addElement(element)

            async with request.session.get(
                request.url,
                headers = {"Authorization": "Bearer {}".format(self.access_token.get('access_token'))} if self.access_token else {},
                params=params
            ) as response:
                assert response.status == 200
                response_json:dict = await response.json()

                if to_get:
                    setattr(
                        self,
                        to_get,
                        response_json.get(to_get)
                    )

                elif list_element and date:
                    feeds:List[dict] = []
                    date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
                    for feed in response_json:
                        # 2025-01-09T00:22:56.418514Z
                        feeds.append({
                            **feed,
                            'timedelta':abs(
                                date-datetime.datetime.strptime(
                                    feed['downloaded_at'],
                                    "%Y-%m-%dT%H:%M:%S.%fZ"
                                ).date()
                            )
                        })

                    timedelta_min = min([f.get('timedelta') for f in feeds])
                    
                    self.raw_files.append(
                        AsyncRawDataFile(
                            self.is_secure,
                            self.domain_name,
                            self.host,
                            self.port,
                            copy.deepcopy(next((
                                f.get('hosted_url') for f in feeds
                                if timedelta_min == f.get('timedelta')
                            ))),
                            directory_name=self.directory_name,
                            downloading_name = self.downloading_name,
                            rename_parameters = self.rename_parameters,
                            directory_name_setter=self.directory_name_setter,
                            data_logging=self.data_logging
                        )
                    )
                
                elif list_element:

                    if is_multi_fetcher and self.domain_name and '.' in self.domain_name:
                        directory_name = os.path.join(
                            self.directory_name,
                            self.domain_name.split('.')[0]
                        )

                        Directory(
                            directory_name,
                            self.file_server
                        ).manage()

                    else:
                        directory_name = self.directory_name

                    self.raw_files.extend([
                        AsyncRawDataFile(
                            self.is_secure,
                            self.domain_name,
                            self.host,
                            self.port,
                            f['hosted_url'],
                            directory_name=directory_name,
                            downloading_name = self.downloading_name,
                            rename_parameters = self.rename_parameters,
                            directory_name_setter=self.directory_name_setter,
                            data_logging=self.data_logging,
                            file_server=self.file_server
                        ) for f in response_json[0:1]
                    ])

    async def getFilesFromList(
        self,
        url_elements:List[str],
        params:dict = {},
        list_from:str = None,
        list_from_filter:list = [],
        list_from_filter_key:str = None,
        date:str =None,
        is_multi_fetcher:bool = False
    ) -> None:

        for list_element in getattr(self,list_from):
            if list_element[list_from_filter_key] in list_from_filter:
                await self.get(
                    url_elements,
                    params,
                    list_element = list_element,
                    date = date,
                    is_multi_fetcher = is_multi_fetcher
                )

class AsyncDataSourceCore(AsyncDataElement):
    """Represent a data source.

    The configuration is initiate with the name, with the schema, directory name and file name or from the
    data configuration.

    Attributes:
    ----------
        configuration

    Methods:
    ----------
        setSchema(self) -> None: Set the schema object.

    Examples:
    ----------
        >>> import datablender
        >>> data_source = datablender.DataSource(
        >>>     datablender.Connection()
        >>>     datablender.DataConfiguration(activate = True)
        >>> )
        >>> print(data_source.schema)
        public
        >>> data_source.data_source_directory.name # Your current directory or env directory + '/data'
        >>> data_source.code_directory.name # Your current directory or env directory + '/code'
        >>> print(data_source.file.name)
        None
        >>> print(data_source.tables[0].name)
        data

    """
    def __init__(
        self,
        connection:AsyncConnection,
        data_configuration:AsyncDataConfiguration,
        id:int=None,
        name:str = None,
        status:str = 'developpement',
        content:dict=None,
        fetch:List[dict] = [],
        extract:List[dict] = [],
        transform:List[dict] = [],
        save:List[dict]=[],
        directory_name:str = None,
        control:dict = {},
        data_version:dict = {},
        database:AsyncDatabase = None,
        database_name:str = None,
        schema_id:int = None,
        schema_name:str = 'public',
        tables:Union[str,List[str],List[dict]] = None,
        event_server=None,
        views:List[Dict[str,any]] = [],
        loop =None,
        file_server:SMBConnection = None
    ):
        
        # structure in the data_config :
        # {
        #   schema_id:1,
        #   tables: [
        #     {
        #       'id':1,
        #       'schema_id':2
        #       'data_conditions':{}
        #     }
        #   ],
        #  data_version:{
        #   
        #  }
        # }
        # User can provide tables
        # table = 'households'
        # table = ['households','persons']
        # table = [
        #   {
        #     'name':'households',
        #     'data_conditions':{}
        #   }
        # ]
        super(AsyncDataSourceCore,self).__init__(
            connection,
            name,
            'data_source',
            status,
            data_configuration,
            True,
            id,
            content,
            event_server
        )

        self.directory_name = directory_name
        self.data_version_config = data_version

        self.element_controller = DirectoryElementController(**control)  
        self.loop = loop

        self.extract = extract
        self.transform = transform
        self.save = save

        self.schema_name = schema_name
        self.schema_id = schema_id
        self.tables_config = tables
        self.views = views

        self.file_server = file_server

        self.tables:List[AsyncTable] = []
        self.temporary_main_files:List[Dict[str,str]] = []
        
        self.setDataFetchers(fetch)

        self.database,self.initiate_database = (database,False) if database else (AsyncDatabase(
            self.connection,
            name = database_name if database_name else self.connection.database_name,
            data_configuration=self.data_configuration,
            event_server=self.data_logging.event_server
        ),True)

        self.data_logging.element_configuration = self.configuration

    async def initiate(self) -> AsyncDataSourceCore:

        self.data_logging.setActionName(
            'initiate',
            self.element_type,
            self.configuration
        )

        await self.data_logging.manageTable()

        if self.initiate_database:
            await self.database.initiate()

        await self.database.manage(
            data_logging_action = self.data_logging.action
        )

        self.files_table = await self.database.manageElement(
            {
                **next(
                    (
                        config for config in
                        self.query_builder.config['elements']['table']['configs']
                        if config['name'] == 'files'
                    ),
                    {}
                ),
                'status':'production'
            },
            'table',
            data_logging_action = self.data_logging.action
        )
        self.files_table.__class__ = AsyncFilesTable
        self.files_table:AsyncFilesTable

        self.main_files_view = await self.database.manageElement(
            {
                'name':'main_files',
                'directory_query':os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    '..',
                    'postgresql'
                ),
                'is_database_saved': True
            },
            'view',
            data_logging_action =self.data_logging.action
        )

        await self.manageAttributes()

        return self

    @property
    def configuration(self) -> dict:
        """Get configuration.

        Returns:
            dict: configuration.
        """
        return {
            'id':self.id,
            'name':self.name,
            'status':self.status,
            'content':self.content,
            'fetch':[
                data_fetcher.configuration for data_fetcher
                in self.data_fetchers
            ],
            'extract':self.extract,
            'transform':self.transform,
            'save':self.save,
            'directory_name':self.directory_name,
            'control':self.element_controller.configuration,
            'data_version':self.data_version.configuration if hasattr(
                self,
                'data_version'
            ) else self.data_version_config,
            'schema_id':self.schema_id,
            'tables':[
                {
                    'id':table.id,
                    'data_conditions':table.data_conditions[self.name]
                } for table in self.tables
            ],
            'views':self.views
        }
    
    @configuration.setter
    def configuration(self,new_config:dict):
        """Set the configuration.

        Args:
            new_config (dict): New configuration.

        Returns:
            Dict: configuration.
        """
        if new_config:
            [
                setattr(
                    self,
                    attribute_name,
                    new_config[attribute_name]
                    if attribute_name in new_config
                    else getattr(self,attribute_name)
                )
                for attribute_name
                in [
                    'name',
                    'status',
                    'content',
                    'extract',
                    'transform',
                    'save',
                    'directory_name',
                    'schema_id',
                    'views'
                ]
            ]
            
            if 'control' in new_config:
                self.element_controller.__init__(**new_config.get('control'))

            if 'fetch' in new_config:
                self.setDataFetchers(new_config.get('fetch'))

        return new_config
    
    async def setConfiguration(
        self,
        new_config:dict
    ) -> None:
    
        self.configuration = copy.deepcopy(new_config)
        await self.manageAttributes()
        if 'tables' in new_config:
            await self.setTables(
                copy.deepcopy(new_config).get('tables')
            )
        if 'data_version' in new_config:
            await self.setDataVersion(
                copy.deepcopy(new_config).get('data_version')
            )

    async def setTable(
        self,
        configuration:dict
    ) -> AsyncTable:
        
        if 'id' in configuration and isinstance(configuration.get('id'),str):
            configuration['name'] = configuration.get('id')
            configuration['id'] = None
        
        data_conditions = configuration.pop('data_conditions',{})
        
        table = await self.database.manageElement(
            {
                'schema_id':self.schema_id,
                'schema_name':self.schema_name,
                'status':copy.deepcopy(self.status),
                **configuration,
                'constraints':[
                    self.query_builder.generic_constraints[0],
                    *configuration.get('constraints',[])
                ],
                'partitions':{
                    'method':'list',
                    'column_names':[
                        'data_source_id'
                    ],
                    'partitions':[]
                } if self.data_configuration.active else {}
            },
            'table',
            ignore_new_config = True
        )
        
        return table.setDataConditions(
            self.name,
            data_conditions
        )

    async def setTables(
        self,
        table:Union[str,List[str],List[dict],None]
    ) -> None:
        
        self.tables = [
            await self.setTable(
                configuration if isinstance(
                    configuration,dict
                ) else {'name':configuration}
            )
            for configuration in (table if isinstance(table,list) else [table])
        ] if table else []

    async def manageDirectory(self) -> None:  
        
        if self.directory_name is None:

            data_host =os.getenv(
                'DATA_HOST',
                None
            )

            if self.file_server:
                pass

            elif data_host:

                self.file_server = SMBConnection(
                    'jgelb',#os.getenv('username'),
                    os.getenv('DATA_PASSWORD'),
                    'tests',
                    os.getenv('DATA_MACHINE_NAME')
                )
                self.file_server.connect(data_host,139)

                if 'sources' not in [
                    getattr(f,'filename') for f in self.file_server.listPath('data', "/")
                ]:
                    self.file_server.createDirectory('data','sources')
                    
                if self.schema_name not in [
                    getattr(f,'filename') for f in self.file_server.listPath('data', "/sources")
                ]:
                    self.file_server.createDirectory('data',
                        os.path.join(
                            'sources',
                            self.schema_name
                        )
                    )

                self.directory_name = os.path.join(
                    'sources',
                    self.schema_name,
                    self.name
                )

            else:

                self.directory_name = os.path.join(
                    os.getenv(
                        'DATA_DIRECTORY',
                        os.getcwd()
                    ),
                    'sources',
                    self.schema_name,
                    self.name
                )

            await self.manage(new_configuration={
                'directory_name':self.directory_name
            })

            for data_fetcher in self.data_fetchers:
                data_fetcher.directory_name = self.directory_name
                data_fetcher.file_server = self.file_server

        Directory(
            self.directory_name,
            self.file_server
        ).manage()
        
        return self.directory_name

    async def setDataVersion(
        self,
        data_version:dict
    ):
        if hasattr(self,'data_version'):
            values = data_version.get(
                'values',[]
            )
            tables = data_version.get(
                'tables',[]
            )
            views = data_version.get(
                'views',[]
            )

            if values or tables:
                self.data_version.active = True
                self.data_version.schema_id = self.schema_id
                self.data_version.schema_name = self.schema_name
                
                self.data_version.getValues(values)
                
                self.data_version.getTables(tables)
                [
                    await table.manage() for table
                    in self.data_version.tables
                ]

                await self.data_version.getViews(
                    self.directory_name
                )

        else:
            if 'views' in data_version or 'files' in data_version:
                await self.manageDirectory()
            
            self.data_version = AsyncDataVersion(
                self.connection,
                self.schema_name,
                self.data_configuration,
                active=True if data_version else False,
                schema_id = self.schema_id,
                database=self.database,
                directory_name=self.directory_name,
                **data_version
            )

            [
                await table.manage() for table
                in self.data_version.tables
            ]

            await self.data_version.getViews(
                self.directory_name,
                self.file_server
            )

    def setDataFetchers(
        self,
        fetch:List[dict]
    ) -> None:
        
        self.data_fetchers = [
            AsyncDataFetcher(
                **fetch_element,
                directory_name=self.directory_name,
                data_logging=self.data_logging,
                loop=self.loop,
                schema_name=self.schema_name
            )
            for fetch_element in fetch
        ]

    async def manage(
        self,
        manage_from='configuration',
        new_configuration:dict={}
    ) -> AsyncDataSourceCore:
        """Manage the data source configuration in the data configuration.

        Args:
            manage_from (str, optional): Manage the data source from. Defaults to 'configuration'.
            new_configuration (dict, optional): New configuration to manage the data source. Defaults to {}.

        Returns:
            DataSource: self.
        """
        
        self.data_logging.setActionName(
            'manage',
            self.element_type,
            self.configuration
        )
            
        await self.data_configuration.getElements('data_source')
        # If there is a new configuration, set all data source attributes from the new config
        if new_configuration:
            await self.setConfiguration(new_configuration)

        # If data source exists in the data configuration,
        # manage the data source in the data config
        if self.data_configuration.active:

            # If there is a config element, it means that it exists in config
            if self.config_element:
                # If there's not a new config from the user,
                # the config in the data configuration is the right one.
                if not new_configuration and manage_from != 'values':
                    await self.setConfiguration(self.config_element)

                # If status is inexistant, then delete it
                if self.status =='inexistant':
                    await self.data_configuration.deleteElement(
                        self.id,
                        self.element_type
                    )
                
                # Else if one of the attributes is different from the data configuration,
                # edit the data source
                
                elif any([
                    self.config_element[attribute] != self.configuration[attribute]
                    for attribute in self.config_element
                ]) and (new_configuration or manage_from == 'values'):
                    await self.data_configuration.putElement(
                        self.id,
                        self.configuration,
                        self.element_type
                    )
            
            # If it does not exists, then post the new config if there is one
            elif new_configuration and self.status !='inexistant':
                setattr(
                    self,
                    'id',
                    await self.data_configuration.postElement(
                        self.configuration,
                        self.element_type
                    )
                )

            # If it does not exists and there is no new config, but the name or id,
            # post it with the values of this object
            elif self.name or self.id:
                await self.setTables(self.tables_config)
                await self.setDataVersion(self.data_version_config)
                setattr(
                    self,
                    'id',
                    await self.data_configuration.postElement(
                        self.configuration,
                        self.element_type
                    )
                )
            # If it does not exists and there is no new config, no a name, no id
            # but a directory_name
            elif self.directory_name:
                # Set the schema and data version.
                await self.setDataVersion(self.data_version_config)
                # If it is not found, set the name and post it.
                if not self.findConfiguration():
                    self.name = os.path.basename(self.directory_name) 
                    await self.setTables(self.tables_config)
                    setattr(
                        self,
                        'id',
                        await self.data_configuration.postElement(
                            self.configuration,
                            self.element_type
                        )
                    )
                
            # If data config is active, but there is no directory name or data source name
            else:
                self.name = 'data'
                await self.setTables(self.tables_config)
                await self.setDataVersion(self.data_version_config)
                setattr(
                    self,
                    'id',
                    await self.data_configuration.postElement(
                        self.configuration,
                        self.element_type
                    )
                )

        # If data config is not active and there is not a new configuration,
        elif not new_configuration and manage_from != 'values':
            self.name = 'data' if not self.name else self.name
            await self.setTables(self.tables_config)
            await self.setDataVersion(self.data_version_config)

        if self.status =='inexistant':
            await self.deleteAllData()
            if self.directory_name:
                Directory(self.directory_name).delete()
        
        self.data_logging.action_name = None
        
        return self

    def findConfiguration(self) -> bool:
        directory_name = copy.deepcopy(self.directory_name)
        for source in getattr(self.data_configuration,'data_source'):

            directory_check = os.path.abspath(
                directory_name
            ) in os.path.abspath(source['directory_name'])

            schema_check = self.schema_id == source['schema_id']

            if directory_check and schema_check:
                self.configuration = source
                self.directory_name = directory_name
                return True

    def checkDataConditions(
        self,
        data_conditions:dict=None,
        table_name:str=None,
        file_name:str=None,
        data_condition_id:int=None,
        directory_name:str=None
    ) -> bool:
        """Check the data conditions using the table name and the file name.

        Args:
            table_name (str): Table name in which the data will be inserted.
            file_name (str): File name from which the data came from.
            data_conditions (dict, optional): Conditions to respect for the data. Defaults to None.

        Returns:
            bool: Indicate if the data conditions are respected or not.
        """
        conditions_pass = []
        
        if not data_conditions:
            return True

        if 'file_name' in data_conditions:
            conditions_pass.append(data_conditions.get('file_name') == file_name)
        
        if 'file_name_pattern' in data_conditions:
            conditions_pass.append(re.match(data_conditions.get('file_name_pattern'),file_name))
        
        if 'file_contains' in data_conditions:
            conditions_pass.append(data_conditions.get('file_contains') in file_name)
        
        if 'file_not_contains' in data_conditions:
            conditions_pass.append(data_conditions.get('file_not_contains') not in file_name)
        
        if 'directory_contains' in data_conditions:
            conditions_pass.append(data_conditions.get('directory_contains') in directory_name)
        
        if 'directory_not_contains' in data_conditions:
            conditions_pass.append(data_conditions['directory_not_contains'] not in directory_name)

        if 'table_name' in data_conditions and table_name:
            if isinstance(data_conditions['table_name'],list):
                conditions_pass.append(table_name in data_conditions['table_name'])
            else:
                conditions_pass.append(data_conditions['table_name'] == table_name)
        
        if 'table_name_pattern' in data_conditions:
            conditions_pass.append(re.match(data_conditions['table_name'],table_name))
        
        if 'id' in data_conditions and data_condition_id:
            conditions_pass.append(int(data_conditions['id'])==data_condition_id)

        if 'data_version' in data_conditions:
            data_version_value = next((v for v in self.data_version.values if v.name == data_conditions.get('data_version')['value_name'])).value
            
            data_condition_value = data_conditions.get('data_version')['value']
            data_condition_value_from = data_conditions.get('data_version')['value_from']
            data_condition_value_to = data_conditions.get('data_version')['value_to']

            if data_version_value is not None:

                if data_condition_value is not None:
                    conditions_pass.append(data_version_value==data_condition_value)

                if data_condition_value_from is not None:
                    conditions_pass.append(data_version_value>=data_condition_value_from)

                if data_condition_value_to is not None:
                    conditions_pass.append(data_version_value<data_condition_value_to)

        return all(conditions_pass) if conditions_pass else False

    async def transformData(
        self,
        data:Data,
        table_name:str=None,
        file_name:str=None,
        data_condition_id:int=None,
        directory_name:str=None
    ) -> None:
        if self.transform:
            
            await self.data_logging.logEvent(
                'transform',
                'loading',
                informations = {
                    'name':file_name,
                    'directory_name':directory_name
                }
            )

            for transform_element in self.transform:
                if self.checkDataConditions(
                    transform_element.get('data_conditions'),
                    table_name,
                    file_name,
                    data_condition_id,
                    directory_name
                ):
                    await data.transform(
                        copy.deepcopy(transform_element.get('transformations')),
                        self.data_logging
                    )

            await self.data_logging.logEvent()

    def getTablesAssociatedWithFiles(self) -> List[Dict]:
        return [
            {
                'name':table.name,
                'data_conditions':table.data_conditions[self.name],
                'priority':2,
                'order':index
            }
            for index, table in enumerate(self.tables)
            if any(
                x in ['file_name','file_name_pattern','file_contains','file_not_contains']
                for x in table.data_conditions[self.name]
            )
        ]

    async def actionsTables(
        self,
        actions:List[Union[str,dict]],
        data:Data=None,
        **kwargs
    ) -> Data:
        """Execute an action by going accros tables and checking data conditions.

        Args:
            action (str): Action to execute (save, delete,append,transform,version, add_data)
        """
        
        if not self.tables and 'manage' in actions:
            await self.setTables(
                os.path.basename(kwargs.get("directory_name"))
            )
            await self.manage('values')
            
        sets = []
        
        for table in self.tables:
            if (
                isinstance(table.data_conditions[self.name],list)
                and table.data_conditions[self.name]
            ):
                frames:List[pandas.DataFrame] = []

                for data_conditions in table.data_conditions[self.name]:
                    data_set = copy.deepcopy(data)
                    await self.dataTableActions(
                        actions,
                        table,
                        data_conditions,
                        data=data_set,
                        **kwargs
                    )
                    if data_set:
                        frames.append(data_set.frame)

                if frames:
                    data_set.frame = pandas.concat(frames)
                    sets.append(data_set)

            else:
                data_set = copy.deepcopy(data)
                await self.dataTableActions(
                    actions,
                    table,
                    table.data_conditions[self.name] if isinstance(
                        table.data_conditions[self.name],
                        dict
                    ) else {},
                    data=data_set,
                    **kwargs
                )

                sets.append(data_set)

        return sets[0]
        
    async def dataTableActions(
        self,
        actions:List[str],
        table:AsyncTable,
        data_conditions:dict,
        file_name:str=None,
        directory_name:str=None,
        **kwargs
    ) -> None:
        """Execute action for a table.

        Args:
            action (str): action name.
            table (AsyncTable): Table.
            data_conditions (dict): Data conditions to execute the action
            data (Data, optional): Data to save. Defaults to None.
            file_name (str, optional): Name of the file where data is coming from. Defaults to None.
            import_mode (str, optional): _description_. Defaults to 'modification_time'.
            directory_name (str, optional): _description_. Defaults to None.
            file_id (int, optional): _description_. Defaults to None.
            where_statement (list, optional): Where condition to delete in table. Defaults to None.
            table_names (list, optional): _description_. Defaults to None.
        """
        if self.checkDataConditions(
            data_conditions,
            table.name,
            file_name,
            directory_name=directory_name
        ):
            for action_name in actions:
                await self.executeDataTableAction(
                    action_name,
                    table,
                    data_conditions,
                    file_name = file_name,
                    directory_name= directory_name,
                    **kwargs
                )

    async def executeDataTableAction(
        self,
        action_name:str,
        table:AsyncTable,
        data_conditions:dict,
        data:Data=None,
        file_name:str=None,
        directory_name:str=None,
        file_id:int=None,
        table_names:list = None,
        **kwargs
    ) -> None:
        
        if action_name == 'transform':
            await self.transformData(
                data,
                table.name,
                file_name,
                data_conditions.get('id') if isinstance(data_conditions,dict) else None,
                directory_name
            )

        elif action_name == 'version':
            self.updateData(
                data,
                file_name,
                directory_name,
                table.name,
                **kwargs
            )
        
        elif action_name == 'copy':
            await table.copy(
                **next((
                    save for save in copy.deepcopy(self.save)
                    if self.checkDataConditions(
                        save.pop('data_conditions'),
                        table.name,
                        file_name,
                        directory_name=directory_name
                    )
                ),{})
            )

        elif action_name == 'delete':
            await table.delete(**kwargs)

        elif action_name == 'manage':

            if mode_level.get(self.status) > mode_level.get(table.status):
                table.status = self.status

            await table.manage(
                data =data,
                data_logging_action=self.data_logging.action,
                data_source_id=self.id,
                **kwargs
            )

        elif action_name == 'add_informations':
            
            data.frame['file_id'] = file_id
            data.setType(
                'file_id',
                'int'
            )

            if self.data_configuration.active:
                data.frame['data_source_id'] = self.id
                table.partitionDataSource(
                    self.id,
                    self.name,
                    self.data_version.configuration
                )

        elif action_name == 'append':
            table_names.append(table.name)

        elif action_name == 'add_data':
            table.setData(data)

        elif action_name == 'reset_data_source':
            await table.resetDataSource(
                self.id,
                self.status
            )
        
        elif action_name == 'reset_data':
            table.data = None

    async def deleteData(
        self,
        file_name:str = None,
        where_statement:list = None,
        directory_name:str = None
    ) -> None:
        """Delete data from a file.

        Args:
            file_name (str): File name.
            where_statement (list, optional): Filter condition to apply when deletation. Defaults to None.
            directory_name (str, optional): File directory name. Defaults to None.
        """
        
        await self.actionsTables(
            ['delete'],
            file_name=file_name,
            directory_name=directory_name,
            where_statement=where_statement
        )

    async def deleteAllData(self) -> None:
        files = await self.files_table.getFiles()
        
        for index, file in files.data.frame.iterrows():

            await self.deleteData(
                file.get('name'),
                {'file_id':file.get('id')},
                file.get('directory_name')
            )

    def getExtractArguments(
        self,
        file_name:str
    ) -> dict:

        for extract_element in copy.deepcopy(self.extract):
            if self.checkDataConditions(extract_element.pop('data_conditions',{}),file_name = file_name):
                if 'read_excel_sheet' in extract_element:
                    extract_element['read_excel_sheet'] = getFunction(**extract_element.get('read_excel_sheet'))
                return extract_element
        
        return {}

    async def getTables(
        self,
        file_name:str
    ) -> List[AsyncTable]:
        
        table_names = []
        
        await self.actionsTables(
            ['append'],
            file_name = file_name,
            table_names = table_names
        )

        return table_names

    async def updateDataVersion(
        self,
        file_name:str,
        directory_name:str,
        file_modification_time:datetime.datetime,
        main_files:List[Dict[str,str]],
        data:Data,
        update_version:bool = False,
        data_version_value:dict = None
    ) -> None:
        """Update the data version values with the file name

        Args:
            file_name (str): File name to be saved.
            file_modification_time (datetime.datetime): Modification time of the file.
            main_file_name (str): Main file name.
            data (Data): Data from file.

        Returns:
            Data: Data updated.
        """
        
        if self.data_version.active:
            if update_version:
                for view in self.data_version.views:
                    if  isinstance(view.query,dict) and view.query.get('from')['element_type'] == 'view':
                        dependent_view = next((
                            v for v in self.views
                            if v.get('name') == view.query.get('from')['name']
                        ))
                        tables = await self.getTables(file_name)
                        if (
                            len(tables) > 0 and
                            tables[0] not in [t['name'] for t in dependent_view.get('dependences')] and 
                            not any([v.file_contains and v.file_contains in file_name for v in self.data_version.values])
                        ):
                            return False
                    elif view.dependences[0].get('element_type')== 'view':
                        dependent_view = next((
                            v for v in self.views
                            if v.get('name') == view.dependences[0].get('name')
                        ))
                        tables = await self.getTables(file_name)
                        if (
                            len(tables) > 0 and
                            tables[0] not in [t['name'] for t in dependent_view.get('dependences')] and 
                            not any([v.file_contains and v.file_contains in file_name for v in self.data_version.values])
                        ):
                            return False  
                
                for file in self.data_version.files:
                    
                    for value in file.values:
                        if value.get('format') == 'date':

                            data.toDateTime(
                                value.get('name'),
                                '%Y%m%d%H%M%S',
                                'timestamp'
                            )

                            values = data.frame[value.get('name')].dt.strftime(
                                '%Y-%m-%d' if value.get('format')== 'date' else '%Y-%m-%d %H:%M:%s'
                                if value.get('format') == 'timestamp' else '%H:%M:%s'
                            )
                        
                        values = pandas.DataFrame(
                            list(values.unique()),
                            columns=['date']
                        )    

                    if file.exists:

                        file.data.frame.drop(
                            file.data.frame[file.data.frame['file_name']==file_name].index,
                            inplace=True
                        )
                        file.data.frame = pandas.concat([
                            file.data.frame,
                            values.assign(file_name = file_name)
                        ])

                        file.write(file.data.frame)
                    else:
                        values = values.assign(file_name = file_name)
                        file.write(values)
                        file.data = Data(values)

                    return False  
            
            {
                value.setValue(
                    file_name,
                    main_files[0].get('directory_name') if main_files else directory_name,
                    main_files[0].get('name') if main_files else None,
                    data
                ) 
                for value in self.data_version.values
                if self.checkDataConditions(
                    value.data_conditions,
                    None,
                    file_name,
                    None,
                    main_files[0].get('directory_name') if main_files else directory_name
                )
            }

            if update_version:
                return True

            for view in self.data_version.views:
                return view.checkDataSaving(data_version_value)

            for table in self.data_version.tables:

                delete_data = await table.updateTableVersion(
                    file_name,
                    file_modification_time,
                    main_files[0].get('name'),
                    data
                )

                if delete_data:
                    columns = table.data_version_columns
                    await self.deleteData(
                        file_name,
                        [
                            {'name':column_name,'value':columns[column_name].value}
                            for column_name in columns
                            if columns[column_name].is_unique_id_column
                        ]
                    )
            
            
            return True
        return True

    def updateData(
        self,
        data:Data,
        file_name:str=None,
        directory_name:str=None,
        table_name:str=None,
        main_files:List[Dict[str,str]] = [],
        data_version_value:dict = None,
        **kwargs
    ) -> None:
        """Add columns to data with data version values.

        Args:
            data (Data): Data to update.

        Returns:
            Data: Data with new data version columns.
        """
        
        if self.data_version.active:
            
            for value in self.data_version.values:
            
                if value.add_to_data and self.checkDataConditions(
                    value.data_conditions,
                    table_name,
                    file_name,
                    None,
                    main_files[0].get('directory_name') if main_files else directory_name,
                ):
            
                    if (
                        isinstance(value.add_to_data,dict)
                        and value.add_to_data.get(file_name)
                    ):
                        data.frame[value.name] =value.value
            
                    elif isinstance(value.add_to_data,bool):
                        data.frame[value.name] =value.value


                    if hasattr(value,'format') and value.format and value.format.get('type') == 'date':

                        data.toDateTime(
                            value.name,
                            value.format.get('format'),
                            value.format.get('type')
                        )

            if data_version_value and 'name' in data_version_value.keys():
                if data_version_value.get('type') == 'date':
                    data.frame = data.frame[
                        data.frame[data_version_value.get('name')].dt.strftime('%Y-%m-%d') == data_version_value.get('value')
                    ]

    def getTemporaryFile(
        self,
        name:str,
        directory_name:str,
        main_file_path:str = None
    ) -> Dict[str, str]:
        """Get the saved temporary file associated 
        with the main file.

        Args:
            name (str): Main file name.
            directory_name (str): Main file directory.
            main_file_path (str): Main file path.

        Returns:
            Dict[str, str]: Temporary directory parameteres.
        """
        return next(
            (
                main_file for main_file
                in self.temporary_main_files
                if (
                    main_file.get('name') == name
                    and main_file.get(
                        'directory_name'
                    ) == directory_name
                )
            ),
            None
        )

    async def saveVersions(
        self,
        database:AsyncDatabase
    ) -> None:
        for view in self.data_version.views:
            await view.saveVersions(database)
