"""
"""
from __future__ import annotations

import copy
import requests
import aiohttp

class Request:
    """Represent a request.

    Attributes:
    ----------
        is_secure (bool): Is the url secure.
        host (str): Host.
        port (int): Port.
        domain_name (str): Domain name.

    Methods:
    ----------
        getBaseUrl(self) -> None:.

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        is_secure:bool=False,
        host:str='localhost',
        port:int=None,
        domain_name:str=None
    ):
        """Initiate the request

        Args:
            is_secure (bool, optional): Is the url secure. Defaults to False.
            host (str, optional): Host. Defaults to 'localhost'.
            port (int, optional): Port. Defaults to None.
            domain_name (str, optional): Domain name. Defaults to None.
        """
        self.is_secure=is_secure
        self.host=host
        self.port=port
        self.domain_name=domain_name
        self.reset()
    
    @property
    def base_url(self) -> str:
        """Get base url.

        Returns:
            str: Base url.
        """
        return ''.join([
            'https' if self.is_secure else 'http',
            '://',
            self.domain_name if self.domain_name else self.host+':'+str(self.port)
        ])

    def reset(self):
        self.url=copy.deepcopy(self.base_url)

    def addElement(self,element:str):
        self.url='/'.join([self.url,element])
    
    def addParameter(self,parameter_name:str,parameter_value):
        joiner='&' if '?' in self.url else '?'
        self.url = joiner.join([
            self.url,
            '='.join([
                parameter_name,
                str(parameter_value)
            ])
        ])

    def addParameters(self,parameters:dict):
        for parameter in parameters:
            self.addParameter(parameter,parameters[parameter])
    
    def get(self,**kwargs):
        self.response = requests.get(self.url,**kwargs)

    def post(self,**kwargs):
        self.response = requests.post(self.url,**kwargs)

    def put(self,**kwargs):
        self.response = requests.put(self.url,**kwargs)
        
    def delete(self,**kwargs):
        self.response = requests.delete(self.url,**kwargs)

class AsyncRequest:
    """Represent a request.

    Attributes:
    ----------
        is_secure (bool): Is the url secure.
        host (str): Host.
        port (int): Port.
        domain_name (str): Domain name.

    Methods:
    ----------
        getBaseUrl(self) -> None:.

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        is_secure:bool=False,
        host:str='localhost',
        port:int=None,
        domain_name:str=None,
        loop = None,
        session:aiohttp.ClientSession = None
    ):
        """Initiate the request

        Args:
            is_secure (bool, optional): Is the url secure. Defaults to False.
            host (str, optional): Host. Defaults to 'localhost'.
            port (int, optional): Port. Defaults to None.
            domain_name (str, optional): Domain name. Defaults to None.
        """
        self.is_secure=is_secure
        self.host=host
        self.port=port
        self.domain_name=domain_name
        self.loop = loop
        self.session = session
        self.session_has_base = False
        self.reset()

    async def setSession(self) -> None:
        self.session = aiohttp.ClientSession(
            self.base_url,
            loop = self.loop
        )
        self.session_has_base = True

    async def close(self) -> None:
        if self.session is not None:
            await self.session.close()
            self.session = None

    @property
    def base_url(self) -> str:
        """Get base url.

        Returns:
            str: Base url.
        """
        return ''.join([
            'https' if self.is_secure else 'http',
            '://',
            self.domain_name if self.domain_name else self.host+':'+str(self.port)
        ])

    def reset(self):
        self.url='' if self.session_has_base else self.base_url

    def addElement(self,element:str):
        self.url='/'.join([self.url,element])
    
    def addParameter(self,parameter_name:str,parameter_value):
        joiner='&' if '?' in self.url else '?'
        self.url = joiner.join([
            self.url,
            '='.join([
                parameter_name,
                str(parameter_value)
            ])
        ])

    def addParameters(self,parameters:dict):
        for parameter in parameters:
            self.addParameter(parameter,parameters[parameter])
