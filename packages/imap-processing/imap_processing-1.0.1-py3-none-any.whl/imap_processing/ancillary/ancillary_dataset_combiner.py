"""File for taking in multiple ancillary files and creating a combined dataset."""

from __future__ import annotations

import json
from collections import namedtuple
from pathlib import Path

import numpy as np
import xarray as xr
from cdflib.xarray import cdf_to_xarray
from imap_data_access import AncillaryFilePath
from imap_data_access.processing_input import (
    ProcessingInput,
)

TimestampedData = namedtuple(
    "TimestampedData", ["start_time", "end_time", "dataset", "version"]
)


class AncillaryCombiner:
    """
    Class for managing multiple ancillary files, received as one ProcessingInput.

    These are the same files across different time spans and versions.

    The base version of the class works as defined for CDF files which do not have time
    varying variables inside them - so, they are valid from the first second of the
    start_date to the last second of the end_date.

    To change the behavior of the class, the methods "convert_file_to_dataset" and
    "get_combined_dataset" can be overridden. If using a file format that is different
    than CDF, override "convert_file_to_dataset" to convert the file to an xarray
    dataset. If the structure of the input file or output file needs to be changed, or
    they need to be combined in a different way, "get_combined_dataset" should be
    overridden.

    Some ancillary files can extend indefinitely. Therefore, the class requires the user
    to provide an end time, which will be used to create the end of the dataset if
    necessary.

    Parameters
    ----------
    ancillary_input : ProcessingInput
        The input to convert, which consists of a collection of ancillary files from
        different dates, all with differing versions.
    expected_end_date : np.datetime64
        The expected end date of the dataset. This is used to fill in the end date
        of the dataset if it is not provided in the input file. This should either
        be a numpy datetime64 object or a string in the format YYYYMMDD.

    Methods
    -------
    convert_to_timestamped_data(filename)
    convert_file_to_dataset(filepath)
    get_combined_dataset()
    """

    time_variable = "epoch"

    def __init__(
        self,
        ancillary_input: ProcessingInput | list[Path],
        expected_end_date: np.datetime64 | str,
    ):
        self.ancillary_input = ancillary_input
        if isinstance(expected_end_date, str):
            expected_end_date = np.datetime64(
                f"{expected_end_date[:4]}-"
                f"{expected_end_date[4:6]}-"
                f"{expected_end_date[6:]}"
            )

        self.expected_end_date = expected_end_date

        self.timestamped_data = []

        file_path_list = (
            ancillary_input
            if isinstance(ancillary_input, list)
            else ancillary_input.filename_list
        )

        for file in file_path_list:
            self.timestamped_data.append(self.convert_to_timestamped_data(file))

        self.combined_dataset = self._combine_input_datasets()

    def convert_to_timestamped_data(self, filename: str | Path) -> TimestampedData:
        """
        Given an ancillary input, convert it to a TimestampedData object.

        These objects are then used to combine data together.

        Parameters
        ----------
        filename : str | Path
            The ancillary input to convert.

        Returns
        -------
        TimestampedData
            The converted TimestampedData object.
        """
        filepath = AncillaryFilePath(filename)
        dataset = self.convert_file_to_dataset(filepath.construct_path())

        # Convert start_date to np.datetime64
        formatted_str = (
            f"{filepath.start_date[:4]}-"
            f"{filepath.start_date[4:6]}-"
            f"{filepath.start_date[6:]}"
        )  # '2025-07-01'
        start_dt = np.datetime64(formatted_str, "D")

        if filepath.end_date is not None:
            # Convert end_date to np.datetime64
            formatted_str = (
                f"{filepath.end_date[:4]}-"
                f"{filepath.end_date[4:6]}-"
                f"{filepath.end_date[6:]}"
            )
            end_dt = np.datetime64(formatted_str, "D")
        else:
            end_dt = self.expected_end_date

        return TimestampedData(start_dt, end_dt, dataset, filepath.version)

    def convert_file_to_dataset(self, filepath: str | Path) -> xr.Dataset:
        """
        Convert the file at filepath to an xarray dataset.

        This method should be overridden if the input file is not a CDF file.

        Parameters
        ----------
        filepath : str | Path
            The path to the file to convert.

        Returns
        -------
        xr.Dataset
            The converted xarray dataset.
        """
        return cdf_to_xarray(filepath)

    @staticmethod
    def convert_json_to_dataset(filepath: str | Path) -> xr.Dataset:
        """
        Read a JSON file and convert it to an xarray Dataset.

        This method handles JSON files by converting them to xarray Datasets
        with appropriate structure. Nested dictionaries are flattened using
        underscore separation, up to 2 levels deep.

        Parameters
        ----------
        filepath : str | Path
            The path to the JSON file to convert.

        Returns
        -------
        xr.Dataset
            The converted xarray dataset with JSON data as data variables.
        """
        with open(filepath) as f:
            json_data = json.load(f)

        # Convert JSON data to xarray Dataset with appropriate structure
        # Each top-level key becomes a data variable

        # The structure of the dictionary is {<variable_name>: (dims, data)}
        # For the lists, we specify the dimension names. For scalars, pass in [].
        data_vars = {}
        for key, value in json_data.items():
            if isinstance(value, (list, tuple)):
                # Handle arrays/lists
                data_vars[key] = ([f"dim_{key}"], value)
            elif isinstance(value, dict):
                # Handle nested dictionaries by flattening with underscore
                for subkey, subvalue in value.items():
                    flat_key = f"{key}_{subkey}"
                    if isinstance(subvalue, (list, tuple)):
                        data_vars[flat_key] = ([f"dim_{flat_key}"], subvalue)
                    else:
                        data_vars[flat_key] = ([], subvalue)
            else:
                # Handle scalar values
                data_vars[key] = ([], value)

        return xr.Dataset(data_vars)

    def _combine_input_datasets(self) -> xr.Dataset:  # noqa: PLR0912
        """
        Combine all the input datasets into one output dataset.

        This method assumes the input datasets have no time-varying dimensions in them.
        Instead, it will take the full time range covered by the input files, and
        assign each epoch such that each day has the valid data for that day.

        To do this, it checks to see if there is data available for that day, and takes
        the highest version of any file that covers the day. Missing days are filled
        with MAX_INT.

        This assumes that the input files cover a full day for each day in the time
        range. It also assumes that all the input files have the same datavars defined
        the same way.

        Returns
        -------
        xr.Dataset
            The combined dataset.
        """
        output_dataset = xr.Dataset()

        # Handle empty input gracefully
        if not self.timestamped_data:
            return output_dataset

        full_range_start = None
        full_range_end = None
        for timestamped_data in self.timestamped_data:
            start_dt = timestamped_data.start_time
            end_dt = timestamped_data.end_time

            if full_range_start is None or start_dt < full_range_start:
                full_range_start = start_dt
            if full_range_end is None or end_dt > full_range_end:
                full_range_end = end_dt

        # sort by version
        sorted_data_list = sorted(
            self.timestamped_data, key=lambda x: (int(x.version[-3:]))
        )

        epoch_data = xr.date_range(
            full_range_start, full_range_end, freq="D"
        ).values.astype("datetime64[D]")
        output_dataset = output_dataset.assign_coords({self.time_variable: epoch_data})

        if any(["epoch" in i.dataset.dims for i in self.timestamped_data]):
            raise ValueError(
                "ERROR: input dataset has epoch dimension. This is not "
                "allowed for this algorithm."
            )

        # create output dimensions for dataset. Each datavar gets its own anonymous
        # dimension, named like {datavar}_dim_0, {datavar}_dim_1, etc.
        for data_var in self.timestamped_data[0].dataset.data_vars:
            shape = self.timestamped_data[0].dataset[data_var].shape
            var_type = self.timestamped_data[0].dataset[data_var].dtype
            if issubclass(var_type.type, np.integer):
                maxval = np.iinfo(var_type).max
            else:
                maxval = np.iinfo(np.int32).max
            output_dataset[data_var] = xr.DataArray(
                np.full((len(epoch_data), *shape), maxval, dtype=var_type),
                dims=[self.time_variable]
                + [f"{data_var}_dim_{i}" for i in range(len(shape))],
            )

        output_dataset["input_file_version"] = xr.DataArray(
            np.zeros((len(epoch_data),)), dims=[self.time_variable]
        )

        for data_input in sorted_data_list:
            for date in xr.date_range(
                data_input.start_time, data_input.end_time, freq="D"
            ):
                np_date = np.datetime64(date, "D")
                for data_var in output_dataset.data_vars.keys():
                    # find the index in output_dataset where date is equal to epoch
                    index = output_dataset.get_index(self.time_variable).get_loc(
                        np_date
                    )
                    # For each data_var, fill the date in output_dataset with the
                    # data_var from the input dataset.
                    if data_var in "input_file_version":
                        output_dataset["input_file_version"].data[index] = int(
                            data_input.version[-3:]
                        )
                    else:
                        output_dataset[data_var].data[index] = data_input.dataset[
                            data_var
                        ].data

        return output_dataset


class MagAncillaryCombiner(AncillaryCombiner):
    """
    MAG-specific instance of AncillaryConverter.

    Parameters
    ----------
        ancillary_input : ProcessingInput
            Collection of MAG calibration files.
        expected_end_date : np.datetime64 | str
            The expected end date of the dataset. This is used to fill in the end date
            of the dataset if it is not provided in the input file. This should either
            be a numpy datetime64 object or a string in the format YYYYMMDD. For MAG,
            1-2 days after the science file timestamp is sufficient.
    """

    def __init__(
        self,
        ancillary_input: ProcessingInput | list[Path],
        expected_end_date: np.datetime64 | str,
    ):
        super().__init__(ancillary_input, expected_end_date)


class GlowsAncillaryCombiner(AncillaryCombiner):
    """
    GLOWS-specific instance of AncillaryConverter for bad-angle flag data.

    This class handles GLOWS ancillary files for L1B processing, including:
    - Excluded regions map (.dat files with ecliptic coordinates)
    - UV sources map (.dat files with star positions and masking radii)
    - Suspected transients (.dat files with time-based histogram masks)
    - Instrument team exclusions (.dat files with time-based histogram masks)

    Parameters
    ----------
    ancillary_input : ProcessingInput
        Collection of GLOWS ancillary files.
    expected_end_date : np.datetime64 | str
        The expected end date of the dataset. This is used to fill in the end date
        of the dataset if it is not provided in the input file. This should either
        be a numpy datetime64 object or a string in the format YYYYMMDD.
    """

    def __init__(
        self,
        ancillary_input: ProcessingInput | list[Path],
        expected_end_date: np.datetime64 | str,
    ):
        super().__init__(ancillary_input, expected_end_date)

    def convert_file_to_dataset(self, filepath: str | Path) -> xr.Dataset:
        """
        Convert GLOWS ancillary .dat files to xarray datasets.

        This method handles different types of GLOWS ancillary files:
        - excluded_regions: longitude/latitude coordinate pairs
        - uv_sources: star names with coordinates and masking radii
        - suspected_transients: time-based histogram masks
        - exclusions_by_instr_team: time-based histogram masks

        Parameters
        ----------
        filepath : str | Path
            The path to the GLOWS ancillary file to convert.

        Returns
        -------
        xr.Dataset
            The converted xarray dataset with appropriate dimensions and variables.
        """
        filepath = Path(filepath)
        filename = filepath.name

        if "excluded-regions" in filename:
            # Handle excluded regions (2 columns: longitude, latitude)
            data = np.loadtxt(filepath, comments="#")
            return xr.Dataset(
                {
                    "ecliptic_longitude_deg": (["region"], data[:, 0]),
                    "ecliptic_latitude_deg": (["region"], data[:, 1]),
                }
            )

        elif "uv-sources" in filename:
            # Handle UV sources (4 columns: name, longitude, latitude, radius)
            data = np.loadtxt(filepath, comments="#", dtype=str)
            return xr.Dataset(
                {
                    "object_name": (["source"], data[:, 0]),
                    "ecliptic_longitude_deg": (["source"], data[:, 1].astype(float)),
                    "ecliptic_latitude_deg": (["source"], data[:, 2].astype(float)),
                    "angular_radius_for_masking": (
                        ["source"],
                        data[:, 3].astype(float),
                    ),
                }
            )

        elif "suspected-transients" in filename:
            # Handle suspected transients (time identifier + mask string)
            with open(filepath) as f:
                lines = [line.strip() for line in f if not line.startswith("#")]
            identifiers = [line.split(" ", 1)[0] for line in lines]
            masks = [line.split(" ", 1)[1] for line in lines]
            return xr.Dataset(
                {
                    "l1b_unique_block_identifier": (["time_block"], identifiers),
                    "histogram_mask_array": (["time_block"], masks),
                }
            )

        elif "exclusions-by-instr-team" in filename:
            # Handle instrument team exclusions (time identifier + mask string)
            with open(filepath) as f:
                lines = [line.strip() for line in f if not line.startswith("#")]
            identifiers = [line.split(" ", 1)[0] for line in lines]
            masks = [line.split(" ", 1)[1] for line in lines]
            return xr.Dataset(
                {
                    "l1b_unique_block_identifier": (["time_block"], identifiers),
                    "histogram_mask_array": (["time_block"], masks),
                }
            )

        elif filename.endswith(".json"):
            # Handle pipeline settings JSON file using the generic read_json method
            return self.convert_json_to_dataset(filepath)

        else:
            raise ValueError(f"Unknown GLOWS ancillary file type: {filename}")
