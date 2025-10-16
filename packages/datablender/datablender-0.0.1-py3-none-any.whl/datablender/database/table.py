"""
This module contain the table class, which represent a single table in a database.
"""
from __future__ import annotations
from typing import Union,List, Dict

from io import StringIO,BytesIO
import re
import copy
import json
import pandas

from datablender.base import (
    Connection,
    DataConfiguration,
    Data,
    AsyncConnection,
    AsyncDataConfiguration
)
from datablender.database.elementSQL import SchemaElement,AsyncSchemaElement, mode_level
from datablender.database.view import AsyncView
from datablender.database.view import View

class Table(SchemaElement):
    """Represent a table in the database.

    This class let you create, drop, rename, change the owner of the table. The data in the table can also be selected, inserted, updated or delete.

    When you initiate the table, it is automatically created or droped depending on the status. To be created, the columns must be available.

    Attributes:
    ----------
        name (str): Table name.

    Methods:
    ----------
        manage(self) -> None: Manage table.

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        connection:Connection,
        name:str=None,
        schema_name:str = 'public',
        owner:str = 'postgres',
        status:str = 'default',
        data_configuration:DataConfiguration = None,
        acticvate_data_config:bool = False,
        id:int = None,
        columns:List[dict] = [],
        constraints:List[dict] = [],
        indexes:List[dict] = [],
        data:Data = None,
        content:dict = None,
        grants:List[dict] = [],
        size:int = 0,
        event_server = None,
        schema_id:int = None,
        owner_id:int = None,
        partitions:Dict[str,Union[str,List[dict]]] = {}
    ):
        super(Table,self).__init__(
            connection,
            name,
            schema_name,
            'table',
            owner,
            status,
            data_configuration,
            acticvate_data_config,
            id,
            content,
            event_server,
            schema_id,
            owner_id
        )
        
        self.columns=columns
        self.constraints=constraints
        self.indexes=indexes
        self.grants = grants
        self.data=data
        self.size = size
        self.partitions = partitions

        self.data_conditions:Union[
            Dict[str,dict],
            Dict[str,List[dict]]
        ] = {}

        if self.db_element:
            self.db_element = {
                **self.db_element,
                'partitions':self.getPartition(
                    self.query_builder.selectElements(
                        'partition'
                    ).execute().to_dict('records'),
                    self.name
                )
            }

    def getPartition(
        self,
        db_partitions:List[dict],
        name:str
    ) -> None:
            
        partition = next((
            element for element
            in db_partitions
            if (
                element.get(
                    'schema_name'
                ) == self.schema_name
                and element.get(
                    'table_name'
                ) == name
            )
        ),{})

        if partition:

            return {
                'method':partition.get('method',None),
                'column_names':partition.get('column_names',None),
                'partitions':[
                    {
                        **partition,
                        **self.getPartition(
                            db_partitions,
                            partition['name']
                        )
                    } for partition in partition.get('partitions',[])
                ]
            }

        return {}

    def manage(
        self,
        manage_from:str='database',
        new_configuration:dict={},
        data:Data=None
    ) -> Table:
        """Manage the table in the database.

        When a element is managed, attributes can come from 3 config:
            * Database
            * Data configuration
            * Values

        If a new configuration is provided or it is manage from the configuration,
        the values are replaced with the new configuration.

        Then they are a few possibilities: 
            The data configuration is not activated. 

        If the element is not manage from the database, attributes are compared 

        Returns:
            Table: self.
        """

        # Get the good status
        self.setManager(
            manage_from,
            new_configuration
        )

        self.setData(data)
        
        # If the element does not exists in the database
        # and the status is not inactive or inexistant, 
        # create the table. 
        if not self.db_element and self.should_exists:

            if not self.columns and self.data is not None:
                self.setColumns()

            self.manageInConfig()
            
            if self.columns:
                self.create()
                self.manageAttributes('database')

        elif self.db_element and self.should_exists:

            if data is not None:
                self.setColumns()
                self.manageAttributes('database')

            else:
                self.manageAttributes(
                    'values'
                    if self.manage_from == 'database'
                    else 'database'
                )
            
            self.manageInConfig()

        # If the element exists and the status is inactive or inexistant,
        # drop the table. 
        elif self.db_element and not self.should_exists:
            self.drop()
            self.manageInConfig()
        
        elif not self.db_element and not self.should_exists:
            self.manageInConfig()

        return self
        
    def create(self) -> None:
        """Create the table in the database.
        """
        
        self.data_logging.logEvent(
            'create',
            'loading'
        )

        self.query_builder.create(
            self.name,
            schema_name=self.schema_name
        ).columns(
            self.columns
        ).constraints(
            self.constraints
        ).partition(
            **self.partitions
        ).built().execute()

        self.getDBElement()
        partitions = copy.deepcopy(self.partitions)
        self.db_element = {
            **self.db_element,
            'partitions':{
                'method':partitions.get('method'),
                'column_names':partitions.get('column_names'),
                'partitions':[]
            } if partitions else {}
        }
        
        self.data_logging.logEvent(
            'create',
            'loaded'
        )
   
    def manageGrants(self) :
        """Grant privileges on schema.
        """
        
        self.data_logging.logEvent(
            'grant',
            'loading'
        )

        db_grants:List[dict] = copy.deepcopy(
            self.db_element.get('grants')
        )

        for grant in self.grants:
            if grant in db_grants:
                db_grants.remove(grant)
            else:
                self.query_builder.grant(
                    self.name,
                    self.element_type,
                    self.schema_name,
                    **grant
                ).built().execute()

        for revoke in db_grants:
            self.query_builder.revoke(
                self.name,
                self.element_type,
                self.schema_name,
                **revoke   
            ).built().execute()

        if self.grants:
            self.db_element['grants'] = copy.deepcopy(self.grants)
        
        self.data_logging.logEvent(
            'grant',
            'loaded'
        )
   
    def manageColumns(self) -> None:
        """Get table columns from existing table or from data.
        """
        
        self.data_logging.logEvent(
            'columns',
            'loading'
        )
        
        db_columns:List[dict] = copy.deepcopy(
            self.db_element.get('columns',[])
        )

        for index,column in enumerate(self.columns):
            db_column_index = next((
                i for i,c in enumerate(db_columns)
                if c.get('name')==column.get('name')
            ),None)

            if db_column_index is not None:
                db_column = db_columns[db_column_index]
                db_columns.remove(db_column)
                self.columns[index] = copy.deepcopy(db_column)

                if db_column.get('type') != column.get('type'):
                    

                    self.query_builder.alter(
                        self.name,
                        schema_name=self.schema_name
                    ).alter(
                        column.get('name'),
                        'column'
                    ).columnType(
                        column.get('type')
                    ).built().execute()

            else:

                self.query_builder.alter(
                    self.name,
                    schema_name=self.schema_name
                ).add(
                    'column',
                    column
                ).built().execute()
            
        for column in db_columns:
            self.query_builder.alter(
                self.name,
                schema_name=self.schema_name
            ).drop(
                column.get('name'),
                'column'
            ).built().execute()

        if self.columns:
            self.db_element['columns'] = copy.deepcopy(self.columns)
        
        self.data_logging.logEvent(
            'columns',
            'loaded'
        )

    def manageConstraints(self) -> None:
                
        self.data_logging.logEvent(
            'constraints',
            'loading'
        )
 
        db_constraints:List[dict] = copy.deepcopy(
            self.db_element.get('constraints')
        )

        for constraint in self.constraints:
            if constraint in db_constraints:
                db_constraints.remove(constraint)
            else:
                self.query_builder.alter(
                    self.name,
                    schema_name=self.schema_name
                ).add(
                    'constraint',
                    constraint
                ).built().execute()
            
        for constraint in db_constraints:
            self.query_builder.alter(
                self.name,
                schema_name=self.schema_name
            ).drop(
                constraint.get('name'),
                'constraint'
            ).built().execute()
        
        if self.constraints:
            self.db_element['constraints'] = copy.deepcopy(self.constraints)
        
        self.data_logging.logEvent(
            'constraints',
            'loaded'
        )
    
    def manageIndexes(self) -> None:
        """Create indexes.
        """

        self.data_logging.logEvent(
            'index',
            'loading'
        )  

        db_indexes:List[dict] = copy.deepcopy(
            self.db_element.get('indexes')
        )

        for index in self.indexes:
            if (
                index not in db_indexes 
                and not index.get('constraint_type')
            ):
 
                self.query_builder.create(
                    index.get('name'),
                    'index'
                ).uniqueIndex(
                    index.get('is_unique')
                ).onIndex(
                    index.get('name'),
                    index.get('schema_name')
                ).usingIndex(
                    index.get('method'),
                    index.get('columns')
                ).built().execute()
            
            else:
                db_indexes.remove(index)

        for index in db_indexes:
            if not index.get('constraint_type'):
                self.query_builder.drop(
                    index.get('name'),
                    'index',
                    exists_condition=True
                ).built().execute()

        if self.indexes:
            self.db_element['indexes'] = copy.deepcopy(self.indexes)

        self.data_logging.logEvent(
            'index',
            'loaded'
        )
    
    def managePartition(self) -> None:

        self.data_logging.logEvent(
            'partition',
            'loading'
        )    

        # {
        #     'method':'list',
        #     'column_names':['data_source_id'],
        #     'partitions': [
        #         {
        #             'name':'links_adresses_quebec',
        #             'expression':'for values in (3)',
        #             'method':'list',
        #             'column_names':['version_id'],
        #             'partitions':[
        #                 {
        #                     'name':'links_adresses_quebec_aq202404',
        #                     'expression':'for values in (AQ202404)',
        #                 }
        #             ]
        #         }
        #     ]
        # }
        self.managePartitions(
            copy.deepcopy(self.partitions.get('partitions')),
            copy.deepcopy(self.db_element.get('partitions',{}).get('partitions',[])),
            self.name
        )

        if self.partitions:
            self.db_element['partitions'] = copy.deepcopy(self.partitions)
        
        self.data_logging.logEvent(
            'partition',
            'loaded'
        )

    def managePartitions(
        self,
        partitions:List[Dict[str,Union[str,dict]]],
        db_partitions:List[Dict[str,Union[str,dict]]],
        parent_table_name:str
    ) -> None:
        for partition in partitions:
            if partition in db_partitions:
                db_partitions.remove(partition)
            else:
                name = partition.pop('name')

                self.query_builder.create(
                    name,
                    schema_name=self.schema_name
                ).partition(
                    **partition,
                    table_name = parent_table_name
                ).built().execute()

                self.managePartitions(
                    copy.deepcopy(partition.get('partitions',[])),
                    copy.deepcopy(next((
                        db_partition for db_partition in db_partitions
                        if db_partition.get('name')== partition.get('name')
                    ),{}).get('partitions',[])),
                    name
                )
        
        for drop in db_partitions:
            self.query_builder.drop(
                drop.get('name'),
                'table',
                self.schema_name,
                True
            ).built().execute()

    def select(
        self,
        where_statement:list=None,
        columns:list=None,
        limit:int=None,
        **kwargs
    ) -> Table:
        """Select data.

        Args:
            where_statement (list, optional): Where conditions. Defaults to None.
            columns (list, optional): Columns to select. Defaults to None.
        """
        
        self.data_logging.logEvent(
            'select',
            'loading'
        )
        
        if self.db_element:
            self.data = Data(
                self.query_builder.select(
                    self.name,
                    schema_name=self.schema_name,
                    limit = limit
                ).columns(
                    columns if columns else self.columns
                ).where(
                    where_statement
                ).built().execute(**kwargs),
                meta_columns=[],
                columns = self.columns
            )

        self.data_logging.logEvent(
            'select',
            'loaded'
        )
        
        return self

    def update(
        self,
        update_values:Union[dict,list],
        from_table:str=None,
        where_statement:list=None,
        columns:list=None,
        from_table_schema:str=None,
        **kwargs
    ) -> None:
        """Update table.

        Args:
            update_values (Union[dict,list]): Values to update with.
            from_table (str, optional): Table from. Defaults to None.
            where_statement (list, optional): Where statement. Defaults to None.
            columns (list, optional): Columns. Defaults to None.
        """
        
        self.data_logging.logEvent(
            'update',
            'loading'
        )

        if isinstance(update_values, dict):
            columns = update_values.keys()
            values = update_values.values()
        elif self.columns and isinstance(update_values, list):
            columns = columns
            values = update_values

        self.query_builder.update(
            self.name,
            self.schema_name
        ).fromTable(
            from_table,
            from_table_schema if from_table_schema else self.schema_name
        ).columns(
            columns
        ).values(
            values
        ).where(
            where_statement
        ).built().execute(**kwargs)

        self.data_logging.logEvent(
            'update',
            'loaded'
        )

    def insert(
        self,
        insert_values:Union[dict, list],
        return_values:list=None,
        **kwargs
    ) -> list:
        """Insert data in table.

        Args:
            insert_values (Union[dict, list]): Values to insert, store in a dictonnary which the keys are the columns,
            or store in list if it's only the values name.
            return_value (str): Values name to return.

        Returns:    
            list: return values.
        """
             
        self.data_logging.logEvent(
            'insert',
            'loading'
        )

        if isinstance(insert_values, dict):
            insert_values = {key:insert_values[key] for key in insert_values if insert_values[key] is not None}
            columns = insert_values.keys()
            values = insert_values.values()
        elif self.columns and isinstance(insert_values, list):
            columns = self.columns
            values = insert_values

        results = self.query_builder.insert(
            self.name,
            schema_name=self.schema_name
        ).columns(
            columns
        ).values(
            values
        ).returnValues(
            return_values
        ).built().execute(**kwargs)
        
        self.data_logging.logEvent(
            'insert',
            'loaded'
        )

        return results

    def delete(
        self,
        where_statement:list=None,
        **kwargs
    ) -> None:
        """Delete data in table.

        Args:
            where_statement (list, optional): Where statement to identify deleted data. Defaults to None.
        """
        
        self.data_logging.logEvent(
            'delete',
            'loading'
        )

        self.query_builder.delete(
            self.name,
            schema_name=self.schema_name
        ).where(
            where_statement
        ).built().execute(**kwargs)

        self.data_logging.logEvent(
            'delete',
            'loaded'
        )

    def copy(
        self,
        data:Union[Data,pandas.DataFrame]=None,
        null_value:str = '',
        separator:str='|'
    ) -> None:
        """Copy data in table via a csv file.

        Args:
            data (pandas.DataFrame, optional): Data to copy. Defaults to None.
            null_value (str, optional): Null value in the data. Defaults to ''.
            separator (str, optional): Separator to put data in the csv file. Defaults to '|'.
        """
                
        self.data_logging.logEvent(
            'copy',
            'loading'
        )

        self.setData(data)
        saved_data = StringIO()

        self.data.export('postgres').to_csv(
            saved_data,
            header=False,
            index=False,
            sep=separator
        )
        
        saved_data.seek(0)
        self.connection.setSchema(self.schema_name)

        self.connection.cursor.copy_from(
            saved_data,
            self.name,
            columns=self.data.frame.columns,
            sep = separator,
            null=null_value
        )

        self.connection.connection.commit()
        self.connection.setSchema()
                
        self.data_logging.logEvent(
            'copy',
            'loaded'
        )

    def updateWithData(
        self,
        data:pandas.DataFrame=None,
        update_values:list=None,
        columns:list=None,
        where_statement=None
    ) -> None:
        self.setData(data)
        temporary_table = Table(
            self.connection,
            "temporary_"+self.name,
            self.schema_name,
            data=self.data
        )
        temporary_table.drop(exists_condition=True)
        temporary_table.manage()
        temporary_table.copy()

        self.update(
            update_values,
            temporary_table.name,
            where_statement,
            columns
        )
        # self.insert(temporary_table.name)
        # self.delete(temporary_table.name)

        temporary_table.drop()
                   
    def transform(
        self,
        transformations:List[dict]
    ) -> None:
        self.data.transform(transformations)

    def setData(
        self,
        data:Union[Data,pandas.DataFrame,None]
    ) -> Table:
        
        if data is not None:
            
            if isinstance(data,Data):
                self.data = data
            elif isinstance(data,pandas.DataFrame):
                if hasattr(self,'data') and isinstance(self.data,Data):
                    self.data.frame = data
                else:
                    self.data = Data(data)
        
        return self
    
    def getData(self) -> Data:
        return copy.deepcopy(self.data)

    def executeDataAction(
        self,
        action_name:str,
        **kwargs
    ) -> Union[None,Data]:
        return getattr(self,action_name)(**kwargs)
    
    def setDataConditions(
        self,
        data_source_name:str,
        data_conditions:Union[dict,List[dict]]
    ) -> Table:
        """Set data conditions for a data source.

        Args:
            data_source_name (str): Name of the data source.
            data_conditions (Union[dict,List[dict]]): Conditions to respect.

        Returns:
            Table: self.
        """
        
        self.data_conditions[data_source_name] = data_conditions
        
        return self

    def partitionDataSource(
        self,
        data_source_id:int,
        data_source_name:str,
        data_version_config:Dict[str,dict]
    ) -> None:
        
        partitions = copy.deepcopy(self.partitions['partitions'])

        partition_name = '{}_{}'.format(self.name,data_source_name)

        partition_index = next((
            i for i,p in enumerate(partitions)
            if p.get('name') == partition_name
        ),None)

        if partition_index is None:
        
            self.partitions['partitions'].append({
                'name':partition_name,
                'expression' :"for values in ('{}')".format(data_source_id)
            })
        
    def setColumns(self) -> None:

        if self.data is not None:
            for column in self.data.columns:
                column_index = next((
                    i for i,c in enumerate(self.columns)
                    if c.get('name') == column.get('name')
                ),None)

                if column_index is None:
                    self.columns.append({
                        'name':column.get('name'),
                        'type':column.get('type')
                    })
                
                else:
                    table_column = copy.deepcopy(self.columns[column_index])
                    if column.get('type') !=table_column.get('type'):
                        self.columns[column_index] = {
                            **table_column,
                            'type':copy.deepcopy(column.get('type'))
                        }

class AsyncTable(AsyncSchemaElement):
    """Represent a table in the database.

    This class let you create, drop, rename, change the owner of the table. The data in the table can also be selected, inserted, updated or delete.

    When you initiate the table, it is automatically created or droped depending on the status. To be created, the columns must be available.

    Attributes:
    ----------
        name (str): Table name.

    Methods:
    ----------
        manage(self) -> None: Manage table.

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        connection:AsyncConnection,
        name:str=None,
        schema_name:str = 'public',
        owner:str = None,
        status:str = 'default',
        data_configuration:AsyncDataConfiguration = None,
        acticvate_data_config:bool = False,
        id:int = None,
        columns:List[dict] = [],
        constraints:List[dict] = [],
        indexes:List[dict] = [],
        data:Data = None,
        content:dict = None,
        grants:List[dict] = None,
        size:int = 0,
        event_server = None,
        schema_id:int = None,
        schema_type:int = 'source',
        owner_id:int = None,
        partitions:Dict[str,Union[str,List[dict]]] = {}
    ):
        super(AsyncTable,self).__init__(
            connection,
            name,
            schema_name,
            'table',
            owner,
            status,
            data_configuration,
            acticvate_data_config,
            id,
            content,
            event_server,
            schema_id,
            owner_id,
            schema_type=schema_type
        )

        self.columns=copy.deepcopy(columns)
        self.constraints=copy.deepcopy(constraints)
        self.indexes=copy.deepcopy(indexes)
        self.grants = copy.deepcopy(grants)
        self.data=data
        self.size = size
        self.partitions = partitions

        self.use_cache = False

        self.data_conditions:Union[
            Dict[str,dict],
            Dict[str,List[dict]]
        ] = {}

    async def initiate(self) -> AsyncTable:
        await self.data_logging.manageTable()
        await self.manageAttributes()
        self.data_logging.updateConfiguration(
            self.configuration,
            self.element_type
        )
        await self.getDBElement()

        if self.db_element:
            partitions = await self.query_builder.selectElements(
                'partition'
            ).asyncExecute()

            self.db_element = {
                **self.db_element,
                'partitions':self.getPartition(
                    partitions.to_dict('records'),
                    self.name
                )
            }

        return self
    
    def getPartition(
        self,
        db_partitions:List[dict],
        name:str
    ) -> None:
            
        partition = next((
            element for element
            in db_partitions
            if (
                element.get(
                    'schema_name'
                ) == self.schema_name
                and element.get(
                    'table_name'
                ) == name
            )
        ),{})

        if partition:

            return {
                'method':partition.get('method',None),
                'column_names':partition.get('column_names',None),
                'partitions':[
                    {
                        **partition,
                        **self.getPartition(
                            db_partitions,
                            partition['name']
                        )
                    } for partition in partition.get('partitions',[])
                ]
            }

        return {}

    async def manage(
        self,
        manage_from:str='database',
        new_configuration:dict={},
        data:Data=None,
        data_logging_action:dict={},
        ignore_new_config = False,
        data_source_id:int = None,
        reset_data_source:bool = False,
        element_from:SchemaElement = None,
        where_statement:dict = {},
        use_query:bool = False,
        **kwargs
    ) -> AsyncTable:
        """Manage the table in the database.

        When a element is managed, attributes can come from 3 config:
            * Database
            * Data configuration
            * Values

        If a new configuration is provided or it is manage from the configuration,
        the values are replaced with the new configuration.

        Then they are a few possibilities: 
            The data configuration is not activated. 

        If the element is not manage from the database, attributes are compared 


        Args:
            manage_from (str, optional): Manage the table from. Defaults to 'database'.
            new_configuration (dict, optional): New configuration. Defaults to {}.
            data (Data, optional): New data to load in the table. Defaults to None.
            data_logging_action (dict, optional): Upper action. Defaults to {}.
            ignore_new_config (bool, optional): Ignore new config arg. Defaults to False.
            data_source_id (int, optional): Data source id of the data to be loaded in table. Defaults to None.
            reset_data_source (bool, optional): Inidcate if data source will be reset. Defaults to False.
            element_from (SchemaElement, optional): . Defaults to None.
            columns_names (list, optional): . Defaults to [].

        Returns:
            AsyncTable: self
        """
            
        # Get the good status
        await self.setManageParameters(
            manage_from,
            new_configuration,
            data_logging_action,
            ignore_new_config
        )

        await self.setData(data)

        # If the element does not exists in the database
        # and the status is not inactive or inexistant, 
        # create the table.
        
        if not self.db_element and self.should_exists:

            self.use_cache = True
            
            if (not self.columns and self.data is not None) or element_from is not None:
                self.setColumns(
                    data_source_id,
                    reset_data_source,
                    element_from
                )
                self.setConstraints(reset_data_source)

            await self.manageInConfig()

            self.data_logging.updateConfiguration(
                self.configuration,
                self.element_type
            )

            if (self.columns and all(['type' in c.keys() for c in self.columns])) or use_query:
                
                await self.create(
                    element_from,
                    where_statement,
                    use_query
                )
                await self.manageAttributes('database')
        
        else:
            
            self.setColumns(data_source_id,reset_data_source)
            self.setConstraints(reset_data_source)
            self.setIndexes()

            if self.db_element and self.should_exists:
                await self.manageAttributes(
                    'database' if data is not None else 'values' if self.manage_from == 'database' else 'database'
                )
            
            elif self.db_element and not self.should_exists:
                await self.drop()

            await self.manageInConfig()

        return self
        
    async def create(
        self,
        element_from:SchemaElement = None,
        where_statement:dict = {},
        use_query:bool = False
    ) -> None:
        """Create the table in the database.
        """
        
        await self.data_logging.logEvent(
            'create',
            'loading'
        )
        
        if element_from:

            await self.query_builder.create(
                self.name,
                schema_name=self.schema_name
            ).select(
                name = element_from.name,
                schema_name=element_from.schema_name
            ).columns(
                self.columns
            ).where(
                where_statement
            ).built().asyncExecute(
                 data_logging=self.data_logging
            )

        elif use_query:
            await self.query_builder.create(
                self.name,
                schema_name=self.schema_name
            ).sqlStatement(
                file_name = self.name,
                schema_name = self.schema_name,
                schema_type = self.schema_type
            ).where(
                where_statement
            ).built().asyncExecute(
                  data_logging=self.data_logging
            )
        
        else:

            await self.query_builder.create(
                self.name,
                schema_name=self.schema_name
            ).columns(
                self.columns
            ).constraints(
                self.constraints
            ).partition(
                **self.partitions
            ).built().asyncExecute(
                data_logging=self.data_logging
            )

        await self.getDBElement()
        partitions = copy.deepcopy(self.partitions)

        self.db_element = {
            **self.db_element,
            'partitions':{
                'method':partitions.get('method'),
                'column_names':partitions.get('column_names'),
                'partitions':[]
            } if partitions else {}
        }

        if use_query:
            self.columns = self.db_element.get('columns')

        if self.grants is None:
            self.grants = self.db_element.get('grants')

    async def manageGrants(self) :
        """Grant privileges on schema.
        """
        
        db_grants:List[dict] = copy.deepcopy(
            self.db_element.get('grants')
        )

        for grant in self.grants:
            if grant in db_grants:
                db_grants.remove(grant)
            else:
                
                await self.data_logging.logEvent(
                    'grant',
                    'loading'
                )   
                await self.query_builder.grant(
                    self.name,
                    self.element_type,
                    self.schema_name,
                    **grant
                ).built().asyncExecute(
                    data_logging=self.data_logging
                )

        for revoke in db_grants:
            
            await self.data_logging.logEvent(
                'revoke',
                'loading'
            )   
            await self.query_builder.revoke(
                self.name,
                self.element_type,
                self.schema_name,
                **revoke   
            ).built().asyncExecute(
                data_logging=self.data_logging
            )

        if self.grants:
            self.db_element['grants'] = copy.deepcopy(self.grants)
    
    async def manageColumns(self) -> None:
        """Get table columns from existing table or from data.
        """
        
        await self.data_logging.logEvent(
            'columns',
            'loading'
        )
        
        db_columns:List[dict] = copy.deepcopy(
            self.db_element.get('columns',[])
        )

        for index,column in enumerate(self.columns):
            db_column_index = next((
                i for i,c in enumerate(db_columns)
                if c.get('name')==column.get('name')
            ),None)

            if db_column_index is not None:
                db_column = db_columns[db_column_index]
                db_columns.remove(db_column)
                self.columns[index] = copy.deepcopy(db_column)

                if db_column.get('type').lower() != column.get('type').lower():
                    
                    await self.query_builder.alter(
                        self.name,
                        schema_name=self.schema_name
                    ).alter(
                        column.get('name'),
                        'column'
                    ).columnType(
                        column.get('type')
                    ).built().asyncExecute(
                        data_logging=self.data_logging
                    )
                
                if db_column.get('comment') != column.get('comment'):
                    await self.query_builder.comment(
                        self.schema_name,
                        self.name,
                        column.get('name'),
                        column.get('comment')
                    ).built().asyncExecute(
                        data_logging=self.data_logging
                    )

            else:

                await self.query_builder.alter(
                    self.name,
                    schema_name=self.schema_name
                ).add(
                    'column',
                    column
                ).built().asyncExecute(
                    data_logging=self.data_logging
                )
            
        for column in db_columns:
            await self.query_builder.alter(
                self.name,
                schema_name=self.schema_name
            ).drop(
                column.get('name'),
                'column'
            ).built().asyncExecute(
                data_logging=self.data_logging
            )

        if self.columns:
            self.db_element['columns'] = copy.deepcopy(self.columns)
    
    async def manageConstraints(self) -> None:
                
        await self.data_logging.logEvent(
            'constraints',
            'loading'
        )
 
        db_constraints:List[dict] = copy.deepcopy(
            self.db_element.get('constraints')
        )

        for constraint in self.constraints:
            if constraint.get('name') in [c.get('name') for c in db_constraints]:
                db_constraints = [
                    c for c in db_constraints
                    if c.get('name') != constraint.get('name')
                ]
            else:
                await self.query_builder.alter(
                    self.name,
                    schema_name=self.schema_name
                ).add(
                    'constraint',
                    constraint
                ).built().asyncExecute(
                    data_logging=self.data_logging
                )
            
        for constraint in db_constraints:
            await self.query_builder.alter(
                self.name,
                schema_name=self.schema_name
            ).drop(
                constraint.get('name'),
                'constraint'
            ).built().asyncExecute(
                data_logging=self.data_logging
            )
        
        if self.constraints:
            self.db_element['constraints'] = copy.deepcopy(self.constraints)
    
    async def manageIndexes(self) -> None:
        """Create indexes.
        """
        
        await self.data_logging.logEvent(
            'index',
            'loading'
        )  

        db_indexes:List[dict] = copy.deepcopy(
            self.db_element.get('indexes')
        )

        for index in self.indexes:
            if (
                index not in db_indexes 
                and not index.get('constraint_type')
            ):
                await self.query_builder.create(
                    index.get('name'),
                    'index'
                ).uniqueIndex(
                    index.get('is_unique')
                ).onIndex(
                    self.name,
                    self.schema_name
                ).usingIndex(
                    index.get('method'),
                    index.get('columns')
                ).built().asyncExecute(
                    data_logging=self.data_logging
                )
            
            else:
                db_indexes.remove(index)

        for index in db_indexes:
            if not index.get('constraint_type'):
                await self.query_builder.drop(
                    index.get('name'),
                    'index',
                    exists_condition=True
                ).built().asyncExecute(
                    data_logging=self.data_logging
                )

        if self.indexes:
            self.db_element['indexes'] = copy.deepcopy(self.indexes)

    async def managePartition(self) -> None:

        await self.data_logging.logEvent(
            'partition',
            'loading'
        )    

        # {
        #     'method':'list',
        #     'column_names':['data_source_id'],
        #     'partitions': [
        #         {
        #             'name':'links_adresses_quebec',
        #             'expression':'for values in (3)',
        #             'method':'list',
        #             'column_names':['version_id'],
        #             'partitions':[
        #                 {
        #                     'name':'links_adresses_quebec_aq202404',
        #                     'expression':'for values in (AQ202404)',
        #                 }
        #             ]
        #         }
        #     ]
        # }
        await self.managePartitions(
            copy.deepcopy(self.partitions.get('partitions')),
            copy.deepcopy(self.db_element.get('partitions',{}).get('partitions',[])),
            self.name
        )

        if self.partitions:
            self.db_element['partitions'] = copy.deepcopy(self.partitions)

    async def managePartitions(
        self,
        partitions:List[Dict[str,Union[str,dict]]],
        db_partitions:List[Dict[str,Union[str,dict]]],
        parent_table_name:str
    ) -> None:
        for partition in partitions:
            if partition in db_partitions:
                db_partitions.remove(partition)
            else:
                name = partition.pop('name')

                await self.query_builder.create(
                    name,
                    schema_name=self.schema_name
                ).partition(
                    **partition,
                    table_name = parent_table_name
                ).built().asyncExecute(
                    data_logging=self.data_logging
                )

                await self.managePartitions(
                    copy.deepcopy(partition.get('partitions',[])),
                    copy.deepcopy(next((
                        db_partition for db_partition in db_partitions
                        if db_partition.get('name')== partition.get('name')
                    ),{}).get('partitions',[])),
                    name
                )
        
        for drop in db_partitions:
            await self.query_builder.drop(
                drop.get('name'),
                'table',
                self.schema_name,
                True
            ).built().asyncExecute(
                data_logging=self.data_logging
            )

    async def select(
        self,
        where_statement:list=None,
        columns:list=None,
        limit:int=None,
        loaded_rows:int = None,
        **kwargs
    ) -> Table:
        """Select data.

        Args:
            where_statement (list, optional): Where conditions. Defaults to None.
            columns (list, optional): Columns to select. Defaults to None.
        """
        
        await self.data_logging.logEvent(
            'select',
            'loading'
        )
        
        if self.db_element:
            self.data = Data(
                await self.query_builder.select(
                    self.name,
                    schema_name=self.schema_name,
                    limit = limit
                ).columns(
                    columns if columns else self.columns
                ).where(
                    where_statement
                ).built().asyncExecute(
                    data_logging=self.data_logging,
                    **kwargs
                ),
                meta_columns=[],
                columns = self.columns,
                geometry_saved_type='text',
                name=self.name,
                loaded_rows = loaded_rows,
            )
        
        return self

    async def update(
        self,
        update_values:Union[dict,list,None] = None,
        from_table:str=None,
        where_statement:list=None,
        columns:list=None,
        from_table_schema:str=None,
        element_from:dict = None,
        **kwargs
    ) -> None:
        """Update table.

        Args:
            update_values (Union[dict,list]): Values to update with.
            from_table (str, optional): Table from. Defaults to None.
            where_statement (list, optional): Where statement. Defaults to None.
            columns (list, optional): Columns. Defaults to None.
        """
        
        await self.data_logging.logEvent(
            'update',
            'loading'
        )
       
        if isinstance(update_values, dict):
            columns = update_values.keys()
            values = update_values.values()
        elif self.columns and isinstance(update_values, list):
            columns = columns
            values = update_values 

        if element_from is not None and isinstance(element_from,Data):

            temporary_table = AsyncTable(
                self.connection,
                "temporary_"+self.name,
                self.schema_name
            )
            await temporary_table.drop(exists_condition=True)
            await temporary_table.manage(data=element_from)
            await temporary_table.copy()

            await self.query_builder.update(
                self.name,
                self.schema_name
            ).fromTable(
                temporary_table.name,
                self.schema_name
            ).columns(
                columns
            ).values(
                values
            ).where(
                where_statement
            ).built().asyncExecute(
                data_logging=self.data_logging,
                **kwargs
            )

            await temporary_table.drop()

        elif (
            element_from is not None and
            not(
                'element_type' in element_from
                and element_from.get('element_type') == 'table'
            )
        ):
            await self.query_builder.update(
                self.name,
                self.schema_name
            ).sqlStatement(
                file_name = element_from.get('name'),
                schema_name = self.schema_name,
                schema_type = self.schema_type
            ).columns(
                columns
            ).values(
                values
            ).where(
                where_statement
            ).built().asyncExecute(
                data_logging=self.data_logging,
                **kwargs
            )

        else:

            if (
                element_from is not None and 'element_type' in element_from
                and element_from.get('element_type') == 'table'
            ):
                from_table = element_from.get('name')
                from_table_schema = element_from.get('schema_name')

            await self.query_builder.update(
                self.name,
                self.schema_name
            ).fromTable(
                from_table,
                from_table_schema if from_table_schema else self.schema_name
            ).columns(
                columns
            ).values(
                values
            ).where(
                where_statement
            ).built().asyncExecute(
                data_logging=self.data_logging,
                **kwargs
            )
        
    async def insert(
        self,
        insert_values:Union[dict, list] = {},
        return_values:list=None,
        element_from:SchemaElement = None,
        where_statement:dict = {},
        use_query:bool = False,
        query_name:str=None,
        columns:List[dict] = [],
        **kwargs
    ) -> list:
        """Insert data in table.

        Args:
            insert_values (Union[dict, list]): Values to insert, store in a dictonnary which the keys are the columns,
            or store in list if it's only the values name.
            return_value (str): Values name to return.

        Returns:    
            list: return values.
        """
             
        await self.data_logging.logEvent(
            'insert',
            'loading'
        )

        if element_from:
            columns_from = [c['name'] for c in element_from.columns]

            await self.query_builder.insert(
                self.name,
                schema_name=self.schema_name
            ).select(
                name = element_from.name,
                schema_name=element_from.schema_name
            ).columns(
                [c for c in self.columns if c.get('name') in columns_from]
            ).where(
                where_statement
            ).built().asyncExecute(
                data_logging=self.data_logging,
                **kwargs
            )

        elif use_query:
            await self.query_builder.insert(
                self.name,
                schema_name=self.schema_name
            ).columns(
                columns
            ).sqlStatement(
                file_name = query_name if query_name else self.name,
                schema_name=self.schema_name,
                schema_type=self.schema_type
            ).where(
                where_statement
            ).built().asyncExecute(
                data_logging=self.data_logging,
                **kwargs
            )

        else:

            if isinstance(insert_values, dict):
                insert_values = {
                    key:insert_values[key]
                    for key in insert_values
                    if insert_values[key] is not None and key in [c.get('name') for c in self.columns]
                }
                columns = insert_values.keys()
                values = insert_values.values()
            elif self.columns and isinstance(insert_values, list):
                columns = self.columns
                values = insert_values
                
            results = await self.query_builder.insert(
                self.name,
                schema_name=self.schema_name
            ).columns(
                columns
            ).values(
                values
            ).returnValues(
                return_values
            ).built().asyncExecute(
                data_logging=self.data_logging,
                **kwargs
            )

            return results
    
    async def delete(
        self,
        where_statement:list=None,
        using:dict={},
        delete_data:bool = False,
        **kwargs
    ) -> None:
        """Delete data in table.

        Args:
            where_statement (list, optional): Where statement to identify deleted data. Defaults to None.
        """
        
        if self.db_element:
            await self.data_logging.logEvent(
                'delete',
                'loading'
            )

            if (
                using is not None and
                not(
                    'element_type' in using
                    and using.get('element_type') == 'table'
                )
            ):
                await self.query_builder.delete(
                    self.name,
                    schema_name=self.schema_name
                ).sqlStatement(
                    file_name = using.get('name'),
                    schema_name = self.schema_name,
                    schema_type = self.schema_type
                ).where(
                    where_statement
                ).built().asyncExecute(
                    data_logging=self.data_logging,
                    **kwargs
                )
            else:
                await self.query_builder.delete(
                    self.name,
                    schema_name=self.schema_name
                ).where(
                    where_statement
                ).built().asyncExecute(
                   data_logging=self.data_logging,
                   **kwargs
                )
        
        if delete_data:
            self.data = None
    
    async def copy(
        self,
        data:Union[Data,pandas.DataFrame]=None,
        null_value:str = '',
        separator:str='|',
        **kwargs
    ) -> None:
        """Copy data in table via a csv file.

        Args:
            data (pandas.DataFrame, optional): Data to copy. Defaults to None.
            null_value (str, optional): Null value in the data. Defaults to ''.
            separator (str, optional): Separator to put data in the csv file. Defaults to '|'.
        """

        await self.data_logging.logEvent(
            'copy',
            'loading'
        )

        try: 
            await self.setData(data)
            saved_data = BytesIO()

            self.data.export('postgres').to_csv(
                saved_data,
                header=False,
                index=False,
                sep=separator,
                **kwargs
            )

            saved_data.seek(0)

            await self.connection.connection.copy_to_table(
                self.name,
                source = saved_data,
                columns = self.data.frame.columns.tolist(),
                schema_name = self.schema_name,
                delimiter = separator,
                null=null_value
            )
        
        except Exception as error:
            await self.data_logging.logEvent(error=error)
        else:
            await self.data_logging.logEvent()
    
    async def setData(
        self,
        data:Union[Data,pandas.DataFrame,None]
    ) -> Table:
        
        if data is not None:
            if isinstance(data,Data):
                self.data = data
            elif isinstance(data,pandas.DataFrame):
                if hasattr(self,'data') and isinstance(self.data,Data):
                    self.data.frame = data
                else:
                    self.data = Data(data)
        
        return self
    
    async def get(
        self,
        to_get:str='self'
    ) -> Union[Table,Data]:
        if to_get == 'self':
            return self
        
        if to_get == 'data':
            return copy.deepcopy(self.data)
        
        return getattr(self,to_get)
    
    async def executeDataAction(
        self,
        action_name:str,
        **kwargs
    ) -> Union[None,Data]:

        return await getattr(
            self if hasattr(self,action_name) else self.data,
            action_name
        )(**kwargs)
    
    def setDataConditions(
        self,
        data_source_name:str,
        data_conditions:Union[dict,List[dict]]
    ) -> AsyncTable:
        """Set data conditions for a data source.

        Args:
            data_source_name (str): Name of the data source.
            data_conditions (Union[dict,List[dict]]): Conditions to respect.

        Returns:
            Table: self.
        """
        
        self.data_conditions[data_source_name] = data_conditions
        
        return self

    def partitionDataSource(
        self,
        data_source_id:int,
        data_source_name:str,
        data_version_config:Dict[str,dict]
    ) -> None:
        """
        Partitions the data source by creating or updating a partition entry.
        Args:
            data_source_id (int): The ID of the data source to partition.
            data_source_name (str): The name of the data source to partition.
            data_version_config (Dict[str, dict]): Configuration dictionary for the data version.
        Returns:
            None
        """
        partitions = copy.deepcopy(self.partitions['partitions'])

        partition_name = '{}_{}'.format(self.name,data_source_name)

        partition_index = next((
            i for i,p in enumerate(partitions)
            if p.get('name') == partition_name
        ),None)

        if partition_index is None:
        
            self.partitions['partitions'].append({
                'name':partition_name,
                'expression' :"for values in ('{}')".format(data_source_id)
            })

    def setColumns(
        self,
        data_source_id: int = None,
        reset_data_source: bool = False,
        element_from: Table = None
    ) -> None:
        """
        Set or update the columns of the table based on various conditions.
        Parameters:
        - data_source_id (int, optional): The ID of the data source. Defaults to None.
        - reset_data_source (bool, optional): Flag to reset the data source. Defaults to False.
        - element_from (Table, optional): Another table to copy columns from. Defaults to None.
        Returns:
        - None
        Behavior:
        - If the table status is 'inactive', it resets the columns to an empty list.
        - If `data_source_id` is provided and `reset_data_source` is True, it removes columns associated with the given `data_source_id`.
        - If the table has data and `reset_data_source` is False, it updates or adds columns based on the data.
        - If `element_from` is provided, it copies columns from the given table that match the specified column names.
        """

        if self.status == 'inactive':
            self.columns = []

        elif data_source_id is not None and reset_data_source:
            columns = copy.deepcopy(self.columns)
            self.columns:List[dict] = []

            for column in self.columns:
                comment = column.get('comment')
                data_source_ids:list = json.loads(comment)['data_source_ids'] if comment else []
                if data_source_id in data_source_ids:
                    if len(data_source_ids) > 1:
                        self.columns.append({
                            **column,
                            "data_source_ids":[id for id in data_source_ids if id != data_source_id]
                        })
                else:
                    self.columns.append(column)                                        

        elif self.data is not None and not reset_data_source:
            for column in self.data.columns:
                column_index = next((
                    i for i,c in enumerate(self.columns)
                    if c.get('name') == column.get('name')
                ),None)

                column_constraints = [
                    c for c in self.constraints
                    if column.get('name') in c.get('columns')
                ]

                if column_index is None:
                    self.columns.append({
                        'name':column.get('name'),
                        'type':column.get('type'),
                        'comment':json.dumps({
                            'data_source_ids':[data_source_id]
                        }),
                        'serial': True if column_constraints and column_constraints[0].get('serial') else False
                    })
                
                else:
                    table_column = copy.deepcopy(self.columns[column_index])
                    comment = table_column.get('comment')
                    data_source_ids:list = json.loads(comment)['data_source_ids'] if comment else []

                    if column.get('type') !=table_column.get('type'):

                        table_column = {
                            **table_column,
                            'type':copy.deepcopy(column.get('type'))
                        }  

                    if data_source_id is not None and data_source_id not in data_source_ids:
                        data_source_ids.append(data_source_id)

                        table_column = {
                            **table_column,
                            'data_source_ids':data_source_ids
                        }

                    self.columns[column_index] = table_column

        elif element_from:
            if self.columns:
                self.columns = [
                    c if 'type' in c.keys() else next((co for co in element_from.columns if co.get('name')==c.get('name')),None)
                    for c in self.columns
                ]
            else:
                self.columns = copy.deepcopy(element_from.columns)

    def setConstraints(
        self,
        reset_data_source:bool = False
    ) -> None:
        if self.status == 'inactive':
            self.constraints = [c for c in self.constraints if c.get('name') == 'fk_file_id']
        
        elif self.data is not None and reset_data_source:
            for i,column in enumerate(self.data.columns):
                if column.get('values'):
                    constraint = {
                        'type':'check',
                        'clause':'{} in any({})'.format(column.get('name'),','.join(
                            ["'{}'".format(k) if column.get('type') == 'text' else k for k in column.get('values').keys()]
                        ))
                    }
                    columns[i] = {
                        **column,
                        'constraints':[constraint]
                    }
                    self.constraints.append(constraint)
                
                for constraint in column.get('constraints'):
                    
                    constraint_index = next(
                        (i for i,c in enumerate(self.constraints) if c.get('type') == constraint['type']),
                        None
                    )
                    if constraint_index is None:
                        if constraint['type'] == 'primary key':
                            columns = [column.get('name')]
                            if self.data_configuration.active:
                                columns.append('data_source_id')
                            constraint = {
                                'type':constraint['type'],
                                'columns':columns,
                                'name':'{}_pkey'.format(self.name)
                            }
                        # elif constraint['type'] == 'foreign key':
                        #     constraint = {
                        #         'type':constraint['type'],
                        #         'columns':[column.get('name')],
                        #         'reference_table_name':constraint['reference_table_name'],
                        #         'reference_columns':[constraint['reference_column']]
                        #     }
                        self.constraints.append(constraint)
                    
                    elif (
                        constraint['type'] == 'primary key' and
                        column.get('name') not in self.constraints[constraint_index]['columns']
                    ):
                        self.constraints[constraint_index]['columns'].append(column.get('name'))
                    # elif constraint['type'] == 'foreign key':
                    #     constraints[constraint_index]['columns'].append(column.get('name'))
                    #     constraints[constraint_index]['reference_columns'].append(constraint['reference_column'])
                    
    def setIndexes(self) -> None:
        if self.status == 'inactive':
            self.indexes = []

    async def resetDataSource(
        self,
        data_source_id:int,
        data_source_status:str
    ) -> None:
        """Reset the data source for that table, by deleting data or
        dropping table if it's the only source

        Args:
            data_source_id (int): Data source id.
            data_source_status (str): Data source status.
        """ 

        # table does not exists 
        # data_source_ids = []
        # status = 'inactive'
        # columns = []
        # constraints = [file_fk]

        # status = 'dev'
        # manage
        # constraints = [file_fk,pk]

        ####
        # table does exists 
        # data_source_ids = [1]
        # status = 'dev'
        # columns = [id,file_id,]

        data_source_ids = []

        # Get data sources
        for p in copy.deepcopy(self.partitions['partitions']):
            pd = re.findall(r'\d+',p.get('expression'))
            if pd:
                data_source_ids.append(int(pd[0]))

        if data_source_id in data_source_ids:
            if len(data_source_ids) == 1:
                self.status = 'inactive'
                await self.manage(
                    'values',
                    data_source_id=data_source_id,
                    reset_data_source=True
                )
            else:
                self.delete({'data_source_id':data_source_id})


        # if self.db_element:
        #     data_columns = self.data.columns
        #     self.data = None

        #     return [
        #         #Compare columns
        #         {
        #             **c,
        #             **self.compareColumn(c)
        #         } for c in self.columns
        #         # Remove data config columns
        #         if c.get('name') not in ['file_id','data_source_id']
        #     ]+[
        #     # Add not existing table
        #         {
        #             **c,
        #             'status':'add'
        #         } for c in data_columns
        #         if c.get('name') not in [
        #             co.get('name') for co in self.columns
        #         ]
        #     ]

        # self.data = None
        # return {}

    async def structureData(
        self,
        data_source_status:str,
        data_source_id:int
    ) -> None:
        
        if self.data is not None:

            data_source_ids = [p.get('data_source_id') for p in copy.deepcopy(self.partitions['partitions'])]
                
            if len(data_source_ids) == 1 and data_source_ids[0] == data_source_id:
                self.status = 'inactive'
                await self.manage()

            elif data_source_id in data_source_ids:
                self.delete({'data_source_id':data_source_id})
                self.setColumns(data_source_id)
                #self.setConstraints(data_source_id)

            if mode_level.get(data_source_status) > mode_level.get(self.status):
                self.status = copy.deepcopy(data_source_status)
                
            # If table exists
            if self.db_element:
                return {
                    'columns':[
                            #Compare columns
                            {
                                **c,
                                **self.compareColumn(c)
                            } for c in self.columns
                            # Remove data config columns
                            if c.get('name') not in ['file_id','data_source_id']
                        ]+[
                        # Add not existing table
                            {
                                **c,
                                'status':'add'
                        } for c in self.data.columns
                            if c.get('name') not in [
                                co.get('name') for co in self.columns
                        ]
                    ],
                    'constraints':self.constraints
                }

            else:
                self.setConstraints()
                self.setIndexes()

                self.manage_from = 'values'
                await self.manageInConfig()
                
                self.data = None
            
        return {}

    def compareColumn(
        self,
        column:dict
    ) -> dict:
        status = 'ok'
        data_column = next((c for c in self.data.columns if c.get('name') == column.get('name')),None)

        if data_column is None:
            status = 'inexistant'
        elif column.get('type') != data_column.get('type'):
            status = 'change_type'

        return {
            'status':status,
            'data_column':data_column
        }
    
    async def load(
        self,
        element_from:Union[Table,View,str]=None,
        where_statement:dict={},
        query:str = None,
        delete_data:bool = True,
        **kwargs
    ) -> None:
        
        if self.db_element:
            if delete_data:
                await self.delete(where_statement)

            if self.data and element_from is None:
                await self.copy(self.data,**kwargs)
            else:
                await self.insert(
                    element_from=element_from if isinstance(element_from,(AsyncTable,AsyncView)) else None,
                    where_statement=where_statement,
                    use_query=element_from is None or query is not None or isinstance(element_from,str),
                    query_name= query if query is not None else element_from if isinstance(element_from,str) else None ,
                    **kwargs
                )

        else:
            await self.manage(
                element_from=element_from,
                where_statement = where_statement,
                use_query=element_from == None
            )

    async def manageCache(
        self,
        action:str,
        directory_name:str,
        extension:str
    ) -> None:
        if self.use_cache:
            data=Data(name=self.name)
            cache_exists = await data.manageCache(
                extension,
                directory_name,
                action
            )

            await self.copy(data)
        
        if action == 'load_end':

            if self.db_element:

                await self.select()

                cache_exists = await self.data.manageCache(
                    extension,
                    directory_name,
                    action
                )
            
            else:

                data = Data(name=self.name)
                cache_exists = await data.manageCache(
                    extension,
                    directory_name,
                    action
                )
                await self.copy(data)


