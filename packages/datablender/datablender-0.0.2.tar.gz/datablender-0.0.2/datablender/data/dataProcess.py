"""
"""
from __future__ import annotations
from typing import Dict, Union, List, Callable, Tuple

import os
import copy
import pandas

from datablender.base import (
    getFunction,
    DataConfiguration,
    Connection,
    Data,
    DataElement
)
from datablender.database import Database
from datablender.data.dataVersion import DataVersion

class DataProcess(DataElement):
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
        connection:Connection,
        name:str,
        database:Database= None,
        data_configuration:DataConfiguration=None,
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
        database_name:str = None
    ):
        super(DataProcess,self).__init__(
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

        self.actions = actions
        self.schema_id = schema_id
        self.schema_name = schema_name
        
        self.directory_name = None
        self.setDirectory(directory_name)
        self.setDataDirectory(data_directory_name)

        self.version = None
        self.data_version_config = data_version
        self.setDataVersion(data_version)

        self.functions:Dict[str,Callable] = {}
        self.data:Dict[str,Data] = {}

        self.database = database if database else Database(
            self.connection,
            name = database_name if database_name else self.connection.database_name,
            data_configuration=self.data_configuration,
            event_server=self.data_logging.event_server
        ).manage()

        self.manageAttributes()

        self.data_logging.setElement(
            'process',
            self.name,
            self.id
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
            #'versions':self.versions,
            'actions':self.actions,
            'content':self.content,
            'data_version':self.data_version.configuration,
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
            
            self.manageAttributes()

            if 'data_version' in new_config:
                self.setDataVersion(new_config.get('data_version'))

        return new_config
  
    def setDirectory(self,directory_name:str) -> None:
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
            if os.path.isdir(os.path.join(base_name,'processes')):
                base_name = os.path.join(base_name,'processes')
                if os.path.isdir(os.path.join(base_name,self.name)):
                    self.directory_name = os.path.join(base_name,self.name)
            else:
                self.directory_name = base_name

    def setDataDirectory(self,directory_name:str) -> None:
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

    def setDataVersion(self,data_version:dict):
        self.data_version = DataVersion(
            self.connection,
            None,
            self.data_configuration,
            active=True if data_version else False,
            **data_version
        )
        
    def manage(
        self,
        manage_from='configuration',
        new_configuration:dict={}
    ) -> DataProcess:
        """Manage the data process configuration in the data configuration.

        Args:
            manage_from (str, optional): Manage the data process from. Defaults to 'configuration'.
            new_configuration (dict, optional): New configuration to manage the data process. Defaults to {}.

        Returns:
            DataSource: self.
        """
        # If there is a new configuration, set all data process attributes from the new config
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
                        'data_process'
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
                        'data_process'
                    )
            
            # If it does not exists, then post the new config if there is one
            elif new_configuration and self.status !='inexistant':
                setattr(
                    self,
                    'id',
                    self.data_configuration.postElement(
                        self.configuration,
                        'data_process'
                    )
                )

            # If it does not exists and there is no new config, but the name or id,
            # post it with the values of this object
            elif self.name or self.id:
                self.setDataVersion(self.data_version_config)
                setattr(
                    self,
                    'id',
                    self.data_configuration.postElement(
                        self.configuration,
                        'data_process'
                    )
                )

                
            # If data config is active, but there is no directory name or data source name
            else:
                self.name = 'data'
                self.setDataVersion(
                    self.data_version_config
                )
                setattr(
                    self,
                    'id',
                    self.data_configuration.postElement(
                        self.configuration,
                        'data_process'
                    )
                )

        # If data config is not active and there is not a new configuration,
        elif not new_configuration and manage_from != 'values':
            self.name = 'data' if not self.name else self.name
            self.setDataVersion(
                self.data_version_config
            )

        # if self.status =='inexistant':
        #     self.deleteAllData()
        
        return self

    def process(self,version:dict=None) -> None:
        
        if version:
            self.version = version
            self.executeActions()
        elif self.data_version.active:
            for version in self.data_version.getNonProccesedVersions():
                self.version = version
                print(self.version)
                self.executeActions()
                self.data_version.checkProccessedVersion(self.version)
        else:
            self.executeActions()

    def executeActions(self) -> None:
        for action in self.actions:
            print(action.get('name'))
            action = copy.deepcopy(action)
            getattr(self,action.pop('name'))(**action)

    def getFunction(
        self,
        function_name:str,
        module:str='__init__'
    ) -> None:
        directory_name =self.directory_name if self.directory_name else os.path.join(
            os.getcwd(),
            'processes',
            self.name
        )
        self.functions[function_name] = getFunction(
            function_name,
            directory_name,
            module
        )

    def applyFunction(
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
                self.executeAction(data_name,'setData',data=data[data_name])
                for data_name in data
            ]

    def select(
        self,
        elements:Union[str,List[str],List[Dict[str,any]]]
    ) -> None:
        for element in elements:
            self.executeAction(
                element,
                'select',
                where_statement=self.getVersion(element)
            )
        
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

    def transform(
        self,
        transformations:List[dict],
        element:Union[str,Dict[str,str]]
    ) -> None:
        self.executeAction(
            element,
            'transform',
            transformations=transformations
        )
    
    def load(self,elements:List[Dict[str,str]]) -> None:
        for element in elements:
            self.executeAction(element,'copy')

    def merge(
        self,
        element_left:Union[Dict[str,str],str],
        element_right:Union[Dict[str,str],str],
        element:Union[Dict[str,str],str]=None,
        **kwargs
    ) -> None:   
        self.executeAction(
            element if element else element_left,
            'setData',
            data = pandas.merge(
                self.executeAction(element_left,'getData').frame,
                self.executeAction(element_right,'getData').frame,
                **kwargs
            )
        )
  
    def copy(
        self,
        element_from:Union[Dict[str,str],str],
        element_to:Dict[str,str]
    ) -> None:
        
        data = self.executeAction(
            element_from,
            'getData'
        )
        self.executeAction(
            element_to,
            'setData',
            data = data
        )
            
    def update(
        self,
        element:Union[Dict[str,str],str],
        id_columns,
        update_columns
    ) -> None:
        self.executeAction(
            element,
            'updateWithData',
            update_values=update_columns,
            columns=update_columns,
            where_statement={id_column:id_column for id_column in id_columns}
        )

    def write(
        self,
        element:str,
        directory_name:str,
        extension:str=None,
        file_name:str=None
    ) -> None:

        self.executeAction(
            element,
            'write',
            extension=extension,
            directory_name=directory_name,
            file_name=file_name
        )

    def read(
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
            
        self.executeAction(
            element,
            'read',
            extension=extension,
            directory_name=directory_name,
            file_name=file_name,
            **kwargs
        )

    def delete(
        self,
        element:Union[str,List[str],List[Dict[str,any]]],
        version:list=[]
    ) -> None:
        self.executeAction(
            element,
            'delete',
            where_statement = {
                v:self.version[v] for v in version
            }
        )

    def addVersion(
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

    def refresh(
        self,
        elements:Union[str,List[str],List[Dict[str,any]]]
    ) -> None:
        
        for element in elements:
            if 'element_type' not in element:
                element['element_type'] = 'view'
            if 'schema_name' not in element:
                element['schema_name'] = self.name

            element['directory_query'] = os.path.join(
                self.directory_name,
                'queries'
            )
            element['is_materialized'] = True

            self.executeAction(
                element,
                'refresh'
            )

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

    def concat(
        self,
        element_1:Union[str,List[str],List[Dict[str,any]]],
        element_2:Union[str,List[str],List[Dict[str,any]]],
        element:Union[str,List[str],List[Dict[str,any]]],
        **kwargs
    ):
        self.executeAction(
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
        
    def executeAction(
        self,
        element:Union[str,dict],
        action_name:str,
        **kwargs
    ) -> Union[Data,None]:
        is_database,element = self.checkElement(element)
        if is_database:
            return self.database.executeDataAction(
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
                    connection = self.connection
                )
            )
            return getattr(
                self.data[element.get('name')],
                action_name
            )(**kwargs)
