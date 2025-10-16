"""

"""
from typing import List,Dict

import os

from datablender.base import Connection, DataConfiguration

def addPathElements(
    data_source_directory_name:str,
    path:str,
    main_files:List[Dict[str,str]] = [],
    elements:List[Dict[str,str]] = []
) -> List[Dict[str,str]]: 
    
    if main_files:
        
        elements.append({
            'name':os.path.basename(path),
            'path':None,
            'main_files':main_files
        })

        main_file = main_files.pop()

        #main_file.get('main_file_path')

        elements = addPathElements(
            data_source_directory_name,
            os.path.join(
                main_file.get('directory_name'),
                main_file.get('name')
            ),
            main_files,
            elements
        )


    elif os.path.normpath(path) == os.path.normpath(data_source_directory_name):
        elements.append({
            'name':os.path.normpath(data_source_directory_name),
            'path':os.path.normpath(data_source_directory_name)
        })
    else:
        elements.append({
            'name':os.path.basename(path),
            'path':path
        })
        elements= addPathElements(
            data_source_directory_name,
            os.path.dirname(path),
            main_files,
            elements
        )

    return elements

def getPathElements(
    data_source_directory_name:str,
    path:str,
    main_files:List[Dict[str,str]] = [],
    file_server = None,
    is_temporary:bool = False
) -> List[Dict[str,str]]:

    main_files.reverse()

    elements = addPathElements(
        data_source_directory_name if file_server or is_temporary else os.path.abspath(data_source_directory_name) ,
        path if file_server or is_temporary else os.path.abspath(path),
        main_files,
        []
    )
    
    elements.reverse()
    
    return elements

from datablender.data.dataVersion import (
    DataVersion,
    DataVersionColumn,
    DataVersionTable,
    DataVersionValue
)
from datablender.data.dataSourceCore import (
    DataSourceCore,
    DirectoryElementController,
    DataFetcher,
    RawDataFile
)
from datablender.data.dataProcess import DataProcess
from datablender.data.asyncDataProcess import AsyncDataProcess
from datablender.data.filesTable import FilesTable
from datablender.data.dataFile import DataFile
from datablender.data.dataDirectory import (
    DataDirectory,
    DataDirectoryElement,
    DataZipFile
)
from datablender.data.dataSource import DataSource, AsyncDataSource
from datablender.data.dataServer import DataServer
from datablender.data.asyncDataServer import AsyncDataServer

def importData(
    connection:Connection,
    data_source_name:str,
    acticvate_data_config:bool = True
) -> None:

    data_source_core = DataSourceCore(
        connection,
        DataConfiguration(active=acticvate_data_config),
        name=data_source_name
    ).manage()
    
    DataDirectory(
        data_source_core.directory_name,
        connection,
        data_source_core=data_source_core
    ).saveFiles()

    # data_source.executeQueries()

