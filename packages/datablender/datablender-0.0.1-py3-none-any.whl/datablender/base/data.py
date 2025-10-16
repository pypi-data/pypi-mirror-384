"""
Data class
"""
from __future__ import annotations
from typing import Union,Dict,List, Callable

import os
import sys
import re
import math
import json
import copy
import numpy
import pandas
import datetime

from pandas.api.types import is_datetime64_any_dtype as is_datetime

from collections.abc import Iterable

import geopandas
import pyproj
import shapely
import shapely.geometry
import shapely.wkb

from shapely.geometry.point import Point
from shapely.geometry.linestring import LineString
from shapely.geometry.polygon import Polygon
from shapely.geometry.multipoint import MultiPoint
from shapely.geometry.multilinestring import MultiLineString
from shapely.geometry.multipolygon import MultiPolygon

from scipy.stats import iqr
import numpy.core.defchararray as np_f
from sklearn.model_selection import train_test_split

from datablender.base.file import File
from datablender.base import getFunction
from datablender.base.connection import Connection
from datablender.base.queryBuilder import QueryBuilder
from datablender.base.dataSets import DataSets

pandas.options.display.float_format = '{:.2f}'.format

class Data:
    """Represent data.

    Attributes:
    ----------
        Attributes

    Methods:
    ----------
        Methods

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        data:Union[pandas.DataFrame,geopandas.GeoDataFrame]=None,
        file_name:str=None,
        directory_name:str=None,
        code_directory:str = None,
        connection:Connection = None,
        name:str = None,
        meta_columns:List[dict] = [],
        columns:List[dict] = [],
        schema_name:str = None,
        schema_type:str = None,
        loaded_rows:int = None,
        transform_columns:List[dict] = [],
        geometry_saved_type:str = 'coordinates',
        data_sets:DataSets = None
    ):
        self.file_name = file_name
        self.directory_name = directory_name
        self.schema_name = schema_name
        self.schema_type = schema_type
        self.code_directory = code_directory
        self.name = name
        self.meta_columns = meta_columns
        self.loaded_rows = loaded_rows
        self.data_sets = data_sets

        self.frame = pandas.DataFrame(
            data.copy() if data is not None else None
        )

        if isinstance(data, geopandas.GeoDataFrame):
            self.setType(
                'geometry',
                geometry=data['geometry'].copy()
            )
            
        elif columns:
            [
                self.setType(
                    column.get('name'),
                    column.get('type'),
                    saved_type=geometry_saved_type
                )
                for column in columns
            ]
            
        else:
            [
                self.detectGeometry(column_name)
                for column_name in self.frame.columns
            ]

        if transform_columns:
            for column in transform_columns:
                column_index = self.getColumnIndex(column.get('name'))

                meta_column = {
                    key: column[key] for key in column.keys()
                    if key in ['url','values','summary','constraints','indexes'] and column[key] is not None
                }

                if meta_column:

                    if column_index is None:
                        self.meta_columns.append({
                            'name':column.get('name'),
                            **meta_column
                        })
                    else:

                        self.meta_columns[column_index] = {
                            **self.meta_columns[column_index],
                            **meta_column
                        }
        
        self.extra_data:Dict[str,pandas.DataFrame] = {}
        self.functions:Dict[str,Callable] = {}

        self.connection = connection

        if self.connection:
            self.query_builder = QueryBuilder(self.connection)

    def importData(
        self,
        buffer=None
    ) -> None:
        column_names = [c.get('name') for c in self.columns]
    
        self.frame = pandas.DataFrame(
            [
                [
                    getattr(record,column)
                    for column in column_names
                ]
                for record
                in getattr(buffer,self.name).record_element
            ],
            columns = column_names
        )

    @property
    def columns(self) -> List[Dict[str,str]]:
        return [
            {  
                'name':column_name,
                'dtype':str(dtype),
                'type': self.getMetaColumn(column_name).get(
                    'column_type',
                    {
                        "int64":"bigint",
                        "Int64":"bigint",
                        "int32":'int',
                        "int":"int",
                        "float64":"numeric",
                        "bool":"bool",
                        "datetime64[ns]":"timestamp",
                        "datetime64[us]":"timestamp",
                        "str":"text",
                        "object":"text"
                    }.get(str(dtype))
                ),
                'sample':self.exportColumn(
                    column_name,
                    dtype,
                    1,
                    is_sample = True,
                    **self.getMetaColumn(column_name)
                ),
                'geometry':self.getMetaColumn(column_name).get('geometry'),
                'values':self.getMetaColumn(column_name).get('values'),
                'url':self.getMetaColumn(column_name).get('url'),
                'summary':self.getMetaColumn(column_name).get('summary'),
                'constraints':self.getMetaColumn(column_name).get('constraints',[]),
                'indexes':self.getMetaColumn(column_name).get('indexes',[])
            }
            for column_name,dtype in zip(self.frame.columns,self.frame.dtypes)
        ]
    
    def detectGeometry(
        self,
        column_name:str
    ) -> None:

        series = self.frame[column_name]

        try:
            first_value = series[~series.isnull()].iloc[0]
            first_value = shapely.wkb.loads(str(first_value), hex=True)
            self.setType(
                column_name,
                geometry_type = first_value.geom_type,
                srid = 4326,
                saved_type = 'text'
            )
        except Exception as e:
            pass

    def getMetaColumn(
        self,
        column_name:str
    ) -> dict:
        column_index = self.getColumnIndex(column_name)

        return self.meta_columns[column_index] if column_index is not None else {}
    
    def getColumnIndex(
        self,
        column_name:str
    ) -> Union[int,None]:
    
        return next(
            (
                index for (index, d) in enumerate(self.meta_columns)
                if d.get("name") == column_name
            ),
            None
        )

    def formatValue(
        self,
        value,
        dtype =None,
        is_sample:bool= False,
        series:pandas.Series = None
    ):
        if isinstance(value,list):
            return value
        if pandas.isna(value):
            return None
        if isinstance(value,numpy.integer):
            return int(value)
        if isinstance(value,numpy.bool_):
            return bool(value)
        if isinstance(value,pandas.Timestamp):
            return value.strftime(
                '%d/%m/%y %H:%M:%S.%f'
            )
        if isinstance(value,pandas.Int64Dtype):
            return int(value)
        
        if is_sample and str(dtype) == 'object':
            return pandas.Series(
                np_f.replace(
                    series.astype(
                        str
                    ).values.tolist(),
                    "'",
                    "''"
                )
            ).iloc[0]
        
        return value

    def exportColumn(
        self,
        column_name:str,
        dtype,
        nrows:int = None,
        export_format = 'json',
        column_type:str= None,
        geometry:dict = None,
        is_sample = False,
        **kwargs
    ) -> Union[pandas.Series,list,any]:
        
        series = self.frame.iloc[:nrows][
            column_name
        ] if nrows is not None else self.frame[
            column_name
        ]
        if (
            column_type
            and column_type == 'json'
            and export_format == 'postgres'
            and isinstance(series,pandas.Series)
        ):                 
            
            series = pandas.Series([
                d if isinstance(d,list) else None if pandas.isna(d) else {
                    k:v.replace('"','\\\"').replace('\n', '\\n').replace('\;','\\\;') if isinstance(v,str) else v for k,v in d.items()
                } for i,d in series.items()
            ]).apply(
                lambda x : x if isinstance(x,list) else None if pandas.isna(x) else json.dumps(x)
            )

        elif (
            column_type
            and column_type[-2:] == '[]'
            and export_format == 'postgres'
        ):
            if column_type[:-2] == 'jsonb':
                series = series.apply(
                    lambda x : str("{"+','.join(map(json.dumps,x))+"}") if isinstance(x,Iterable) else None
                )
            else:
                series = series.apply(
                    lambda x : str("{"+','.join(map(str,x))+"}") if isinstance(x,Iterable) else None
                )

        elif (
            column_type
            and column_type[-2:] == '[]'
            and export_format == 'json'
            and column_type[:-2] in ['json','jsonb']
        ):
            pass

        elif (
            is_datetime(dtype)
            and export_format in ['json','geojson']
        ):
            
            series = series.dt.strftime(
                '%Y-%m-%d' if column_type== 'date' else '%Y-%m-%d %H:%M:%s'
                if column_type == 'timestamp' else '%H:%M:%s'
            )
        
        elif (
            not series[~series.isnull()].empty and
            (
                isinstance(
                    series[~series.isnull()].iloc[0],
                    datetime.date
                )
                or 
                isinstance(
                    series[~series.isnull()].iloc[0],
                    datetime.datetime
                )
            )
            and export_format in ['json','geojson']
        ):
            series = pandas.to_datetime(series).dt.strftime(
                '%Y-%m-%d' if column_type== 'date' else '%Y-%m-%d %H:%M:%s'
                if column_type == 'timestamp' else '%H:%M:%s'
            )

        elif geometry is not None:

            if geometry.get('saved_type') == 'text':
                series = series.apply(
                    lambda x: shapely.wkb.loads(str(x), hex=True) if x and not pandas.isna(x) else None
                )
                if geometry['type'] is None:
                    geometry['type'] = type(series.iloc[0]).__name__.lower()
                geometry = copy.deepcopy(geometry)
                geometry['saved_type'] = 'shapely'
            else:
                geometry = copy.deepcopy(geometry)

            
            if geometry.get('srid_from') is not None:

                transformer = pyproj.Transformer.from_crs(
                    pyproj.CRS('EPSG:{}'.format(geometry.get('srid_from'))),
                    pyproj.CRS('EPSG:{}'.format(geometry.get('srid'))),
                    always_xy=True
                ).transform

                if geometry.get('saved_type') in ['shapely','coordinates']:
                    
                    coords = shapely.get_coordinates(series).tolist() if geometry.get('saved_type') in ['shapely','text'] else series.tolist()

                    series = pandas.Series(shapely.set_coordinates(
                        series.copy() if geometry.get('saved_type') in ['shapely','text'] else [shapely.Point(0,0) for e in series.tolist()],
                        [list(transformer(*c))  for c in coords]
                    ))
                    geometry['saved_type'] = 'shapely'

            if export_format == 'geojson':   
                geometries = numpy.array(series, copy=False)
                columns = [
                    column.get('name') for column in self.columns if column.get('geometry') is None
                ]
                properties = self.frame[columns].astype(object)

                return self.exportGeojson(
                    properties,
                    geometries,
                    export_format,
                    columns,
                    geometry
                )
            else:
                series = series.reset_index().apply(
                    lambda x: self.exportGeometry(
                        *x,
                        export_format,
                        **geometry
                    ),
                    axis=1
                )
        
        elif dtype == 'object':
            samples = series[~series.isnull()]
            
            if not samples.empty and isinstance(samples.iloc[0],list) and len(samples.iloc[0])>0:
                if isinstance(samples.iloc[0][0],dict):
                    series = series.apply(
                        lambda x : str("{"+','.join(["{}".format(json.dumps(i)) for i in x])+"}") if isinstance(x,Iterable) else None
                    ).astype(str)
            
                    # series = series.apply(
                    #     lambda x : str("array['"+','.join(map(json.dumps,x)).replace('"',"'")+"']::jsonb[]") if isinstance(x,Iterable) else None
                    # )
                elif isinstance(samples.iloc[0][0],str):
                    series = series.apply(
                        lambda x : str("{"+','.join(x)+"}") if isinstance(x,Iterable) else None
                    )

        if is_sample:
            if series.shape[0]:

                return self.formatValue(
                    series.iloc[0],
                    dtype,
                    is_sample,
                    series
                )
        elif export_format == 'json':
            return [self.formatValue(a) for a in series] 
        
        return series

    def exportGeojson(
        self,
        properties:pandas.DataFrame,
        geometries,
        export_format,
        columns,
        geometry
    ):
    
        for index, row in enumerate(properties.values):
                
            yield self.exportGeometry(
                index,
                geometries[index],
                export_format,
                properties=dict(zip(columns,[self.formatValue(r) for r in row])),
                **geometry
            )
      
    async def transform(
        self,
        transformations:List[dict],
        data_logging = None
    ) -> Data:
        for transformation in transformations:
            try:
                getattr(
                    self,
                    transformation.pop('name')
                )(**transformation)
            except Exception as error:
                await data_logging.logEvent(error = error)
    
    def setMultiGeometry(
        self,
        feature
    ) -> None:
        if isinstance(feature, Polygon):
            return MultiPolygon([feature])
        
        elif isinstance(feature, Point):
            return MultiPoint([feature])
        
        elif isinstance(feature, LineString):
            return MultiLineString([feature])
        
        return feature

    def setType(
        self,
        column_name:str,
        column_type:str = None,
        geometry_type:str = None,
        srid:int = 4326,
        geometry:geopandas.GeoSeries = None,
        saved_type:str = 'coordinates',
        srid_from:int = None,
        **kwargs
    ) -> None:

        column_index = self.getColumnIndex(column_name)

        meta_geometry = None

        if geometry is not None:

            geometry_types = list(set(geometry.geom_type.values))
            srid = geometry.crs.to_epsg()

            if len(geometry_types)>1:

                self.frame[column_name] = [
                    self.setMultiGeometry(feature)
                    for feature in geometry
                ]
                geometry_type = next((
                    geometry_type
                    for geometry_type in geometry_types
                    if geometry_type[:5]=='Multi'
                ))
            else:
                geometry_type = geometry_types[0]

            meta_geometry = {
                'type':geometry_type,
                'srid':srid,
                'saved_type':'shapely',
                'srid_from':srid_from
            }
            column_type = 'geometry({},{})'.format(
                geometry_type,
                srid
            )

        elif geometry_type is not None:
            
            meta_geometry = {
                'type':geometry_type,
                'srid':srid,
                'saved_type':saved_type,
                'srid_from':srid_from
            }
            column_type = 'geometry({},{})'.format(
                geometry_type,
                srid
            )
            
        elif column_type[:8] == 'geometry':
            geometry_type_ =re.search(r'\([a-z]+,',column_type.lower()).group()[1:-1]
            meta_geometry = {
                'type':None if geometry_type_.lower() == 'geometry' else geometry_type_,
                'srid':re.search(r',[0-9]+\)',column_type).group()[1:-1],
                'saved_type':saved_type
            }

        elif column_type == 'geography':
            meta_geometry = {
                'type':None,
                'srid':4326,
                'saved_type':saved_type
            }

        # elif column_type in ['date','time','timestamp']:

        meta_column = {
            'name':column_name,
            'column_type':column_type,
            'geometry':meta_geometry
        }

        if column_index is None:
            self.meta_columns.append(meta_column)
        else:
            self.meta_columns[column_index] = meta_column

    def asType(
        self,
        column_name:str,
        column_type:str
    ) -> None:
        column_types = {
            'int':int,
            'int64':pandas.Int64Dtype(),
            'str':str,
            'boolean':bool,
            'float':float
        }
        
        self.frame[column_name] = self.frame[
            column_name
        ].astype(
            column_types.get(column_type)
        )
    
    def rename(
        self,
        columns:Dict[str,str]
    ) -> None:
        
        self.frame.rename(
            columns,
            axis='columns',
            inplace=True
        )

        for column_name in columns:
            column_index = self.getColumnIndex(column_name)
            if column_index is not None:
                self.meta_columns[column_index]['name'] = columns[column_name]

    def replace(
        self,
        replace_values:dict
    ) -> None:

        self.frame.replace(
            replace_values,
            inplace=True
        )

    def keep(
        self,
        column_names:list
    ) -> None:
        
        self.frame = self.frame[column_names]
    
    def filter(
        self,
        column_name:str,
        value=None,
        value_to=None,
        match:str = None,
        contains:str = None,
        null_filter:bool=False,
        reverse:bool=False
    ) -> None:
        
        self.frame = self.frame.loc[
            self.getFilter(
                column_name,
                value,
                value_to,
                match,
                contains,
                null_filter,
                reverse
            )
        ]
        self.frame.reset_index(drop=True,inplace=True)

    def getFilter(
        self,
        column_name:str,
        value=None,
        value_to=None,
        match:str = None,
        contains:str = None,
        null_filter:bool=False,
        reverse:bool=False
    ) -> pandas.Series:
        
        series = self.frame[column_name].copy()
        if value_to:
            filter = series.between(value,value_to)

        elif null_filter:
            filter = series.isnull()

        elif match:
            filter = series.str.match(match)

        elif contains:
            filter = series.str.contains(contains)

        elif value is not None:
            if isinstance(value,list):
                filter = series.isin(value)
            else:
                filter = series==value
        
        else:
            filter = series
        
        return ~filter if reverse else filter

    def sort(
        self,
        column_names:List[str]
    ) -> None:
        
        self.frame.sort_values(
            by = column_names,
            inplace=True
        )

    def replaceInValues(
        self,
        column_name:str,
        to_replace:str,
        replace_with:str
    ) -> None:
        """Replace a sub string in each column value with another sub string.

        Args:
            to_replace (str): Sub string to replace.
            replace_with (str): Sub string to replace with.
        """
        
        self.frame[column_name] = pandas.Series(
            np_f.replace(
                self.frame[column_name].astype(
                    str
                ).values.tolist(),
                to_replace,
                replace_with if replace_with else ""
            )
        )
    
    def modifyValues(
        self,
        condition:list=None,
        true_value=None,
        false_value=None
    ) -> pandas.Series:
        """Modify each column value. Based on condition, return true values or false values.

        Args:
            condition (list, optional): Array of true or false values. Defaults to None.
            true_value ([type], optional): Array or unique value to replace the Trues. Defaults to None.
            false_value ([type], optional): Array or unique value to replace the Falses. Defaults to None.
        """
        
        return pandas.Series(
            numpy.where(
                condition,
                true_value,
                false_value
            )
        )

    def modifyValuesMultiple(
        self,
        conditions:list=None,
        choices:list=None,
        default_value=numpy.nan
    ) -> pandas.Series:
        """Modify each column value. Based on multiple conditions, return a choice from choices.

        Args:
            condition (list, optional): Array of conditions. Defaults to None.
            choices (list, optional): Array of choices. Defaults to None.
            default_value ([type], optional): Array or unique value to replace the Falses. Defaults to None.
        """
        
        return pandas.Series(
            numpy.select(
                conditions,
                choices,
                default_value
            )
        )
    
    def match(
        self,
        series:pandas.Series,
        regex:str
    ) -> bool:
        """Check every value and indicates if it match the regex.
        
        Args:
            regex (str): Regular expression.

        Returns:
            bool: match or not.
        """
        
        r = re.compile(regex)

        vmatch = numpy.vectorize(
            lambda x:bool(r.match(x))
        )

        return vmatch(series)

    def strip(
        self,
        column_name:str
    ) -> None:
        
        """Clean the column by deleting the first or the last character
        if it's a space and by cleaning line breaks.
        """
        self.frame[column_name] = self.frame[
            column_name
        ].str.strip()

    def split(
        self,
        column_name:str,
        separator:str=None,
        split_patterns:List[dict]=None,
        columns:List[dict]=None
    ) -> None:
    
        if separator:
            self.frame[column_name] = numpy.char.split(
                self.frame[column_name].tolist(),
                sep =separator
            )

        elif split_patterns:

            series = self.frame[column_name]
            conditions=[]
            choices=[]

            for split_pattern in split_patterns:
                if 'match' in split_pattern:
                    conditions.append(
                        self.match(
                            series,
                            split_pattern['match']
                        )
                    )

                choices.append([
                    value[
                        split_pattern['start']:split_pattern['stop']
                    ]
                    for value in self
                ])

            self.frame[column_name] = self.modifyValuesMultiple(
                conditions,
                choices
            )
        
        elif columns:
            for column in columns:
                new_column_name = column.pop('name')
                self.frame[new_column_name] = self.frame[
                    column_name
                ].str.slice(**column)

    def add(
        self,
        column_name:str,
        value=None,
        column_to_copy:str=None
    ) -> None:

        if column_name not in self.frame.columns:

            if column_to_copy:
                self.frame[column_name] = self.frame[column_to_copy]
            elif value =='index':
                self.frame[column_name] = self.frame.index
            else:   
                self.frame[column_name] = value

    def aggregate(
        self,
        column_names:List[str],
        columns:dict={},
        **kwargs
    ) -> None:
        
        # check functions 
        functions = [
            'mean',
            'sum',
            'size',
            'count',
            'std',
            'var',
            'sem',
            'describe',
            'first',
            'last',
            'nth',
            'min',
            'max',
            'rank'
        ]

        if columns:
            for col in columns:
                function = columns[col]

                if col not in self.frame.columns:
                    self.frame[col]=None

                if function not in functions:
                    if function == 'list':
                        columns[col] = lambda x: x.values.tolist()

            self.frame = self.frame.groupby(
                column_names,
                **kwargs
            ).agg(columns).reset_index()

        else:
            self.frame = self.frame.groupby(
                column_names,
                **kwargs
            ).mean().reset_index()

    def toDateTime(
        self,
        column_name:str,
        format:str,
        column_type:str
    ) -> None:
        
        self.frame[column_name] = pandas.Series(
            pandas.to_datetime(
                self.frame[column_name],
                format=format
            )
        )

        self.setType(
            column_name,
            column_type
        )

    def toGeometry(
        self,
        column_name:str,
        geometry_type:str=None,
        coordinates_column:str=None,
        srid:int=4326,
        is_geojson=False,
        geometry_column:str='geometry',
        srid_to:int=None
    ) -> None:
        # if srid_to:
        #     self.frame.to_crs("EPSG:{}".format(srid_to))
        # geometry_type = list(self.frame.geom_type.unique())[0]

        final_geometry_type = None   
        transformer = pyproj.Transformer.from_proj(
            pyproj.Proj(init='epsg:{}'.format(srid)),
            pyproj.Proj(init='epsg:{}'.format(srid_to))
        ) if srid_to else None
        to_multi = False
    
        def getCoordinates(coordinates:list,transformer:Union[pyproj.Transformer,None]) -> Union[tuple,list]:
            return ' '.join(map(str,transformer.transform(*tuple(coordinates)) if transformer else coordinates))
           
        def Geometry(
            srid:int,
            transformer:Union[pyproj.Transformer,None],
            to_multi:bool,
            coordinates:list = [],
            type:str = None
        ) -> str:
        
            if type.lower() == 'point':
                if math.isnan(coordinates[0]) or math.isnan(coordinates[1]) or coordinates[0]==0 or coordinates[1]==0:
                    return None

                coordinates_wkt = getCoordinates(coordinates,transformer)
                if to_multi:
                    type = 'MultiPoint'
                    coordinates_wkt = '({})'.format(coordinates_wkt)
                
            elif type.lower() == 'linestring':

                coordinates_wkt = ','.join([
                    getCoordinates(coordinate,transformer)
                    for coordinate in coordinates
                ])

                if to_multi:
                    type = 'MultiLineString'
                    coordinates_wkt = '({})'.format(coordinates_wkt)

            elif type.lower() == 'polygon':

                coordinates_wkt = '({})'.format(','.join([
                    getCoordinates(coordinate,transformer)
                    for coordinate in coordinates[0]
                ]))
                
                if to_multi:
                    type = 'multipolygon'
                    coordinates_wkt = '({})'.format(coordinates_wkt)

            elif type.lower() == 'multipolygon':
                
                coordinates_wkt = ','.join([
                    '({})'.format(','.join([
                        '({})'.format(','.join([
                            getCoordinates(coordinate,transformer)
                            for coordinate in coordinates__
                        ]))
                        for coordinates__ in coordinates_
                    ]))
                    for coordinates_ in coordinates
                ])

            return 'SRID={};{} ({})'.format(str(srid),type.upper(),coordinates_wkt)

        if is_geojson:
            geometries = pandas.json_normalize(self.frame[geometry_column])
            geometry_types:List[str]=geometries['type'].unique().tolist()
            
            if len(geometry_types)>1:
                
                geometry_type:pandas.Series=geometries['type']

                final_geometry_type = [
                    geometry_type_ for geometry_type_ in geometry_types
                    if geometry_type_[0:5].lower() == 'multi'
                ][0]

                coordinates = geometries['coordinates']
                to_multi = True
                is_geojson = False
            else:
                geometry_type = geometry_types[0]

        else:
            coordinates = self.frame[coordinates_column]

        if not is_geojson:
            self.frame[geometry_column] = pandas.DataFrame({
                'type':geometry_type,
                'coordinates':coordinates
            }).to_dict(orient= 'records')  

        self.frame[column_name]=self.frame[geometry_column].apply(
            lambda x: Geometry(srid_to if srid_to else srid,transformer,to_multi,**x)
        )
        
        # self.data_types[column_name] = 'geometry({},{})'.format(
        #     final_geometry_type if final_geometry_type else geometry_type,
        #     srid_to if srid_to else srid
        # )
    
    def toDict(
        self,
        column_name:str,
        column_names:List[str]
    ) -> pandas.Series:
        
        self.frame[column_name] = self.frame[
            column_names
        ].to_dict(
            orient= 'records'
        )
    
    def toList(
        self,
        column_name:str,
        column_names:List[str]
    ) -> None:
        
        self.frame[column_name] = self.frame[
            column_names
        ].values.tolist()
    
    def normalize(
        self,
        column_name:str,
        method:str,
        factor:int,
        root:int,
        base:str
    ) -> None:
    
        if method == 'interquartile':    
            self.frame[column_name] = self.frame[column_name]/(factor*iqr(self))

        elif method == 'root':   
            self.frame[column_name] = self.frame[column_name]**(1/int(root))

        elif method == 'log':   
            self.frame[column_name] = math.log(self.frame[column_name],base)

        elif method == 'square':
            self.frame[column_name] = self.frame[column_name]**2

    def pivot(
        self,
        values:list,
        index:list,
        column_names:list
    ) -> None:
        
        self.frame = pandas.pivot_table(
            self.frame,
            values=values,
            index=index,
            columns=column_names,
            aggfunc=numpy.sum
        ).reset_index()
     
    def explode(
        self,
        column_name:str
    ) -> None:
    
        self.frame = self.frame.explode(
            column_name
        ).reset_index(drop=True)

    def listToColumns(
        self,
        column_name:str,
        column_names:List[str]
    ) -> None:
        
        self.frame[column_names] = pandas.DataFrame(
            self.frame[column_name].tolist(),
            index= self.frame.index
        )

    def dictToColumns(
        self,
        column_name:str,
        column_names:List[str]
    ) -> None:

        self.frame[column_names] = pandas.json_normalize(
            self.frame[column_name]
        )[column_names]

    def stack(
        self,
        column_name:str,
        column_names:List[str],
        differentiator:str
    ) -> None:

        stack_columns = [
            column for column in self.frame.columns
            if column not in column_names
        ]
        
        for column in stack_columns:

            self.frame[column_name] = self.frame[column]
            self.frame[differentiator] = column

            self.frame[column] = self.frame[
                [
                    column_name,
                    differentiator,
                    *column_names
                ]
            ].to_dict(orient= 'records')
            
            del self.frame[column_name]
            del self.frame[differentiator]

        self.frame = pandas.DataFrame(
            self.frame[stack_columns].stack(0),
            columns=[column_name]
        ).reset_index(drop=True)

        self.frame[[
            column_name,
            differentiator,
            *column_names
        ]] = pandas.DataFrame(
            self.frame[column_name].tolist(),
            index= self.frame.index
        )   
    
    def partition(
        self,
        nom_y,
        proportion,
        column_id
    ) -> None:

        X_train, X_test, y_train, y_test = train_test_split(
            self.frame.loc[:, self.frame.columns != nom_y],
            self.frame[nom_y],
            test_size=proportion
        )

        self.frame['train'] = False

        self.frame.loc[
            self.frame[column_id].isin(
                X_train[column_id].values
            ),
            'train'
        ] = True

    def loadJSON(
        self,
        column_name:str
    ) -> None:
        
        self.frame[column_name] = self.frame[
            column_name
        ].apply(
            lambda x : json.loads(x)
        )

    def getFunction(
        self,
        function_name:str,
        directory_name:str=None,
        module:str='__init__',
        code:str = None
    ) -> None:
        
        self.functions[function_name] = getFunction(
            function_name,
            directory_name if directory_name else self.code_directory,
            module,
            code,
            self.schema_name,
            self.schema_type
        )

    def applyFunction(
        self,
        function_name:str,
        column_names:list,
        output_columns:list,
        **kwargs
    ) -> Data:
        """Apply a function to the data frame.

        Args:
            transformation (Transformation): The transformation.

        Returns:
            Data: self.
        """

        if isinstance(
            column_names,
            list
        ) and len(column_names) == 1:
            column_names = column_names[0]

        if isinstance(
            output_columns,
            list
        ) and len(output_columns) == 1:
            output_columns = output_columns[0]
            
        self.frame['input'] = self.frame[
            column_names
        ].to_dict(
            'records'
        ) if isinstance(
            column_names,
            list
        ) else self.frame[column_names]

        self.frame[output_columns] = self.frame.apply(
            lambda x: self.executeApplyFunction(
                x['input'],
                function_name,
                **kwargs
            ),
            axis=1,
            result_type='expand' if isinstance(
                output_columns,
                list
            ) else None
        )
        
        del self.frame['input']

    def executeApplyFunction(
        self,
        input:Union[list,str,int],
        function_name:str,
        **kwargs
    ) -> Union[list,str,int]:
        """Apply a function to a value.

        Args:
            input (Union[list,str,int]): Input values.

        Returns:
            Union[list,str,int]: Return values.
        """
        
        function = self.functions[function_name]
        
        output = function(
            **input,
            **kwargs
        ) if isinstance(
            input,dict
        ) else function(input)
        
        return [
            output_ for output_ in output
        ] if isinstance(
            output, tuple
        ) else output

    def transformWithFunction(
        self,
        function_name:str,
        **kwargs:dict
    ) -> None:
        
        self.frame = self.functions[
            function_name
        ](self.frame,**kwargs)

    def getFile(
        self,
        file_name:str = None,
        directory_name:str = None,
        extra_data_name:str=None,
        transformations:List[dict]=[],
        file:File = None,
        **kwargs
    ) -> None:
        
        if not file:
            file = File(
                directory_name if directory_name else self.directory_name,
                file_name
            )
        
        extra_data = Data(
            file.read(**kwargs).content
        )

        for transformation in transformations:
            getattr(
                extra_data,
                transformation.pop('name')
            )(**transformation)

        self.extra_data[
            extra_data_name if extra_data_name else file_name
        ] = extra_data.frame
        
    def mergeExtraData(
        self,
        extra_data_name:str,
        **kwargs
    ) -> None:
        
        self.frame = pandas.merge(
            self.frame,
            self.extra_data[extra_data_name],
            **kwargs
        )

    def multiTransform(
        self,
        transform_elements:List[dict]
    ) -> None:
        
        frames = []
        data = self.frame.copy()
        
        for transform_element in transform_elements:

            transformations = transform_element.pop(
                'transformations'
            )
            filter = self.getFilter(
                **transform_element
            )
            transform_data = Data(
                data[filter].copy()
            )

            if transform_data.frame.shape[0]:
                transform_data.transform(
                    transformations
                )     
                frames.append(
                    transform_data.frame
                )
                data = data[~filter]

        frames.append(data)
        self.frame = pandas.concat(frames)
    
    def concat(
        self,
        column_name:str,
        columns:list
    ) -> None:
        
        self.frame[column_name] = self.frame[
            columns
        ].agg(
            ''.join,
            axis=1
        )

    def zFill(
        self,
        column_name:str,
        width:int
    ) -> None:
       
        self.frame[column_name] = self.frame[
            column_name
        ].str.zfill(width)
   
    def fillna(
        self,
        column_name:str,
        value
    ) -> None:
        
        self.frame[column_name] = self.frame[
            column_name
        ].fillna(value)
   
    def toNestedDict(
        self,
        module_name:str
    ) -> None:
        
        class_ = self.data_sets.getClass(**self.data_sets.getObjectMeta(
            self.data_sets.cleanName(self.name)
        ))

        data = {}

        for index,data_tuple in self.frame.iterrows():
            print(index, end='\r')
            object_ = class_(
                self.data_sets,
                **data_tuple
            )

            network_nodes = data.get(object_.link.network,{})
            node_links = network_nodes.get(object_.node.id,[])
            
            node_links.append(object_)

            network_nodes[object_.node.id] = node_links
            data[object_.link.network] = network_nodes

        self.frame = data

    def setSrid(
        self,
        column_name:str,
        srid:int
    ) -> None:
        
        column_index = self.getColumnIndex(column_name)

        if column_index is not None:
            
            self.meta_columns[column_index]['geometry']['srid_from'] = copy.deepcopy(
                self.meta_columns[column_index]['geometry']['srid']
            )
            self.meta_columns[column_index]['geometry']['srid'] = srid   

            self.meta_columns[column_index]['column_type'] = 'geometry({},{})'.format(
                self.meta_columns[column_index]['geometry']['type'],
                srid
            )

    def exportGeometry(
        self,
        index,
        geometry,
        export_format:str,
        type:str,
        srid:int,
        srid_from:int=None,
        saved_type:str = None,
        properties:dict = None
    ) -> dict:
        if export_format in ['json','geojson'] and geometry is not None:

            if properties is None:
                properties = {}
                row = self.frame.loc[[index]]

                for column_name,row_element_ in row.items():
                    column_geometry = self.getMetaColumn(column_name).get('geometry')


                    if column_geometry is None:

                        properties[column_name] = self.formatValue(row_element_.iloc[0])

            return {
                'type':'Feature',
                'properties':{
                    'index':index,
                    **properties
                },
                'geometry':shapely.geometry.mapping(geometry) if saved_type in ['text','shapely'] else {
                   'type':type,
                   'coordinates':geometry
                }
            }
        
        elif export_format== 'postgres':
            
            if saved_type == 'shapely':
                if type.upper() == 'POINT'and numpy.isinf(geometry.x):
                    return None
                return geometry.wkt
            
            if type.upper() == 'POINT':
                geometry = ' '.join(map(str,geometry))

            elif type.upper() == 'LINESTRING':
                geometry = ','.join([' '.join(map(str,geom)) for geom in geometry])

            return 'SRID={};{} ({})'.format(
                str(srid),
                type.upper(),
                geometry
            )
    
    def export(
        self,
        export_format:str='json',
        column_name:str=None,
        buffer_format = None
    ) -> Union[
        List[list],
        pandas.DataFrame
    ]:
        self.frame.reset_index(
            drop=True,
            inplace = True
        )
    
        if export_format == 'json':
            return [
                self.exportColumn(
                    column_name,
                    dtype,
                    self.loaded_rows,
                    export_format,
                    **self.getMetaColumn(column_name)
                )
                for column_name,dtype in zip(self.frame.columns,self.frame.dtypes)
            ]

        elif export_format == 'geojson':
            return {
                "type": "FeatureCollection",
                "features": list(
                    self.exportColumn(
                        column_name,
                        None,
                        export_format= export_format,
                        **self.getMetaColumn(column_name)
                    )
                )
            }
                
        elif export_format == 'postgres':
            frame = self.frame.copy()
            
            for column_name,dtype in zip(self.frame.columns,self.frame.dtypes):
                frame[column_name] = self.exportColumn(
                    column_name,
                    dtype,
                    export_format= export_format,
                    **self.getMetaColumn(column_name)
                )
                    
            return frame
        
        elif export_format == 'protobuf':
            records = getattr(buffer_format,'Data_{}'.format(self.name))()
            data_columns = self.columns
            
            for i,d in self.frame.iterrows():
                if i>2:
                    continue
            
                record = records.record_element.add()
                for column in data_columns:
                    value = d[column.get('name')]
                    if column.get('type') in ['bigint','int']:
                        value = int(value)
                    setattr(record,column.get('name'),value) if value else None
                
            return records

    async def select(
        self,
        where_statement:Union[
            dict,
            List[dict]
        ]
    ) -> None:
        
        # query,file_query, directory_query = manageQuery(
        #     self.name,
        #     directory_name=self.code_directory
        # )

        query_directory = os.path.join(
            self.code_directory,
            'queries' 
        )

        self.frame = await self.query_builder.select().sqlStatement(
            directory_name = query_directory if os.path.isdir(
                query_directory
            ) else self.code_directory,
            file_name = self.name,
            definition='select',
            schema_name=self.schema_name
        ).where(
            where_statement
        ).built().asyncExecute()
        
    async def get(
        self,
        to_get:str = 'data'
    ) -> Data:
        if to_get == 'self':
            return self
        
        if to_get == 'data':

            return Data(
                self.frame.copy(),
                connection = self.connection,
                code_directory= self.code_directory,
                name = self.name,
                meta_columns = self.meta_columns
            )
        return getattr(self,to_get)
    
    async def setData(
        self,
        data:Union[
            Data,
            pandas.DataFrame,
            None
        ]
    ) -> None:
        
        if data is not None:

            if isinstance(data,Data):
                self.frame = data.frame

            elif isinstance(data,pandas.DataFrame):
                self.frame = data
    
    async def write(
        self,
        directory_name:str=None,
        extension:str=None,
        file_name:str=None,
        column_name:str=None,
        buffer = None,
        buffer_format = None,
        file:File = None,
        *args,
        **kwargs
    ) -> None:
                
        if buffer:
            getattr(buffer,self.name).CopyFrom(self.export(
                'protobuf',
                buffer_format = buffer_format
            ))

        else:
            if not file:
                if directory_name is None:
                    directory_name = os.path.join(
                        os.getenv(
                            'DATA_DIRECTORY',
                            os.getcwd()
                        ),
                        'temporary'
                    )

                if file_name is None:
                    if column_name is not None:
                        file_name = '{}_{}.{}'.format(
                            self.name,
                            column_name,
                            extension
                        )
                    elif self.name is not None:
                        file_name = '{}.{}'.format(
                            self.name,
                            extension
                        )

                file = File(
                    directory_name,
                    file_name 
                )
            
            file.write(
                self.export(extension,column_name) if extension in ['geojson','json'] else self.frame,
                *args,
                **kwargs
            )

        if column_name is not None:
            return 'http://localhost:8003/{}'.format(file_name)
      
    async def read(
        self,
        directory_name:str = None,
        extension:str = None,
        file_name:str = None,
        *args,
        **kwargs
    ) -> None:
        if directory_name is None:
            directory_name = os.path.join(
                os.getenv(
                    'DATA_DIRECTORY',
                    os.getcwd()
                ),
                'temporary'
            )

        self.frame = File(
            directory_name,
            file_name if file_name else '{}.{}'.format(
                self.name,
                extension
            )
        ).read(
            *args,
            **kwargs
        ).content 
 
    async def columnAction(
        self,
        column_name:str,
        action_name:str
    ) -> None:
        column_index = self.getColumnIndex(column_name)

        if action_name == 'get_values':
            meta_column = {
                'name':column_name,
                'values':self.frame[column_name].value_counts().to_dict()
            }
            
        elif action_name == 'write':
            meta_column = {
                'name':column_name,
                'url':await self.write(
                    extension = 'geojson',
                    column_name = column_name
                )
            }
        
        elif action_name == 'describe':
            meta_column = {
                'name':column_name,
                'summary':self.frame[column_name].describe().to_dict()
            }

        if column_index is None:
            self.meta_columns.append(meta_column)
        else:
            
            self.meta_columns[column_index] = {
                **self.meta_columns[column_index],
                **meta_column
            }

    async def protocolFormat(
        self,
        main_message:list,
        index:int
    ) -> str:
        main_message.append(
            '\tData_{} {} = {};'.format(self.name,self.name,index+1),
        )

        return '\n'.join([
            'message Record_{} {}'.format(self.name,'{'),
            '\n'.join([
                '\t{} {} = {};'.format(
                    {
                        'str':'string',
                        'float64':'float',
                        'object':'string',
                        'datetime64[ns]':'string'
                    }.get(c.get('dtype'),c.get('dtype')),
                    c.get('name'),
                    i+1
                )
                for i,c in enumerate(self.columns)
            ]),
            '}',
            'message Data_{} {}'.format(self.name,'{'),
            '\trepeated Record_{} record_element = 1;'.format(self.name),
            '}'
        ])

    async def manageCache(
        self,
        extension:str,
        directory_name:str = None,
        action:str = None
    ) -> None:

        path = os.path.join(directory_name,'{}.{}'.format(
            self.name,
            extension
        ))
        if action in ['start','load'] and os.path.isfile(path):
            await self.read(
                directory_name,
                extension
            )
            return True
        elif action in ['end','load_end']:
            await self.write(
                directory_name,
                extension
            )

        return False
    
    def printFrame(
        self,
        column_names:List[str] = [],
        print_columns = True,
        unique_column = None
    ) -> None:
        print(self.frame[column_names] if column_names else self.frame)
        if print_columns:
            print(list(self.frame.columns))

        if unique_column is not None and unique_column in self.frame.columns:
            print(self.frame[unique_column].unique())

    
