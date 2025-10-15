import numpy as np
import torch
from typing import Tuple
import lightning as L
from torch.utils.data import random_split, DataLoader


class CubicDataset(torch.utils.data.Dataset):
    """
    Cubic dataset

    The Cubic Dataset is a test case for uncertainty quantification. The data is real values of x in the interval [-4,4]
    for the training set and [-7,7] for the test set. The labels are $y=x^3 + N(0,3)$. The aleatoric uncertainty is
    measured between the training set, and epistemic uncertainty exists outside the training interval.

    Attributes:
        NOISE_STD (float): The standard deviation of the Gaussian noise. 3.0

    Args:
        train (bool): Returns the training dataset when true. Default: False
        noise (bool): Adds Gaussian noise to output labels when True. Default: True
        num_samples (int): Number of data samples to create in the dataset. Default: 1000
        seed (int): Random sampling seed. Default: None

    Returns
        object (CubicDataset): A dataset object
    """
    NOISE_STD = 3.0

    def __init__(self,
                 train: bool = False,
                 noise: bool = True,
                 num_samples: int = 1000,
                 seed: int = None):
        self.num_samples = num_samples

        # Set the seed if provided
        if seed is not None:
            torch.manual_seed(seed)
            np.random.seed(seed)

        # Decide the range based on whether it's a train or test set
        self.range_min, self.range_max = (-4, 4) if train else (-7, 7)

        # Generate x values within the specified range
        self.x = np.linspace(self.range_min, self.range_max, self.num_samples).astype(np.float32)
        # self.x = np.random.uniform(self.range_min, self.range_max, num_samples).astype(np.float32)

        # Convert x to a PyTorch tensor and reshape for consistency
        self.x = torch.from_numpy(self.x).view(-1, 1)

        # Generate noise if necessary
        if noise:
            sigma = np.random.normal(0, self.NOISE_STD, num_samples).astype(np.float32)
        else:
            sigma = np.zeros(num_samples, dtype=np.float32)

        # Convert noise to a PyTorch tensor
        sigma = torch.from_numpy(sigma)

        # Calculate y values and reshape
        self.y = (self.x ** 3) + sigma.view(-1, 1)

    def __len__(self) -> int:
        """
        Returns the number of samples in the dataset

        Returns:
            (int): The number of samples in the dataset
        """
        return self.num_samples

    def __getitem__(self, index: int) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Implements the get item method of the Pytorch Dataset.

        Args:
            index: Index of data sample to return

        Returns:
            (torch.Tensor, torch.Tensor): x value and x^3 with noise label both of shape (B, 1)
        """
        # Return items as tuples of x and y, ensuring they are individual samples of shape (1,)
        return self.x[index], self.y[index]

class CubicDataModule(L.LightningDataModule):
    """
    Cubic Dataset Lightning Data Module

    This class is a lightning data module wrapper for the Pytorch Cubic Dataset for easier training with lightning
    networks.

    Args:
        batch_size (int): Data batch size. Default: 64
        num_workers (int): Number of data loading workers. Defaults: 16
        shuffle (bool): Whether to shuffle the dataset. Defaults: True
        seed (int): Random seed for generating Cubic dataset. Defaults: 0
    """

    def __init__(self,
                 batch_size: int = 100,
                 num_workers: int = 16,
                 shuffle: bool = True,
                 seed: int = 0):
        super().__init__()
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.shuffle = shuffle
        self.seed = seed

    def prepare_data(self) -> None:
        pass

    def setup(self, stage: str) -> None:
        # Load the training data
        train_data = CubicDataset(train=True, noise=True, num_samples=1000, seed=self.seed)

        # Split the dataset into training and validation with 80/20 split
        self.cubic_train, self.cubic_val = random_split(train_data,
                                                        [int(0.8 * len(train_data)), int(0.2 * len(train_data))])

        # Load the test dataset
        self.cubic_test = CubicDataset(train=False, noise=False, num_samples=1000, seed=self.seed)

    def train_dataloader(self):
        train_loader = DataLoader(self.cubic_train,
                                  batch_size=self.batch_size,
                                  num_workers=self.num_workers,
                                  shuffle=self.shuffle)
        return train_loader

    def val_dataloader(self):
        val_loader = DataLoader(self.cubic_val,
                                batch_size=self.batch_size,
                                num_workers=self.num_workers,
                                shuffle=False)
        return val_loader

    def test_dataloader(self):
        test_loader = DataLoader(self.cubic_test,
                                 batch_size=self.batch_size,
                                 num_workers=self.num_workers,
                                 shuffle=False)
        return test_loader

    def predict_dataloader(self):
        pred_loader = DataLoader(self.cubic_test,
                                 batch_size=self.batch_size,
                                 num_workers=self.num_workers,
                                 shuffle=False)
        return pred_loader