class ASE:
    """
    ASE class inherits from Atoms and FileManager, facilitating operations related
    to atomic structures and file management.
    """

    def __init__(self, name:str=None, file_location:str=None ):    
        """
        Initialize the ASE class by initializing parent classes.
        :param name: Name of the file.
        :param file_location: Location of the file.
        """
        #FileManager.__init__(self, name=name, file_location=file_location)
        # Initialize Atoms with default values, including PBC
        #Atoms.__init__(self, pbc=np.array([True, True, True]))
        pass
    def export_as_ASE(self, file_location:str=None, verbose:bool=False) -> bool:
        """
        Exports the ASE object to a specified file location.
        :param file_location: The file path to save the object.
        :param verbose: If True, enables verbose output.
        :return: Boolean indicating successful export.
        """
        try:
            import pickle
        except ImportError as e:
            import sys
            sys.stderr.write(f"An error occurred while importing pickle: {str(e)}\n")
            del sys

        file_location = file_location if file_location is not None else 'ASE.obj'

        try:
            with open(file_location, 'wb') as file:
                pickle.dump(self, file)
            return True
        except Exception as e:
            if verbose:
                print(f"Error exporting ASE object: {e}")
            return False

    def read_ASE(self, file_location:str=None, ase_atoms:object=None, **kwargs):
        """
        Reads an ASE object either from an existing Atoms object or from a file.
        :param ase_atoms: An existing Atoms object.
        :param file_location: The file path to read the object from.
        :return: Boolean indicating successful read.
        """
        if ase_atoms is not None:
            self.ASE_2_SAGE(ase_atoms=ase_atoms)
            return True

        elif file_location is not None: 
            from ase.io import read
            self = read(file_path)
            self.ASE_2_SAGE(ase_atoms=ase_atoms)
            return True

        return False

    def ASE_2_SAGE(self, ase_atoms:object=None):
        """
        Transforms an ASE Atoms object to the SAGE internal representation.
        :param ase_atoms: An ASE Atoms object.
        """

        import numpy as np

        # --- Basic configuration ---
        try:
            self._atomCount = len(ase_atoms)
        except Exception:
            self._atomCount = 0

        try:
            symbols = ase_atoms.get_chemical_symbols()
            self._atomLabelsList = symbols
            self._uniqueAtomLabels = list(set(symbols))
            self._atomCountByType = [symbols.count(x) for x in self._uniqueAtomLabels]
        except Exception:
            self._atomLabelsList = []
            self._uniqueAtomLabels = []
            self._atomCountByType = []

        try:
            self._atomPositions = ase_atoms.get_positions()
        except Exception:
            self._atomPositions = None

        try:
            self._latticeVectors = ase_atoms.get_cell()
        except Exception:
            self._latticeVectors = None

        try:
            self._cellVolumen = ase_atoms.get_volume()
        except Exception:
            self._cellVolumen = None

        try:
            self._pbc = ase_atoms.get_pbc()
        except Exception:
            self._pbc = None

        self._atomCoordinateType = 'Cartesian'

        # --- Constraints ---
        try:
            if getattr(ase_atoms, "constraints", None):
                idx = np.asarray(ase_atoms.constraints[0].get_indices(), dtype=np.intp)
                self._atomicConstraints = np.isin(np.arange(len(ase_atoms), dtype=np.intp), idx)
            else:
                self._atomicConstraints = None
        except Exception:
            self._atomicConstraints = None

        # --- Energies ---
        try:
            self._E = ase_atoms.get_total_energy() 
        except (AttributeError, RuntimeError):
            self._E = None  # O algún valor predeterminado si es más apropiado

        try:
            self._K = ase_atoms.get_kinetic_energy()
        except (AttributeError, RuntimeError):
            self._K = None

        if self._E is not None and self._K is not None:
            self._U = self._E - self._K
        else:
            self._U = None  # O algún valor predeterminado
            
        # --- Forces ---
        try:
            if "forces" in getattr(ase_atoms, "arrays", {}):
                self._total_force = np.sum(ase_atoms.get_forces(), axis=0)
            else:
                self._total_force = None

        except Exception:
            self._total_force = None