"""
"""
from __future__ import annotations
from typing import Dict, Union, List, Callable, Tuple

import os
import copy
import json
import pandas
import subprocess

from datablender.base import (
    getFunction,
    Directory,
    Data,
    AsyncDataConfiguration,
    AsyncConnection,
    AsyncDataElement,
    AsyncRequest
)
from datablender.database import AsyncDatabase
from datablender.data.dataVersion import AsyncDataVersion
from datablender.base import DataSets

class AsyncDataProcess(AsyncDataElement):
    """Extract, transform and load data within the database.

    The first step is to extract data from the database.
    Data can come from 3 places :
        1. Query
        2. Table
        3. View

    After the data selection, the data is transform. Transformations 
    can be applied to a specific data set, or all of them.

    Then the data is export to the tables.

    Attributes:
    ----------
        Attributes

    Methods:
    ----------
        Methods

    Examples:
    ----------
        >>> import datablender
        >>> data_process = datablender.DataProcess(
        >>>     datablender.Connection(),
        >>>     data_process_test,
        >>>     data = [
        >>>         'data_set'
        >>>     ] 
        >>> )

        >>> import datablender
        >>> data_process = datablender.DataProcess(
        >>>     datablender.Connection(),
        >>>     data_process_test,
        >>>     data = [
        >>>         'data_set'
        >>>     ] 
        >>> )
        

    """
    def __init__(
        self,
        connection:AsyncConnection,
        name:str,
        database:AsyncDatabase= None,
        data_configuration:AsyncDataConfiguration=None,
        acticvate_data_config:bool=False,
        status:str='developpement',
        actions:List[Dict[str,any]] = [],
        data_version:dict={},
        directory_name:str=None,
        event_server=None,
        id:int=None,
        data_directory_name:str= None,
        content:dict = None,
        schema_name:str = 'public',
        schema_id:int = None,
        database_name:str = None,
        loop =None,
        objects:Dict[str,Union[List[dict],str]] = []
    ):
        super(AsyncDataProcess,self).__init__(
            connection,
            name,
            'data_process',
            status,
            data_configuration,
            acticvate_data_config,
            id,
            content,
            event_server
        )

        self.schema_id = schema_id
        self.schema_name = schema_name
        self.loop = loop

        self.actions = actions
        self.actions_to_process = copy.deepcopy(self.actions)
        
        self.directory_name = None
        self.setDirectory(directory_name)
        self.setDataDirectory(data_directory_name)

        self.version = {}
        self.data_version_config = data_version

        self.functions:Dict[str,Callable] = {}
        self.data:Dict[str,Data] = {}
        self.raw_data = None

        self.database,self.initiate_database = (database,False) if database else (AsyncDatabase(
            self.connection,
            name = database_name if database_name else self.connection.database_name,
            data_configuration=self.data_configuration,
            event_server=self.data_logging.event_server
        ),True)

        self.data_logging.element_configuration = self.configuration          

        self.data_sets = DataSets(**objects,directory_name=self.directory_name)
    
    async def initiate(self) -> AsyncDataProcess:

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
            #'versions':self.versions,
            'actions':self.actions,
            'content':self.content,
            'data_version':self.data_version.configuration if hasattr(
                self,
                'data_version'
            ) else self.data_version_config,
            'schema_id':self.schema_id
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
                    'actions'
                ]
            ]
            
        return new_config
  
    async def setConfiguration(
        self,
        new_config:dict
    ) -> None:
    
        self.configuration = copy.deepcopy(new_config)
        await self.manageAttributes()
            
        if 'data_version' in new_config:
            await self.setDataVersion(
                copy.deepcopy(new_config).get('data_version')
            )
     
    def setDirectory(
        self,
        directory_name:str
    ) -> None:
        # Si un nom est fourni
        if directory_name:
            # Si le nom est valide
            if os.path.isdir(directory_name):
                self.directory_name = directory_name
            # Si le nom est invalide, le joindre 
            else:
                base_name = os.getenv('code_directory',os.getcwd())
                os.path.join(base_name,'processes',self.name)

        # Si aucun nom est fourni
        else:
            base_name = os.getenv('code_directory',os.getcwd())
            if os.path.isdir(os.path.join(base_name,'process')):
                base_name = os.path.join(base_name,'process')
                if os.path.isdir(os.path.join(base_name,self.name)):
                    self.directory_name = os.path.join(base_name,self.name)

    def setDataDirectory(
        self,
        directory_name:str
    ) -> None:
        # Si un nom est fourni
        if directory_name:
            # Si le nom est valide
            if os.path.isdir(directory_name):
                self.data_directory_name = directory_name
            # Si le nom est invalide, le joindre 
            else:
                base_name = os.getenv('data_directory',os.getcwd())
                self.data_directory_name = os.path.join(base_name,'processes',self.name)

        # Si aucun nom est fourni
        else:
            base_name = os.getenv('data_directory',os.getcwd())
            if os.path.isdir(os.path.join(base_name,'processes')):
                base_name = os.path.join(base_name,'processes')
                if os.path.isdir(os.path.join(base_name,self.name)):
                    self.data_directory_name = os.path.join(base_name,self.name)
                else:
                    self.data_directory_name = os.path.join(base_name,self.name)
                    Directory(self.data_directory_name).make()
            else:
                self.data_directory_name = os.path.join(base_name,'processes',self.name)
                Directory(self.data_directory_name).make()

    async def manage(
        self,
        manage_from='configuration',
        new_configuration:dict={}
    ) -> AsyncDataProcess:
        """Manage the data process configuration in the data configuration.

        Args:
            manage_from (str, optional): Manage the data process from. Defaults to 'configuration'.
            new_configuration (dict, optional): New configuration to manage the data process. Defaults to {}.

        Returns:
            DataSource: self.
        """
        self.data_logging.setActionName(
            'manage',
            self.element_type,
            self.configuration
        )
            
        await self.data_configuration.getElements(self.element_type)
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

            elif new_configuration and self.status !='inexistant':
                await self.setDataVersion(self.data_version_config)
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
                await self.setDataVersion(self.data_version_config)
                setattr(
                    self,
                    'id',
                    await self.data_configuration.postElement(
                        self.configuration,
                        self.element_type
                    )
                )

                
            # If data config is active, but there is no directory name or data source name
            # If data config is active, but there is no directory name or data source name
            else:
                self.name = 'data'
                await self.setDataVersion(self.data_version_config)
                setattr(
                    self,
                    'id',
                    await self.data_configuration.postElement(
                        self.configuration,
                        'data_source'
                    )
                )

        # If data config is not active and there is not a new configuration,
        elif not new_configuration and manage_from != 'values':
            self.name = 'data' if not self.name else self.name
            await self.setDataVersion(self.data_version_config)
        
        return self

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

        else:
            self.data_version = AsyncDataVersion(
                self.connection,
                self.schema_name,
                self.data_configuration,
                active=True if data_version else False,
                schema_id = self.schema_id,
                **data_version
            )
            [
                await table.manage() for table
                in self.data_version.tables
            ]

    def getVersion(
        self,
        element:Union[str,List[str],List[Dict[str,any]]]
    ) -> dict:

        if self.data_version.active:
            # S'il y a un structure de la data version et qu'il y 
            # a une version spécifié, récupérer les bonnes variables pour filtere 
            # selon l'élément
            return {
                value_name:self.version[value_name]
                for value_name in self.data_version.values
                if any([
                    self.checkElement(element_)[1] == self.checkElement(element)[1]
                    for element_
                    in self.data_version.values[value_name].elements
                ])
            }
        
        # Si le data version n'a pas de structure, retourner la version, qui peut être None 
        # si elle n'a pas été spécifié
        return self.version

    async def addVersion(
        self,
        element:Union[Dict[str,str],str],
        version:list=[]
    ) -> None:
        self.executeAction(
            element,
            'transform',
            transformations=[
                {
                    'name':'add',
                    'column_name':v,
                    'value':self.version[v]
                }
                for v in version
                if v in self.version
            ]
        )
    
    def getVersions(
        self,
        attribute:str,
        values:list
    ) -> None:
    
        return [{attribute:v} for v in values]

    async def iterateVersion(
        self,
        action:str,
        versions    
    ) -> None:
        actions = copy.deepcopy(self.actions_to_process)

        for self.version in self.getVersions(**versions):
            self.actions_to_process = copy.deepcopy(actions)
            await self.process()

    async def process(
        self,
        process_from:int = None,
        process_to:int = None
    ) -> None:
        
        if process_from is not None or process_to is not None:
            self.actions_to_process = [
                a for i,a in enumerate(self.actions_to_process) if (
                    (process_from <= i <= process_to)
                    or a.get('name') in ['getFunction']
                )
            ]

        while self.actions_to_process:
            action = self.actions_to_process.pop(0)


            if (
                action.get('name') in ['iterate','iterateVersion']
                and action.get('action') == 'end'
            ):
                self.version = {}
                break

            versions_to_process:dict = action.pop('versions_to_process',None)

            if versions_to_process is not None and self.version is not None:
                skip_action = False 
                for version_attribute, version_value in self.version.items():
                    versions_to_process_value = versions_to_process.get(version_attribute)
                    if versions_to_process_value is not None and version_value not in versions_to_process_value:
                        skip_action = True
                        break

                if skip_action:
                    continue
                
            print(action.get('name'))

            await getattr(self,action.pop('name'))(**action)

    async def getFunction(
        self,
        function_name:str,
        module:str='__init__'
    ) -> None:
        self.functions[function_name] = getFunction(
            function_name,
            self.directory_name,
            module
        )

    async def applyFunction(
        self,
        function_name:str,
        **kwargs
    ):
        data = self.functions[function_name](
            {data_name:self.data[data_name].frame for data_name in self.data},
            **{
                name:getattr(self,name,kwargs[name])
                for name in kwargs
            }
        )
        if data:
            [
                await self.executeAction(
                    data_name,
                    'setData',
                    data=data[data_name]
                )
                for data_name in data
            ]

    async def select(
        self,
        element:Union[str,Dict[str,any]],
        where_statement:dict={}
    ) -> None:
        await self.executeAction(
            element,
            'select',
            where_statement=where_statement if where_statement else self.version
        )
        
    async def transform(
        self,
        transformations:List[dict],
        element:Union[str,Dict[str,str]]
    ) -> None:
        await self.executeAction(
            element,
            'transform',
            transformations=transformations
        )
    
    async def load(
        self,
        element_to:Dict[str,str],
        element_from:Union[Dict[str,str],str] = None,
        query:str=None,
        where_statement:dict={},
        **kwargs
    ) -> None:
        
        if element_from and isinstance(element_from,dict):
            element_from = await self.executeAction(
                element_from,
                'get'
            )
            
        await self.executeAction(
            element_to,
            'load',
            element_from = element_from,
            where_statement = where_statement if where_statement else self.version,
            query = query,
            **kwargs
        )

    async def merge(
        self,
        element_left:Union[Dict[str,str],str],
        element_right:Union[Dict[str,str],str],
        element:Union[Dict[str,str],str]=None,
        **kwargs
    ) -> None:
        
        data_left = await self.executeAction(element_left,'getData')
        data_right = await self.executeAction(element_right,'getData')

        await self.executeAction(
            element if element else element_left,
            'setData',
            data = pandas.merge(
                data_left.frame,
                data_right.frame,
                **kwargs
            )
        )
  
    async def copy(
        self,
        element_from:Union[Dict[str,str],str],
        element_to:Dict[str,str]
    ) -> None:
        
        data = await self.executeAction(
            element_from,
            'get',
            to_get='data'
        )
        await self.executeAction(
            element_to,
            'setData',
            data = data
        )
            
    async def update(
        self,
        element:Union[Dict[str,str],str],
        id_columns,
        update_columns,
        element_from:Union[Dict[str,str],str]=None
    ) -> None:
        if element_from and isinstance(element_from,str):
            element_from = await self.executeAction(
                element_from,
                'get'
            )
        
        await self.executeAction(
            element,
            'update',
            update_values=update_columns,
            columns=update_columns,
            where_statement={id_column:id_column for id_column in id_columns} if isinstance(id_columns,list) else id_columns,
            element_from = element_from
        )

    async def write(
        self,
        element:str,
        directory_name:str,
        extension:str=None,
        file_name:str=None
    ) -> None:

        await self.executeAction(
            element,
            'write',
            extension=extension,
            directory_name=directory_name,
            file_name=file_name
        )

    async def read(
        self,
        element:str,
        extension:str='csv',
        directory_name:str=None,
        file_name:str=None,
        version:list=[],
        **kwargs
    ) -> None:
        if not directory_name:
            path = [self.data_directory_name]+ [
                str(self.version[v]) if v in self.version else v
                for v in version
            ]

            directory_name = os.path.join(*path)
            
        await self.executeAction(
            element,
            'read',
            extension=extension,
            directory_name=directory_name,
            file_name=file_name,
            **kwargs
        )

    async def delete(
        self,
        element:Union[str,List[str],List[Dict[str,any]]],
        where_statement:dict={},
        **kwargs
    ) -> None:
        await self.executeAction(
            element,
            'delete',
            where_statement=where_statement if where_statement else self.version,
            **kwargs
        )

    async def manageDataElement(
        self,
        element:Union[str,Dict[str,any]],
        refresh:bool = False
    ) -> None:
        
        if 'schema_name' not in element:
            element['schema_name'] = self.name

        await self.executeAction(
            element,
            'manage',
            refresh=refresh
        )

    async def concat(
        self,
        element_1:Union[str,List[str],List[Dict[str,any]]],
        element_2:Union[str,List[str],List[Dict[str,any]]],
        element:Union[str,List[str],List[Dict[str,any]]],
        **kwargs
    ):
        await self.executeAction(
            element if element else element_1,
            'setData',
            data = pandas.concat(
                [
                    self.executeAction(element_1,'getData').frame,
                    self.executeAction(element_2,'getData').frame
                ],
                **kwargs
            )
        )
    
    async def iterate(
        self,
        action:str,
        element:Union[str,Dict[str,str]],
        version_columns:List[str],
        to_execute_column = None,
        to_execute:dict = {}
    ) -> None:
    
        actions = copy.deepcopy(self.actions_to_process)
        version = copy.deepcopy(self.version)
        data = await self.executeAction(element,'get',to_get='data')

        for index,data_tuple in data.frame.iterrows():
            self.data_tuple = data_tuple.to_dict()

            if not all([self.data_tuple.get(k) in v for k,v in to_execute.items()]):
                continue

            if to_execute_column is not None:
                if not self.data_tuple.get(to_execute_column):
                    continue

            self.actions_to_process = copy.deepcopy(actions)
            self.version = {
                **version,
                **{k:v for k,v in self.data_tuple.items() if k in version_columns}
            }
            
            await self.process()

        self.version = copy.deepcopy(version)

    def checkElement(
        self,
        element:Union[str,Dict[str,str]]
    ) -> Tuple[bool,Dict[str,str]]:
        
        if isinstance(element,dict):

            if 'schema_name' not in element:
                element['schema_name'] = self.name

            if 'element_type' not in element:
                element['element_type'] = 'table'

            return True,element

        elif isinstance(element,str):
            return False,{'name':element}

        else:
            return True,element            
        
    async def executeAction(
        self,
        element:Union[str,dict],
        action_name:str,
        **kwargs
    ) -> Union[Data,None]:
        is_database,element = self.checkElement(element)
        if is_database:
            return await self.database.executeDataAction(
                element,
                action_name,
                **kwargs
            )
        else:
            self.data.setdefault(
                element.get('name'),
                Data(
                    name = element.get('name'),
                    code_directory = self.directory_name,
                    connection = self.connection,
                    schema_name=self.schema_name,
                    data_sets=self.data_sets
                )
            )
            return await getattr(
                self.data[element.get('name')],
                action_name
            )(**kwargs)

    async def getProtocolBuffer(
        self,
        elements:Union[str,List[str],List[Dict[str,any]]]
    ) -> None:
        with open(os.path.join(os.getcwd(),'data.proto'), 'w+') as proto_file:
            proto_file.write('syntax = "proto3";\n')
            proto_file.write('\n')
            proto_file.write('package data_buffer;\n')
            proto_file.write('\n')

            main_message = []

            for i,element in enumerate(elements):

                proto_file.write(await self.executeAction(
                    element,
                    'protocolFormat',
                    main_message = main_message,
                    index = i 
                ))
                proto_file.write('\n')

            proto_file.write('message Data {}\n'.format('{'))
            proto_file.write('\n'.join(main_message))
            proto_file.write('\n{}'.format('}'))
            proto_file.close()
            
        process = subprocess.Popen(
            [
                "protoc",
                "-I=.",
                "--python_out=.",
                "./data.proto"
            ],
            stdout=subprocess.PIPE,
            cwd=os.getcwd()
        )

        stdout ,stderr = process.communicate()

        # os.remove("data.proto")

        import data_pb2
        return data_pb2.Data()

    async def serialize(
        self,
        elements:Union[str,List[str],List[Dict[str,any]]]
    ) -> None:
        buffer = await self.getProtocolBuffer(elements)
        import data_pb2

        [
            await self.executeAction(
                element,
                'write',
                buffer = buffer,
                buffer_format = data_pb2
            )
            for element in elements
        ]

        self.raw_data = buffer.SerializeToString()
        #os.remove("data_pb2.py")
        
    async def unserialize(
        self,
        elements:Union[str,List[str],List[Dict[str,any]]]
    ) -> None:
        buffer = self.getProtocolBuffer(elements)
        buffer.ParseFromString(self.raw_data)
    
        [
            await self.executeAction(
                element,
                'importData',
                buffer = buffer
            )
            for element in elements
        ]
        
        os.remove("data_pb2.py")

    async def switch(
        self,
        language,
        actions:List[dict] = [
            {
                'name':'applyFunction',
                'function_name':'get_temps',
                'source':'temps.R'
            }
        ]
    ) -> None:
        request = AsyncRequest(
            port = 5318,
            host = '10.4.0.13',
            loop=self.loop
        )
        await request.setSession()
        request.reset()
        request.addElement('area')

        async with request.session.post(
            request.url,
            headers={'Content-Type': 'application/protobuf'},
            params = {
                'sets':json.dumps([
                    {
                        'name':data_name,
                        'columns':self.data[data_name].columns
                    } for data_name in self.data
                ]),
                'actions':json.dumps(actions)
            },
            data = self.raw_data
        ) as response:
            assert response.status == 200
            self.raw_data = await response.read()
            
        await request.close()

    async def processObjects(
        self,
        module_name:str,
        action:str,
        object_meta:Dict[str,str],
        data_meta:Union[dict,List[dict]],
        data_tuple = None,
        method:str = 'iterrows',
    ):
        # for data_ in self.data:
        #     if data_ in ['links','links_links__','links_links','links_']:
        #         print(data_)
        #         print(self.data.get(data_).frame)

        self.data_sets.initiateData(
            {data_name:self.data[data_name].frame for data_name in self.data},
            data_meta
        )

        if method == 'iterrows':
            for object_index,object_attributes in getattr(self.data_sets,object_meta.get('name')).iterrows():
                print(object_index, end='\r')
                self.data_sets.processObject(
                    object_meta,
                    object_attributes,
                    action
                ) 
        
        elif method == 'while':

            # for data_ in self.data:
            #     print(data_)
            #     print(self.data.get(data_).frame)

            data_set = getattr(self.data_sets,object_meta.get('name'))

            while data_set.shape[0]:
                print(data_set.index[0], end='\r')
                self.data_sets.processObject(
                    object_meta,
                    data_set.iloc[0],
                    action
                ) 
        
        elif method == 'data_tuple':

            print(self.data_tuple['shape_id'])
            
            self.data_sets.processObject(
                object_meta,
                self.data_tuple,
                action
            ) 

        data = self.data_sets.setData()

        if data:
            [
                await self.executeAction(
                    data_name,
                    'setData',
                    data=data[data_name]
                )
                for data_name in data
            ]

    async def loadFromCache(
        self,
        action:str,
        element:Union[str,Dict[str,any]],
        **kwargs
    ) -> None:
        
        cache_exists = await self.executeAction(
            element,
            'manageCache',
            directory_name = self.data_directory_name,
            action = action,
            **kwargs
        )

        if cache_exists and action == 'start':
            while (
                self.actions_to_process and
                self.actions_to_process[0].get('name') != 'loadFromCache'
            ):
                self.actions_to_process.pop(0)
            
            # Remove action - loadFromCache - end
            self.actions_to_process.pop(0)

    async def refresh(
        self,
        element:Union[str,List[str],List[Dict[str,any]]],
    ) ->None:
        await self.executeAction(
            element,
            'refresh'
        )
    
    async def drop(
        self,
        element:Union[str,List[str],List[Dict[str,any]]],
    ) ->None:
        await self.executeAction(
            element,
            'drop'
        )
