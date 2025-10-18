# ms_thermo

![logo_msthermo](https://cerfacs.fr/coop/images/logo_msthermo.gif)

This is a small package from Cerfacs dedicated to multispecies thermodynamics operations.

*It is available on [PyPI](https://pypi.org/project/ms-thermo/),
documentation is on [readtthedocs](https://ms-thermo.readthedocs.io/en/latest/), sources are mirrored on [gitlab.com](https://gitlab.com/cerfacs/ms_thermo)*

## Installation

Install from Python Package index:

```shell
pip install ms_thermo
```

## Features

### Command line tools

Once the package is installed, you have access in your terminal to a CLI from the command `ms_thermo`:

```bash
Usage: ms_thermo [OPTIONS] COMMAND [ARGS]...

  ---------------    MS-THERMO  --------------------

  You are now using the Command line interface of MS-Thermo, a Python3
  helper for reactive multispecies computation, created at CERFACS
  (https://cerfacs.fr).

  This is a python package currently installed in your python environement.
  See the full documentation at : https://ms-
  thermo.readthedocs.io/en/latest/.

Options:
  --help  Show this message and exit.

Commands:
  fresh-gas       (Deprecated) Renamed as kero-prim2cons
  gasout          Apply GASOUT actions to a mixture.
  hp-equil        HP equilibrium using Cantera.
  kero-prim2cons  Primitive to conservative variable conversion...
  kero-tadia      Adiabatic flame temperature for a kerosene-air...
  tadia           (Deprecated) Renamed as kero-tadia
  yk-from-phi     Mass fractions of a fuel-air mixture.
```

Details on the commands are available in the [documentation](https://ms-thermo.readthedocs.io/en/latest/explanations/cli.html#command-line-tools).

### The `State` class

The `State` class describes the full thermodynamic state of a gas mixture.
As an example, the following script creates an initial mixture of fresh gases, then changes a subset of the field into hot gases.

```
>>> from ms_thermo.state import State
>>> case = State()
>>> print(case)

Current primitive state of the mixture

		        | Most Common |    Min    |    Max
----------------------------------------------------
             rho| 1.17192e+00 | 1.172e+00 | 1.172e+00
          energy| 2.16038e+05 | 2.160e+05 | 2.160e+05
     temperature| 3.00000e+02 | 3.000e+02 | 3.000e+02
        pressure| 1.01325e+05 | 1.013e+05 | 1.013e+05
            Y_O2| 2.32500e-01 | 2.325e-01 | 2.325e-01
            Y_N2| 7.67500e-01 | 7.675e-01 | 7.675e-01

>>> case.temperature = 1200
>>> print(case)

Current primitive state of the mixture
			   	| Most Common |    Min    |    Max
----------------------------------------------------
             rho| 2.92980e-01 | 2.930e-01 | 2.930e-01
          energy| 9.41143e+05 | 9.411e+05 | 9.411e+05
     temperature| 1.20000e+03 | 1.200e+03 | 1.200e+03
        pressure| 1.01325e+05 | 1.013e+05 | 1.013e+05
            Y_O2| 2.32500e-01 | 2.325e-01 | 2.325e-01
            Y_N2| 7.67500e-01 | 7.675e-01 | 7.675e-01
```

Additional details on the commands are provided in the [documentation](https://ms-thermo.readthedocs.io/en/latest/explanations/state.html#).
