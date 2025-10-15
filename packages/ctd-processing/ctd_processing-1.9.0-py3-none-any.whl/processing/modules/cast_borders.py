import argparse as arg
from pathlib import Path

import numpy as np
from seabirdfilehandler import CnvFile
from tomlkit import parse

from processing.module import ArrayModule


class CastBorders(ArrayModule):
    """
    Get the Borders of a given cast, either only the borders for the downcast or the borders for the entire cast.

    the Data outside the borders will either be Marked or cut out entirely

    !!!Only the Downcast works at the moment!!!
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "cast_borders"

    def __call__(
        self,
        input: Path | str | CnvFile,
        parameters: dict = {},
        output: str = "cnvobject",
        output_name: str | None = None,
        **kwargs,
    ) -> None | CnvFile:
        self.file = input
        return super().__call__(input, parameters, output, output_name)

    def transformation(self):
        """
        handles output for cast_borders overwritten from the ArrayModule - module

        """
        if self.get_cast_borders() == -1:
            return False

        elif self.parameters["verbosity"] >= 1:
            if not self.parameters["downcast_only"]:
                print(
                    "Downcast Start: ",
                    self.ind_dc_start,
                    "Downcast End: ",
                    self.ind_dc_end,
                    "Upcast Start: ",
                    self.ind_uc_start,
                    "Upcast End: ",
                    self.ind_uc_end,
                )
            else:
                print(
                    "Downcast Start: ",
                    self.ind_dc_start,
                    "Downcast End: ",
                    self.ind_dc_end,
                )

        if self.parameters["cut"]:
            self.cnv.parameters.full_data_array = self.cut_cast_borders()
        else:
            self.mark_cast_borders(self.CB_list)

        self.parameters["Cast_Borders"] = [self.ind_dc_start, self.ind_dc_end]

        return True

    def ini_cast_borders(self):
        """
        Initializes necessary variables for the clas to work


        Returns:
        --------

        self.prDM_list: a list with the pressure values from a cast
        self.bad_flag: the badflag set for the cnv
        self.interval: the interval at wich the data is sampled
        self.smooth_velo: the result of self.get_velo

        """

        parameter_list = self.cnv.parameters.get_parameter_list()

        index = -1
        for i in range(len(parameter_list)):
            if "Depth" in str(parameter_list[i]) or "Pressure" in str(
                parameter_list[i]
            ):
                index = i
                break

        self.prDM_list = self.array[:, index]
        misc_data_dict = self.cnv.parameters.data_table_misc
        self.bad_flag = float(misc_data_dict["bad_flag"])
        self.interval = float(misc_data_dict["interval"].strip().split(":")[1])
        self.smooth_velo = self.get_velo(self.prDM_list)
        return

    def get_cast_borders(self):
        """
        gets the borders of a given cast based on if the argrument "downcast_only" is set


        Returns:
        --------

        returns -1 if there was a problem with getting the cast borders and else returns the borders

        """

        self.ini_cast_borders()

        self.ind_dc_start = self.get_downcast_start()
        self.ind_dc_end = self.get_downcast_end()

        if self.ind_dc_end < 0:
            return -1

        if not self.parameters["downcast_only"]:
            self.ind_uc_start = self.get_upcast_start(
                self.ind_dc_end, self.smooth_velo
            )
            self.ind_uc_end = self.get_upcast_end(
                self.ind_dc_end, self.smooth_velo
            )

        return

    def cut_cast_borders(self):
        """
        removes lines outside the cast borders from the given structure

        Returns:
        --------

        either just the downcast or the downcast and the upcast depending on if the "downcast_only" argument was set

        """
        downcast = self.array[self.ind_dc_start : self.ind_dc_end]

        if self.parameters["downcast_only"]:
            return downcast
        else:
            upcast = self.array[self.ind_uc_start : self.ind_uc_end]
            return np.concatenate((downcast, upcast))

    def get_velo(
        self,
        prDM_list: np.array,
    ) -> np.array:
        """
        derives the velocity from the diffrence in depth over a second

        Parameters
        ----------

        prDM_list : list of pressure/depth values

        Returns:
        --------

        velo_arr array with the velocity at each point in the cast

        """
        velo_arr = []
        sampling_rate = 24
        for i in range(len(prDM_list) - sampling_rate):
            velo_arr.append(prDM_list[i + sampling_rate] - prDM_list[i])

        return velo_arr

    def get_downcast_end(
        self,
    ) -> int:
        """
        gets the downcast end of a given cast, meaning the point in the cast, where the ctd begins stops moving downward

        Parameters
        ----------

        Returns:
        --------

        the index of the start of the downcast

        """

        dc_start = self.ind_dc_start

        window = 50
        half_w = int(window / 2)

        average_dc_arr = self.sliding_average(self.prDM_list, window)
        average_dc_arr = self.prDM_list[dc_start : np.argmax(average_dc_arr)]

        pre_avg = 0
        current_avg = 0

        border = -1
        pre_avg = np.average(average_dc_arr[:window])
        for i in range(window, len(average_dc_arr)):
            current_avg = np.average(average_dc_arr[i - half_w : i + half_w])
            if current_avg < pre_avg:
                border = i
                break
            pre_avg = current_avg

        border_ind = border + dc_start

        if border == -1:
            print(
                "ERROR: No cast borders Found, check if the right file is Input and contains the whole cast"
            )
            self.parameters["ERROR"] = (
                "No cast borders Found, Nothing was changed check if the right file is Input and contains the whole cast"
            )
            return -1

        return border_ind

    def get_downcast_start(
        self,
    ) -> int:
        """
        gets the downcast start of a given cast, meaning the point in the cast, where the ctd begins to continuously move downward

        Parameters
        ----------

        Returns:
        --------

        the index of the start of the downcast

        """
        max_pressure_index = np.argmax(self.prDM_list)

        downcast_arr = self.prDM_list[0:max_pressure_index]
        downcast_arr = np.flip(downcast_arr)

        window = 24
        half_w = int(window / 2)

        average_dc_arr = self.sliding_average(downcast_arr, window)

        average_dc_arr = average_dc_arr[int(len(average_dc_arr) * 0.1) :]

        pre_avg = 0
        current_avg = 0

        pre_avg = np.average(average_dc_arr[:window])
        for i in range(window, len(average_dc_arr)):
            current_avg = np.average(average_dc_arr[i - half_w : i + half_w])
            if current_avg > pre_avg:
                border = i
                break
            pre_avg = current_avg

        border_ind = len(average_dc_arr) - border
        return border_ind

    def get_upcast_start(self, ind_dc_end: int, smooth_velo: np.array) -> int:
        upcast_velo_mean = np.mean(smooth_velo[ind_dc_end : len(smooth_velo)])
        for i in range(ind_dc_end, len(smooth_velo)):
            if smooth_velo[i] < upcast_velo_mean * 0.5:
                return i

    def get_upcast_end(self, ind_dc_end: int, smooth_velo: np.array) -> int:
        upcast_velo_mean = np.mean(smooth_velo[ind_dc_end : len(smooth_velo)])
        for i in range(len(smooth_velo) - 1, ind_dc_end, -1):
            if smooth_velo[i] < upcast_velo_mean * 0.5:
                return i

    def sliding_average(
        self, arr: list | np.ndarray, window_size=24
    ) -> list | np.ndarray:
        """
        applies a sliding average on a given list or np.ndarray

        Parameters
        ----------

        arr: list or np.ndarray that is to be filtered
        window_size: size of the sliding average window, default is 24


        Returns:
        --------

        avg_arr: the filtered array

        """

        avg_arr = []
        for i in range(len(arr)):
            if i < window_size:
                avg_arr.append(np.average(arr[0 : window_size - i]))
            else:
                avg_arr.append(
                    np.average(
                        arr[
                            i - int(window_size / 2) : i + int(window_size / 2)
                        ]
                    )
                )

        return avg_arr


def main(args):
    """
    Prepares the file and manages the arguments

    Parameters
    ----------

    args:
        list of arguments


    Returns:
    --------

    instance of cast_borders

    """
    input = Path(args.file)
    if not isinstance(input, str) and not isinstance(input, Path):
        print("Invalid file type, Input .psa or .cnv")
    if isinstance(input, str):
        input = Path(input)
    if input.suffix == ".psa":
        with open(input) as toml:
            doc = parse(toml.read())
            if len(doc["file"]["InputDir"]) > 0:
                input: str = (
                    doc["file"]["InputDir"] + "\\" + doc["file"]["InputFile"]
                )
            else:
                input: str = doc["file"]["InputFile"]

            if len(doc["file"]["OutputDir"]) > 0:
                output: str = (
                    doc["file"]["OutputDir"] + "\\" + doc["file"]["OutputFile"]
                )
            else:
                output: str = doc["file"]["OutputFile"]

            instance = cast_borders()
            instance(
                input=input,
                parameters=doc["arguments"],
                output="cnv",
                output_name=output,
            )
    elif input.suffix == ".cnv":
        args = vars(args)
        instance = cast_borders()
        instance(
            input=input,
            parameters=args,
            output="cnv",
        )
    else:
        print("Invalid File, input .cnv or .psa")


if __name__ == "__main__":
    parser = arg.ArgumentParser()
    parser.add_argument(
        "-c",
        "--cut",
        help="Returns .cnv with bad scans flagged",
        action="store_false",
    )
    parser.add_argument(
        "-d",
        "--downcast_only",
        help="only returns the downcast without the upcast",
        action="store_true",
    )
    parser.add_argument(
        "file",
        help=".cnv file for which cast borders are to be determined or .psa file",
    )
    parser.add_argument(
        "-v",
        "--verbosity",
        action="count",
        default=0,
        help="increase output verbosity",
    )
    args = parser.parse_args()
    main(args)
