"""
"""
import unittest

import numpy
import pandas
import geopandas
import asyncpg
import asyncio

from shapely.geometry.point import Point

from selenium.webdriver.common.by import By

from datablender.base import (
    File,
    ZipFile_,
    getNextID,
    Bot,
    BotAction,
    WebElement,
    Request,
    Connection,
    QueryBuilder,
    DataLogging,
    DataEventsTable,
    DataConfiguration,
    DataElement,
    Data,
    AsyncDataConfiguration,
    AsyncConnection,
    AsyncDataEventsTable,
    AsyncDataLogging
)

class TestFile(unittest.TestCase):

    def testFileInformations(self):
        file = File(
            'datablender/tests/tests_requirements/',
            'test.csv'
        )
        self.assertEqual(file.name ,'test.csv')
        self.assertEqual(file.extension ,'csv')
    
    def testReadCSV(self) -> None:
        file = File(
            'datablender/tests/tests_requirements/',
            'test.csv'
        )
        file.read()
        self.assertEqual(file.content['id'].values.tolist()[0],1)
    
    def testReadSHP(self) -> None:
        file = File(
            'datablender/tests/tests_requirements/',
            'EOD2018_update.shp'
        )
        file.read(nrows = 5)
        self.assertIsInstance(
            file.content,
            geopandas.GeoDataFrame
        )
        self.assertEqual(file.content.shape[0],5)

    def testReadDBF(self) -> None:
        file = File(
            'datablender/tests/tests_requirements/',
            'jonctions_etude.dbf'
        )
        file.read(nrows = 0)
        self.assertIsInstance(
            file.content,
            pandas.DataFrame
        )
        self.assertEqual(file.content.shape[0],0)

    def testReadExcelWithSheetName(self) -> None:
        
        file = File(
            'datablender/tests/tests_requirements/',
            'test.xlsx'
        )
        file.read(sheet_name = 'Feuil1')
        self.assertEqual(file.content['id'].values.tolist()[0],1)

    def testReadExcelWithoutSheetName(self) -> None:
        
        file = File(
            'datablender/tests/tests_requirements/',
            'test.xlsx'
        )
        file.read()
        self.assertEqual(file.content['id'].values.tolist()[0],1)

    def testReadExcelWithSheets(self) -> None:
        
        file = File(
            'datablender/tests/tests_requirements/',
            'test.xlsx'
        )
        file.read(sheets=['Feuil1','Feuil2'])
        print(file.content)
        self.assertEqual(file.content['id'].values.tolist(),[1,2])

    def testReadExcelWithSheetsConfig(self) -> None:
        
        file = File(
            'datablender/tests/tests_requirements/',
            'test.xlsx'
        )
        file.read(
            sheets=[
                {
                    'sheet_name':'Feuil3',
                    'usecols':'B:D',
                    'skiprows':3
                },
                {
                    'sheet_name':'Feuil3',
                    'usecols':'G:I',
                    'skiprows':3
                },
                {
                    'sheet_name':'Feuil4',
                    'usecols':'B:D',
                    'skiprows':4
                },
                {
                    'sheet_name':'Feuil4',
                    'usecols':'G:I',
                    'skiprows':4
                }
            ]
        )
        self.assertEqual(file.content['id'].values.tolist(),[1,2,3,4])

class TestZipFile_(unittest.TestCase):

    def testFileInformations(self):

        file = ZipFile_(
            'test.zip',
            'datablender/tests/tests_requirements/'
        )
        self.assertEqual(
            file.namelist()[0],
            'test1/test1.csv'
        )
        
class testGetNextID(unittest.TestCase):
    
    def testGetNextID(self):
        next_id = getNextID([
            {
                'id':1
            },
            {
                'id':2
            },
            {
                'id':4
            }
        ])
        self.assertEqual(next_id,3)

    def testGetNextIDEmpty(self):
        next_id = getNextID([])
        self.assertEqual(next_id,1)

class TestWebElement(unittest.TestCase):

    def testMark(self):
        web_element = WebElement('a')
        self.assertEqual(
            web_element.mark,
            (By.TAG_NAME,'a')
        )

    def testMark1(self):
        web_element = WebElement('a',None,{'id':'1'})
        self.assertEqual(web_element.mark,(By.XPATH,"//a[@id='1']"))

    def testMark2(self):
        web_element = WebElement('a','test')

        self.assertEqual(
            web_element.mark,
            (By.XPATH,"//a[text()='test']")
        )
    
    def testSetValue(self):
        web_element = WebElement(
            'a',
            None,
            {'href':'/p/__possible_value__'}
        )
        web_element.setValue(
            'agence-metropolitaine-de-transport',
            'href'
        )
        self.assertEqual(
            web_element.mark,
            (By.XPATH,"//a[@href='/p/agence-metropolitaine-de-transport']")
        )
    
class TestWebBotAction(unittest.TestCase):

    def testInitiation(self):
        bot_action = BotAction(
            'https://transitfeeds.com',
            'click_button',
            tag_name='a',
            attributes={'href':'/p/__possible_value__'}
        )
        self.assertEqual(
            bot_action.web_element.mark,
            (By.XPATH,"//a[@href='/p/__possible_value__']")
        )

class TestWebBot(unittest.TestCase):

    def setUp(self):
        self.bot =Bot(domain_name='transitfeeds.com')
        self.bot.open()

    def tearDown(self):
        self.bot.close()

    def testBot(self):
        self.assertTrue(
            hasattr(self.bot,'driver')
        )

    def testBotWithUrl(self):

        self.bot.get('https://transitfeeds.com/l/54-quebec-canada')
        self.bot.clickButton(
            (By.XPATH,"//a[@href='/p/agence-metropolitaine-de-transport']")
        )
        self.assertEqual(
            self.bot.driver.current_url,
            'https://transitfeeds.com/p/agence-metropolitaine-de-transport'
        )
    
    def testFindElements(self):
        self.bot.get('https://transitfeeds.com/p/agence-metropolitaine-de-transport/128')
        elements = self.bot.findElements((By.XPATH,"//a[@class='btn btn-xs btn-primary']"))

        # self.assertTrue(
        #     elements[0].attributes['class'],
        #     'btn btn-xs btn-primary'
        # )

    def testBotAction(self):
        self.bot.domain_name = 'transitfeeds.com'

        bot_action = BotAction(
            'https://transitfeeds.com',
            'click_button',
            tag_name='a',
            attributes={'href':'/p/agence-metropolitaine-de-transport'}
        )
        self.bot.get('https://transitfeeds.com/l/54-quebec-canada')
        self.bot.executeAction(bot_action)
        self.assertEqual(
            self.bot.driver.current_url,
            'https://transitfeeds.com/p/agence-metropolitaine-de-transport'
        )

    def testManageAction(self):
        self.bot.domain_name = 'transitfeeds.com'
        bot_action = BotAction(
            'https://transitfeeds.com',
            'click_button',
            tag_name='a',
            attributes={
                'href':'/p/__possible_value__',
                'class':'btn btn-xs btn-success'
            },
            multi_mode='replace',
            attribute_name='href',
            values=[
                'agence-metropolitaine-de-transport',
                'reseau-de-transport-de-longueuil',
                'societe-de-transport-de-laval',
                'societe-de-transport-de-montreal'
            ]
        )

        self.bot.get('https://transitfeeds.com/l/54-quebec-canada')
        self.bot.manageAction(bot_action)
        self.assertTrue(
            self.bot.driver.current_url,
            'https://transitfeeds.com/p/societe-de-transport-de-montreal'
        )
    
    def testBotActions(self):
        self.bot.domain_name = 'transitfeeds.com'
        actions = [
            {
                'name':'get',
                'url_path':'/l/54-quebec-canada'
            },
            {
                'name':'click_button',
                'tag_name':'a',
                'attributes': {
                    'href':'/p/agence-metropolitaine-de-transport'
                }
            }
        ]
        self.bot.executeActions(actions)
        self.assertEqual(
            self.bot.driver.current_url,
            'https://transitfeeds.com/p/agence-metropolitaine-de-transport'
        )

    def testBotActionsWithElements(self):
        self.bot.domain_name = 'transitfeeds.com'
        actions = [
            {
                'name':'get',
                'url_path':'/l/54-quebec-canada'
            },
            {
                'name':'click_button',
                'tag_name':'a',
                'attributes': {
                    'href':'/p/__possible_value__',
                    'class':'btn btn-xs btn-success'
                },
                'multi_mode':'replace',
                'attribute_name':'href',
                'values':[
                    'agence-metropolitaine-de-transport'
                    #'reseau-de-transport-de-longueuil',
                    #'societe-de-transport-de-laval',
                    #'societe-de-transport-de-montreal'
                ]
            },
            {
                'name':'click_button',
                'tag_name':'a',
                'attributes':{
                    'href':'/p/__possible_value__',
                    'class':'list-group-item'
                },
                'multi_mode':'replace',
                'attribute_name':'href',
                'values':{
                    'agence-metropolitaine-de-transport':[
                        'agence-metropolitaine-de-transport/129',
                        'agence-metropolitaine-de-transport/128'
                        #'agence-metropolitaine-de-transport/130',
                        #'agence-metropolitaine-de-transport/131',
                        #'agence-metropolitaine-de-transport/132',
                        #'agence-metropolitaine-de-transport/133',
                        #'agence-metropolitaine-de-transport/134',
                        #'agence-metropolitaine-de-transport/135',
                        #'agence-metropolitaine-de-transport/136',
                        #'agence-metropolitaine-de-transport/137',
                        #'agence-metropolitaine-de-transport/138',
                        #'agence-metropolitaine-de-transport/139',
                        #'agence-metropolitaine-de-transport/140',
                        #'agence-metropolitaine-de-transport/141',
                        #'agence-metropolitaine-de-transport/142',
                        #'agence-metropolitaine-de-transport/143'
                    ]
                    # 'reseau-de-transport-de-longueuil':[
                    #     'reseau-de-transport-de-longueuil/37'
                    # ],
                    # 'societe-de-transport-de-laval':[
                    #     'societe-de-transport-de-laval/38'
                    # ],
                    # 'societe-de-transport-de-montreal':[
                    #     'societe-de-transport-de-montreal/39'
                    # ]
                }
            },
            {
                'name':'find_elements',
                'tag_name':'a',
                'attributes':{
                    'class':'btn btn-xs btn-primary'
                },
                'multi_mode':'get',
                'attribute_name':'href'
            },
            {
                'name':'click_button',
                'tag_name':'a',
                'element_text':'__possible_value__',
                'multi_mode':'iterate',
                'attribute_name':'text',
                'start_value':2,
                'execute_previous_action':True
            }
        ]
        self.bot.executeActions(actions)
        print(self.bot.results)
        print(self.bot.driver.current_url)

    def testBotActionsWithElements1(self):
        self.bot.domain_name = 'bixi.com'
        self.bot.executeActions([
            {
                'name':'get',
                'url_path':'/fr/donnees-ouvertes'
            },
            {
                'name':'find_elements',
                'tag_name':'a',
                'attributes':{
                    'class':'button button-primary ',
                    'target':'_blank',
                    'rel':'noopener'
                },
                'multi_mode':'get',
                'attribute_name':'href'
            }
        ])

        self.assertIn(
            'https://s3.ca-central-1.amazonaws.com/cdn.bixi.com/wp-content/uploads/2023/06/Historique-BIXI-2014.zip',
            self.bot.results
        )

        self.assertEqual(
            self.bot.driver.current_url,
            'https://bixi.com/fr/donnees-ouvertes'
        )
    
    def testBotActionsWithElements2(self):
        self.bot.domain_name = 'bixi.com'
        actions = [
            {
                'name':'get',
                'url_path':'/fr/donnees-ouvertes'
            },
            {
                'name':'find_elements',
                'tag_name':'a',
                'attributes':{
                    'class':'document-csv col-md-2 col-sm-4 col-xs-12'
                },
                'multi_mode':'get',
                'attribute_name':'href'
            }
        ]
        self.bot.executeActions(actions)
        print(self.bot.results)
        print(self.bot.driver.current_url)

class TestRequest(unittest.TestCase):

    def setUp(self):
        self.request = Request(port=3000)
        self.deleteAll()

    def tearDown(self) -> None:
        
        self.deleteAll()
    
    def deleteAll(self) -> None:
        element_types = [
          "docs",
          "role",
          "extension",
          "schema",
          "table",
          "function",
          "view",
          "data_source",
          "process",
          "visualizations"
        ]
        for element_type in element_types:
            self.request.addElement(element_type)
            self.request.get()
            response = self.request.response.json()
            self.request.reset()
            for element in response:
                self.request.addElement(element_type)
                self.request.addElement(str(element['id']))
                self.request.delete()
                self.request.reset()

    def testRequestInitiation(self):
        self.assertEqual(
            self.request.base_url,
            'http://localhost:3000'
        )
        self.assertEqual(
            self.request.url,
            'http://localhost:3000'
        )

    def testAddElement(self):
        self.request.addElement('schema')
        self.assertEqual(
            self.request.url,
            'http://localhost:3000/schema'
        )
   
    def testPostDeleteElement(self):

        self.request.addElement('schema')
        self.request.post(
            json={'name':'test','array':[0,0,0]}
        )

        self.request.get(params={'id':1})
        schemas = self.request.response.json()
        
        self.assertEqual(
            schemas,
            [{'name': 'test', 'array': [0, 0, 0], 'id': 1}]
        )

        self.request.addElement('1')
        self.request.delete()

    def testGetElement(self) -> None:

        self.request.addElement('schema')

        self.request.get()
        response = self.request.response.json()
        
        self.assertIsInstance(response,list)

    def testOSM(self):
        # request = Request(domain_name='overpass-api.de')
        # request.addElement('api/interpreter')
        # overpass_query = """
        # [out:json];
        # area["name"="Saint-Bruno-de-Montarville"];
        # (node(area););
        # out body;
        # """
        # request.get(params={'data': overpass_query})
        # data = request.response.json()
        # nodes=[element for element in data['elements'] if element['type']=='node']
        # ways = [element for element in data['elements'] if element['type']=='way']
        # for node in nodes:
        #     print(node)
        #     break
        # for way in ways:
        #     print(way)
        #     break
        test = [
            *[{
                'type': 'way',
                'id': 15240109,
                'nodes': [150958228, 453157995],
                'tags': {'highway': 'tertiary', 'lanes': '2', 'name': 'Boulevard Clairevue Ouest', 'oneway': 'yes'}
            }],
            *[{'type': 'node', 'id': 16874517, 'lat': 45.5182399, 'lon': -73.3718366}]
        ]
        print(pandas.DataFrame(iter(test)).columns)
    
    def testOSRM(self) -> None:
        request = Request(domain_name='router.project-osrm.org')
        request.addElement('route/v1/driving')
        request.addElement('-73.60587658959338,45.54381145173219;-73.5968311623849,45.54422175812567?steps=true&geometries=geojson')
        request.get()
        print(request.response.json())
        return

class TestConnection(unittest.TestCase):

    def setUp(self):
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)

    def tearDown(self):
        self.connection.close()

    def testConnection(self):
        self.assertTrue(hasattr(
            self.connection,
            'connection'
        ))
    
    def testSetDatabase(self):
        self.connection.setDatabase('postgres')
        self.assertEqual(
            self.connection.database_name,
            'postgres'
        )

class TestQueryBuilder(unittest.TestCase):

    def setUp(self):
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)

    def tearDown(self):
        self.connection.close()

    def testSqlStatement(self):
        self.query_builder.sqlStatement(
            directory_name='datablender/tests/tests_requirements/',
            file_name='test.sql'
        ).built()
        
        self.assertEqual(
            ' '.join(self.query_builder.text_elements),
            'select *\nfrom files \n;'
        )
    
    def testSqlStatementWithoutSQL(self):
        self.query_builder.sqlStatement(
            directory_name='datablender/tests/tests_requirements/',
            file_name='test'
        ).built()
        
        self.assertEqual(
            ' '.join(self.query_builder.text_elements),
            'select *\nfrom files \n;'
        )

    def testBuiltCreate(self):

        self.query_builder.create(
            'files',
            'table',
            'public'
        ).columns(
            columns =  [
                {
                    "name": "id",
                    "type": "int"
                },
                {
                    "name": "file",
                    "type": "text"
                }
            ]
        ).built()
        
        self.assertEqual(
            ' '.join(self.query_builder.text_elements),
            "create table public.files (\n id int  ,\n	file text   \n) \n;"
        )
    
    def testBuiltCreateWithConstraints(self):
        query_builder = QueryBuilder(Connection())

        query_builder.create(
            'files',
            'table',
            'public'
        ).columns(
            columns =  [
                {
                    "name": "id",
                    "type": "int"
                },
                {
                    "name": "file",
                    "type": "text"
                }
            ]
        ).constraints(
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
        ).built()
        self.assertEqual(
            ' '.join(query_builder.text_elements),
            "create table public.files (\n id int  ,\n	file text   ,\n CONSTRAINT unique_constraint unique (id,file)     \n) \n;"
        )
        query_builder.connection.close()
    
    def testSelectElement(self):
        query_builder = QueryBuilder(Connection())
        query_builder.selectElements('database')
        self.assertEqual(
            ' '.join(query_builder.text_elements)[0:24],
            'select\n\ta.datname "name"'
        )
        query_builder.connection.close()
    
    def testSelectCurrentDatabse(self):
        query_builder = QueryBuilder(Connection())
        query_builder.select().currentDatabase().built()
        self.assertEqual(
            ' '.join(query_builder.text_elements),
            'select current_database() \n;'
        )
        query_builder.connection.close()

    def testExectuteCreate(self):
        query_builder = QueryBuilder(Connection())
        query_builder.drop(
            "test_table",
            "table",
            exists_condition=True
        ).built().execute()

        query_builder.create(
            "test_table",
        ).columns(
            columns = [
                {
                    "name": "id",
                    "type": "int"
                },
                {
                    "name": "file",
                    "type": "text"
                }
            ]
        ).built().execute()

        tables = query_builder.selectElements("table").execute()
        self.assertIn(
            'test_table',
            tables['name'].values
        )

        query_builder.drop(
            "test_table",
            "table"
        ).built().execute()

        query_builder.connection.close()

    def testSelect(self):
        query_builder = QueryBuilder(Connection())
        query_builder.drop(
            "test_table",
            "table",
            exists_condition=True
        ).built().execute()

        query_builder.create(
            "test_table",
        ).columns(
            columns = [
                {
                    "name": "id",
                    "type": "int"
                },
                {
                    "name": "file",
                    "type": "text"
                }
            ]
        ).built().execute()

        df = query_builder.select(
            "test_table"
        ).columns([
            {
                "name": "id",
                "type": "int"
            },
            {
                "name": "file",
                "type": "text"
            }
        ]).built().execute()
        self.assertIsInstance(df,pandas.DataFrame)

        query_builder.drop(
            "test_table",
            "table"
        ).built().execute()
        query_builder.connection.close()
    
    def testSelectWithWhere(self):
        query_builder = QueryBuilder(Connection())
        query_builder.drop(
            "test_table",
            "table",
            exists_condition=True
        ).built().execute()

        query_builder.create(
            "test_table",
        ).columns(
            columns = [
                {
                    "name": "id",
                    "type": "int"
                },
                {
                    "name": "file",
                    "type": "text"
                }
            ]
        ).built().execute()

        df = query_builder.select(
            "test_table"
        ).columns([
            {
                "name": "id",
                "type": "int"
            },
            {
                "name": "file",
                "type": "text"
            }
        ]).where([
            {
                'name':'id',
                'value':1
            }
        ]).built().execute()
        self.assertIsInstance(df,pandas.DataFrame)

        query_builder.drop(
            "test_table",
            "table"
        ).built().execute()
        query_builder.connection.close()

    def testGrant(self):
        query_builder = QueryBuilder(Connection())
        query_builder.grant(
            'test_name',
            user_name='test_user_name'
        ).built()
        self.assertEqual(
            ' '.join(query_builder.text_elements),
            "grant select on table test_name to test_user_name \n;"
        )

class TestDataEventsTable(unittest.TestCase):

    def setUp(self):
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)

        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()

        self.table = DataEventsTable(self.connection)

    def tearDown(self):
        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()
        self.connection.close()

    def testIntiation(self):

        self.assertIn(
            'data_events',
            self.query_builder.selectElements(
                'table'
            ).execute()['name'].values
        )
    
    def testDataLog(self):

        self.table.logEvent(
            'table',
            'test',
            'create',
            'public',
            None
        )

        df = self.query_builder.select(
            "data_events"
        ).columns(
            [{'name':'element_type'}]
        ).built().execute()

        self.assertEqual(df.iloc[0,0],'table')

class TestDataLogging(unittest.TestCase):

    def setUp(self):
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)

        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()

        self.data_logging = DataLogging(self.connection)

    def tearDown(self):
        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()
        self.connection.close()

    def testIntiation(self):
        
        self.assertIn(
            'data_events',
            self.query_builder.selectElements(
                'table'
            ).execute()['name'].values
        )
    
    def testDataLog(self):

        self.data_logging.logEvent(
            'table',
            'test',
            'create'
        )

        df = self.query_builder.select(
            "data_events"
        ).columns(
            [{'name':'element_type'}]
        ).built().execute()

        self.assertEqual(
            df.iloc[0,0],
            'table'
        )

class TestDataConfiguration(unittest.TestCase):
    
    def setUp(self):
        self.data_config = DataConfiguration()
  
    def tearDown(self):
        self.data_config.deleteAllElements()

    def testInitiation(self) -> None:
        
        self.assertEqual(
            self.data_config.storage_type,
            'server'
        )
        self.assertEqual(
            self.data_config.request.host,
            'localhost'
        )  
    
    def testPostElement(self) -> None:

        self.data_config.postElement(
            {'name':'public'},
            'schema'
        )
    
    def testGetElements(self) -> None:
        self.data_config.postElement(
            {'name':'public'},
            'schema'
        )
        self.data_config.getElements('schema')
        
        self.assertEqual(
            self.data_config.schema[0]['name'],
            'public'
        )
    
    def testGetAllElements(self):
        self.data_config.postElement(
            {'name':'public'},
            'schema'
        )
        self.data_config.getAllElements()
        self.assertEqual(
            getattr(
                self.data_config,
                'schema'
            )[0]['name'],
            'public'
        )

class TestDataElement(unittest.TestCase):

    def setUp(self):
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)

        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()

        self.data_logging = DataLogging(self.connection)

    def tearDown(self):
        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()
        self.connection.close()

    def testInitiation(self) -> None:
        data_element = DataElement(
            self.connection,
            'test_table'
        )
        self.assertEqual(
            data_element.attributes[0]['name'],
            'id'
        )
    
    def testSetCompareValueDict(self) -> None:
        data_element = DataElement(
            self.connection,
            'test_table'
        )
        self.assertEqual(
            data_element.setCompareValue({
                'name':'srid',
                'constraints':None
            }),
            {'name': 'srid'}
        )

    def testSetCompareValueList(self) -> None:
    
        data_element = DataElement(
            self.connection,
            'test_table'
        )
        self.assertEqual(
            data_element.setCompareValue(
                [
                    {
                        'name':'b',
                        'constraints':[
                            {
                                'name':'b'
                            },
                            {
                                'name':'a'
                            }
                        ]
                    },
                    {
                        'name':'a'
                    }
                ]
            ),
            [
                {'name': 'a'},
                {
                    'name': 'b',
                    'constraints': [
                        {'name': 'a'},
                        {'name': 'b'}
                    ]
                }
            ]
        )

class TestData(unittest.TestCase):

    def setUp(self):
        self.data = Data({
            'col1': [1, 2],
            'col2': [0.5, 0.75],
            'col3': ['1','2']
        })
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)

    def tearDown(self):
        self.connection.close()

    def testInitiation(self):
        self.assertEqual(
            self.data.columns[0].get('type'),
            'bigint'
        )
        self.assertEqual(
            self.data.frame.columns.values.tolist(),
            ['col1','col2','col3']
        )

    def testFormatValues(self) -> None:
        self.assertEqual(
            self.data.formatValues(
                'col1',
                self.data.frame.dtypes['col1'],
                1
            ).values[0],
            '1'
        )

    def testApplyTransformationRename(self):
        self.data.transform([{
            'name':'rename',
            'columns':{
                'col1':'COL1',
                'col2':'COL2'
            }
        }])
        self.assertEqual(
            self.data.frame.columns.values.tolist(),
            ['COL1','COL2','col3']
        )

    def testApplyTransformationToInt(self):
        self.data.transform([{
            'name':'asType',
            'column_name':'col3',
            'column_type':'int'
        }])
        self.assertEqual(
            self.data.frame.iloc[0,0],
            1
        )
        self.assertEqual(
            self.data.columns[0].get('type'),
            'bigint'
        )

    def testGeometryPostgis(self):

        self.data.transform([
            {
                'name':'toList',
                'column_name':'station',
                'column_names':['col1','col2']
            },
            {
                'name':'setType',
                'column_name':'station',
                'geometry_type':'Point'
            }
        ])

        data = self.data.export('postgres')

        self.assertEqual(
            self.data.columns[3].get('type'),
            'geometry(Point,4326)'
        )

        self.assertEqual(
            data.iloc[0,3],
            'SRID=4326;POINT (1.0 0.5)'
        )

    def testGeometryGeoJSON(self):

        self.data.transform([
            {
                'name':'toList',
                'column_name':'station',
                'column_names':['col1','col2']
            },
            {
                'name':'setType',
                'column_name':'station',
                'geometry_type':'Point'
            }
        ])

        data = self.data.export('json')

        self.assertEqual(
            self.data.columns[3].get('type'),
            'geometry(Point,4326)'
        )

        self.assertEqual(
            data[3][0],
            {
                'type': 'Feature',
                'properties': {
                    'index': 0
                },
                'geometry': {
                    'type': 'Point',
                    'coordinates': [1.0, 0.5]
                }
            }
        )

    def testTransformToList(self) -> None:
        
        self.data = Data({
            'id':[1,1,2,2],
            'longitude': [1, 1, 2, 2],
            'latitude': [0.5, 0.75,1,1]
        })
        
        self.data.transform([
            {
                'name':'toList',
                'column_name':'shape',
                'column_names':['longitude','latitude']
            },
            {
                'name':'aggregate',
                'colums_group_by':[
                    'id'
                ],
                'columns_to_group_by':{
                    'shape':'list'
                }
            },
            {
                'name':'setType',
                'column_name':'shape',
                'geometry_type':'Line'
            }
        ])
        
        data = self.data.export('json')

        self.assertEqual(
            self.data.columns[1].get('type'),
            'geometry(Line,4326)'
        )

        self.assertEqual(
            data[1][0],
            {
                'type': 'Feature',
                'properties': {
                    'index': 0
                },
                'geometry': {
                    'type': 'Line',
                    'coordinates':  [[1.0, 0.5], [1.0, 0.75]]
                }
            }
        )
  
    def testApplyTransformationParseDate(self):

        self.data = Data(
            {'start_date': ['2022-01-01 13:00:00']}
        )

        self.data.transform([{
            'name':'toDateTime',
            'column_name':'start_date',
            'format':'%Y-%m-%d %H:%M:%S'
        }])
        
        self.assertEqual(
            str(self.data.frame.iloc[0,0]),
            '2022-01-01 13:00:00'
        )

        self.assertEqual(
            self.data.columns[0].get('type'),
            'timestamp'
        )

    def testApplyFunction(self):

        self.data.transform([
            {
                'name':'getFunction',
                'function_name':'testFunction',
                'directory_name':'datablender/tests/tests_requirements/sources/public'
            },
            {
                'name':'applyFunction',
                'function_name':'testFunction',
                'input_columns':'col1',
                'output_columns':'col3'
            }
        ])
        
        self.assertEqual(
            self.data.frame.columns.values.tolist(),
            ['col1', 'col2', 'col3']
        )

    def testStrip(self) -> None:
        self.data = Data({'col1': [' ttt', 'ttt  ']})
        self.data.transform([
            {
                'name':'strip',
                'column_name':'col1'
            }
        ])

        self.assertEqual(
            self.data.frame.iloc[0,0],
            'ttt'
        )

    def testExportGeometryShapely(self) -> None:
    
        data = Data()
        self.assertEqual(
            data.exportGeometry(
                Point(1, 1),
                'json',
                'Point',
                4326,
                saved_type='shapely'
            ),
            {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': (1.0, 1.0)}}
        )
    
    def testExportGeometryGeojson(self) -> None:
    
        # data = Data()
        # self.assertEqual(
        #     data.exportGeometry(
        #        '{"type": "Point", "coordinates": [1.0, 1.0]}',
        #         'json',
        #         'Point',
        #         4326,
        #         saved_type='geojson'
        #     ),
        #     {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [1.0, 1.0]}}
        # )
        series = pandas.Series(
            [1, 2, 3, 4],
            name='foo',
            index=pandas.Index(['a', 'b', 'c', 'd'], name='idx')
        )

        def test(x,y) -> None:
            print('--')
            print(x)
            print(y)
            return x
        
        print(
        series.reset_index().apply(
            lambda x: test(*x), axis=1
        ).to_list()
        )
  
    def testGeoDataframe(self):
        file = File(
            'datablender/tests/tests_requirements/',
            'EOD2018_update.shp'
        )
        file.read()
        data = Data(file.content)

        data.export()

    def testExportInt(self) -> None:

        file = File(
            'datablender/tests/tests_requirements/',
            'test1.csv'
        )
        file.read()
        print(file.content)
        data = Data(
            file.content
        )
        data.asType(
            'attr',
            'int64'
        )
        print(data.export())
        
        # for column_name,dtype in zip(data.frame.columns,data.frame.dtypes):
        #     if str(dtype) == 'float64':

        #         self.assertEqual(
        #             [
        #                 None if pandas.isna(a) else a
        #                 for a in data.frame[column_name]
        #             ],
        #             [1,None]
        #         )

    def testExportGeometry(self) -> None:
        df = pandas.DataFrame({'id':[1,2],'x':[300728.611,283542.446],'y':[5039208.941,5039732.941]})
        data = Data(
            geopandas.GeoDataFrame(
                df, geometry=geopandas.points_from_xy(df.x, df.y), crs="EPSG:32188"
            )
        )
        data.setSrid('geometry',4326)
        print(data.export())
        
    def testExportGeography(self) -> None:

        async def asynctest(loop:asyncio.AbstractEventLoop) -> None:
            pass
            # Data(
            #     await self.query_builder.select(
            #         'links',
            #         'network',
            #         limit = 200
            #     ).columns(
            #         columns if columns else self.columns
            #     ).where(
            #         where_statement
            #     ).built().asyncExecute(
            #         data_logging=self.data_logging,
            #         **kwargs
            #     ),
            #     meta_columns=[],
            #     columns = self.columns,
            #     geometry_saved_type='text',
            #     name=self.name,
            #     loaded_rows = loaded_rows,
            # )

        loop = asyncio.get_event_loop()
        loop.run_until_complete(asynctest(loop))


class TestAsyncDataConfiguration(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):

        self.loop = asyncio.get_event_loop()

    def tearDown(self) -> None:
        pass
    
    def testGetElements(self) -> None:

        async def asynctest(loop:asyncio.AbstractEventLoop) -> None:
            data_config = AsyncDataConfiguration(loop=loop)
            await data_config.getElements('schema')
            schemas = getattr(data_config,'schema')
            await data_config.deactivate()
            return schemas

        schemas = self.loop.run_until_complete(asynctest(self.loop))
        print(schemas)
    
    def testGetAllElements(self):

        async def asynctest(loop:asyncio.AbstractEventLoop) -> None:
            data_config = AsyncDataConfiguration(loop=loop)
            await data_config.getAllElements()
            schemas = getattr(data_config,'schema')
            await data_config.deactivate()
            return schemas

        loop = asyncio.get_event_loop()
        schemas = loop.run_until_complete(asynctest(loop))
        print(schemas)

    def testPostSchema(self):

        async def asynctest(loop:asyncio.AbstractEventLoop) -> None:
            data_config = AsyncDataConfiguration(loop=loop)
            await asyncio.gather(data_config.postElement(
                {'name':'test','array':[0,0,0]},
                'schema'
            ))
            schemas = getattr(data_config,'schema')
            await data_config.deactivate()
            return schemas

        loop = asyncio.get_event_loop()
        schemas = loop.run_until_complete(asynctest(loop))
        print(schemas)

class TestAsyncConnection(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        self.loop = asyncio.get_event_loop()

    def tearDown(self) -> None:
        pass

    def testConnect(self) -> None:
    
        async def asynctest(loop:asyncio.AbstractEventLoop) -> None:

            connection = AsyncConnection()
            await connection.connect()
            #spatial_ref_sys
            query = 'SELECT * FROM spatial_ref_sys limit 1'
            values = await connection.connection.fetch(
                query
            )
            print(values)

            async with connection.engine.begin() as conn:
                data = await conn.run_sync(
                    lambda sync_conn: pandas.read_sql(
                        query,
                        con=sync_conn,
                    )
                )

            print(data)

            await connection.close()
        
        self.loop.run_until_complete(asynctest(self.loop))
    
class TestAsyncQueryBuilder(unittest.IsolatedAsyncioTestCase):
    
    def setUp(self):
        self.loop = asyncio.get_event_loop()

    def testSelect(self) -> None:
    
        async def asynctest(loop:asyncio.AbstractEventLoop) -> None:

            connection = AsyncConnection()
            await connection.connect()
            query_builder = QueryBuilder(connection)
            tables = await query_builder.selectElements('table').asyncExecute()

            print(tables)

            await connection.close()
        
        self.loop.run_until_complete(asynctest(self.loop))
   
    def testDrop(self) -> None:
    
        async def asynctest(loop:asyncio.AbstractEventLoop) -> None:

            connection = AsyncConnection()
            await connection.connect()
            query_builder = QueryBuilder(connection)
            await query_builder.drop(
                'data_events',
                'table',
                exists_condition=True
            ).built().asyncExecute(False)

            await connection.close()
        
        self.loop.run_until_complete(asynctest(self.loop))
    
class TestAsyncDataEventsTable(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()

    def testInit(self) -> None:
    
        async def asynctest(loop:asyncio.AbstractEventLoop) -> None:

            connection = AsyncConnection(loop=loop)
            await connection.connect()
            
            table = AsyncDataEventsTable(
                connection
            )

            await table.manage()
            await connection.close()

        self.loop.run_until_complete(asynctest(self.loop))

class TestAsyncDataLogging(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()

    def testLog(self) -> None:
    
        async def asynctest(loop:asyncio.AbstractEventLoop) -> None:

            connection = AsyncConnection(loop=loop)
            await connection.connect()
            
            data_logging = AsyncDataLogging(
                connection
            )
            await data_logging.manageTable()
            data_logging.setElement(
                'table',
                'files'
            )

            await data_logging.logEvent(
                'create',
                'loading'
            )

            await data_logging.logEvent(
                'create',
                'loaded'
            )


            await connection.close()

        self.loop.run_until_complete(asynctest(self.loop))
