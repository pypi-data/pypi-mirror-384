""" Module for species and mixture """

import numpy as np

ATOMIC_MASS = {"C": 12.0107, "H": 1.00784, "O": 15.999, "N": 14.0067}


class SpeciesState:
    """
    *Class managing species*

    :Attributes:

        - **_name** - Name of the species
        - **_atoms** - Dict['CHON'] of atom numbers
        - **_molar_mass** - Molar mass of the species
        - **_mass_fraction** - Mass fraction of the species
        - **_stream** - Input stream of the species
        - **_mass_fraction_stream** - Mass fraction streamwise
    """

    def __init__(self, name, mass_fraction, stream=None, mass_fraction_stream=0.0, species_database:str=None):
        """Initialize SpeciesState class"""
        self._name = name.upper()
        if species_database is None:
            self._atoms = get_atoms_chon_by_name(self._name)
        else:
            self._atoms = self._get_atoms_mdb(species_database)
        self._molar_mass = self._get_molar_mass()
        self._mass_fraction = mass_fraction
        self._stream = stream
        self._mass_fraction_stream = mass_fraction_stream

    @property
    def atoms(self):
        """returns dict['CHON'] of number of atoms"""
        return self._atoms

    @property
    def molar_mass(self):
        """returns species molar mass"""
        return self._molar_mass

    @property
    def name(self):
        """returns species name"""
        return self._name

    def set_stream_data(self, stream, mass_frac):
        """
        *Set stream of the species and streamwise mass fraction*

        :param stream: Input stream number of the species (1 for fuel, 2 for oxydizer)
        :type stream: int
        :param mass_frac: Streamsize mass fraction of the species:
        :type mass_frac: float
        """
        self._stream = stream
        self._mass_fraction_stream = mass_frac

    def mass_fraction(self, stream=None):
        """
        *Returns either mass fraction or stream-wize mass fraction*

        :returns: Mass Fraction of the species
        """
        if stream is None:
            mass_fraction = self._mass_fraction
        else:
            mass_fraction = self._mass_fraction_stream * (stream == self._stream)
        return mass_fraction

    def mass(self):
        """
        *Compute the mass of the species*

        :returns: Mass of the species
        """
        mass = 0.0
        for atom, n_atom in self.atoms.items():
            mass += n_atom * ATOMIC_MASS[atom]
        return mass

    def _get_atoms_mdb(self, species_database):

        atoms = {}
        with open(species_database ,"r") as fin:
            mdb_lines = fin.readlines()
        idx = None
        for i,line in enumerate(mdb_lines):
            if line.startswith("species_name ") and line.split("=")[-1].strip() == self._name:
                idx = i
                break
        
        if idx is None:
            return get_atoms_chon_by_name(self._name)
            
        for atom in "CHON":
            for line in mdb_lines[idx:]:
                if line.startswith(f"species_{atom}_atoms "):
                    atoms[atom] = float(line.split("=")[-1].strip().replace("d","e"))
                    break
        return atoms

    def _get_molar_mass(self):
        """
        *Compute the molar mass of the species*

            m_i = sum_j (n_i,j * M_j)

        with :

            - i : Species
            - j : Atom

        :returns: Molar mass of the species
        """

        molar_mass = 0.0
        for atom, n_atoms in self._atoms.items():
            molar_mass += n_atoms * ATOMIC_MASS[atom]

        return molar_mass


# TODO : awgh very complicated PI, we should do something easier next time!!!
def get_atoms_chon_by_name(string_chon:str):
    """
    *Get number of atoms of "CHON" in the species*

    :returns: Dict['CHON'] of number of atoms
    """
    atoms = {}
    idx = 0
    if "-" in string_chon:
        string_chon = string_chon.split("-")[0]
    size = len(string_chon)
    while idx < size:
        atom = string_chon[idx]
        n_atom = ""
        idx += 1
        while idx < size and string_chon[idx] not in ATOMIC_MASS:
            n_atom += string_chon[idx]
            idx += 1
        if n_atom == "":
            n_atom = "1."
        atoms[atom] = float(n_atom)

    for atom in ATOMIC_MASS:
        if atom not in atoms:
            atoms[atom] = 0.0

    return atoms

class MixtureState:
    r"""\
    *Class managing mixture state*

    ::
              __ Stream 2
             /
        ----/---------------------
         -- m_ox --->
        -----------|
        -----------|
         -- m_fuel ->
        ---\----------------------
            \_ Stream 1

    :Attributes:

        - **_stream_dict** - Dict['O2', 'N2', ...] of dict['stream', 'mass_frac']
        - **_species** - List of SpeciesState object
        - **_mixture_fraction** - Mixture fraction of the mixture based on Bilger's
        - **_far** - Fuel Air Ratio of the mixture
        - **_far_st** - Stoechiometric Fuel Air Ratio of the mixture
        - **_phi** - Equivalence ratio of the mixture
    """

    def __init__(self, species_dict, fuel, stream_update=None, convert_sp=None, species_database:str=None):
        """Initialize MixtureState

        :param species_dict: dict of species mass fractions
            all KEYS must be CHON compositions
            accepted : O2, H2O, CH4, C12.34H21.07I68

        :param fuel: string, key of the fuel in species_dict

        :stream_update: - Dict['O2', 'N2', ...] of dict['stream', 'mass_frac']
            e.g.
            {
                "O2": {"stream": 2, "mass_frac": 0.2},
                "N2": {"stream": 2, "mass_frac": 0.7},
                "CH4": {"stream": 2, "mass_frac": 0.1},
                "O2": {"stream": 1, "mass_frac": 0.0},
                "N2": {"stream": 1, "mass_frac": 0.0},
                "CH4": {"stream": 1, "mass_frac": 1.0},
            }

        :param convert_sp: optional list of tuples , translates keys if needed


        Example of call:

        MixtureState(
            {O2: ..., N2: ..., KERO: ...},
            "KERO",
            convert_sp=(("KERO", "C10.45678H20.45678),)
        )


        """

        if stream_update is None:
            stream_update = {}

        if convert_sp is not None:
            for convert in convert_sp:
                species_dict[convert[1]] = species_dict[convert[0]]
                del species_dict[convert[0]]
                if convert[0] == fuel:
                    fuel = convert[1]
            

        self._stream_dict = {
            "O2": {"stream": 2, "mass_frac": 0.2331},
            "N2": {"stream": 2, "mass_frac": 0.7669},
            fuel: {"stream": 1, "mass_frac": 1.0},
        }

        self._species = self._instanciate_species_atomic(species_dict, species_database=species_database)
        self._fuel = self.species_by_name(fuel)
        self._check_mass_fraction()

        self._update_streams(stream_update)

        self._mixture_fraction = self._compute_mixture_fraction()
        self._far = self._compute_far()
        self._far_st = self._compute_far_st()
        self._phi = self._compute_equivalence_ratio()

    @property
    def species(self):
        """return list of SpeciesState object"""
        return self._species

    @property
    def species_name(self):
        """Return list of species names"""
        return [species.name for species in self._species]

    @property
    def mixture_fraction(self):
        """Return mixture fraction"""
        return self._mixture_fraction

    @property
    def far(self):
        """return Fuel Air Ratio"""
        return self._far

    @property
    def afr(self):
        """return Air Fuel Ratio"""
        return 1 / self._far

    @property
    def far_st(self):
        """return stoechiometric Fuel Air Ratio"""
        return self._far_st

    @property
    def equivalence_ratio(self):
        """returns equivalence ratio"""
        return self._phi

    def _instanciate_species_atomic(self, species_dict, species_database:str=None):
        # pylint: disable=no-self-use
        """
        *Instanciate SpeciesState object for each species of the mixture*

        :param species_dict: Dict['O2', 'N2', ..] of species mass fraction
        :param fuel: Fuel name
        :type fuel: str

        :returns: List of SpeciesState object
        """
        species_list = []
        for species, mass_fraction in species_dict.items():
            species_list.append(SpeciesState(species, mass_fraction, species_database=species_database))
        return species_list

    def _update_streams(self, stream_update):
        """
        *Update stream data for mixture's species*

        :param stream_update: Dict['O2', 'N2', ...] of dict['stream', 'mass_frac']
        """
        self._stream_dict.update(stream_update)

        for species, stream_data in self._stream_dict.items():
            self.species_by_name(species).set_stream_data(
                stream_data["stream"], stream_data["mass_frac"]
            )

    def species_by_name(self, name):
        """
        *Gets SpeciesState by name*

        :param name: Name of the species
        :type name: str

        :returns: SpeciesState object matching with name
        """
        try:
            idx = self.species_name.index(name)
        except ValueError:
            msg = "Species name '" + name + "' does not match with any species :"
            msg += "\n - "
            msg += "\n - ".join(self.species_name)
            raise NameError(msg)
        return self._species[idx]

    def _check_mass_fraction(self):
        """ """
        mass_fraction = 0.0
        for species in self._species:
            mass_fraction += species.mass_fraction()
        if not np.allclose(mass_fraction, 1.0, atol=1e-4):
            non_unit = np.where(np.abs(mass_fraction - 1.0) > 1e-4)[0]
            msg = "Sum of mass fractions is not unit in "
            msg += f"{len(non_unit)} / {len(mass_fraction)} of solutions.\n"
            raise RuntimeError(msg)

    def elem_mass_frac(self, atom, stream=None):
        """
        *Compute elemental mass fraction of atom j in mixture*

        For each species i, get the elemental mass fraction of the atom j.

                           a_i,j * M_j * Y_i
            Y_j = sum_i (---------------------)
                                  M_i
        with :

            - **a_i,j** : Number of atom j in species i
            - **M_j** : Molar mass of atom j
            - **M_i** : Molar mass of species i
            - **Y_i** : Mass fraction of species i

        If stream is not None, the mass_fraction is defined as the mass_fraction of \
        the species i in a the stream s :

            - s = 1 : Fuel stream
            - s = 2 : Oxydizer stream

                            a_i,j * M_j * Y_i,s
            Y_j,s = sum_i (---------------------)
                                   M_i
        with :

            - **Y_i,s** : Mass fraction of species i in stream s
        """

        el_mass_frac = 0.0
        for species in self._species:
            el_mass_frac += np.divide(
                species.atoms[atom] * ATOMIC_MASS[atom] * species.mass_fraction(stream),
                species.molar_mass,
            )

        return el_mass_frac

    def _compute_mixture_fraction(self):
        # pylint: disable=invalid-name
        """
        *Compute mixture fraction of the mixture*

        The mixture fraction Z defined by Bilger as :

              Y_C  / m.M_C  + Y_H  / n.M_H + (Y_O,2 - Y_O) / nu_O2.M_O
        Z = -----------------------------------------------------------
             Y_C,1 / m.M_C + Y_H,1 / n.M_H   +    Y_O,2    / nu_O2.M_O

        with :

            - **Y_j** : Elemental mass fraction of element j
            - **Y_j,s** : Elemental mass fraction of element j in stream s
            - **m, n** : Respectively number of carbon and hydrogen atoms in fuel
            - **M_j** : Molar mass of element j
            - **nu_O2** : Number of moles of O2
        """
        nu_o2 = np.add(self._fuel.atoms["C"], self._fuel.atoms["H"] / 4)

        num_C = np.divide(
            self.elem_mass_frac("C"), self._fuel.atoms["C"] * ATOMIC_MASS["C"]
        )
        num_H = np.divide(
            self.elem_mass_frac("H"), self._fuel.atoms["H"] * ATOMIC_MASS["H"]
        )
        num_O = np.divide(
            self.elem_mass_frac("O", 2) - self.elem_mass_frac("O"),
            nu_o2 * ATOMIC_MASS["O"],
        )
        num = num_C + num_H + num_O

        den_C = np.divide(
            self.elem_mass_frac("C", 1), self._fuel.atoms["C"] * ATOMIC_MASS["C"]
        )
        den_H = np.divide(
            self.elem_mass_frac("H", 1), self._fuel.atoms["H"] * ATOMIC_MASS["H"]
        )
        den_O = np.divide(self.elem_mass_frac("O", 2), nu_o2 * ATOMIC_MASS["O"])
        den = den_C + den_H + den_O

        mixture_fraction = np.divide(num, den)

        return mixture_fraction

    def _compute_far(self):
        """
        *Compute FAR (Fuel Air Ratio) from mixture fraction*

        FAR = Z / (1 - Z)
        """

        far = np.divide(self.mixture_fraction, 1.0 - self.mixture_fraction)
        return far

    def _compute_far_st(self):
        """
        *Compute stoechiometric FAR from stoechiometric quantities*

                sum_j(s=1) m_j    Y_O2,2 * (m*M_C + n*M_H)
        FAR_s = --------------- = ------------------------
                sum_j(s=2) m_j        M_O2 * (m + n/4)
        """

        fuel_mass = 1.0 * self._fuel.molar_mass
        nu_o2 = np.add(self._fuel.atoms["C"], self._fuel.atoms["H"] / 4)

        far_st = np.divide(
            self.species_by_name("O2").mass_fraction(2) * fuel_mass,
            self.species_by_name("O2").molar_mass * nu_o2,
        )

        return far_st

    def _compute_equivalence_ratio(self):
        """
        *Compute equivalence ratio phi*

        phi = FAR / FAR_st
        """

        return np.divide(self.far, self.far_st)
