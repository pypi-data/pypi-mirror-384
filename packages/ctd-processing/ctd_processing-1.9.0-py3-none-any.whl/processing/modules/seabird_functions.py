import logging
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from scipy.signal import butter, correlate, filtfilt, find_peaks
from seabirdfilehandler import CnvFile
from seabirdfilehandler.parameter import Parameter

from processing.module import ArrayModule, MissingParameterError

logger = logging.getLogger(__name__)


class AlignCTD(ArrayModule):
    """
    Align the given parameter columns.

    Given a measurement parameter in parameters, the column will be shifted
    by either, a float amount that is given as value, or, by a calculated
    amount, using cross-correlation between the high-frequency components of
    the temperature and the target parameters.
    The returned numpy array will thus feature the complete CnvFile data,
    with the columns shifted to their correct positions.
    """

    def __init__(self) -> None:
        super().__init__()

    def __call__(
        self,
        input: Path | str | CnvFile | pd.DataFrame | np.ndarray,
        parameters: dict = {},
        output: str = "cnvobject",
        output_name: str | None = None,
        minimum_correlation: float = 0.1,
        default_value: float = 72,
        flag_value="-9.990e-29",
        **kwargs,
    ) -> None | CnvFile | pd.DataFrame | np.ndarray:
        self.minimum_correlation = minimum_correlation
        self.default_value = default_value
        self.flag_value = flag_value
        return super().__call__(input, parameters, output, output_name)

    def transformation(self) -> bool:
        """
        Performs the base logic of distinguishing whether to use given values
        or compute a delay.

        Returns
        -------
        A numpy array, representing the cnv data after the alignment.

        """
        assert len(self.parameters) > 0
        return_value = False
        new_parameter_metadata = {}
        for key, value in self.handle_parameter_input(self.parameters).items():
            # key is something like oxygen1 or oxygen2
            # value is either None or a numerical value in string or other form
            target_parameters = [
                k
                for k, v in self.cnv.parameters.metadata.items()
                if (v["name"].lower().startswith(key[:-1]))
                and (str(int(key[-1]) - 1) in v["shortname"])
            ]
            # if there are no measurement parameters of the given key inside
            # the cnv file, remove the key from the input, to avoid printing
            # that key to the output files header
            if len(target_parameters) == 0:
                continue
            # if no shift value given, estimate it
            if not value:
                value, correlation_value = self.estimate_sensor_delay(
                    delayed_parameter=self.cnv.parameters[
                        target_parameters[0]
                    ],
                    margin=len(self.cnv.parameters.full_data_array) // 4,
                )
                correlation_string = f", with PCC: {correlation_value}"
                if not self.check_correlation_result(value, correlation_value):
                    correlation_string = f", default value. Calculated delay: {str(float('{:.2f}'.format(value / self.sample_interval)))} PCC: {correlation_value}"
                    # set to a default value
                    value = self.default_value
            else:
                # the input is in seconds, so we calculate a shift in rows
                value = float(value) * self.sample_interval
                correlation_string = ""
            # apply shift for all columns of the given parameter
            for parameter in target_parameters:
                # find the columns position in the grand array
                index = [
                    index
                    for index, param in enumerate(self.cnv.parameters)
                    if param == parameter
                ][0]

                # get the number of decimals to format the output in the same
                # way
                number_of_decimals = len(
                    str(self.array[:, index][0]).split(".")[1]
                )
                # do the shifting/alignment
                self.array[:, index] = np.append(
                    self.array[int(value) :, index].round(
                        decimals=number_of_decimals
                    ),
                    np.full((int(value),), self.flag_value),
                )
                # format the output back to seconds
                new_parameter_metadata[parameter] = (
                    str(float("{:.2f}".format(value / self.sample_interval)))
                    + "s"
                    + correlation_string
                )
                # at least one column has been altered so we can give positive
                # feedback
                return_value = True
        self.parameters = new_parameter_metadata
        return return_value

    def estimate_sensor_delay(
        self,
        delayed_parameter: Parameter,
        margin: int = 240,
        shift_seconds: int = 10,
    ) -> Tuple[float, float]:
        """
        Estimate delay between a delayed parameter and temperature signals via
        cross-correlation of high-frequency components.

        Parameters
        ----------
        delayed_parameter: Parameter :
            The parameter whose delay shall be computed.

        margin: int :
            A number of data points that are cutoff from both ends.
             (Default value = 240)

        shift_seconds: int :
             Maximum time window to search for lag (default: 10 seconds).

        Returns
        -------
        A float value, representing the parameter delay in seconds.

        """
        temperature = self.find_corresponding_temperature(
            delayed_parameter
        ).data
        delayed_values = delayed_parameter.data
        assert len(temperature) == len(delayed_values)
        # remove edge effects (copying Gerds MATLAB software)
        while len(temperature) <= 2 * margin:
            margin = margin // 2

        t_shortened = np.array(temperature[margin:-margin])
        v_shortened = np.array(delayed_values[margin:-margin])

        if np.all(np.isnan(v_shortened)):
            return np.nan, np.nan

        # design Butterworth filter
        b, a = butter(3, 0.005)

        # smooth signals
        t_smoothed = filtfilt(b, a, t_shortened)
        v_smoothed = filtfilt(b, a, v_shortened)

        # high-frequency components
        t_high_freq = t_shortened - t_smoothed
        v_high_freq = v_shortened - v_smoothed

        # cross-correlation
        max_lag = int(shift_seconds * self.sample_interval)
        sign = self.get_correlation(delayed_parameter)
        corr = correlate(v_high_freq, t_high_freq * sign, mode="full")
        lags = np.arange(-len(t_high_freq) + 1, len(t_high_freq))
        lag_indices = np.where(np.abs(lags) <= max_lag)[0]

        # normalize correlation values
        norm_factor = np.sqrt(np.sum(v_high_freq**2) * np.sum(t_high_freq**2))
        corr_normalized = corr / norm_factor

        corr_segment = corr_normalized[lag_indices]
        lags_segment = lags[lag_indices]

        # restrict to only positive delays
        positive_indices = np.where(lags_segment > 0)[0]
        corr_segment_positive = corr_segment[positive_indices]

        peaks, props = find_peaks(
            corr_segment_positive, height=0.01, distance=5
        )

        # handle case, when no correlation can be found
        if len(peaks) == 0:
            return np.nan, np.nan

        # find lag with highest correlation
        best_index = int(np.argmax(props["peak_heights"]))

        return float(peaks[best_index]), float(
            "{:.2f}".format(props["peak_heights"][best_index])
        )

    def check_correlation_result(
        self, value: float, correlation_value: float
    ) -> bool:
        """
        Performs several checks on the delay outputed by
        self.estimate_sensor_delay and returns True, if the result is
        considered feasible.
        """
        if (value is np.nan) or (correlation_value is np.nan):
            return False
        value = value / self.sample_interval
        if correlation_value < self.minimum_correlation:
            return False
        if value < 1 or value > 6:
            return False
        return True

    def find_corresponding_temperature(
        self, parameter: Parameter
    ) -> Parameter:
        """
        Find the temperature values of the sensor that shared the same water
        mass as the input parameter.

        Parameters
        ----------
        parameter: Parameter :
            The parameter of interest.


        Returns
        -------
        The temperature parameter object.

        """
        if "0" in parameter.name:
            return self.cnv.parameters["t090C"]
        elif "1" in parameter.name:
            return self.cnv.parameters["t190C"]
        else:
            raise MissingParameterError("AlignCTD", "Temperature")

    def get_correlation(self, parameter: Parameter) -> float:
        """
        Gives a number indicating the cross correlation type regarding the
        input parameter and the temperature.

        Basically distinguishes between positive correlation, 1, and anti-
        correlation, -1. This value is then used to alter the temperature
        values accordingly.

        Parameters
        ----------
        parameter: Parameter :
            The parameter to cross correlate with temperature.

        Returns
        -------
        A float value representing positive or negative correlation.

        """
        if parameter.metadata["name"].lower().startswith("oxygen"):
            return -1
        else:
            return 1

    def handle_parameter_input(self, input_dict: dict) -> dict:
        new_dict = {}
        all_parameter_names = [
            value["name"].lower()
            for value in self.cnv.parameters.metadata.values()
        ]
        for parameter_input, value in input_dict.items():
            # remove all non-alphanumeric characters
            parameter = (
                "".join(filter(str.isalnum, parameter_input)).lower().strip()
            )
            if parameter_input[-1] in ["1", "2"]:
                parameter = parameter[:-1]
                number = parameter_input[-1]
            else:
                number = None
            parameter_names = [
                name
                for name in all_parameter_names
                if name.startswith(parameter)
            ]
            # check, whether we are working with multiple sensors
            if "2" in [name[-1] for name in parameter_names]:
                # differentiate the different cases for 2 sensors
                # only parameter without sensor number information given
                if parameter.lower() in parameter_names and not number:
                    new_dict[f"{parameter}1"] = value
                    new_dict[f"{parameter}2"] = value
                # explicitly given sensor 1
                if parameter.lower() in parameter_names and number == "1":
                    new_dict[f"{parameter}1"] = value
                # explicitly given sensor 2
                if parameter.lower() in parameter_names and number == "2":
                    new_dict[f"{parameter}2"] = value
            else:
                # single sensor is easy, just use the value for sensor 1
                if not parameter[-1] == "2":
                    new_dict[f"{parameter}1"] = value
        return new_dict
