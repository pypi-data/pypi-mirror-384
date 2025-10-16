"""

"""
from typing import Callable,Tuple
import types

import os
import sys
import numpy
import pandas

import importlib
import importlib.util

def getDirectoryElementName(
    path:str=None,
    directory_name:str=None,
    element_name:str=None
) -> Tuple[str,str]:
    """Get directory name and data directory element name from path.

    Args:
        path (str, optional): Path. Defaults to None.
        directory_name (str, optional): Directory name. Defaults to None.
        element_name (str, optional): Directory element name. Defaults to None.

    Returns:
        Tuple[str,str]: Directory name and directory element name.
    """
    if path:
        return os.path.dirname(
            os.path.normpath(path)
        ),os.path.basename(
            os.path.normpath(path)
        )
    elif directory_name and element_name:
        return directory_name,element_name

from datablender.base.file import File,ZipFile_
from datablender.base.directory import Directory,DirectoryElement
from datablender.base.text import Text,formatText
from datablender.base.request import Request, AsyncRequest

def normalize_user_name(user_name:str):
    return user_name.split(' ')[0]

def getNextID(elements:list,id_attribute_name:str='id') -> int:
    """Get next id in a list of dictionnary.

    Args:
        elements (list): List of dictionnary.
        id_attribute_name (str, optional): Id attribute name. Defaults to 'id'.

    Returns:
        int: Next id.
    """
    ids = numpy.append(
        numpy.array([element[id_attribute_name] for element in elements]),
        numpy.nan
    )
    df = pandas.DataFrame({
        'column':numpy.sort(ids),
        'ids':numpy.arange(1,ids.size+1,1)
    })
    return df.loc[df['column']!=df['ids'],'ids'].min()
   
def readFile(
    path:str=None,
    directory_name:str=None,
    file_name:str=None,
    **kwargs
) -> pandas.DataFrame:
    return File(
        directory_name,
        file_name,
        path
    ).read(
        **kwargs
    ).content

def getFunction(
    function_name:str,
    directory_name:str,
    module:str='__init__',
    code:str = None,
    schema_name:str = None,
    schema_type:str = None
) -> Callable:

    if module is None:
        module = '__init__'

    if directory_name is None:
        directory_name = os.path.join(
            os.getenv(
                'code_directory',
                os.getcwd()
            ),
            schema_type,
            schema_name
        )
        os.makedirs(
            directory_name,
            exist_ok=True
        )
    
    if code is not None:
        File(
            directory_name,
            os.path.join(directory_name,'{}.py'.format(module))
        ).write(code)
        
    spec = importlib.util.spec_from_file_location(
        module,
        os.path.join(directory_name,'{}.py'.format(module))
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, function_name)

def getModule(
    directory_name:str,
    module:str='__init__',
    package_name:str = None,
    schema_name:str = None,
    schema_type:str = None
) -> types.ModuleType:
    
    original_path = os.getcwd()

    if package_name:
        module = package_name
    else:
        if module is None:
            module = '__init__'

        if directory_name is None:
            directory_name = os.path.join(
                os.getenv(
                    'CODE_DIRECTORY',
                    os.getcwd()
                ),
                schema_type,
                schema_name
            )
            os.makedirs(
                directory_name,
                exist_ok=True
            )

    # os.chdir(directory_name)
    sys.path.append(directory_name)

    module = importlib.import_module(module)

    # spec = importlib.util.spec_from_file_location(
    #     module,
    #     os.path.join(directory_name,'{}.py'.format(module))
    # )
    # module = importlib.util.module_from_spec(spec)
    # spec.loader.exec_module(module)


    sys.path.append(original_path)

    return module

def manageQuery(
    name:str=None,
    query:str=None,
    file_name:str=None,
    directory_name:str=None,
    schema_name:str=None,
    schema_type:str= None,
    data_config_is_active:bool=None
) -> Tuple[str,str,str]:
    
    if query is not None:
        if data_config_is_active:
            if file_name is None and directory_name is None and name is not None:
                file_name = name+'.sql'
                directory_name = os.path.join(
                    os.getenv(
                        'CODE_DIRECTORY',
                        os.getcwd()
                    ),
                    schema_type,
                    schema_name,
                    'queries'
                )
                os.makedirs(
                    directory_name,
                    exist_ok=True
                )
                
                File(
                    directory_name,
                    file_name
                ).write(query)


            # if os.path.isfile(os.path.join(os.path.abspath(directory_name),file_name)):
            #     query = File(
            #         directory_name,
            #         file_name
            #     ).read().content            

            # if directory_name is None:

            #     directory_name = os.getenv(
            #         'CODE_DIRECTORY',
            #         os.getcwd()
            #     )

            #     if schema_name:
            #         new_directory_name = os.path.join(
            #             directory_name,
            #             schema_type,
            #             schema_name,
            #             'queries'
            #         )
            #         if os.path.isdir(new_directory_name):
            #             directory_name = new_directory_name

            # elif not os.path.isdir(directory_name):
            #     new_directory_name = os.path.join(
            #         os.getenv('CODE_DIRECTORY',os.getcwd()),
            #         directory_name
            #     )
            #     if os.path.isdir(new_directory_name):
            #         directory_name = new_directory_name

            # if file_name is None:
            #     pass

            # query = File(
            #     directory_name,
            #     file_name+'.sql' if '.' not in file_name else file_name
            # ).read().content            

    elif file_name is not None:   
        pass

    elif name is not None:
        if directory_name is None:
            directory_name=os.getenv(
                'CODE_DIRECTORY',
                os.getcwd()
            )
            if schema_type:
                directory_name = os.path.join(
                    directory_name,
                    schema_type
                )
            if schema_name:
                directory_name = os.path.join(
                    directory_name,
                    schema_name
                )

        query = File(
            os.path.join(
                directory_name,
                'queries'
            ),
            name+'.sql'
        ).read(encoding = 'utf-8').content            

    return query,file_name,directory_name

from datablender.base.web import Bot,BotAction,WebElement
from datablender.base.connection import Connection, AsyncConnection
from datablender.base.queryBuilder import QueryBuilder
from datablender.base.dataLogging import (
    DataEventsTable,
    DataLogging,
    AsyncDataEventsTable,
    AsyncDataLogging
)
from datablender.base.dataConfiguration import DataConfiguration,AsyncDataConfiguration
from datablender.base.dataElement import DataElement, AsyncDataElement
from datablender.base.data import Data
from datablender.base.dataSets import DataSets
