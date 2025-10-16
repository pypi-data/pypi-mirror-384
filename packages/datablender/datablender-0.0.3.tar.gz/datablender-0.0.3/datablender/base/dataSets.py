from typing import Dict,List,Union

import pandas

from datablender.base import (
    getModule
)

class DataSets:
    """description

    Attributes:
    ----------
        Attributes

    Methods:
    ----------
        Methods

    Examples:
    ----------
        >>> Example

    """
    def __init__(
        self,
        module_name:str = None,
        package_name:str = None,
        objects:List[dict] = [],
        directory_name:str = None
    ):  
        self.objects = objects
        self.directory_name = directory_name
        
        self.module = getModule(
            self.directory_name,
            module_name,
            package_name
        ) if isinstance(module_name,str) or isinstance(package_name,str) else module_name
        
    def initiateData(
        self,
        data:Dict[str,Union[List[tuple],List[dict],pandas.DataFrame]] = {},
        data_meta:Union[dict,List[dict]] = []
    ) -> None:

        for data_set_name_,data_set in data.items():
            data_set_name = self.cleanName(data_set_name_)

            object_meta = self.getObjectMeta(data_set_name)

            if object_meta and 'transform' in object_meta:
                data_set = data_set.to_dict('records')

            if data_set_name in list(data.keys()):
                data_set_name = data_set_name_

            setattr(self,data_set_name,data_set)
    
        self.data_meta = [data_meta] if isinstance(data_meta,dict) else data_meta

        for data_set_meta in self.data_meta:
            if 'columns' in data_set_meta:
                setattr(self,data_set_meta.get('name'),[])
    
        self.ids = []

    def getObjectMeta(
        self,
        name:str
    ) -> Dict[str,Union[str,List[dict]]]:
        return next((o for o in self.objects if o.get('name') == name),{})

    def getData(
        self,
        object_name:str,
        filter = None,
        reverse_bridge_object:bool = False,
    ) -> list:
        if hasattr(self,object_name):

            object_meta = self.getObjectMeta(object_name)
            data:pandas.DataFrame = getattr(self,object_name)
            if filter is not None :  data = data[filter] 

            if not object_meta:
                names = object_name.split('_')
                if len(names) == 2 and names[0] == names[1]:
                    object_name = names[0]
                    object_meta = self.getObjectMeta(object_name)
                    data.rename(
                        {c:c[:-2] for c in data.columns if c[-2:] == ('_0' if reverse_bridge_object else '_1')},
                        axis='columns',
                        inplace=True
                    )
            class_ = self.getClass(**object_meta)

            return [
                class_(
                    self,
                    **object_attributes
                )
                for object_index,object_attributes in
                data.iterrows()
            ]
        
        return []
    
    def getClass(
        self,
        class_name:str,
        **kwargs
    )-> None:
        return getattr(
            self.module,
            class_name
        )
        
    def setDataAttributes(
        self,
        object_name:str,
        filter,
        object
    ) -> None:
        
        attribute_values:pandas.DataFrame = getattr(
            self,
            object_name,
        )[filter]

        if attribute_values.shape[0]: self.setObjectAttributes(
            object_name,
            attribute_values.iloc[0].to_dict(),
            object
        )

    def setObjectAttributes(
        self,
        object_name:str,
        attribute_values:Dict[str,str],
        object
    ) -> None:
    
        attributes = self.getObjectMeta(object_name).get('attributtes')

        for attribute_name,attribute_value in attribute_values.items():
            attribute_meta = next((a for a in attributes if a.get('name') == attribute_name),{})
            if attribute_meta:
                setattr(
                    getattr(object,attribute_meta.get('sub_object')) if 'sub_object' in attribute_meta else object,
                    attribute_meta.get('name'),
                    attribute_value
                )

    def setData(self) -> None:
        for data_set_meta in self.data_meta:
            if 'columns' in data_set_meta:

                setattr(
                    self,
                    data_set_meta.get('name'),
                    pandas.DataFrame(
                        getattr(
                            self,
                            data_set_meta.get('name'),
                        ),
                        columns = data_set_meta.get('columns')
                    ).assign(
                        **data_set_meta.get('assign')
                    )
                )

            # print()
            # print(getattr(self,data_set_meta.get('name')))

        return {
            data_set_meta.get('name'):getattr(self,data_set_meta.get('name'))
            for data_set_meta in self.data_meta
        }

    def insertData(
        self,
        object_name:str,
        to_delete,
        to_insert:List[tuple]
    ) -> None:
        object_meta = self.getObjectMeta(object_name)
        data:pandas.DataFrame = getattr(self,object_name)

        data.drop(
            index=data[to_delete].index,
            inplace=True 
        )
        data.reset_index(
            drop=True,
            inplace= True
        )

        data = pandas.concat([
            data,
            pandas.DataFrame(
                to_insert,
                columns = object_meta.get('columns')
            )
        ])

        data.reset_index(
            drop=True,
            inplace=True
        )

        setattr(self,object_name,data)

    def processObject(
        self,
        object_meta:Dict[str,Union[str,List[dict]]],
        object_attributes,
        action:str
    ) -> None:
        getattr(
            self.getClass(**object_meta)(
                self,
                **object_attributes
            ),
            action
        )() 

    def cleanName(self,data_set_name:str) -> str:

        while data_set_name[-1] == '_':
            data_set_name = data_set_name[:-1]

        return data_set_name
