from abc import ABC, abstractmethod
from typing import Any

from torch.utils.data import Dataset

class Data(ABC): 
    """
        The Data class is an abstract class that defines the methods
        that get and process the data for the model to train on.

        The data_dir will be passed to the install, preprocess, and
        uninstall methods. The data_dir is the directory where the
        data, or database-storage is located.

        The install method is used to install the data. This can be
        downloading the data from a URL, or loading the data from
        a database to a file; it could even ignore the data_dir and
        just load the data from a local or remote database server.
    """
    @abstractmethod
    def install(self, data_dir) -> bool:
        pass


    @abstractmethod
    def preprocess(self, data_dir) -> bool:
        pass


    @abstractmethod
    def uninstall(self, data_dir) -> bool:
        pass