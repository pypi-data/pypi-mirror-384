import torchvision
from typing import Optional, Callable, List
import lightning as L
from torch.utils.data import random_split, DataLoader

class MNISTDataset(torchvision.datasets.MNIST):
    """
    Wrapper class for the torchvision MNIST dataset.

    Attributes:
        MNIST_MEAN (float): The mean value of the MNIST
        MNIST_STD_DEV (float): The standard deviation of the MNIST

    Args:
        root (string): Root directory of the dataset
        train (bool, optional): Whether to load the training or test data. Defaults to True
        transform (callable, optional): A function/transform
        target_transform (callable, optional): A function
        exclude_digits (list, optional):
        download (bool, optional): If true, downloads the dataset
    """
    MNIST_MEAN = 0.1307
    MNIST_STD_DEV = 0.3081

    def __init__(self,
                 root: str = '.',
                 train: bool = True,
                 transform: Optional[Callable] = None,
                 target_transform: Optional[Callable] = None,
                 exclude_digits: List[int] = [],
                 download: bool = False,
                 ):
        # Convert to a tensor and normalize
        transform = torchvision.transforms.Compose([
            torchvision.transforms.ToTensor(),
            torchvision.transforms.Normalize(
                (self.MNIST_MEAN,), (self.MNIST_STD_DEV,)),
        ])
        super(MNIST, self).__init__(root, train, transform, target_transform, download)

        # Update the data and targets to remove classes
        for c in exclude_digits:
            indices = self.targets != c
            self.targets = self.targets[indices]
            self.data = self.data[indices]


class MNISTDataModule(L.LightningDataModule):
    """
    MNIST Lightning Data Module


    """

    def __init__(self,
                 root: str = '.',
                 exclude_digits: List[int] = [],
                 batch_size: int = 64):
        super().__init__()
        self.root = root
        self.exclude_digits = exclude_digits
        self.batch_size = batch_size

    def prepare_data(self) -> None:
        # Make sure the MNIST datasets are downloaded to the root directory
        MNISTDataset(root=self.root, train=True, download=True)
        MNISTDataset(root=self.root, train=False, download=True)

    def setup(self, stage: str) -> None:
        # Load the training data
        train_data = MNISTDataset(root=self.root, train=True, exclude_digits=self.exclude_digits)

        # Split the dataset into training and validation with 80/20 split
        self.mnist_train, self.mnist_val = random_split(train_data,
                                                        [int(0.8 * len(train_data)), int(0.2 * len(train_data))])

        # Load the test dataset
        self.mnist_test = MNISTDataset(root=self.root, train=False, exclude_digits=self.exclude_digits)

    def train_dataloader(self):
        train_loader = DataLoader(self.mnist_train, batch_size=self.batch_size)
        return train_loader

    def val_dataloader(self):
        val_loader = DataLoader(self.mnist_val, batch_size=self.batch_size)
        return val_loader

    def test_dataloader(self):
        test_loader = DataLoader(self.mnist_test, batch_size=self.batch_size)
        return test_loader