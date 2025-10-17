#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr  3 14:08:42 2023

@author: villa
"""
import importlib
import warnings
from abc import ABCMeta, abstractmethod, abstractproperty
from monty.json import MSONable
import importlib

from pymatgen.core.composition import Composition
from pymatgen.core.sites import PeriodicSite
from pymatgen.symmetry.analyzer import SpacegroupAnalyzer

from .tools.structure import is_site_in_structure, is_site_in_structure_coords



class Defect(MSONable,metaclass=ABCMeta): #MSONable contains as_dict and from_dict methods
    """
    Abstract class for a single point defect
    """

    def __init__(self, 
                specie=None, 
                defect_site=None,
                bulk_structure=None,
                charge=None,
                multiplicity=None,
                bulk_volume=None,
                label=None): 
        """
        Base class for defect objets.

        Parameters
        ----------
        specie : str
            Defect element symbol.
        defect_site : Site
            Pymatgen Site object of the defect.
        bulk_structure : Structure
            Pymatgen Structure without defects.
        charge : int or float
            Charge of the defect.
        multiplicity : int
            Multiplicity of defect within the simulation cell.
        bulk_volume : float
            Volume of bulk cell in A°^3.
        label : str
            Defect label.

        """
        if  specie:
            self._specie = specie
        elif defect_site:
            self._specie = defect_site.specie.symbol
        else:
            raise ValueError('Either defect species symbol or defect Site have to be provided')
        self._defect_site = defect_site
        self._bulk_structure = bulk_structure
        self._charge = charge
        self._multiplicity = multiplicity
        self._bulk_volume = bulk_volume
        self._label = label


    def __repr__(self):
        string = f'Defect: type={self.type}, species={self.specie}'
        if self.charge:
            string += f', charge={self.charge}'
        if self.label:
            string += f', label={self.label}'
        if self._defect_site:
            string +=  ", site= {}".format(self.site.frac_coords)
        return string
    
    def __print__(self):
        return self.__repr__()
    
    def __iter__(self):
        """
        Dummy iterable for integration with defect complexes
        """
        return [self].__iter__()

    @staticmethod
    def from_string(string, **kwargs):
        if '(' in string:
            name,label = string.split('(')
            label = label.strip(')')
        else:
            name = string
            label=None
        nsplit = name.split('_')
        ntype = nsplit[0]
        el = nsplit[1]
        bulk_specie = None
        if ntype=='Vac':
            dtype = 'Vacancy'
            dspecie = el
        elif ntype=='Int':
            dtype = 'Interstitial'
            dspecie = el
        elif ntype=='Sub':
            dtype = 'Substitution'
            dspecie = el
            el_bulk = nsplit[3]
            bulk_specie = el_bulk
        elif ntype=='Pol':
            dtype = 'Polaron'
            dspecie = el

        module = importlib.import_module(Defect.__module__)
        defect_class = getattr(module,dtype)
        kwargs.update({
            'specie':dspecie,
            'label': label
            })
        if dtype=='Substitution':
            kwargs['bulk_specie'] = bulk_specie

        return defect_class(**kwargs)
            

    @property
    def bulk_structure(self):
        """
        Structure without defects.
        """
        if self._bulk_structure:
            return self._bulk_structure
        else:
            warnings.warn('Bulk structure is not stored in Defect object')

    @property
    def bulk_volume(self):
        """
        Volume of bulk cell in A°^3.
        """
        if self._bulk_volume:
            return self._bulk_volume
        elif self.bulk_structure:
            return self.bulk_structure.volume
        else:
            warnings.warn('Neither bulk structure nor the bulk cell volume were assigned')
    
    @property
    def charge(self):
        """
        Charge of the defect.
        """
        if self._charge is None:
            warnings.warn('Charge was not assigned to defect object. Use set_charge to assign it.')
        else:
            return self._charge
     
    @abstractproperty
    def defect_composition(self):
        """
        Defect composition as a Composition object
        """
        return

    @abstractproperty
    def defect_site_index(self):
        """
        Index of the defect site in the structure
        """
        return
    
    @property
    def defects(self): # dummy property to integrate Defect and DefectComplex
        return [self]
    
    @property
    def specie(self):
        """
        Defect species.
        """
        return self._specie
    
    @property
    def defect_structure(self):
        """
        Structure of the defect.
        """
        return self.generate_defect_structure() 
    
    @property
    def type(self):
        """
        Defect type.
        """
        return self.__class__.__name__
    
    @property
    def delta_atoms(self):
        """
        Dictionary with defect element symbol as keys and difference in particle number 
        between defect and bulk structure as values
        """
        return

    @abstractmethod
    def get_multiplicity(self):
        return 

    @property
    def label(self):
        """
        Defect label.
        """
        return self._label

    @property
    def multiplicity(self):
        """
        Multiplicity of a defect site within the structure
        """
        return self._multiplicity
      
    @abstractproperty  
    def name(self):
        """
        Name of the defect.
        """
        return

    @property
    def site(self):
        """
        Defect position as a Site object
        """
        if self._defect_site:
            return self._defect_site
        else:
            warnings.warn('Site is not stored in Defect object')
   
    @property
    def site_concentration_in_cm3(self):
        """
        Site concentration (multiplicity/volume) expressed in cm^-3.
        """
        return self.multiplicity * 1e24 / self.bulk_volume 
   
    @property  
    def symbol(self):
        """
        Latex formatted name of the defect.
        """
        return 

    @property
    def symbol_with_charge(self):
        """
        Name in latex format with charge written as a number.
        """
        return format_legend_with_charge_number(self.symbol,self.charge)
    
    @property
    def symbol_with_charge_kv(self):
        """
        Name in latex format with charge written with Kröger and Vink notation.
        """
        return format_legend_with_charge_kv(self.symbol,self.charge)
    
    def set_bulk_volume(self, new_volume):
        """
        Sets the volume of bulk cell
        """
        self._bulk_volume = new_volume
        return

    def set_charge(self, new_charge=0.0):
        """
        Sets the charge of the defect.
        """
        self._charge = new_charge
        return
    
    def set_label(self,new_label):
        """
        Sets the label of the defect
        """
        self._label = new_label
        return

    def set_multiplicity(self, new_multiplicity=None):
        """
        Sets the Multiplicity of the defect.
        If `new_multiplicity` is not provided it is determined 
        with `self.get_multiplicity`
        """
        if new_multiplicity is None:
            new_multiplicity = self.get_multiplicity()
        self._multiplicity = new_multiplicity
        return
        
        
class Vacancy(Defect):
    
    """
    Subclass of Defect for single vacancies.
    """
    @property
    def defect_composition(self):
        """
        Composition of the defect.
        """
        temp_comp = self.bulk_structure.composition.as_dict()
        temp_comp[str(self.site.specie)] -= 1
        return Composition(temp_comp)
    
    @property
    def defect_site_index(self):
        """
        Index of the defect site in the bulk structure
        """
        _,index = is_site_in_structure_coords(self.site, self.bulk_structure)
        return index
    
    @property
    def delta_atoms(self):
        """
        Dictionary with element symbol as keys and difference in particle number 
        between defect and bulk structure as values
        """
        return {self.specie:-1}
    
    def generate_defect_structure(self,bulk_structure=None,defect_site_index=None):
        """
        Generate a structure containing the defect starting from a bulk structure.

        Parameters
        ----------
        bulk_structure : Structure
            Bulk Structure. If not provided `self.bulk_structure` is used.
        defect_site_index : Structure
            Index of the defect site in the bulk structure. If not provided 
            `self.defect_site_index` is used.

        Returns
        -------
        structure : Structure
            Structure containing the defect.

        """
        bulk_structure = bulk_structure if bulk_structure else self.bulk_structure
        defect_site_index = defect_site_index if defect_site_index else self.defect_site_index
        defect_structure = bulk_structure.copy()
        defect_structure.remove_sites([defect_site_index])
        return defect_structure
    
    def get_multiplicity(self,**kwargs):
        """
        Get multiplicity of the defect in the structure.

        Parameters
        ----------
        **kwargs : dict
            Kwargs to pass to `SpacegroupAnalyzer` ("symprec", "angle_tolerance")
        """
        sga = SpacegroupAnalyzer(self.bulk_structure,**kwargs)
        symmetrized_structure = sga.get_symmetrized_structure()
        equivalent_sites = symmetrized_structure.find_equivalent_sites(self.site)
        return len(equivalent_sites)

    @property
    def name(self):
        """
        Name of the defect.
        """
        name = f"Vac_{self.specie}"
        if self.label:
            name += f'({self.label})'
        return name
    
    @property
    def symbol(self):
        symbol = "$V_{%s}$" %self.specie
        if self.label:
            symbol += '(%s)' %self.label
        return symbol 
        
        
    
class Substitution(Defect):
    """
    Subclass of Defect for substitutional defects.
    """

    def __init__(self,
                specie=None,
                bulk_specie=None,
                defect_site=None,
                bulk_structure=None,
                charge=None,
                multiplicity=None,
                bulk_volume=None,
                label=None,
                site_in_bulk=None):
        """
        Parameters
        ----------
        site_in_bulk : PeriodicSite
            Original Site in bulk structure were substitution took place.

        """
        super().__init__(specie=specie,
                        defect_site=defect_site,
                        bulk_structure=bulk_structure,
                        charge=charge,
                        multiplicity=multiplicity,
                        bulk_volume=bulk_volume,
                        label=label)
        if bulk_specie:
            self._bulk_specie = bulk_specie 
        elif site_in_bulk:
            self._bulk_specie = site_in_bulk.specie.symbol
        else:
            raise ValueError('Either bulk species or substitution site in bulk structure have to be provided')
        
        self._site_in_bulk = site_in_bulk 


    @property
    def bulk_specie(self):
        return self._bulk_specie

    @property  
    def defect_composition(self):
        """
        Composition of the defect.
        """
        defect_index = self.defect_site_index
        comp = self.bulk_structure.composition.as_dict()
        if str(self.specie) not in comp.keys():
            comp[str(self.specie)] = 0
        comp[str(self.specie)] += 1
        comp[str(self.bulk_structure[defect_index].specie)] -= 1
        return Composition(comp)

    @property
    def defect_site_index(self):
        """
        Index of the defect site in the bulk structure.
        """
        return self.bulk_structure.index(self.site_in_bulk)

    @property
    def delta_atoms(self):
        """
        Dictionary with element symbol as keys and difference in particle number 
        between defect and bulk structure as values
        """
        return {self.specie:1, self.bulk_specie:-1}
    
    def generate_defect_structure(self,bulk_structure=None,defect_site_index=None):
        """
        Generate a structure containing the defect starting from a bulk structure.

        Parameters
        ----------
        bulk_structure : Structure
            Bulk Structure. If not provided `self.bulk_structure` is used.
        defect_site_index : Structure
            Index of the defect site in the bulk structure. If not provided 
            `self.defect_site_index` is used.

        Returns
        -------
        structure : Structure
            Structure containing the defect.
        """
        bulk_structure = bulk_structure if bulk_structure else self.bulk_structure
        defect_site_index = defect_site_index if defect_site_index else self.defect_site_index
        defect_structure = bulk_structure.copy()
        defect_structure.replace(defect_site_index,self.specie)  
        return defect_structure

    def get_multiplicity(self,**kwargs):
        """
        Get multiplicity of the defect in the structure

        Parameters
        ----------
        **kwargs : dict
            Kwargs to pass to `SpacegroupAnalyzer` ("symprec", "angle_tolerance")
        """
        sga = SpacegroupAnalyzer(self.bulk_structure,**kwargs)
        symmetrized_structure = sga.get_symmetrized_structure()
        equivalent_sites = symmetrized_structure.find_equivalent_sites(self.site_in_bulk)
        return len(equivalent_sites)

    def get_site_in_bulk(self):
        try:
            site = min(
                self.bulk_structure.get_sites_in_sphere(self.site.coords, 0.5, include_index=True),
                           key=lambda x: x[1])  
            # there's a bug in pymatgen PeriodicNeighbour.from_dict and the specie attribute, get PeriodicSite instead
            site = PeriodicSite(site.species, site.frac_coords, site.lattice)
            return site
        except:
            return ValueError("""No equivalent site has been found in bulk, defect and bulk structures are too different.\
Try using the unrelaxed defect structure or provide bulk site manually""")

    @property 
    def name(self):
        """
        Name for this defect.
        """
        name = f'Sub_{self.specie}_on_{self.bulk_specie}'
        if self.label:
            name += f'({self.label})'
        return name   
    
    @property
    def symbol(self):
        symbol = "$%s_{%s}$" %(self.specie, self.bulk_specie)   
        if self.label:
            symbol += '(%s)' %self.label
        return symbol 
    
    @property
    def site_in_bulk(self):
        if self._site_in_bulk:
            return self._site_in_bulk
        else:
            return self.get_site_in_bulk()


    
class Interstitial(Defect):
    """
    Subclass of Defect for interstitial defects.
    """
    
    @property
    def defect_composition(self):
        """
        Composition of the defect.
        """
        temp_comp = self.bulk_structure.composition.as_dict()
        temp_comp[str(self.site.specie)] += 1
        return Composition(temp_comp)
    
    @property
    def defect_site_index(self):
        """
        Index of the defect site in the defect structure
        """
        is_site,index = is_site_in_structure(self.site, self.defect_structure)
        return index  # more flexibility with is_site_in_structure
       
    @property
    def delta_atoms(self):
        """
        Dictionary with element symbol as keys and difference in particle number 
        between defect and bulk structure as values
        """
        return {self.specie:1}
    
    def generate_defect_structure(self,bulk_structure=None):
        """
        Generate a structure containing the defect starting from a bulk structure.

        Parameters
        ----------
        bulk_structure : Structure
            Bulk Structure. If not provided `self.bulk_structure` is used.

        Returns
        -------
        structure : Structure
            Structure containing the defect.
        """
        bulk_structure = bulk_structure if bulk_structure else self.bulk_structure
        defect_structure = bulk_structure.copy()
        defect_structure.append(self.site.species,self.site.frac_coords)
        return defect_structure
        

    def get_multiplicity(self):
        raise NotImplementedError('Multiplicity calculation not implemented for Interstitial')

    @property
    def name(self):
        """
        Name of the defect.
        """
        name = f"Int_{self.specie}"
        if self.label:
            name += f'({self.label})'
        return name

    @property
    def symbol(self):
        symbol = "$%s_i$" %(self.specie)     
        if self.label:
            symbol += '(%s)' %self.label
        return symbol    
        
      
class Polaron(Defect):
    """
    Subclass of Defect for polarons.
    """   
    
    def __init__(self,
                specie=None,
                defect_site=None,
                bulk_structure=None,
                charge=None,
                multiplicity=None,
                label=None,
                bulk_volume=None,
                defect_structure=None):
        """
        defect_structure: Structure
            Structure containing the polaron. If not provided the site index is searched 
            in the bulk structure, and `defect_structure` is set equal to the bulk structure.
        """
        super().__init__(specie=specie,
                        defect_site=defect_site,
                        bulk_structure=bulk_structure,
                        charge=charge,
                        multiplicity=multiplicity,
                        bulk_volume=bulk_volume,
                        label=label)
        self._defect_structure = defect_structure
        
        
    @property
    def defect_composition(self):
        """
        Composition of the defect.
        """
        return self.bulk_structure.composition
    
    @property
    def defect_site_index(self):
        """
        Index of the defect site in the structure.
        """
        return self.defect_structure.index(self.site)
        
    @property
    def delta_atoms(self):
        """
        Dictionary with delement as keys and difference in particle number 
        between defect and bulk structure as values.
        """
        return {}
    
    def generate_defect_structure(self,bulk_structure=None):
        """
        Structure containing the polaron. If not provided the site index is searched 
        in the bulk structure, and `defect_structure` is set equal to the bulk structure.
        """
        if self._defect_structure:
            return self._defect_structure
        else:
            bulk_structure = bulk_structure if bulk_structure else self.bulk_structure
            return bulk_structure  
        
        
    def get_multiplicity(self,**kwargs):
        """
        Get multiplicity of the defect in the structure.

        Parameters
        ----------
        **kwargs : dict
            Kwargs to pass to `SpacegroupAnalyzer` ("symprec", "angle_tolerance")
        """
        sga = SpacegroupAnalyzer(self.bulk_structure,**kwargs)
        symmetrized_structure = sga.get_symmetrized_structure()
        equivalent_sites = symmetrized_structure.find_equivalent_sites(self.site)
        return len(equivalent_sites)

    @property
    def name(self):
        """
        Name of the defect.
        """
        name = f"Pol_{self.specie}"
        if self.label:
            name += f'({self.label})'
        return name
    
    @property
    def symbol(self):
        symbol = "$%s_{%s}$" %(self.specie,self.specie)
        if self.label:
            symbol += '(%s)' %self.label
        return symbol   
    
    
class DefectComplex(MSONable,metaclass=ABCMeta):

    def __init__(self,
                defects,
                bulk_structure=None,
                charge=None,
                multiplicity=None,
                bulk_volume=None,
                label=None):
        """
        Class to describe defect complexes

        Parameters
        ----------
        defects : list
            List of Defect objects.
        bulk_structure : Structure
            Pymatgen Structure of the bulk material.
        charge : int or float
            Charge of the defect.
        multiplicity : int
            Multiplicity of the defect.
        """
        self._defects = defects
        self._bulk_structure = bulk_structure
        self._charge = charge
        self._multiplicity = multiplicity
        self._bulk_volume = bulk_volume
        self._label = label


    def __repr__(self):
        string = 'DefectComplex: ['
        for df in self.defects:
            string += f' {df.__repr__()},'
        string += ' ] '
        return string
    
    def __str__(self):
        return self.__repr__()
    
    def __iter__(self):
        return self.defects.__iter__()
    
    @staticmethod
    def from_string(string, **kwargs):
        """
        Get `DefectComplex` object from string.
        """
        names = string.split('-')
        defects = [Defect.from_string(n) for n in names]
        return DefectComplex(defects=defects, **kwargs)
    

    @property
    def bulk_structure(self):
        """
        Structure without defects.
        """
        if self._bulk_structure:
            return self._bulk_structure
        else:
            warnings.warn('Bulk structure is not stored in Defect object')

    @property
    def bulk_volume(self):
        """
        Volume of bulk cell in A°^3.
        """
        if self._bulk_volume:
            return self._bulk_volume
        elif self.bulk_structure:
            return self.bulk_structure.volume
        else:
            warnings.warn('Neither bulk structure nor the bulk cell volume were assigned')
    
    @property
    def charge(self):
        """
        Charge of the defect.
        """
        if self._charge is None:
            warnings.warn('Charge was not assigned to defect object. Use set_charge to assign it.')
        else:
            return self._charge

    @property
    def defects(self):
        """
        List of single defects consituting the complex.
        """
        return self._defects

    @property
    def defect_composition(self):
        """
        Composition of defect structure.
        """
        return self.defect_structure.composition
        
    @property
    def defect_names(self):
        """
        List of names of the single defects.
        """
        return [d.name for d in self.defects]

    @property
    def defect_structure(self):
        """
        Structure containing the defect.
        """
        return self.generate_defect_structure()

    @property
    def type(self):
        """
        Defect type.
        """
        return self.__class__.__name__
    
    @property
    def delta_atoms(self):
        """
        Dictionary with Element as keys and particle difference between defect structure
        and bulk structure as values.
        """
        da_global = None
        for d in self.defects:
            da_single = d.delta_atoms
            if da_global is None:
                da_global = da_single.copy()
            else:
                for e in da_single:
                    prec = da_global[e] if e in da_global.keys() else 0
                    da_global[e] = prec + da_single[e]       
        return da_global 

    def generate_defect_structure(self,bulk_structure=None):
        """
        Generate a structure containing the defect starting from a bulk structure.
        If not provided `self.bulk_structure` is used.
        """
        bulk_structure = bulk_structure if bulk_structure else self.bulk_structure
        structure = bulk_structure.copy()
        for df in self.defects:
            df_structure = df.generate_defect_structure(structure)
            structure = df_structure.copy()
        return structure

    def get_multiplicity(self):
        raise NotImplementedError('Not implemented for DefectComplex')

    @property
    def label(self):
        """
        Defect label.
        """
        return self._label

    @property
    def multiplicity(self):
        """
        Multiplicity of a defect site within the structure
        """
        return self._multiplicity

    @property
    def name(self):
        """
        Name of the defect. Behaves like a string with additional attributes.
        """
        name = '-'.join([df.name for df in self.defects])
        if self.label:
            name += f'({self.label})'
        return name
    
    @property
    def site_concentration_in_cm3(self):
        """
        Site concentration (multiplicity/volume) expressed in cm^-3.
        """
        return self.multiplicity * 1e24 / self.bulk_volume 
    
    @property
    def sites(self):
        """
        Site objects of single defects.
        """
        return [d.site for d in self.defects]
    
    @property
    def symbol(self):
        """
        Latex formatted name of the defect.
        """
        symbol = '-'.join([df.symbol for df in self.defects])  #'-'.join([df.symbol.split('(')[0] for df in self.defects]) without single df labels
        if self.label:
            symbol = symbol + '(%s)'%self.label 
        return symbol

    @property
    def symbol_with_charge(self):
        """
        Name in latex format with charge written as a number.
        """
        return format_legend_with_charge_number(self.symbol,self.charge)
    
    @property
    def symbol_with_charge_kv(self):
        """
        Name in latex format with charge written with kroger and vink notation.
        """
        return format_legend_with_charge_kv(self.symbol,self.charge)


    def set_charge(self, new_charge):
        """
        Sets the charge of the defect.
        """
        self._charge = new_charge
        return    

    def set_label(self,new_label):
        """
        Sets the label of the defect
        """
        self._label = new_label
        return

    def set_multiplicity(self, new_multiplicity):
        """
        Sets the charge of the defect.
        """
        self._multiplicity = new_multiplicity
        return
    


def get_defect_from_string(string, **kwargs):
    """
    Get defect object from a string (`Defect` or `DefectComplex`).
    """
    if '-' in string:
        return DefectComplex.from_string(string, **kwargs)
    else:
        return Defect.from_string(string, **kwargs)
   

def format_legend_with_charge_number(label,charge):
    """
    Get label in latex format with charge written as a number.
   
    Parameters
    ----------
    label : str
        Original name of the defect.
    charge : int or float
        Charge of the defect. Floats are converted to integers.
    
    Returns
    -------
    string : str
        Formatted defect name with charge.
    """
    s = label
    charge = int(charge)
    if charge > 0:
        q = '+'+str(charge)
    elif charge == 0:
        q = '\;' + str(charge)
    else:
        q = str(charge)
    return s + '$^{' + q + '}$'


def format_legend_with_charge_kv(label,charge):
    """
    Get label in latex format with charge written with Kröger and Vink notation.

    Parameters
    ----------
    label : str
        Original name of the defect.
    charge : int or float
        Charge of the defect. Floats are converted to integer.

    Returns
    -------
    string : str
        Formatted defect name with Kröger and Vink notation.
    """
    mod_label = label + '$'
    charge = int(charge)
    if charge < 0:
        for i in range(0,abs(charge)):
            if i == 0:
                mod_label = mod_label + "^{"
            mod_label = mod_label + "'"
        mod_label = mod_label + "}"
    elif charge == 0:
        mod_label = mod_label + "^{x}"
    elif charge > 0:
        for i in range(0,charge):
            if i == 0:
                mod_label = mod_label + "^{"
            mod_label = mod_label + "°"
        mod_label = mod_label + "}"
    
    mod_label = mod_label + "$"
    
    return mod_label

    
def get_delta_atoms(structure_defect,structure_bulk):
    """
    Build delta_atoms dictionary starting from Pymatgen Structure objects.

    Parameters
    ----------
    structure_defect : Structure
        Defect structure.
    structure_bulk : Structure
        Bulk structure.

    Returns
    -------
    delta_atoms : dict
        Dictionary with Element as keys and delta n as values.
    """
    comp_defect = structure_defect.composition
    comp_bulk = structure_bulk.composition
        
    return get_delta_atoms_from_comp(comp_defect, comp_bulk)


def get_delta_atoms_from_comp(comp_defect,comp_bulk):
    """
    Build delta_atoms dictionary starting from Composition objects.

    Parameters
    ----------
    comp_defect : Composition
        Defect structure.
    comp_bulk : Composition
        Bulk structure.

    Returns
    -------
    delta_atoms : dict
        Dictionary with Element as keys and delta n as values.
    """
    delta_atoms = {}
    for el,n in comp_defect.items():
        nsites_defect = n
        nsites_bulk = comp_bulk[el] if el in comp_bulk.keys() else 0
        delta_n = nsites_defect - nsites_bulk
        if delta_n != 0:
            delta_atoms[el] = delta_n
        
    return delta_atoms    
    
    