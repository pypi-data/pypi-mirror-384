import lightning as L
from pathlib import Path
import torch

class Dataset(torch.utils.data.Dataset):
    """
    Base class for implement Pytorch compatible Datasets.
    
    The class inherits from 'torch.utils.data.Dataset' and requires subclasses to implement the following methods:
        - __len__: Returns the number of samples in the dataset.
        - __getitem__: Retrieves a sample and its corresponding label by index.
        - download: Class method to handle dataset downloading.
    
    """
    @classmethod
    def download(cls, root: Path, **kwargs) -> Path:
        """
        Downloads the dataset to the specified root directory.
        
        Args:
            root (Path): The root directory where the dataset should be downloaded.
            **kwargs: Additional keyword arguments for dataset-specific download options.
        Returns:
            Path: The path to the downloaded dataset.
        """
        raise NotImplementedError("This method should be overridden by subclasses")
    
class DataModule(L.LightningDataModule):
    """
    Base class for implementing Lightning compatible Data Modules.
    
    The class inherits from 'lightning.LightningDataModule' and requires subclasses to implement the following methods:
        - prepare_data: Handles dataset downloading and preparation.
        - setup: Sets up the dataset for training, validation, and testing.
        - train_dataloader: Returns the training data loader.
        - val_dataloader: Returns the validation data loader.
        - test_dataloader: Returns the test data loader.
        - download: Class method to handle dataset downloading.
    
    """
    @classmethod
    def download(cls, root: Path, **kwargs) -> Path:
        """
        Downloads the dataset to the specified root directory.
        
        Args:
            root (Path): The root directory where the dataset should be downloaded.
            **kwargs: Additional keyword arguments for dataset-specific download options.
        Returns:
            Path: The path to the downloaded dataset.
        """
        raise NotImplementedError("This method should be overridden by subclasses")