"""
"""
from __future__ import annotations
import re
import unidecode

class Text:
    """Text class
    """
    def __init__(self,text:str):
        """Text class
        Args:
            text (str): text to eddit
        """
        self.text = text

    def replace(self,replace_with:str="",to_replace:str= "",is_reg_ex:bool=False) -> Text:
        """Replace substring in text
        Args:
            replace_with (str, optional): Substring to replace with. Defaults to replace with"".
            to_replace (str, optional): Element to replace. Defaults to "".
            is_reg_ex (bool, optional): Is the element to replace with is a regular expression?. Defaults to False.
        """
        if isinstance(replace_with, list) and isinstance(to_replace, list):

            if not isinstance(is_reg_ex, list):
                reg_ex = [is_reg_ex] * len(replace_with)

            for i in range(0,len(replace_with)):
                if reg_ex[i]:
                    self.text = re.sub(to_replace[i],replace_with[i],self.text)
                else:
                    self.text = self.text.replace(to_replace[i],replace_with[i])

        else:
            if is_reg_ex:
                self.text = re.sub(to_replace,replace_with,self.text)
            else:
                self.text = self.text.replace(to_replace,replace_with)
        
        return self

    def add_text(self,text_to_add):
        self.text=self.text+text_to_add

    def removeAccents(self):
        """Removes accents from a string
        """
        self.text = unidecode.unidecode(self.text)
        
    def removeSpaces(self):
        """Removes spaces from a string
        """
        wordsList = self.text.replace(" ",'_')

    def removeSpecialChar(self):
        """Replace anny non alpha numerical char with _
        """

        self.text = re.sub(r"\$", "_dollar_", self.text)
        self.text = re.sub(r"\W+", "_", self.text)

    def format(self):
        """Normalizes a string. It will put lettre in lower, remove accent spaces and special char
        """
        self.text = self.text.lower()
        self.removeAccents()
        self.removeSpaces()
        self.removeSpecialChar()
        return self

def formatText(input:str):
    """Format a string
    Args:
        input (str): String to format
    Returns:
        str: Format string
    """
    return Text(input).format().text