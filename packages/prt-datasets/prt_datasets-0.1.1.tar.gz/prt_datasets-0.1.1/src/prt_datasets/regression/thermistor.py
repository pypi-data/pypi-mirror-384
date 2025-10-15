import numpy as np
import torch
from torch.utils.data import Dataset
from typing import Optional, Callable, Tuple, Any


def _gaussian_noise(samples):
    mean = 0
    stddev = 100
    noise = np.random.normal(mean, stddev, len(samples))
    return noise


class ThermistorModel:
    """Create a thermistor model based on the Steinhart-Hart equations to output temperature in celcius given resistance
    """

    def __init__(self, ka=1.283 * 1e-3, kb=2.362 * 1e-4, kc=9.285 * 1e-8, seed=None):
        self._ka = ka
        self._kb = kb
        self._kc = kc
        self.min_resistance = 100  # Ohms
        self.max_resistance = 15000  # Ohms
        self.noise_mean = 0
        self.noise_stddev = 100

        if seed is not None:
            np.random.seed(seed)

    def evaluate(self, resistance):
        """
        Evaluates the dynamic model given resistances
        :param resistance:
        :return:
        """
        T_kelvin = 1.0 / (self._ka + self._kb * np.log(resistance) + self._kc * np.log(resistance) ** 3)
        T_celcius = T_kelvin - 273.15
        return T_celcius

    def fit(self):
        raise NotImplementedError

    def sample(self, num_samples, input_noise=None, output_noise=None):
        """
        Returns noisy samples and true temperature values
        :param num_samples:
        :param noise_model: A function that calculates the thermistor noise
        :return:
        """
        # samples = np.random.rand(num_samples) * (self.max_resistance - self.min_resistance) + self.min_resistance
        samples = np.random.uniform(low=self.min_resistance, high=self.max_resistance, size=num_samples)
        temperatures = self.evaluate(samples)

        if input_noise is None:
            # noisy_samples = samples + np.random.normal(self.noise_mean, self.noise_stddev, len(samples))
            noisy_samples = samples
            print('No input noise')
        else:
            noisy_samples = samples + input_noise(samples)

        if output_noise is None:
            noisy_temps = temperatures
        else:
            noisy_temps = temperatures + output_noise(temperatures)

        return noisy_samples, noisy_temps, temperatures

    def normalize(self, resistances):
        """
        Takes resistances and normalizes them to 0 to 1
        :param resistances:
        :return:
        """
        return (resistances - self.min_resistance) / (self.max_resistance - self.min_resistance)

    def unnormalize(self, norm_resistances):
        return norm_resistances * (self.max_resistance - self.min_resistance) + self.min_resistance


class ThermistorDataset(Dataset):
    """
    The Thermistor dataset generates data based on the Steinhart-Hart equations and a provided noise model.

    There are 10,000 training samples and 1,000 test samples

    Args:
        train (bool): Set to true to get a training dataset


    """

    def __init__(
            self,
            train: bool = True,
            transform: Optional[Callable] = None,
            target_transform: Optional[Callable] = None,
            seed: int = None
    ) -> None:

        self.train = train
        self.transforms = transform
        self.target_transforms = target_transform

        # Generator the thermistor data
        self.thermistor = ThermistorModel(seed=seed)

        if self.train:
            num_samples = 10_000
        else:
            num_samples = 1_000

        self.resistances, self.temperatures, _ = self.thermistor.sample(num_samples)
        self.resistances = torch.from_numpy(self.resistances)
        self.temperatures = torch.from_numpy(self.temperatures)

    def __len__(self) -> int:
        return len(self.resistances)

    def __getitem__(self, index: int) -> Tuple[Any, Any]:
        data = self.resistances[index]
        label = self.temperatures[index]

        if self.transforms is not None:
            data = self.transforms(data)

        if self.target_transforms is not None:
            label = self.target_transforms(label)

        return torch.Tensor([data]), torch.Tensor([label])
