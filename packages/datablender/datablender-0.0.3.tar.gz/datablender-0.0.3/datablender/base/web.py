"""
"""

from __future__ import annotations
from typing import Union,Dict

from sys import platform
import copy

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement as SeleniumWebElement

if platform == "win32":
    from webdriver_manager.chrome import ChromeDriverManager
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
else:
    from selenium.webdriver.firefox.options import Options

from datablender.base.text import Text
from datablender.base import getFunction

class WebElement:
    """Represent a web element.

    Attributes:
    ----------
        attributes_name (list) : attributes name.
        tag_name (str): Tag name.
        text (str): Text in the element.
        attributes (dict): Element attributes.
        mark (tuple) : Element mark.

    Methods:
    ----------
        fromElement(self,element:SeleniumWebElement) -> WebElement: Set attributes from selenium web element.
        mark(self) -> tuple: Set mark of the web element.

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        tag_name:str=None,
        text:str=None,
        attributes:Dict[str,str] = {},
        driver:webdriver.Chrome=None,
        element:SeleniumWebElement = None
    ):
        """Initiate the web element.

        Args:
            tag_name (str, optional): Tag name. Defaults to None.
            text (str, optional): Text in the element. Defaults to None.
            attributes (Dict[str,str], optional): Element attributes. Defaults to {'id':None,'href':None,'class':None,'name':None,'onclick':None}.
        """

        if element:
            self.tag_name = element.tag_name
            self.text = element.text
            if driver:
                self.attributes = driver.execute_script(
                    """
                    var items = {};
                    for (index = 0; index < arguments[0].attributes.length; ++index) {
                        items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value
                    };
                    return items;
                    """,
                    element
                )
            else:
                self.attributes = attributes
        else:
            self.tag_name = tag_name
            self.text = text
            self.attributes=attributes

    @property
    def mark(self) -> tuple:
        """Mark of the element.

        Returns:
            tuple: mark.
        """
        
        if self.tag_name:
            if self.attributes:

                attributes = ''.join([
                    "[@{}='{}']".format(attribute,self.attributes[attribute])
                    if self.attributes[attribute] is not None
                    else "[@{}]".format(attribute)
                    for attribute in self.attributes
                ])

                if self.text is not None:
                    return (By.XPATH,"//"+self.tag_name+attributes+"[text()='"+self.text+"']")
                else:
                    return (By.XPATH,"//"+self.tag_name+attributes)
            elif self.text:
                return (By.XPATH,"//"+self.tag_name+"[text()='"+self.text+"']")        
            else:
                return (By.TAG_NAME,self.tag_name)
        
        elif self.text:
            return (By.LINK_TEXT,self.text)

        elif self.attributes.get('id'):
            return (By.ID,self.attributes.get('id'))

        elif self.attributes.get('class'):
            return (By.CLASS_NAME,self.attributes.get('class'))

        elif self.attributes.get('name'):
            return (By.NAME,self.attributes.get('name'))
        
    def setValue(
        self,
        value:str,
        attribute_name:str
    ):
        
        if attribute_name == 'text':
            self.text = Text(self.text).replace(value,'__possible_value__').text
        else:
            self.attributes[attribute_name] = Text(
                self.attributes.get(attribute_name)
            ).replace(
                value,
                '__possible_value__'
            ).text

class BotAction:
    """An action execute by the bot.

    Attributes:
    ----------
        base_url (str): Base url.
        name (str): Action name.
        url_path (str): Url path.
        url (str): Base url + the url path.
        tag_name (str): Tag name.
        element_text (str): Text of the web element.
        element_attributes (dict): Attributes of the web element.
        multi_mode (dict): Mode if there's multiple element.
        attribute_name (str): Attribute name to modify if it is multiple.
        values (Union[list,dict]): Values to try if it is multiple.
        start_value (Union[str,int]): Start value if it is multiple.
        execute_previous_action (bool): Indicate if the previous action is execute after each iteration.
        web_element (WebElement): Web element related to the action.

    Methods:
    ----------
        url(self) -> str: Get full url.
        getPossibleValues(self,previous_value:str) -> list:Get values to try.

    Examples:
    ----------
        >>> import datablender
        >>> bot_action = datablender.BotAction(
        >>>     'https://transitfeeds.com',
        >>>     'click_button',
        >>>     tag_name='a',
        >>>     element_attributes={'href':'/p/__possible_value__'}
        >>> )

    """
    def __init__(
        self,
        base_url:str,
        name:str,
        url_path:str=None,
        tag_name:str=None,
        element_text:str=None,
        attributes:Dict[str,str] = {},
        multi_mode:str=None,
        attribute_name:str=None,
        values:Union[list,dict]=None,
        start_value:Union[str,int]=None,
        execute_previous_action:bool=False,
        module:str = None,
        function_name:str = None
    ):  
        """Initiate the action.

        Args:
            base_url (str): Base url.
            name (str): Action name.
            url_path (str, optional): Url path. Defaults to None.
            tag_name (str, optional): Tag name. Defaults to None.
            element_text (str, optional): Text of the web element. Defaults to None.
            attributes (Dict[str,str], optional): Attributes of the web element.
                Defaults to {'id':None,'href':None,'class':None,'name':None,'onclick':None}.
            multi_mode (str, optional): Mode if there's multiple element. Defaults to None.
            attribute_name (str, optional): Attribute name to modify if it is multiple. Defaults to None.
            values (Union[list,dict], optional): Values to try if it is multiple. Defaults to None.
            start_value (Union[str,int], optional): Start value if it is multiple. Defaults to None.
            execute_previous_action (bool, optional): Indicate if the previous action is execute after each iteration. Defaults to False.
        """
        self.name = name
        self.base_url=base_url
        self.url_path=url_path
        self.multi_mode = multi_mode
        self.attribute_name = attribute_name
        self.values = values
        self.start_value = start_value
        self.execute_previous_action = execute_previous_action
        self.module = module
        self.function_name = function_name
        
        self.web_element = WebElement(
            tag_name,
            element_text,
            attributes
        )

    @property
    def url(self) -> str:
        """Get full url.

        Returns:
            str: url.
        """
        return self.base_url+self.url_path
    
    def getPossibleValues(self,previous_value:str) -> list:
        """Get values to try.

        Args:
            previous_value (str): Value of the previous action.

        Returns:
            list: List of possible values.
        """
        return self.values[previous_value] if previous_value else self.values

class Bot:
    """Represent a bot.

    Attributes:
    ----------
        headless (bool): Display the browser.
        is_secure (bool): Is the url secure.
        domain_name (str): Domain name.
        host (str): Host.
        port (int): Port.
        base_url (str): Base url from domain name or host and port.
        chrome_options (Options) : Chrome options.
        results (list) : results get by the bot.

    Methods:
    ----------
        base_url(self) -> str: Get base url.
        open(self) -> None: Open selenium bot.

    Examples:
    ----------
        >>> import datablender
        >>> bot = datablender.Bot(domain_name='transitfeeds.com')
        >>> actions = [
        >>>     {
        >>>         'name':'get',
        >>>         'url_path':'/l/54-quebec-canada'
        >>>     },
        >>>     {
        >>>         'name':'click_button',
        >>>         'tag_name':'a',
        >>>         'element_attributes': {
        >>>             'href':'/p/agence-metropolitaine-de-transport'
        >>>         }
        >>>     }
        >>> ]
        >>> bot.open()
        >>> bot.executeActions(actions)
        >>> bot.close()

    """
    def __init__(
        self,
        headless:bool=True,
        is_secure:bool=True,
        domain_name:str=None,
        host:str=None,
        port:int=None,
        schema_name:str =None,
        directory_name:str = None
    ):
        """Initiate the bot.

        Args:
            headless (bool, optional): Display the browser. Defaults to True.
            is_secure (bool, optional): Is the url secure. Defaults to True.
            domain_name (str, optional): Domain name. Defaults to None.
            host (str, optional): Host. Defaults to None.
            port (int, optional): Port. Defaults to None.
        """
        self.is_secure = is_secure
        self.domain_name = domain_name
        self.host = host
        self.port = port
        self.schema_name = schema_name
        self.directory_name = directory_name

        #param of chrome
        self.options = Options()

        # manage option to lunch the driver in headless
        if headless:
            self.options.add_argument("--headless")

        self.options.add_argument("--window-size=2000,1440")

        if platform == "win32":
            #option to set if file in headless
            self.options.add_experimental_option(
                "prefs",
                {
                    "download.prompt_for_download": False,
                    'w3c': False,
                    'download.default_directory': self.directory_name,
                    'download.directory_upgrade': True,
                    'safebrowsing.enabled': True
                }
            )

        self.results = []
    
    @property
    def base_url(self) -> str:
        """Get base url.
        """
        return ''.join([
            'https' if self.is_secure else 'http',
            '://',
            self.domain_name if self.domain_name else self.host+':'+str(self.port)
        ])

    def open(self) -> None:
        """Open selenium bot.

        Args:
            actions (list, optional): Actions to be execute by the bot. Defaults to None.
        """
        
        if platform == "win32":
            self.driver = webdriver.Chrome(
                #service=Service(ChromeDriverManager().install()),
                options=self.options
            )
        else:
            self.driver = webdriver.Firefox(
                options=self.options
            )

        self.wait = WebDriverWait(self.driver, 10)

    def close(self) ->None:
        """close selenium bot.
        """
        self.driver.close()
    
    def get(self, url:str) ->None:
        """Go to a website.

        Args:
            url (str): url of site.
        """
        # print('\t\tget --------------- url : ',url)

        self.driver.get(url)

    def clickButton(self, mark:tuple) -> None:
        """Click on a button

        Args:
            mark (tuple, optional): Mark of the button. Defaults to None.
        """
        button = self.wait.until(
            EC.element_to_be_clickable(mark)
        )
        # print('\t\tclickButton --------------- href : ',button.get_attribute('href'))
        button.click()

    def findElement(self,mark:tuple) -> WebElement:
        """Find a element in a web page.

        Args:
            mark (tuple): the mark of the element.

        Returns:
            WebElement: the element.
        """
        return WebElement(
            driver = self.driver,
            element=self.driver.find_element(*mark)
        )
        
    def findElements(self,mark:tuple) -> list[WebElement]:
        """Find all elements in a web page.

        Args:
            mark (tuple): the mark of the elements.

        Returns:
            list[WebElement]: List of elements.
        """
        return [
            copy.deepcopy(WebElement(
                driver=self.driver,
                element = element
            ))
            for element in self.driver.find_elements(*mark)
        ]

    def executeAction(
        self,
        action:BotAction,
        actions:list=[],
    ) -> Union[list[WebElement],WebElement,None]:
        """Execute bot action.

        Args:
            action (BotAction): bot action to execute.

        Returns:
            Union[None,list[WebElement],WebElement]: Element or elements result by the action.
        """
        if action.name=='get':
            self.get(action.url)

        elif action.name=='click_button':
            self.clickButton(action.web_element.mark)
        
        elif action.name == 'find_element':
            return self.findElement(action.web_element.mark)
        
        elif action.name == 'find_elements':
            return self.findElements(action.web_element.mark)

        elif action.name == 'executeFunction':
            function = getFunction(
                action.function_name,
                None,
                action.module,
                schema_type='source',
                schema_name=self.schema_name,
            )
            return function(self,actions)

    def executeActions(
        self,
        actions:list,
        past_values:list=[]
    ):
        """Execute actions.

        Args:
            actions (list): Actions to execute.
            past_values (str, optional): Value of previous action. Defaults to [].
        """

        while actions:
            # print('executeActions : ',[a['name'] for a in actions])
            # print('\texecute action : ',actions[0].get('name'))
            break_loop = self.manageAction(
                BotAction(
                    self.base_url,
                    **actions.pop(0)
                ),
                actions,
                past_values
            )

            if break_loop:
                break

    def manageAction(
        self,
        action:BotAction,
        actions:list=[],
        past_values:list=[]
    ):
        """Manage action.

        Args:
            action (BotAction): Action to manage.
            actions (list, optional): Other actions to execute. Defaults to None.
            past_values (list, optional): Value of previous action. Defaults to [].
        """
        # print(
        #     '\tmanage action : ',action.name,
        #     ' -- multi_mode : ',action.multi_mode,
        #     ' -- values ',[v for v in action.values] if action.values else None
        # )

        if action.multi_mode=='replace':
            for value in action.values:
                self.get(action.url.replace(
                    '__possible_value__',
                    value                    
                ))
                self.executeActions(copy.deepcopy(actions))
            return True

                # action.web_element.setValue(
                #     str(value),
                #     action.attribute_name
                # )
                # print(action.attributes)
                #self.executeAction(action)

            # initial_url = copy.deepcopy(self.driver.current_url)
            
            # for value in action.getPossibleValues(past_values[-1] if past_values else None):

            #     self.executeMultiAction(
            #         value,
            #         action,
            #         copy.deepcopy(actions),
            #         initial_url,
            #         copy.deepcopy(past_values)
            #     )

        elif action.multi_mode=='get':

            self.results.extend([
                element.attributes.get(action.attribute_name)
                for element in self.executeAction(action)
            ])
            # print('\tresults : ',len(self.results),self.results[0],self.results[-1])

        elif action.multi_mode=='iterate':
            value = action.start_value
            # print('\t\tvakue : ',value)
            while value:
                value = self.executeMultiAction(
                    value,
                    action,
                    copy.deepcopy(actions),
                    past_values=copy.deepcopy(past_values)
                )
                if value == 3:
                    break
                # print('\t\tnext value',value)

        else:
            return self.executeAction(action,actions)

        # print('\tmanage action -- end ----- actions : ',[a['name'] for a in actions])

        self.previous_action = action
  
    def executeMultiAction(
        self,
        value:str,
        action:BotAction,
        actions:list,
        initial_url:str=None,
        past_values:list=[]
    ) -> Union[None,int]:
        """Execute multi action.

        Args:
            value (str): Value to set.
            action (BotAction): Action to execute.
            actions (list): Other actions to execute.
            initial_url (str, optional): Url from where the multi action is execute. Defaults to None.
            past_values (list, optional): Value of previous action. Defaults to [].

        Returns:
            Union[None,int]: next value if it's an iteration.
        """
        if initial_url:
            self.get(initial_url)

        action_ = copy.deepcopy(action)
        
        action_.web_element.setValue(str(value),action.attribute_name)
        # print('\t\ttext : ',action_.web_element.text)

        try:
            self.executeAction(action_)
        except:
            return None
        
        # print('\t\tprevious_action : ',self.previous_action.name)
        # print('\t\texecute_previous_action : ',action_.execute_previous_action)

        if action_.execute_previous_action:
            self.manageAction(self.previous_action)
        
        # past_values.append(value)
        # self.executeActions(actions,past_values)


        return value+1 if isinstance(value,int) else None
