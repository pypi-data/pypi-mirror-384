"""

"""
from __future__ import annotations
from typing import Union,List,Dict

import os
import copy

from datablender.base import (
    DataConfiguration,
    Connection,
    Data,
    AsyncDataConfiguration,
    AsyncConnection
)
from datablender.database import Database, AsyncDatabase
from datablender.data.dataSourceCore import  DataSourceCore
from datablender.data.asyncDataSourceCore import  AsyncDataSourceCore
from datablender.data.dataDirectory import DataDirectoryElement,AsyncDataDirectoryElement

class DataSource:

    def __init__(
        self,
        connection:Connection=None,
        data_configuration:DataConfiguration = None,
        acticvate_data_config:bool = False,
        core:DataSourceCore = None,
        id:int=None,
        name:str=None,
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
        database_name:str= None,
        schema_id:int = None,
        schema_name:str = 'public',
        tables:Union[str,List[str],List[dict]] = None,
        event_server = None,
        actions:List[Dict[str,any]] = []
    ) -> None:
        
        self.name = name
        self.id = id
        self.status = status

        self.core = core if core else DataSourceCore(
            connection,
            data_configuration if data_configuration else DataConfiguration(
                active=acticvate_data_config
            ),
            self.id,
            self.name,
            status,
            content,
            fetch,
            extract,
            transform,
            save,
            directory_name,
            control,
            data_version,
            database,
            database_name,
            schema_id,
            schema_name,
            tables,
            event_server=event_server,
            actions = actions
        )

    @property
    def configuration(self) -> dict:
        return self.core.configuration
    
    def manage(
        self,
        manage_from: str = 'configuration',
        new_configuration: dict = {}
    ) -> DataSource:

        self.core.manage(manage_from,new_configuration)
        
        self.name = self.core.name
        self.id = self.core.id
        self.status = self.core.status

        self.directory_element = None

        return self
            
    def setDirectoryElement(
        self,
        directory_element:dict = {},
        relative_path:str = None,
        **kwargs
    ) -> DataSource:
        
        
        if relative_path:
            directory_element['path'] = os.path.join(
                self.core.directory_name,
                relative_path 
            )

        elif (
            directory_element.get('path',None) is None
            and directory_element.get('name',None) is None
            and directory_element.get('directory_name',None) is None
            and self.core.directory_name is not None
        ):
            directory_element['path'] = self.core.directory_name
        
        if (
            directory_element.get('path') and
            self.core.directory_name and
            os.path.normpath(
                self.core.directory_name
            ) not in os.path.normpath(
                directory_element.get('path')
            )
        ):
            directory_element['path'] = self.core.directory_name
        
        self.directory_element = DataDirectoryElement(
            self.core,
            **directory_element
        )

        return self
    
    def fetchFiles(
        self,
        index:str = None,
        directory_element:dict = {},
        relative_path:str = None,
        **kwargs
    ) -> dict:
        
        self.core.manageDirectory()
        
        for data_fetcher_index,data_fetcher in enumerate(self.core.data_fetchers):
            if index is None or (index is not None and int(index) ==data_fetcher_index):
                data_fetcher.fetchFiles()
                
        return self.getDataDirectoryElement(
            directory_element,
            relative_path,
            **kwargs
        )
    
    def downloadFiles(
        self,
        index:str=None,
        directory_element:dict = {},
        relative_path:str = None,
        **kwargs
    ) -> dict:
        
        for data_fetcher_index,data_fetcher in enumerate(self.core.data_fetchers):
            if index is None or (index is not None and int(index) ==data_fetcher_index):
                data_fetcher.downloadFiles()
        
        return self.getDataDirectoryElement(
            directory_element,
            relative_path,
            **kwargs
        )

    def fetchData(
        self,
        index:str = None,
        transformation:list = [],
        add_data_version:bool = False,
        **kwargs
    ) -> None:
        
        raw_data = []
        for data_fetcher_index,data_fetcher in enumerate(self.core.data_fetchers):
            if index is None or (index is not None and int(index) ==data_fetcher_index):
                data_fetcher.setRequest()
                data_fetcher.addRequestElements()
                data_fetcher.fetchDataFromRequest()
                raw_data = [
                    *raw_data,
                    *data_fetcher.raw_data
                ]

        data = Data(raw_data)

        if transformation:
            if self.core.tables:
                for table in self.core.tables:
                    if isinstance(table.data_conditions[self.core.name],dict):      
                        if self.core.checkDataConditions(
                            table.data_conditions[self.core.name],
                            table.name,
                            data_condition_id=table.data_conditions[self.core.name].get('id')
                        ):          
                            data = self.core.transformData(
                                data,
                                table.name,
                                data_condition_id=table.data_conditions[
                                    self.core.name
                                ].get('id')
                            )
                            
            else:
                data = self.core.transformData(data)
 
        return {
            **self.core.configuration,
            'data':{
                'data':data.export(),
                'columns':data.columns
            }       
        }

    def saveData(
        self,
        directory_element:dict = {},
        relative_path:str = None,
        **kwargs
    ) -> None:
    
        self.setDirectoryElement(
            directory_element,
            relative_path
        )

        if self.core.directory_name is not None:
        
            if os.path.normpath(
                self.directory_element.path
            ) == os.path.normpath(
                self.core.directory_name
            ):

                self.directory_element.save(
                    **kwargs
                )

            else:
                self.directory_element.get()
            
        else:
            raw_data = []
            for data_fetcher in self.core.data_fetchers:
                data_fetcher.setRequest()
                data_fetcher.addRequestElements()
                data_fetcher.fetchDataFromRequest()
                raw_data = [
                    *raw_data,
                    *data_fetcher.raw_data
                ]

            if self.core.data_configuration.active:

                self.core.deleteData(
                    where_statement={
                        'data_source_id':self.core.id
                    }
                )
            
            self.core.saveData(Data(raw_data))

        return self.core.configuration

    def getDataDirectoryElement(
        self,
        directory_element:dict = {},
        relative_path:str = None,
        **kwargs
    ) -> dict:
        return {
            **self.core.configuration,
            'directory_element':self.setDirectoryElement(
                directory_element,
                relative_path
            ).directory_element.get(**kwargs)         
        }

class AsyncDataSource:

    def __init__(
        self,
        connection:AsyncConnection=None,
        data_configuration:AsyncDataConfiguration = None,
        acticvate_data_config:bool = False,
        core:AsyncDataSourceCore = None,
        id:int=None,
        name:str=None,
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
        database_name:str= None,
        schema_id:int = None,
        schema_name:str = 'public',
        tables:Union[str,List[str],List[dict]] = None,
        event_server = None,
        views:List[Dict[str,any]] = [],
        loop =None
    ) -> None:
        
        self.name = name
        self.id = id
        self.status = status

        self.core = core if core else AsyncDataSourceCore(
            connection,
            data_configuration if data_configuration else AsyncDataConfiguration(
                active=acticvate_data_config
            ),
            self.id,
            self.name,
            status,
            content,
            fetch,
            extract,
            transform,
            save,
            directory_name,
            control,
            data_version,
            database,
            database_name,
            schema_id,
            schema_name,
            tables,
            event_server=event_server,
            views = views,
            loop=loop
        )

    async def initiate(self) -> AsyncDataSource:
        await self.core.initiate()
        return self
    
    @property
    def configuration(self) -> dict:
        return self.core.configuration
    
    async def manage(
        self,
        manage_from: str = 'configuration',
        new_configuration: dict = {}
    ) -> AsyncDataSource:

        await self.core.manage(
            manage_from,
            new_configuration
        )
        
        self.name = self.core.name
        self.id = self.core.id
        self.status = self.core.status

        self.directory_element = None

        return self
            
    async def setDirectoryElement(
        self,
        directory_element:dict = {},
        relative_path:str = None,
        **kwargs
    ) -> AsyncDataSource:
             
        if relative_path:
            directory_element['path'] = os.path.join(
                self.core.directory_name,
                relative_path 
            )

        elif (
            directory_element.get('path',None) is None
            and directory_element.get('name',None) is None
            and directory_element.get('directory_name',None) is None
            and self.core.directory_name is not None
        ):
            directory_element['path'] = self.core.directory_name
        
        if (
            directory_element.get('path') and
            self.core.directory_name and
            os.path.normpath(
                self.core.directory_name
            ) not in os.path.normpath(
                directory_element.get('path')
            )
        ):
            directory_element['path'] = self.core.directory_name
        
        if (
            not directory_element and
            self.core.directory_name is None and
            (
                not all([len(d.request_params.get('elements')) != 0 for d in self.core.data_fetchers])
                or not self.core.data_fetchers
            )
        ):
            await self.core.manageDirectory()
            directory_element['path'] = self.core.directory_name
        
        self.directory_element = AsyncDataDirectoryElement(
            self.core,
            file_server=self.core.file_server,
            **directory_element
        ).control()

        return self
    
    async def fetchFiles(
        self,
        index:str = None,
        directory_element:dict = {},
        relative_path:str = None,
        **kwargs
    ) -> dict:

        self.core.data_logging.setActionName(
            'fetchFiles',
            self.core.element_type,
            self.core.configuration
        )
        await self.core.manageDirectory()

        for data_fetcher_index,data_fetcher in enumerate(self.core.data_fetchers):
            if index is None or (index is not None and int(index) ==data_fetcher_index):
                if data_fetcher.directory_name is None:
                    data_fetcher.directory_name = self.core.directory_name
                await data_fetcher.fetchFiles(len(self.core.data_fetchers) > 1)

        return await self.getDataDirectoryElement(
            directory_element,
            relative_path,
            check_directory = len(self.core.data_fetchers) > 1,
            **kwargs
        )
    
    async def downloadFiles(
        self,
        index:str=None,
        directory_element:dict = {},
        relative_path:str = None,
        **kwargs
    ) -> dict:
        
        self.core.data_logging.setActionName(
            'downloadFiles',
            self.core.element_type,
            self.core.configuration
        )

        for data_fetcher_index,data_fetcher in enumerate(self.core.data_fetchers):
            if index is None or (index is not None and int(index) ==data_fetcher_index):
                await data_fetcher.downloadFiles()
        
        return await self.getDataDirectoryElement(
            directory_element,
            relative_path,
            **kwargs
        )

    async def fetchData(
        self,
        index:str = None,
        transformation:list = [],
        add_data_version:bool = False,
        **kwargs
    ) -> None:
        self.core.data_logging.setActionName(
            'fetchData',
            self.core.element_type,
            self.core.configuration
        )

        raw_data = []
        for data_fetcher_index,data_fetcher in enumerate(self.core.data_fetchers):
            if index is None or (index is not None and int(index) ==data_fetcher_index):
                await data_fetcher.fetchDataFromRequest()
                raw_data = [
                    *raw_data,
                    *data_fetcher.raw_data
                ]

        data = Data(raw_data)

        if transformation:
            if self.core.tables:
                data = await self.core.actionsTables(
                    ['transform'],
                    data
                )                            
            else:
                await self.core.transformData(
                    data
                )
 
        return {
            **self.core.configuration,
            'data':{
                'data':data.export(),
                'columns':data.columns
            }       
        }

    async def saveData(
        self,
        directory_element:dict = {},
        relative_path:str = None,
        **kwargs
    ) -> None:
        
        self.core.data_logging.setActionName(
            'saveData',
            self.core.element_type,
            self.core.configuration
        )

        await self.setDirectoryElement(
            directory_element,
            relative_path
        )

        if self.core.directory_name is not None:
            if os.path.normpath(
                self.directory_element.path
            ) == os.path.normpath(
                self.core.directory_name
            ):
                await self.directory_element.save(
                    **kwargs
                )

            else:
                self.directory_element.get()
            
        else:
            raw_data = []
            for data_fetcher in self.core.data_fetchers:
                await data_fetcher.fetchDataFromRequest()
                raw_data = [
                    *raw_data,
                    *data_fetcher.raw_data
                ]

            if self.core.data_configuration.active:

                await self.core.deleteData(
                    where_statement={
                        'data_source_id':self.core.id
                    }
                )
            else:
                await self.core.deleteData()
            
            await self.core.actionsTables(
                ['transform','version','add_informations','manage','copy'],
                Data(raw_data),
                manage_from = 'values'
            )

        for view in self.core.views:
            await self.core.database.manageElement(
                view,
                'view'
            )

        await self.core.saveVersions(self.core.database)

        return self.core.configuration

    async def getDataDirectoryElement(
        self,
        directory_element:dict = {},
        relative_path:str = None,
        **kwargs
    ) -> dict:
        if self.core.data_logging.action_name is None:
            self.core.data_logging.setActionName(
                'getDataDirectoryElement',
                self.core.element_type,
                self.core.configuration
            )
        await self.setDirectoryElement(
            directory_element,
            relative_path
        )
        return {
            **self.core.configuration,
            'directory_element':await self.directory_element.get(**kwargs)         
        }

    async def structureData(
        self,
        sets:List[dict]
    ) -> None:
        
        for set in sets:
            
            data:List[list] = set.get('data')
            columns:List[dict] = set.get('columns')

            await self.core.actionsTables(
                ['add_data','reset_data_source','manage','reset_data'],
                Data(
                    {c.get('name'):data[i] for i,c in enumerate(columns)},
                    set.get('directory_element')['name'],
                    set.get('directory_element')['directory_name'],
                    columns=columns,
                    transform_columns=columns
                ),
                file_name = set.get('directory_element')['name'],
                directory_name = set.get('directory_element')['directory_name'],
                manage_from = 'values',
                reset_data_source = True
            )

        return {
            **self.configuration, 
            # 'structure':{
            #     'tables':[
            #         {  
            #             **table.configuration,
            #             **await table.resetDataSource(
            #                 self.core.id,
            #                 self.core.status
            #             )
            #         } for table in self.core.tables
            #     ]
            # }
        }
