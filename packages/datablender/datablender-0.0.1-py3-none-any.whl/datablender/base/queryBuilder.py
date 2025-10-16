"""
"""
from __future__ import annotations
from typing import Union, List, Dict

import os
import re
import json
import pandas
import datetime

from sqlalchemy.sql import text

from datablender.base.file import File
from datablender.base.connection import Connection,AsyncConnection

class QueryBuilder:
    """Built and execute a query.

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        config (dict): PostgreSQL configuration, lile vocabulary, variables type, type of element.
        vocabulary (list): .
        types (list): .
        elements_type_name (list): .
        text (str): The query itself.
        definition (str): Definition of the query, such as create, drop, alter, insert, update, delete, select or grant. 
        action (str): Query action that comes after a definition, such as add, drop, rename or own.

    Methods:
    ----------
        built(self) -> None: Built query.
        execute(self) -> None: Execute the query.

    Examples:
    --------
        >>> import datablender
        >>> query_builder = datablender.QueryBuilder(datablender.Connection())
        >>> query_builder.create(
        >>>     'test_database',
        >>>     'database'
        >>> ).built().execute()
        >>> query_builder.connection.close()

    """
    def __init__(
        self,
        connection:Union[AsyncConnection,Connection],
        config = None
    ):
        """Initiate the query builder.

        Args:
            connection (Connection): Connection to a database.
        """
        self.connection=connection

        self.psql_directory_name = os.path.join(
            os.path.dirname(__file__),
            '..',
            'postgresql'
        )
        self.config = config if config else File(
            path = os.path.join(
                os.path.dirname(__file__),
                '..',
                'configuration.json'
            )
        ).read().content

        self.vocabulary=self.config['vocabulary']
        self.generic_constraints = self.config['generic_constraints']

        self.resetAttributes()

        self.text_elements:List[str] = []

    def resetAttributes(self) -> None:

        self.definition = None
        self.action = None
        self.sub_element = None
        self.element = None
        self.name = None
        self.schema_name = None
        self.columns_ = None
        self.constraints_ = None
        self.constraint = None
        self.column = None
        self.is_materialized = False
        self.index_is_unique = False
        self.is_superuser = None
        self.can_create_database = None
        self.sub_name = None
        self.values_ = None
        self.return_values = None
        self.from_table = None
        self.where_statement = None
        self.select_value = None
        self.exists_condition = None
        self.privilege = None
        self.replace_view =False
        self.index_using_columns =None
        self.sub_schema_name =None
        self.return_values_text =None
        self.query = None
        self.method = None
        self.limit = None
        self.partition_method = None
        self.partition_columns = None
        self.expression = None
        self.column_type = None
        self.group_by = None

    def setValues(
        self,
        value,
        is_where:bool = False
    ):
      
        # Function to clean values to insert or update.
        if value is None:
            return 'NULL'

        elif isinstance(value,bool):
            return str(value).lower()
        
        elif str(value) == 'nan':
            return 'NULL'

        elif isinstance(value,str):
            return "'"+value.replace("'","''")+"'"

        elif isinstance(value,datetime.date):
            return "'"+value.strftime("%Y-%m-%d %H:%M:%S")+"'"
            
        elif isinstance(value,list):

            if all([isinstance(x,str) for x in value]):
                if is_where:
                    return '({})'.format(','.join(["'{}'".format(v) for v in value]))
                
                return "'"+str("{"+','.join(value)+"}")+"'"

            elif all([isinstance(x,dict) for x in value]):

                return 'array[{}]::json[]'.format(
                    ','.join([
                        "'{}'".format(json.dumps(value_dict))
                        for value_dict in value
                    ])
                )
            
        else:
            return str(value)

    def checkVocabulary(
        self,
        vocabulary:str
    ) -> str:
        
        if vocabulary.isdigit():
            return '"'+vocabulary+'"'
        
        return '"'+vocabulary+'"' if vocabulary in self.vocabulary else vocabulary
            
    def built(self) -> QueryBuilder:
        """Built query.

        Returns:
            QueryBuilder: self.
        """

        self.text_elements.append(self.definition) if self.definition else None

        if self.definition == 'create':

            if self.element == 'table':

                self.text_elements.append(self.element)

                self.text_elements.append(
                    '.'.join([self.schema_name,self.name])
                    if self.schema_name else self.name
                )

                if self.from_table:
                    self.text_elements.append('as\n')
                    self.text_elements.append('select\n')
                    self.text_elements.append(self.columns_)
                    self.text_elements.append('from')
                    self.text_elements.append(
                        '.'.join([self.from_table_schema,self.from_table])
                        if self.from_table_schema else self.from_table
                    )
                    if self.where_statement:
                        self.text_elements.append('where')
                        self.text_elements.append(self.where_statement)

                elif self.query:
                    self.text_elements.append('as\n')

                    self.text_elements.append(self.query)


                else:

                    if self.columns_:
                        self.text_elements.append('(\n')
                        self.text_elements.append(self.columns_)

                    if self.constraints_:
                        self.text_elements.append(',\n')
                        self.text_elements.append(self.constraints_)
                    
                    if self.columns_:
                        self.text_elements.append('\n)')

                    if self.expression:
                        self.text_elements.append('partition of')
                        self.text_elements.append(
                            '.'.join([self.schema_name,self.sub_name])
                            if self.schema_name else self.sub_name
                        )
                        self.text_elements.append(self.expression)

                    if self.partition_method:
                        self.text_elements.append('partition by')
                        self.text_elements.append(self.partition_method) 
                        self.text_elements.append(self.partition_columns)

            elif self.element == 'view':
                if self.replace_view:
                    self.text_elements.append('or replace')

                if self.is_materialized:
                    self.text_elements.append('materialized')

                self.text_elements.append(self.element)
                 
                self.text_elements.append(
                    '.'.join([self.schema_name,self.name])
                    if self.schema_name else self.name
                )
                   
                self.text_elements.append('as\n')

                if self.query:
                    self.text_elements.append(self.query)
                else:
                    self.text_elements.append('select \n\t')
                    self.text_elements.append(self.columns_)
                    self.text_elements.append('\nfrom')
                    self.text_elements.append(
                        '.'.join([self.from_table_schema,self.from_table])
                        if self.from_table_schema else self.from_table
                    )

                    if self.group_by:
                        self.text_elements.append('\ngroup by ')
                        self.text_elements.append(self.group_by)
                        
                
            elif self.element == 'role':
                
                self.text_elements.append(self.element)
                
                self.text_elements.append(
                    '.'.join([self.schema_name,self.name])
                    if self.schema_name else self.name
                )
                
                self.text_elements.append(
                    'SUPERUSER'
                ) if self.is_superuser else None

                self.text_elements.append(
                    'CREATEDB'
                ) if self.can_create_database else None
                
                self.text_elements.append(
                    'LOGIN'
                )
            
            elif self.element == 'index':

                self.text_elements.append(
                    'unique'
                ) if self.index_is_unique else None

                self.text_elements.append(self.element)

                self.text_elements.append(
                    '.'.join([self.schema_name,self.name])
                    if self.schema_name else self.name
                )

                self.text_elements.append('on')

                self.text_elements.append(
                    '.'.join([self.sub_schema_name,self.sub_name])
                    if self.sub_schema_name else self.sub_name
                )                  

                self.text_elements.append('\n')
                self.text_elements.append('USING')
                self.text_elements.append(self.method)
                self.text_elements.append('({})'.format(self.columns_))

            else:

                self.text_elements.append(self.element)

                self.text_elements.append(
                    '.'.join([self.schema_name,self.name])
                    if self.schema_name else self.name
                )

        elif self.definition == 'alter':
            
            if self.is_materialized:
                self.text_elements.append('materialized')
                
            self.text_elements.append(self.element)

            self.text_elements.append(
                '.'.join([self.schema_name,self.name])
                if self.schema_name else self.name
            )

            if self.action == 'rename':
                self.text_elements.append('rename to')
                self.text_elements.append(self.new_name)

            elif self.action == 'owner':
                self.text_elements.append('owner to')
                self.text_elements.append(self.sub_name)
            
            elif self.action == 'schema':
                self.text_elements.append('set schema')
                self.text_elements.append(self.new_schema)
                
            elif self.action == 'add':
                self.text_elements.append(self.action)
                self.text_elements.append(self.sub_element)

                if self.column:
                    self.text_elements.append(self.column)
                elif self.constraint:
                    self.text_elements.append(self.constraint)
            
            elif self.action == 'alter':
                self.text_elements.append(self.action)
                self.text_elements.append(self.sub_element)
                self.text_elements.append(self.sub_name)
                if self.column_type:
                    self.text_elements.append('type')
                    self.text_elements.append(self.column_type)
                    self.text_elements.append('using')
                    self.text_elements.append('{}::{}'.format(
                        self.sub_name,
                        self.column_type
                    ))

        elif self.definition == 'insert':
            self.text_elements.append('into')

            self.text_elements.append(
                '.'.join([self.schema_name,self.name])
                if self.schema_name else self.name
            )

            if self.from_table:
                self.text_elements.append('select\n')
                self.text_elements.append(self.columns_)
                self.text_elements.append('from')
                self.text_elements.append(
                    '.'.join([self.from_table_schema,self.from_table])
                    if self.from_table_schema else self.from_table
                )
                if self.where_statement:
                    self.text_elements.append('where')
                    self.text_elements.append(self.where_statement)

            elif self.query:
                if self.columns_:
                    self.text_elements.append(self.columns_)
                self.text_elements.append(self.query)

            else:

                self.text_elements.append(self.columns_)
                self.text_elements.append('\n')
                self.text_elements.append('values')
                self.text_elements.append(self.values_)
                if self.return_values:

                    self.text_elements.append('\n')
                    self.text_elements.append('returning')
                    self.text_elements.append(self.return_values_text)
        
        elif self.definition == 'update':

            self.text_elements.append(
                '.'.join([self.schema_name,self.name])
                if self.schema_name else self.name
            )
            self.text_elements.append('a') if self.from_table or self.query else None
            self.text_elements.append('set')
            self.text_elements.append(','.join([
                ' = '.join([
                    self.checkVocabulary(column),
                    'b.{}'.format(self.checkVocabulary(value)) if self.from_table or self.query else self.setValues(value)
                ]) for column,value in zip(self.columns_, self.values_)
            ]))

            if self.from_table:
                self.text_elements.append('from')
                self.text_elements.append(
                    '.'.join([self.from_table_schema,self.from_table])
                    if self.from_table_schema else self.from_table
                )
                self.text_elements.append('b')

            if self.query:
                self.text_elements.append('from (\n')
                self.text_elements.append(self.query)
                self.text_elements.append('\n) b')

            if self.where_statement:
                
                self.text_elements.append('where')
                self.text_elements.append(self.where_statement)

        elif self.definition == 'select':

            if self.query:
                self.text_elements = [self.query]

            else:
                if self.columns_:
                    self.text_elements.append(self.columns_)
                
                elif self.select_value:
                    self.text_elements.append(self.select_value)
                
                else:
                    self.text_elements.append('*')

                if self.name:
                    self.text_elements.append('from')

                    self.text_elements.append(
                        '.'.join([self.schema_name,self.name])
                        if self.schema_name else self.name
                    )
                elif self.from_table:
                    self.text_elements.append('from')

                    self.text_elements.append(
                        '.'.join([self.from_table_schema,self.from_table])
                        if self.from_table_schema else self.from_table
                    )

                elif self.query:
                    self.text_elements.append('from')
                    self.text_elements.append('({}\n)'.format(self.query))
                    self.text_elements.append('a')

                if self.where_statement:
                    self.text_elements.append('where')
                    self.text_elements.append(self.where_statement)

                if self.group_by:
                    self.text_elements.append('\ngroup by ')
                    self.text_elements.append(self.group_by)

                if self.limit:
                    self.text_elements.append('limit')
                    self.text_elements.append(str(self.limit))

        elif self.definition == 'drop':

            if self.is_materialized:
                self.text_elements.append('materialized')

            self.text_elements.append(self.element)

            if self.exists_condition:
                self.text_elements.append('if exists')

            self.text_elements.append(
                '.'.join([self.schema_name,self.name])
                if self.schema_name else self.name
            )

        elif self.definition == 'delete':
            self.text_elements.append('from')

            self.text_elements.append(
                '.'.join([self.schema_name,self.name])
                if self.schema_name else self.name
            )

            if self.query:
                self.text_elements.append('using (\n')
                self.text_elements.append(self.query)
                self.text_elements.append('\n) b')

            if self.where_statement:
                self.text_elements.append('where')
                self.text_elements.append(self.where_statement)
    
        elif self.definition == 'grant':
            self.text_elements.append(self.privilege)
            self.text_elements.append('on')
            self.text_elements.append(self.element)

            self.text_elements.append(
                '.'.join([self.schema_name,self.name])
                if self.schema_name else self.name
            )

            self.text_elements.append('to')
            self.text_elements.append(self.sub_name)
       
        elif self.definition == 'revoke':
            
            self.text_elements.append(self.privilege)
            self.text_elements.append('on')

            if self.element in ['schema','database']:
                self.text_elements.append(self.element)

            self.text_elements.append(
                '.'.join([self.schema_name,self.name])
                if self.schema_name else self.name
            )

            self.text_elements.append('from')
            self.text_elements.append(self.sub_name)

        elif self.definition == 'refresh':
            self.text_elements.append('materialized')
            self.text_elements.append('view')
            self.text_elements.append(
                '.'.join([self.schema_name,self.name])
                if self.schema_name else self.name
            )
        
        elif self.definition == 'comment':
            self.text_elements.append('on column')

            self.text_elements.append(
                '.'.join([self.schema_name,self.name,self.column])
            )
            self.text_elements.append('is')
            self.text_elements.append("'{}'".format(self.sub_name))

            #comment on column session_log.userid is 'The user ID';

        elif self.query:
            self.text_elements.append(self.query)

        self.text_elements.append('\n;')

        return self

    def execute(
        self,
        use_engine=True,
        **kwargs
    ) -> Union[
        pandas.DataFrame,
        list
    ]:
        """Execute the query.

        Args:
            use_engine (bool, optional): True if the engine will be used. Defaults to True.

        Returns:
            Union[list,Data]: data from the query.
        """
        # Execute select query
        
        if self.definition == 'select':
            self.resetAttributes()
            query = ' '.join(self.text_elements)
            self.text_elements = []
            return pandas.read_sql(
                query,
                self.connection.engine if use_engine else self.connection.connection,
                **kwargs
            )
        # Execute query
        else:
            query = ' '.join(self.text_elements)
            self.text_elements = []

            if use_engine:
                connection = self.connection.engine.connect()
                cursor_results = connection.execute(
                    text(query) 
                )
                connection.commit()
                connection.close()

                if self.return_values:
                    values=[
                        {
                            return_value:value
                            for return_value,value in zip(self.return_values,values)
                        }
                        for values in list(cursor_results.fetchall())
                    ]
                    self.resetAttributes()
                    return values
                
                self.resetAttributes()
                
            else:
                self.resetAttributes()

                self.connection.cursor.execute(query)
                if self.connection.cursor.description:
                    return list(self.connection.cursor.fetchall())

                self.connection.connection.commit()

    async def asyncExecute(
        self,
        use_engine:bool = True,
        is_transaction:bool = True,
        data_logging = None,
        **kwargs
    ) -> Union[
        pandas.DataFrame,
        list
    ]:
        """Execute the query.

        Args:
            use_engine (bool, optional): True if the engine will be used. Defaults to True.

        Returns:
            Union[list,Data]: data from the query.
        """
        # Execute select query
        
        if self.definition == 'select':

            self.resetAttributes()
            query = ' '.join(self.text_elements)
            self.text_elements = []

            #print(query)

            async with self.connection.engine.begin() as conn:
                try:
                    data = await conn.run_sync(
                        lambda sync_conn: pandas.read_sql(
                            query,
                            con=sync_conn,
                            **kwargs
                        )
                    )
                except Exception as error:
                    await conn.rollback()

                    if data_logging is not None:
                        await data_logging.logEvent(error = error)
                    return pandas.DataFrame()
                
                else:
                    if data_logging is not None:
                        await data_logging.logEvent()
                    return data
            
        else:
            query = ' '.join(self.text_elements)
            self.text_elements = []

            #if self.definition == 'delete': print(query)

            if use_engine:
                async with self.connection.async_session() as session:
                    try:
                        result = await session.execute(text(query))

                        if self.return_values:
                            values=[
                                {
                                    return_value:value
                                    for return_value,value in zip(self.return_values,values)
                                }
                                for values in list(result.fetchall())
                            ]
                            self.resetAttributes()
                            return values
                        
                        self.resetAttributes()
                    
                    except Exception as error:
                        await session.rollback()
                        if data_logging is not None:
                            await data_logging.logEvent(error = error)
                    else:
                        await session.commit()
                        if data_logging is not None:
                            await data_logging.logEvent()

            else:
                self.resetAttributes()
                if is_transaction:
                    tr = self.connection.connection.transaction()
                    try:
                        await tr.start() 
                        values = await self.connection.connection.execute(
                            query
                        )
                    except Exception as error:
                        await tr.rollback()
                        if data_logging is not None:
                            await data_logging.logEvent(eror = error)
                            
                    else:
                        await tr.commit()
                        if data_logging is not None:
                            await data_logging.logEvent()
                else :
                    try:
                        await self.connection.connection.execute(
                            query
                        )
                    except Exception as error:
                        if data_logging is not None:
                            await data_logging.logEvent(error = error)
                            
                    else:
                        if data_logging is not None:
                            await data_logging.logEvent()

    def create(
        self,
        name:str,
        element:str='table',
        schema_name:str=None,
        is_materialized:bool=None
    ) -> QueryBuilder:
        """Create a SQL element.

        Args:
            name (str): Element name.
            element (str, optional): Element type. Defaults to 'table'.
            schema_name (str, optional): Element schema name. Defaults to 'public'.

        Returns:
            QueryBuilder: self.
        """
        self.name=name
        self.definition = 'create'
        self.element = element
        self.schema_name = schema_name
        self.is_materialized=is_materialized
        return self

    def update(
        self,
        name:str,
        schema_name:str='public'
    ) -> QueryBuilder:

        """Update a SQL element.

        Args:
            name (str): Element name.
            schema_name (str, optional): Schema element name. Defaults to 'public'.

        Returns:
            QueryBuilder: self.
        """
        
        self.definition = 'update'
        self.element = 'table'
        self.name = name
        self.schema_name = schema_name
        
        return self

    def insert(
        self,
        name:str,
        schema_name:str='public'
    ) -> QueryBuilder:
        
        self.definition = 'insert'
        self.element = 'table'
        self.name = name
        self.schema_name = schema_name

        return self

    def delete(
        self,
        name:str,
        schema_name:str='public'
    ) -> QueryBuilder:
    
        self.definition = 'delete'
        self.element = 'table'
        self.name = name
        self.schema_name = schema_name
    
        return self

    def alter(
        self,
        name:str,
        element:str='table',
        schema_name:str=None,
        is_materialized:bool=None
    ) -> QueryBuilder:
        """Alter element.

        Args:
            name (str): Element name.
            element (str, optional): Element type. Defaults to 'table'.
            schema_name (str, optional): Schema name. Defaults to 'public'.

        Returns:
            QueryBuilder: self.
        """
        
        if schema_name:
            self.schema_name = schema_name 
        
        if element in ['column','constraint']:
            self.sub_element = element
            self.action = 'alter'
            self.sub_name=self.checkVocabulary(name)
        
        else:
            self.definition = 'alter'
            self.element = element
            self.name=name
            self.is_materialized=is_materialized
        
        return self

    def select(
        self,
        name:str=None,
        element:str='table',
        schema_name:str='public',
        limit:int=None
    ) -> QueryBuilder:
        if self.definition in ['insert','create']:
            self.from_table_schema = schema_name
            self.from_table = name
        else:
            self.definition = 'select'
            self.element = element
            self.name=name
            self.schema_name = schema_name
            self.limit = limit
        return self

    def grant(
        self,
        name:str,
        element:str='table',
        schema_name:str=None,
        privilege:str='select',
        user_name:str='postgres'
    ) -> QueryBuilder:
     
        self.definition = 'grant'
        self.element = element
        self.name=name
        self.schema_name = schema_name
        self.privilege = privilege
        self.sub_name = user_name
     
        return self

    def revoke(
        self,
        name:str,
        element:str='table',
        schema_name:str=None,
        privilege:str='select',
        user_name:str='postgres'
    ) -> QueryBuilder:
        
        self.definition = 'revoke'
        self.element = element
        self.name = name
        self.schema_name = schema_name
        self.privilege = privilege
        self.sub_name = user_name
     
        return self

    def add(
        self,
        element_type:str,
        element:dict = None
    ) -> QueryBuilder:
        self.action='add'
        if element_type in ['column','constraint']:
            self.sub_element = element_type

            if element_type == 'constraint':

                self.constraint =' '.join([
                    self.checkVocabulary(element['name']),
                    element['type'] if 'type' in element else '',
                    "({})".format(
                        ','.join(element['columns'])
                    ) if element.get('columns') and element.get('type') != 'check' else '',

                    'REFERENCES ' if element.get('reference_table_name') else '',
                    '{}.{}'.format(
                        element.get('reference_schema_name'),
                        element.get('reference_table_name')
                    ) if  element.get('reference_table_name') else '',                            
                    "({})".format(
                        ','.join(element['reference_columns'])
                    ) if element.get('reference_table_name') else '',

                    element['clause'] if 'clause' in element else '',                            

                ])     
            
            elif element_type == 'column':
                
                self.column = ' '.join([
                    element.get('name'),
                    element.get('type')
                ])
        
        else:
            self.element = element_type
        
        return self

    def drop(
        self,
        name:str,
        element:str,
        schema_name:str=None,
        exists_condition=False,
        is_materialized:bool=None
    ) -> QueryBuilder:
        """Drop SQL element.

        Args:
            name (str): Element name.
            element (str): Element type.
            schema_name (str, optional): Schema name. Defaults to 'public'.
            exists_condition (bool, optional): Add exists condition. Defaults to False.
            is_materialized (bool, optional): If it's a view, specified if it's materialized. Defaults to False.

        Returns:
            QueryBuilder: self.
        """
        
        self.schema_name = schema_name
        
        if element in ['column','constraint']:
            self.sub_element = element
            self.action = 'drop'
            self.sub_name = name
        
        else:
            self.definition = 'drop'
            self.element = element
            self.name = name
        
        self.exists_condition = exists_condition
        self.is_materialized = is_materialized
        
        return self

    def owner(
        self,
        name:str
    ) -> QueryBuilder:
        self.action='owner'
        self.sub_name = name
        return self

    def columns(
        self,
        columns:List[dict]=None
    ) -> QueryBuilder:
        
        if self.definition == 'create':

            if self.element == 'table':

                if self.from_table:
                    self.columns_ = ',\n    '.join([
                        self.checkVocabulary(
                            column.get('name')
                        )
                        for column in columns
                    ]) 
                else:
                
                    self.columns_=',\n\t'.join([
                        ' '.join([
                            self.checkVocabulary(column.get('name')),
                            'SERIAL' if column.get('serial') else column.get('type'),
                            'DEFAULT {}'.format(
                                self.setValues(column.get('default_value'))
                            ) if column.get('default_value') else '',
                            'NOT NULL' if (
                                column.get('constraints')
                                and any([
                                    constraint['type'] == 'not_null'
                                    for constraint in column.get('constraints')
                                ])
                            ) else ''
                        ]) for column in columns
                    ])

        elif self.definition == 'insert':

            if self.from_table:
                self.columns_ = ',\n    '.join([
                    self.checkVocabulary(
                        column.get('name')
                    )
                    for column in columns
                ]) 

            elif columns:

                if all([isinstance(column,str) for column in columns]):
                    columns=','.join([
                        self.checkVocabulary(column)
                        for column in columns
                    ])

                elif all([isinstance(column,dict) for column in columns]):
                    columns=','.join([
                        self.checkVocabulary(column['name'])
                        for column in columns
                    ])

                self.columns_ = '({})'.format(columns)
            
        elif self.definition == 'update':
            self.columns_ = columns
        
        elif self.definition == 'select':
            self.columns_ = ',\n    '.join([
                self.checkVocabulary(
                    column.get('name')
                )
                for column in columns
            ])

        return self

    def values(
        self,
        values:list
    ) -> QueryBuilder:
        """List of the values.

        Example :
        >>> values(['a','b'])

        Args:
            values (list): List of the values.

        Returns:
            QueryBuilder: self.
        """
        if self.definition == 'insert':
            values =','.join([self.setValues(value) for value in values])
            self.values_ = '({})'.format(values)
        elif self.definition == 'update':
            self.values_ = values
        return self

    def constraints(
        self,
        constraints:List[dict]=[]
    ) -> QueryBuilder:
        
        self.constraints_=',\n\t'.join([
            ' '.join([

                'CONSTRAINT',
                self.checkVocabulary(constraint['name']),
                constraint['type'] if 'type' in constraint else '',
                "({})".format(
                    ','.join(constraint['columns'])
                ) if constraint.get('columns') and constraint.get('type') != 'check' else '',

                'REFERENCES ' if constraint.get('reference_table_name') else '',
                '{}.{}'.format(
                    constraint.get('reference_schema_name'),
                    constraint.get('reference_table_name')
                ) if  constraint.get('reference_table_name') else '',                            
                "({})".format(
                    ','.join(constraint['reference_columns'])
                ) if constraint.get('reference_table_name') else '',

                constraint['clause'] if constraint.get('clause') else '',                            

            ]) for constraint in constraints
        ])
        
        return self

    def uniqueIndex(
        self,
        is_unique:bool
    ) -> QueryBuilder:
        """Indicate if index is unique.

        Args:
            is_unique (bool): Is index unique.

        Returns:
            QueryBuilder: self.
        """
       
        self.index_is_unique = is_unique
        
        return self

    def onIndex(
        self,
        name:str,
        schema_name:str='public'
    ) -> QueryBuilder:
        
        self.sub_name = name
        self.sub_schema_name = schema_name

        return self

    def usingIndex(
        self,
        method:str,
        columns:list = None
    ) -> QueryBuilder:
        
        self.method = method
        
        self.columns_ = ','.join(columns) if columns else None

        return self

    def where(
        self,
        statement:Union[List[Dict[str,str]],Dict[str,str]]
    ) -> QueryBuilder:
        if statement:
            if isinstance(statement,dict) and sorted(statement.keys()) != ['operator','where_elements']:
                statement = [
                    {
                        **statement[statement_element],
                        'name':statement_element
                    } if isinstance(statement[statement_element],dict) else {
                        'name':statement_element,
                        'value':statement[statement_element]
                    }
                    for statement_element in statement
                ]

            if self.query and self.definition not in ('update','delete'):
                for column in statement:
                    self.query = re.sub(
                        "{} = '\w+'".format(self.checkVocabulary(column.get('name'))),
                        "{} = {}".format(
                            self.checkVocabulary(column.get('name')),
                            self.setValues(column.get('value'),True)
                        ),
                        self.query
                    )

                # self.query = re.sub(
                #     ' and\n    '.join([
                #         #"{} = '[^\W\d_]+'".format(k.get("name"))
                #         "{} = '\w+'".format(k.get("name"))
                #         for k in statement
                #     ]),
                #     self.where_statement,
                #     self.query
                # )

            elif self.query and self.definition == 'delete':

                self.where_statement=' {}\n    '.format(statement.get('operator')).join([
                    self.setWhereComparaison(column)
                    for column in statement.get('where_elements')
                ])
                

            else:
                self.where_statement=' and\n    '.join([
                    self.setWhereComparaison(column)
                    for column in statement
                ])

        return self

    def setWhereComparator(
        self,
        column:Dict[str, str]
    ):
        if isinstance(column.get('value'),list) and column.get('type') == 'text[]':
            return ' && '
        
        if isinstance(column.get('value'),list):
            return ' in '
        
        return ' = '
    
    def setWhereComparaison(
        self,
        column:Dict[str, str]
    ) -> None:
        
        if column.get('value') is not None:
            return self.setWhereComparator(column).join([
                '{}{}'.format(
                    'a.' if (self.from_table or self.query) and self.definition == 'update' else '',
                    self.checkVocabulary(column.get('name'))
                ),
                'b.{}'.format(
                    self.checkVocabulary(column.get('value'))
                ) if (
                    (self.from_table or self.query) and self.definition == 'update'
                ) else self.setValues(
                    column.get('value'),
                    column.get('type') != 'text[]'
                )
            ])  
        
        if column.get('operator') is not None:
            return '({})'.format(' {}\n    '.format(column.get('operator')).join([
                self.setWhereComparaison(column)
                for column in column.get('where_elements')
            ]))

        return '{}{} is {} null'.format(
            'b.' if 'element' in column else '',
            self.checkVocabulary(column.get('name')),
            'not' if column.get('reverse') else ''
        )

    def roleOptions(
        self,
        is_superuser:bool = False,
        can_create_database:bool = False
    ) -> QueryBuilder:
    
        self.is_superuser=is_superuser
        self.can_create_database=can_create_database

        return self
    
    def rename(
        self,
        new_name:str
    ) -> QueryBuilder:
        self.action='rename'
        self.new_name=new_name
        return self

    def materialized(
        self,
        is_materialized:bool
    ) -> QueryBuilder:
        self.is_materialized=is_materialized
        return self
    
    def setSelectColumn(
        self,
        name:str,
        group_by:bool = False,
        as_name:str = None,
        function:str=None,
        **kwargs
    ) -> str:
        
        column = self.checkVocabulary(name)
        
        if function:
            column = '{}({})'.format(
                function,
                '*' if function == 'count' else self.checkVocabulary(name)
            )

        if as_name is not None:
            return '{} {}'.format(column,self.checkVocabulary(as_name))
    
        return column

    def sqlStatement(
        self,
        query:Union[str,dict]=None,
        directory_name:str=None,
        file_name:str=None,
        definition:str=None,
        schema_name:str=None,
        schema_type:str=None
    ) -> QueryBuilder:

        if query:
            if isinstance(query,dict):
                self.from_table=query.get('from')['name']
                self.from_table_schema=query.get('from')['schema_name']
                
                self.columns_ = ',\n    '.join([
                    self.setSelectColumn(
                        **column
                    )
                    for column in query.get('columns')
                ])

                self.group_by = ','.join([
                    str(i+1) for i,c in enumerate(query.get('columns'))
                    if 'group_by' in c and c['group_by']
                ])

                if 'where' in query:
                    self.where(query.get('where'))

            else:
                self.query = query
        
        elif file_name:
            if not directory_name :
                directory_name = os.getenv('CODE_DIRECTORY',os.getcwd())
                
                if schema_name:
                    new_directory_name = os.path.join(
                        directory_name,
                        schema_type,
                        schema_name,
                        'queries'
                    )
                    
                    if os.path.isdir(new_directory_name):
                        directory_name = new_directory_name

            elif not os.path.isdir(directory_name):
                new_directory_name = os.path.join(
                    os.getenv('CODE_DIRECTORY',os.getcwd()),
                    directory_name
                )
                if os.path.isdir(new_directory_name):
                    directory_name = new_directory_name

            self.query = File(
                directory_name,
                file_name+'.sql' if '.' not in file_name else file_name
            ).read(encoding = 'utf-8').content            

        self.definition = definition if definition else self.definition

        return self

    def returnValues(
        self,
        values:str
    ) -> QueryBuilder:
        """Return a value from a query.

        Args:
            values (str): Value name.

        Returns:
            QueryBuilder: self.
        """
        if values:
            self.return_values = values
            values_text =','.join([self.checkVocabulary(value) for value in values])
            self.return_values_text = '({})'.format(values_text)
        return self

    def selectElements(
        self,
        element_type_name:str
    ) -> QueryBuilder:
        """Get the list of elements in a data server, like databases, tables, schema,...

        Args:
            element_type_name (str): database, table, schema, view,...

        Returns:
            QueryBuilder: self.
        """
        self.element = element_type_name
        self.definition = 'select'
        self.text_elements.append(File(
            os.path.join(self.psql_directory_name,'elements'),
            '{}.sql'.format(self.element)
        ).read().content)

        return self
    
    def currentDatabase(self) -> QueryBuilder:
        self.select_value = 'current_database()'
        return self

    def fromTable(
        self,
        table_name:str,
        schema_name:str
    ) -> QueryBuilder:
        """Specify the from table for an update.

        Args:
            table_name (str): Table name.

        Returns:
            QueryBuilder: self.
        """
        self.from_table_schema = schema_name
        self.from_table = table_name
        return self

    def replace(self) -> QueryBuilder:
        self.replace_view = True
        return self

    def schema(
        self,
        schema:str
    ) -> QueryBuilder:
        
        self.action = 'schema'
        self.new_schema = schema

        return self
    
    def refresh(
        self,
        name:str,
        schema_name:str=None
    ) -> QueryBuilder:
        
        self.definition = 'refresh'
        self.name = name
        self.schema_name = schema_name

        return self

    def partition(
        self,
        method:str=None,
        column_names:List[str]=None,
        expression:str=None,
        table_name:str=None,
        **kwargs
    ) -> QueryBuilder:
        
        self.partition_method = method
        self.partition_columns = "({})".format(','.join(column_names)) if column_names else None

        self.expression = expression
        self.sub_name = table_name

        return self

    def columnType(
        self,
        column_type:str
    ) -> QueryBuilder:
        self.column_type = column_type
        return self
    
    def comment(
        self,
        schema_name:str,
        table_name:str,
        column_name:str,
        comment:str
    ) -> QueryBuilder:
        
        self.definition = 'comment'
        self.schema_name =schema_name
        self.name =table_name
        self.column =column_name
        self.sub_name = comment

        return self
