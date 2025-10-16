"""

"""
from typing import Dict

import os
import unittest
import pandas
import datetime
import shutil
import asyncio

from datablender.base import (
    Connection,
    QueryBuilder,
    DataConfiguration,
    Data,
    AsyncConnection,
    AsyncDataConfiguration
)
from datablender.database import Database, View
from datablender.data import (
    getPathElements,
    DataVersion,
    DataVersionColumn,
    DataVersionTable,
    DataVersionValue,
    FilesTable,
    DataSourceCore,
    DirectoryElementController,
    DataFile,
    DataZipFile,
    DataDirectoryElement,
    DataDirectory,
    RawDataFile,
    DataFetcher,
    DataSource,
    DataProcess,
    DataServer,
    AsyncDataServer,
    AsyncDataProcess
)

class TestGetPathElements(unittest.TestCase):
    
    def testGetPathElements(self):
    
        print(
        getPathElements(
            'C:/data/systems/bixi/',
            'C:/data/systems/bixi/DonneesOuverte2022.zip'
        )
        )

class TestFileTable(unittest.TestCase):

    def setUp(self):
        
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)

        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()

        self.query_builder.drop(
            "main_files",
            "view",
            exists_condition=True
        ).built().execute()

        self.query_builder.drop(
            "files",
            "table",
            exists_condition=True
        ).built().execute()
        
        self.files =FilesTable(self.connection)
        self.files.manage()

    def tearDown(self):

        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()

        self.query_builder.drop(
            "main_files",
            "view",
            exists_condition=True
        ).built().execute()

        self.query_builder.drop(
            "files",
            "table",
            exists_condition=True
        ).built().execute()

        self.connection.close()

    def testInitiation(self):

        self.assertIn(
            'files',
            self.query_builder.selectElements(
                'table'
            ).execute()['name'].values
        )
    
    def testInsert(self) -> None:

        self.files.insert({
            'name':'test.csv',
            'schema':'public',
            'main_files':[
                {
                    'name':'test.zip',
                    'directory_name':'C:/data',
                    'main_file_path':''
                }
            ],
            'path_index':'C:/data/test.zip/test.csv'
        })

        self.files.select()

        self.assertEqual(
            self.files.data.frame.iloc[0,1],
            'C:/data/test.zip/test.csv'
        )

    def testMainFilesView(self) -> None:

        self.files.insert({
            'name':'test.csv',
            'schema':'public',
            'main_files':[
                {
                    'name':'test.zip',
                    'directory_name':'C:/data',
                    'main_file_path':''
                }
            ],
            'path_index':'C:/data/test.zip/test.csv'
        })
        
        view = View(
            self.connection,
            'main_files',
            file_query='main_files',
            directory_query=os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..',
                'postgresql',
                'queries'
            )
        ).manage()

        view.select()

        self.assertEqual(
            view.data.frame.iloc[0,1],
            '"C:/data"'
        )

    def testCheckFile(self) -> None:

        self.files.insert({
            'name':'test.csv',
            'schema':'public',
            'main_files':[
                {
                    'name':'test.zip',
                    'directory_name':'C:/data',
                    'main_file_path':''
                }
            ],
            'path_index':'C:/data/test.zip/test.csv'
        })

        self.files.getFiles()

        self.assertTrue(
            self.files.checkFile(
                'C:/data/test.zip/test.csv'
            )
        )

class TestDirectoryElementController(unittest.TestCase):

    def testWithElements(self):

        controller = DirectoryElementController(
            file_controls = {
                'elements':{
                    "__MACOSX":False,
                    "__Licence.txt":False,
                    "trips2.txt":False
                }
            }
        )

        self.assertTrue(
            controller.control('stops.txt','file')
        )

        self.assertFalse(
            controller.control('trips2.txt','file')
        )

    def testWithExtensions(self):
        controller = DirectoryElementController(
            file_controls = {
                'elements':{
                    "trips2.txt":False,
                    "__Licence.txt":False
                },
                'extensions':{
                'txt':True
                }
            }
        )

        self.assertTrue(
            controller.control('stops.txt','file')
        )

        self.assertFalse(
            controller.control('trips2.txt','file')
        )
    
    def testWithoutControls(self) -> None:

        controller = DirectoryElementController()

        self.assertTrue(
            controller.control('stops.txt','file')
        )
        
        self.assertTrue(
            controller.control('trips2.txt','file')
        )
        
    def testWithMultipleExtensions(self):

        controller = DirectoryElementController(
            file_controls = {
                'extensions':{
                    'txt':True,
                    'xlsx':True
                }
            }
        )

        self.assertTrue(
            controller.control(
                'stops.txt','file'
            )
        )

        self.assertTrue(
            controller.control(
                'test.xlsx','file'
            )
        )

        self.assertFalse(
            controller.control(
                'test.dbf','file'
            )
        )
       
class TestDataVersionValue(unittest.TestCase):

    def testInitiation(self):

        data_version_value = DataVersionValue(
            'agency_id',
            'file',
            r'[a-zA-Z]+_',
            start=0,
            end=-1,
            add_to_data=True
        )     

        data_version_value.setValue(
            'data/gtfs/CITCRC/',
            'CITCRC_111'
        )

        self.assertEqual(
            'CITCRC',
            data_version_value.value
        )

class TestDataVersionColumn(unittest.TestCase):

    def testInitiation(self):

        data_version_values: Dict[str, DataVersionValue] = {}
        values_config=[
            {
                "name": "agency_id",
                "type": "file",
                "detect": "[a-zA-Z]+_",
                "start": 0,
                "end": -1,
                "add_to_data": True
            },
            {
                "name": "start_date",
                "type": "file",
                "detect": "_[0-9]{8}_",
                "start": 1,
                "end": 9,
                "add_to_data": False,
                "format": {
                    "type": "date",
                    "format": "%Y%m%d"
                }
            },
            {
                "name": "end_date",
                "type": "file",
                "detect": "_[0-9]{8}\\.",
                "start": 1,
                "end": 9,
                "add_to_data": False,
                "format": {
                    "type": "date",
                    "format": "%Y%m%d"
                }
            },
            {
                "name": "version_id",
                "type": "generated",
                "add_to_data": True
            }
        ]

        data_version_values = {
            value['name']:DataVersionValue(**value)
            for value in values_config
        }
        
        {
            data_version_values[value_name].setValue(
                'data/gtfs/CITCRC/',
                'CITCRC_20180101_20180505.zip'
            ) for value_name in data_version_values
        }

        data_version_column = DataVersionColumn(
            'agency.txt',
            data_version_values,
            'agency_id',
            'text',
            'detected',
            True,
            True
        )

        data_version_column.setValue(
            'stops.txt',
            datetime.datetime(2018,1,1),
            'CITCRC_20180101_20180505.zip',
            pandas.DataFrame()
        )
        
        self.assertEqual(
            'CITCRC',
            data_version_column.value
        )

class TestDataVersionTable(unittest.TestCase):

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
            "agency",
            "table",
            exists_condition=True
        ).built().execute()

        data_version_values: Dict[str, DataVersionValue] = {}
        values_config=[
            {
                "name": "agency_id",
                "type": "file",
                "detect": "[a-zA-Z]+_",
                "start": 0,
                "end": -1,
                "add_to_data": True
            },
            {
                "name": "start_date",
                "type": "file",
                "detect": "_[0-9]{8}_",
                "start": 1,
                "end": 9,
                "add_to_data": False,
                "format": {
                    "type": "date",
                    "format": "%Y%m%d"
                }
            },
            {
                "name": "end_date",
                "type": "file",
                "detect": "_[0-9]{8}\\.",
                "start": 1,
                "end": 9,
                "add_to_data": False,
                "format": {
                    "type": "date",
                    "format": "%Y%m%d"
                }
            },
            {
                "name": "version_id",
                "type": "generated",
                "add_to_data": True
            }
        ]
        
        data_version_values = {
            value['name']:DataVersionValue(**value)
            for value in values_config
        }

        {
            data_version_values[value_name].setValue(
                'data/gtfs/CITCRC/',
                'CITCRC_20180101_20180505.zip'
            ) for value_name in data_version_values
        }

        columns_config = [
            {
                "name": "agency_id",
                "type": "text",
                "extract_mode": "detected",
                "is_in_id_columns": True,
                "is_unique_id_column": True
            },
            {
                "name": "agency_name",
                "type": "text",
                "extract_mode": "data",
                "is_in_id_columns": False,
                "is_unique_id_column": False
            },
            {
                "name": "agency_url",
                "type": "text",
                "extract_mode": "data",
                "is_in_id_columns": False,
                "is_unique_id_column": False
            },
            {
                "name": "agency_timezone",
                "type": "text",
                "extract_mode": "data",
                "is_in_id_columns": False,
                "is_unique_id_column": False
            },
            {
                "name": "agency_lang",
                "type": "text",
                "extract_mode": "data",
                "is_in_id_columns": False,
                "is_unique_id_column": False
            },
            {
                "name": "agency_phone",
                "type": "text",
                "extract_mode": "data",
                "is_in_id_columns": False,
                "is_unique_id_column": False
            },
            {
                "name": "agency_fare_url",
                "type": "text",
                "extract_mode": "data",
                "is_in_id_columns": False,
                "is_unique_id_column": False
            },
            {
                "name": "agency_email",
                "type": "text",
                "extract_mode": "data",
                "is_in_id_columns": False,
                "is_unique_id_column": False
            }
        ]

        self.data_version_table = DataVersionTable(
            self.connection,
            self.data_config,
            'public',
            data_version_values,
            # {
            #     'stops':Table(
            #         self.connection,
            #         'stops',
            #         'public',
            #         status='inactive'
            #     )
            # },
            'agency',
            columns_config,
            False,
            'agency.txt'
        )

    def tearDown(self):

        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()
        
        self.query_builder.drop(
            "agency",
            "table",
            exists_condition=True
        ).built().execute()

        self.connection.close()
        
        if self.data_config.active:
            self.data_config.deleteAllElements()

    def testManage(self):

        self.data_version_table.manage()
        
        self.data_version_table.setColumns(
            'stops.txt',
            datetime.datetime(2018,1,1),
            'CITCRC_20180101_20180505.zip',
            pandas.DataFrame()
        )

        self.assertEqual(
            self.data_version_table.data_version_columns['agency_id'].value,
            'CITCRC'
        )

    def testCheckUniqueID(self):
    
        self.data_config.active= True
        self.data_config.activate()

        self.data_version_table.manage()
        
        self.data_version_table.setColumns(
            'stops.txt',
            datetime.datetime(2018,1,1),
            'CITCRC_20180101_20180505.zip',
            pandas.DataFrame()
        )
       
        self.data_version_table.checkUniqueID()

        self.assertFalse(
            self.data_version_table.version_exists
        )
        
    def testUpdateTableVersion(self):
    
        self.data_config.active= True
        self.data_config.activate()
        
        self.data_version_table.manage()
        
        self.data_version_table.setColumns(
            'stops.txt',
            datetime.datetime(2018,1,1),
            'CITCRC_20180101_20180505.zip',
            pandas.DataFrame()
        )
        
        self.data_version_table.updateTableVersion(
            'stops.txt',
            datetime.datetime.now(),
            'CITCRC_20180101_20180505.zip',
            Data()
        )

        self.assertFalse(
            self.data_version_table.version_exists
        )

class TestRawDataFile(unittest.TestCase):

    def setUp(self):
        self.directory_name= 'datablender/tests/tests_requirements/test/'
        if os.path.isdir(self.directory_name):
            shutil.rmtree(self.directory_name)

        os.mkdir(
            self.directory_name
        ) 

        self.raw_file = RawDataFile(
            url='https://sitewebbixi.s3.amazonaws.com/uploads/docs/biximontrealrentals2014-f040e0.zip',
            directory_name=self.directory_name
        )

    def tearDown(self):
        shutil.rmtree(self.directory_name)

    def testFromUrl(self):
        self.assertEqual(
            self.raw_file.is_secure,
            True
        )
        self.assertEqual(
            self.raw_file.domain_name,
            'sitewebbixi.s3.amazonaws.com'
        )
        self.assertEqual(
            self.raw_file.url_path,
            'uploads/docs'
        )
        self.assertEqual(
            self.raw_file.name,
            'biximontrealrentals2014-f040e0.zip'
        )

    def testDownloadFile(self):
        self.raw_file.download()
        self.assertIn(
            'biximontrealrentals2014-f040e0.zip',
            os.listdir(self.directory_name)
        )

    def testFile(self) -> None:
        self.raw_file = RawDataFile(
            url='https://diffusion.mern.gouv.qc.ca/Diffusion/RGQ/Vectoriel/Carte_Topo/Local/AQReseau/ESRI(SHP)/AQreseau_SHP.zip',
            directory_name=self.directory_name
        )
        self.raw_file.download()
        self.assertIn(
            'AQreseau_SHP.zip',
            os.listdir(self.directory_name)
        )

class TestDataFetcher(unittest.TestCase):

    def setUp(self):
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)
        self.directory_name= 'datablender/tests/tests_requirements/test/'
        os.mkdir(self.directory_name) 
        self.delete_tables = False

    def tearDown(self):
        shutil.rmtree(self.directory_name)
        
        if self.delete_tables and hasattr(self,'directory'):
            for table in self.directory.data_source_core.tables:
                table.drop(exists_condition=True)

        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()
        self.query_builder.drop(
            "main_files",
            "view",
            exists_condition=True
        ).built().execute()
        self.query_builder.drop(
            "files",
            "table",
            exists_condition=True
        ).built().execute()

        self.connection.close()

    def testFetchFiles1(self):

        data_fetcher = DataFetcher(
            domain_name='transitfeeds.com',
            directory_name=self.directory_name,
            bot_actions = [ 
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
                            'agence-metropolitaine-de-transport/129'
                        ]
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
            ],
            downloading_name = 'gtfs.zip',
            rename_parameters ={
                'rename_from':'url_path',
                'method':'split',
                'character':'/',
                'position':-2
            },
            directory_name_setter = {
                'set_from':'url_path',
                'method':'contain',
                'values':{
                    'agence-metropolitaine-de-transport/129':'EXPRESS',
                    'agence-metropolitaine-de-transport/128':'TRAINS',
                    'agence-metropolitaine-de-transport/130':'CITCRC',
                    'agence-metropolitaine-de-transport/132':'CITLA',
                    'agence-metropolitaine-de-transport/131':'CITHSL',
                    'agence-metropolitaine-de-transport/133':'CITPI',
                    'agence-metropolitaine-de-transport/134':'CRTLA',
                    'agence-metropolitaine-de-transport/135':'CITLR',
                    'agence-metropolitaine-de-transport/136':'CITROUS',
                    'agence-metropolitaine-de-transport/137':'CITSV',
                    'agence-metropolitaine-de-transport/138':'CITSO',
                    'agence-metropolitaine-de-transport/139':'CITVR',
                    'agence-metropolitaine-de-transport/140':'MRCLM',
                    'agence-metropolitaine-de-transport/141':'MRCDM',
                    'agence-metropolitaine-de-transport/142':'MRCLASSO',
                    'agence-metropolitaine-de-transport/143':'OMITSJU',
                    'reseau-de-transport-de-longueuil/37':'RTL',
                    'societe-de-transport-de-laval/38':'STL',
                    'societe-de-transport-de-montreal/39':'STM'
                }
            }
        )

        data_fetcher.fetchFiles()

        self.assertEqual(
            data_fetcher.files[0].url_path,
            '/p/agence-metropolitaine-de-transport/129/latest/download'
        )
        self.assertFalse(
            data_fetcher.files[0].file_included,
        )

        print(data_fetcher.files[0].url_path)
        print(data_fetcher.files[0].directory_name)

    def testFetchFiles2(self):
        data_fetcher = DataFetcher(
            domain_name='bixi.com',
            directory_name=self.directory_name,
            bot_actions = [
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
            ]
        )
        
        data_fetcher.fetchFiles()
        
        self.assertIn(
            'Historique-BIXI-2014.zip',
            [raw_file.name for raw_file in data_fetcher.raw_files]
        )

        for file in data_fetcher.raw_files:
            if file.name is not None:
                file.download()

        data_directory_element = DataDirectoryElement(

        )

    def testFetchFiles3(self):
        data_fetcher = DataFetcher(
            files = [
                {
                    'url':'https://www12.statcan.gc.ca/census-recensement/2016/dp-pd/prof/details/download-telecharger/comp/GetFile.cfm?Lang=F&FILETYPE=CSV&GEONO=044_QUEBEC',
                    'directory_name_setter':{
                        'method':'set',
                        'value':'2016'
                    },
                    'downloading_name':'98-401-X2016044_QUEBEC_fra_CSV.zip'
                },
                {
                    'url':'https://www12.statcan.gc.ca/census-recensement/2011/dp-pd/prof/details/download-telecharger/comprehensive/comp_download.cfm?CTLG=98-316-XWF2011001&FMT=CSV1501&Lang=F&Tab=1&Geo1=PR&Code1=01&Geo2=PR&Code2=01&Data=Count&SearchText=&SearchType=Begins&SearchPR=01&B1=All&Custom=&TABID=1',
                    'directory_name_setter':{
                        'method':'set',
                        'value':'2011'
                    },
                    'downloading_name':'98-316-XWF2011001-1501_CSV.zip'
                }
            ]
        )
        data_fetcher.fetchFiles()

        self.assertIn(
            'census-recensement/2016/dp-pd/prof/details/download-telecharger/comp/GetFile.cfm?Lang=F&FILETYPE=CSV&GEONO=044_QUEBEC',
            [file.url_path for file in data_fetcher.files]
        )
        
    def testFetchFiles4(self):
        data_fetcher = DataFetcher(
            domain_name='donnees.montreal.ca',
            directory_name='datablender/tests/tests_requirements/test/',
            bot_actions = [
                {
                    'name':'get',
                    'url_path':'/ville-de-montreal/velos-comptage'
                },
                {
                    'name':'find_elements',
                    'tag_name':'a',
                    'attributes':{
                        'download':None
                    },
                    'multi_mode':'get',
                    'attribute_name':'href'
                }
            ]
        )
        data_fetcher.fetchFiles()
        self.assertEqual(
            'localisation_des_compteurs_velo.csv',
            data_fetcher.files[0].name
        )
    
    def testFetchFiles5(self):
        data_fetcher = DataFetcher(
            directory_name=self.directory_name,
            files=[
                'https://diffusion.mern.gouv.qc.ca/Diffusion/RGQ/Vectoriel/Carte_Topo/Local/AQReseau/ESRI(SHP)/AQreseau_SHP.zip'
            ]
        )
        data_fetcher.fetchFiles()
        self.assertEqual(
            data_fetcher.files[0].name,
            'AQreseau_SHP.zip'
        )

    def testCompareFiles(self):

        self.delete_tables = True

        self.directory = DataDirectory(
            self.directory_name,
            self.connection
        )

        data_fetcher = DataFetcher(
            domain_name='bixi.com',
            directory_name=self.directory_name,
            bot_actions = [
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
            ]
        )

        data_fetcher.fetchFiles()

        self.directory.setElementStatus(data_fetcher.files)

        self.assertIn(
            'DonneesOuverte2022.zip',
            [file.name for file in data_fetcher.files]
        )
        
    def testDownloadFiles(self):

        self.delete_tables = True

        self.directory = DataDirectory(
            self.directory_name,
            self.connection
        )

        data_fetcher = DataFetcher(
            domain_name='bixi.com',
            directory_name=self.directory_name,
            bot_actions = [
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
            ]
        )

        data_fetcher.fetchFiles()

        self.directory.setElementStatus(data_fetcher.files)

        data_fetcher.downloadFiles()

        self.assertIn(
            'Historique-BIXI-2014.zip',
            os.listdir(self.directory_name)
        )

    def testSetRequest(self) -> None:
    
        data_fetcher = DataFetcher(
            domain_name='overpass-api.de'
        )
        data_fetcher.setRequest()
        self.assertEqual(
            data_fetcher.request.url,
            'https://overpass-api.de'
        )
    
    def testAddRequestElements(self) -> None:
    
        data_fetcher = DataFetcher(
            domain_name='overpass-api.de',
            request_params={
                'elements':[
                    'api/interpreter'
                ]
            }
        )
        data_fetcher.setRequest()
        data_fetcher.addRequestElements()
        self.assertEqual(
            data_fetcher.request.url,
            'https://overpass-api.de/api/interpreter'
        )

    def testFetchDataFromRequest(self) -> None:
    
        data_fetcher = DataFetcher(
            domain_name='overpass-api.de',
            request_params={
                'elements':[
                    'api/interpreter'
                ],
                'params':{
                    "data":"""
                        [out:json];
                        area["name"="Saint-Bruno-de-Montarville"];
                        (
                            node["amenity"="cafe"](area);
                            way["amenity"="biergarten"](area);
                            rel["amenity"="biergarten"](area);
                        );
                        out center;
                    """
                },
                'data_attribute':'elements'
            }
        )
        data_fetcher.setRequest()
        data_fetcher.addRequestElements()
        data_fetcher.fetchDataFromRequest()

        self.assertEqual(data_fetcher.raw_data[0]['id'],3009438159)

class TestDataSourceCore(unittest.TestCase):

    def setUp(self):
        
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)
        self.delete_tables = False

    def tearDown(self):

        if self.data_source_core.data_configuration.active:
            self.data_source_core.data_configuration.deleteAllElements()

        if self.delete_tables:
            for table in self.data_source_core.tables:
                table.drop(exists_condition=True)

        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()

        self.query_builder.drop(
            "main_files",
            "view",
            exists_condition=True
        ).built().execute()

        self.query_builder.drop(
            "files",
            "table",
            exists_condition=True
        ).built().execute()

        self.connection.close()

    def testInitiation(self):
        
        self.data_source_core = DataSourceCore(
            self.connection,
            DataConfiguration(active=False)
        )
        
        self.assertEqual(
            self.query_builder.selectElements(
                'table'
            ).execute()['name'].values.tolist().sort(),
            ['spatial_ref_sys','data_events','files'].sort()
        )
        
        self.assertIsInstance(
            self.data_source_core.files_table,
            FilesTable
        )

    def testInitiationWithConfig(self):
        
        self.data_source_core = DataSourceCore(
            self.connection,
            DataConfiguration(),
            tables = [
                {
                    'name':'households'
                }
            ],
            data_version={
                'tables':[
                    {
                        'name':'surveys'
                    }
                ]
            }
        ).manage()

        self.assertEqual(
            self.data_source_core.data_configuration.data_source[0].get('name'),
            'data'
        )
        
    def testInitiationWithConfigExisting(self):

        data_config = DataConfiguration()

        database = Database(
            self.connection,
            data_configuration=data_config
        ).manage()

        table = database.manageElement(
            {
              "name": "households",
              "schema_id": 1,
              "status": "developpement",
              "owner_id": 1,
              "columns": [],
              "indexes": [],
              "constraints": [
                {
                  "name": "fk_file_id",
                  "type": "foreign key",
                  "columns": [
                    "file_id"
                  ],
                  "reference_table_name": "files",
                  "reference_schema_name": "public",
                  "reference_columns": [
                    "id"
                  ]
                }
              ],
              "grants": [],
              "content": None
            },
            'table'
        )
        data_source_id = data_config.postElement(
            {
                'name':'test_source',
                "status":"developpement",
                "content":None,
                "fetch": [],
                "extract": [
                  {}
                ],
                "transform": [],
                "directory_name": 'datablender/tests/tests_requirements/',
                "control": {
                    "file_controls":{"extensions": ['csv']}
                },
                "data_version": {
                  "values": [],
                  "tables": []
                },
                "schema_id":1,
                "tables":[
                  {
                    "id": table.id,
                    "schema_id": 1,
                    "data_conditions": {
                      "data": {}
                    }
                  }
                ],
                "actions": []
            },
            'data_source'
        )
        
        self.data_source_core = DataSourceCore(
            self.connection,
            data_config,
            id = data_source_id,
            directory_name='datablender/tests/tests_requirements/',
            database = database
        ).manage()

        self.assertEqual(
            self.data_source_core.name,
            'test_source'
        )

    def testInitiationWithConfigExisting_1(self):
        
        data_config = DataConfiguration()
        
        database = Database(
            self.connection,
            data_configuration=data_config
        ).manage()
        
        table = database.manageElement(
            {
              "name": "households",
              "schema_id": 1,
              "status": "developpement",
              "owner_id": 1,
              "columns": [],
              "indexes": [],
              "constraints": [
                {
                  "name": "fk_file_id",
                  "type": "foreign key",
                  "columns": [
                    "file_id"
                  ],
                  "reference_table_name": "files",
                  "reference_schema_name": "public",
                  "reference_columns": [
                    "id"
                  ]
                }
              ],
              "grants": [],
              "content": None
            },
            'table'
        )

        data_source_id = data_config.postElement(
            {
                'name':'test_source',
                "status":"developpement",
                "content":None,
                "fetch": [],
                "extract": [
                  {}
                ],
                "transform": [],
                "directory_name": 'datablender/tests/tests_requirements/',
                "control": {
                    "file_controls":{"extensions": ['csv']}
                },
                "data_version": {
                  "values": [],
                  "tables": []
                },
                "schema_id":1,
                "tables":[
                  {
                    "id": table.id,
                    "schema_id": 1,
                    "data_conditions": {
                      "data": {}
                    }
                  }
                ],
                "actions": []
            },
            'data_source'
        )

        self.data_source_core = DataSourceCore(
            self.connection,
            data_config,
            data_source_id,
            schema_name='public',
            directory_name='datablender/tests/tests_requirements/',
            database = database
        ).manage()

        self.assertEqual(
            self.data_source_core.name,
            'test_source'
        )
    
    def testTransformDataDefault(self):
        
        data = Data(
            {
                'test_1': ['1', '2'],
                'col2': [0.5, 0.75]
            }
        )
        
        self.data_source_core = DataSourceCore(
            self.connection,
            DataConfiguration(active=False),
            schema_name='public',
            directory_name='datablender/tests/tests_requirements/',
            control={
                "file_controls":{
                    'elements':{
                        'test.csv':True
                    }
                }
            },
            transform=[
                {
                    'data_conditions':{},
                    'transformations':[
                        {
                            'name':'rename',
                            'columns':{
                            'col1':'test_1'
                        }
                        }
                    ]
                }
            ]
        )
        
        self.data_source_core.transformData(
            data,
            'test',
            'test.csv',
            'datablender/tests/tests_requirements/'
        )
        
        self.assertEqual(
            data.frame.columns.values.tolist(),
            ['test_1','col2']
        )
    
    def testTransformDataWithConditions(self):

        data = Data(
            {
                'COL1': ['1', '2'],
                'col2': [0.5, 0.75]
            }
        )
        
        self.data_source_core = DataSourceCore(
            self.connection,
            DataConfiguration(active=False),
            schema_name='public',
            directory_name='datablender/tests/tests_requirements/',
            control={
                "file_controls":{
                    'elements':{
                        'test.csv':True
                    }
                }
            },
            transform=[
                {
                    'data_conditions':{
                        'table_name':'test'
                    },
                    'transformations':[
                        {
                            'name':'rename',
                            'columns':{
                                'COL1':'col1'
                            }
                        }
                    ]
                }
            ]
        )
        
        data = self.data_source_core.transformData(
            data,
            'test',
            'test.csv',
            directory_name='datablender/tests/tests_requirements/'
        )
        
        self.assertEqual(
            data.frame.columns.values.tolist(),
            ['col1','col2']
        )

    def testSaveData(self) -> None:
        
        self.delete_tables = True

        self.data_source_core = DataSourceCore(
            self.connection,
            DataConfiguration(active=False),
            directory_name='datablender/tests/tests_requirements',
            control={
                "file_controls":{
                    'elements':{
                        'test.csv':True
                    }
                }
            }
        ).manage()

        self.data_source_core.files_table.insert(
            {
                'id':1,
                'name':'test.csv'
            }
        )

        self.data_source_core.saveData(
            Data(
                data={
                    'col1': [0, 1, 2, 3],
                    'col2':  [0, 1, 2, 3]
                }
            ),
            'test.csv',
            directory_name='datablender/tests/tests_requirements',
            file_id=1
        )

        self.assertIn(
            'tests_requirements',
            self.query_builder.selectElements(
                'table'
            ).execute()['name'].values
        )

    def testDeleteAllData(self) -> None:
        
        self.delete_tables = True

        self.data_source_core = DataSourceCore(
            self.connection,
            DataConfiguration(active=False),
            directory_name='datablender/tests/tests_requirements',
            control={
                "file_controls":{
                    'elements':{
                        'test.csv':True
                    }
                }
            }
        ).manage()

        self.data_source_core.files_table.insert({
            'id':1,
            'name':'test.csv',
            'directory_name':'datablender/tests/tests_requirements'
        })
        
        self.data_source_core.saveData(
            Data(
                data={
                    'col1': [0, 1, 2, 3],
                    'col2': [0, 1, 2, 3]
                }
            ),
            'test.csv',
            directory_name='datablender/tests/tests_requirements',
            file_id = 1
        )

        self.data_source_core.deleteAllData()

        self.assertEqual(
            0,
            self.query_builder.select(
                'tests_requirements'
            ).built().execute().shape[0]
        )
         
class TestDataFile(unittest.TestCase):

    def setUp(self):
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)
        self.file = DataFile(
            'datablender/tests/tests_requirements',
            'test.csv',
            connection=self.connection
        )
        self.delete_tables = False

    def tearDown(self):
        
        if self.delete_tables:
            for table in self.file.data_source_core.tables:
                table.drop(exists_condition=True)

        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()
        self.query_builder.drop(
            "main_files",
            "view",
            exists_condition=True
        ).built().execute()
        self.query_builder.drop(
            "files",
            "table",
            exists_condition=True
        ).built().execute()

        self.connection.close()

    def testInitiation(self):
        
        self.assertEqual(
            self.file.informations.get('columns')[0]['name'],
            'id'
        )
        
        self.file.data_source_core.files_table.insert(
            {
                'name':'test.csv',
                'path_index':os.path.join(
                    'datablender/tests/tests_requirements',
                    'test.csv'),
                'tables':['data'],
                'schema':'public',
                'import_mode':'modification_time',
                'main_files':[],
                'directory_name':'datablender/tests/tests_requirements',
                'size':None,
                'modification_time':None
            }
        )

        self.file.data_source_core.files_table.getFiles()
        self.file.getFileDatabaseInformations()

        self.assertTrue(
            hasattr(self.file,'id')
        )
        self.assertEqual(
            self.file.id,
            1
        )

    def testCheckInDatabase(self):

        self.file.checkInDatabase()

        self.assertTrue(hasattr(self.file,'id'))
        self.assertEqual(self.file.id,1)
    
    def testExtractData(self):

        self.file.extract()

        self.assertIsInstance(
            self.file.data.frame,
            pandas.DataFrame
        )
        
    def testSaveData(self):

        self.delete_tables = True
        self.file.checkInDatabase()
        self.file.extract()
        self.file.saveData()

        self.assertIn(
            'tests_requirements', 
            self.query_builder.selectElements(
                'table'
            ).execute()['name'].values
        )

    def testSave(self):

        self.delete_tables = True

        self.file.save()

        self.assertIn(
            'tests_requirements',
            self.query_builder.selectElements(
                'table'
            ).execute()['name'].values
        )
    
    def testTransfrom(self):

        self.delete_tables = True

        self.file = DataFile(
            'datablender/tests/tests_requirements',
            'test.csv',
            connection=self.connection,
            transform=[
                {
                    'data_conditions':{},
                    'transformations':[
                        {
                            'name':'rename',
                            'columns':{
                                'attr1':'test_1'
                            }
                        }
                    ]
                }
            ]
        )
        
        self.file.save()
        
        tables = self.query_builder.selectElements(
            'table'
        ).execute()
        
        self.assertEqual(
            tables.loc[
                tables['name']=='tests_requirements',
                'columns'
            ].values[0][0]['name'],
            'id'
        )
        
    def testMultiTable(self):

        self.delete_tables = True
        self.file = DataFile(
            'datablender/tests/tests_requirements/',
            'survey.csv',
            connection=self.connection,
            table=[
                'households',
                'persons'
            ],
            transform=[
                {
                    "data_conditions":{},
                    "transformations":[
                        {
                            'name':'rename',
                            'columns':{
                                'age':'age_'
                            }
                        }
                    ]
                },
                {
                    "data_conditions":{
                        'table_name':'households'
                    },
                    "transformations":[
                        {
                            'name':'keep',
                            'column_names':[
                                'houshold_id',
                                'person_id',
                                't_household',
                                't_person',
                                'age_'
                            ]
                        },
                        {
                            'name':'filter',
                            'column_name':'t_household',
                            'value':'T'
                        }
                    ]
                },
                {
                    "data_conditions":{
                        'table_name':'persons'
                    },
                    "transformations":[
                        {
                            'name':'keep',
                            'column_names':[
                                'houshold_id',
                                'person_id',
                                't_household',
                                't_person',
                                'age_'
                            ]
                        },
                        {
                            'name':'filter',
                            'column_name':'t_person',
                            'value':'T'
                        }
                    ]
                }
            ]
        )
        self.file.save()

        self.assertIn(
            'households',
            self.query_builder.selectElements(
                'table'
            ).execute()['name'].values
        )

        self.assertIn(
            'persons',
            self.query_builder.selectElements(
                'table'
            ).execute()['name'].values
        )

class TestDataZipFile(unittest.TestCase):
      
    def setUp(self):
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)
        self.file = DataZipFile(
            'test.zip',
            'datablender/tests/tests_requirements',
            connection=self.connection
        )
        self.delete_tables = False

        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()
        self.query_builder.drop(
            "main_files",
            "view",
            exists_condition=True
        ).built().execute()
        self.query_builder.drop(
            "files",
            "table",
            exists_condition=True
        ).built().execute()

    def tearDown(self):
        
        if self.delete_tables:
            for table in self.file.data_source_core.tables:
                table.drop(exists_condition=True)

        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()
        self.query_builder.drop(
            "main_files",
            "view",
            exists_condition=True
        ).built().execute()
        self.query_builder.drop(
            "files",
            "table",
            exists_condition=True
        ).built().execute()

        self.connection.close()
  
    def testInitiation(self):
        self.assertEqual(
            self.file.name,
            'test.zip'
        )

    def testInformations(self) -> None:
    
        print(self.file.informations)

class TestDataDirectoryElement(unittest.TestCase):

    def setUp(self):
        
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)
        self.delete_tables = False

    def tearDown(self):

        if self.data_source_core.data_configuration.active:
            self.data_source_core.data_configuration.deleteAllElements()

        if self.delete_tables:
            for table in self.data_source_core.tables:
                table.drop(exists_condition=True)

        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()

        self.query_builder.drop(
            "main_files",
            "view",
            exists_condition=True
        ).built().execute()

        self.query_builder.drop(
            "files",
            "table",
            exists_condition=True
        ).built().execute()

        self.connection.close()

    def testGetData(self) -> None:

        self.data_source_core = DataSourceCore(
            self.connection,
            DataConfiguration(active=False),
            extract=[
                {
                    'data_conditions':{},
                    'sheet_name':'feries'
                }
            ],
            name='test_data_source'
        )

        element = DataDirectoryElement(
            self.data_source_core,
            path='C:/data/public/feries/feries.xlsx'
        )
        
        self.assertEqual(
            element.get(True).get('data')[0][0],
            '2017-01-01'
        )

    def testSetStatus(self) -> None:

        self.data_source_core = DataSourceCore(
            self.connection,
            DataConfiguration(active=False),
            name='test_data_source',
            directory_name='datablender/tests/tests_requirements/test1/'
        )

        path = 'C:/MODELISATION/datablender/datablender/tests/tests_requirements/test1'

        data_directory_element = DataDirectoryElement(
            self.data_source_core,
            path = path
        )
        
        data_directory_element.setStatus(
            [
                RawDataFile(
                    url='https://test/test_url/test1.csv',
                    directory_name=path
                ),
                RawDataFile(
                    url='https://test/test_url/test12.csv',
                    directory_name=path
                )
            ]
         )

        self.assertEqual(
            data_directory_element.informations.get('elements')[0]['name'],
            'test1.csv'
        )

    def testZipFile(self):
        self.data_source_core = DataSourceCore(
            self.connection,
            DataConfiguration(active=False),
            name='test_data_source'
        )
        element = DataDirectoryElement(
            self.data_source_core,
            'test.zip',
            'datablender/tests/tests_requirements'
        )
        self.assertIn(
            'test1',
            [element['name'] for element in element.informations.get('elements')]
        )

    def testGetWithMainFile(self) -> None:

        self.data_source_core = DataSourceCore(
            self.connection,
            DataConfiguration(active=False),
            name='test_data_source'
        )
        element = DataDirectoryElement(
            self.data_source_core,
            'test1',
            main_files = [
                {
                    'directory_name': 'datablender/tests/tests_requirements',
                    'name': 'test.zip',
                    'main_file_path': None
                }
            ]
        )
        
        self.assertEqual(
            element.get().get('name'),
            'test1'
        )

class TestDataDirectory(unittest.TestCase):

    def setUp(self):
        
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)
        self.delete_tables = False

        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()

        self.query_builder.drop(
            "main_files",
            "view",
            exists_condition=True
        ).built().execute()

        self.query_builder.drop(
            "files",
            "table",
            exists_condition=True
        ).built().execute()

    def tearDown(self):
        
        if self.delete_tables and hasattr(self,'directory'):
            for table in self.directory.data_source_core.tables:
                table.drop(exists_condition=True)

        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()

        self.query_builder.drop(
            "main_files",
            "view",
            exists_condition=True
        ).built().execute()

        self.query_builder.drop(
            "files",
            "table",
            exists_condition=True
        ).built().execute()

        self.connection.close()

    def testInitiation(self):

        self.directory = DataDirectory(
            'datablender/tests/tests_requirements/',
            self.connection
        )
        self.assertEqual(
            self.directory.informations.get('name'),
            'tests_requirements'
        )

    def testDataDirectoryElement(self):
        
        directory = DataDirectory(
            'datablender/tests/tests_requirements/',
            self.connection
        )
       
        data_directory_element=DataDirectoryElement(
            directory.data_source_core,
            'survey.csv',
            directory.name
        )

        self.assertEqual(
            data_directory_element.name,
            'survey.csv'
        )
    
    def testSaveDataDirectoryElement(self):

        self.query_builder.drop(
            "tests_requirements",
            "table",
            exists_condition=True
        ).built().execute()

        directory = DataDirectory(
            'datablender/tests/tests_requirements/',
            self.connection
        )
       
        data_directory_element=DataDirectoryElement(
            directory.data_source_core,
            'survey.csv',
            directory.name
        )

        data_directory_element.save()

        self.assertIn(
            'tests_requirements',
            self.query_builder.selectElements(
                'table'
            ).execute()['name'].values.tolist()
        )

        self.query_builder.drop(
            "tests_requirements",
            "table",
            exists_condition=True
        ).built().execute()

    def testSaveDataDirectory(self):
        
        self.query_builder.drop(
            "tests_requirements",
            "table",
            exists_condition=True
        ).built().execute()

        self.delete_tables = True

        self.directory = DataDirectory(
            'datablender/tests/tests_requirements/',
            self.connection,
            control={
                "file_controls":{
                    'elements':{
                        'test.csv':True
                    }
                }
            }
        )
        
        self.directory.saveFiles()

        self.assertIn(
            'tests_requirements',
            self.query_builder.selectElements(
                'table'
            ).execute()['name'].values.tolist()
        )
        
        self.query_builder.drop(
            "tests_requirements",
            "table",
            exists_condition=True
        ).built().execute()

    def testManageElements(self) -> None:

        data_directory = DataDirectory(
            'datablender/tests/tests_requirements/test1/',
            self.connection
        )
        
        data_directory.data_source_core.files_table.delete()

        data_directory.data_source_core.files_table.insert({
            'name':'test3.csv',
            'schema':'public',
            'directory_name':data_directory.name
        })
        data_directory.setElements()

        data_directory.manageElements()

        self.assertTrue(
            data_directory.data_source_core.files_table.select().data.frame.empty
        )

class TestDataSource(unittest.TestCase):
    
    def setUp(self):
        self.connection =Connection()
        self.query_builder = QueryBuilder(self.connection)
        self.directory_name= 'datablender/tests/tests_requirements/test/'
        shutil.rmtree(self.directory_name)
        os.mkdir(self.directory_name) 
        self.delete_tables = False

    def tearDown(self):

        if hasattr(self,'data_source') and self.data_source.core.data_configuration.active:
            self.data_source.core.data_configuration.deleteAllElements()

        if self.delete_tables:
            for table in self.data_source.core.tables:
                table.drop(exists_condition=True)

                if table.schema_name != 'public':
                    self.query_builder.drop(
                        table.schema_name,
                        "schema",
                        exists_condition=True
                    ).built().execute()

        self.query_builder.drop(
            "data_events",
            "table",
            exists_condition=True
        ).built().execute()
        self.query_builder.drop(
            "main_files",
            "view",
            exists_condition=True
        ).built().execute()
        self.query_builder.drop(
            "files",
            "table",
            exists_condition=True
        ).built().execute()

        self.connection.close()

        #shutil.rmtree(self.directory_name)

    def testInitiation(self) -> None:
    
        self.data_source = DataSource(
            self.connection,
            name = 'test',
            directory_name=self.directory_name
        )

        self.assertEqual(
            self.query_builder.selectElements(
                'table'
            ).execute()['name'].values.tolist().sort(),
            ['spatial_ref_sys','data_events','files'].sort()
        )
        
        self.assertIsInstance(
            self.data_source.core.files_table,
            FilesTable
        )

    def testInitiationWithConfig(self) -> None:
    
        self.data_source = DataSource(
            self.connection,
            acticvate_data_config=True,
            name = 'test',
            directory_name=self.directory_name
        ).manage()

        self.assertEqual(
            self.query_builder.selectElements(
                'table'
            ).execute()['name'].values.tolist().sort(),
            ['spatial_ref_sys','data_events','files'].sort()
        )

        self.assertIsInstance(
            self.data_source.core.files_table,
            FilesTable
        )

        self.data_source.core.data_configuration.getElements(
            'data_source'
        )
        
        self.assertEqual(
            'test',
            self.data_source.core.data_configuration.data_source[0]['name']
        )

    def testInitiationWithConfigExisting(self) -> None:
        
        data_config = DataConfiguration()

        data_config.postElement(
            {
                'name':'test',
                'status':'developpement',
                'content':None,
                'fetch':[
                    {
                        'domain_name':'bixi.com'
                    }
                ],
                'extract':[],
                'transform':[],
                'save':[],
                'schema_id':1,
                'tables':[],
                'directory_name':self.directory_name,
                'control':{},
                'data_version':{}
            },
            'data_source'
        )

        self.data_source = DataSource(
            self.connection,
            data_configuration=data_config,
            name = 'test',
            directory_name=self.directory_name
        ).manage()

        self.assertEqual(
            self.query_builder.selectElements(
                'table'
            ).execute()['name'].values.tolist().sort(),
            ['spatial_ref_sys','data_events','files'].sort()
        )

        self.assertIsInstance(
            self.data_source.core.files_table,
            FilesTable
        )

        self.data_source.core.data_configuration.getElements('data_source')

        self.assertEqual(
            'test',
            self.data_source.core.data_configuration.data_source[0]['name']
        )

        self.assertEqual(
            'bixi.com',
            self.data_source.core.data_fetchers[0].domain_name
        )
    
    def testSetDataDirectoryElement(self) -> None:
    
        self.data_source = DataSource(
            self.connection,
            name = 'test',
            directory_name=self.directory_name
        )

        self.data_source.setDirectoryElement()

        self.assertEqual(
            self.data_source.directory_element.name,
            'test'
        )

    def testFetchFiles(self):
        
        self.delete_tables = True
         
        self.data_source = DataSource(
            self.connection,
            name = 'bixi',
            fetch=[
                {
                    'domain_name':'bixi.com',
                    'bot_actions':[
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
                    ]
                }
            ],
            transform=[
                {
                    'data_conditions':{
                        'file_not_contains':'tation'
                    },
                    'transformations':[
                        {
                            'name':'rename',
                            'columns':{
                                'emplacement_pk_start':'start_station_id',
                                'emplacement_pk_end':'end_station_id',
                                'start_station_code':'start_station_id',
                                'end_station_code':'end_station_id'
                            }
                        },
                        {
                            'name':'toDate',
                            'column_name':'start_date',
                            'format':'%Y%m%d'
                        },
                        {
                            'name':'toDate',
                            'column_name':'start_date',
                            'format':'%Y%m%d'
                        }
                    ]
                },
                {
                    'data_conditions':{
                        'file_contains':'tation'
                    },
                    'transformations':[
                        {
                            'name':'rename',
                            'columns':{
                                'pk':'id',
                                'code':'id'
                            }
                        },
                        {
                            "name": "toList",
                            "column_name": "point",
                            "column_names": [
                                "longitude",
                                "latitude"
                            ]
                        },
                        {
                            'name':'toGeometry',
                            "column_name": "station",
                            "coordinates_column": "point",
                            "geometry_type": "Point"
                        }
                    ]
                }
            ],
            directory_name=self.directory_name,
            control={
                'file_controls':{
                    'elements':{
                        'DonneesOuverte2022.zip':False,
                        'DonneesOuverte2023-04050607.zip':False,
                        #'Historique-BIXI-2014.zip':True,
                        'Historique-BIXI-2015.zip':False,
                        'Historique-BIXI-2016.zip':False,
                        'Historique-BIXI-2017.zip':False,
                        'Historique-BIXI-2018.zip':False,
                        'Historique-BIXI-2019.zip':False,
                        'Historique-BIXI-2020.zip':False,
                        'Historique-BIXI-2021.zip':False
                    }
                }
            },
            data_version={
                'values':[
                    {
                        'name':'version_id',
                        'type':'file',
                        'detect':'[0-9]{4}',
                        "start": 0,
                        "end": 4,
                        'add_to_data':True,
                        'format':{'type':'int'}
                    }
                ]
            },
            schema_name = 'systems',
            tables = [
                {
                    'name':'stations',
                    'data_conditions':{
                        'file_contains':'tation'
                    }
                },
                {
                    'name':'trips',
                    'data_conditions':{
                        'file_not_contains':'tation'
                    }
                }
            ]
        ).manage()

        self.assertIn(
            'Historique-BIXI-2016.zip',
            [element['name'] for element in self.data_source.fetchFiles('0').get('elements')]
        )

    def testSaveData(self) -> None:

        self.delete_tables = True
        
        self.data_source = DataSource(
            self.connection,
            directory_name='datablender/tests/tests_requirements/',
            control={
                'file_controls':{
                    'elements':{
                        'test.csv':True
                    }
                }
            }
        ).manage()

        self.data_source.saveData()
        
        self.assertIn(
            'tests_requirements',
            self.query_builder.selectElements(
                'table'
            ).execute()['name'].values
        )

    def testGetDataDirectoryElement(self) -> None:
        
        self.data_source = DataSource(
            self.connection,
            directory_name='datablender/tests/tests_requirements'
        ).manage()

        self.assertIn(
            'test1.csv',
            [
                element['name'] for element
                in self.data_source.getDataDirectoryElement(
                    relative_path='test1'
                ).get('elements')
            ]
        )
    
    def testGetDataDirectoryElement1(self) -> None:
        
        self.data_source = DataSource(
            self.connection,
            directory_name='C:/data/systems/bixi'
        ).manage()
        print(
        self.data_source.getDataDirectoryElement(
            {
                'directory_name':"C:/data/systems/bixi",
                'main_files':[],
                'name':"DonneesOuverte2022.zip",
                'path':"C:/data/systems/bixi/DonneesOuverte2022.zip"
            }
        )
        )

    def testExecuteAction(self) -> None:

        self.data_source = DataSource(
            self.connection,
            name = 'test',
            fetch=[
                {
                    'domain_name':'bixi.com',
                    'bot_actions':[
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
                    ]
                }
            ],
            directory_name=self.directory_name
        ).manage()
        
        self.assertIn(
            'Historique-BIXI-2016.zip',
            [file.get('name') for file in self.data_source.getFiles('0').get('elements')]
        )
        print(self.data_source.getDataDirectoryElement())
        # self.assertIn(
        #     'test1',
        #     [
        #         element['name'] for element
        #         in self.data_source.getDataDirectoryElement().get('directory_element')['elements']
        #     ]
        # )
    
    def testSaveData1(self) -> None:
        # query_builder.drop(
        #     'nodes',
        #     "table",
        #     "open_street_map",
        #     exists_condition=True
        # ).built().execute()
        # query_builder.drop(
        #     'relations',
        #     "table",
        #     "open_street_map",
        #     exists_condition=True
        # ).built().execute()
        # query_builder.drop(
        #     'ways',
        #     "table",
        #     "open_street_map",
        #     exists_condition=True
        # ).built().execute()
        # query_builder.drop(
        #     "open_street_map",
        #     "schema",
        #     exists_condition=True
        # ).built().execute()
        
        # data_source = DataSource(
        #     connection,
        #     name='open_street_map',
        #     schema_name='territory'
        # )

        # data_import = DataImportation(
        #     connection,
        #     'open_street_map',
        #     schema='open_street_map',
        #     table=['nodes','ways','relations'],
        #     fetch={
        #         'domain_name':'overpass-api.de',
        #         'request_params':{
        #             'elements':[
        #                 'api/interpreter'
        #             ],
        #             'params':[
        #                 {
        #                     "data":"""
        #                         [out:json];
        #                         area["name"="Saint-Bruno-de-Montarville"];
        #                         (node(area););
        #                         out body;
        #                     """
        #                 },
        #                 {
        #                     "data":"""
        #                         [out:json];
        #                         area["name"="Saint-Bruno-de-Montarville"];
        #                         (way(area););
        #                         out body;
        #                     """
        #                 },
        #                 {
        #                     "data":"""
        #                         [out:json];
        #                         area["name"="Saint-Bruno-de-Montarville"];
        #                         (rel(area););
        #                         out body;
        #                     """
        #                 }
        #             ],
        #             'data_attribute':'elements'
        #         }
        #     },
        #     transform=[
        #         {
        #             "data_conditions":{
        #                 'table_name':'nodes'
        #             },
        #             'transformations':[
        #                 {
        #                     'name':'filter',
        #                     'columns':['type','id','lat','lon','tags'],
        #                     'column':'type',
        #                     'value':'node'
        #                 },
        #                 {
        #                     'name':'geometry',
        #                     'columns':[
        #                         {
        #                             'name':'node',
        #                             'x_coordinate_name':'lon',
        #                             'y_coordinate_name':'lat'
        #                         }
        #                     ]
        #                 }
        #             ]
        #         },
        #         {
        #             "data_conditions":{
        #                 'table_name':'ways'
        #             },
        #             'transformations':[
        #                 {
        #                     'name':'filter',
        #                     'columns':['type','id','tags','nodes'],
        #                     'column':'type',
        #                     'value':'way'
        #                 }
        #             ]
        #         },
        #         {
        #             "data_conditions":{
        #                 'table_name':'relations'
        #             },
        #             'transformations':[
        #                 {
        #                     'name':'filter',
        #                     'columns':['type','id','tags'],
        #                     'column':'type',
        #                     'value':'relation'
        #                 }
        #             ]
        #         }
        #     ]
        # )

        # data_import.fetchData()
        # data_import.importData()

        # print(data_import.data.frame)
        # print(data_import.data_source.tables)
        
        # query_builder.drop(
        #     "data_events",
        #     "table",
        #     exists_condition=True
        # ).built().execute()

        self.connection.close()

    def testDownloadFiles(self) -> None:
        self.data_source = DataSource(
            self.connection,
            name = 'test',
            directory_name='datablender/tests/tests_requirements/test/',
            fetch=[
                {
                    'domain_name':'bixi.com',
                    'bot_actions':[
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

                    ]
                }
            ]
        )
        self.data_source.manage()
        self.data_source.fetchFiles()

        for file in self.data_source.core.data_fetchers[0].raw_files:
            if file.name == 'DonneesOuvertes2024_0102.zip':
                file.download()
        
        directory_element = self.data_source.getDataDirectoryElement()
        print('-----------------------')
        [
            print(element) for element in directory_element.get('directory_element')['elements']
            if element['name'] == 'DonneesOuvertes2024_0102.zip'
        ]
        
    def testTransformData(self) -> None:
    
        self.data_source = DataSource(
            self.connection,
            name = 'test_source',
            directory_name=self.directory_name,
            fetch = [
                {
                    'files':[
                        'https://diffusion.mern.gouv.qc.ca/Diffusion/RGQ/Vectoriel/Carte_Topo/Local/AQReseau/ESRI(SHP)/AQreseau_SHP.zip'
                    ]   
                }
            ]
        )

        self.data_source.getFiles('0')
        self.data_source.downloadFiles('0')

        print(
        self.data_source.getDataDirectoryElement(
            {
                'name' : 'AQ_ROUTES.shp',
                'directory_name':self.directory_name,
                'main_files': [
                    {
                        'directory_name':'datablender/tests/tests_requirements/test/',
                        'name': 'AQreseau_SHP.zip',
                        'main_file_path': ''
                    }
                ]
            }
        )
        )
        
        if self.data_source.directory_element.file:
            self.data_source.directory_element.file.extract()
            
        if self.data_source.directory_element.zip_file:
            self.data_source.directory_element.zip_file.close()

class TestDataProcess(unittest.TestCase):

    def testInit(self) -> None:
        connection =Connection()
        data_process = DataProcess(
            connection,
            'test_process',
            data='modes'
        )
        print(data_process.database.name)
        print(data_process.directory_name)
        print(data_process.data['modes'].frame)
        #self.assertEqual(data_process.directory_name,'C:/MODELISATION/datablender/datablender/tests\processes\\test_process')
        connection.close()

    def testGetData(self) -> None:
        connection =Connection()
        data_process = DataProcess(
            connection,
            'test_process'
        )
        data = data_process.setData(
            ['modes']
        )
        #self.assertEqual(data.frame['srid'].values.tolist()[0],3819)
        print(data_process.data)
        connection.close()

    def testTransformData(self) -> None:
        connection =Connection()
        data_process = DataProcess(
            connection,
            'test_process',
            data='modes'
        )
        data_process.process()
        connection.close()

class TestAsyncDataFetcher(unittest.IsolatedAsyncioTestCase):
        
    async def testInit(self) -> None:
        pass

class TestAsyncDataProcess(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.connection = AsyncConnection()
        self.loop = asyncio.get_event_loop()
        self.data_process = AsyncDataProcess(
            self.connection,
            'test_data_process',
            loop=self.loop
        )
        
        async def setUpTests() -> None:
            await self.connection.connect()
            await self.data_process.initiate()
            await self.data_process.manage()
            
        self.loop.run_until_complete(setUpTests())

    def tearDown(self) -> None:

        async def tearDownTests() -> None:
            await self.connection.close()
        
        self.loop.run_until_complete(tearDownTests())

    def testInit(self) -> None:
        pass

    async def testSelect(self) -> None:
        
        await self.data_process.select(
            [
                {'name':'spatial_ref_sys','schema_name':'public'}
            ]
        )
        self.assertIsInstance(
            self.data_process.database.schema[0].table[0].data.frame,pandas.DataFrame
        )
        self.assertGreater(
            self.data_process.database.schema[0].table[0].data.frame.shape[0],
            1
        )

    async def testSerialize(self) -> None:
        await self.data_process.select(
            [
                {'name':'spatial_ref_sys','schema_name':'public'}
            ]
        )
        await self.data_process.serialize(
            [
                {'name':'spatial_ref_sys','schema_name':'public'}
            ]
        )
        await self.data_process.switch(
            [
                {'name':'spatial_ref_sys','schema_name':'public'}
            ]
        )

class TestDataServer(unittest.TestCase):
    
    def setUp(self):
        
        self.data_server = DataServer()
        self.data_server.connect()

    def tearDown(self):
                
        for database in self.data_server.database:
            database.drop()
        
        self.data_server.disconnect()
        self.data_server.data_configuration.deleteAllElements()

    def testDataServer(self):
        
        self.assertEqual(
            self.data_server.database[0].query_builder.connection.database_name,
            'developpement'
        )
        self.assertEqual(
            self.data_server.database[0].extension[0].name,
            'postgis'
        )

    def testGetSchemas(self):

        self.assertEqual(
            self.data_server.getElements('schema')[0].get('name'),
            'public'
        )

    def testGetTables(self):
        self.assertIn(
            'data_events',
            [element.get('name') for element in self.data_server.getElements('table',schema_id=1)]
        )
    
    def testManageSchema(self) -> None:

        self.data_server.manageElement(
            {
                'name': 'surveys',
                'status': 'developpement',
                'content': None,
                'schema_type': 'source',
                'grants': [
                    {'privilege': 'usage', 'user_name': 'postgres'},
                    {'privilege': 'create', 'user_name': 'postgres'}
                ],
                'owner_id': 1
            },
            'schema'
        )

        self.assertEqual(
            self.data_server.database[0].schema[1].name,
            'surveys'
        )
    
    def testManageTable(self) -> None:

        schema = self.data_server.manageElement(
            {
                'name': 'surveys',
                'status': 'developpement',
                'content': None,
                'schema_type': 'source',
                'grants': [
                    {'privilege': 'usage', 'user_name': 'postgres'},
                    {'privilege': 'create', 'user_name': 'postgres'}
                ],
                'owner_id': 1
            },
            'schema',
            'values'
        )

        element= self.data_server.manageElement(
            {
                'name': 'households',
                'schema_id':schema.id,
                'status': 'developpement',
                'content': None,
                'columns': [
                    {
                        'name':'id',
                        'type':'int'
                    }
                ],
                'owner_id': 1
            },
            'table',
            'values'
        )
        
        self.data_server.getSizes(
            element.configuration,
            'table'
        )

        self.assertEqual(self.data_server.database[0].schema[1].name,'surveys')
        self.assertEqual(self.data_server.database[0].schema[1].table[0].name,'households')
        
    def testManageDataSource(self) -> None:

        schema = self.data_server.manageElement(
            {
                'name': 'surveys',
                'status': 'developpement',
                'content': None,
                'schema_type': 'source',
                'grants': [
                    {'privilege': 'usage', 'user_name': 'postgres'},
                    {'privilege': 'create', 'user_name': 'postgres'}
                ],
                'owner_id': 1
            },
            'schema',
            'values'
        )
        table= self.data_server.manageElement(
            {
                'name': 'households',
                'schema_id':schema.id,
                'status': 'developpement',
                'content': None,
                'columns': [
                    {
                        'name':'id',
                        'type':'int'
                    }
                ],
                'owner_id': 1
            },
            'table',
            'values'
        )
        data_source= self.data_server.manageElement(
            {
                'name':'test_source',
                "status":"developpement",
                "schema_id":schema.id,
                "tables":[
                  {
                    "id": table.id,
                    "schema_id": schema.id,
                    "data_conditions": {
                      "data": {}
                    }
                  }
                ],
                "directory_name": 'datablender/tests/tests_requirements/',
                "control": {
                    'file_controls':{
                        "extensions": ['csv']
                    }
                },
                "data_version": {
                  "values": [],
                  "tables": []
                },
                "fetch": [],
                "extract": [],
                "transform": [],
                "actions": [],
                "content":None
            },
            'data_source',
            'values'
        )
        
        self.assertEqual(self.data_server.data_source[0].name,'test_source')
    
    def testManageDataSource1(self) -> None:

        schema = self.data_server.manageElement(
            {
                'name': 'surveys',
                'status': 'developpement',
                'content': None,
                'schema_type': 'source',
                'grants': [
                    {'privilege': 'usage', 'user_name': 'postgres'},
                    {'privilege': 'create', 'user_name': 'postgres'}
                ],
                'owner_id': 1
            },
            'schema',
            'values'
        )
        data_source= self.data_server.manageElement(
            {
                'name':'test_source',
                "status":"developpement",
                "schema_id":schema.id,
                "tables":[
                  {
                    "id": 'households',
                    "data_conditions": {
                      "data": {}
                    }
                  }
                ],
                "directory_name": 'datablender/tests/tests_requirements/',
                "control": {
                    'file_controls':{
                        "extensions": ['csv']
                    }
                },
                "data_version": {
                  "values": [],
                  "tables": []
                },
                "fetch": [],
                "extract": [],
                "transform": [],
                "actions": [],
                "content":None
            },
            'data_source',
            'values'
        )
        
        self.assertEqual(
            self.data_server.data_source[0].name,
            'test_source'
        )

    def testDataSourceAction(self) -> None:

        data_source= self.data_server.manageElement(
            {
                'name':'test_source',
                "status":"developpement",
                "schema_id":1,
                "tables":[],
                "directory_name": 'datablender/tests/tests_requirements',
                "control": {},
                "data_version": {
                  "values": [],
                  "tables": []
                },
                "fetch": [
                    {
                        'domain_name':'bixi.com',
                        'bot_actions':[
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
                        ]
                    }
                ],
                "extract": [],
                "transform": [],
                "content":None
            },
            'data_source',
            'values'
        )
        
        data_source_configuration = self.data_server.dataSourceAction(
            1,
            action_name='fetchFiles',
            index='0'
        )
        
        self.assertEqual(data_source_configuration.get('name'),'test_source')

        self.assertIn(
            'Historique-BIXI-2016.zip',
            data_source_configuration.get('files')
        )

class TestAsyncDataServer(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:

        self.loop = asyncio.get_event_loop()
        self.data_server = AsyncDataServer(loop=self.loop)
        
        async def setUpTests() -> None:
            await self.data_server.initiate()
            await self.data_server.connect()
        
        self.loop.run_until_complete(setUpTests())

    def tearDown(self) -> None:
        async def tearDownTests() -> None:
            for database in self.data_server.database:
                await database.drop()
            
            await self.data_server.data_configuration.deleteAllElements()
            await self.data_server.disconnect(True)
        
        self.loop.run_until_complete(tearDownTests())

    async def testInitiation(self):
        self.assertEqual(
            self.data_server.data_configuration.schema[0]['id'],
            1
        )
        self.assertEqual(
            self.data_server.database[0].query_builder.connection.database_name,
            'developpement'
        )
    
    async def testGetElements(self) -> None:

        elements = await self.data_server.getElements(
            'schema'
        )
        print(elements)

    async def testManageDataSource(self) -> None:
    
        await self.data_server.manageElement(
            {
                'name':'bixi',
                'status':'developpement',
                'content':None,
                'fetch':[],
                'extract':[],
                'transform':[],
                'save':[],
                'schema_id':1,
                'tables':[],
                'directory_name':None,
                'control':{},
                'data_version':{}
            },
            'data_source'
        )
        events = await self.data_server.database[0].data_logging.view.selectEvents()

        print(events[['action_name','action_time']])
    async def testManageDataSource(self) -> None:
    
        await self.data_server.manageElement(
            {
                'name':'test',
                'status':'developpement',
                'content':None,
                'fetch':[],
                'extract':[],
                'transform':[],
                'save':[],
                'schema_id':1,
                'tables':[],
                'directory_name':None,
                'control':{},
                'data_version':{}
            },
            'data_source'
        )
        events = await self.data_server.database[0].data_logging.view.selectEvents()

        print(events[['action_name','action_time']])

    async def testSave(self) -> None:
        self.data_server.getSizes(
            self.data_server.manageElement(
                {
                    'id': 1,
                    'name': 'bixi',
                    'status': 'developpement',
                    'content': [],
                    'fetch': [
                        {
                            'is_secure': True, 'domain_name': 'bixi.com',
                            'host': None, 'port': None, 'downloading_name': None,
                            'rename_parameters':{},
                            'directory_name_setter': {},
                            'bot_actions': [
                                {
                                    'name': 'get',
                                    'url_path': '/fr/donnees-ouvertes',
                                    'tag_name': None,
                                    'element_text': None,
                                    'attributes': {},
                                    'multi_mode': None,
                                    'attribute_name': None,
                                    'values': None,
                                    'start_value': None,
                                    'execute_previous_action': False
                                },
                                {
                                    'name': 'find_elements',
                                    'url_path': None,
                                    'tag_name': 'a', 'element_text': None,
                                    'attributes': {
                                        'class': 'button button-primary ',
                                        'target': '_blank', 'rel': 'noopener'
                                    },
                                    'multi_mode': 'get', 'attribute_name': 'href',
                                    'values': None, 'start_value': None,
                                    'execute_previous_action': False
                                }    
                            ],
                            'files': [],
                            'request_params': {}
                            }
                        ],
                    'extract': [],
                    'transform': [
                        {
                            'data_conditions': {'file_contains': 'tation'},
                            'transformations': [
                                {
                                    'name': 'toList',
                                    'column_name': 'station',
                                    'column_names': ['longitude', 'latitude']
                                },
                                {
                                    'name': 'setType', 'column_name': 'station',
                                    'column_type': None, 'geometry_type': 'Point',
                                    'srid': '4326'
                                },
                                {
                                    'name': 'keep',
                                    'column_names': ['code', 'name', 'station']
                                }
                            ]
                        },
                        {
                            'data_conditions': {'file_not_contains': 'tation'},
                            'transformations': [
                                {
                                    'name': 'rename',
                                    'columns': {
                                        'start_station_code': 'station_code',
                                        'start_date': 'date'
                                    }
                                },
                                {
                                    'name': 'toDict',
                                    'column_name': 'start',
                                    'column_names':[
                                        'station_code', 'date'
                                    ]
                                },
                                {
                                    'name': 'rename',
                                    'columns': {
                                        'end_station_code': 'station_code',
                                        'end_date': 'date'
                                    }
                                },
                                {
                                    'name': 'toDict',
                                    'column_name': 'end',
                                    'column_names': ['station_code', 'date']
                                },
                                {
                                    'name': 'keep',
                                    'column_names': [
                                        'is_member', 'duration_sec', 'start', 'end'
                                    ]
                                },
                                {
                                    'name': 'stack',
                                    'column_name': 'switch',
                                    'column_names': [
                                        'is_member',
                                        'duration_sec'
                                    ],
                                    'differentiator': 'rank'
                                },
                                {
                                    'name': 'dictToColumns',
                                    'column_name': 'switch',
                                    'column_names': ['station_code', 'date']
                                },
                                {
                                    'name': 'toDateTime',
                                    'column_name': 'date',
                                    'column_type': 'timestamp',
                                    'format': '%Y-%m-%d %H:%M'
                                },
                                {
                                    'name': 'keep',
                                    'column_names': [
                                        'is_member', 'duration_sec',
                                        'rank', 'station_code', 'date'
                                    ]
                                }
                            ]
                        }
                    ],
                    'save': [],
                    'directory_name': 'C:\\data\\systems\\bixi',
                    'control': {
                        'file_controls': {
                            'extensions': {},
                            'elements': {
                                'Stations_2014.csv': True
                            }, 'contains': {}, 'start': {}, 'patterns': {}
                        },
                        'directory_controls': {}
                    }, 'data_version': {
                        'values': [],
                        'tables': []
                    },
                    'schema_id': 2,
                    'tables': [
                         {'data_conditions': {}, 'id': 'stations'}
                    ],
                    'actions': []
                },
                'data_source',
                'values'
            ).configuration,
            'data_source'
        )

        self.data_server.dataSourceAction(
            **{'id': 1, 'action_name': 'saveData'}
        )

