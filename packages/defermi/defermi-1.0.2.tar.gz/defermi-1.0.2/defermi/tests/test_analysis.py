#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue May 16 17:34:15 2023

@author: villa
"""
import matplotlib

#matplotlib.use('Agg') # no graphical output

from pymatgen.electronic_structure.dos import CompleteDos
import numpy as np
import os.path as op
import pandas as pd

from defermi.tools.utils import get_object_from_json
from defermi.chempots.core import Chempots
from defermi.defects import Vacancy
from defermi.entries import DefectEntry
from defermi.analysis import DefectsAnalysis, SingleDefConc, DefectConcentrations

from defermi.testing.core import DefermiTest
from defermi.testing.defects import DefectEntryTest
from defermi.tests.test_entries import TestDefectEntry


def get_textbook_case_with_ctl():

    bulk_volume = 800 # A^3

    data_dict = [
    {'name': 'Vac_O',
    'charge': 2,
    'multiplicity': 1,
    'energy_diff': 7,
    'bulk_volume': bulk_volume},

    {'name': 'Vac_Sr',
    'charge': -2,
    'multiplicity': 1,
    'energy_diff': 8,
    'bulk_volume': bulk_volume},

    {'name': 'Vac_O',
    'charge':0,
    'multiplicity':1,
    'energy_diff': 10.8, 
    'bulk_volume': bulk_volume},

    {'name': 'Vac_Sr',
    'charge': 0,
    'multiplicity': 1,
    'energy_diff': 7.8,
    'bulk_volume': bulk_volume},
    ]

    df = pd.DataFrame(data_dict)
    df

    vbm = 0 # eV
    band_gap = 2 # eV
    chempots = {'O': -4.95, 'Sr': -2}
    bulk_dos = {'m_eff_e': 0.5, 'm_eff_h': 0.4} # effective masses
    da = DefectsAnalysis.from_dataframe(df,band_gap=band_gap,vbm=vbm)
    return da, chempots , bulk_dos



class TestDefectsAnalysis(DefermiTest):
    
    @classmethod
    def setUpClass(cls):
        self = cls()
        da = DefectsAnalysis.from_vasp_directories(
                                                    path_defects=op.join(self.test_files_path,'SiO2-defects/Defects'),
                                                    path_bulk=op.join(self.test_files_path,'SiO2-defects/Bulk-2x2x2-supercell'),
                                                    get_charge_correction=False,
                                                    get_multiplicity=True,
                                                    common_path='2-PBE-OPT',
                                                    initial_structure=True)
        for entry in da:
            entry.defect.set_multiplicity(1)
        cls.da_comp = da.copy()
        da.filter_entries(inplace=True,exclude=True,types=['DefectComplex'])
        cls.da = da
        mu_O = -6
        mu_P = -5.4133
        mu_Si = -5.4224
        cls.chempots = Chempots({'Si':mu_Si,'P':mu_P,'O':mu_O},ndecimals=2)
        cls.dos = get_object_from_json(CompleteDos, self.get_testfile_path('SiO2-defects/Bulk-2x2x2-supercell/complete_dos.json')) 


    def test_plot(self):
        plt = self.da_comp.plot_formation_energies(self.chempots)
        plt = self.da_comp.plot_ctl(figsize=(6,6))
        plt = self.da_comp.plot_binding_energies()
        
    def test_stable_charges(self):
        stable_charge_Vac_O = (2, 0.08920299999999681)
        stable_charge_Int_O = (0, 5.666554999999903)
        self.assert_all_close(self.da.stable_charges(self.chempots)['Vac_O'], stable_charge_Vac_O)
        self.assert_all_close(self.da.stable_charges(self.chempots)['Int_O'], stable_charge_Int_O)
    
    def test_formation_energies(self):
        formation_energies = self.da.formation_energies(self.chempots)
        formation_energy_Vac_Si_qminus4 = 21.89906667999999
        desired = formation_energy_Vac_Si_qminus4
        actual = formation_energies['Vac_Si'][1][1]
        self.assert_all_close(actual , desired, rtol=1e-03 )
    
    def test_charge_transition_levels(self):
        actual = self.da.charge_transition_levels()['Sub_P_on_Si'][0]
        desired = (1, 0, 6.224602499999989)
        self.assert_all_close( actual , desired )
    
    def test_carrier_concentrations(self):
        actual = self.da.carrier_concentrations(bulk_dos=self.dos,fermi_level=2)
        desired = (2.5207523856086593e-16, 5.386720e-49)
        self.assert_all_close(actual , desired)
    
    def test_defect_concentrations(self):
        conc = self.da.defect_concentrations(self.chempots)
        actual = conc.select_concentrations(name='Vac_O',charge=2)[0]['conc']
        desired = 3.383174303005728e+19
        self.assert_all_close(actual, desired, rtol=1e-03)
        actual = conc.select_concentrations(name='Sub_P_on_Si',charge=1)[0]['conc']
        desired = 1.1001057398319168e+21
        self.assert_all_close(actual, desired, rtol=1e-03)

        
    def test_defect_concentrations_fixed(self):    
        concfix = 1e17
        fixed = {'P':concfix}
        conc = self.da.defect_concentrations(chemical_potentials=self.chempots,fixed_concentrations=fixed)

        actual = conc.elemental['P']
        desired = concfix
        self.assert_all_close(actual, desired)

        actual = conc.select_concentrations(charge=2, name='Vac_O')[0]['conc']
        desired = 3.383174303005728e+19
        self.assert_all_close(actual, desired, rtol=1e-03)

        fixed = {'Vac_O':concfix}
        conc = self.da.defect_concentrations(chemical_potentials=self.chempots,fixed_concentrations=fixed,fermi_level=1.87)
        conc_Vac_O_q2 = conc.select_concentrations(name='Vac_O',charge=2)[0]['conc']
        conc_Vac_O_q0 = conc.select_concentrations(name='Vac_O',charge=0)[0]['conc']
        actual = conc_Vac_O_q2, conc_Vac_O_q0
        desired = (6.412340108578859e+16,3.58765989142114e+16)
        self.assert_all_close(actual, desired, rtol=1e-03)
        self.assert_all_close(conc.elemental['Vac_O'], concfix, rtol=1e-05)
        self.assert_all_close(conc.total['Sub_P_on_Si'], 0.13903596778575308, rtol=5e-03)

    def test_names(self):
        actual = self.da.names
        desired = ['Int_O', 'Sub_P_on_Si', 'Vac_O', 'Vac_Si', 'Vac_Si-Vac_O']
        self.assert_object_almost_equal(actual, desired)
        
    def test_select_entries(self):
        manual_entries = self.da[3], self.da[4]
        selected_entries = self.da.select_entries(elements=['P'])
        for i in range(0,len(selected_entries)):
            DefectEntryTest().assert_DefectEntry_equal(selected_entries[i], manual_entries[i])
            
    def test_solve_fermi_level(self):
        actual = self.da.solve_fermi_level(chemical_potentials=self.chempots,bulk_dos=self.dos)
        desired = 3.0042287011146547
        self.assert_all_close(actual,desired)

    def test_binding_energy(self):
        actual = self.da_comp.binding_energy(name='Vac_Si-Vac_O')
        desired = 1.3470440099999914
        self.assert_all_close(actual, desired)
           
        
    def test_from_csv(self):
        vbm = self.da.vbm
        band_gap = self.da.band_gap
        da = DefectsAnalysis.from_file(
                                self.get_testfile_path('SiO2_defects_analysis.csv'),
                                vbm=vbm,
                                band_gap=band_gap)
        self.da = da
        self.test_defect_concentrations_fixed()
        self.test_formation_energies()
        self.test_charge_transition_levels()


    def test_from_dataframe(self):
        bulk_volume = 909.0035
        d =[{'name': 'Int_O',
            'charge': -2.0,
            'multiplicity': 1,
            'energy_diff': 4.543,
            'bulk_volume': bulk_volume},
            {'name': 'Int_O',
            'charge': -1.0,
            'multiplicity': 1,
            'energy_diff': 1.7746,
            'bulk_volume': bulk_volume},
            {'name': 'Int_O',
            'charge': 0.0,
            'multiplicity': 1,
            'energy_diff': -0.3334,
            'bulk_volume': bulk_volume},
            {'name': 'Sub_P_on_Si',
            'charge': 0.0,
            'multiplicity': 1,
            'energy_diff': 5.6674,
            'bulk_volume': bulk_volume},
            {'name': 'Sub_P_on_Si',
            'charge': 1.0,
            'multiplicity': 1,
            'energy_diff': -1.5959,
            'bulk_volume': bulk_volume},
            {'name': 'Vac_O',
            'charge': 0.0,
            'multiplicity': 1,
            'energy_diff': 9.8442,
            'bulk_volume': bulk_volume},
            {'name': 'Vac_O',
            'charge': 1.0,
            'multiplicity': 1,
            'energy_diff': 8.3845,
            'bulk_volume': bulk_volume},
            {'name': 'Vac_O',
            'charge': 2.0,
            'multiplicity': 1,
            'energy_diff': 4.0104,
            'bulk_volume': bulk_volume},
            {'name': 'Vac_Si',
            'charge': -5.0,
            'multiplicity': 1,
            'energy_diff': 38.4723,
            'bulk_volume': bulk_volume},
            {'name': 'Vac_Si',
            'charge': -4.0,
            'multiplicity': 1,
            'energy_diff': 31.4767,
            'bulk_volume': bulk_volume},
            {'name': 'Vac_Si',
            'charge': -3.0,
            'multiplicity': 1,
            'energy_diff': 28.4873,
            'bulk_volume': bulk_volume}]
        
        df = pd.DataFrame(d)
        vbm = self.da.vbm
        band_gap = self.da.band_gap
        da = DefectsAnalysis.from_dataframe(df,vbm=vbm,band_gap=band_gap)
        self.da = da
        self.test_defect_concentrations_fixed()
        self.test_formation_energies()
        self.test_charge_transition_levels()

    def test_to_json(self):
        try:
            da = self.da
            da.to_json('test.json')
            test_da = DefectsAnalysis.from_json('test.json')
        finally:
            import os
            os.remove('test.json')



class TestDefectsAnalysisTextbook(DefermiTest):

        
    def get_textbook_case(self):
        e1 = DefectEntry(Vacancy('O',charge=2,bulk_volume=800,multiplicity=1),energy_diff=7)
        e2 = DefectEntry(Vacancy('Sr',charge=-2,bulk_volume=800,multiplicity=1),energy_diff=8)
        da = DefectsAnalysis([e1,e2],vbm=0,band_gap=2)
        chempots = {'O':-4.95,'Sr':-2}
        mdos = {'m_eff_e':0.5,'m_eff_h':0.4}
        return da, chempots, mdos


    def test_textbook_case_from_entries(self):
        da, chempots , mdos = self.get_textbook_case()

        plt = da.plot_doping_diagram(
                        variable_defect_specie={'name':'Sub_K_on_Sr','charge':-1},
                        concentration_range=(1,1e21),
                        chemical_potentials=chempots,
                        bulk_dos=mdos,
                        temperature=1000,
                        xtol=1e-100,
                        figsize=(6,6))
        
        plt = da.plot_brouwer_diagram(
                        bulk_dos=mdos,
                        temperature=1000,
                        precursors={'SrO':-10},
                        oxygen_ref=-4.95,
                        xtol=1e-100,
                        figsize=(6,6))
        data = da.thermodata
        plt.show()

        actual = data.partial_pressures[11]
        desired = 5.429e-14
        self.assert_all_close(actual, desired)

        actual = data.defect_concentrations[33].select_concentrations(name='Vac_Sr')[0]['conc']
        desired = 64410690128.7698
        self.assert_all_close(actual, desired)
    
        actual = data.carrier_concentrations[27][0]
        desired = 416759307474107.94
        self.assert_all_close(actual, desired)

        actual = data.fermi_levels[42]
        desired = 0.9790673314740697
        self.assert_all_close(actual, desired)



    def test_custom_functions(self):
        da , chempots , mdos = self.get_textbook_case()

        def custom_eform(entry,vbm=None,chemical_potentials=None,fermi_level=0,temperature=300,**kwargs):
                formation_energy = entry.energy_diff + entry.charge*(vbm+fermi_level) 
                if chemical_potentials:
                    chempot_correction = -1 * sum([entry.delta_atoms[el]*chemical_potentials[el] for el in entry.delta_atoms])
                else:
                    chempot_correction = 0
                    
                formation_energy = formation_energy + chempot_correction
                test_quantity = kwargs['test'] if kwargs and 'test' in kwargs.keys() else 0
                return formation_energy - 1/500 *temperature + test_quantity       
        

        def custom_dconc(entry,vbm=0,chemical_potentials=None,temperature=0,fermi_level=0,per_unit_volume=True,eform_kwargs={},**kwargs):
                from defermi.entries import fermi_dirac
                n = entry.defect.site_concentration_in_cm3 if per_unit_volume else entry.multiplicity 
                if per_unit_volume:
                    n = n * (1+1/500*temperature)
                eform = entry.formation_energy(
                                        vbm=vbm,
                                        chemical_potentials=chemical_potentials,
                                        fermi_level=fermi_level,
                                        temperature=temperature,
                                        **eform_kwargs)
                
                test_quantity = kwargs['test_conc'] if kwargs and 'test_conc' in kwargs.keys() else 1
                return  n * fermi_dirac(eform,temperature) * test_quantity
        
        da.set_formation_energy_functions(function=custom_eform,name='Vac_O')
        da.set_defect_concentration_functions(function=custom_dconc,name='Vac_Sr')

        conc = da.defect_concentrations(chemical_potentials=chempots,fermi_level=1,temperature=800)
        actual = conc.select_concentrations(name='Vac_O')[0]['conc']
        desired = 459821.5493220144
        self.assert_all_close(actual, desired)

        conc = da.defect_concentrations(chemical_potentials=chempots,fermi_level=1.6,temperature=800)
        actual = conc.select_concentrations(name='Vac_Sr')[0]['conc']
        desired = 7458.641140002768
        self.assert_all_close(actual, desired)

        da.reset_all_custom_functions()
        conc = da.defect_concentrations(chemical_potentials=chempots,fermi_level=1,temperature=800)
        actual = conc.select_concentrations(name='Vac_O')[0]['conc']
        desired = 3.828537891774964e-05
        self.assert_all_close(actual, desired)

        conc = da.defect_concentrations(chemical_potentials=chempots,fermi_level=1.6,temperature=800)
        actual = conc.select_concentrations(name='Vac_Sr')[0]['conc']
        desired = 2868.7081307702956
        self.assert_all_close(actual, desired)


def TestDefectConcentrations(DefermiTest):

    @classmethod
    def setUpClass(cls):
        self = cls()
        self.conc = DefectConcentrations([
        SingleDefConc(charge=-2.0,conc=2.08e-20,name='Int_O'),
        SingleDefConc(charge=-1.0,conc=8.15e-16,name='Int_O'),
        SingleDefConc(charge=0.0,conc=2.21e-15,name='Int_O'),
        SingleDefConc(charge=0.0,conc=2.52e-15,name='Sub_P_on_Si'),
        SingleDefConc(charge=1.0,conc=2.04e+18,name='Sub_P_on_Si'),
        SingleDefConc(charge=0.0,conc=6.67e-04,name='Vac_O'),
        SingleDefConc(charge=1.0,conc=1.49e-07,name='Vac_O'),
        SingleDefConc(charge=2.0,conc=7.59e+07,name='Vac_O'),
        SingleDefConc(charge=-5.0,conc=1.15e-123,name='Vac_Si'),
        SingleDefConc(charge=-4.0,conc=1.91e-92,name='Vac_Si'),
        SingleDefConc(charge=-3.0,conc=1.85e-86,name='Vac_Si')
        ])
 

    def test_total(self):

        total = self.conc.total
        
        actual = total['Sub_P_on_Si']
        desired = 2.0403206475490184e+18
        self.assert_all_close(actual,desired)

        actual = total['Vac_O']
        desired = 75867140.1773762
        self.assert_all_close(actual,desired)


    def test_elemental(self):
        el = self.conc.elemental
        actual = el['P']
        desired = 2.0403206475490184e+18
        self.assert_all_close(actual,desired)

        actual = el['O']
        desired = 3.0203081157289413e-15
        self.assert_all_close(actual,desired)

    
    def test_stable(self):
        stable = self.conc.stable
        self.assertEqual(type(stable),DefectConcentrations)

        actual = stable.select_concentrations(name='Vac_O')[0]['charge']
        desired = 2.0
        self.assert_all_close(actual,desired)

        actual = stable.select_concentrations(name='Int_O')[0]['conc']
        desired = 2.2050864130947814e-15
        self.assert_all_close(actual,desired)

    
    def test_select_concentrations(self):
        selected = self.conc.select_concentrations(name='Vac_O',charge=2)
        
        self.assertEqual(len(selected), 1)

        actual = selected[0]['conc']
        desired = 75867140.17670918
        self.assert_all_close(actual, desired)





    
    