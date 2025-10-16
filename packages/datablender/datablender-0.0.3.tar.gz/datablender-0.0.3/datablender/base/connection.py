"""

"""
from __future__ import annotations

import os
import psycopg2
import postgis
import sqlalchemy
import aiohttp
import asyncio
import asyncpg
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)

from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT,ISOLATION_LEVEL_DEFAULT

from datablender.base import normalize_user_name

class Connection:
    """Connection to a database.

    Attributes:
    ----------
        host (str): Server's host.
        port (str): Server's port.
        database_name (str): Database name.
        user_name (str): User name.
        password (str): Password.
        dialect (str): Dialect.
        connection_string (str) : Connection string.
        engine (object) : SQLAlchemy engine.
        connection (object) : Connection.
        cursor (object) : Connection's cursor.

    Methods:
    ----------
        getConnection (self) -> None: Get the connection.
        getCursor (self) -> None: Get the connection's cursor.
        getEngine (self) -> None: Get SQLAlchemy engine.
        connectActions (self) -> None: Get the connection, cursor and engine.
        connect (self) -> None: Connect to the database.
        close (self) -> None: a .
        registerToPostgis (self) -> None: .
        setIsolationLevel (self) -> None: .

    """

    def __init__(
        self,
        host:str = 'localhost',
        port:str = '5432',
        database_name:str = 'postgres',
        user_name:str = 'postgres',
        password:str = None,
        default_database:int = 'postgres',
        **kwargs
    ):
        """Initiate the connection.

        Args:
            host (str, optional): Server's host. Defaults to 'localhost'.
            port (str, optional): Server's port. Defaults to '5432'.
            database_name (str, optional): Database name. Defaults to 'postgres'.
            user_name (str, optional): User name. Defaults to 'postgres'.
            password (str, optional): Password. Defaults to None.
            dialect (str, optional): Dialect. Defaults to 'PostgreSQL'.
        """
        self.database_name = database_name
        self.default_database = default_database


        self.host = os.getenv('host',host)
        self.port = os.getenv('port',port)
        self.password = os.getenv('PASSWORD',password)
        
        self.user_name = user_name if user_name != 'postgres' else normalize_user_name(
            os.getenv(
                'username',
                user_name
            )
        )
        
        self.connect(**kwargs)
    
    @property
    def connection_string(self) -> str:
        """Get connection string.

        Returns:
            str: Connection string.
        """
        return  "postgresql+psycopg2://{}:{}@{}:{}/{}".format(
            self.user_name,
            self.password,
            self.host,
            self.port,
            self.database_name
        )

    def getConnection(self) -> None:
        """Get connection.
        """
        self.connection = psycopg2.connect(
            database = self.database_name,
            user = self.user_name,
            host = self.host,
            password = self.password,
            port = self.port
        )

    def getCursor(self,**kwargs) -> None:
        """Get connection's cursor.
        """
        self.cursor = self.connection.cursor(**kwargs)

    def getEngine(self) -> None:
        """Get SQLAlchemy engine.
        """
        self.engine = sqlalchemy.create_engine(
            self.connection_string
        )

    def connect(self,**kwargs) -> None:
        """Connect to the database.

        Raises:
            TypeError: _description_
            TypeError: _description_

        Returns:
            object: self
        """
        self.getConnection()
        self.getCursor(**kwargs)
        self.getEngine()

    def close(self) -> None:
        """Close the connected object.
        """
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        if self.engine:
            self.engine.dispose()
    
    def registerToPostgis(self) -> None:
        """Register to Postgis.
        """
        postgis.register(self.cursor)

    def setIsolationLevel(
        self,
        level:str = 'default'
    ) -> None:
        """Set the isolation level.

        Args:
            level (str, optional): Level to set. Defaults to auto.
        """
        self.connection.set_isolation_level(
            {
                'auto':ISOLATION_LEVEL_AUTOCOMMIT,
                'default':ISOLATION_LEVEL_DEFAULT
            }[level]
        )

    def setSchema(
        self,
        schema:str='public'
    ) -> None:
        """Set default schema.

        Args:
            schema (str, optional): Schema to set to default. Defaults to 'public'.
        """
        self.cursor.execute(
            "SET search_path TO "+schema
        )
        self.connection.commit()
    
    def setDatabase(
        self,
        database_name:str
    ) -> None:
        """Change the connection's database.

        Args:
            database_name (str): Database name.
        """
        self.close()
        self.database_name = database_name
        self.connect()

    def getDefaultConnection(
        self,
        default_database_name:str=None
    ) -> None:
        """Change the database connection to the default one

        Args:
            default_database_name (str, optional): Name of the default database. Defaults to None.
        """
        if default_database_name:
            self.default_database = default_database_name
            
        self.setDatabase(
            self.default_database
        )

class AsyncConnection:
    """Connection to a database.

    Attributes:
    ----------
        host (str): Server's host.
        port (str): Server's port.
        database_name (str): Database name.
        user_name (str): User name.
        password (str): Password.
        dialect (str): Dialect.
        connection_string (str) : Connection string.
        engine (object) : SQLAlchemy engine.
        connection (object) : Connection.
        cursor (object) : Connection's cursor.

    Methods:
    ----------
        getConnection (self) -> None: Get the connection.
        getCursor (self) -> None: Get the connection's cursor.
        getEngine (self) -> None: Get SQLAlchemy engine.
        connectActions (self) -> None: Get the connection, cursor and engine.
        connect (self) -> None: Connect to the database.
        close (self) -> None: a .
        registerToPostgis (self) -> None: .
        setIsolationLevel (self) -> None: .

    """

    def __init__(
        self,
        host:str = 'localhost',
        port:str = '5432',
        database_name:str = 'postgres',
        user_name:str = 'postgres',
        password:str = None,
        default_database:int = 'postgres',
        **kwargs
    ):
        """Initiate the connection.

        Args:
            host (str, optional): Server's host. Defaults to 'localhost'.
            port (str, optional): Server's port. Defaults to '5432'.
            database_name (str, optional): Database name. Defaults to 'postgres'.
            user_name (str, optional): User name. Defaults to 'postgres'.
            password (str, optional): Password. Defaults to None.
            dialect (str, optional): Dialect. Defaults to 'PostgreSQL'.
        """
        self.database_name = database_name
        self.default_database = default_database


        self.host = os.getenv('host',host)
        self.port = os.getenv('port',port)
        self.password = os.getenv('PASSWORD',password)
        
        self.user_name = user_name if user_name != 'postgres' else normalize_user_name(
            os.getenv(
                'username',
                user_name
            )
        )
        
    @property
    def connection_string(self) -> str:
        """Get connection string.

        Returns:
            str: Connection string.
        """
        return  "postgresql+asyncpg://{}:{}@{}:{}/{}".format(
            self.user_name,
            self.password,
            self.host,
            self.port,
            self.database_name
        )

    async def connect(self,**kwargs) -> None:
        """Connect to the database.

        Raises:
            TypeError: _description_
            TypeError: _description_

        Returns:
            object: self
        """
        await self.getConnection()
        self.getEngine()

    async def getConnection(self) -> None:
        """Get connection.
        """
        self.connection:asyncpg.connection.Connection = await asyncpg.connect(
            database = self.database_name,
            user = self.user_name,
            host = self.host,
            password = self.password,
            port = self.port
        )

    def getEngine(self) -> None:
        """Get SQLAlchemy engine.
        """
        self.engine = create_async_engine(
            self.connection_string
        )
        self.async_session = async_sessionmaker(self.engine, expire_on_commit=False)

    async def close(self) -> None:
        await self.connection.close()
        await self.engine.dispose()

    async def setSchema(
        self,
        schema:str='public'
    ) -> None:
        """Set default schema.

        Args:
            schema (str, optional): Schema to set to default. Defaults to 'public'.
        """
        await self.connection.execute(
            "SET search_path TO "+schema
        )
    
    async def setDatabase(
        self,
        database_name:str
    ) -> None:
        """Change the connection's database.

        Args:
            database_name (str): Database name.
        """
        await self.close()
        self.database_name = database_name
        await self.connect()

    async def getDefaultConnection(
        self,
        default_database_name:str=None
    ) -> None:
        """Change the database connection to the default one

        Args:
            default_database_name (str, optional): Name of the default database. Defaults to None.
        """
        if default_database_name:
            self.default_database = default_database_name
            
        await self.setDatabase(
            self.default_database
        )
