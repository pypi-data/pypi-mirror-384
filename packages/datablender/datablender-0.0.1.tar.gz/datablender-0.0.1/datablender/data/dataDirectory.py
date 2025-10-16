"""
Directory containing files with data to go in a database. Data can go in one table or multiples tables. If 
"""
from __future__ import annotations
from typing import Union,List,Dict

import os
import copy
import tempfile
import shutil
from smb.SMBConnection import SMBConnection

from datablender.base import (
    Directory,
    ZipFile_,
    DirectoryElement,
    Connection,
    DataConfiguration,
    AsyncConnection,
    AsyncDataConfiguration
)
from datablender.database import (
    Database,
    Schema,
    Table,
    AsyncDatabase,
    AsyncSchema,
    AsyncTable
)
from datablender.data import getPathElements
from datablender.data.dataSourceCore import (
    DataSourceCore,
    RawDataFile
)

from datablender.data.asyncDataSourceCore import (
    AsyncDataSourceCore,
    AsyncRawDataFile
)

from datablender.data.dataFile import DataFile, AsyncDataFile

class DataDirectory(Directory):
    """Directory containing files with data.

    Attributes:
    ----------
        extensions (list): Accepted extensions.

    Methods:
    ----------
        setSchema(self,schema:Union[Schema,str]) -> None : Set the schema.
        setTable(self,table:Union[Table,str,list]) -> None : .
        orderElements(self) -> list : .

    Examples:
    ----------
        >>> import datablender
        >>> directory = datablender.DataDirectory(
        >>>     datablender.Connection(),
        >>>     'path/to/directory'
        >>> )
        >>> directory.saveFiles()
        >>> directory.connection.close()

    """
    def __init__(
        self,
        directory_name:str,
        connection:Connection=None,
        data_configuration:DataConfiguration = None,
        acticvate_data_config:bool = False,
        main_files:List[Dict[str,str]]= [],
        data_source_core:DataSourceCore = None,
        data_source_name:str=None,
        status:str = 'developpement',
        fetch:List[dict] = [],
        extract:List[dict] = [],
        transform:list = [],
        save:List[dict]=[],
        control:dict = {},
        data_version:dict = {},
        database:Database = None,
        database_name:str= None,
        schema:Union[Schema,str] = 'public',
        table:Union[Table,str,list] = None,
        event_server = None,
        actions:List[Dict[str,any]] = [],
        is_temporary:bool = False,
        file_server:SMBConnection = None
    ):
        
        super(DataDirectory,self).__init__(directory_name)
        
        self.main_files = main_files
        self.is_temporary = is_temporary
        self.file_server = file_server

        self.data_source_core = data_source_core if data_source_core else DataSourceCore(
            connection,
            data_configuration if data_configuration else DataConfiguration(active=acticvate_data_config),
            name = data_source_name,
            status = status,
            fetch = fetch,
            extract = extract,
            transform = transform,
            save = save,
            directory_name = self.name,
            control = control,
            data_version = data_version,
            database=database,
            database_name = database_name,
            schema_name=schema,
            tables=table,
            event_server=event_server,
            actions = actions
        ).manage()

        self.elements:List[DataDirectoryElement]=[]
        self.raw_files:List[RawDataFile] = []

        if self.main_files and not is_temporary:
            self.main_files[-1]['main_file_path'] = os.path.join(
                self.main_files[-1].get('main_file_path'),
                self.name_
            ) if self.main_files[-1].get('main_file_path') else self.name_
    
    @property
    def informations(self) -> dict:
        return {
            'name':self.name_,
            'path':self.name,
            'main_files':self.main_files,
            'elements':[
                element.informations
                for element in self.elements
            ]+[
                file.informations
                for file in self.raw_files
                if file.download_status == 'new'
            ],
            'control':self.data_source_core.element_controller.control(self.name_,'directory'),
            'path_elements':getPathElements(
                self.data_source_core.directory_name,
                self.name,
                copy.deepcopy(self.main_files)
            )
        }

    def setElements(self) -> None:
        """Set the elements by initiatig every element with the Data Directory Element.
        """
        
        self.elements = [
            DataDirectoryElement(
                self.data_source_core,
                name = element_name,
                directory_name = self.name,
                main_files = copy.deepcopy(self.main_files)
            ) for element_name in self.elements_name
        ]

    def orderElements(self) -> None:
        """List of the files in a directory, if there's a table list in config,
        sort the files to load data in rigth order
        """
        [
            element.setOrderPriority(
                [
                    *self.data_source_core.getTablesAssociatedWithFiles(),
                    *self.data_source_core.data_version.getTablesAssociatedWithFiles()
                ]
            ) for element in self.elements
        ]
        
        self.elements = sorted(self.elements, key=lambda item: (item.priority, item.order, item.name))

    def manageElements(self):
        """
        Before loading data, manage files in diretory to delete old ones
        by comparing files in the database.
        """
        if not self.main_files:
            database_files = self.data_source_core.main_files_view.select({
                'directory_name':self.name,
                'schema':self.data_source_core.schema_name
            }).data.frame.to_dict('records')
            [
                self.deleteDataFile(main_file)
                for main_file in database_files
                if main_file.get('name') not in [
                    element.name for element in self.elements if element.is_file
                ]
            ]

    def deleteDataFile(self,main_file:dict):
        
        for file_ in main_file.get('files'):       
            self.data_source_core.files_table.delete({'id':file_.get('id')})     
            self.data_source_core.deleteData(
                file_.get('name'),
                {'file_id':file_.get('id')}
            )
 
    def saveFiles(self) -> None:
        """Save files in directory.
        """
        self.setElements()
        self.manageElements()
        self.orderElements()
        
        for element in self.elements:
            element.save()

    def setElementStatus(
        self,
        files:List[RawDataFile],
        check_directory:bool = True
    ) -> List[RawDataFile]:
        
        # For every elements in the directory, set the status
        [
            element.setStatus(files,False)
            for element in self.elements
        ]
        
        [
            file.setStatus(
                [
                    element.informations
                    for element in self.elements
                ],
                self.name
            )
            for file in files
        ]
        self.raw_files = [
            file for file in files
            if (
                file.download_status == 'new'
                and os.path.abspath(
                    file.directory_name
                ) == os.path.abspath(
                    self.name
                )
            ) 
        ]

class DataDirectoryElement(DirectoryElement):
    """Element of a directory containing data, which can be a DataFile, DataDirectory of a ZipFile_.

    Attributes:
    ----------


    Methods:
    ----------
        getTable(self) -> Union[Table,Dict[str, Table]] : Control element with his name.

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        data_source_core:DataSourceCore,
        name:str = None,
        directory_name:str = None,
        path:str = None,
        main_files:List[Dict[str,str]]= [],
        **kwargs
    ):

        self.data_source_core = data_source_core
        self.main_files = main_files

        if path or (name and directory_name):
            super(DataDirectoryElement,self).__init__(
                name,
                directory_name,
                path
            )
        else:
            self.name =name
                
        self.priority = None
        self.order = None

        self.file:DataFile = None
        self.directory:DataDirectory = None
        self.zip_file:DataZipFile = None

        if path or (name and directory_name):
            self.setElement()
            self.control()
    
    @property
    def informations(self) -> dict:
        
        if self.file:
            return self.file.informations
            
        elif self.directory:
            return self.directory.informations
            
        elif self.zip_file:
            return self.zip_file.informations

        else:
            return {}

    def setElement(self) -> None:
        if self.is_directory:

            self.directory = DataDirectory(
                self.path+'/',
                main_files=copy.deepcopy(self.main_files),
                data_source_core=self.data_source_core
            )

        elif self.is_zip_file:

            self.zip_file = DataZipFile(
                self.name,
                self.directory_name,
                main_files=copy.deepcopy(self.main_files),
                data_source_core=self.data_source_core
            )

        elif self.is_file:
            self.file = DataFile(
                self.directory_name,
                self.name,
                main_files=copy.deepcopy(self.main_files),
                data_source_core = self.data_source_core
            )
        
    def control(self):
        """Check the element type (directory,zip file or data file) and if it can be saved.
        """
        
        self.save_directory = False
        self.save_file = False
        self.save_zip_file = False
                    
        if self.is_directory:
            self.save_directory = self.data_source_core.element_controller.control(
                self.name,
                'directory'
            )

        elif self.is_zip_file:
            self.save_zip_file = self.zip_file.save and self.data_source_core.element_controller.control(
                self.name,
                'zipfile'
            )
            
        elif not self.is_temp_file:
            self.save_file = self.data_source_core.element_controller.control(
                self.name,
                'file'
            )
    
    def save(self,**kwargs):
        """Save the element.
        """
        
        if self.save_directory:
            self.directory.saveFiles(**kwargs)

        elif self.save_zip_file:
            self.zip_file.saveFiles(**kwargs)

        elif self.save_file:
            self.data_source_core.data_version.setValues(
                **(self.main_files[0] if self.main_files else self.file.informations),
            )
            self.file.save(**kwargs)

    def setOrderPriority(self,tables:List[dict]) -> None:
        tables = [
            table for table in tables 
            if self.data_source_core.checkDataConditions(
                table['data_conditions'],
                table['name'],
                self.name,
                directory_name=self.directory_name
            )
        ]
        self.priority = tables[0]['priority'] if tables else 3
        self.order = tables[0]['order'] if tables else 1

    def get(
        self,
        extract_files:bool = False,
        transformation:list = [],
        add_data_version:bool = False,
        **kwargs
    ) -> dict:
        if self.main_files:
            
            # To do :  if there's more main files then 1
            for main_file_config in self.main_files:

                main_file_config = copy.deepcopy(main_file_config)
                main_file_path = main_file_config.pop('main_file_path')

            # If it is a file
            if '.' in self.name:

                # Check if the main file has a temporary directory
                temporary_directory = self.data_source_core.getTemporaryFile(
                    **main_file_config
                )

                # If it's a file and there is a temporary directory, 
                # then initiate the data directory element
                if temporary_directory:
                    
                    super(DataDirectoryElement,self).__init__(
                        self.name,
                        os.path.join(
                            temporary_directory.get(
                                'temporary_directory_name'
                            ),
                            main_file_path if main_file_path else ''
                        )
                    )

                    self.setElement()
                    self.control()
                    
                else:
                    return {}
            
            # Else, it is a directory, return informations
            else:
                
                return {
                    'name':self.name,
                    'main_files':self.main_files,
                    'elements':DataZipFile(
                        **main_file_config,
                        main_files=copy.deepcopy(self.main_files),
                        data_source_core=self.data_source_core
                    ).getElements(
                        os.path.join(
                            main_file_path if main_file_path else '',
                            self.name
                        )
                    )
                }

        if self.zip_file and extract_files:

            # Check if the main file has a temporary directory
            temporary_directory = self.data_source_core.getTemporaryFile(
                self.name,
                self.directory_name
            )

            if temporary_directory:
                self.zip_file.temporary_directory_name = temporary_directory.get(
                    'temporary_directory_name'
                )
            else:
                self.zip_file.extractFiles()
                
                self.data_source_core.temporary_main_files.append({
                    'name':self.name,
                    'directory_name':self.directory_name,
                    'temporary_directory_name':self.zip_file.temporary_directory_name
                })
            
        elif self.file and (transformation or add_data_version):
            self.file.extract(**kwargs)

            if self.data_source_core.tables:
                for table in self.data_source_core.tables:
                    if isinstance(table.data_conditions[self.data_source_core.name],dict):      
                        if self.data_source_core.checkDataConditions(
                            table.data_conditions[self.data_source_core.name],
                            table.name,
                            self.file.name,
                            table.data_conditions[self.data_source_core.name].get('id'),
                            self.file.directory_name
                        ):          
                            self.file.data = self.data_source_core.transformData(
                                self.file.data,
                                table.name,
                                self.file.name,
                                table.data_conditions[self.data_source_core.name].get('id'),
                                self.file.directory_name
                            )
                            
            else:
                self.file.data = self.data_source_core.transformData(
                    self.file.data,
                    file_name = self.file.name,
                    directory_name = self.file.directory_name
                )
        
            if add_data_version:
                self.data_source_core.data_version.setValues(
                    **(
                        self.main_files[0]
                        if self.main_files else self.file.informations
                    ),
                )

                self.data_source_core.data_version.updateData(
                    self.file.data,
                    self.file.name
                )
            
        elif self.directory:
            self.directory.setElements()

        for data_fetcher in self.data_source_core.data_fetchers:
            self.setStatus(
                data_fetcher.raw_files
            )
        
        return self.informations

    def setStatus(
        self,
        files:List[RawDataFile],
        check_directory:bool = True
    ) -> List[RawDataFile]:

        if self.file:
            self.file.setStatus(files)
        
        if self.directory and check_directory:
            
            return self.directory.setElementStatus(
                files,
                check_directory
            )    
        
        if self.zip_file:
            self.zip_file.setStatus(files)

class DataZipFile(ZipFile_):
    """Represent a zip file with data.

    Attributes:
    ----------
        name (str): File name.
        directory_name (str): Directory name.
        connection (Connection): Connection to a database.
        main_file (File): Main file name.
        schema (Union[Schema,str]): Schema.
        table (Union[Table,str,list]): Table.
        data_configuration (DataConfiguration): Data configuration.
        data_source (DataSource): Data source configuration.
        status (str): Status.
        extensions (list): Accepted extensions.

    Methods:
    ----------
        checkData(self) -> None: If the zip file contain only one csv file, it can be save with pandas.read_csv.
        saveFiles(self) -> None: Save files in zip file

    Examples:
    ----------
        >>> import datablender
        >>> zip_file = datablender.DataZipFile(
        >>>     'path/to/file',
        >>>     'file_name.zip',
        >>>     datablender.Connection()
        >>> )
        >>> zip_file.saveFiles()
        >>> zip_file.connection.close()
    
    """
    def __init__(
        self,
        name:str=None,
        directory_name:str=None,
        path:str=None,
        connection:Connection=None,
        data_configuration:DataConfiguration = None,
        acticvate_data_config:bool = False,
        main_files:List[Dict[str,str]]= [],
        data_source_core:DataSourceCore = None,
        data_source_name:str=None,
        status:str = 'developpement',
        fetch:List[dict] = [],
        extract:List[dict] = [],
        transform:list = [],
        save:List[dict]=[],
        control:dict = {},
        data_version:dict = {},
        database:Database = None,
        database_name:str= None,
        schema:Union[Schema,str] = 'public',
        table:Union[Table,str,list] = None,
        event_server = None,
        actions:List[Dict[str,any]] = []
    ):
        """Initiate the zip file.

        Args:
            connection (Connection): Connection to a database.
            name (str): File name.
            directory_name (str): Directory name
            main_file (File, optional): Main file name. Defaults to None.
            schema (Union[Schema,str], optional): Schema. Defaults to 'public'.
            table (Union[Table,str,list], optional): Table. Defaults to None.
            data_configuration (DataConfiguration, optional): Data configuration. Defaults to None.
            data_source (DataSource, optional): Data source configuration. Defaults to None.
            status (str, optional): Status. Defaults to 'developpement'.
        """
        super(DataZipFile,self).__init__(
            name,
            directory_name,
            path
        )

        self.data_source_core = data_source_core if data_source_core else DataSourceCore(
            connection,
            data_configuration if data_configuration else DataConfiguration(active=acticvate_data_config),
            name = data_source_name,
            status = status,
            fetch = fetch,
            extract = extract,
            transform = transform,
            save = save,
            directory_name = self.directory_name,
            control = control,
            data_version = data_version,
            database=database,
            database_name = database_name,
            schema_name=schema,
            tables=table,
            event_server=event_server,
            actions=actions
        ).manage()
        
        self.checkData()

        self.main_files = main_files
        self.elements = []
        self.download_status = None

    def getElements(
        self,
        relative_path:str=None
    ) -> List[dict]:
        
        main_files = copy.deepcopy(self.main_files)

        if relative_path and main_files:
            main_files[-1]['main_file_path'] = relative_path
        else:
            main_files.append({
                'directory_name':self.directory_name,
                'name':self.name,
                'main_file_path':None
            })

        return [
            {
                'name':element,
                'main_files':main_files,
                'control':self.data_source_core.element_controller.control(
                    element,
                    'file' if '.' in element else 'directory'
                )
            } for element in list(set(
                [
                    name[len(relative_path)+1 if relative_path else 0:].split('/')[0]
                    for name in self.namelist()
                    if relative_path is None or (
                        relative_path is not None
                        and name != relative_path+'/'
                    )
                ]
            ))
        ]

    @property
    def informations(self) -> None:
        
        return {
            'name':self.name,
            'directory_name':self.directory_name,
            'path':self.path,
            'size':self.size,
            'main_files':self.main_files,
            'elements':self.getElements(),
            'download_status':self.download_status,
            'control':self.data_source_core.element_controller.control(self.name,'file'),
            'path_elements':getPathElements(
                self.data_source_core.directory_name,
                self.path,
                copy.deepcopy(self.main_files)
            )
        }
    
    def extractFiles(self) -> None:
        
        self.temporary_directory_name = tempfile.mkdtemp()
        self.extractall(
            self.temporary_directory_name +"\\"
        )

    def checkData(self) -> None:
        """If the zip file contain only one csv file, it can be save with pandas.read_csv.
        """
        
        contain_csv_file = self.namelist()[0][-4:]=='.csv'
        contain_only_one_file = len(self.namelist())==1
        self.save=~(contain_csv_file and contain_only_one_file)
    
    def saveFiles(self) -> None:
        """Save files in zip file.
        """
        
        self.extractFiles()
        
        self.main_files.append({
            'directory_name':self.directory_name,
            'name':self.name,
            'main_file_path':None
        })
        
        DataDirectory(
            self.temporary_directory_name +"\\",
            main_files = copy.deepcopy(self.main_files),
            data_source_core=self.data_source_core,
            is_temporary=True
        ).saveFiles()
        
        shutil.rmtree(self.temporary_directory_name)

    def setStatus(
        self,
        files:List[RawDataFile]
    ) -> None:
        
        self.download_status = 'existant' if self.name in [
            file.name for file in files if file.name is not None
        ] else 'old'

class AsyncDataDirectory(Directory):
    """Directory containing files with data.

    Attributes:
    ----------
        extensions (list): Accepted extensions.

    Methods:
    ----------
        setSchema(self,schema:Union[Schema,str]) -> None : Set the schema.
        setTable(self,table:Union[Table,str,list]) -> None : .
        orderElements(self) -> list : .

    Examples:
    ----------
        >>> import datablender
        >>> directory = datablender.DataDirectory(
        >>>     datablender.Connection(),
        >>>     'path/to/directory'
        >>> )
        >>> directory.saveFiles()
        >>> directory.connection.close()

    """
    def __init__(
        self,
        directory_name:str,
        connection:AsyncConnection=None,
        data_configuration:AsyncDataConfiguration = None,
        acticvate_data_config:bool = False,
        main_files:List[Dict[str,str]]= [],
        data_source_core:AsyncDataSourceCore = None,
        data_source_name:str=None,
        status:str = 'developpement',
        fetch:List[dict] = [],
        extract:List[dict] = [],
        transform:list = [],
        save:List[dict]=[],
        control:dict = {},
        data_version:dict = {},
        database:AsyncDatabase = None,
        database_name:str= None,
        schema:Union[AsyncSchema,str] = 'public',
        table:Union[AsyncTable,str,list] = None,
        event_server = None,
        actions:List[Dict[str,any]] = [],
        is_temporary:bool = False,
        file_server:SMBConnection = None
    ):
        
        super(AsyncDataDirectory,self).__init__(
            directory_name,
            file_server,
            is_temporary
        )
        
        self.main_files = main_files

        self.data_source_core = data_source_core if data_source_core else AsyncDataSourceCore(
            connection,
            data_configuration if data_configuration else AsyncDataConfiguration(
                active=acticvate_data_config
            ),
            name = data_source_name,
            status = status,
            fetch = fetch,
            extract = extract,
            transform = transform,
            save = save,
            directory_name = self.name,
            control = control,
            data_version = data_version,
            database=database,
            database_name = database_name,
            schema_name=schema,
            tables=table,
            event_server=event_server,
            actions = actions
        )

        self.elements:List[AsyncDataDirectoryElement]=[]
        self.raw_files:List[AsyncRawDataFile] = []

        if self.main_files and not is_temporary:
            self.main_files[-1]['main_file_path'] = os.path.join(
                self.main_files[-1].get('main_file_path'),
                self.name_
            ) if self.main_files[-1].get('main_file_path') else self.name_
    
    @property
    def informations(self) -> dict:

        return {
            'name':self.name_,
            'path':self.name,
            'main_files':self.main_files,
            'elements':[
                element.informations
                for element in self.elements
            ]+[
                file.informations
                for file in self.raw_files
                if file.download_status == 'new'
            ],
            'control':self.data_source_core.element_controller.control(self.name_,'directory'),
            'path_elements':getPathElements(
                self.data_source_core.directory_name,
                self.name,
                copy.deepcopy(self.main_files)
            )
        }

    def setElements(self) -> None:
        """Set the elements by initiatig every element with the Data Directory Element.
        """
        
        self.elements = [
            AsyncDataDirectoryElement(
                self.data_source_core,
                name = element_name,
                directory_name = self.name,
                main_files = copy.deepcopy(self.main_files),
                file_server=self.file_server,
                is_temporary= self.is_temporary
            ).control(
                self.elements_name
            ) for element_name in self.elements_name
        ]

    def orderElements(self) -> None:
        """List of the files in a directory, if there's a table list in config,
        sort the files to load data in rigth order
        """
        [
            element.setOrderPriority(
                [
                    *self.data_source_core.getTablesAssociatedWithFiles(),
                    *self.data_source_core.data_version.getTablesAssociatedWithFiles()
                ]
            ) for element in self.elements
        ]
        
        self.elements = sorted(
            self.elements,
            key=lambda item: (item.priority, item.order, item.name)
        )

    async def manageElements(self):
        """
        Before loading data, manage files in diretory to delete old ones
        by comparing files in the database.
        """
        if not self.main_files:
            database_files = await self.data_source_core.main_files_view.select({
                'directory_name':self.name,
                'schema':self.data_source_core.schema_name
            })
            database_files = database_files.data.frame.to_dict('records')
            [
                await self.deleteDataFile(main_file)
                for main_file in database_files
                if main_file.get('name') not in [
                    element.name for element in self.elements if element.is_file
                ]
            ]

    async def deleteDataFile(self,main_file:dict):
        
        for file_ in main_file.get('files'):       
            await self.data_source_core.files_table.delete({'id':file_.get('id')})     
            await self.data_source_core.deleteData(
                file_.get('name'),
                {'file_id':file_.get('id')}
            )
 
    async def saveFiles(self, **kwargs) -> None:
        """Save files in directory.
        """
        self.setElements()
        await self.manageElements()
        self.orderElements()
        
        for element in self.elements:
            await element.save(**kwargs)

    def setElementStatus(
        self,
        files:List[AsyncRawDataFile],
        check_directory:bool = False
    ) -> List[RawDataFile]:

        self.setElements()

        # For every elements in the directory, set the status
        [
            element.setStatus(
                files,
                check_directory
            )
            for element in self.elements
        ]
        [
            file.setStatus(
                [
                    element.informations
                    for element in self.elements
                ],
                self.name
            )
            for file in files
        ]

        self.raw_files = [
            file for file in files
            if (
                file.download_status == 'new'
                and os.path.abspath(
                    file.directory_name
                ) == os.path.abspath(
                    self.name
                )
            ) 
        ]

class AsyncDataDirectoryElement(DirectoryElement):
    """Element of a directory containing data, which can be a DataFile, DataDirectory of a ZipFile_.

    Attributes:
    ----------


    Methods:
    ----------
        getTable(self) -> Union[Table,Dict[str, Table]] : Control element with his name.

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        data_source_core:AsyncDataSourceCore,
        name:str = None,
        directory_name:str = None,
        path:str = None,
        main_files:List[Dict[str,str]]= [],
        file_server:SMBConnection = None,
        is_temporary:bool = False,
        **kwargs
    ):
        self.data_source_core = data_source_core
        self.main_files = main_files

        if path or (name and directory_name):
            super(AsyncDataDirectoryElement,self).__init__(
                name,
                directory_name,
                path,
                file_server,
                is_temporary
            )
        else:
            self.name =name
                
        self.priority = None
        self.order = None

        self.file:AsyncDataFile = None
        self.directory:AsyncDataDirectory = None
        self.zip_file:AsyncDataZipFile = None

        if path or (name and directory_name):
            self.setElement()
    
    @property
    def informations(self) -> dict:
        
        if self.file:
            return self.file.informations
            
        elif self.directory:
            return self.directory.informations
            
        elif self.zip_file:
            return self.zip_file.informations

        else:
            return {}

    def setElement(self) -> None:
        if self.is_directory:

            self.directory = AsyncDataDirectory(
                self.path+'/',
                main_files=copy.deepcopy(self.main_files),
                data_source_core=self.data_source_core,
                file_server=self.file_server,
                is_temporary=self.is_temporary
            )

        elif self.is_zip_file:

            self.zip_file = AsyncDataZipFile(
                self.name,
                self.directory_name,
                main_files=copy.deepcopy(self.main_files),
                data_source_core=self.data_source_core,
                file_server=self.file_server,
                is_temporary=self.is_temporary
            )

        elif self.is_file:
            self.file = AsyncDataFile(
                self.directory_name,
                self.name,
                main_files=copy.deepcopy(self.main_files),
                data_source_core = self.data_source_core,
                file_server=self.file_server,
                is_temporary=self.is_temporary
            )
        
    def control(
        self,
        directory_element_names:List[str]= []
    ) -> AsyncDataDirectoryElement:
        """Check the element type (directory,zip file or data file) and if it can be saved.
        """

        if hasattr(self,'directory_name') and self.directory_name and self.name:
        
            self.save_directory = False
            self.save_file = False
            self.save_zip_file = False

            if self.is_directory and self.name.lower()+'.zip' not in [n.lower() for n in directory_element_names]:
                self.save_directory = self.data_source_core.element_controller.control(
                    self.name,
                    'directory'
                )

            elif self.is_zip_file:
                self.save_zip_file = self.zip_file.save and self.data_source_core.element_controller.control(
                    self.name,
                    'zipfile'
                )
                
            elif not self.is_temp_file:
                self.save_file = self.data_source_core.element_controller.control(
                    self.name,
                    'file'
                )
        
        return self

    async def save(self,**kwargs):
        """Save the element.
        """

        if self.save_directory:
            await self.directory.saveFiles(**kwargs)

        elif self.save_zip_file:
            await self.zip_file.saveFiles(**kwargs)

        elif self.save_file:
            await self.file.save(**kwargs)

    def setOrderPriority(self,tables:List[dict]) -> None:
        tables = [
            table for table in tables 
            if self.data_source_core.checkDataConditions(
                table['data_conditions'],
                table['name'],
                self.name,
                directory_name=self.directory_name
            )
        ]
        self.priority = tables[0]['priority'] if tables else 3
        self.order = tables[0]['order'] if tables else 1

    async def get(
        self,
        extract_files:bool = False,
        transformation:list = [],
        add_data_version:bool = False,
        columns_actions:List[dict] =[],
        **kwargs
    ) -> dict:
        if self.main_files:
            
            # To do :  if there's more main files then 1
            for main_file_config in self.main_files:

                main_file_config = copy.deepcopy(main_file_config)
                main_file_path = main_file_config.pop('main_file_path')

            # If it is a file
            if '.' in self.name:

                # Check if the main file has a temporary directory
                temporary_directory = self.data_source_core.getTemporaryFile(
                    **main_file_config
                )

                # If it's a file and there is a temporary directory, 
                # then initiate the data directory element
                if temporary_directory:
                    
                    super(AsyncDataDirectoryElement,self).__init__(
                        self.name,
                        os.path.join(
                            temporary_directory.get(
                                'temporary_directory_name'
                            ),
                            main_file_path if main_file_path else ''
                        )
                    )

                    self.setElement()
                    self.control()
                    
                else:
                    return {}
            
            # Else, it is a directory, return informations
            else:
                
                return {
                    'name':self.name,
                    'main_files':self.main_files,
                    'elements':AsyncDataZipFile(
                        **main_file_config,
                        main_files=copy.deepcopy(self.main_files),
                        data_source_core=self.data_source_core
                    ).getElements(
                        os.path.join(
                            main_file_path if main_file_path else '',
                            self.name
                        )
                    )
                }

        if self.zip_file and extract_files:

            # Check if the main file has a temporary directory
            temporary_directory = self.data_source_core.getTemporaryFile(
                self.name,
                self.directory_name
            )

            if temporary_directory:
                self.zip_file.temporary_directory_name = temporary_directory.get(
                    'temporary_directory_name'
                )
            else:
                await self.zip_file.extractFiles()
                
                self.data_source_core.temporary_main_files.append({
                    'name':self.name,
                    'directory_name':self.directory_name,
                    'temporary_directory_name':self.zip_file.temporary_directory_name
                })
            
        elif self.file:
            await self.file.extract(**kwargs)
            
            if transformation or add_data_version:
                
                self.data_source_core.data_version.setValues(
                    **(
                        self.main_files[0]
                        if self.main_files else self.file.informations
                    ),
                )
                
                if self.data_source_core.tables:

                    self.file.data = await self.data_source_core.actionsTables(
                        ['transform','version'] if add_data_version else ['transform'],
                        self.file.data,
                        file_name = self.file.name,
                        directory_name = self.file.name,
                    )
                
                else:
                    await self.data_source_core.transformData(
                        self.file.data,
                        file_name = self.file.name,
                        directory_name = self.file.directory_name
                    )
                    if add_data_version:
                        self.data_source_core.updateData(
                            self.file.data,
                            self.file.name,
                            self.file.directory_name
                        )

            [       
                await self.file.data.columnAction(**column)
                for column in columns_actions
            ]

        elif self.directory:
            self.directory.setElements()

        check_directory = kwargs.pop('check_directory',False)
        for data_fetcher in self.data_source_core.data_fetchers:
            self.setStatus(
                data_fetcher.raw_files,
                check_directory
            )
        
        self.data_source_core.data_logging.action_name = None
        return self.informations

    def setStatus(
        self,
        files:List[AsyncRawDataFile],
        check_directory:bool = True
    ) -> List[AsyncRawDataFile]:

        if self.file:
            self.file.setStatus(files)
        
        if self.directory and check_directory:
            return self.directory.setElementStatus(
                files,
                check_directory
            )    
        
        if self.zip_file:
            self.zip_file.setStatus(files)

class AsyncDataZipFile(ZipFile_):
    """Represent a zip file with data.

    Attributes:
    ----------
        name (str): File name.
        directory_name (str): Directory name.
        connection (Connection): Connection to a database.
        main_file (File): Main file name.
        schema (Union[Schema,str]): Schema.
        table (Union[Table,str,list]): Table.
        data_configuration (DataConfiguration): Data configuration.
        data_source (DataSource): Data source configuration.
        status (str): Status.
        extensions (list): Accepted extensions.

    Methods:
    ----------
        checkData(self) -> None: If the zip file contain only one csv file, it can be save with pandas.read_csv.
        saveFiles(self) -> None: Save files in zip file

    Examples:
    ----------
        >>> import datablender
        >>> zip_file = datablender.DataZipFile(
        >>>     'path/to/file',
        >>>     'file_name.zip',
        >>>     datablender.Connection()
        >>> )
        >>> zip_file.saveFiles()
        >>> zip_file.connection.close()
    
    """
    def __init__(
        self,
        name:str=None,
        directory_name:str=None,
        path:str=None,
        connection:AsyncConnection=None,
        data_configuration:AsyncDataConfiguration = None,
        acticvate_data_config:bool = False,
        main_files:List[Dict[str,str]]= [],
        data_source_core:AsyncDataSourceCore = None,
        data_source_name:str=None,
        status:str = 'developpement',
        fetch:List[dict] = [],
        extract:List[dict] = [],
        transform:list = [],
        save:List[dict]=[],
        control:dict = {},
        data_version:dict = {},
        database:AsyncDatabase = None,
        database_name:str= None,
        schema:Union[AsyncSchema,str] = 'public',
        table:Union[AsyncTable,str,list] = None,
        event_server = None,
        actions:List[Dict[str,any]] = [],
        file_server:SMBConnection = None,
        is_temporary:bool = False
    ):
        """Initiate the zip file.

        Args:
            connection (Connection): Connection to a database.
            name (str): File name.
            directory_name (str): Directory name
            main_file (File, optional): Main file name. Defaults to None.
            schema (Union[Schema,str], optional): Schema. Defaults to 'public'.
            table (Union[Table,str,list], optional): Table. Defaults to None.
            data_configuration (DataConfiguration, optional): Data configuration. Defaults to None.
            data_source (DataSource, optional): Data source configuration. Defaults to None.
            status (str, optional): Status. Defaults to 'developpement'.
        """
        super(AsyncDataZipFile,self).__init__(
            name,
            directory_name,
            path,
            file_server,
            is_temporary
        )

        self.data_source_core = data_source_core if data_source_core else AsyncDataSourceCore(
            connection,
            data_configuration if data_configuration else AsyncDataConfiguration(
                active=acticvate_data_config
            ),
            name = data_source_name,
            status = status,
            fetch = fetch,
            extract = extract,
            transform = transform,
            save = save,
            directory_name = self.directory_name,
            control = control,
            data_version = data_version,
            database=database,
            database_name = database_name,
            schema_name=schema,
            tables=table,
            event_server=event_server,
            actions=actions
        )
        
        self.checkData()

        self.main_files = main_files
        self.elements = []
        self.download_status = None

    def getElements(
        self,
        relative_path:str=None
    ) -> List[dict]:
        
        main_files = copy.deepcopy(self.main_files)

        if relative_path and main_files:
            main_files[-1]['main_file_path'] = relative_path
        else:
            main_files.append({
                'directory_name':self.directory_name,
                'name':self.name,
                'main_file_path':None
            })

        return [
            {
                'name':element,
                'main_files':main_files,
                'control':self.data_source_core.element_controller.control(
                    element,
                    'file' if '.' in element else 'directory'
                )
            } for element in list(set(
                [
                    name[len(relative_path)+1 if relative_path else 0:].split('/')[0]
                    for name in self.namelist()
                    if relative_path is None or (
                        relative_path is not None
                        and name != relative_path+'/'
                    )
                ]
            ))
        ]

    @property
    def informations(self) -> None:
        
        return {
            'name':self.name,
            'directory_name':self.directory_name,
            'path':self.path,
            'size':self.size,
            'main_files':self.main_files,
            'elements':self.getElements(),
            'download_status':self.download_status,
            'control':self.data_source_core.element_controller.control(self.name,'file'),
            'path_elements':getPathElements(
                self.data_source_core.directory_name,
                self.path,
                copy.deepcopy(self.main_files)
            )
        }
    
    async def extractFiles(self) -> None:

        directory = Directory(
            os.path.join(
                self.directory_name,
                self.name_
            )
        )

        await self.data_source_core.data_logging.logEvent(
            'extract',
            'loading',
            directory_element = {
                'name':self.name,
                'directory_name':self.directory_name
            }
        )

        try:

            self.temporary_directory_name = directory.name
            
            if not directory.exists:
                directory.manage()
                self.extractall(
                    self.temporary_directory_name +"\\"
                )
            
        except Exception as error:
            directory.delete()

            await self.data_source_core.data_logging.logEvent(
                'extract',
                error=error,
                directory_element = {
                    'name':self.name,
                    'directory_name':self.directory_name
                }
            )
            
        else:

            await self.data_source_core.data_logging.logEvent(
                'extract',
                directory_element = {
                    'name':self.name,
                    'directory_name':self.directory_name
                }
            )

    def checkData(self) -> None:
        """If the zip file contain only one csv file, it can be save with pandas.read_csv.
        """
        
        contain_csv_file = self.namelist()[0][-4:]=='.csv'
        contain_only_one_file = len(self.namelist())==1
        self.save= not (contain_csv_file and contain_only_one_file)
    
    async def saveFiles(self,**kwargs) -> None:
        """Save files in zip file.
        """
        
        if self.data_source_core.data_version.checkDataSaving(
            self.name,
            self.directory_name,
            **kwargs
        ):

            await self.extractFiles()
            
            self.main_files.append({
                'directory_name':self.directory_name,
                'name':self.name,
                'main_file_path':None
            })
            
            await AsyncDataDirectory(
                self.temporary_directory_name +"\\",
                main_files = copy.deepcopy(self.main_files),
                data_source_core=self.data_source_core,
                is_temporary=True,
                file_server=self.file_server
            ).saveFiles(**kwargs)
            
            shutil.rmtree(self.temporary_directory_name)

    def setStatus(
        self,
        files:List[RawDataFile]
    ) -> None:
        
        self.download_status = 'existant' if self.name in [
            file.name for file in files if file.name is not None
        ] else 'old'
