import numpy as np
import torch
import lightning as L
from torch.utils.data import random_split, DataLoader


class CircleDataset(torch.utils.data.Dataset):
    """
    Circle Dataset

    References:
        [1] https://github.com/avitase/mder/blob/main/notebooks/multivariate_experiment/data.py
    """
    NOISE_STD = 0.1

    def __init__(self,
                 num_samples: int = 1000,
                 seed: int = None
                 ):
        self.num_samples = num_samples
        self.seed = seed

        # Set the seed if provided
        if seed is not None:
            torch.manual_seed(seed)

        t_flat = torch.rand(num_samples, dtype=torch.float32)
        self.x = self._inverse_cdf(t_flat) * 2.0 * torch.pi

        sig = 1.0 + torch.from_numpy(np.random.normal(loc=0, scale=self.NOISE_STD, size=num_samples)).to(torch.float32)
        y1 = sig * torch.cos(self.x)
        y2 = sig * torch.sin(self.x)
        self.y = torch.stack((y1, y2), dim=1)

    def __len__(self):
        return self.x.shape[0]

    def __getitem__(self, idx):
        return self.x[idx], self.y[idx]

    def _inverse_cdf(self, x):
        """Inverse Cumulative Distribution Function

        Inverse cumulative distribution of a v-shape function,
        'f(x) = -4x+2 if x < .5 else 4x-2`.

        Args:
            x: Number sequence between 0 and 1.
        Returns:
            Inverse cumulative distribution evaluated at `x`.
        """
        y = torch.ones_like(x)*0.5

        sel = x < 0.5
        y[sel] *= 1.0 - torch.sqrt(1.0 - 2.0 * x[sel])
        y[~sel] *= 1.0 + torch.sqrt(2.0 * x[~sel] - 1.0)
        return y


class CircleDataModule(L.LightningDataModule):
    """
    Circle Dataset Lightning Data Module

    """

    def __init__(self,
                 batch_size: int = 64,
                 num_workers: int = 16,
                 seed: int = 0):
        super().__init__()
        self.batch_size = batch_size
        self.num_workers = num_workers
        self.seed = seed

    def prepare_data(self) -> None:
        pass

    def setup(self, stage=None) -> None:
        # Load the training data
        data = CircleDataset()

        # Split the dataset
        self.circle_train, self.circle_val = random_split(data, [int(0.8 * len(data)), int(0.2 * len(data))])

    def train_dataloader(self):
        train_loader = DataLoader(self.circle_train,
                                  batch_size=self.batch_size,
                                  num_workers=self.num_workers,
                                  shuffle=True)
        return train_loader

    def val_dataloader(self):
        val_loader = DataLoader(self.circle_val,
                                batch_size=self.batch_size,
                                num_workers=self.num_workers,
                                shuffle=False)
        return val_loader

    def test_dataloader(self):
        test_loader = DataLoader(self.circle_val,
                                 batch_size=self.batch_size,
                                 num_workers=self.num_workers,
                                 shuffle=False)
        return test_loader