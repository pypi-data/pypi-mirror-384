#!/usr/bin/env python
# -*- coding: utf-8 -*-
#  author: Benjamin FARCY, Anne FELDEN

""" Tool Flame param to get laminar premixed flame parameters such as
    laminar flame thickness and laminar flame speed from a table, with
    pressure, fresh gas temperature and equivalence ratio as entries.
"""
import numpy as np
import h5py
from scipy.interpolate import interpn

__all__ = ["FlameTable"]


class FlameTable:
    """
    *FlameTable class includes:*

    :param phi_list: list of equivalence ratios
    :param temperature_list: list of fresh gases temperatures
    :param pressure_list: list of pressures
    :param datanames_list: list of the stored data for the flames
    :param data_dict: dictionnary with all the stored data for the flames
    """

    def __init__(self):

        self.phi_list = None
        self.temperature_list = None
        self.pressure_list = None

        self.datanames_list = None
        self.data_dict = {}
        self.interpolated_data_dict = {}
        self.nparam = None

    def print_param_space(self):
        """Pretty print param space"""

        self.nparam = (
            len(self.phi_list) * len(self.temperature_list) * len(self.pressure_list)
        )
        print(" >>> Parameters space")
        print(" >>> Number of operating conditions: " + str(self.nparam))
        print(str("eq ratio").ljust(20) + ": " + str(np.mean(self.phi_list)) + " [-]")
        print(
            str("temperature").ljust(20)
            + ": "
            + str(np.mean(self.temperature_list))
            + " [K]"
        )
        print(
            str("pressure").ljust(20)
            + ": "
            + str(np.mean(self.pressure_list))
            + " [Pa]"
        )

    def read_table_hdf(self, hdf_filename):
        """
        *Read the flame data table from an hdf format*

        :param hdf_filename: name of the input hdf file
        :param verbosity: display infos
        """

        hdf_file = h5py.File(hdf_filename, "r")

        self.phi_list = hdf_file["Data"]["EQUIVALENCE_RATIO"][:]
        self.temperature_list = hdf_file["Data"]["TEMPERATURE"][:]
        self.pressure_list = hdf_file["Data"]["PRESSURE"][:]

        self.datanames_list = [
            dataset
            for dataset in hdf_file["Data"].keys()
            if not "CLASS" in hdf_file["Data"][dataset].attrs.keys()
        ]
        for dataset in self.datanames_list:
            self.data_dict[dataset] = hdf_file["Data"][dataset][:]

        if isinstance(hdf_file["Data"].attrs["DIM1_NAME"], str):
            dims = [
                hdf_file["Data"].attrs["DIM1_NAME"],
                hdf_file["Data"].attrs["DIM2_NAME"],
                hdf_file["Data"].attrs["DIM3_NAME"],
            ]
        else:  # H5py <3 (2.10)
            dims = [
                hdf_file["Data"].attrs["DIM1_NAME"].decode(),
                hdf_file["Data"].attrs["DIM2_NAME"].decode(),
                hdf_file["Data"].attrs["DIM3_NAME"].decode(),
            ]

        if dims[0] != "EQUIVALENCE_RATIO":
            raise IOError(
                "The first dimension of the table " + "should be EQUIVALENCE_RATIO"
            )
        if dims[1] != "TEMPERATURE":
            raise IOError(
                "The second dimension of the table " + "should be TEMPERATURE"
            )
        if dims[2] != "PRESSURE":
            raise IOError("The third dimension of the table " + "should be PRESSURE")

        hdf_file.close()

    def check_bounds(self, equivalence_ratio, temperature, pressure):
        """Check that the input variables temperature, pressure and
        equivalence ratio are within the bounds of the stored data base
        """
        # print("\n ----", self.pressure_list)
        if (pressure < self.pressure_list[0]) or (pressure > self.pressure_list[-1]):
            raise IOError(
                "Input pressure "
                + str(pressure)
                + " is out of database bounds: "
                + str(self.pressure_list[0])
                + " "
                + str(self.pressure_list[-1])
            )
        if (temperature < self.temperature_list[0]) or (
            temperature > self.temperature_list[-1]
        ):
            raise IOError(
                "Input temperature "
                + str(temperature)
                + " is out of database bounds: "
                + str(self.temperature_list[0])
                + " "
                + str(self.temperature_list[-1])
            )
        if (equivalence_ratio < self.phi_list[0]) or (
            equivalence_ratio > self.phi_list[-1]
        ):
            raise IOError(
                "Input equivalence_ratio "
                + str(equivalence_ratio)
                + " is out of database bounds: "
                + str(self.phi_list[0])
                + " "
                + str(self.phi_list[-1])
            )

    def get_params(self, equivalence_ratio=1.0, temperature=600, pressure=101325):
        """Get the laminar flame params (flame speed, thickness and omega) from
        the pressure, the temperature and the equivalence ratio.
        It involves a trilinear interpolation in the table.
        """

        def squeeze_interp(in_index, in_data):
            """Remove one data dimensions from the interpolation
            becaues interpn is not capable of handling it.
            Example:
             in_index is a tuple:
              in_index: ([0.5, 0.6], [300, 400], [101325])
              out_index: ([0.5, 0.6], [300, 400])
             in_data is an array:
              in_data: [0.55, 350, 101325]
              out_data: [0.55, 350]
            """
            out_index = ()
            out_data = []
            for i_elem, elem in enumerate(in_index):
                if len(elem) > 1:
                    out_index += (elem,)
                    out_data.append(in_data[i_elem])

            return out_index, out_data

        #  bounds error is activated in interpn but it is more explicit
        #  to do it externally
        self.check_bounds(equivalence_ratio, temperature, pressure)

        index, target_point = squeeze_interp(
            (self.phi_list, self.temperature_list, self.pressure_list),
            [equivalence_ratio, temperature, pressure],
        )

        for dataname in self.data_dict:
            self.interpolated_data_dict[dataname] = interpn(
                index,
                np.squeeze(self.data_dict[dataname]),
                target_point,
                bounds_error=True,
            )

    def print_interpolated_data(self):
        """Print interpolated data"""

        for dataname in self.interpolated_data_dict:
            print(str(dataname) + " = " + str(self.interpolated_data_dict[dataname]))
