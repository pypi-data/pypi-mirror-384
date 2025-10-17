#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jun  2 16:39:01 2025

@author: lorenzo
"""

import numpy as np
from pandas import DataFrame
import matplotlib.pyplot as plt
from pymatgen.core.periodic_table import Element
from pymatgen.core.composition import Composition
from pymatgen.symmetry.groups import SpaceGroup
from pymatgen.analysis.phase_diagram import GrandPotentialPhaseDiagram, PDPlotter

from ..tools.utils import format_composition
from .core import Chempots


def _get_composition_object(comp):
    if type(comp) == str:
        return Composition(comp)
    elif type(comp) == Composition:
        return comp
    else:
        raise ValueError('Composition needs to be str or pymatgen Composition')
        

class PDHandler:
    
    def __init__(self,phase_diagram):
        """
        Class to generate and handle Pymatgen phase diagram more rapidly.

        Parameters
        ----------
        phase_diagram : PhaseDiagram
            Pymatgen PhaseDiagram object

        """
        self.pd = phase_diagram 
        self.mu_refs = self.get_chempots_reference()


    def calculate_single_chempot(self,comp,chempots_ref):
        """
        Calculate referenced chemical potential in a given composition and given
        the chemical potentials of the other elements.

        Parameters
        ----------
        comp : str or Composition
            Compositions of the phase.
        chempots_ref : Dict
            Dictionary with element symbols as keys and respective chemical potential as value ({el:chempot}).
            The chemical potentials used here are the ones relative to the reference (delta_mu).

        Returns
        -------
        mu : float
            Chemical potential.

        """        
        comp = _get_composition_object(comp)
        form_energy = self.get_formation_energy_from_stable_comp(comp)
        mu = form_energy
        for el,coeff in comp.items():
            if el.symbol in chempots_ref:
                mu += -1*coeff * chempots_ref[el.symbol]
            else:
                factor = coeff
        
        return mu/factor


    def get_all_boundaries_chempots(self,comp):
        """
        Get chemical potentials at the corners of the stability ta given composition.

        Parameters
        ----------
        comp : str or Composition

        Returns
        -------
        chempots : Chempots
            Chempots object.

        """
        comp = _get_composition_object(comp)
        chempots_pmg = self.pd.get_all_chempots(comp)
        for r,mu in chempots_pmg.items():
            chempots_pmg[r] = {k:v.item() for k,v in mu.items()} # convert from np.float64
        chempots = {r:Chempots.from_pmg_elements(mu) for r,mu in chempots_pmg.items()}
        return chempots

        
    def get_chempots_reference(self):
        """
        Gets elemental reference compounds and respective e.p.a with Pymatgen el_ref attribute in PhaseDiagram class.

        Returns
        -------
        chempots : Chempots
            Chempots object.

        """
        chempots_ref = {}
        pd = self.pd
        for el in pd.el_refs:
            chempots_ref[el] = pd.el_refs[el].energy_per_atom
        chempots_ref = {k: v for k, v in sorted(chempots_ref.items(), key=lambda item: item[0])}
        return Chempots.from_pmg_elements(chempots_ref)
       

    def get_dataframe(self):
        """
        Generate pandas DataFrame with columns 'Composition, Structure, Formation energy'.
        To display a string for 'Structure' the entry needs to be a ComputedStructureEntry (see pymatgen docs).
        """
        phases = []
        for e in self.pd.stable_entries:
            d = {}
            d['Composition'] = format_composition(e.composition.reduced_formula)
            sg = SpaceGroup(e.structure.get_space_group_info()[0])
            crystal_system, sg_string = sg.crystal_system , sg.to_latex_string()
            if e.__class__.__name__ == 'ComputedStructureEntry':
                d['Structure'] = f'{crystal_system.capitalize()} ({sg_string})'
            else:
                d['Structure'] = None
            d['Formation energy p.a (eV)'] = np.around(self.pd.get_form_energy_per_atom(e),decimals=2)
            phases.append(d)
        df = DataFrame(phases)
        return df

        
    def get_entries_from_comp(self,comp):
       """
       Get a list of entries corrisponding to the target composition.
       
       Parameters
       ----------
       comp : str or Composition
            Composition.

       Returns
       -------
       target_entries : list
        List of Pymatgen PDEntry objects.

       """
       comp = _get_composition_object(comp)
       target_entries=[]
       pd = self.pd
       for e in pd.all_entries:
           if e.composition.reduced_composition == comp:
               target_entries.append(e)
       if target_entries != []:
           return target_entries
       else:
           raise ValueError('No entry has been found for target composition:%s' %comp.reduced_formula)


    def get_energies_from_comp(self,comp):
        """
        Get dictionary of energies for all entries of a given reduced composition.

        Parameters
        ----------
        comp : str or Composition
            Composition.

        Returns
        -------
        form_energies : dict
            Dictionary with PDEntry objects as keys and Energies as values.

        """
        comp = _get_composition_object(comp)
        pd = self.pd
        energies = {}
        for e in self.get_entries_from_comp(comp):
            factor = e.composition.get_reduced_composition_and_factor()[1]
            energies[e] = e.energy/factor
        return energies
            

    def get_energy_from_stable_comp(self,comp):
        """
        Get energy of a target stable composition.

        Parameters
        ----------
        comp : str or Composition
            Composition.

        Returns
        -------
        energy : float
            Energy in eV.

        """
        comp = _get_composition_object(comp)
        pd = self.pd
        entry = self.get_stable_entry_from_comp(comp)
        factor = entry.composition.get_reduced_composition_and_factor()[1]
        return entry.energy/factor


    def get_formation_energies_from_comp(self,comp):
        """
        Get dictionary of formation energies for all entries of a given reduced composition.

        Parameters
        ----------
        comp : str or Composition
            Composition.

        Returns
        -------
        form_energies : dict
            Dictionary with PDEntry objects as keys and formation energies in eV as values.
        
        """
        comp = _get_composition_object(comp)
        pd = self.pd
        form_energies = {}
        for e in self.get_entries_from_comp(comp):
            factor = e.composition.get_reduced_composition_and_factor()[1]
            form_energies[e] = pd.get_form_energy(e)/factor
        return form_energies
            

    def get_formation_energy_from_stable_comp(self,comp):
        """
        Get formation energy of a target stable composition.

        Parameters
        ----------
        comp : str or Composition
            Composition.

        Returns
        -------
        form_energy : float
            Formation energy in eV (float).

        """
        comp = _get_composition_object(comp)
        pd = self.pd
        entry = self.get_stable_entry_from_comp(comp)
        factor = entry.composition.get_reduced_composition_and_factor()[1]
        return pd.get_form_energy(entry)/factor
        

    def get_phase_boundaries_chempots(self,comp,chempot_ref):
        """
        Given a composition and a fixed chemical potential, this function analises the composition of the boundary phases
        and the associated chemical potentials at the boundaries. Only works for 3 component PD.

        Parameters
        ----------
        comp : str or Composition
            Composition of the phase you want to get the chemical potentials at the boundary.
        chempot_ref : dict
            Dictionary with fixed element symbol as key and respective chemical potential as value ({el:chempot}).
            The chemical potential here is the referenced value. 

        Returns
        -------
        chempots : dict
            Dictionary with compositions at the boundaries as keys and delta chemical potentials as value.

        """       
        comp = _get_composition_object(comp)
        chempots = {}
        comp1,comp2 = self.get_phase_boundaries_compositions(comp, chempot_ref)
        
        boundary = '-'.join([comp1.reduced_formula,comp.reduced_formula])
        chempots[boundary] = self.solve_phase_boundary_chempots(comp1, comp, chempot_ref)
        
        boundary = '-'.join([comp.reduced_formula,comp2.reduced_formula])
        chempots[boundary] = self.solve_phase_boundary_chempots(comp, comp2, chempot_ref)
        
        return chempots      
                  
    
    def get_phase_boundaries_compositions(self,comp,chempot_ref):
        """
        Get compositions of phases in boundary of stability with a target composition given a fixed chemical potential 
        on one component. Currently only works for 3-component PD (to check). 
        Used Pymatgen GrandPotentialPhaseDiagram class. The fixed chemical potential is the referenced value that is
        converted in the global value for the analysis with the GrandPotentialPhaseDiagram class.

        Parameters
        ----------
        comp : str or Composition
            Target composition for which you want to get the bounday phases.
        chempot_ref : dict
            Dictionary with fixed element symbol as key and respective chemical potential as value ({el:chempot}).
            The chemical potential is the referenced value

        Returns
        -------
        comp1,comp2 : (Composition objects)
            Compositions of the boundary phases given a fixed chemical potential for one element.

        """
        comp = _get_composition_object(comp)
        chempot_ref = Chempots(chempot_ref)
        fixed_chempot = chempot_ref.get_absolute(self.mu_refs).to_pmg_elements()
        
        entries = self.pd.all_entries
        gpd = GrandPotentialPhaseDiagram(entries, fixed_chempot)
        stable_entries = gpd.stable_entries
        comp_in_stable_entries = False
        for e in stable_entries:
            if e.original_comp.reduced_composition == comp:
                comp_in_stable_entries = True
        if comp_in_stable_entries == False:
            raise ValueError('Target composition %s is not a stable entry for fixed chemical potential: %s' %(comp.reduced_formula,fixed_chempot))
        
        el = comp.elements[0]
        x_target = comp.get_wt_fraction(el)
        x_max_left = 0
        x_min_right = 1
        for e in stable_entries:
            c = e.original_comp
            if c != comp:
                x = c.get_wt_fraction(el)
                if x < x_target and x >= x_max_left:
                    x_max_left = x
                    comp1 = c
                if x > x_target and x <= x_min_right:
                    x_min_right = x
                    comp2 = c
        return comp1.reduced_composition,comp2.reduced_composition   
                  
                    
    def solve_phase_boundary_chempots(self,comp1,comp2,chempot_ref):
        """
        Given a fixed chemical potential, gets the values of the remaining two chemical potentials
        in the boundary between two phases (region where the two phases coexist). Only works for 3-component PD (to check).

        Given a phase P1 (formula AxByOz) and a phase P2 (formula AiBjOk) the chemical potentials have to satisfy the conditions:

        - form_energy(P1) = x*mu(A) + y*mu(B) +z*mu(O)
        - form_energy(P2) = i*mu(A) + j*mu(B) +k*mu(O)
        
        From these conditions the values of mu(A) and mu(B) are determined given a fixed value of mu(O).
        All of the chemical potentials used here are delta_mu, i.e. relative to the elemental phase(delta_mu(O) = mu(O) - mu_ref(O))

        Parameters
        ----------
        comp1,comp2 : str or Composition
            Compositions of the two phases at the boundary.
        chempot_ref : dict
            Dictionary with fixed element symbol as key and respective chemical potential as value ({el:chempot}). The chemical potential
            used here is the one relative to the reference (delta_mu).

        Returns
        -------
        chempots_boundary : dict
            Dictionary of chemical potentials.

        """
        comp1 = _get_composition_object(comp1)
        comp2 = _get_composition_object(comp2)
        chempots_boundary ={}
        chempot_ref = Chempots(chempot_ref)
        mu_fixed = chempot_ref.to_pmg_elements()
        for el,chempot in mu_fixed.items():
            el_fixed, mu_fixed = el, chempot
        e1 = self.get_formation_energy_from_stable_comp(comp1)
        e2 = self.get_formation_energy_from_stable_comp(comp2)
        
        coeff1 = []
        coeff2 = []
        # order of variables (mu) will follow the order of self.chempots_reference which is alphabetically ordered
        mu_refs = self.mu_refs.to_pmg_elements()
        for el in mu_refs:
            if el != el_fixed:
                if el not in comp1:
                    coeff1.append(0)
                else:
                    coeff1.append(comp1[el])
                if el not in comp2:
                    coeff2.append(0)
                else:
                    coeff2.append(comp2[el])                
        a = np.array([coeff1,coeff2])
        
        const1 = e1 - comp1[el_fixed]*mu_fixed if el_fixed in comp1 else e1 
        const2 = e2 - comp2[el_fixed]*mu_fixed if el_fixed in comp2 else e2
        b = np.array([const1,const2])
        x = np.linalg.solve(a, b)
        # output will follow the order given in input
        counter = 0
        for el in mu_refs:
            if el != el_fixed:
                chempots_boundary[el] = x[counter]
                counter += 1
        chempots_boundary[el_fixed] = mu_fixed        
        
        return Chempots.from_pmg_elements(chempots_boundary) 


    def get_plot(self,**kwargs):
        """
        Get plot with Pymatgen
        """
        PDPlotter(self.pd,show_unstable=0,backend='matplotlib').get_plot(**kwargs)
        return plt


    def get_stability_diagram(self,elements,figsize=None):
        """
        Method to get stability diagram with 'get_chempot_range_map_plot' method in pymatgen.

        Parameters
        ----------
        elements : list
            List with strings of the elements to be used as free variables.
        size : tuple
            New size in inches.

        Returns
        -------
        plt : 
            Matplotlib object.

        """
        pd = self.pd
        elements = [Element(el) for el in elements]
        PDPlotter(pd).get_chempot_range_map_plot(elements)
        if figsize:
            fig = plt.gcf()
            fig.set_size_inches(figsize[0],figsize[1])
        
        return plt


    def get_stable_entry_from_comp(self,comp):
        """
        Get the PDEntry of the stable entry of a target composition.

        Parameters
        ----------
        comp : str or Composition
            Composition.

        Returns
        -------
        entry : PDEntry
            Pymatgen PDEntry object.

        """
        comp = _get_composition_object(comp)
        target_entry=None
        pd = self.pd
        for e in pd.stable_entries:
            if e.composition.reduced_composition == comp:
                target_entry = e
                break
        if target_entry is not None:
            return target_entry
        else:
            raise ValueError('No stable entry has been found for target composition:%s' %comp.reduced_formula)
            
            
            
class StabilityDiagram:
    
    def __init__(self,phase_diagram=None,size=1):
        """
        Class with tools to add features to default PD plots generated by Pymatgen.

        Parameters
        ----------
        phase_diagram : PhaseDiagram
            Pymatgen PhaseDiagram object.
        size : float
            Multiplier for the size of the objects added in the plot.

        """
        self.pd = phase_diagram if phase_diagram else None
        self.pdh = PDHandler(phase_diagram) if phase_diagram else None
        self.size = size
        
    
    def add_points(self,points,size=1,label_size=1,color=[],edgecolor='k',label_color='k',linewidths=3,**kwargs):
        """
        Add points to plot representing reservoirs.

        Parameters
        ----------
        points : dict
            Dictionary with points labels as keys and tuples or list with coordinates as values.
        size : float
            Float multiplier for points size. Default is 1, which would yield a default size of 450*self.size
        label_size : float
            Float multiplier for labels size. Default is 1, which would yield a default size of 30*self.size
        color : str
            Color of filling of points
        edgecolor : str 
            Color of point edge
        label_color : str
            Color of labels
        linewidths : int
            line width of point edge
        kwargs : dict
            kwargs to pass to matplotlib `scatter` function.

        Returns
        -------
        plt : matplotlib
            Matplotlib object.

        """
        for p in points:
            plt.scatter(points[p][0],points[p][1], color=color, edgecolor=edgecolor, linewidths=linewidths, s=450*self.size*size,**kwargs)
            plt.text(points[p][0]+(0.1/self.size*label_size),points[p][1],p,size=30*self.size*label_size,color=label_color)
        return plt
    
    
    def add_constant_chempot_line(self, comp, variable_element, chempots_ref,**kwargs):
        """
        Add line of constant chemical potential (at a given composition) to the plot. Only works for 3 component PD.

        Parameters
        ----------
        comp : str or Composition
            Composition of the phase.
        variable_element : str
            Element chosen as indipendent variable.
        chempots_ref : dict
            Dictionary with fixed chemical potentials (values relative to reference phase). The format is {Element:chempot}.
        **kwargs : 
            kwargs passed to Matplotlib plot function.

        Returns
        -------
        plt : matlotlib
            Matplotlib object.

        """
        comp = _get_composition_object(comp)
        axes = plt.gca()
        xlim , ylim = axes.get_xlim() , axes.get_ylim()
        plt.xlim(xlim)
        plt.ylim(ylim)
        mu = np.arange(xlim[0]-1,xlim[1]+1,0.01)
        plt.plot(mu,self.constant_chempot_line(mu,comp,variable_element,chempots_ref),
                 linewidth= 4.5*self.size , **kwargs)
        return plt
    

    def add_heatmap(self,comp,elements,cbar_label='$\Delta\mu_{O}$',cbar_values=True,**kwargs):
        """
        Add heatmap that shows the value of the last chemical potential based on the values of the other two "free" 
        chemical potentials and the composition of interest. Currently works only for 3 component PDs.

        Parameters
        ----------
        comp : str or Composition
            Composition of interest to compute the chemical potential.
        elements : list
            List of strings with elements with free chemical potentials.
        cbar_label : str
            String with label of the colormap. The default is ''.
        cbar_values : tuple or bool
            Show max e min chempot values on colorbar. If tuple the values are used, if not the 
            minimum chempot and 0 are used. The default is True.
        **kwargs : dict
            kwargs for "pcolormesh" function.

        Returns
        -------
        plt : matplotlib
            Matplotlib object.

        """        
        comp = _get_composition_object(comp)
        el1,el2 = elements  
        
        def f(mu1,mu2):            
            return self.pdh.calculate_single_chempot(comp,{el1:mu1,el2:mu2})
        
        axes = plt.gca()
        xlim , ylim = axes.get_xlim() , axes.get_ylim()
        npoints = 100
        x = np.arange(xlim[0],xlim[1]+0.1,abs(xlim[1]+0.1-xlim[0])/npoints)
        y = np.arange(ylim[0],ylim[1]+0.1,abs(ylim[1]+0.1-ylim[0])/npoints)   
        
        X,Y = np.meshgrid(x,y)
        Z = f(X,Y)

        plt.pcolormesh(X,Y,Z,vmax=0,shading='auto',**kwargs)

        cbar = plt.colorbar()
       # cbar.ax.tick_params(labelsize='xx-large')
        if cbar_values:
            if isinstance(cbar_values,tuple):
                cbar_min,cbar_max = cbar_values[0], cbar_values[1]
            else:
                cbar_min = np.around(Z.min(),decimals=1)        # colorbar min value - avoid going out of range
                cbar_max = 0                                    # colorbar max value
            plt.text(0.81,1.6,str(cbar_max),size=15)         # easier to show cbar labels as text
            plt.text(0.73,-14.2,str(cbar_min),size=15)
        cbar.set_ticks([]) # comment if you want ticks
        cbar.ax.set_yticklabels('') # comment if you want tick labels
        cbar.ax.set_ylabel(cbar_label,fontsize='xx-large')

        return plt
        

    def add_reservoirs(self,reservoirs,elements,size=1,label_size=1,color=[],edgecolor='k',
                       label_color='k',linewidths=3,**kwargs):
        """
        Add reservoirs as points on the stability diagram.

        Parameters
        ----------
        reservoirs : Reservoirs
            Reservoirs object.
        elements : list
            List with strings of the elements to be used as free variables.
        size : float
            Float multiplier for points size. Default is 1, which would yield a default size of 450*self.size
        label_size : float
            Float multiplier for labels size. Default is 1, which would yield a default size of 30*self.size
        color : str
            Color of filling of points
        edgecolor : str 
            Color of point edge
        label_color : str 
            Color of labels
        linewidths : 3
            line width of point edge
        kwargs: dict
            kwargs to pass to matplotlib `scatter` function.

        Returns
        -------
        plt : matplotlib
            Matplotlib object.

        """         
        points = {}
        for r,mu in reservoirs.items():
            points[r] = [mu[el] for el in elements]
        
        return self.add_points(points,size,label_size,color,edgecolor,label_color,linewidths,**kwargs)
        
    
    def constant_chempot_line(self, mu, comp, variable_element, chempots_ref):
        """
        Function that expresses line of constant chemical potential of a given composition. Only works for 3-component PD.

        Parameters
        ----------
        mu : float
            Indipendent variable of chemical potential.
        comp : str or Composition
            Composition of the phase.
        variable_element : Pymatgen Element object
            Element chosen as indipendent variable.
        chempots_ref : dict
            Dictionary with fixed chemical potentials (values relative to reference phase). The format is {Element:chempot}.
        
        Returns
        -------
        chempot : float
            Chemical potential in eV.

        """
        comp = _get_composition_object(comp)
        chempots_ref[variable_element] = mu
        return self.chempots_analysis.calculate_single_chempot(comp,chempots_ref)
    
    
    def get_plot(self,elements,figsize=None):
        """
        Method to get stability diagram with 'get_chempot_range_map_plot' method in pymatgen.

        Parameters
        ----------
        elements : list
            List with strings of the elements to be used as free variables.
        figsize : tuple
            New size in inches.

        Returns
        -------
        plt : matplotlib
            Matplotlib object.

        """
        pdhandler = PDHandler(self.phase_diagram)
        return pdhandler.get_stability_diagram(elements=elements,figsize=figsize)
        