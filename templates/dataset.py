from pymind.data import Data

class MindData(Data):
    def __init__(self, data_dir):
        self.data_dir = data_dir

    def __install__(self):
        pass

    def __preprocess__(self):
        pass

    def __uninstall__(self):
        pass