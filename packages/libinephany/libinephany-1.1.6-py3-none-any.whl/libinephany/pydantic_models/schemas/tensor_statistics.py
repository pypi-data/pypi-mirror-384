# ======================================================================================================================
#
# IMPORTS
#
# ======================================================================================================================

import torch
from pydantic import BaseModel

# ======================================================================================================================
#
# CONSTANTS
#
# ======================================================================================================================

FIELD_SUFFIX = "_"

# ======================================================================================================================
#
# CLASSES
#
# ======================================================================================================================


class TensorStatistics(BaseModel):

    norm_: float = 0.0
    mean_: float = 0.0
    median_: float = 0.0
    variance_: float = 0.0
    tenth_percentile_: float = 0.0
    ninetieth_percentile_: float = 0.0
    inter_quartile_range_: float = 0.0

    @property
    def norm(self) -> float:
        """
        :return: Tensor norm.
        """

        return self.norm_

    @norm.setter
    def norm(self, tensor: torch.Tensor) -> None:
        """
        :param tensor: Tensor to compute the norm from.
        """

        self.norm_ = torch.norm(tensor, p=2).item()

    @property
    def mean(self) -> float:
        """
        :return: Tensor mean.
        """

        return self.mean_

    @mean.setter
    def mean(self, tensor: torch.Tensor) -> None:
        """
        :param tensor: Tensor to compute the mean from.
        """

        self.mean_ = tensor.mean().item()

    @property
    def median(self) -> float:
        """
        :return: Tensor median.
        """

        return self.median_

    @median.setter
    def median(self, tensor: torch.Tensor) -> None:
        """
        :param tensor: Tensor to compute the median from.
        """

        self.median_ = tensor.median().item()

    @property
    def variance(self) -> float:
        """
        :return: Tensor variance.
        """

        return self.variance_

    @variance.setter
    def variance(self, tensor: torch.Tensor) -> None:
        """
        :param tensor: Tensor to compute the variance from.
        """

        self.variance_ = tensor.var(unbiased=False).item()

    @property
    def tenth_percentile(self) -> float:
        """
        :return: Tensor tenth percentile.
        """

        return self.tenth_percentile_

    @tenth_percentile.setter
    def tenth_percentile(self, tensor: torch.Tensor) -> None:
        """
        :param tensor: Tensor to compute the tenth percentile from.
        """

        self.tenth_percentile_ = torch.quantile(tensor, 0.1).item()

    @property
    def ninetieth_percentile(self) -> float:
        """
        :return: Tensor ninetieth percentile.
        """

        return self.ninetieth_percentile_

    @ninetieth_percentile.setter
    def ninetieth_percentile(self, tensor: torch.Tensor) -> None:
        """
        :param tensor: Tensor to compute the ninetieth from.
        """

        self.ninetieth_percentile_ = torch.quantile(tensor, 0.9).item()

    @property
    def inter_quartile_range(self) -> float:
        """
        :return: Tensor inter-quartile range.
        """

        return self.inter_quartile_range_

    @inter_quartile_range.setter
    def inter_quartile_range(self, tensor: torch.Tensor) -> None:
        """
        :param tensor: Tensor to compute the inter-quartile range from.
        """

        self.inter_quartile_range_ = (torch.quantile(tensor, 0.75) - torch.quantile(tensor, 0.25)).item()

    @staticmethod
    def downsample_tensor(tensor: torch.Tensor, sample_percentage: float) -> torch.Tensor:
        """
        :param tensor: Tensor to downsample.
        :param sample_percentage: Percentage of the given tensor to randomly sample and compute statistics from.
        :return: Downsampled tensor.
        """

        if sample_percentage >= 1.0:
            return tensor

        input_size = tensor.numel()
        sample_size = max(int(input_size * sample_percentage), 1)

        random_indices = torch.randint(0, input_size, (sample_size,), device=tensor.device)
        tensor = tensor.view(-1)

        return tensor[random_indices]

    @classmethod
    def filter_include_statistics(cls, include_statistics: list[str]) -> list[str]:
        """
        :param include_statistics: Names of the fields in the model to include in returned observations.
        :return: List of fields from the given include_statistics list that are present in this pydantic model.
        :raises ValueError: If no statistics to include are given.
        """

        filtered_include_statistics: list[str] = []

        for include_stat in include_statistics:
            with_suffix = include_stat + FIELD_SUFFIX if not include_stat.endswith(FIELD_SUFFIX) else include_stat

            if with_suffix in cls.model_fields.keys():
                filtered_include_statistics.append(with_suffix)

        if not filtered_include_statistics:
            raise ValueError(f"No statistics to include given to {cls.__name__}!")

        return filtered_include_statistics

    @classmethod
    def build(
        cls,
        tensor: torch.Tensor,
        include_statistics: list[str],
        sample_percentage: float = 0.01,
    ) -> "TensorStatistics":
        """
        :param tensor: Tensor to compute and store statistics of.
        :param include_statistics: If the observation uses the TensorStatistic model to return observations, names of the
        fields in the model to include in returned observations.
        :param sample_percentage: Percentage of the given tensor to randomly sample and compute statistics from.
        :return: Constructed tensor statistics.
        """

        stats = cls()
        downsampled_tensor = cls.downsample_tensor(tensor=tensor, sample_percentage=sample_percentage)

        for field, field_value in stats.model_dump().items():
            name = field[:-1] if field.endswith(FIELD_SUFFIX) else field

            if name in include_statistics or field in include_statistics:
                setattr(stats, name, downsampled_tensor)

        return stats

    @classmethod
    def from_tensor(cls, tensor: torch.Tensor) -> "TensorStatistics":
        """
        :param tensor: Tensor to build the model from.
        :return: Reconstructed model.
        """

        return cls(
            norm_=tensor[0],
            mean_=tensor[1],
            median_=tensor[2],
            variance_=tensor[3],
            tenth_percentile_=tensor[4],
            ninetieth_percentile_=tensor[5],
            inter_quartile_range_=tensor[6],
        )

    def to_list(self, include_statistics: list[str]) -> list[float]:
        """
        :param include_statistics: List of field names to include in the returned list.
        :return: List of field values.
        """

        filtered_includes = self.filter_include_statistics(include_statistics=include_statistics)

        as_list = []

        for field, field_value in self.model_dump().items():
            without_suffix = field[:-1]

            if field in filtered_includes or without_suffix in filtered_includes:
                as_list.append(field_value)

        return as_list

    def to_tensor(self) -> torch.Tensor:
        """
        :return: Tensor with contents of the Pydantic model in a specific order.
        """

        return torch.tensor(
            [
                self.norm,
                self.mean,
                self.median,
                self.variance,
                self.tenth_percentile,
                self.ninetieth_percentile,
                self.inter_quartile_range,
            ]
        )

    def as_observation_dict(self) -> dict[str, float]:
        """
        :return: Dictionary of observation values.
        """

        return {
            field[:-1] if field.endswith(FIELD_SUFFIX) else field: field_value
            for field, field_value in self.model_dump().items()
        }
