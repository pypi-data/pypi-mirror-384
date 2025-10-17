import importlib
from functools import cached_property

class AtomPositionMaker:
    """
    Lazily builds and manipulates molecular structures (mono-, di-, and triatomic).

    Attributes are computed on first access to minimize initial import overhead.
    """

    def __init__(self, file_location: str = None, name: str = None, **kwargs):
        self.file_location = file_location
        self.name = name
        # other attributes (e.g. atomPositions, mass_list) will be set when building

    # --- periodic data & helpers ---
    @cached_property
    def _covalent_radius(self):
        # Å | minimal but broad enough; fallback = 0.77
        return {
            'H':0.31,'B':0.85,'C':0.76,'N':0.71,'O':0.66,'F':0.57,
            'Si':1.11,'P':1.07,'S':1.05,'Cl':1.02,'Br':1.20,'I':1.39,
            'Na':1.66,'K':2.03,'Li':1.28,'Cu':1.32,'Ni':1.24
        }

    @cached_property
    def _empirical_diatomic_lengths(self):
        # Gas-phase bond lengths in Å (approx); covers your presets + a few more.
        return {
            ('H','H'):0.74, ('O','O'):1.21, ('N','N'):1.10,
            ('F','F'):1.42, ('Cl','Cl'):1.99, ('Br','Br'):2.28, ('I','I'):2.66,
            ('H','F'):0.92, ('H','Cl'):1.27, ('H','Br'):1.41, ('H','I'):1.61,
            ('O','H'):0.97, ('S','H'):1.34,
            ('C','O'):1.13, ('N','O'):1.15, ('C','N'):1.17, ('B','O'):1.21,
            ('Si','O'):1.52, ('Cu','O'):1.82, ('C','S'):1.54
        }

    def _norm_sym(self, s: str) -> str:
        s = s.strip()
        if not s: return s
        return s[0].upper() + s[1:].lower()

    def _is_element(self, s: str) -> bool:
        import math, re
        return bool(re.fullmatch(r'[A-Z][a-z]?', self._norm_sym(s)))

    def _default_bond_length(self, A: str, B: str) -> float:
        """Empirical length if known, else scaled sum of covalent radii."""
        A, B = self._norm_sym(A), self._norm_sym(B)
        key = tuple(sorted((A, B)))
        if key in self._empirical_diatomic_lengths:
            return self._empirical_diatomic_lengths[key]
        ra = self._covalent_radius.get(A, 0.77)
        rb = self._covalent_radius.get(B, 0.77)
        # single-bond-ish scale; works fine as a neutral fallback
        return 1.20 * (ra + rb)

    def _parse_diatomic_formula(self, name: str):
        """
        Accepts 'CO', 'NaCl', 'Cl2', 'H2' etc. Returns (A, B) or None if total atoms != 2.
        """
        import math, re
        tokens = re.findall(r'([A-Z][a-z]?)(\d*)', name)
        if not tokens:
            return None
        expanded = []
        for sym, cnt in tokens:
            n = int(cnt) if cnt else 1
            expanded.extend([self._norm_sym(sym)] * n)
        if len(expanded) != 2:
            return None
        return expanded[0], expanded[1]

    # --- public builders (no external deps) ---
    def build_mono(self, symbol_or_Z: str, center: str = 'mass_center'):
        """Monoatomic: symbol ('Ni') or atomic number ('28')."""
        sym = None
        if isinstance(symbol_or_Z, str) and symbol_or_Z.isdigit():
            # If you keep a periodic table map elsewhere, plug it here; otherwise best-effort:
            Z2sym = {
                1:'H',6:'C',7:'N',8:'O',9:'F',14:'Si',15:'P',16:'S',17:'Cl',
                29:'Cu',28:'Ni',35:'Br',53:'I',11:'Na',19:'K',5:'B'
            }
            sym = Z2sym.get(int(symbol_or_Z))
        else:
            sym = self._norm_sym(str(symbol_or_Z))
        if not sym or not self._is_element(sym):
            raise ValueError(f"Unrecognized element: {symbol_or_Z}")
        self.build_molecule([sym], [[0.0, 0.0, 0.0]], center=center)

    def build_diatomic(self, A: str, B: str, center: str = 'mass_center'):
        """Diatomic: place along z with reasonable bond length."""
        A, B = self._norm_sym(A), self._norm_sym(B)
        if not (self._is_element(A) and self._is_element(B)):
            raise ValueError(f"Unrecognized diatomic: {A}-{B}")
        d = self._default_bond_length(A, B)
        self.build_molecule([A, B], [[0.0, 0.0, 0.0], [0.0, 0.0, d]], center=center)

    @cached_property
    def atomic_compounds(self):
        # Single-atom entries; uses self.atomic_numbers if defined
        nums = getattr(self, 'atomic_numbers', [])
        return {str(a): {'atomLabels': [str(a)], 'atomPositions': [[0, 0, 0]]} for a in nums}

    @cached_property
    def diatomic_compounds(self):
        return {
            'H2':  {'atomLabels': ['H', 'H'],   'atomPositions': [[0, 0, 0], [0, 0, 0.74]]},  
            'O2':  {'atomLabels': ['O', 'O'],   'atomPositions': [[0, 0, 0], [0, 0, 1.21]]},  
            'OH':  {'atomLabels': ['O', 'H'],   'atomPositions': [[0, 0, 0], [0, 0, 0.97]]},  
            'N2':  {'atomLabels': ['N', 'N'],   'atomPositions': [[0, 0, 0], [0, 0, 1.10]]},  
            'F2':  {'atomLabels': ['F', 'F'],   'atomPositions': [[0, 0, 0], [0, 0, 1.42]]},  
            'Cl2': {'atomLabels': ['Cl', 'Cl'], 'atomPositions': [[0, 0, 0], [0, 0, 1.99]]},  
            'Br2': {'atomLabels': ['Br', 'Br'], 'atomPositions': [[0, 0, 0], [0, 0, 2.28]]},  
            'I2':  {'atomLabels': ['I', 'I'],   'atomPositions': [[0, 0, 0], [0, 0, 2.66]]},  
            'HF':  {'atomLabels': ['H', 'F'],   'atomPositions': [[0, 0, 0], [0, 0, 0.92]]},  
            'CO':  {'atomLabels': ['C', 'O'],   'atomPositions': [[0, 0, 0], [0, 0, 1.13]]},  
            'NO':  {'atomLabels': ['N', 'O'],   'atomPositions': [[0, 0, 0], [0, 0, 1.15]]},  
            'CN':  {'atomLabels': ['C', 'N'],   'atomPositions': [[0, 0, 0], [0, 0, 1.17]]},  
            'BO':  {'atomLabels': ['B', 'O'],   'atomPositions': [[0, 0, 0], [0, 0, 1.21]]},  
            'SiO': {'atomLabels': ['Si', 'O'],  'atomPositions': [[0, 0, 0], [0, 0, 1.52]]},  
            'CuO': {'atomLabels': ['Cu', 'O'],  'atomPositions': [[0, 0, 0], [0, 0, 1.82]]},   
            'SH':  {'atomLabels': ['S', 'H'],   'atomPositions': [[0, 0, 0], [0, 0, 1.02]]},   
            'HCl': {'atomLabels': ['H','Cl'], 'atomPositions': [[0,0,0], [0,0,1.27]]},
            'HBr': {'atomLabels': ['H','Br'], 'atomPositions': [[0,0,0], [0,0,1.41]]},
            'HI':  {'atomLabels': ['H','I'],  'atomPositions': [[0,0,0], [0,0,1.61]]},
            'CS':  {'atomLabels': ['C','S'],  'atomPositions': [[0,0,0], [0,0,1.54]]},
        }

    @cached_property
    def triatomic_compounds(self):
        # lazy import numpy only when needed
        np = importlib.import_module('numpy')
        to_rad = np.radians
        return {
            'CO2': {'atomLabels': ['C', 'O', 'O'], 'atomPositions': [[0, 0, 0], [0, 0, 1.16], [0, 0, -1.16]]},
            'H2O': {'atomLabels': ['O', 'H', 'H'], 'atomPositions': [
                [0, 0, 0], 
                [0.96 * np.cos(np.radians(104.5 / 2)), 0, 0.96 * np.sin(np.radians(104.5 / 2))], 
                [0.96 * np.cos(np.radians(104.5 / 2)), 0, -0.96 * np.sin(np.radians(104.5 / 2))]]},
            'SO2': {'atomLabels': ['S', 'O', 'O'], 'atomPositions': [
                [0, 0, 0], 
                [1.43 * np.cos(np.radians(119.5)), 0, 1.43 * np.sin(np.radians(119.5))], 
                [-1.43 * np.cos(np.radians(119.5)), 0, -1.43 * np.sin(np.radians(119.5))]]},  
            'O3':  {'atomLabels': ['O', 'O', 'O'], 'atomPositions': [
                [0, 0, 0], 
                [1.28 * np.cos(np.radians(116.8)), 0, 1.28 * np.sin(np.radians(116.8))], 
                [-1.28 * np.cos(np.radians(116.8)), 0, -1.28 * np.sin(np.radians(116.8))]]},
            'HCN': {'atomLabels': ['H', 'C', 'N'], 'atomPositions': [[0, 0, 1.06], [0, 0, 0], [0, 0, -1.16]]},
            'H2S': {'atomLabels': ['S', 'H', 'H'], 'atomPositions': [
                [0, 0, 0], 
                [0.96 * np.cos(np.radians(92.1 / 2)), 0, 0.96 * np.sin(np.radians(92.1 / 2))], 
                [0.96 * np.cos(np.radians(92.1 / 2)), 0, -0.96 * np.sin(np.radians(92.1 / 2))]]},  
            'CS2': {'atomLabels': ['C', 'S', 'S'], 'atomPositions': [[0, 0, 0], [0, 0, 1.55], [0, 0, -1.55]]},  
            'NO2': {'atomLabels': ['N', 'O', 'O'], 'atomPositions': [
                [0, 0, 0], 
                [1.20 * np.cos(np.radians(134.1)), 0, 1.20 * np.sin(np.radians(134.1))], 
                [-1.20 * np.cos(np.radians(134.1)), 0, -1.20 * np.sin(np.radians(134.1))]]},  
            'HCO': {'atomLabels': ['H', 'C', 'O'], 'atomPositions': [[0, 0, 1.10], [0, 0, 0], [0, 0, -1.12]]}, 
            'HOF': {'atomLabels': ['H', 'O', 'F'], 'atomPositions': [[0, 0, 1.10], [0, 0, 0], [0, 0, -1.44]]}, 
            'C2H2': {'atomLabels': ['C', 'C', 'H', 'H'], 'atomPositions': [[0, 0, 0], [1.20, 0, 0], [0, 0, 1.08], [1.20, 0, -1.08]]}  
        }

    def get_triatomic_compound(self, name: str):
        return self.triatomic_compounds.get(name)

    def build_molecule(self, atomLabels: list, atomPositions, center: str = 'mass_center'):
        # add atoms, compute mass_list etc before centering
        for label, pos in zip(atomLabels, atomPositions):
            self.add_atom(label, pos, [1, 1, 1])

        if center in ('mass_center', 'gravity_center'):
            disp = (self.atomPositions.T * self.mass_list).sum(axis=1) / self.mass_list.sum()
        elif center in ('geometric_center', 'baricenter'):
            disp = self.atomPositions.mean(axis=1)
        else:
            disp = [0, 0, 0]

        self.set_atomPositions(self.atomPositions - disp)

    def build(self, name: str, center: str = 'mass_center'):
        if name in self.atomic_compounds:
            labels = self.atomic_compounds[name]['atomLabels']
            pos = self.atomic_compounds[name]['atomPositions']
        elif name in self.diatomic_compounds:
            labels = self.diatomic_compounds[name]['atomLabels']
            pos = self.diatomic_compounds[name]['atomPositions']
        elif name in self.triatomic_compounds:
            labels = self.triatomic_compounds[name]['atomLabels']
            pos = self.triatomic_compounds[name]['atomPositions']
        else:
            raise ValueError(f"Unknown molecule '{name}'")

        self.build_molecule(labels, pos, center)

    def build(self, name: str, center: str = 'mass_center'):
        # 1) your cached dictionaries (unchanged priority)
        if name in self.atomic_compounds:
            labels = self.atomic_compounds[name]['atomLabels']
            pos = self.atomic_compounds[name]['atomPositions']
            self.build_molecule(labels, pos, center)
            return

        if name in self.diatomic_compounds:
            labels = self.diatomic_compounds[name]['atomLabels']
            pos = self.diatomic_compounds[name]['atomPositions']
            self.build_molecule(labels, pos, center)
            return

        if name in self.triatomic_compounds:
            labels = self.triatomic_compounds[name]['atomLabels']
            pos = self.triatomic_compounds[name]['atomPositions']
            self.build_molecule(labels, pos, center)
            return

        # 2) monoatomic fallback: element symbol or atomic number
        if self._is_element(name) or name.isdigit():
            self.build_mono(name, center=center)
            return

        # 3) diatomic fallback: parse "XY" / "X2" style names
        pair = self._parse_diatomic_formula(name)
        if pair is not None:
            A, B = pair
            self.build_diatomic(A, B, center=center)
            return

        # 4) otherwise: unknown
        raise ValueError(f"Unknown molecule '{name}'")



