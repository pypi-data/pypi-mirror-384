"""
``State`` is an object handling the internal state of a gaseous mixture, namely:

- Density
- Total energy
- Species mass fractions

Limitations of the ``State`` object
===================================
- Velocity is not a property of a ``State`` and must be treated separately.
- The spatial aspects, i.e. the position of the points, or the mesh, must be handled separately.

.. warning:: ``State`` variables are represented as structured arrays that must have the *same* shape

Initializing a ``State``
========================
A ``State`` object can be initialized in two ways:

- From the temperature, pressure, and species mass fractions :math:`(T, P, Y_k)` through the default constructor::

    state = State(T, P, Yk)

- From conservative variables :math:`(\\rho, \\rho E, \\rho Y_k)` through the ``from_cons`` constructor::

    state = State.from_cons(rho, rhoE, rhoYk)

The constructor arguments :math:`(T, P, Y_k)` or :math:`(\\rho, \\rho E, \\rho Y_k)` can be scalars or multidimensional arrays.

.. warning::
    When initializing from conservative variables, :math:`T` is determined by a
    Newton-Raphson method to ensure that the mixture energy matches the input total energy.
    This is an **expensive** step that may take a long time for large inputs.

Transforming a ``State``
========================
After a ``State`` has been initialized, :math:`T`, :math:`P` and :math:`Y_k` can
independently be set to new values (`e.g.` ``myState.temperature = newTemperature``) and the other state variables are modified
accordingly:

- When setting a new value for :math:`T`, the other state variables are modified assuming an **isobaric and iso-composition** transformation from the previous state.
- When setting a new value for :math:`P`, the other state variables are modified assuming an **isothermal and iso-composition** transformation from the previous state.
- When setting a new value for :math:`Y_k`, the other state variables are modified assuming an **isothermal and isobaric** transformation from the previous state.

State transformations always satisfy the perfect gas equation of state

.. math:: P = \\rho \\frac{R}{W_{mix}} T
"""

from importlib import resources
import numpy as np
from scipy.optimize import newton
from scipy.stats import mode
from ms_thermo.species import build_thermo_from_avbp
from ms_thermo.constants import GAS_CST, ATOMIC_WEIGHTS
import warnings

__all__ = ["State"]


class State:
    """Container class to handle mixtures."""

    def __init__(
        self,
        species_db=None,
        temperature=300.0,
        pressure=101325.0,
        mass_fractions_dict=None,
    ):
        """
        Initialize a ``State`` object.

        :param species_db: Species database, defaults to AVBP species database
        :type species_db: Species, optional
        :param temperature: Temperature, defaults to 300 K
        :type temperature: ndarray or scalar, optional
        :param pressure: Pressure, defaults to 1 atm
        :type pressure: ndarray or scalar, optional
        :param mass_fractions_dict: Species mass fractions, defaults to air
        :type mass_fractions_dict: dict[str, ndarray or scalar], optional
        """
        self.species = species_db
        if self.species is None:
            self._default_thermo_database()

        self._y_k = dict()
        if mass_fractions_dict is None:
            self._y_k = {"O2": 0.2325, "N2": 0.7675}
        else:
            self._y_k = mass_fractions_dict
        self._check_y_input(self._y_k)

        self.rho = pressure * self.mix_w / (GAS_CST * temperature)

        self.energy = self.mix_energy(temperature)
        self._temperature = temperature

    def __repr__(self):
        """Define the value returned by calling State representation (printing State)"""
        mini = dict()
        maxi = dict()
        moco = dict()
        moco["rho"] = mode(self.rho, axis=None, keepdims=False)[0]
        mini["rho"] = np.min(self.rho)
        maxi["rho"] = np.max(self.rho)
        moco["energy"] = mode(self.energy, axis=None, keepdims=False)[0]
        mini["energy"] = np.min(self.energy)
        maxi["energy"] = np.max(self.energy)
        moco["temperature"] = mode(self.temperature, axis=None, keepdims=False)[0]
        mini["temperature"] = np.min(self.temperature)
        maxi["temperature"] = np.max(self.temperature)
        moco["pressure"] = mode(self.pressure, axis=None, keepdims=False)[0]
        mini["pressure"] = np.min(self.pressure)
        maxi["pressure"] = np.max(self.pressure)
        for specy in self._y_k:
            frac_specy = "Y_" + specy
            moco[frac_specy] = mode(self._y_k[specy], axis=None, keepdims=False)[0]
            mini[frac_specy] = np.min(self._y_k[specy])
            maxi[frac_specy] = np.max(self._y_k[specy])
        repr_str = "\nCurrent primitive state of the mixture \n"
        repr_str += "\t\t| Most Common |    Min    |    Max \n"
        repr_str += "-" * 52 + "\n"
        for var in moco:
            infos = (var, moco[var], mini[var], maxi[var])
            repr_str += "%16s| %#.05e | %#.03e | %#.03e \n" % infos

        return repr_str

    @classmethod
    def from_cons(cls, rho, rho_e, rho_y, species_db=None):
        """
        Class constructor from conservative values.

        :param rho: Density
        :type rho: ndarray or scalar
        :param rho_e: Total energy (conservative form)
        :type rho_e: ndarray or scalar
        :param rho_y: Species mass fractions (conservative form)
        :type rho_y: dict[str, ndarray or scalar]
        :param species_db: Species database, defaults to AVBP species database
        :type species_db: Species, optional
        """
        y_k = dict()
        for specy in rho_y:
            y_k[specy] = np.divide(rho_y[specy], rho)
        # State is initialized with default T, P
        state = cls(species_db=species_db, mass_fractions_dict=y_k)
        state.energy = np.divide(rho_e, rho)

        # Only rho and T need to be set. P is always derived from the equation of state
        state.rho = rho
        # Don't use the temperature setter as it modifies rho assuming an isobaric
        # transformation, which is not the case when starting from the default T,P
        state._temperature = state._energy_to_temperature(state.energy)
        return state

    @property
    def mass_fracs(self):
        """Getter or setter for the species mass fractions. Setting the mass fractions
        will modify the density assuming an isothermal and isobaric transformation.

        :rtype: dict[str, ndarray or scalar]
        """
        return self._y_k

    @mass_fracs.setter
    def mass_fracs(self, mass_fractions_dict):
        mol_weight_old = self.mix_w
        # actual update
        self._check_y_input(mass_fractions_dict)
        self._y_k = dict()
        for k in mass_fractions_dict:
            self._y_k[k] = mass_fractions_dict[k]

        mol_weight_new = self.mix_w
        self.rho = self.rho * mol_weight_new / mol_weight_old
        self.energy = self.mix_energy(self._temperature)

    @property
    def temperature(self):
        """Getter or setter for the temperature. Setting the temperature will recompute
        the total energy and modify the density assuming an isobaric transformation.

        :rtype: ndarray or scalar
        """
        return self._temperature

    @temperature.setter
    def temperature(self, temp):
        self.rho = np.divide(np.multiply(self.rho, self.temperature), temp)
        self._temperature = temp
        self.energy = self.mix_energy(temp)

    @property
    def pressure(self):
        """Getter or setter for the pressure. Setting the pressure will modify the
        density assuming an isothermal transformation.

        :rtype: ndarray or scalar
        """
        return self.rho * self.temperature * GAS_CST / self.mix_w

    @pressure.setter
    def pressure(self, press):
        self.rho = np.divide(np.multiply(self.rho, press), self.pressure)

    @property
    def gamma(self):
        """
        Get the heat capacity ratio

        :returns: **gamma** - Heat capacity ratio
        :rtype: ndarray or scalar
        """
        return self.c_p / self.c_v

    @property
    def c_p(self):
        r"""
        Get the mixture-averaged heat capacity at constant pressure

        .. warning::
            :math:`C_p` is computed like in AVBP as :math:`C_v+P/(\rho T)`, *not* as
            the weighted average of species :math:`C_{p,k}`

        :returns: **Cp** - Heat capacity at constant pressure
        :rtype: ndarray or scalar
        """
        # YOu thought it would this, me too
        # But  no!!!
        # c_p =  sum(
        #     self._y_k[k] * self.species[k].c_p(self.temperature)
        #     for k in self.list_spec

        c_p = self.c_v + self.pressure / (self.rho * self.temperature)

        return c_p

    @property
    def c_v(self):
        """
        Get the mixture-averaged heat capacity at constant volume

        :returns: **Cv** - Heat capacity at constant volume
        :rtype: ndarray or scalar
        """
        temp = self.temperature
        return sum(self._y_k[k] * self.species[k].c_v(temp) for k in self.list_spec)

    @property
    def csound(self):
        """
        Get the speed of sound

        :returns: **csound** - Speed of sound
        :rtype: ndarray or scalar
        """
        csound = np.sqrt(self.gamma * GAS_CST / self.mix_w * self.temperature)
        return csound

    @property
    def list_spec(self):
        """
        Get the names of the species

        :returns: **species_names** - List of species names
        :rtype: list[str]
        """
        return list(self._y_k.keys())

    @property
    def mix_w(self):
        r"""
        Compute the mixture molecular weight:

        .. math:: W_{mix} = \left[ \sum_{k=1}^{N_{sp}} \frac{Y_k}{W_k} \right]^{-1}

        :returns: **mix_mw** - Mixture molecular weight
        :rtype: ndarray or scalar
        """
        y_ov_w = [
            np.divide(self._y_k[k], self.species[k].molecular_weight)
            for k in self.list_spec
        ]
        mix_mw = 1.0 / np.sum(y_ov_w, axis=0)
        return mix_mw

    def mach(self, velocity):
        """
        Compute the Mach number

        :param velocity: Velocity
        :type velocity: ndarray or scalar

        :returns: **M** - Mach number
        :rtype: ndarray or scalar
        """
        return velocity / self.csound

    def temperature_total(self, velocity):
        r"""
        Compute the total temperature:

        .. math:: T_t = T \left[1+\frac{\gamma-1}{2}M^2 \right]

        where :math:`M` is the Mach number derived from the input velocity.
        This assumes an isentropic flow and constant gamma.

        :param velocity: Velocity
        :type velocity: ndarray or scalar

        :returns: **temp_total** - Total temperature
        :rtype: ndarray or scalar
        """
        return (
            1 + 0.5 * (self.gamma - 1) * self.mach(velocity) ** 2
        ) * self.temperature

    def pressure_total(self, velocity):
        r"""
        Compute the total pressure:

        .. math:: P_t = P \left[1+\frac{\gamma-1}{2}M^2 \right]^{\frac{\gamma}{\gamma-1}}

        where :math:`M` is the Mach number derived from the input velocity.
        This assumes an isentropic flow and constant gamma.

        :param velocity: Velocity
        :type velocity: ndarray or scalar
        :returns: **press_total** - Total pressure
        :rtype: ndarray or scalar
        """
        return (
            np.power(
                1 + 0.5 * (self.gamma - 1) * self.mach(velocity) ** 2,
                (self.gamma / (self.gamma - 1)),
            )
            * self.pressure
        )

    def mix_energy(self, temperature):
        r"""
        Compute the mixture total energy:

        .. math:: e = \sum_{k=1}^{N_{sp}} Y_k e_k

        :param temperature: Temperature
        :type temperature: ndarray or scalar

        :returns: **mix_energy** - Mixture total energy
        :rtype: ndarray or scalar
        """
        # Chesterton fence
        # func is called within setter self.temperature
        # do not use self.temperature here
        return sum(
            self._y_k[k] * self.species[k].total_energy(temperature)
            for k in self.list_spec
        )

    def mix_enthalpy(self, temperature):
        r"""
        Get mixture total enthalpy:

        .. math:: h = \sum_{k=1}^{N_{sp}} Y_k h_k

        :param temperature: Temperature
        :type temperature: ndarray or scalar

        :returns: **mix_enthalpy** - Mixture total enthalpy
        :rtype: ndarray or scalar
        """
        return sum(
            self._y_k[k] * self.species[k].total_enthalpy(temperature)
            for k in self.list_spec
        )

    def update_state(self, temperature=None, pressure=None, mass_fracs=None):
        """
        Compute density from temperature, pressure and mass fractions by assuming the
        following transformations:

            1) Isobaric and isothermal transformation,
            i.e (*P=cst*, *T=cst* and only **composition** is varying)

            2) Isobaric and iso-composition transformation,
            i.e (*P=cst*, *Y=cst* and only **temperature** is varying)

            3) Isothermal and iso-composition transformation,
            i.e (*T=cst*, *Y=cst* and only **pressure** is varying)

        :param temperature: Temperature to set, defaults to None
        :type temperature: ndarray or scalar, optional
        :param pressure: Pressure to set, defaults to None
        :type pressure: ndarray or scalar, optional
        :param mass_fracs: Mass fractions to set, defaults to None
        :type mass_fracs: dict[str, ndarray or scalar], optional
        """
        if mass_fracs is not None:
            self.mass_fracs = mass_fracs
        if temperature is not None:
            self.temperature = temperature
        if pressure is not None:
            self.pressure = pressure

    def compute_z_frac(
        self,
        specfuel,
        fuel_mass_fracs=None,
        oxyd_mass_fracs=None,
        atom_ref="C",
        verbose=False,
    ):
        """Compute the Z mixture fraction.

        0 oxidizer, 1 fuel

        :param specfuel: Fuel species
        :type specfuel: str
        :param fuel_mass_fracs: Fuel mass fractions, defaults to composition at peak fuel concentration
        :type fuel_mass_fracs: dict, optional
        :param oxyd_mass_fracs: Oxydizer mass fractions, defaults to air
        :type oxyd_mass_fracs: dict, optional
        :param atom_ref: Reference atom, defaults to C
        :type atom_ref: str, optional
        :param verbose: Verbosity, defaults to False
        :type verbose: bool, optional

        :returns: Z Mixture fraction
        :rtype: ndarray or scalar
        """
        log = "Computing Z fraction"
        if fuel_mass_fracs is None:
            # find where the maximum fuel concentration
            fuel_mass_fracs = dict()
            idx = np.argmax(self.mass_fracs[specfuel].ravel())
            for spec in self.mass_fracs:
                fuel_mass_fracs[spec] = self.mass_fracs[spec].ravel()[idx]
            log += "   Fuel mixture taken as : "
            for spec in fuel_mass_fracs:
                log += "\n.  - " + spec + ":" + str(fuel_mass_fracs[spec])
            log += "\n"
        if oxyd_mass_fracs is None:
            oxyd_mass_fracs = {"O2": 0.233, "N2": 0.767}
            log += "\n.  Oxidizer mixture taken as AIR."

        z_frac = 0.0
        z_fuel = 0.0
        z_oxyd = 0.0

        for spec in self.mass_fracs:
            nb_atoms = self.species[spec].atoms

            rel_weight = (
                nb_atoms[atom_ref]
                * ATOMIC_WEIGHTS[atom_ref.lower()]
                / self.species[spec].molecular_weight
            )
            z_frac += self.mass_fracs[spec] * rel_weight
            if spec in fuel_mass_fracs:
                z_fuel += fuel_mass_fracs[spec] * rel_weight
            if spec in oxyd_mass_fracs:
                z_oxyd += oxyd_mass_fracs[spec] * rel_weight

        z_frac = (z_frac - z_oxyd) / (z_fuel - z_oxyd)

        if verbose:
            print(log)
        return z_frac

    def _temp_energy_res(self, temperature):
        """Compute energy residuals from temperature.

        :param temperature: Temperature
        :type temperature: ndarray or scalar
        :returns: Energy residual
        :rtype: ndarray or scalar
        """
        comp_energy = self.mix_energy(temperature)
        total_energy = self.energy
        diff = 1.0 - comp_energy / total_energy
        return diff

    def _default_thermo_database(self):
        """
        Initialize the thermodynamic database if none is provided.

        By default it is the AVBP standard species database.
        """

        thermo_db_file = str(
            resources.files(__package__) / "INPUT/species_database.dat"
        )

        self.species = build_thermo_from_avbp(thermo_db_file)

    def _check_y_input(self, mass_fractions_dict):
        """
        Check if the names of the species are in the database
        the sum of mixture species mass fractions is unity

        :param mass_fractions_dict: Mass fractions
        :type mass_fractions_dict: dict[str, ndarray or scalar]
        """
        y_tol = 1.0e-5
        not_one_msg = "Mass fraction sum is not unity at point %d"
        not_in_db_msg = "Species %s is not present in the database"

        # check species presence
        for specie in mass_fractions_dict:
            if specie not in self.species:
                msg = not_in_db_msg % specie
                raise ValueError(msg)

        # check sum
        sum_y = 0
        for specie in mass_fractions_dict:
            sum_y += mass_fractions_dict[specie]
        conds = np.abs(sum_y - 1.0) > y_tol
        is_not_one = np.any(conds)
        if is_not_one:
            index = np.where(conds)[0][0]
            msg = not_one_msg % index
            msg += "\n min:" + str(np.min(sum_y))
            msg += "\n max:" + str(np.max(sum_y))
            raise ValueError(msg)

    def _energy_to_temperature(self, energy):
        r"""
        Find the temperature `T` that satisfies the constraint:

        .. math:: e = \sum_{k=1}^{N_{sp}} Y_k e_k(T)

        given a target value of the total energy `e`.

        :param energy: Target total energy
        :type energy: ndarray or scalar

        :returns: Temperature
        :rtype: ndarray or scalar
        """
        guess = np.ones_like(energy) * 300.0
        temperature = newton(self._temp_energy_res, guess, tol=1e-12)
        return temperature

    # Deprecated ====================================================================

    def list_species(self):
        r"""
        *Return primitives species names*.

        :returns: **species_names** - A list( ) of primitives species names

        """
        warnings.simplefilter("ignore")
        msgwarn = "ms_thermo.state.list_species() is deprecated,"
        msgwarn += "use instead ms_thermo.state.list_spec"
        warnings.warn(msgwarn)
        print(msgwarn)
        return self.list_spec

    def mix_molecular_weight(self):
        r"""
        *Compute mixture molecular weight following the formula :*

        .. math:: W_{mix} = \left[ \sum_{k=1}^{N_{sp}} \frac{Y_k}{W_k} \right]^{-1}

        :returns: **mix_mw** (float) - Mixture molecular weight
        """
        warnings.simplefilter("ignore")
        msgwarn = "ms_thermo.state.mix_molecular_weight() is deprecated,"
        msgwarn += "use instead ms_thermo.state.mix_w"
        warnings.warn(msgwarn)
        print(msgwarn)
        return self.mix_w
