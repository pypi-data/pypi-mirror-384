import math
import itertools
import logging
import importlib.resources
import itertools

import numpy as np
import pandas as pd
import networkx as nx
from networkx.readwrite import json_graph

import copy
import json
import altair as alt

from collections import deque, defaultdict
from dataclasses import dataclass, asdict
from typing import Self, Iterator
from types import SimpleNamespace

from rdkit import Chem

from rdworks import Mol
from rdworks.tautomerism import ComprehensiveTautomers, RdkTautomers


logger = logging.getLogger(__name__)

ln10 = math.log(10)

# adapted from https://github.com/dptech-corp/Uni-pKa/enumerator
smarts_path = importlib.resources.files('rdworks.predefined.ionized')
AcidBasePatterns = pd.read_csv(smarts_path / 'smarts_pattern.csv')
AcidBasePatternsSimple = pd.read_csv(smarts_path / 'simple_smarts_pattern.csv')
UnreasonablePatterns = list(map(Chem.MolFromSmarts, [
    "[#6X5]",
    "[#7X5]",
    "[#8X4]",
    "[*r]=[*r]=[*r]",
    "[#1]-[*+1]~[*-1]",
    "[#1]-[*+1]=,:[*]-,:[*-1]",
    "[#1]-[*+1]-,:[*]=,:[*-1]",
    "[*+2]",
    "[*-2]",
    "[#1]-[#8+1].[#8-1,#7-1,#6-1]",
    "[#1]-[#7+1,#8+1].[#7-1,#6-1]",
    "[#1]-[#8+1].[#8-1,#6-1]",
    "[#1]-[#7+1].[#8-1]-[C](-[C,#1])(-[C,#1])",
    # "[#6;!$([#6]-,:[*]=,:[*]);!$([#6]-,:[#7,#8,#16])]=[C](-[O,N,S]-[#1])",
    # "[#6]-,=[C](-[O,N,S])(-[O,N,S]-[#1])",
    "[OX1]=[C]-[OH2+1]",
    "[NX1,NX2H1,NX3H2]=[C]-[O]-[H]",
    "[#6-1]=[*]-[*]",
    "[cX2-1]",
    "[N+1](=O)-[O]-[H]"
]))



def beta_constant(T: float = 278.15) -> float:
    """Returns the beta constant in Kcal/mol unit at a given temperature (Kelvin).

    The constant \\( \\beta \\) is defined as:
    
    \\[
    \\beta = \\frac{1}{ k_{B} T }
    \\]
    
    
    where \\( k_{B} \\) is the Boltzmann constant and 
    T is the absolute temperature of the system in Kelvin.
    
    \\( k_{B} \\) = 1.987204259e-3 Kcal/(mol K)
    
    For example, \\( \\beta \\) = 0.5527408646408499 Kcal/(mol K) at 278.15 K

    Args:
        T (float) : temperature in Kelvin unit.
    """
    return 1.987204259e-3 * T


def Boltzmann_weights(energies: list[float] | np.ndarray, beta: float=1.0) -> np.ndarray:
    """Returns the Boltzmann weights of energies.

    The Boltzmann weight, \\( p_{i} \\) is defined as:
    
    \\[
    p_{i} = \\frac{exp(- \\beta E_{i}) }{ \\sum_{i} exp(- \\beta E_{i})}
    \\]
        

    Since the Boltzmann weighted average of any property is taken at a specific temperature, 
    changing the temperature means changing the value of \\( \\beta \\).

    Args:
        energies (list[float] | np.ndarray) : energies
        beta (float) : \\( \\beta = \\frac{1}{ k_{B} T } \\) (Kcal/mol)

    Returns:s
        np.ndarray

    """
    if isinstance(energies, list) and isinstance(energies[0], float):
        energies = np.array(energies)    
    elif isinstance(energies, np.ndarray):
        pass
    else:
        raise TypeError
    relative_energies = energies - np.min(energies)
    boltzmann_factors = np.exp(-beta * relative_energies)
    # Partition function, Z
    Z = np.sum(boltzmann_factors)

    return boltzmann_factors / Z


def Boltzmann_weighted_average(energies: list[float] | np.ndarray, beta: float=1.0) -> float:
    """Returns the Boltzmann weighted average of energies.
        \\[
            E_{avg} = \\frac{\\sum_{i} E_{i} exp(-\\beta E_{i})}{\\sum_{i} exp(-\\beta E_{i})}
        \\]
        
    Args:
        energies (list[float] | np.ndarray) : energies
        beta (float) : \\( \\beta = \\frac{1}{k_{B}T} \\) (Kcal/mol)

    Returns:
        float
    """
    if isinstance(energies, list) and isinstance(energies[0], float):
        energies = np.array(energies)    
    elif isinstance(energies, np.ndarray):
        pass
    else:
        raise TypeError
    relative_energies = energies - np.min(energies)
    boltzmann_factors = np.exp(-beta * relative_energies)
    Z = np.sum(boltzmann_factors)
    weights = boltzmann_factors / Z

    return float(np.dot(weights, energies))


@dataclass
class IonizableSite:
    """(de)protonation site information"""
    atom_idx: int
    atom: str
    hs: int # number of H attached to the atom
    q: int # formal charge of the atom
    pr: bool  # can be protonated?
    de: bool  # can be deprotonated?
    name: str # site name
    acid_base: str
    

class State:
    def __init__(self, 
                 smiles: str | None = None,
                 origin: str | None = None, 
                 transformation: str | None = None,
                 min_formal_charge: int = -2,
                 max_formal_charge: int = +2,
                 min_atomic_charge: int = -1,
                 max_atomic_charge: int = +1,
                 protomer_rule: str = 'default',
                 tautomer_rule: str | None = None) -> None:
        """Molecular state.

        Args:
            smiles (str): SMILES
            origin (str | None, optional): original SMILES before tautomerization or ionization. Defaults to None.
            transformation (str | None, optional): Tautomer, +H, -H, or None. Defaults to None.
            min_formal_charge (int, optional): min formal charge. Defaults to -2.
            max_formal_charge (int, optional): max formal charge. Defaults to +2.
            min_atomic_charge (int, optional): min atomic charge. Defaults to -1.
            max_atomic_charge (int, optional): max atomic charge. Defaults to +1.
            protomer_rule (str, optional): 
                Ioniziation patterns ('default' or 'simple').
                Defaults to 'default'.
            tautomer_rule (str, optional): 
                Tautomerization patterns ('rdkit' or 'comprehensive'). 
                Defaults to None.
        """
        self.smiles = smiles
        self.origin = origin # parent or origin
        self.transformation = transformation  # how this state is generated from origin
        self.min_formal_charge = min_formal_charge
        self.max_formal_charge = max_formal_charge
        self.min_atomic_charge = min_atomic_charge
        self.max_atomic_charge = max_atomic_charge
        self.protomer_rule = protomer_rule
        self.tautomer_rule = tautomer_rule

        self.rdmol = None
        self.rdmolH = None
        self.sites = []
        self.charge = None
        self.energy = None
        self.update()


    def __str__(self) -> str:
        """String representation.

        Returns:
            str: short description of the state.
        """
        return f"State(smiles={self.smiles}, sites={self.sites}, transformation={self.transformation}, origin={self.origin})"


    def __eq__(self, other: Self) -> bool:
        """Operator `==`."""
        if isinstance(other, State):
            return self.smiles == other.smiles
        
        return False
    
    
    def copy(self) -> Self:
        return copy.deepcopy(self)


    def update(self) -> None:
        if isinstance(self.smiles, str) and len(self.smiles) > 0:
            self.rdmol = Chem.MolFromSmiles(self.smiles)
            self.rdmolH = Chem.AddHs(self.rdmol)
            self.find_ionizable_sites()
            self.charge = Chem.GetFormalCharge(self.rdmol)


    def info(self, index: int | None = None) -> None:
        if isinstance(index, int):
            serial = f'[{index:2}] '
        else:
            serial = ''
        print(f"{serial}SMILES: {self.smiles}")
        print(f"{serial}Origin: {self.origin}")
        print(f"{serial}Charge: {self.charge}")
        print(f"{serial}Energy: {self.energy}")
        print(f"{serial}Transformation: {self.transformation}")
        print(f"{serial}Ionizable sites:")
        
        for site in self.sites:
            print(f"{serial}    atom_idx= {site.atom_idx:2},", end=" ")
            print(f"atom= {site.atom:>2},", end=" ")
            print(f"q= {site.q:+2}, hs= {site.hs:1},", end=" ")
            print(f"pr= {site.pr:1}, de= {site.de:1},", end=" ")
            print(f"acid_base= {site.acid_base}, name= {site.name}")
        print()


    def hydrogen_count(self, idx: int) -> int:
        atom = self.rdmolH.GetAtomWithIdx(idx)
        hydrogen_count = 0
        if atom.GetAtomicNum() == 1:
            for bond in atom.GetNeighbors()[0].GetBonds():
                neighbor = bond.GetOtherAtom(atom)
                if neighbor.GetAtomicNum() == 1:
                    hydrogen_count += 1
        else:
            for bond in atom.GetBonds():
                neighbor = bond.GetOtherAtom(atom)
                if neighbor.GetAtomicNum() == 1:
                    hydrogen_count += 1
        return hydrogen_count
    

    def site_info(self) -> list[tuple]:
        return [(site.atom, site.atom_idx, site.q, site.pr, site.de) for site in self.sites]       


    def can_be_protonated_at(self, atom_idx:int) -> bool:
        """Check if an atom can potentially be protonated"""
        atom = self.rdmol.GetAtomWithIdx(atom_idx)
        # Check formal charge (negative charge can be protonated)
        if atom.GetFormalCharge() < 0:
            return True
        
        # Check for atoms with lone pairs (N, O, S, P, etc.)
        # that aren't already fully protonated
        atomic_num = atom.GetAtomicNum()
        total_valence = atom.GetTotalValence()
        
        # Common protonatable atoms
        if atomic_num == 7:  # N, O, S
            if total_valence < 4:  # Can form NH4+
                return True
        elif atomic_num in [8, 16]:  # O, S
            if total_valence < 3:  # Can form OH3+ or SH3+
                return True
        
        return False


    def can_be_deprotonated_at(self, atom_idx:int) -> bool:
        """Check if an atom can potentially be deprotonated"""
        atom = self.rdmol.GetAtomWithIdx(atom_idx)
        # Check if atom has a positive formal charge (can lose H+)
        if atom.GetFormalCharge() > 0:
            return True
        
        # Check if atom has hydrogens that can be removed
        if atom.GetTotalNumHs() == 0:
            return False
        
        # Common deprotonatable atoms with acidic hydrogens
        if atom.GetAtomicNum() in [7, 8, 15, 16]:  # N, O, P, S
            return True
        
        return False
    

    def find_ionizable_sites(self) -> None:
        if self.protomer_rule == 'simple':
            template = AcidBasePatternsSimple
        elif self.protomer_rule == 'default':
            template = AcidBasePatterns
        else:
            template = AcidBasePatterns
        for idx, name, smarts, index, acid_base in template.itertuples():
            pattern = Chem.MolFromSmarts(smarts)
            match = self.rdmolH.GetSubstructMatches(pattern)
            if len(match) == 0:
                continue
            else:
                index = int(index)
                for m in match:
                    atom_idx = m[index]
                    at = self.rdmol.GetAtomWithIdx(atom_idx)
                    atom = at.GetSymbol()
                    hs = self.hydrogen_count(atom_idx)
                    q = at.GetFormalCharge()
                    pr = self.can_be_protonated_at(atom_idx)
                    de = self.can_be_deprotonated_at(atom_idx)
                    site = IonizableSite(atom_idx=atom_idx, 
                                        atom=atom,
                                        hs=hs,
                                        q=q,
                                        name=name,
                                        acid_base=acid_base,
                                        pr=pr,
                                        de=de)
                    exist = False
                    for _ in self.sites:
                        if _.atom_idx == site.atom_idx:
                            exist = True
                            _.acid_base += f':{site.acid_base}'
                            _.name += f':{site.name}'
                    if not exist:
                        self.sites.append(site)
        self.sites = sorted(self.sites, key=lambda x: x.atom_idx)


    def ionize(self, idx: int, mode: str) -> None:
        rwmol = Chem.RWMol(self.rdmol)
        atom = rwmol.GetAtomWithIdx(idx)
        if mode == "a2b":
            if atom.GetAtomicNum() == 1:
                atom_X = atom.GetNeighbors()[0] # only one
                charge = atom_X.GetFormalCharge() -1
                atom_X.SetFormalCharge(charge) # <-- change formal charge
                rwmol.RemoveAtom(idx) # remove the H atom
                rwmol.RemoveBond(idx, atom_X.GetIdx()) # remove the bond    
                ionized = rwmol.GetMol()         
            else:
                charge = atom.GetFormalCharge() -1
                numH = atom.GetTotalNumHs() -1
                atom.SetFormalCharge(charge) # <-- change formal charge
                atom.SetNumExplicitHs(numH) # <-- remove one H
                atom.UpdatePropertyCache() # <-- update the property cache
                ionized = Chem.AddHs(rwmol)
        
        elif mode == "b2a":
            charge = atom.GetFormalCharge() + 1
            atom.SetFormalCharge(charge) # <-- change formal charge
            numH = atom.GetNumExplicitHs() + 1
            atom.SetNumExplicitHs(numH) # <-- add one H
            ionized = Chem.AddHs(rwmol)
            # Add hydrogens, specifying onlyOnAtoms to target the desired atom
            # explicitOnly=True ensures only explicit Hs are added, not implicit ones
            # ionized = Chem.AddHs(mw, explicitOnly=True, onlyOnAtoms=[idx])

        Chem.SanitizeMol(ionized)

        rdmol = Chem.MolFromSmiles(Chem.MolToSmiles(ionized, canonical=False))
        rdmolH = Chem.AddHs(rdmol)
        smiles = Chem.CanonSmiles(Chem.MolToSmiles(Chem.RemoveHs(rdmolH)))

        self.smiles = smiles
        self.sites = []
        self.update()


    def get_protonated(self, 
                        atom_idx: int | None = None, 
                        site_idx: int | None = None) -> list[Self]:
        """Make protonated state(s) from the current state.

        All ionizable sites are considered for protonation unless `atom_idx` or `site_idx` is given.

        Args:
            atom_idx (int | None, optional): atom index. Defaults to None.
            site_idx (int | None, optional): site index. Defaults to None.

        Returns:
            list[Self]: list of protonated States.
        """
        states = []

        if self.charge == self.max_formal_charge:
            return states
        
        if isinstance(atom_idx, int):
            for site in self.sites:
                if site.pr and (site.atom_idx == atom_idx):
                    new_state = self.copy()
                    new_state.ionize(site.atom_idx, "b2a")
                    new_state.transformation = '+H'
                    new_state.origin = self.smiles
                    states.append(new_state)        
        elif isinstance(site_idx, int):
            site = self.sites[site_idx]
            if not site.pr:
                return states
            new_state = self.copy()
            new_state.ionize(site.atom_idx, "b2a")
            new_state.transformation = '+H'
            new_state.origin = self.smiles
            states.append(new_state)
        else:
            for site in self.sites:
                if not site.pr:
                    continue
                new_state = self.copy()
                new_state.ionize(site.atom_idx, "b2a")
                new_state.transformation = '+H'
                new_state.origin = self.smiles
                states.append(new_state)

        return states
    

    def get_deprotonated(self, 
                          atom_idx: int | None = None, 
                          site_idx: int | None = None) -> list[Self]:
        """Make deprotonated state(s) from the current state.

        Args:
            atom_idx (int | None, optional): atom index. Defaults to None.
            site_idx (int | None, optional): site index. Defaults to None.

        Returns:
            list[Self]: list of deprotonated States.
        """
        states = []

        if self.charge == self.min_formal_charge:
            return states
        
        if isinstance(atom_idx, int):
            for site in self.sites:
                if site.de and (site.atom_idx == atom_idx):
                    new_state = self.copy()
                    new_state.ionize(atom_idx, "a2b")
                    new_state.transformation = '-H'
                    new_state.origin = self.smiles
                    states.append(new_state)
        elif isinstance(site_idx, int):
            site = self.sites[site_idx]
            if not site.de:
                return states
            new_state = self.copy()
            new_state.ionize(site.atom_idx, "a2b")
            new_state.transformation = '-H'
            new_state.origin = self.smiles
            states.append(new_state)
        else:
            for site in self.sites:
                if not site.de:
                    continue
                new_state = self.copy()
                new_state.ionize(site.atom_idx, "a2b")
                new_state.transformation = '-H'
                new_state.origin = self.smiles
                states.append(new_state)
        return states


    def get_tautomers(self) -> list[Self]:
        if self.tautomer_rule is None:
            return []
        elif self.tautomer_rule == "rdkit":
            t = RdkTautomers(self.smiles).enumerate()
        elif self.tautomer_rule == "comprehensive":
            t = ComprehensiveTautomers(self.smiles).enumerate()
        else:
            return []
        
        states = []
        for smiles in t.enumerated:
            try:
                assert smiles != self.smiles
                rdmol = Chem.MolFromSmiles(smiles)
                assert rdmol is not None
                charge = Chem.GetFormalCharge(rdmol)
                assert charge == self.charge
                states.append(State(smiles=smiles,
                                    origin=self.smiles,
                                    transformation='Tautomer'))
            except:
                continue
        return states
    

    def serialize(self) -> str:
        """Serialize the state to a string."""
        data = {
            'smiles': self.smiles,
            'origin': self.origin,
            'transformation': self.transformation,
            'min_formal_charge': self.min_formal_charge,
            'max_formal_charge': self.max_formal_charge,
            'min_atomic_charge': self.min_atomic_charge,
            'max_atomic_charge': self.max_atomic_charge,
            'protomer_rule': self.protomer_rule,
            'tautomer_rule': self.tautomer_rule,
            'charge': self.charge,
            'energy': self.energy,
            'sites': [asdict(site) for site in self.sites]
        }
        return json.dumps(data)
    

    def deserialize(self, data: str) -> Self:
        """Deserialize the state from a string."""
        obj = json.loads(data)
        self.smiles = obj['smiles']
        self.origin = obj['origin']
        self.transformation = obj['transformation']
        self.min_formal_charge = obj['min_formal_charge']
        self.max_formal_charge = obj['max_formal_charge']
        self.min_atomic_charge = obj['min_atomic_charge']
        self.max_atomic_charge = obj['max_atomic_charge']
        self.protomer_rule = obj['protomer_rule']
        self.tautomer_rule = obj['tautomer_rule']
        self.charge = obj['charge']
        self.energy = obj['energy']
        self.sites = [IonizableSite(**site) for site in obj['sites']]
        self.update()
        return self
    


class StateEnsemble:
    def __init__(self, states: list[State] | None = None, transformation: str | None = None) -> None:
        self.states = []
        
        if isinstance(states, list) and all(isinstance(_, State) for _ in states):
            self.states = states
        
        if transformation:
            for state in self.states:
                state.transformation = transformation


    def __str__(self) -> str:
        """String representation.

        Returns:
            str: short description of the state.
        """
        return f"StateEnsemble(n={self.size()}, states={[st.smiles for st in self.states]})"


    def __eq__(self, other: Self) -> bool:
        """Operator `==`."""
        if isinstance(other, StateEnsemble):
            return set([st.smiles for st in self.states]) == set([st.smiles for st in other.states])
        
        return False
    
    
    def __iter__(self) -> Iterator:
        """Operator `for ... in ...` or list()"""
        return iter(self.states)


    def __next__(self) -> State:
        """Operator `next()`"""
        return next(self.states)
    

    def __getitem__(self, index: int | slice) -> State | Self:
        """Operator `[]`"""
        if isinstance(index, slice):
            return StateEnsemble(self.states[index])
        else:
            return self.states[index]


    def __setitem__(self, index: int, state: State) -> Self:
        """Set item."""
        self.states[index] = state
        return self


    def __add__(self, other: State | Self) -> Self:
        """Operator `+`."""
        assert isinstance(other, State | StateEnsemble), "'+' operator expects State or StateEnsemble object"
        new_object = self.copy()
        if isinstance(other, State):
            new_object.states.append(other)
        elif isinstance(other, StateEnsemble):
            new_object.states.extend(other.states)
        return new_object
    

    def __iadd__(self, other: State | Self) -> Self:
        """Operator `+=`."""
        assert isinstance(other, State | StateEnsemble), "'+=' operator expects State or StateEnsemble object"
        if isinstance(other, State):
            self.states.append(other)
        elif isinstance(other, StateEnsemble):
            self.states.extend(other.states)
        return self
    

    def copy(self) -> Self:
        """Copy."""
        return copy.deepcopy(self)
    

    def drop(self) -> Self:
        """Drop duplicate and unreasonable states."""
        U = []
        mask = []
        for state in self.states:
            if state.rdmol is None:
                mask.append(False)
                continue
            if state.smiles in U:
                mask.append(False)
                continue
            reasonable = True
            for pattern in UnreasonablePatterns:
                if len(state.rdmol.GetSubstructMatches(pattern)) > 0:
                    reasonable = False
                    break
            if not reasonable:
                mask.append(False)
                continue
            mask.append(True)
            U.append(state.smiles)  
        self.states = list(itertools.compress(self.states, mask))
        return self
    

    def trim(self, pH: np.ndarray, C: float = ln10, beta: float = 1.0, ref_state_idx: int = 0, threshold: float = 0.05) -> Self:
        """Trim states whose pH-dependent population is below a given threshold across pH range 0-14.

        \\[
        \\begin{align}
        \\Delta G_{i, ref} &= PE_{i} - PE_{ref} \\\\[0.5em]
        \\Delta m_{i, ref} &= charge_{i} - charge _{ref} \\\\[0.5em]
        \\Delta G_{i, pH} &= \\Delta G_{i, ref} + \\Delta m_{i, ref} C pH \\\\[0.5em]
        p_{i, pH} &= \\frac {exp(-\\beta \\Delta G_{i, pH})}{\\sum_{i} exp(-\\beta \\Delta G_{i, pH})}
        \\end{align}
        \\]
            
        Args:
            pH (np.ndarray): array of pH values.
            C (float, optional): constant for pH-dependent dG calculation. Defaults to ln(10)
            beta (float, optional): \\( \\beta = \\frac{1}{k_{B} T} \\). Defaults to 1.0.
            ref_state_idx (int, optional): reference state index. Defaults to 0.
            threshold (float, optional): min population. Defaults to 0.05.

        Returns:
            Self: StateEnsemble
        """
        pH_dependent_populations = self.get_population(pH, C, beta, ref_state_idx)
        # p.shape == (self.size(), pH.shape[0])
        
        retain_mask = [False if max(p) < threshold else True for p in pH_dependent_populations]
        self.states = list(itertools.compress(self.states, retain_mask))


    def set_energies(self, energies: list[float] | np.ndarray) -> Self:
        """Set energies to states.

        Args:
            energies (list[float] | np.ndarray): list or array of energies.

        Returns:
            Self: StateEnsemble
        """
        assert len(energies) == self.size(), "The number of energies does not match the number of states"
        for i, energy in enumerate(energies):
            self.states[i].energy = float(energy)
        return self
    

    def get_state(self, index: int) -> State:
        """Get a state by index

        Args:
            index (int): state index.

        Returns:
            State: State
        """
        
        assert -self.size() <= index < self.size(), "State does not exist"
        return self.states[index]
    

    def size(self) -> int:
        """ Number of states."""
        return len(self.states)
    

    def info(self) -> None:
        """Print information of all states."""
        for i, state in enumerate(self.states):
            state.info(index=i)


    def serialize(self) -> str:
        """Serialize states to a string."""
        pass
    

    def get_micro_pKa(self, beta: float = 1.0, ref_state_idx: int = 0) -> dict[int, np.ndarray]:
        """Get micro-pKa.

        Args:
            beta (float, optional): \\( \\beta = \\frac{1}{k_{B} T} \\). Defaults to 1.0.
            ref_state_idx (int, optional): refence state index. Defaults to 0.

        Returns:
            dict[int, np.ndarray]: micro-pKa values for each ionizable site.
        """
        assert -self.size() <= ref_state_idx < self.size(), "Reference state does not exist"
        assert all([st.energy is not None for st in self.states]), "All states should have energy values"

        pKa = defaultdict(list)
        for site in self.states[ref_state_idx].sites:
            group = defaultdict(list)
            for st in self.states:
                for (a, i, q, pr, de) in st.site_info():
                    # ex. [('N', 5, 0, True, True), ...]
                    if i == site.atom_idx:
                        group[q].append(st.energy)
            weighted_mean = {q: Boltzmann_weighted_average(_, beta=beta) for q, _ in sorted(group.items())}
            charges = list(sorted(weighted_mean)) # ex. [-1, 0, +1]
            for (q1, q2) in list(itertools.pairwise(charges)): # ex. [(-1, 0), (0, +1)]
                G_deprotonated = weighted_mean[q1]
                G_protonated = weighted_mean[q2]
                delta_G_deprotonation = G_deprotonated - G_protonated
                pKa[site.atom_idx].append(delta_G_deprotonation)
        
        ordered_pKa = {}
        for k, v in pKa.items():
            ordered_pKa[k] = sorted(v)

        return ordered_pKa
            

    def get_macro_pKa(self, beta: float = 1.0, ref_state_idx: int = 0) -> np.ndarray:
        """Get macro-pKa.

        Args:
            beta (float, optional): \\( \\beta = \\frac{1}{k_{B} T} \\). Defaults to 1.0.
            ref_state_idx (int): refence state index. Defaults to 0.

        Returns:
            list[float]: macro-pKa values.
        """
        assert -self.size() <= ref_state_idx < self.size(), "Reference state does not exist"
        assert all([st.energy is not None for st in self.states]), "All states should have energy values"

        pKa = []
        for site in self.states[ref_state_idx].sites:
            group = defaultdict(list)
            for st in self.states:
                for (a, i, q, pr, de) in st.site_info():
                    # ex. [('N', 5, 0, True, True), ...]
                    group[q].append(st.energy)
        weighted_mean = {q: Boltzmann_weighted_average(_, beta=beta) for q, _ in sorted(group.items())}
        charges = list(sorted(weighted_mean)) # ex. [-1, 0, +1]
        for (q1, q2) in list(itertools.pairwise(charges)): # ex. [(-1, 0), (0, +1)]
            G_deprotonated = weighted_mean[q1]
            G_protonated = weighted_mean[q2]
            delta_G_deprotonation = G_deprotonated - G_protonated
            pKa.append(delta_G_deprotonation)
        
        return sorted(pKa)
    
    
    def get_population(self, pH: np.ndarray, C: float = ln10, beta: float = 1.0, ref_state_idx: int = 0) -> np.ndarray:
        """Get populations at a given pH.

        The reference state can be arbitrary and is set to the initial_state here.

        \\[
        \\begin{align}
        \\Delta G_{i, ref} &= PE_{i} - PE_{ref} \\\\[0.5em]
        \\Delta m_{i, ref} &= charge_{i} - charge _{ref} \\\\[0.5em]
        \\Delta G_{i, pH} &= \\Delta G_{i, ref} + \\Delta m_{i, ref} C pH \\\\[0.5em]
        p_{i, pH} &= \\frac {exp(-\\beta \\Delta G_{i, pH})}{\\sum_{i} exp(-\\beta \\Delta G_{i, pH})}
        \\end{align}
        \\]
            
        Args:
            pH (np.ndarray): array of pH values.
            C (float, optional): constant for pH-dependent dG calculation. Defaults to ln(10).
            beta (float, optional): \\( \\beta = \\frac{1}{k_{B} T} \\). Defaults to 1.0.
            ref_state_idx (int, optional): refence state index. Defaults to 0.

        Returns:
            np.ndarray: 
                array of populations with shape of (number of states, number of pH).
        """
        assert -self.size() <= ref_state_idx < self.size(), "Reference state does not exist"
        assert all([st.energy is not None for st in self.states]), "All states should have energy values"
        ref = self.states[ref_state_idx]
        pH = np.array(pH)
        
        dG = []
        for st in self.states:
            delta_G = st.energy - ref.energy
            delta_m = st.charge - ref.charge
            dG.append(delta_G + delta_m * C * pH)
        
        dG = np.array(dG)
        Boltzmann_factors = np.exp(-beta * dG)
        Z = np.sum(Boltzmann_factors, axis=0)
        p = Boltzmann_factors/Z

        assert p.shape == (self.size(), pH.shape[0]), "Population array has wrong shape"
        
        return p


    def get_pH_population_chart(self, 
                                pH: np.ndarray, 
                                C: float = ln10, 
                                beta: float = 1.0,
                                ref_state_idx: int = 0,
                                ignore_below: float = 0.01,
                                pH_label: np.ndarray | None = None,
                                width: int = 600,
                                height: int = 400,
                                palette: str = 'tableau10') -> tuple[alt.vegalite.v5.api.LayerChart, list[int]]:
        """Get an Altair plot object for pH-dependent population curve.

        Args:
            pH (np.ndarray): array of pH values.
            C (float): constant for pH-dependent dG calculation. Defaults to ln(10).
            beta (float, optional): \\( \\beta = \\frac{1}{k_{B} T} \\). Defaults to 1.0.
            ignore_below (float) : 
                ignore low populated microstates. Defaults to 0.01.
            pH_label (np.ndarray | None, optional): 
                array of pH values for plot. 
                If None, pH is used. Defaults to None.
            width (int, optional): plot width. Defaults to 600.
            height (int, optional): plot height. Defaults to 300.
            palette (str, optional): color palette. Defaults to 'tableau10'.

        Returns:
            alt.vegalite.v5.api.LayerChart: Altair plot object
        """
        
        # calculate populations
        p = self.get_population(pH, C, beta, ref_state_idx)
        # p.shape == (self.size(), pH.shape[0])
        
        if pH_label is None:
            pH_label = pH
        
        # preparing dataframe and state ensemble
        data = {'Microstate': [], 'pH':[], 'p':[]}
        
        populated_state_idx = []
        for i, pH_dependent_populations in enumerate(p):
            if max(pH_dependent_populations) < ignore_below:
                continue
            populated_state_idx.append(i)
            j = len(populated_state_idx)
            for k, pop in enumerate(pH_dependent_populations):
                data['Microstate'].append(j) # 1, 2, 3, ...
                data['pH'].append(pH_label[k])
                data['p'].append(pop)

        df = pd.DataFrame(data)
        
        # line plot
        lineplot = alt.Chart(df).mark_line().encode(
            x=alt.X('pH:Q', title='pH'),
            y=alt.Y('p:Q', title='Population'),
            color=alt.Color('Microstate:N', scale=alt.Scale(scheme=palette)),
        ).properties(
            width=width,
            height=height)
        
        # data labels
        labels = alt.Chart(df).mark_text(
            align='left',
            dx=5,
            dy=-5
        ).encode(
            x=alt.X('pH', aggregate={'argmax': 'p'}),
            y=alt.Y('p', aggregate={'argmax': 'p'}),
            text='Microstate:N',
            color='Microstate:N'
        )

        chart = (lineplot + labels)
        
        return (chart, populated_state_idx)
    

    def serialize(self) -> str:
        """Serialize states to a string."""
        data = [json.loads(state.serialize()) for state in self.states]
        return json.dumps(data)
    

    def deserialize(self, data: str) -> Self:
        """Deserialize states from a string."""
        obj = json.loads(data)
        self.states = []
        for state_data in obj:
            state = State(smiles=state_data['smiles'])
            state.deserialize(json.dumps(state_data))
            self.states.append(state)
        return self
        

class StateNetwork:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.visited_states = []
        self.initial_state = None
    
    def copy(self) -> Self:
        """Copy."""
        return copy.deepcopy(self)
    

    def build(self, 
              smiles: str,
              origin: str | None = None, 
              transformation: str | None = None,
              min_formal_charge: int = -2,
              max_formal_charge: int = +2,
              min_atomic_charge: int = -1,
              max_atomic_charge: int = +1,
              protomer_rule: str = 'default',
              tautomer_rule: str | None = None,
              verbose: bool = False) -> Self:
        """Build the microstate network using BFS from initial state.""" 
        self.initial_state = State(smiles=smiles,
                              protomer_rule=protomer_rule,
                              tautomer_rule=tautomer_rule,
                              min_formal_charge=min_formal_charge,
                              max_formal_charge=max_formal_charge,
                              min_atomic_charge=min_atomic_charge,
                              max_atomic_charge=max_atomic_charge)
        self.initial_state
        # Initialize BFS
        queue = deque([self.initial_state])
        self.visited_states.append(self.initial_state)
        self.graph.add_node(self.initial_state.smiles, 
                            initial=True, 
                            sites=self.initial_state.site_info())
        iter = 0

        while queue:
            iter += 1
            current_state = queue.popleft()
            neighbors = self._generate_neighbors(current_state)
            for neighbor_state in neighbors:
                if neighbor_state.transformation == 'Tautomer' and current_state.charge != neighbor_state.charge:
                    continue
                self.graph.add_edge(current_state.smiles, 
                                    neighbor_state.smiles, 
                                    transformation=neighbor_state.transformation)
                if neighbor_state not in self.visited_states:
                    self.visited_states.append(neighbor_state)
                    imap = self._mcs_index_map(neighbor_state)
                    sites = [(a, imap[i], q, pr, de) for (a, i, q, pr, de) in neighbor_state.site_info()]
                    self.graph.add_node(neighbor_state.smiles, 
                                        initial=False, 
                                        sites=sites)
                    queue.append(neighbor_state)
            if verbose:
                print(f"Iteration {iter:2}: {len(self.visited_states):2} microstates found")
        
        if verbose:
            print(f"\nNetwork construction complete!")
            print(f"Total microstates: {len(self.graph.nodes())}")
            print(f"Total transformations: {len(self.graph.edges())}")

        return self
    

    def set_energies(self, energies: list[float] | np.ndarray) -> Self:
        """Set energies to states.

        Args:
            energies (list[float] | np.ndarray): list or array of energies.

        Returns:
            Self: self
        """
        assert len(energies) == self.size(), "The number of energies does not match the number of states"
        for i, energy in enumerate(energies):
            self.visited_states[i].energy = float(energy)
        return self 
    

    def trim(self, pH: np.ndarray, C: float = ln10, beta: float = 1.0, ref_state_idx: int = 0, threshold: float = 0.05) -> Self:
        """Trim states whose pH-dependent population is below a given threshold across pH range 0-14.

        \\[
        \\begin{align}
        \\Delta G_{i, ref} &= PE_{i} - PE_{ref} \\\\[0.5em]
        \\Delta m_{i, ref} &= charge_{i} - charge _{ref} \\\\[0.5em]
        \\Delta G_{i, pH} &= \\Delta G_{i, ref} + \\Delta m_{i, ref} C pH \\\\[0.5em]
        p_{i, pH} &= \\frac {exp(-\\beta \\Delta G_{i, pH})}{\\sum_{i} exp(-\\beta \\Delta G_{i, pH})}
        \\end{align}
        \\]
            
        Args:
            pH (np.ndarray): array of pH values.
            C (float, optional): constant for pH-dependent dG calculation. Defaults to ln(10).
            beta (float, optional): \\( \\beta = \\frac{1}{k_{B} T} \\). Defaults to 1.0.
            ref_state_idx (int, optional): reference state index. Defaults to 0.
            threshold (float, optional): min population. Defaults to 0.05.

        Returns:
            Self: StateEnsemble
        """
        pH_dependent_populations = self.get_population(pH, C, beta, ref_state_idx)
        # p.shape == (self.size(), pH.shape[0])
        
        retain_mask = [False if max(p) < threshold else True for p in pH_dependent_populations]
        remove_mask = [not b for b in retain_mask]
        nodes_to_remove = list(itertools.compress([st.smiles for st in self.visited_states], remove_mask))

        self.graph.remove_nodes_from(nodes_to_remove)
        self.visited_states = list(itertools.compress(self.visited_states, retain_mask))

        return self
    

    def get_state_ensemble(self, index: int | slice | None = None) -> StateEnsemble:
        """Get states by index or slice or all states."""
        if isinstance(index, slice):
            return StateEnsemble(self.visited_states[index])
        elif isinstance(index, int):
            return StateEnsemble([self.visited_states[index]])
        else: # all
            return StateEnsemble(self.visited_states)


    def _generate_neighbors(self, state: State) -> StateEnsemble:
        """Generate all possible neighboring microstates."""
        neighbors = StateEnsemble()
        if state == self.initial_state and isinstance(state.tautomer_rule, str):
            neighbors += StateEnsemble(state.get_tautomers())
        neighbors += StateEnsemble(state.get_protonated())
        neighbors += StateEnsemble(state.get_deprotonated())
        neighbors = neighbors.drop()
        
        return neighbors

    def get_initial_state(self) -> State:
        """Get the initial state."""
        return self.initial_state


    def info(self) -> None:
        """Print information of the network."""
        print(f"StateNetwork - nodes: {self.get_num_nodes()} edeges: {self.get_num_edges()}")


    def size(self) -> int:
        """Number of unique states in the network."""
        return len(self.visited_states)
    

    def get_num_nodes(self) -> int:
        """Number of nodes in the network."""
        return len(self.graph.nodes())
    

    def get_num_edges(self) -> int:
        """Number of edges in the network."""
        return len(self.graph.edges())
    

    def _mcs_index_map(self, other: State) -> dict[int, int]:
        """Mapping atom indices using the maximum common structure (MCS).

        Uses the self.initial_state as reference in mapping `other` State.

        Args:
            other (State): to be mapped state.

        Returns:
            dict: {ref atom index: other atom index, ...}
        """
        mcs = Chem.rdFMCS.FindMCS([self.initial_state.rdmol, other.rdmol], 
                            atomCompare=Chem.rdFMCS.AtomCompare.CompareAny, 
                            bondCompare=Chem.rdFMCS.BondCompare.CompareAny, 
                            completeRingsOnly=True)
        mcs_rdmol = Chem.MolFromSmarts(mcs.smartsString)
        match_1 = self.initial_state.rdmol.GetSubstructMatch(mcs_rdmol)
        match_2 = other.rdmol.GetSubstructMatch(mcs_rdmol)
        return {match_2[i]: match_1[i] for i in range(len(match_1))}


    def get_micro_pKa(self, beta: float=1.0, ref_state_idx: int = 0) -> dict[int,np.ndarray]:
        """Calculate micro-pKa with provided potential energies.

        Args:
            beta (float, optional): \\( \\beta = \\frac{1}{k_{B} T} \\). Defaults to 1.0.

        Returns:
            dict[int,list[float]]: micro-pKa values for each ionizable site.
        """
        state_ens = StateEnsemble(self.visited_states)
        return state_ens.get_micro_pKa(beta=beta, ref_state_idx=ref_state_idx)

            
    def get_macro_pKa(self, beta: float = 1.0, ref_state_idx: int = 0) -> np.ndarray:
        """Calculatate macro-pKa with provided potential energies.

        Args:
            beta (float, optional): \\( \\beta = \\frac{1}{k_{B} T} \\). Defaults to 1.0.

        Returns:
            list[float]: macro-pKa values.
        """
        state_ens = StateEnsemble(self.visited_states)
        return state_ens.get_macro_pKa(beta=beta, ref_state_idx=ref_state_idx)

    
    def get_population(self, pH: np.ndarray, C: float = ln10, beta: float = 1.0, ref_state_idx: int = 0) -> np.ndarray:
        """Calculate populations with provided potential energies and pH.

        The reference state can be arbitrary and is set to the initial_state here.

        \\[
        \\begin{align}
        \\Delta G_{i, ref} &= PE_{i} - PE_{ref} \\\\[0.5em]
        \\Delta m_{i, ref} &= charge_{i} - charge _{ref} \\\\[0.5em]
        \\Delta G_{i, pH} &= \\Delta G_{i, ref} + \\Delta m_{i, ref} C pH \\\\[0.5em]
        p_{i, pH} &= \\frac {exp(-\\beta \\Delta G_{i, pH})}{\\sum_{i} exp(-\\beta \\Delta G_{i, pH})}
        \\end{align}
        \\]
            
        Args:
            pH (np.ndarray): array of pH values.
            C (float): constant for pH-dependent dG calculation. Defaults to ln(10).
            beta (float, optional): \\( \\beta = \\frac{1}{k_{B} T} \\). Defaults to 1.0.

        Returns:
            np.ndarray: 
                array of populations with shape of (number of states, number of pH).
        """
        state_ens = StateEnsemble(self.visited_states)
        return state_ens.get_population(pH, C, beta=beta, ref_state_idx=ref_state_idx)


    def get_pH_population_chart(self,
                                pH: np.ndarray, 
                                C: float = ln10, 
                                beta: float = 1.0,
                                ref_state_idx: int = 0,
                                ignore_below: float = 0.01,
                                pH_label: np.ndarray | None = None,
                                width: int = 600,
                                height: int = 400,
                                palette: str = 'tableau10') -> tuple[alt.vegalite.v5.api.LayerChart, list[int]]:
        """Make an Altair plot object for pH-dependent population curve.

        Args:
            pH (np.ndarray): array of pH values.
            C (float): constant for pH-dependent dG calculation. Defaults to ln(10).
.            beta (float, optional): \\( \\beta = \\frac{1}{k_{B} T} \\). Defaults to 1.0.
            ignore_below (float) : 
                ignore low populated microstates. Defaults to 0.01.
            pH_label (np.ndarray | None, optional): 
                array of pH values for plot. 
                If None, pH is used. Defaults to None.
            width (int, optional): plot width. Defaults to 600.
            height (int, optional): plot height. Defaults to 300.
            palette (str, optional): color palette. Defaults to 'tableau10'.

        Returns:
            alt.vegalite.v5.api.LayerChart: Altair plot object
        """
        state_ens = StateEnsemble(self.visited_states)
        return state_ens.get_pH_population_chart(pH, 
                                                 C, 
                                                 beta=beta, 
                                                 ref_state_idx=ref_state_idx,
                                                 ignore_below=ignore_below,
                                                 pH_label=pH_label, 
                                                 width=width, 
                                                 height=height, 
                                                 palette=palette)

    def serialize(self) -> str:
        """Serialize the network to a string."""
        data = {
            'graph': json_graph.node_link_data(self.graph), 
            'visited_states': [st.serialize() for st in self.visited_states],
            'initial_state': self.initial_state.serialize(),
            }
        return json.dumps(data)
    

    def deserialize(self, data: str) -> Self:
        """Deserialize the network from a string."""
        obj = json.loads(data)
        self.graph = json_graph.node_link_graph(obj['graph'])
        self.visited_states = [State().deserialize(st) for st in obj['visited_states']]
        self.initial_state = State().deserialize(obj['initial_state'])
        return self
    


class QupkakeMicrostates():

    def __init__(self, origin: Mol, calculator: str = 'xTB'):
        self.origin = origin
        self.calculator = calculator
        self.basic_sites = []
        self.acidic_sites = []
        self.states = []
        self.mols = []
        self.reference = None
    

    def enumerate(self) -> None:
        # Qu pKake results must be stored at .confs
        for conf in self.origin:
            pka = conf.props.get('pka', None)
            if pka is None:
                # no protonation/deprotonation sites
                continue
            if isinstance(pka, str) and pka.startswith('tensor'):
                # ex. 'tensor(9.5784)'
                pka = float(pka.replace('tensor(','').replace(')',''))
            if conf.props.get('pka_type') == 'basic':
                self.basic_sites.append(conf.props.get('idx'))
            elif conf.props.get('pka_type') == 'acidic':
                self.acidic_sites.append(conf.props.get('idx'))

        # enumerate protonation/deprotonation sites to generate microstates

        np = len(self.basic_sites)
        nd = len(self.acidic_sites)
        P = [c for n in range(np+1) for c in itertools.combinations(self.basic_sites, n)]
        D = [c for n in range(nd+1) for c in itertools.combinations(self.acidic_sites, n)]
        
        PD = list(itertools.product(P, D))
        
        for (p, d) in PD:
            conf = self.origin.confs[0].copy()
            conf = conf.protonate(p).deprotonate(d).optimize(calculator=self.calculator)
            charge = len(p) - len(d)
            self.states.append(SimpleNamespace(
                charge=charge, 
                protonation_sites=p, 
                deprotonation_sites=d,
                conf=conf,
                smiles=Mol(conf).smiles,
                delta_m=None,
                PE=None))
            
        # sort microstates by ascending charges
        self.states = sorted(self.states, key=lambda x: x.charge)


    @staticmethod
    def Boltzmann_weighted_average(potential_energies: list) -> float:
        """Calculate Boltzmann weighted average potential energy at pH 0.

        Args:
            potential_energies (list): a list of potential energies.

        Returns:
            float: Boltzmann weighted average potential energy.
        """
        kT = 0.001987 * 298.0 # (kcal/mol K), standard condition
        C = math.log(10) * kT
        pe_array = np.array(potential_energies)
        pe = pe_array - min(potential_energies)
        Boltzmann_factors = np.exp(-pe/kT)
        Z = np.sum(Boltzmann_factors)
        p = Boltzmann_factors/Z

        return float(np.dot(p, pe_array))


    def populate(self) -> None:
        for microstate in self.states:
            mol = Mol(microstate.conf).make_confs(n=4).optimize_confs()
            # mol = mol.drop_confs(similar=True, similar_rmsd=0.3, verbose=True)
            # mol = mol.optimize_confs(calculator=calculator)
            # mol = mol.drop_confs(k=10, window=15.0, verbose=True)
            PE = []
            for conf in mol.confs:
                conf = conf.optimize(calculator=self.calculator, verbose=True)
                # GFN2xTB requires 3D coordinates
                # xtb = GFN2xTB(conf.rdmol).singlepoint(water='cpcmx', verbose=True)
                PE.append(conf.potential_energy(calculator=self.calculator))
                # xtb = GFN2xTB(conf.rdmol).singlepoint(verbose=True)
                # SimpleNamespace(
                #             PE = datadict['total energy'] * hartree2kcalpermol,
                #             Gsolv = Gsolv,
                #             charges = datadict['partial charges'],
                #             wbo = Wiberg_bond_orders,
                #             )
            microstate.PE = self.Boltzmann_weighted_average(PE)
            logger.info(f"PE= {PE}")
            logger.info(f"Boltzmann weighted= {microstate.PE}")            
            self.mols.append(mol)

    def get_populations(self, pH: float) -> list[tuple]:
        # set the lowest dG as the reference
        self.reference = self.states[np.argmin([microstate.PE for microstate in self.states])]
        for microstate in self.states:
            microstate.delta_m = microstate.charge - self.reference.charge
        dG = []
        for microstate in self.states:
            dG.append((microstate.PE - self.reference.PE) + microstate.delta_m * C * pH)
        dG = np.array(dG)

        logger.info(f"dG= {dG}")
        kT = 0.001987 * 298.0 # (kcal/mol K), standard condition
        C = math.log(10) * kT
        Boltzmann_factors = np.exp(-dG/kT)
        Z = np.sum(Boltzmann_factors)
        p = Boltzmann_factors/Z
        idx_p = sorted(list(enumerate(p)), key=lambda x: x[1], reverse=True)
        # [(0, p0), (1, p1), ...]

        return idx_p

    def get_ensemble(self) -> list[Mol]:
        return self.mols

    def get_mol(self, idx: int) -> Mol:
        return self.mols[idx]
    
    def count(self) -> int:
        return len(self.states)