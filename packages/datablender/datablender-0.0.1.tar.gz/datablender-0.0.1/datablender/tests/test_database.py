"""
"""
import unittest
import pandas
import asyncio

from datablender.base import (
    Connection,
    QueryBuilder,
    DataConfiguration,
    AsyncConnection,
    Data
)

from datablender.database import (
    DatabaseElement,
    SchemaElement,
    Table,
    View,
    Database,
    Function,
    Extension,
    Role,
    AsyncDatabase,
    AsyncTable
)

class TestDatabaseElement(unittest.TestCase):

    def setUp(self):
        
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)
        self.data_config = DataConfiguration(active=False)

    def tearDown(self):

        self.connection.close()
        if self.data_config.active:
            self.data_config.deleteAllElements()

    def testInitiation(self):
        test_database = DatabaseElement(
            self.connection,
            'test',
            'database'
        )
        self.assertTrue(not test_database.db_element)
        self.assertEqual(
            test_database.name,
            'test'
        )
        self.assertEqual(
            test_database.status,
            'default'
        )
    
    def testInitiationWithConfig(self):
        
        self.data_config.active = True
        self.data_config.activate()

        self.data_config.postElement(
            {
                'name':'test',
                'owner':'postgres',
                'status':'developpement'
            },
            'schema'
        )      

        test_schema = DatabaseElement(
            self.connection,
            'test',
            'schema',
            data_configuration=self.data_config
        )
        
        self.assertTrue(
            len(test_schema.config_element) != 0
        )
        
class TestSchemaElement(unittest.TestCase):

    def setUp(self):
        
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)
        self.data_config = DataConfiguration(active=False)
        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()

    def tearDown(self):

        self.connection.close()
        if self.data_config.active:
            self.data_config.deleteAllElements()

    def testInitiation(self):

        test_schema = SchemaElement(
            self.connection,
            'test',
            'table'
        )

        self.assertTrue(not test_schema.db_element)
        self.assertEqual(test_schema.name,'test')
        self.assertEqual(test_schema.status,'default')

    def testInitiationWithConfig(self):
        self.data_config.active = True
        self.data_config.activate()

        self.data_config.postElement(
            {
                'name':'test',
                'schema_id':1,
                'owner':'postgres',
                'status':'developpement'
            },
            'table'
        )      

        test_table = SchemaElement(
            self.connection,
            'test',
            element_type='table',
            data_configuration=self.data_config
        )

        self.assertTrue(
            len(test_table.config_element) != 0
        )
        
class TestTable(unittest.TestCase):

    def setUp(self):
        
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)
        self.data_config = DataConfiguration(active=False)

        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()

        self.query_builder.drop(
            "test_table",
            "table",
            exists_condition=True
        ).built().execute()

    def tearDown(self):
        
        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()

        self.query_builder.drop(
            "test_table",
            "table",
            exists_condition=True
        ).built().execute()

        self.connection.close()
        if self.data_config.active:
            self.data_config.deleteAllElements()

    def testInitiation(self):

        Table(
            self.connection,
            'test_table',
            columns =  [
                {
                    "name": "id",
                    "type": "int",
                    'constraints':[
                        {
                            'name':'id_not_null',
                            'type':'not_null'
                        }
                    ]
                },
                {
                    "name": "file",
                    "type": "text",
                    'constraints':[
                        {
                            'name':'file_not_null',
                            'type':'not_null'
                        }
                    ]
                }
            ],
            constraints=[
                {
                    "name":"unique_constraint",
                    "type":"unique",
                    "columns":[
                        "id",
                        "file"
                    ]
                }
            ]
        ).manage()

        self.assertIn(
            'test_table',
            self.query_builder.selectElements(
                'table'
            ).execute()['name'].values
        )

    def testSelectData(self):

        test_table =Table(
            self.connection,
            'test_table',
            columns =  [
                {
                    "name": "id",
                    "type": "int",
                    'has_not_null_constraint': False
                },
                {
                    "name": "file",
                    "type": "text",
                    'has_not_null_constraint': False
                }
            ],
            constraints=[
                {
                    "name":"unique_constraint",
                    "type":"unique",
                    'clause': None,
                    "columns":[
                        "id",
                        "file"
                    ],
                    'reference_columns': None,
                    'reference_table_name': None,
                    'reference_schema_name': None
                }
            ]
        ).manage()

        test_table.select()

        self.assertIsInstance(
            test_table.data.frame,
            pandas.DataFrame
        )

    def testInsertData(self):

        test_table =Table(
            self.connection,
            'test_table',
            columns =  [
                {
                    "name": "id",
                    "type": "int",
                    'has_not_null_constraint': False
                },
                {
                    "name": "file",
                    "type": "text",
                    'has_not_null_constraint': False
                }
            ],
            constraints=[
                {
                    "name":"unique_constraint",
                    "type":"unique",
                    'clause': None,
                    "columns":[
                        "id",
                        "file"
                    ],
                    'reference_columns': None,
                    'reference_table_name': None,
                    'reference_schema_name': None
                }
            ]
        ).manage()

        test_table.insert({
            'id':1,
            'file':'test.csv'
        })

        test_table.select()

        self.assertEqual(
            test_table.data.frame.iloc[0,0],
            1
        )
    
    def testDeleteData(self):

        test_table =Table(
            self.connection,
            'test_table',
            columns =  [
                {
                    "name": "id",
                    "type": "int",
                    'has_not_null_constraint': False
                },
                {
                    "name": "file",
                    "type": "text",
                    'has_not_null_constraint': False
                }
            ],
            constraints=[
                {
                    "name":"unique_constraint",
                    "type":"unique",
                    'clause': None,
                    "columns":[
                        "id",
                        "file"
                    ],
                    'reference_columns': None,
                    'reference_table_name': None,
                    'reference_schema_name': None
                }
            ]
        ).manage()

        test_table.insert({
            'id':1,
            'file':'test.csv'
        })
        
        test_table.delete([{
            "name":'id',
            "value":1
        }])

        test_table.select()

        self.assertEqual(
            test_table.data.frame.shape[0],
            0
        )
    
    def testUpdate(self):

        test_table =Table(
            self.connection,
            'test_table',
            columns =  [
                {
                    "name": "id",
                    "type": "int",
                    'has_not_null_constraint': False
                },
                {
                    "name": "file",
                    "type": "text",
                    'has_not_null_constraint': False
                }
            ],
            constraints=[
                {
                    "name":"unique_constraint",
                    "type":"unique",
                    'clause': None,
                    "columns":[
                        "id",
                        "file"
                    ],
                    'reference_columns': None,
                    'reference_table_name': None,
                    'reference_schema_name': None
                }
            ]
        ).manage()

        test_table.insert({
            'id':1,
            'file':'test.csv'
        })

        test_table.update( {
            "id":2
        })
        
        test_table.select()
        
        self.assertEqual(
            test_table.data.frame.iloc[0,0],
            2
        )
    
    def testInitiationWithDataConfig(self):

        self.data_config.active = True 
        self.data_config.activate()

        test_table = Table(
            self.connection,
            'test_table',
            columns =  [
                {
                    "name": "id",
                    "type": "int",
                    'constraints':[
                        {
                            'name':'id_not_null',
                            'type':'not_null'
                        }
                    ]
                },
                {
                    "name": "file",
                    "type": "text",
                    'constraints':[
                        {
                            'name':'file_not_null',
                            'type':'not_null'
                        }
                    ]
                }
            ],
            constraints=[
                {
                    "name":"unique_constraint",
                    "type":"unique",
                    'clause': None,
                    "columns":[
                        "id",
                        "file"
                    ],
                    'reference_columns': None,
                    'reference_table_name': None,
                    'reference_schema_name': None
                }
            ],
            data_configuration=self.data_config
        ).manage()

        self.assertIn(
            'test_table',
            self.query_builder.selectElements(
                'table'
            ).execute()['name'].values
        )

        self.assertEqual(
            'test_table',
            getattr(
                test_table.data_configuration,
                'table'
            )[0]['name']
        )

class TestView(unittest.TestCase):

    def setUp(self):
        
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)
        self.data_config = DataConfiguration(active=False)

        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()

        self.query_builder.drop(
            'test_view',
            'view',
            exists_condition=True,
            is_materialized=False
        ).built().execute()

    def tearDown(self):
        
        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()

        self.query_builder.drop(
            'test_view',
            'view',
            exists_condition=True,
            is_materialized=False
        ).built().execute()

        self.query_builder.drop(
            'test_',
            'view',
            exists_condition=True,
            is_materialized=False
        ).built().execute()

        self.connection.close()
        if self.data_config.active:
            self.data_config.deleteAllElements()

    def testInitiation(self):

        test_view =View(
            self.connection,
            'test_view',
            'select * from pg_database'
        ).manage()
        
        self.assertIn(
            'test_view',
            self.query_builder.selectElements(
                'view'
            ).execute()['name'].values
        )

    def testInitiationWithSelectStatement(self):

        test_view =View(
            self.connection,
            'test_view',
            file_query='test_',
            directory_query='datablender/tests/tests_requirements'
        ).manage()

        self.assertIn(
            32188,
            test_view.select().data.frame['srid'].values
        )
        self.assertIn(
            'test_view',
            self.query_builder.selectElements(
                'view'
            ).execute()['name'].values
        )

    def testInitiationWithName(self):

        test_view =View(
            self.connection,
            'test_'
        ).manage()

        self.assertIn(
            32188,
            test_view.select().data.frame['srid'].values
        )

        self.assertIn(
            'test_',
            self.query_builder.selectElements(
                'view'
            ).execute()['name'].values
        )

class TestDatabase(unittest.TestCase):

    def setUp(self):
        
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)
        self.data_config = DataConfiguration(active=False)

        self.connection.setIsolationLevel('auto')
        self.query_builder.drop(
            "test",
            "database",
            exists_condition=True
        ).built().execute(False)
        self.connection.setIsolationLevel()

    def tearDown(self):
        self.connection.setDatabase(
            self.connection.default_database
        )

        self.connection.setIsolationLevel('auto')
        self.query_builder.drop(
            "test",
            "database",
            exists_condition=True
        ).built().execute(False)
        self.connection.setIsolationLevel()

        self.connection.close()
        if self.data_config.active:
            self.data_config.deleteAllElements()

    def testInitiation(self):
       
        test_database = Database(
            self.connection,
            'test'
        )
        
        self.assertEqual(test_database.name,'test')
        self.assertEqual(test_database.status,'test')

    def testManageDefaultsElements(self) -> None:

        test_database = Database(
            self.connection,
            'test'
        )
        test_database.manageDefaultsElements()
        print(test_database.extension)

    def testInitiationWithConnection(self):

        test_database = Database(
            self.connection,
            'test'
        ).manage()

        self.assertTrue(
            test_database.connection.database_name,
            'test'
        )

    def testDatabaseWithDataConfig(self):
        self.data_config.active = True
        self.data_config.activate()

        owner_id = self.data_config.postElement(
            {
                'name':'postgres',
                'status':'production',
                'is_superuser':True,
                'can_create_database':True
            },
            'role'
        )
        schema_id = self.data_config.postElement({
            'name':'transit_services',
            'status':'test',
            'schema_type':'source',
            'content':None,
            'owner_id':owner_id,
            'grants':[
                {
                  "privilege": "usage",
                  "user_name": "postgres"
                },
                {
                  "privilege": "create",
                  "user_name": "postgres"
                }
            ]
        },'schema')

        self.data_config.postElement(
            {
                'name':'stops',
                'status':'test',
                'columns':[
                    {
                        'name':'id',
                        'type':'int'
                    }
                ],
                "constraints":[],
                "indexes":[],
                "grants":[],
                "content":None,
                'schema_id':schema_id,
                'owner_id':owner_id
            },
            'table'
        )
        self.data_config.postElement(
            {
                'name':'stops_',
                'query':'select * from transit_services.stops;',
                'status':'test',
                'is_materialized':False,
                'indexes':[],
                'grants':[],
                'content':None,
                'schema_id':schema_id,
                'owner_id':owner_id
            },
            'view'
        )

        test_database = Database(
            self.connection,
            'test',
            data_configuration=self.data_config
        ).manage()

        test_database.createElements('schema')
        transit_services_schema = test_database.getElement({'name':'transit_services'},'schema')

        transit_services_schema.createElements('table')
        transit_services_schema.createElements('view')
        
        self.assertIn(
            'transit_services',
            test_database.query_builder.selectElements(
                'schema'
            ).execute()['name'].values
        )

        self.assertIn(
            'stops',
            test_database.query_builder.selectElements(
                'table'
            ).execute()['name'].values
        )
        
        self.assertIn(
            'stops_',
            test_database.query_builder.selectElements(
                'view'
            ).execute()['name'].values
        )

class TestAsyncDatabase(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()

    def testInitiation(self):
       
        async def asynctest(loop:asyncio.AbstractEventLoop) -> None:
            connection = AsyncConnection()
            await connection.connect()
            test_database = AsyncDatabase(
                connection,
                'test_database'
            )
            await test_database.initiate()
            await test_database.manage()


            await connection.close()

        self.loop.run_until_complete(asynctest(self.loop))

    def testDrop(self):
       
        async def asynctest(loop:asyncio.AbstractEventLoop) -> None:
            connection = AsyncConnection()
            await connection.connect()
            test_database = AsyncDatabase(
                connection,
                'test_database'
            )
            await test_database.initiate()
            await test_database.manage()

            await test_database.drop()
            
            await connection.close()

        self.loop.run_until_complete(asynctest(self.loop))

class TestAsyncTable(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()

    def testInitiation(self):
       
        async def asynctest(loop:asyncio.AbstractEventLoop) -> None:
            connection = AsyncConnection()
            await connection.connect()
            table = AsyncTable(
                connection,
                'test_table'
            )
            await table.initiate()
            data = Data(
                pandas.DataFrame(
                    {'col1': [1, 2], 'col2': [3, 4]}
                )
            )
            await table.manage('values',data=data)
            await table.copy()
            await connection.close()

        self.loop.run_until_complete(asynctest(self.loop))



