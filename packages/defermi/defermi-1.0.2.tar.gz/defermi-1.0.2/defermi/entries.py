#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Dec 11 14:33:12 2020

@author: villa
"""

from abc import ABCMeta
from monty.json import MSONable, MontyDecoder, MontyEncoder, jsanitize
import numpy as np
import warnings
import os

from pymatgen.core.units import kb

from .structure import defect_finder
from .elasticity import get_relaxation_volume
from .tools.utils import get_charge_from_computed_entry



class DefectEntry(MSONable,metaclass=ABCMeta):
    
    def __init__(self,
                defect,
                energy_diff=None,
                corrections={},
                data=None,
                formation_energy_function=None,
                defect_concentration_function=None):
        """
        Object to store the results of a defect calculation. 
        This object is usually created automatically when importing results, either from directories or
        DataFrame.
        
        Parameters
        ----------
        defect : Defect
            Defect object (Vacancy, Interstitial, Substitution, Polaron or DefectComplex)
        energy_diff : float
            Difference btw energy of defect structure and energy of pristine (bulk) structure in eV.
        corrections : dict
            Dictionary of corrections in eV to apply to defect formation energy.
            All values will be added to the defect formation energy. Keys indicate the correction type.     
        data : dict
            Store additional data in dict format.
        label : str
            Additional label to add to defect specie.
        formation_energy_function : function
            Custom function for calculation of defect formation energy.
            Check documentation in `formation_energy` function for more details.
        defect_concentration_function : function
            Custom function for calculation of defect concentration.
            Check documentation in `defect_concentration` function for more details.
        """
        self._defect = defect
        self._energy_diff = energy_diff
        self._corrections = corrections
        self._data = data if data else {}
        self._formation_energy_function = formation_energy_function
        self._defect_concentration_function = defect_concentration_function
    
    def __repr__(self):
        return "DefectEntry: Name=%s, Charge=%i" %(self.name,self.charge)

    def __str__(self):
        output = [
            "DefectEntry",
            "Defect: %s" %(self.defect.__str__()),
            "Energy: %.4f" %self.energy_diff,
            "Corrections: %.4f" %sum([v for v in self.corrections.values()]),
            "Charge: %i" %self.charge,
            "Multiplicity: %i" %self.multiplicity,
            "Data: %s" %list(self.data.keys()),
            "Name: %s" %self.name,
            "\n"
            ]
        return "\n".join(output)

    @property
    def bulk_structure(self):
        """
        Structure of pristine material.
        """
        return self.defect.bulk_structure   

    @property
    def charge(self):
        if self.defect.charge is None:
            warnings.warn('Charge is not set in Defect object, setting charge to 0')
            self.defect.set_charge(0)
        return self.defect.charge
    
    @property
    def corrections(self):
        """
        Dictionary with corrections to the defect energy. Its values will be added to the formation energy.
        """
        return self._corrections
    
    @property
    def data(self):
        """
        Dictionary containing additional data.
        """
        return self._data

    @property
    def defect(self):
        """
        Defect object.
        """
        return self._defect  
    
    @property
    def defect_specie(self):
        """
        Species involved in defect.
        """
        return self.defect.specie
    
    @property
    def defect_type(self):
        """
        Defect type.
        """
        return self.defect.type
    
    @property
    def delta_atoms(self):
        """
        Dictionary with Element as keys and particle difference between defect structure
        and bulk structure as values.
        """
        return self.defect.delta_atoms
    
    @property
    def energy_diff(self):
        return self._energy_diff
    
    @property
    def label(self):
        return self.defect.label

    @property
    def multiplicity(self):
        if self.defect.multiplicity is None:
            warnings.warn('Multiplicity is not set in Defect object, setting multiplicity to 1.')
            self.defect.set_multiplicity(1)
        return self.defect.multiplicity
                
    @property
    def name(self):
        return self.defect.name
        
    @property
    def structure(self):
        return self.defect.defect_structure
    
    @property
    def symbol(self):
        return self.defect.symbol

    @property
    def symbol_charge(self):
        """
        Defect symbol with charge formatted with numbers.
        """
        return self.defect.symbol_with_charge

    @property
    def symbol_kroger(self):
        """
        Defect symbol with charge formatted with Kröger-Vink notation.
        """
        return self.defect.symbol_with_charge_kv
    

    @property
    def formation_energy_function(self):
        return self._formation_energy_function
    
    @property
    def defect_concentration_function(self):
        return self._defect_concentration_function
    
    def set_charge(self,new_charge=0):
        """
        Set defect charge
        """
        self.defect.set_charge(new_charge)
        return 
    
    def set_corrections(self,**kwargs):
        """
        Set defect corrections. Pass either dict or kwargs.
        """
        if self._corrections is None:
            self._corrections = {}
        for k,v in kwargs.items():
            self._corrections[k] = v
        return

    def set_data(self,new_data):
        """
        Set data dictionary
        """
        self._data = new_data
    
    def set_multiplicity(self,new_multiplicity=None):
        """
        Sets the Multiplicity of the defect.
        If `new_multiplicity` is not provided it is determined 
        with `self.defect.get_multiplicity`
        """
        self.defect.set_multiplicity(new_multiplicity)
    
    def set_label(self,new_label):
        """
        Set defect label.
        """
        self.defect.set_label(new_label)


    def set_defect_concentration_function(self, new_function):
        """
        Set custom defect concentration function.
        """
        self._defect_concentration_function = new_function
    
    def set_formation_energy_function(self, new_function):
        """
        Set custom defect concentrations function.
        """
        self._formation_energy_function = new_function

    def reset_defect_concentration_function(self):
        """
        Reset formation energy function to default.
        """
        self._defect_concentration_function = None
    
    def reset_formation_energy_function(self):
        """
        Reset formation energy function to default.
        """
        self._formation_energy_function = None

    
    def as_dict(self):
        """
        Returns:
            Json-serializable dict representation of DefectEntry.
        """
        d = {}
        d['defect'] = MontyEncoder().encode(self.defect)
        d['energy_diff'] = self.energy_diff
        d['corrections'] = jsanitize(self.corrections)
        d['data'] = jsanitize(self.data)
        return d


    @classmethod
    def from_dict(cls,d):
        """
        Reconstitute a DefectEntry object from a dict representation created using
        as_dict().

        Parameters
        ----------
        d : dict
            Dictionary representation of DefectEntry.

        Returns
        -------
        entry : DefectEntry
            DefectEntry object

        """
        defect = MontyDecoder().decode(d['defect'])
        energy_diff = d['energy_diff']
        corrections = d['corrections']
        data = d['data']
        return cls(defect=defect,energy_diff=energy_diff,corrections=corrections,data=data)


    @staticmethod
    def from_computed_entries(
                            computed_entry_defect,
                            computed_entry_bulk,
                            corrections,
                            multiplicity=1,
                            data=None,
                            label=None,
                            initial_structure=False,
                            **kwargs):
        """
        Generate DefectEntry object from Pymatgen's ComputedStructureEntry objects.

        Parameters
        ----------
        computed_entry_defect : VaspJob
            ComputedStructureEntry of the defect calculation.
        computed_entry_bulk : VaspJob
            ComputedStructureEntry of the bulk calculation.
        corrections : dict
            Dict of corrections for defect formation energy. All values will be summed and
            added to the defect formation energy.
        multiplicity : int
            Multiplicity of defect within the supercell. 
            If set to None is attempted to be determined automatically.
        data : dict
            Store additional data in dict format.
        label : str
            Additional label to add to defect specie. Does not influence non equilibrium calculations.
        initial_structure : bool
            Use initial structure for defect recognition. Useful when relaxations are large and 
            defect_finder struggles to find the right defects.
        kwargs : dict
            Kwargs to pass to `defect_finder`.

        Returns
        -------
        entry : DefectEntry
            DefectEntry object

        """ 
        entry_df, entry_bulk = computed_entry_defect,computed_entry_bulk
        charge = get_charge_from_computed_entry(entry_df)
        energy_diff = entry_df.energy - entry_bulk.energy
        if initial_structure:
            defect_structure = entry_df.data['ionic_steps'][0]['structure']
        else:
            defect_structure = entry_df.structure
        
        return DefectEntry.from_structures(defect_structure=defect_structure,
                                           bulk_structure=entry_bulk.structure,
                                           energy_diff=energy_diff,corrections=corrections,
                                           charge=charge,multiplicity=multiplicity,data=data,
                                           label=label,**kwargs)
    

    @staticmethod
    def from_structures(
                    defect_structure,
                    bulk_structure,
                    energy_diff,
                    corrections,
                    charge=0,
                    multiplicity=1,
                    data=None,
                    label=None,
                    **kwargs):
        """
        Generate DefectEntry object from Structure objects.

        Parameters
        ----------
        defect_structure : Structure
            Defect structure.
        bulk_structure : Structure
            Bulk structure.
        energy_diff : float 
            Difference btw energy of defect structure and energy of pristine structure
        corrections : dict
            Dict of corrections in eV for defect formation energy. All values will be summed and
            added to the defect formation energy.  
        charge : int or float
            Charge of the defect system. The default is 0.
        multiplicity : int
            multiplicity of defect within the supercell. 
            If set to None is attempted to be determined automatically with Pymatgen. The default is 1.
        data : dict
            Store additional data in dict format.
        label : str
            Additional label to add to defect specie. Does not influence non equilibrium calculations.
        kwargs : dict
            Kwargs to pass to defect_finder. 'verbose' is set to True by default.

        Returns
        -------
        entry : DefectEntry
            DefectEntry object

        """
        if not kwargs:
            kwargs = {'verbose':True}
        elif 'verbose' not in kwargs.keys():
            kwargs['verbose'] = True
        defect = defect_finder(defect_structure, bulk_structure,**kwargs)
        if not defect:
            raise ValueError('Cannot create DefectEntry from empty defect object')
        defect.set_charge(charge)
        defect.set_label(label)
        if multiplicity:
            defect.set_multiplicity(multiplicity)
        else:
            try:
                new_multiplicity = defect.get_multiplicity()
                defect.set_multiplicity(new_multiplicity)
            except NotImplementedError:
                warnings.warn(f'get_multiplicity not implemented for {defect.defect_type}, setting multiplicity to 1')
                defect.set_multiplicity(1)
        
        return DefectEntry(defect, energy_diff, corrections, data)


    @staticmethod
    def from_vasp_directories(
                            path_defect,
                            computed_entry_bulk=None,
                            path_bulk=None,
                            corrections={},
                            multiplicity=1,
                            data=None,
                            label=None,
                            initial_structure=False,
                            function=None,
                            computed_entry_kwargs={},
                            finder_kwargs={}):
        """
        Generate DefectEntry object from VASP directories read with Pymatgen.

        Parameters
        ----------
        path_defect : str
            Path of VASP defect calculation.
        computed_entry_bulk : VaspJob
            ComputedStructureEntry of the bulk calculation.
        path_bulk : str
            If `computed_entry_bulk` is not provided, read directly from VASP directory. 
        corrections : dict
            Dict of corrections for defect formation energy. All values will be summed and
            added to the defect formation energy.
        multiplicity : int
            Multiplicity of defect within the supercell. 
            If set to None is attempted to be determined automatically with Pymatgen. The default is 1.
        data : dict
            Store additional data in dict format.
        label : str
            Additional label to add to defect specie. Does not influence non equilibrium calculations.
        initial_structure : bool
            Use initial structure for defect recognition. Useful when relaxations are large and 
            defect_finder struggles to find the right defects.
        function : function
            Function to apply to DefectEntry. Useful to automate custom entry modification.
            The function can modify entry attributes and returns None.
        computed_entr_kwargs : dict
            Kwargs to pass to Vasprun.get_computed_entry. 
        finder_kwargs : dict
            Kwargs to pass to `defect_finder`.

        Returns
        -------
        entry : DefectEntry
            DefectEntry object

        """ 
        from pymatgen.io.vasp.outputs import Vasprun

        if initial_structure:
            if computed_entry_kwargs:
                if 'data' in computed_entry_kwargs.keys():
                    computed_entry_kwargs['data'].append('ionic_steps')
                else:
                    computed_entry_kwargs['data'] = ['ionic_steps']
            else:
                computed_entry_kwargs = {'data':['ionic_steps']}
        computed_entry_defect = _get_computed_entry_from_path(path_defect,**computed_entry_kwargs)
        if not computed_entry_bulk:
            if path_bulk:
                vasprun_bulk = os.path.join(path_bulk,'vasprun.xml')
                computed_entry_bulk = Vasprun(vasprun_bulk,parse_dos=False,parse_eigen=False,parse_potcar_file=False).get_computed_entry(**computed_entry_kwargs)
            else:
                raise ValueError('Either bulk ComputedEntry or path of bulk calculation has to be provided')

        entry = DefectEntry.from_computed_entries(
                                                computed_entry_defect=computed_entry_defect,
                                                computed_entry_bulk=computed_entry_bulk,
                                                corrections=corrections,
                                                multiplicity=multiplicity,
                                                data=data,
                                                label=label,
                                                initial_structure=initial_structure,
                                                **finder_kwargs)
        
        if function:
            function(entry)
        return entry
        

    def defect_concentration(self,
                            vbm=0,
                            chemical_potentials=None,
                            temperature=300,
                            fermi_level=0.0, 
                            per_unit_volume=True,
                            eform_kwargs={},
                            **kwargs):
        """
        Compute the defect concentration.
        If `defect_concentration_function` is set, the custom function is called, 
        otherwise, the concentration is computed in the dilute limit as:

        n = N * (1 / e^(Ef/kT) + 1), where:

        - N is the site multiplicity (in cm^-3 or per unit cell)
        - Ef is the formation energy of the defect.
        - k is the Boltzmann constant.
        - T is the temperature.

        A custom function can be set when initializing the `DefectEntry` or by using the
        'set_defect_concentration_function` method. Use `reset_defect_concentration_function`
        to restore the default behaviour.
        If a custom function is given, the input must have the same args as this function,
        with the possibility to add more kwargs. 

        Parameters
        ----------
        vbm : float
            Valence band maximum of bulk calculation in eV
        chemical_potentials : dict
            Chemical potentials of the elements involved in the defect.
        temperature : float
            Temperature in Kelvin.
        fermi_level : float
            Fermi level in eV (with respect to the VBM).
        per_unit_volume : bool
            Compute concentrations per unit volume using `self.defect.bulk_volume`.
        eform_kwargs : dict
            Kwargs to pass to `self.formation_energy`.
        kwargs : dict
            Kwargs to pass to custom function.
                
        Returns:
        --------
        conc : float
            Defect concentration in cm^-3 or per unit cell.

        """
        if self.defect_concentration_function:
            return self.defect_concentration_function(self,
                                                    vbm=vbm,
                                                    chemical_potentials=chemical_potentials,
                                                    temperature=temperature,
                                                    fermi_level=fermi_level,
                                                    per_unit_volume=per_unit_volume,
                                                    eform_kwargs=eform_kwargs,
                                                    **kwargs)
        
        
        n = self.defect.site_concentration_in_cm3 if per_unit_volume else self.multiplicity 
        eform = self.formation_energy(
                                vbm=vbm,
                                chemical_potentials=chemical_potentials,
                                fermi_level=fermi_level,
                                temperature=temperature,
                                **eform_kwargs)
        
        conc = n * fermi_dirac(eform,temperature) # maxwell_boltzmann(eform,temperature) # 
        return conc


    def formation_energy(self,
                        vbm=0,
                        chemical_potentials=None,
                        fermi_level=0,
                        temperature=0,
                        **kwargs):
        """
        Compute the formation energy of the defect.
        If `formation_energy_function` is set, the custom function is called, 
        otherwise, the formation energy is computed as:

        Ef = E_D - E_B + q(eVBM + fermi_level) + Ecorr - sum_i [(ni(D) - ni(B))* mu_i]

        where:

        - E_D is the energy of the defective cell
        - E_B is the energy of the pristine (bulk) cell
            Note: E_D - E_B is `self.energy_diff`
        - eVBM is the valence band maximum energy
        - fermi_level is the chemical potential of electrons
        - Ecorr are correction terms
        - ni are the number of particles in the defective and pristine cells
        - mu_i are the chemical potentials of the elements.

        A custom function can be set when initializing the `DefectEntry` or by using the
        'set_formation_energy_function` method. Use `reset_formation_energy_function`
        to restore the default behaviour.
        If a custom function is given, the input must have the same args as this function,
        with the possibility to add more kwargs. 

        Parameters
        ----------
        vbm : float
            Valence band maximum of bulk calculation in eV
        chemical_potentials : dict
            Chemical potentials of the elements involved in the defect.
        fermi_level : float
            Fermi level in eV (with respect to the VBM).
        temperature : float
            Temperature in Kelvin. If a custom function is not passed, this parameter has no effect.
        kwargs : dict
            Kwargs to pass to custom function.
        
        Returns
        -------
        formation_energy : float
            Formation energy in eV.

        """
        if self._formation_energy_function:
            return self.formation_energy_function(self,
                                                vbm=vbm,
                                                chemical_potentials=chemical_potentials,
                                                fermi_level=fermi_level,
                                                temperature=temperature,
                                                **kwargs)
            
        formation_energy = (self.energy_diff + self.charge*(vbm+fermi_level) + 
                       sum([ self.corrections[correction_type]  for correction_type in self.corrections ]) 
                        ) 
        
        if chemical_potentials:
            chempot_correction = -1 * sum([self.delta_atoms[el]*chemical_potentials[el] for el in self.delta_atoms])
        else:
            chempot_correction = 0
            
        formation_energy = formation_energy + chempot_correction
        
        return formation_energy
    
    
    def relaxation_volume(self,stress_bulk,bulk_modulus,stress_defect=None,corrections={}):
        """
        Calculate relaxation volume from stresses.
        Stress of defect calculation needs to be provided either directly or in data dict with "stress" key.

        Parameters
        ----------
        stress_bulk : np.array
            Stresses from bulk calculation in kbar (units of VASP output)
        bulk_volume : float
            Cell volume of bulk calculation in A°^3.
        bulk_modulus : float
            Bulk modulus in GPa.
        stress_defect : np.array
            Stresses from defect calculation in kbar (units of VASP output)
        corrections : bool
            Add correction terms to the residual stress tensor.
            
        Returns
        -------
        rel_volume : float
            Relaxation volume in A°^3.

        """
        if not stress_defect:
            if 'stress' in self.data.keys():
                stress_defect = self.data['stress']
            else:
                raise ValueError('Stress of defect calculation needs to be provided, either directly or in data dict with "stress" key.')
        
        return get_relaxation_volume(stress_defect=stress_defect,
                                    stress_bulk=stress_bulk,
                                    bulk_volume=self.defect.bulk_volume,
                                    bulk_modulus=bulk_modulus,
                                    corrections=corrections)





def _get_computed_entry_from_path(path,**kwargs):
    """
    Get Pymatgen's ComputedEntry object from VASP calculation path with additional parameters for defect entries.
    Pass kwargs to Vasprun.get_computed_entry.
    """
    from pymatgen.io.vasp.outputs import Vasprun
    vasprun_defect = os.path.join(path,'vasprun.xml')
    if kwargs:
        if 'data' in kwargs.keys(): # computed entry kwarg and list member are called the same
            if 'parameters' not in kwargs['data']:
                kwargs['data'].append('parameters')
        else:
            kwargs['data'] = ['parameters']
    else:
        kwargs = {'data':['parameters']}     
    return Vasprun(vasprun_defect,parse_dos=False,parse_eigen=False,parse_potcar_file=False).get_computed_entry(**kwargs)


def fermi_dirac(E,T):
    """
    Returns the defect occupation as a function of the formation energy,
    using the Fermi-Dirac distribution with chemical potential equal to 0. 

    Parameters
    ----------
    E : float
        Energy in eV
    T : float
        Temperature in Kelvin.
    """
    from scipy.special import expit
    exponent = E/(kb*T)
    return expit(-exponent)


def maxwell_boltzmann(E, T, clip=True):
    """
    Maxwell-Boltzmann distribution function.
    Can be clipped to prevent divergence.

    Parameters
    ----------
    E : float
        Energy in eV.
    fermi : float
        Fermi level in eV.
    T : float
        Temperature in kelvin.
    clip : bool
        Clip exponential factor to 700 to avoid divergence, returns 1e304.

    Returns
    -------
    occupation : float
        Maxwell-Boltzmann occupation probability at energy E.

    """
    factor = -E / (kb*T)
    if clip:
        factor = np.clip(factor,None,700)
    return np.exp(factor)


