"""
This module contain the data file class.
A file contening data to go in a database. From the file name, the directory name, the schema and the table, data in the file can be imported.
The mode defined how it is import, based on the modification date, by updating or replacing a table, or to multiple tables.
A function can be provided to extract data from the file. Transformations can be applied to the data as well. If the file is in a archive,
it can be indicate via the main file.
If a data version
"""
from __future__ import annotations
from typing import Union, List, Dict

import os
import copy
import datetime
from smb.SMBConnection import SMBConnection

from datablender.base import (
    File,
    DataConfiguration,
    Connection,
    Data,
    AsyncConnection,
    AsyncDataConfiguration
)
from datablender.database import (
    Table,
    Schema,
    Database,
    AsyncTable,
    AsyncSchema,
    AsyncDatabase
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

class DataFile(File):
    """A file contening data to go in a database.

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        directory_name (str): Directory name.
        name (str): File name.
        main_file (str): Main file containing the data file.
        
    Methods:
    ----------
        getTable(self,table_name,tables_names) -> None: .
        getFileDatabaseInformations(self) -> None: .
        checkInDatabase(self) -> None: .

    Examples:
    ----------
        >>> import datablender
        >>> file = datablender.DataFile(
        >>>     datablender.Connection(),
        >>>     'path/to/file',
        >>>     'file_name.csv'
        >>> )
        >>> file.save()
        >>> file.connection.close()

    """
    def __init__(
        self,
        directory_name:str=None,
        file_name:str=None,
        path:str=None,
        connection:Connection = None,
        data_configuration:DataConfiguration = None,
        acticvate_data_config:bool = False,
        main_files:List[Dict[str,str]]= [],
        import_mode:str = 'modification_time',
        data_source_core:DataSourceCore = None,
        data_source_name:str=None,
        status:str = 'developpement',
        fetch:List[dict] = [],
        extract:List[dict] = [],
        transform:List[dict] = [],
        save:List[dict] = [],
        data_version:dict = {},
        database:Database = None,
        database_name:str= None,
        schema:Union[Schema,str] = 'public',
        table:Union[Table,str,list] = None,
        event_server = None,
        actions:List[Dict[str,any]] = []
    ):
        super(DataFile,self).__init__(
            directory_name,
            file_name,
            path
        )
        
        self.import_mode = import_mode

        self.main_files = main_files
        
        self.data_modification_time = File(
            self.main_files[0].get('directory_name'),
            self.main_files[0].get('name')
        ).modification_time if self.main_files else self.modification_time

        self.data_source_core = data_source_core if data_source_core else DataSourceCore(
            connection,
            data_configuration if data_configuration else DataConfiguration(active=acticvate_data_config),
            name = data_source_name,
            status = status,
            fetch = fetch,
            extract = extract,
            transform = transform,
            save = save,
            directory_name=self.directory_name,
            control = {'file_controls':{'elements':{self.name:True}}},
            data_version = data_version,
            database=database,
            database_name = database_name,
            schema_name=schema,
            tables=table,
            event_server=event_server,
            actions = actions
        ).manage()

        self.data = Data(
            meta_columns=[],
            columns=[]
        )
        
        self.id = None
        self.database_modification_time:datetime.datetime = None
        self.save_data = True
        self.download_status = None

    @property
    def path_index(self) -> str:
        if self.main_files:
            return os.path.join(
                os.path.join(
                    self.main_files[0].get('directory_name'),
                    self.main_files[0].get('name'),
                    self.main_files[0].get('main_file_path','') if self.main_files[0].get('main_file_path') else '' 
                ),
                self.name
            )
        else:
            return self.path
        
    @property
    def informations(self) -> dict:
        if self.data.frame.empty and self.extension in ['xlsx','xls','xlsm','csv','zip','txt','shp','dbf']:
            self.extract(nrows = 1)
            
        return {
            'id':self.id,
            'name':self.name,
            'schema':self.data_source_core.schema_name,
            'main_files':self.main_files,
            'tables':[table.name for table in self.data_source_core.tables],
            'modification_time':self.data_modification_time.strftime('%Y-%m-%d'),
            'size':self.size,
            'rows':self.data.frame.shape[0],
            'directory_name':None if self.main_files else self.directory_name,
            'import_mode':self.import_mode,
            'path':None if self.main_files else self.path,
            'columns':self.data.columns,
            'status':self.data_source_core.status,
            'data':self.data.export(),
            'control':self.data_source_core.element_controller.control(self.name,'file'),
            'download_status':self.download_status,
            'path_index':self.path_index,
            'path_elements':getPathElements(
                self.data_source_core.directory_name,
                self.path,
                copy.deepcopy(self.main_files)
            )
        }

    def getFileDatabaseInformations(self) -> None:
        """Get file information in database.
        """
        informations = self.data_source_core.files_table.data.frame.loc[self.path_index]
        self.id = informations['id']
        self.database_modification_time = informations['modification_time']

    def checkInDatabase(self) -> None:
        """Check the file in the database.
        """
        self.data_source_core.files_table.getFiles()
        
        # If the file in the database, get informations and check the modification time.
        if self.data_source_core.files_table.checkFile(
            self.path_index
        ):
            self.getFileDatabaseInformations()
            # if (self.import_mode == 'modification_time' and self.database_modification_time != self.data_modification_time) or self.import_mode !="table_import":
            # if self.data_modification_time.strftime('%Y%m%d%H%M%S') == self.database_modification_time.strftime('%Y%m%d%H%M%S'):
            #     self.save_data=False
            # else:
            #     self.deleteData()
            self.deleteData()

        else:
            self.data_source_core.files_table.insert({
                k:v for k,v in self.informations.items()
                if k not in ['data','id','control','path','download_status','path_elements']
            })
            self.data_source_core.files_table.getFiles()
            self.getFileDatabaseInformations()
        
    def extract(
        self,
        *args,
        **kwargs
    ) -> DataFile:
        """Extract data from file.
        """
        
        self.data_source_core.data_logging.logEvent(
            'extract',
            'loading',
            self.id
        )

        self.data = Data(
            self.read(
                *args,
                **{
                    **self.data_source_core.getExtractArguments(
                        self.name
                    ),
                    **kwargs
                }
            ).content,
            self.name,
            self.directory_name,
            name = self.name_,
            meta_columns=[],
            columns=[],
            schema_name = self.data_source_core.schema_name,
            schema_type = 'source'
        )

        self.data_source_core.data_logging.logEvent(
            'extract',
            'loaded',
            self.id
        )
        
        return self

    def saveData(self,**kwargs) -> None:
        """Save data in database.
        """

        self.data_source_core.data_logging.logEvent(
            'save',
            'loading',
            self.id
        )

        if self.data.frame.shape[0]:
            self.data_source_core.saveData(
                copy.deepcopy(self.data),
                self.name,
                self.import_mode,
                self.directory_name,
                self.id,
                **kwargs
            )        

        self.data_source_core.files_table.updateFileInformation(
            **self.informations
        )
        
        self.data_source_core.data_logging.logEvent(
            'save',
            'loaded',
            self.id
        )

    def save(self,**kwargs) -> None:
        """Save data from file in database.
        """
        self.save_data = self.data_source_core.data_version.checkDataSaving(
            self.name
        )
        
        if self.save_data:
            self.checkInDatabase()

        if self.save_data:
            self.extract()
            self.data_source_core.updateDataVersion(
                self.name,
                self.data_modification_time,
                self.main_files,
                self.data
            )

            if self.save_data:
                self.saveData(**kwargs)

    def deleteData(self) -> None:
        if not self.id:
            self.getFileDatabaseInformations()
        
        self.data_source_core.deleteData(
            self.name,
            {'file_id':self.id},
            self.directory_name
        )

    def setStatus(
        self,
        files:List[RawDataFile]
    ) -> None:
        
        self.download_status = 'existant' if self.name in [
            file.name for file in files if file.name is not None
        ] else 'old'

class AsyncDataFile(File):
    """A file contening data to go in a database.

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        directory_name (str): Directory name.
        name (str): File name.
        main_file (str): Main file containing the data file.
        
    Methods:
    ----------
        getTable(self,table_name,tables_names) -> None: .
        getFileDatabaseInformations(self) -> None: .
        checkInDatabase(self) -> None: .

    Examples:
    ----------
        >>> import datablender
        >>> file = datablender.DataFile(
        >>>     datablender.Connection(),
        >>>     'path/to/file',
        >>>     'file_name.csv'
        >>> )
        >>> file.save()
        >>> file.connection.close()

    """
    def __init__(
        self,
        directory_name:str=None,
        file_name:str=None,
        path:str=None,
        connection:AsyncConnection = None,
        data_configuration:AsyncDataConfiguration = None,
        acticvate_data_config:bool = False,
        main_files:List[Dict[str,str]]= [],
        data_source_core:AsyncDataSourceCore = None,
        data_source_name:str=None,
        status:str = 'developpement',
        fetch:List[dict] = [],
        extract:List[dict] = [],
        transform:List[dict] = [],
        save:List[dict] = [],
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
        super(AsyncDataFile,self).__init__(
            directory_name,
            file_name,
            path,
            file_server=file_server,
            is_temporary=is_temporary
        )
        
        self.main_files = main_files
        
        self.data_modification_time = File(
            self.main_files[0].get('directory_name'),
            self.main_files[0].get('name'),
            file_server=self.file_server
        ).modification_time if self.main_files else self.modification_time

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
            directory_name=self.directory_name,
            control = {'file_controls':{'elements':{self.name:True}}},
            data_version = data_version,
            database=database,
            database_name = database_name,
            schema_name=schema,
            tables=table,
            event_server=event_server,
            actions = actions
        )

        self.data = Data(
            meta_columns=[],
            columns=[]
        )
        
        self.id = None
        self.database_modification_time:datetime.datetime = None
        self.save_data = True
        self.download_status = None
    
    @property
    def path_index(self) -> str:
        if self.main_files:
            return os.path.join(
                os.path.join(
                    self.main_files[0].get('directory_name'),
                    self.main_files[0].get('name'),
                    self.main_files[0].get('main_file_path','') if self.main_files[0].get('main_file_path') else '' 
                ),
                self.name
            )
        else:
            return self.path
        
    @property
    def informations(self) -> dict:

        return {
            'id':self.id,
            'name':self.name,
            'schema':self.data_source_core.schema_name,
            'main_files':self.main_files,
            'tables':[table.name for table in self.data_source_core.tables],
            'modification_time':self.data_modification_time.strftime('%Y-%m-%d %H:%M:%S.%f'),
            'size':self.size,
            'rows':self.data.frame.shape[0],
            'directory_name':None if self.main_files else self.directory_name,
            'path':None if self.main_files else self.path,
            'columns':self.data.columns,
            'status':self.data_source_core.status,
            'data':self.data.export(),
            'control':self.data_source_core.element_controller.control(self.name,'file'),
            'download_status':self.download_status,
            'path_index':self.path_index,
            'path_elements':getPathElements(
                self.data_source_core.directory_name,
                self.path,
                copy.deepcopy(self.main_files),
                self.file_server,
                self.is_temporary
            )
        }

    def getFileDatabaseInformations(self) -> None:
        """Get file information in database.
        """
        informations = self.data_source_core.files_table.data.frame.loc[self.path_index]
        self.id = informations['id']
        self.database_modification_time = informations['modification_time']

    async def checkInDatabase(
        self,
        import_mode:str=None
    ) -> None:
        """Check the file in the database.
        """
        await self.data_source_core.files_table.getFiles()
        
        # If the file in the database, get informations and check the modification time.
        if self.data_source_core.files_table.checkFile(
            self.path_index
        ):
            self.getFileDatabaseInformations()

            if (
                import_mode == 'modification_time' and
                self.data_modification_time.strftime('%Y%m%d%H%M%S') == self.database_modification_time.strftime('%Y%m%d%H%M%S')
            ):
                self.save_data=False
            else:
                await self.deleteData()


        else:
            await self.extract(nrows = 1)
            await self.data_source_core.files_table.insert(self.informations)
            await self.data_source_core.files_table.getFiles()
            self.getFileDatabaseInformations()
        
    async def extract(
        self,
        *args,
        **kwargs
    ) -> AsyncDataFile:
        """Extract data from file.
        """
        
        await self.data_source_core.data_logging.logEvent(
            'extract',
            'loading',
            informations = {
                'name':self.name,
                'directory_name':self.directory_name,
                'id':int(self.id) if self.id else None
            }
        )

        try:

            loaded_rows = kwargs.pop('loaded_rows',kwargs.get('nrows',None))
            transform_columns = kwargs.pop('columns',[])

            self.data = Data(
                self.read(
                    *args,
                    **{
                        **self.data_source_core.getExtractArguments(
                            self.name
                        ),
                        **kwargs
                    }
                ).content,
                self.name,
                self.directory_name,
                name = self.name_,
                meta_columns=[],
                columns=[],
                schema_name = self.data_source_core.schema_name,
                schema_type = 'source',
                loaded_rows = loaded_rows,
                transform_columns = transform_columns
            )

        except Exception as error:
            await self.data_source_core.data_logging.logEvent(
                error =error
            )
        else:

            await self.data_source_core.data_logging.logEvent()
        
        return self

    async def save(
        self,
        import_mode:str=None,
        update_version:bool = False,
        data_version_value:dict = False,
        actions:List[str] = ['transform','version','add_informations','manage','copy','reset_data'],
        **kwargs,
    ) -> None:
        """Save data from file in database.
        """
        
        self.save_data = self.data_source_core.data_version.checkDataSaving(
            self.name,
            self.data_source_core.directory_name,
            data_version_value,
            update_version
        )
        
        if self.save_data:
            await self.checkInDatabase(import_mode)

        if self.save_data:
            await self.extract()

            self.save_data = await self.data_source_core.updateDataVersion(
                self.name,
                self.directory_name,
                self.data_modification_time,
                self.main_files,
                self.data,
                update_version,
                data_version_value
            )

            if self.save_data: 
                if self.data.frame.shape[0]:
                    await self.data_source_core.actionsTables(
                        actions,
                        self.data,
                        file_name = self.name,
                        directory_name = self.directory_name,
                        file_id = self.id,
                        manage_from = 'values',
                        main_files = self.main_files,
                        data_version_value = data_version_value,
                        **kwargs
                    )        

                await self.data_source_core.files_table.updateFileInformation(
                    **self.informations
                )

    async def deleteData(self) -> None:

        if not self.id:
            self.getFileDatabaseInformations()
        
        await self.data_source_core.deleteData(
            self.name,
            {'file_id':self.id},
            self.directory_name
        )

    def setStatus(
        self,
        files:List[AsyncRawDataFile]
    ) -> None:
        
        self.download_status = 'existant' if self.name in [
            file.name for file in files if file.name is not None
        ] else 'old'
