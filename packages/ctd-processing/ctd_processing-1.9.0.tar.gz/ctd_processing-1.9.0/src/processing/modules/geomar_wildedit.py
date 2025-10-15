import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from scipy.ndimage import uniform_filter1d
from seabirdfilehandler import CnvFile

from processing.module import ArrayModule
from processing.utils import is_directly_measured_value

logger = logging.getLogger(__name__)


class WildeditGEOMAR(ArrayModule):
    """
    Flags outliers in a dataset via standard deviation.

    Iterates over blocks of data, calculates mean and standard deviation and
    flags data outside a pre-set standard deviation window. In contrast to the
    standard SeaBird processing module, wild_edit, this module uses a sliding
    window around each data point instead of fixed blocks of data.
    Additionally, while the SeaBird variant terminates after two fixed cycles
    of flagging, here we iterate as long as there are bad values found.
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "wildedit_geomar"

    def __call__(
        self,
        input: Path | str | CnvFile | pd.DataFrame | np.ndarray,
        parameters: dict = {},
        output: str = "cnvobject",
        output_name: str | None = None,
        flag_value=-9.99e-29,
        **kwargs,
    ) -> None | CnvFile | pd.DataFrame | np.ndarray:
        self.flag_value = flag_value
        return super().__call__(input, parameters, output, output_name)

    def transformation(self) -> bool:
        """
        Selects the appropiate data columns and applies the flagging to each
        one individually.

        Returns
        -------
        A numpy array, representing full cnv data with outliers removed.

        """
        for key, value in self.parameters.items():
            try:
                self.parameters[key] = float(value)
            except ValueError:
                self.parameters[key] = value
            if key == "window_size":
                self.parameters[key] = int(value)
        return_value = False
        for index, parameter in enumerate(self.cnv.parameters.values()):
            if is_directly_measured_value(parameter):
                # TODO: how to handle the new flag?
                new_data, _ = wildedit_geomar(
                    data=parameter.data,
                    flag=self.cnv.parameters["flag"].data,
                    **self.parameters,
                )
                self.array[:, index] = new_data.round(decimals=4)
                return_value = True
        return return_value


def wildedit_geomar(
    data: np.ndarray,
    flag: np.ndarray = np.ndarray(shape=(0, 0)),
    std1: float = 3.0,
    std2: float = 10.0,
    window_size: int = 50,
    minstd: float = 0,
    **kwargs,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Wild editing filter, addapted from Gerd Krahmann.

    Uses a sliding window and repeated flagging loops until no bad values are
    found.

    Parameters
    ----------
    data: np.ndarray :
        The input data array.

    flag: np.ndarray :
        The data flag array.

    std1: float :
        The standard deviation cutoff for the first flagging loop.
         (Default value = 3.0)
    std2: float :
        The standard deviation cutoff for the all the following loops.
         (Default value = 10.0)
    window_size: int :
        The size of the sliding window.
         (Default value = 50)
    minstd: float :
        The minimum standard deviation threshold to flag data.
         (Default value = 0)

    Returns
    -------
    A tuple of cleaned data and new data flags.

    """

    if window_size < 10:
        raise ValueError("window_size must be >= 10")

    data = np.asarray(data, dtype=float)

    if flag.size > 0:
        flag = np.asarray(flag)

        good_indices = np.where(flag == 1)[0]
        if good_indices.size > 1:
            interp_func = interp1d(
                good_indices,
                data[good_indices],
                kind="nearest",
                fill_value="extrapolate",
                bounds_error=False,
            )
            data = interp_func(np.arange(len(data)))

    def running_mean_std(
        data: np.ndarray, window_size: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Fast running mean and standard deviation using uniform filter."""
        mean = uniform_filter1d(data, size=window_size, mode="nearest")
        mean_sq = uniform_filter1d(data**2, size=window_size, mode="nearest")
        var = mean_sq - mean**2
        var = np.maximum(0, var)
        std = np.sqrt(var)
        return mean, std

    def flag_bad_points(
        x: np.ndarray,
        mean: np.ndarray,
        std: np.ndarray,
        threshold: float,
        min_std: float,
    ) -> np.ndarray:
        """Apply mean and standard deviation to find outliers."""
        std = np.abs(std)
        if len(std) > 100:
            sorted_std = np.sort(std)
            low_limit = sorted_std[len(std) // 100]
            std = np.maximum(std, low_limit)
        std = np.maximum(std, min_std)
        return np.abs(x - mean) > threshold * std

    total_bad_mask = np.zeros_like(data, dtype=bool)
    local_data = data.copy()

    threshold = std1
    iteration = 0

    while True:
        iteration += 1

        mean, std = running_mean_std(local_data, window_size)
        bad_mask = flag_bad_points(data, mean, std, threshold, minstd)
        new_bad_mask = bad_mask & ~total_bad_mask

        if not np.any(new_bad_mask):
            break

        total_bad_mask |= new_bad_mask
        good_indices = np.where(~total_bad_mask)[0]

        if good_indices.size < 2:
            break

        interp_func = interp1d(
            good_indices,
            local_data[good_indices],
            kind="cubic",
            fill_value="extrapolate",
            bounds_error=False,
        )
        local_data[new_bad_mask] = interp_func(np.where(new_bad_mask)[0])
        # switch to second threshold after first iteration
        threshold = std2

    data_geomar = data.copy()
    data_geomar[total_bad_mask] = np.nan

    flag_geomar = np.zeros_like(data, dtype=int)
    flag_geomar[total_bad_mask] = 4

    return data_geomar, flag_geomar
