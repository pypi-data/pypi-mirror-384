"""

"""

from __future__ import annotations
from typing import Dict

import os

class DirectoryElementController:
    """Object to control file in a directory according to given params.

    Attributes:
    ----------
        extensions (list): Accepted extensions.
        ignored_elements (list, optional): Ignored elements. Defaults to None.
        sub_element_contain (str, optional): Elements to accept if the element name contains. Defaults to None.
        start_string (str, optional): Element to accept if the element name start with this. Defaults to None.

    Methods:
    ----------
        control(self,element_name:str) -> Tuple[bool, bool, bool, bool] : Control element with his name.
        checkExtensions(self,element_name:str) -> bool : Check if element extension is in the given extensions.

    Examples:
    ----------
        >>> import datablender

    """
    def __init__(
        self,
        file_controls:Dict[Dict[str,bool]]={},
        directory_controls:Dict[Dict[str,bool]] = {},
        zip_file_controls:Dict[Dict[str,bool]] = {}
    ):
        """Initiate the controller.

        Args:
            extensions (list): Accepted extensions.
            ignored_elements (list, optional): Ignored elements. Defaults to None.
            sub_element_contain (str, optional): Elements to accept if the element name contains. Defaults to None.
            start_string (str, optional): Element to accept if the element name start with this. Defaults to None.
        """

        self.file_controls = file_controls
        self.directory_controls = directory_controls
        self.zip_file_controls = zip_file_controls
    
    @property
    def configuration(self):
        """Get configuration.

        Returns:
            dict: configuration.
        """
        return {
            'file_controls':self.file_controls,
            'directory_controls':self.directory_controls,
            'zip_file_controls':self.zip_file_controls
        }

    def controlFile(
        self,
        file_name:str,
        elements:Dict[str,bool] = {},
        extensions:Dict[str,bool]  = {},
        contains:Dict[str,bool]  = {},
        start:Dict[str,bool]  = {},
        patterns:Dict[str,bool]  = {}
    ) -> bool:
    
        for element in elements:
            if file_name == element:
                return elements.get(element)

        if (
            elements 
            and file_name not in elements 
            and any([elements[element] for element in elements])
        ):
            return False
           
        verifications = []    
        extension_verification = []

        for extension in extensions:

            if extensions[extension]:
                extension_verification.append(
                    file_name[-len(extension):].lower() == extension
                )
            else:
                extension_verification.append(
                    file_name[-len(extension):].lower() != extension
                )

        verifications.append(
            any(extension_verification)
        ) if extensions else None

        # for contain in self.contains:
        #     if self.contains[contain]:
        #         verifications.append(
        #             contain in element_name.lower()
        #         )
        #     else:
        #         verifications.append(
        #             contain not in element_name.lower()
        #         )

        # for start_ in self.start:
        #     sub_string_len = len(start_)

        #     if self.start[start_]:
        #         verifications.append(
        #             element_name[:sub_string_len] == start_
        #         )
        #     else:
        #         verifications.append(
        #             element_name[:sub_string_len] != start_
        #         )

        return all(
            verifications
        ) if verifications else True
    
    def controlZipfile(
        self,
        file_name:str,
        elements:Dict[str,bool] = {},
    ) -> None :
        if elements:
            for element in elements:
                if file_name == element:
                    return elements.get(element)
        else:
            return True
    
    def controlDirectory(
        self,
        directory_name:str,
        elements:Dict[str,bool] = {},  
    ) -> None :
        if elements:
            for element in elements:
                if os.path.basename(directory_name) == element:
                    return elements.get(element)
        else:
            return True

    def control(
        self,
        element_name:str,
        element_type:str
    ) -> bool:
        """Control element with his name.

        Args:
            element_name (str): Element name.

        Returns:
            self: Controls.
        """
            
        if element_type == 'file':
            return self.controlFile(element_name,**self.file_controls)
        
        elif element_type == 'directory':
            return self.controlDirectory(element_name,**self.directory_controls)
    
        elif element_type == 'zipfile':
            return self.controlZipfile(element_name,**self.zip_file_controls)
