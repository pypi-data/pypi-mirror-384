try:
    import numpy as np
except ImportError as e:
    import sys
    sys.stderr.write(f"An error occurred while importing numpy: {str(e)}\n")
    del sys

try:
    import re
except ImportError as e:
    import sys
    sys.stderr.write(f"An error occurred while importing re: {str(e)}\n")
    del sys

@staticmethod
def read_file(file_location:str=None, strip=True):

    if file_location is None:
        raise ValueError("(!) File location is not set.")
    
    try:
        with open(file_location, 'r') as file:
            if strip:
                for line in file:
                    yield line.strip()  # strip() elimina espacios y saltos de línea al principio y al final
            else:
                for line in file:
                    yield line  # strip() elimina espacios y saltos de línea al principio y al final
    except FileNotFoundError:
        raise FileNotFoundError(f"(!) File not found at {file_location}")
    except IOError:
        raise IOError(f"(!) Error reading file at {file_location}")
    except Exception as e:
        print(f"Error inesperado: {e}")

@staticmethod
def is_number(s):
    if s is None:
        return False
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False

class POSCAR:
    def __init__(self, file_location:str=None, name:str=None, **kwargs):
        self._atomCountByType = None

    @property
    def atomCountByType(self):
        return self._atomCountByType

    @atomCountByType.setter
    def atomCountByType(self, value):
        """Allow external or internal code to overwrite the cached counts."""
        self._atomCountByType = np.asarray(value, dtype=int)

    def group_elements_and_positions(self, atomLabelsList:list=None, atomPositions:list=None, regroup=False):
        atomLabelsList = atomLabelsList if atomLabelsList is not None else self.atomLabelsList
        atomPositions = atomPositions if atomPositions is not None else self.atomPositions

        if regroup:
            element_indices = {}
            for i, label in enumerate(atomLabelsList):
                if label not in element_indices:
                    element_indices[label] = []
                element_indices[label].append(i)

            atomLabelsList_new = []
            atomPositions_new = []
            uniqueAtomLabels_new = list(element_indices.keys())  # preserve order
            for label in uniqueAtomLabels_new:
                atomLabelsList_new.extend([label] * len(element_indices[label]))
                atomPositions_new.extend(atomPositions[element_indices[label]])

            self.atomLabelsList = np.array(atomLabelsList_new, dtype=object)
            self.atomPositions = np.array(atomPositions_new)
            self.uniqueAtomLabels = uniqueAtomLabels_new
        else:
            self.atomLabelsList = np.array(atomLabelsList, dtype=object)
            self.atomPositions = np.array(atomPositions)
            self.uniqueAtomLabels = list(dict.fromkeys(atomLabelsList))  # keep first appearance order

        unique_labels, count = np.unique(self.atomLabelsList, return_counts=True)
        self.atomCountByType = count

        return True


    def export_as_POSCAR(self, file_location:str=None, v:bool=False) -> bool:
        file_location  = file_location  if not file_location  is None else self.file_location+'POSCAR' if self.file_location is str else self.file_location

        self.group_elements_and_positions(regroup=True)

        with open(file_location, 'w') as file:
            # Comentario inicial
            file.write(f'POSCAR : JML code \n')

            # Factor de escala
            file.write(f"{' '.join(map(str, self.scaleFactor))}\n")

            # Vectores de la celda unitaria
            for lv in self.latticeVectors:
                file.write('{:>18.15f}\t{:>18.15f}\t{:>18.15f}\n'.format(*lv))

            # Tipos de átomos y sus números
            file.write('    '.join(self.uniqueAtomLabels) + '\n')
            file.write('    '.join(map(str, self.atomCountByType)) + '\n')

            # Opción para dinámica selectiva (opcional)
            if self.selectiveDynamics:     file.write('Selective dynamics\n')
            # Tipo de coordenadas (Direct o Cartesian)
            aCT = 'Cartesian' if self.atomCoordinateType[0].capitalize() in ['C', 'K'] else 'Direct'
            file.write(f'{aCT}\n')

            # Coordenadas atómicas y sus restricciones
            for i, atom in enumerate(self.atomPositions if self.atomCoordinateType[0].capitalize() in ['C', 'K'] else self.atomPositions_fractional):
                coords = '\t'.join(['{:>18.15f}'.format(n) for n in atom])
                constr = '\t'.join(['T' if n else 'F' for n in self.atomicConstraints[i]]) if self.selectiveDynamics else ''
                file.write(f'\t{coords}\t{constr}\n')

            # Comentario final (    opcional)
            file.write('Comment_line\n')
            if hasattr(self, 'dynamical_eigenvector_diff') and not self.dynamical_eigenvector_diff is None: 
                for i, atom in enumerate(self.dynamical_eigenvector_diff if self.atomCoordinateType[0].capitalize() in ['C', 'K'] else self.dynamical_eigenvector_diff_fractional):
                    coords = '\t'.join(['{:>18.15f}'.format(n) for n in atom])
                    file.write(f'\t{coords}\n')
                
    def read_POSCAR(self, file_location:str=None):
        file_location = file_location if type(file_location) == str else self.file_location
        lines = [n for n in read_file(file_location) ]
        
        self.comment = lines[0].strip()
        self.scaleFactor = list(map(float, lines[1].strip().split()))
        
        # Reading lattice vectors
        self.latticeVectors = np.array([list(map(float, line.strip().split())) for line in lines[2:5]])
        
        # Species names (optional)
        if is_number(lines[5].strip().split()[0]):
            self.uniqueAtomLabels = None
            offset = 0
        else:
            self.uniqueAtomLabels = lines[5].strip().split()
            offset = 1
  
        # Ions per species
        self.atomCountByType = np.array(list(map(int, lines[5+offset].strip().split())))
        
        # Selective dynamics (optional)
        if not is_number(lines[6+offset].strip()[0]):
            if lines[6+offset].strip()[0].capitalize() == 'S':
                self.selectiveDynamics = True
                offset += 1
            else:
                self.selectiveDynamics = False
        
        # atomic coordinated system
        if lines[6+offset].strip()[0].capitalize() in ['C', 'K']:
            self.atomCoordinateType = 'cartesian'
        else:
            self.atomCoordinateType = 'direct'

        # Ion positions
        self.atomCount = np.array(sum(self.atomCountByType))
        if self.atomCoordinateType == 'cartesian':
            self.atomPositions = np.array([list(map(float, line.strip().split()[:3])) for line in lines[7+offset:7+offset+self.atomCount]])
        else:
            self.atomPositions_fractional = np.array([list(map(float, line.strip().split()[:3])) for line in lines[7+offset:7+offset+self.atomCount]])

        self.atomicConstraints = (np.array([list(map(str, line.strip().split()[3:])) for line in lines[7+offset:7+offset+self.atomCount]]) == 'T').astype(int) if self.selectiveDynamics else None
        # Check for lattice velocities
        # Check for ion velocities

    def read_CONTCAR(self, file_location:str=None):
        self.read_POSCAR(file_location)

