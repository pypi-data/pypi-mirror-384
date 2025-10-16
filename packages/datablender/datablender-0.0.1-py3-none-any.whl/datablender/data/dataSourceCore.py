"""

"""

from __future__ import annotations
from typing import Union, Dict,List

import os
import re
import copy
import datetime

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
)

from datablender.database import (
    Table,
    Database
)

from datablender.data.dataVersion import DataVersion
from datablender.data.filesTable import FilesTable
from datablender.data.directoryElementController import DirectoryElementController

class RawDataFile(File):
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
        data_logging:DataLogging = None
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
            super(RawDataFile,self).__init__(
                self.setDirectoryName(
                    directory_name,
                    **directory_name_setter
                ) if directory_name_setter else directory_name,
                downloading_name if downloading_name else self.name
            )
        
        else:
            self.directory_name = None

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
            and len(last_url_element.split('.',-1)[-1])<10
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
        position:str=None
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
            return source.split(
                character
            )[position]
        
        return self.name

    def download(self) -> None:
        """Download file from the web.
        """
        
        self.data_logging.logEvent(
            'download',
            'loading'
        )

        self.request = Request(
            self.is_secure,
            self.host,
            self.port,
            self.domain_name
        )

        self.request.addElement(self.url_path)

        self.request.addElement(
            self.name
        ) if self.file_included else None

        self.request.get(allow_redirects=True)

        self.write(self.request.response.content)

        if self.rename_parameters:
            self.rename(
                self.getNewName(
                    **self.rename_parameters
                )
            )
        
        self.data_logging.logEvent(
            'download',
            'loaded'
        )

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

class DataFetcher:
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
        data_logging:DataLogging=None
    ):

        self.is_secure=is_secure
        self.host=host
        self.port=port
        self.domain_name=domain_name
        self.directory_name=directory_name

        self.downloading_name=downloading_name
        self.rename_parameters=rename_parameters
        self.directory_name_setter=directory_name_setter

        self.files = files
        self.bot_actions = bot_actions
        self.request_params = request_params

        self.data_logging = data_logging

        self.raw_files:List[RawDataFile]=[]
        self.raw_data= None

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

    def setRawDataFile(
        self,
        file:dict
    ) -> None:
    
        return RawDataFile(
            directory_name=self.directory_name,
            data_logging=self.data_logging,
            **{
                **file,
                'downloading_name':self.downloading_name,
                'rename_parameters':self.rename_parameters,
                'directory_name_setter':self.directory_name_setter
            }
        )

    def fetchFiles(self):

        self.data_logging.logEvent(
            'fetch',
            'loading'
        )
                  
        if self.files:
            self.raw_files = [
                self.setRawDataFile(
                    file if isinstance(file,dict) else {'url':file}
                )
                for file in self.files
            ]

        elif self.bot_actions:

            bot = Bot(
                is_secure=self.is_secure,
                domain_name=self.domain_name,
                host=self.host,
                port=self.port
            )

            bot.open()

            bot.executeActions(
                copy.deepcopy(self.bot_actions)
            )
            
            bot.close()
                    
            self.raw_files = [
                RawDataFile(
                    self.is_secure,
                    self.domain_name,
                    self.host,
                    self.port,
                    copy.deepcopy(result),
                    directory_name=self.directory_name,
                    downloading_name = self.downloading_name,
                    rename_parameters = self.rename_parameters,
                    directory_name_setter=self.directory_name_setter,
                    data_logging=self.data_logging
                )
                for result in list(set(bot.results))
            ] 
        
        self.data_logging.logEvent(
            'fetch',
            'loaded'
        )
          
    def downloadFiles(self):
        
        self.data_logging.logEvent(
            'download',
            'loading'
        )
        [
            file.download()
            for file in self.raw_files
            if file.download_status == 'new'
        ]
        self.data_logging.logEvent(
            'download',
            'loaded'
        )

    def setRequest(self) -> None:
        self.request = Request(
            self.is_secure,
            self.host,
            self.port,
            self.domain_name
        )

    def addRequestElements(self) -> None:
        for element in self.request_params.get('elements'):
            self.request.addElement(element)

    def fetchDataFromRequest(self) -> None:
        if isinstance(self.request_params.get('params'),list):
            self.raw_data = []
            for params in self.request_params.get('params'):
                self.request.get(params=params)
                self.raw_data = [
                    *self.raw_data,
                    *self.request.response.json()[self.request_params.get('data_attribute')]
                ]

        elif isinstance(self.request_params.get('params'),dict):
            self.request.get(params=self.request_params.get('params'))
            self.raw_data = self.request.response.json()[self.request_params.get('data_attribute')]

class DataSourceCore(DataElement):
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
        connection:Connection,
        data_configuration:DataConfiguration,
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
        database:Database = None,
        database_name:str = None,
        schema_id:int = None,
        schema_name:str = 'public',
        tables:Union[str,List[str],List[dict]] = None,
        event_server=None,
        actions:List[Dict[str,any]] = []
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
        super(DataSourceCore,self).__init__(
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

        self.setDataFetchers(fetch)

        self.extract = extract
        self.transform = transform
        self.save = save

        self.schema_name = schema_name
        self.schema_id = schema_id
        self.tables_config = tables
        self.actions = actions
        
        self.tables:List[Table] = []

        self.temporary_main_files:List[Dict[str,str]] = []

        self.database = database if database else Database(
            self.connection,
            name = database_name if database_name else self.connection.database_name,
            data_configuration=self.data_configuration,
            event_server=self.data_logging.event_server
        ).manage()

        self.files_table = self.database.manageElement(
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
            'table'
        )
        self.files_table.__class__ = FilesTable
        self.files_table:FilesTable

        self.main_files_view = self.database.manageElement(
            {
                'name':'main_files',
                'directory_query':os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    '..',
                    'postgresql',
                    'queries'
                ),
                'is_database_saved': True
            },
            'view',
        )

        self.manageAttributes()

        self.data_logging.setElement(
            'data_source',
            self.name,
            self.id,
            self.schema_id,
            self.schema_name
        )
   
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
            'data_version':self.data_version.configuration,
            'schema_id':self.schema_id,
            'tables':[
                {
                    'id':table.id,
                    'data_conditions':table.data_conditions[self.name]
                } for table in self.tables
            ],
            'actions':self.actions
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
                    new_config[attribute_name] if attribute_name in new_config else getattr(self,attribute_name)
                )
                for attribute_name
                in [
                    'name',
                    'status',
                    'content',
                    'fetch',
                    'extract',
                    'transform',
                    'save',
                    'directory_name',
                    'schema_id',
                    'actions',
                    'id'
                ]
            ]
            
            self.manageAttributes()

            if 'tables' in new_config:
                self.setTables(new_config.get('tables'))

            if 'data_version' in new_config:
                self.setDataVersion(new_config.get('data_version'))

            if 'control' in new_config:
                self.element_controller.__init__(**new_config.get('control'))

            if 'fetch' in new_config:
                self.setDataFetchers(new_config.get('fetch'))

        return new_config
    
    def setTable(
        self,
        configuration:dict
    ) -> Table:
        
        if 'id' in configuration and isinstance(configuration.get('id'),str):
            configuration['name'] = configuration.get('id')
            configuration['id'] = None
        
        data_conditions = configuration.pop('data_conditions',{})
        
        return self.database.manageElement(
            {},
            'table',
            default_configuration = {   
                'schema_id':self.schema_id,
                'schema_name':self.schema_name,
                'status':copy.deepcopy(self.status),
                **configuration,
                'columns':[
                    {'name':'file_id','type':'int'},
                    *configuration.get('columns',[])
                ] if 'columns' in configuration else [],
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
            }
        ).setDataConditions(
            self.name,
            data_conditions
        )

    def setTables(
        self,
        table:Union[str,List[str],List[dict],None]
    ) -> None:
        
        self.tables = [
            self.setTable(
                configuration if isinstance(
                    configuration,dict
                ) else {'name':configuration}
            )
            for configuration in (table if isinstance(table,list) else [table])
        ] if table else []

    def manageDirectory(self) -> None:  
        
        if self.directory_name is None:
            self.directory_name = os.path.join(
                os.getenv(
                    'DATA_DIRECTORY',
                    os.getcwd()
                ),
                self.schema_name,
                self.name
            )

            self.manage(new_configuration={
                'directory_name':self.directory_name
            })

            for data_fetcher in self.data_fetchers:
                data_fetcher.directory_name = self.directory_name

        if not os.path.isdir(self.directory_name):
            Directory(self.directory_name).make()
        
        return self.directory_name

    def setDataVersion(
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

            if values or tables:
                self.data_version.active = True
                self.data_version.schema_id = self.schema_id
                self.data_version.schema_name = self.schema_name
                self.data_version.getValues(values)
                self.data_version.getTables(tables)

        else:
            self.data_version = DataVersion(
                self.connection,
                self.schema_name,
                self.data_configuration,
                active=True if data_version else False,
                schema_id = self.schema_id,
                **data_version
            )

    def setDataFetchers(
        self,
        fetch:List[dict]
    ) -> None:
        
        self.data_fetchers = [
            DataFetcher(
                **fetch_element,
                directory_name=self.directory_name,
                data_logging=self.data_logging
            )
            for fetch_element in fetch
        ]

    def manage(
        self,
        manage_from='configuration',
        new_configuration:dict={}
    ) -> DataSourceCore:
        """Manage the data source configuration in the data configuration.

        Args:
            manage_from (str, optional): Manage the data source from. Defaults to 'configuration'.
            new_configuration (dict, optional): New configuration to manage the data source. Defaults to {}.

        Returns:
            DataSource: self.
        """
        # If there is a new configuration, set all data source attributes from the new config
        if new_configuration:
            self.configuration = new_configuration

        # If data source exists in the data configuration,
        # manage the data source in the data config
        if self.data_configuration.active:

            # If there is a config element, it means that it exists in config
            if self.config_element:
                # If there's not a new config from the user,
                # the config in the data configuration is the right one.
                if not new_configuration and manage_from != 'values':
                    self.configuration = copy.deepcopy(self.config_element)

                # If status is inexistant, then delete it
                if self.status =='inexistant':
                    self.data_configuration.deleteElement(
                        self.id,
                        'data_source'
                    )
                
                # Else if one of the attributes is different from the data configuration,
                # edit the data source
                
                elif any([
                    self.config_element[attribute] != self.configuration[attribute]
                    for attribute in self.config_element
                ]) and (new_configuration or manage_from == 'values'):
                    self.data_configuration.putElement(
                        self.id,
                        self.configuration,
                        'data_source'
                    )
            
            # If it does not exists, then post the new config if there is one
            elif new_configuration and self.status !='inexistant':
                setattr(
                    self,
                    'id',
                    self.data_configuration.postElement(
                        self.configuration,
                        'data_source'
                    )
                )

            # If it does not exists and there is no new config, but the name or id,
            # post it with the values of this object
            elif self.name or self.id:
                self.setTables(self.tables_config)
                self.setDataVersion(self.data_version_config)
                setattr(
                    self,
                    'id',
                    self.data_configuration.postElement(
                        self.configuration,
                        'data_source'
                    )
                )
            # If it does not exists and there is no new config, no a name, no id
            # but a directory_name
            elif self.directory_name:
                # Set the schema and data version.
                self.setDataVersion(self.data_version_config)
                # If it is not found, set the name and post it.
                if not self.findConfiguration():
                    self.name = os.path.basename(self.directory_name) 
                    self.setTables(self.tables_config)
                    setattr(
                        self,
                        'id',
                        self.data_configuration.postElement(
                            self.configuration,
                            'data_source'
                        )
                    )
                
            # If data config is active, but there is no directory name or data source name
            else:
                self.name = 'data'
                self.setTables(self.tables_config)
                self.setDataVersion(self.data_version_config)
                setattr(
                    self,
                    'id',
                    self.data_configuration.postElement(self.configuration,'data_source')
                )

        # If data config is not active and there is not a new configuration,
        elif not new_configuration and manage_from != 'values':
            self.name = 'data' if not self.name else self.name
            self.setTables(self.tables_config)
            self.setDataVersion(self.data_version_config)

        if self.status =='inexistant':
            self.deleteAllData()
            if self.directory_name:
                Directory(self.directory_name).delete()
        
        return self

    def findConfiguration(self) -> bool:

        directory_name = copy.deepcopy(self.directory_name)

        for source in getattr(
            self.data_configuration.getElements('data_source'),
            'data_source'
        ):
            
            directory_check = os.path.abspath(directory_name) in os.path.abspath(
                source['directory_name']
            )

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
            conditions_pass.append(data_conditions['file_name'] == file_name)
        
        if 'file_name_pattern' in data_conditions:
            conditions_pass.append(re.match(data_conditions['file_name'],file_name))
        
        if 'file_contains' in data_conditions:
            conditions_pass.append(data_conditions['file_contains'] in file_name)
        
        if 'file_not_contains' in data_conditions:
            conditions_pass.append(data_conditions['file_not_contains'] not in file_name)
        
        if 'directory_contains' in data_conditions:
            conditions_pass.append(data_conditions['directory_contains'] in directory_name)
        
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
            conditions_pass.append(data_conditions['id']==data_condition_id)

        if 'data_version_value' in data_conditions:
            data_version_value = self.data_version.values.get(data_conditions['data_version_value']['name']).value
            data_condition_value = data_conditions['data_version_value']['value']
            conditions_pass.append(data_version_value==data_condition_value)

        return all(conditions_pass) if conditions_pass else False

    def transformData(
        self,
        data:Data,
        table_name:str=None,
        file_name:str=None,
        data_condition_id:int=None,
        directory_name:str=None
    ):
        if self.transform:
            for transform_element in self.transform:
                if self.checkDataConditions(
                    transform_element.get('data_conditions'),
                    table_name,
                    file_name,
                    data_condition_id,
                    directory_name
                ):
                    data.transform(
                        copy.deepcopy(transform_element.get('transformations'))
                    )
        return data

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
                condition in [
                    'file_name','file_name_pattern',
                    'file_contains','file_not_contains'
                ]
                for condition in table.data_conditions[self.name]
            )
        ]

    def saveData(
        self,
        data:Data,
        file_name:str=None,
        import_mode:str='modification_time',
        directory_name:str=None,
        file_id:int = None,
        **kwargs
    ) -> None:
        
        if not self.tables:
            self.setTables(
                os.path.basename(directory_name)
            )
            self.manage('values')

        for table in self.tables:

            if isinstance(table.data_conditions[self.name],dict):                
                self.saveDataToTable(
                    copy.deepcopy(data),
                    table,
                    file_name,
                    import_mode,
                    directory_name=directory_name,
                    file_id = file_id,
                    **kwargs
                )

            if isinstance(table.data_conditions[self.name],list):

                for data_conditions in table.data_conditions[self.name]:
                    self.saveDataToTable(
                        copy.deepcopy(data),
                        table,
                        file_name,
                        import_mode,
                        data_conditions,
                        directory_name,
                        file_id = file_id,
                        **kwargs
                    )

    def saveDataToTable(
        self,
        data:Data,
        table:Table,
        file_name:str,
        import_mode:str,
        data_conditions:dict=None,
        directory_name:str=None,
        file_id:int=None,
        **kwargs
    ) -> None:
        
        data_conditions = data_conditions if data_conditions else table.data_conditions[
            self.name
        ]
        
        if self.checkDataConditions(
            data_conditions,
            table.name,
            file_name,
            directory_name=directory_name
        ):

            saved_data = self.transformData(
                data,
                table.name,
                file_name,
                data_conditions.get('id'),
                directory_name
            )

            saved_data.frame['file_id'] = file_id
            saved_data.setType(
                'file_id',
                'int'
            )

            if self.data_configuration.active:
                saved_data.frame['data_source_id'] = self.id

            self.data_version.updateData(
                saved_data,
                file_name
            )
                        
            if self.data_configuration.active:
                table.partitionDataSource(
                    self.id,
                    self.name,
                    self.data_version.configuration
                )
            
            table.manage('values',data =saved_data)

            if import_mode == 'table_update':
                table.updateWithData()

            elif import_mode == 'modification_time':

                table.copy(
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

    def deleteData(
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
        
        for table in self.tables:
            
            if isinstance(
                table.data_conditions[self.name],
                dict
            ):
                if table.db_element and self.checkDataConditions(
                    table.data_conditions[self.name],
                    table.name,
                    file_name,
                    directory_name=directory_name
                ):
                    table.delete(where_statement)
                    
            elif isinstance(
                table.data_conditions[self.name],
                list
            ):
                for data_contidions in table.data_conditions[self.name]:
                    if table.db_element and self.checkDataConditions(
                        data_contidions,
                        table.name,
                        file_name,
                        directory_name=directory_name
                    ):
                        table.delete(where_statement)

    def deleteAllData(self) -> None:
        for index, file in self.files_table.getFiles().data.frame.iterrows():

            self.deleteData(
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

    def getTables(
        self,
        file_name:str
    ) -> List[Table]:
        
        table_names = []
        
        for table in self.tables:

            if isinstance(table.data_conditions[self.name],dict):
                if self.checkDataConditions(
                    table.data_conditions[self.name],
                    table.name,
                    file_name
                ):
                    table_names.append(table.name)

            elif isinstance(table.data_conditions[self.name],list):

                table_names.append(table.name) if any([
                    self.checkDataConditions(
                        data_contidions,
                        table.name,
                        file_name
                    )
                    for data_contidions in table.data_conditions[self.name]
                ]) else None

        return table_names

    def updateDataVersion(
        self,
        file_name:str,
        file_modification_time:datetime.datetime,
        main_files:List[Dict[str,str]],
        data:Data
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
            for table in self.data_version.tables:

                delete_data = table.updateTableVersion(
                    file_name,
                    file_modification_time,
                    main_files[0].get('name') if main_files else None,
                    data
                )

                if delete_data:
                    columns = table.data_version_columns
                    self.deleteData(
                        file_name,
                        [
                            {'name':column_name,'value':columns[column_name].value}
                            for column_name in columns
                            if columns[column_name].is_unique_id_column
                        ]
                    )

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
