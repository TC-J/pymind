from pymind.data import Dataset

class MindDataset(Dataset):
    def __init__(self, data_dir):
        self.data_dir = data_dir

    def __len__(self):
        pass

    def __getitem__(self, idx):
        pass

    def install(self, data_dir):
        pass

    def preprocess(self, data_dir):
        pass

    def uninstall(self, data_dir):
        pass