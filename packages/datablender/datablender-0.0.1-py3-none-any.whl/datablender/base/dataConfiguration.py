"""

"""
from __future__ import annotations

import os
import copy
import shutil
import datetime
import asyncio

from datablender.base.file import File
from datablender.base.request import Request,AsyncRequest
from datablender.base import getNextID
 
class DataConfiguration:
    """Represents the data configuration.

    Allow request in the data configuration. The config can be stored in a json file 
    or in a json server.

    Attributes:
    ----------
        host (str): Host of the data config.
        port (int): Port of the data config.
        directory_name (str): Directory name containing the data config
        active (bool): Indicate if the data config is active.
        storage_type (str): .
        request (DataConfigurationRequest): .
        configuration (dict): .

    Methods:
    ----------
        activate(self) -> None: Activate data configuration.
        getElements(self,element_type='schema',schema_name:str='public') -> list: Get all elements in the data configuration.

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        host:str='localhost',
        port:int=None,
        directory_name:str=None,
        active:bool = True
    ):
        """Initiate the data configuration.

        Args:
            host (str, optional): Host of the data config. Defaults to 'localhost'.
            port (int, optional): Port of the data config. Defaults to None.
            directory_name (str, optional): Directory name containing the data config. Defaults to None.
            active (bool, optional): Indicate if the data config is active. Defaults to True.
        """
        self.host = host
        self.port = port
        self.directory_name = directory_name
        self.active = active

        self.storage_type = None
        self.session = None

        if self.active:
            self.activate()
        
    def activate(self) -> None:
        """Activate data configuration.
        """

        if self.port or os.getenv('DATA_CONFIGURATION_SERVER_PORT'):
            self.storage_type = 'server'

            if os.getenv('ENVIRONNEMENT') == 'developpement':
                self.host = 'localhost'
            else:
                self.host = os.getenv('DATA_CONFIGURATION_SERVER_HOST',self.host)

            self.port = self.port if self.port else os.getenv(
                'DATA_CONFIGURATION_SERVER_PORT'
            )

            self.request = Request(
                host = self.host,
                port = self.port
            )
    
        else:

            self.directory_name = self.directory_name if self.directory_name else os.getenv(
                'CODE_DIRECTORY',
                os.getcwd()
            )

            self.storage_type = 'file'

            self.configuration_file = File(
                self.directory_name,
                'data.config.json',
                content = {
                  "docs": [],
                  "role": [],
                  "extension": [],
                  "schema": [],
                  "table": [],
                  "function": [],
                  "view": [],
                  "data_source": [],
                  "data_process": []
                }
            ).touch().read(encoding='utf-8')

    def getElements(
        self,
        element_type:str,
        **kwargs
    ) -> DataConfiguration:

        if not hasattr(self,element_type) and self.active:

            if self.storage_type=='server':
                self.request.reset()
                self.request.addElement(element_type)
                self.request.get(**kwargs)
    
            setattr(
                self,
                element_type,
                copy.deepcopy(
                    self.configuration_file.content[element_type]
                ) if self.storage_type == 'file' else self.request.response.json()
            )

        return self

    def postElement(
        self,
        configuration:dict,
        element_type:str
    ) -> int:
        
        for attribute in ['size','sizes']:
            configuration.pop(attribute,None)
    
        if self.storage_type=='server':
            self.request.reset()
            self.request.addElement(element_type)
            self.request.post(json = configuration)
            configuration['id'] = self.request.response.json()['id']

        elif self.storage_type == 'file':

            configuration['id'] = getNextID(
                self.configuration_file.content[element_type]
            )

            self.configuration_file.content[element_type].append(
                configuration
            )

            self.configuration_file.write(encoding='utf-8')

        elements:list = getattr(self,element_type,[])
        elements.append(configuration)
        setattr(self,element_type,elements)     

        return configuration['id']   
         
    def deleteElement(
        self,
        element_id:int,
        element_type:str
    ) -> None:
    
        if self.storage_type=='server':
            self.request.reset()   
            self.request.addElement(element_type)
            self.request.addElement(str(element_id))
            self.request.delete()

        elif self.storage_type == 'file':
            [
                element for element
                in self.configuration_file.content[element_type]
                if element['id'] != element_id    
            ]
            
            self.configuration_file.write(
                encoding='utf-8'
            )

        setattr(
            self,
            element_type,
            [
                element for element
                in getattr(self,element_type,[])
                if element['id'] != element_id
            ]
        )  

    def putElement(
        self,
        element_id:int,
        configuration:dict,
        element_type:str
    ) -> None:
    
        if self.storage_type=='server':
            self.request.reset()   
            self.request.addElement(element_type)
            self.request.addElement(str(element_id))
            self.request.put(json=configuration)

        elif self.storage_type == 'file':

            element_index = next(
                (
                    index
                    for (index, element) in enumerate(
                        self.configuration_file.content[element_type]
                    )
                    if element["id"] == element_id
                ),
                None
            )
            self.configuration_file.content[element_type][element_index]=configuration
            self.configuration_file.write(encoding='utf-8')

        elements:list = getattr(self,element_type,[])
        element_index = next(
            (
                index
                for (index, element) in enumerate(elements)
                if element["id"] == element_id
            ),
            None
        )    

        elements[element_index] = configuration

        setattr(self,element_type,elements) 

    def getAllElements(self) -> None:
        
        [
            self.getElements(element) for element
            in [
                'docs',
                'table',
                'schema',
                'role',
                'view',
                'extension',
                'function',
                'data_process',
                'data_source'
            ]
        ]

    def getElement(
        self,
        element_name:str=None,
        element_type:str=None,
        element_id:int=None,
        schema_id:str=None
    ) -> dict:
        
        element = {}

        if self.active and element_type != 'database':

            elements = getattr(
                self.getElements(element_type),
                element_type,
                []
            )

            if element_id:
                element = next(
                    (
                        element for element in elements
                        if element['id']== element_id
                    ),
                    {}
                )

            if not element:
                element = next(
                    (
                        element for element in elements
                        if element['name']== element_name and (
                            not schema_id
                            or element['schema_id'] == schema_id
                        )
                    ),
                    {}
                )
            
        return element

    def deleteAllElements(self) -> None:

        element_types = [
            'docs',
            'table',
            'schema',
            'role',
            'view',
            'extension',
            'function',
            'data_process',
            'data_source'
        ]

        for element_type in element_types:
            [
                self.deleteElement(
                    element['id'],element_type
                )
                for element in getattr(
                    self,element_type,[]
                )
            ]

class AsyncDataConfiguration:
    """Represents the data configuration.

    Allow request in the data configuration. The config can be stored in a json file 
    or in a json server.

    Attributes:
    ----------
        host (str): Host of the data config.
        port (int): Port of the data config.
        directory_name (str): Directory name containing the data config
        active (bool): Indicate if the data config is active.
        storage_type (str): .
        request (DataConfigurationRequest): .
        configuration (dict): .

    Methods:
    ----------
        activate(self) -> None: Activate data configuration.
        getElements(self,element_type='schema',schema_name:str='public') -> list: Get all elements in the data configuration.

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        host:str='localhost',
        port:int=None,
        directory_name:str=None,
        active:bool = True
    ):
        """Initiate the data configuration.

        Args:
            host (str, optional): Host of the data config. Defaults to 'localhost'.
            port (int, optional): Port of the data config. Defaults to None.
            directory_name (str, optional): Directory name containing the data config. Defaults to None.
            active (bool, optional): Indicate if the data config is active. Defaults to True.
        """
        self.host = host
        self.port = port
        self.directory_name = directory_name
        self.active = active

        self.storage_type = None
        
    async def activate(self,loop=None) -> None:
        """Activate data configuration.
        """
        
        if self.active:

            if self.port or os.getenv('DATA_CONFIGURATION_SERVER_PORT'):

                self.storage_type = 'server'
                if os.getenv('ENVIRONNEMENT') == 'developpement':
                    self.host = 'localhost'

                else:
                    self.host = os.getenv('DATA_CONFIGURATION_SERVER_HOST',self.host)

                self.port = self.port if self.port else os.getenv(
                    'DATA_CONFIGURATION_SERVER_PORT'
                )
                
                if not hasattr(self,'request'):

                    self.request = AsyncRequest(
                        host = self.host,
                        port = self.port,
                        loop=loop
                    )
                
                if self.request.session is None:
                    await self.request.setSession()

            else:
                self.directory_name = self.directory_name if self.directory_name else os.getenv(
                    'CODE_DIRECTORY',
                    os.getcwd()
                )
                self.storage_type = 'file'
                self.configuration_file = File(
                    self.directory_name,
                    'data.config.json',
                    content = {
                  "docs": [],
                  "role": [],
                  "extension": [],
                  "schema": [],
                  "table": [],
                  "function": [],
                  "view": [],
                  "data_source": [],
                  "data_process": []
                }
                ).touch().read(encoding='utf-8')

    async def getElements(
        self,
        element_type:str,
        **kwargs
    ) -> DataConfiguration:

        if not hasattr(self,element_type) and self.active:

            if self.storage_type=='server':
                self.request.reset()
                self.request.addElement(element_type)

                async with self.request.session.get(
                    self.request.url,
                    **kwargs
                ) as response:
                    assert response.status == 200
                    elements = await response.json()
                
            setattr(
                self,
                element_type,
                copy.deepcopy(
                    self.configuration_file.content[element_type]
                ) if self.storage_type == 'file' else elements
            )

        return self

    async def postElement(
        self,
        configuration:dict,
        element_type:str
    ) -> int:
        
        for attribute in ['size','sizes']:
            configuration.pop(attribute,None)
    
        if self.storage_type=='server':

            self.request.reset()
            self.request.addElement(element_type)

            async with self.request.session.post(
                self.request.url,
                json = configuration
            ) as response:
                
                assert response.status == 201
                element = await response.json()
                configuration['id'] = element['id']

        elif self.storage_type == 'file':

            configuration['id'] = getNextID(
                self.configuration_file.content[element_type]
            )

            self.configuration_file.content[element_type].append(
                configuration
            )

            self.configuration_file.write(encoding='utf-8')

        elements:list = getattr(self,element_type,[])
        elements.append(configuration)
        setattr(self,element_type,elements)     

        return configuration['id']   
         
    async def deleteElement(
        self,
        element_id:int,
        element_type:str,
        **kwargs
    ) -> None:
    
        if self.storage_type=='server':
            self.request.reset()   
            self.request.addElement(element_type)
            self.request.addElement(str(element_id))

            async with self.request.session.delete(
                self.request.url,
                **kwargs
            ) as response:
                assert response.status == 200
                await asyncio.sleep(0.001)

        elif self.storage_type == 'file':
            [
                element for element
                in self.configuration_file.content[element_type]
                if element['id'] != element_id    
            ]
            
            self.configuration_file.write(
                encoding='utf-8'
            )

        setattr(
            self,
            element_type,
            [
                element for element
                in getattr(self,element_type,[])
                if element['id'] != element_id
            ]
        )   

    async def putElement(
        self,
        element_id:int,
        configuration:dict,
        element_type:str,
        **kwargs
    ) -> None:
    
        if self.storage_type=='server':
            self.request.reset()   
            self.request.addElement(element_type)
            self.request.addElement(str(element_id))

            async with self.request.session.put(
                self.request.url,
                json=configuration
            ) as response:
                assert response.status == 200
                await asyncio.sleep(0.001)

        elif self.storage_type == 'file':

            element_index = next(
                (
                    index
                    for (index, element) in enumerate(
                        self.configuration_file.content[element_type]
                    )
                    if element["id"] == element_id
                ),
                None
            )

            self.configuration_file.content[element_type][element_index]=configuration
            self.configuration_file.write(encoding='utf-8')

        elements:list = getattr(self,element_type,[])

        elements[
            next(
                (
                    index
                    for (index, element) in enumerate(elements)
                    if element["id"] == element_id
                ),
                None
            )
        ] = configuration

        setattr(self,element_type,elements) 

    async def getAllElements(self) -> None:

        element_types = [
            'docs',
            'table',
            'schema',
            'role',
            'view',
            'extension',
            'function',
            'data_process',
            'data_source'
        ]

        for element_type in element_types:
            await self.getElements(element_type)

    def getElement(
        self,
        element_name:str=None,
        element_type:str=None,
        element_id:int=None,
        schema_id:str=None
    ) -> dict:
        
        element = {}

        if self.active and element_type != 'database':

            elements = getattr(
                self,
                element_type,
                []
            )

            if element_id:
                element = next(
                    (
                        element for element in elements
                        if element['id']== element_id
                    ),
                    {}
                )

            if not element:
                element = next(
                    (
                        element for element in elements
                        if element['name']== element_name and (
                            not schema_id
                            or element['schema_id'] == schema_id
                        )
                    ),
                    {}
                )
            
        return element

    async def deleteAllElements(self) -> None:

        element_types = [
            'docs',
            'table',
            'schema',
            'role',
            'view',
            'extension',
            'function',
            'data_process',
            'data_source'
        ]

        for element_type in element_types:
            
            for element in getattr(
                self,element_type,[]
            ):                    
            
                await self.deleteElement(
                    element['id'],
                    element_type
                )
            
    def backupConfig(self) -> None:

        timestamp = datetime.datetime.now().strftime("%Y_%m_%d_%H%M%S")
    
        code_directory = os.getenv('CODE_DIRECTORY')

        os.mkdir(os.path.join(
            code_directory,
            'backup',
            timestamp
        ))

        for to_copy in ['data.config.json','source','process']:
            path = os.path.join(
                code_directory,
                to_copy
            )
            if os.path.isdir(path) or os.path.isfile(path):

                shutil.copy(
                    path,
                    os.path.join(
                        code_directory,
                        'backup',
                        timestamp,
                        to_copy
                    )
                )
                if to_copy in ['source','process']:
                    os.unlink(path)

