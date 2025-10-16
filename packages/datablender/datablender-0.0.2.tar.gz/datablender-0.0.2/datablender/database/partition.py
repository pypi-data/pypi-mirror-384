"""

"""

from data_utils.base import Connection,DataConfiguration
from data_utils.database.elementSQL import SchemaElement


class Partition(SchemaElement):
    """Partition of a table.

    Attributes:
    ----------
        Attributes

    Methods:
    ----------
        Methods

    Examples:
    ----------
        >>> import data_utils

    """
    def __init__(self,name):
        super(Partition,self).__init__(name)