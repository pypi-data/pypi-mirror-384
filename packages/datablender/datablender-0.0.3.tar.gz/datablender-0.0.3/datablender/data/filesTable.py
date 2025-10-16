"""

"""
from __future__ import annotations

import datetime

from datablender.base import (
    Connection,
    QueryBuilder,
    AsyncConnection
)
from datablender.database import Table,AsyncTable

class FilesTable(Table):
    """A table containing all the files.

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        schema_name (str): Schema name.

    Methods:
    ----------
        getFiles(self) -> FilesTable: Get files in the files table according to the schema.
        checkFile(self,file:File,main_file:File) -> bool: Check if file is in the database files.
        updateFileInformation(
            self,modification_time:datetime.datetime,rows:int,size:int,id:int,table:str,schema:str
        ) -> None: Update the files table on a file with his informations.

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        connection:Connection
    ):
        """Initiate files table.

        Args:
            connection (Connection): Connection to a database.
        """

        self.query_builder = QueryBuilder(connection)

        super(FilesTable,self).__init__(
            connection,
            **next(
                (
                    config for config in
                    self.query_builder.config['elements']['table']['configs']
                    if config['name'] == 'files'
                ),
                {}
            )
        )

    def getFiles(self) -> FilesTable:
        """Get files in the files table.
        """
        self.select(index_col='path_index')
        return self
    
    def checkFile(self,path_index:str) -> bool:
        """Check if file is in the database files.

        Args:
            path_index (File): File to check.

        Returns:
            bool: Is the file in the files.
        """
        return self.data.frame.index.isin([path_index]).any()

    def updateFileInformation(
        self,
        id:int,
        schema:str,
        tables:list,
        modification_time:datetime.datetime,
        size:int,
        rows:int,
        columns:list,
        **kwargs
    ) -> None:
        """Update the files table on a file with his informations.

        Args:
            modification_time (datetime.datetime): Modification time.
            rows (int): Number of rows in the data.
            size (int): File size.
            id (int): File id.
            table (str): Table name that will contain the data.
            schema (str): Table schema name.
        """
        
        self.update(
            {
                'modification_time':modification_time,
                'rows':rows,
                'size':size,
                'columns':columns
            },
            where_statement={
                'id':id,
                'tables':tables,
                'schema':schema
            }
        )

class AsyncFilesTable(AsyncTable):
    """A table containing all the files.

    Attributes:
    ----------
        connection (Connection): Connection to a database.
        schema_name (str): Schema name.

    Methods:
    ----------
        getFiles(self) -> FilesTable: Get files in the files table according to the schema.
        checkFile(self,file:File,main_file:File) -> bool: Check if file is in the database files.
        updateFileInformation(
            self,modification_time:datetime.datetime,rows:int,size:int,id:int,table:str,schema:str
        ) -> None: Update the files table on a file with his informations.

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        connection:AsyncConnection
    ):
        """Initiate files table.

        Args:
            connection (Connection): Connection to a database.
        """

        self.query_builder = QueryBuilder(connection)

        super(AsyncFilesTable,self).__init__(
            connection,
            **next(
                (
                    config for config in
                    self.query_builder.config['elements']['table']['configs']
                    if config['name'] == 'files'
                ),
                {}
            )
        )

    async def getFiles(self) -> AsyncFilesTable:
        """Get files in the files table.
        """
        await self.select(index_col='path_index')
        return self
    
    def checkFile(self,path_index:str) -> bool:
        """Check if file is in the database files.

        Args:
            path_index (File): File to check.

        Returns:
            bool: Is the file in the files.
        """
        return self.data.frame.index.isin([path_index]).any()

    async def updateFileInformation(
        self,
        id:int,
        schema:str,
        tables:list,
        modification_time:datetime.datetime,
        size:int,
        rows:int,
        columns:list,
        **kwargs
    ) -> None:
        """Update the files table on a file with his informations.

        Args:
            modification_time (datetime.datetime): Modification time.
            rows (int): Number of rows in the data.
            size (int): File size.
            id (int): File id.
            table (str): Table name that will contain the data.
            schema (str): Table schema name.
        """
        
        await self.update(
            {
                'modification_time':modification_time,
                'rows':rows,
                'size':size,
                'columns':columns
            },
            where_statement= [
                {
                    'name':'id',
                    'value':id
                },
                {
                    'name':'tables',
                    'value':tables,
                    'type':'text[]'
                },
                {
                    'name':'schema',
                    'value':schema
                }
            ]
        )
