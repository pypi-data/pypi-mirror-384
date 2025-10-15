import importlib.metadata
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from seabirdfilehandler import CnvFile
from seabirdfilehandler.parameter import Parameters

from processing.utils import get_sample_rate

logger = logging.getLogger(__name__)


class Module(ABC):
    """
    An interface to implement new processing modules against.

    Is meant to perform and unify all the necessary work that is needed to
    streamline processing on Sea-Bird CTD data. Implementing classes should
    only overwrite the transformation method, that does the actual altering of
    the data. All other organizational overhead should be covered by this
    interface. This includes parsing to .cnv output with correct handling of
    the metadata header.
    """

    shortname = ""
    longname = ""
    unit = ""

    def __init__(self) -> None:
        self.parent_module = "ctd-processing"
        self.info = self.__doc__
        self.name = self.__class__.__name__.lower()

    def __call__(
        self,
        input: Path | str | CnvFile | pd.DataFrame | np.ndarray,
        parameters: dict,
        output: str = "cnvobject",
        output_name: str | None = None,
    ) -> None | CnvFile | pd.DataFrame | np.ndarray:
        self.parameters = parameters
        self.output_name = output_name

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.__str__()

    def add_processing_metadata(self):
        """
        Parses the module processing information into cnv-compliant metadata
        lines.

        These take on the form of {MODULE_NAME}_{KEY} = {VALUE} for every
        key-value pair inside of the given dictionary with the modules
        processing info.

        """
        if isinstance(self.cnv, CnvFile):
            # general header for every module
            timestamp = datetime.now(timezone.utc).strftime(
                "%Y.%m.%d %H:%M:%S"
            )
            try:
                version = (
                    f", v{importlib.metadata.version(self.parent_module)}"
                )
            except Exception:
                version = ""
            self.cnv.add_processing_metadata(
                module=self.name,
                key="metainfo",
                value=f"{timestamp}, {self.parent_module} python package{version}",
            )
            for key, value in self.parameters.items():
                if key == "file_suffix":
                    continue
                self.cnv.add_processing_metadata(
                    module=self.name,
                    key=key,
                    value=value,
                )
        else:
            logger.error(
                "Cannot write processing metainfo without any cnv source."
            )

    def load_file(self, file_path: Path) -> CnvFile:
        """
        Loads the target files information into an CnvFile instance.

        Parameters
        ----------
        file_path: Path :
            Path to the target file.

        Returns
        -------
        CnvFile object representing the file in the file system.

        """
        return CnvFile(file_path)

    @abstractmethod
    def to_cnv(self):
        pass


class ArrayModule(Module):
    def __init__(self) -> None:
        super().__init__()

    def __call__(
        self,
        input: Path | str | CnvFile | pd.DataFrame | np.ndarray,
        parameters: dict = {},
        output: str = "cnvobject",
        output_name: str | None = None,
        original_input_path: Path | str | None = None,
    ) -> None | CnvFile | pd.DataFrame | np.ndarray:
        super().__call__(input, parameters, output, output_name)
        if isinstance(input, Path | str):
            self.cnv = CnvFile(input, create_dataframe=False)
            self.array = self.cnv.parameters.full_data_array
            self.original_input_path = Path(input)
        elif isinstance(input, CnvFile):
            self.cnv = input
            self.cnv.parameters = Parameters(
                self.cnv.data, self.cnv.data_table_description
            )
            self.array = self.cnv.parameters.full_data_array
            self.original_input_path = input.path_to_file
        else:
            raise TypeError(f"Incorrect input type: {type(input)}. Aborting.")
        if original_input_path:
            self.original_input_path = Path(original_input_path)
        self.sample_interval = get_sample_rate(self.cnv)
        self.ran_processing = self.transformation()
        if self.ran_processing:
            self.add_processing_metadata()
        if "file_suffix" in self.parameters:
            output = "cnv"
        if output.lower() in ("cnv", "file"):
            self.to_cnv()
            return self.cnv
        elif output.lower() in ("internal", "cnvobject") and isinstance(
            self.cnv, CnvFile
        ):
            return self.cnv
        else:
            return self.array

    @abstractmethod
    def transformation(self) -> bool:
        pass

    def to_cnv(self):
        if not self.cnv:
            return
        self.cnv.parameters.full_data_array = self.array
        if "file_suffix" in self.parameters:
            if self.output_name:
                output_name = Path(self.output_name)
                stem = output_name.stem
                self.output_name = output_name.with_stem(
                    stem + self.parameters["file_suffix"]
                )
            else:
                self.output_name = self.cnv.path_to_file.with_stem(
                    self.cnv.file_name + self.parameters["file_suffix"]
                )
        self.cnv.to_cnv(file_name=self.output_name, use_dataframe=False)


class DataFrameModule(Module):
    def __call__(
        self,
        input: Path | str | CnvFile | pd.DataFrame | np.ndarray,
        parameters: dict = {},
        output: str = "cnvobject",
        output_name: str | None = None,
    ) -> None | CnvFile | pd.DataFrame | np.ndarray:
        super().__call__(input, parameters, output, output_name)
        if isinstance(input, Path | str):
            self.cnv = self.load_file(Path(input))
            self.df = self.cnv.df
        elif isinstance(input, CnvFile):
            self.cnv = input
            self.df = self.cnv.df
        elif isinstance(input, pd.DataFrame):
            self.cnv = None
            self.df = input
        else:
            raise TypeError(f"Incorrect input type: {type(input)}. Aborting.")
        self.df = self.transformation()
        self.add_processing_metadata()
        if output.lower() in ("cnv", "file"):
            self.to_cnv()
            return None
        elif output.lower() in ("internal", "cnvobject") and isinstance(
            self.cnv, CnvFile
        ):
            return self.cnv
        else:
            return self.df

    @abstractmethod
    def transformation(self) -> pd.DataFrame:
        """
        The actual data transformation on the CTD data.

        Needs to be implemented by the implementing classes.
        """
        df = self.df
        return df

    def _alter_cnv_data_table_description(
        self,
        shortname: str | None = None,
        secondary_column: bool = False,
    ):
        """

        Parameters
        ----------
        shortname: str | None :
             (Default value = None)
        secondary_column: bool :
             (Default value = False)

        Returns
        -------

        """
        shortname = self.shortname if shortname is None else shortname
        assert isinstance(self.cnv, CnvFile)
        # update number of columns
        self.cnv.data_table_stats["nquan"] = len(self.cnv.df.columns)
        # add column name
        name = f"{shortname}: {self.longname}{
            ', 2' if secondary_column else ''
        } [{self.unit}]"
        # add column span
        span = f"{self.cnv.df[shortname].min().round(4)}, {
            self.cnv.df[shortname].max().round(4)
        }"
        self.cnv.data_table_names_and_spans.append((name, span))

    def _check_parameter_existence(self, parameter: str) -> bool:
        """
        Helper method to ensure parameter presence in input data before
        attempting the transformation.

        Parameters
        ----------
        parameter: str :
            The parameter to check for.

        Returns
        -------
        Whether the parameter is present inside of the cnv dataframe or not.

        """
        # ensure shortnames as column names
        self.df.meta.header_detail = "shortname"
        return parameter in self.df.columns

    def to_cnv(
        self,
        additional_data_columns: list[str] = [],
        custom_data_columns: list | None = None,
    ):
        """
        Writes the internal CnvFile instance to disk.

        Uses the CnvFile's output parser for that and organizes the different
        bits of information for that.

        Parameters
        ----------
        additional_data_columns: list[str] :
            A list of columns that in addition to the ones inside the original
            dataframe.
             (Default value = [])
        custom_data_columns: list | None :
            A list of coulumns that will exclusively used to select the data
            items for the output .cnv .
             (Default value = None)

        """
        if isinstance(self.cnv, CnvFile):
            if custom_data_columns:
                header_list = custom_data_columns
            else:
                header_list = [
                    header[self.cnv.df.meta.header_detail]
                    for header in list(self.cnv.df.meta.metadata.values())
                ]
            self.cnv.df = self.df
            self.cnv.to_cnv(
                file_name=self.output_name,
                header_list=[*header_list, *additional_data_columns],
            )
        else:
            logger.error("Cannot write to cnv without any cnv as source.")

    def to_csv(self):
        """Writes the dataframe as .csv to disk."""
        try:
            self.df.to_csv()
        except IOError as error:
            logger.error(f"Failed to write dataframe to csv: {error}")


class MissingParameterError(Exception):
    """A custom error to throw when necessary parameters are missing from the
    input .cnv file."""

    def __init__(self, step_name: str, parameter_name: str):
        super().__init__(
            f"Could not run processing step {
                step_name
            } due to a missing parameter: {parameter_name}"
        )
