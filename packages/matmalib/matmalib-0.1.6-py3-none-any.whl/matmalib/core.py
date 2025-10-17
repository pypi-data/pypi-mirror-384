from time import sleep

import numpy as np
import os
import sys
import networkx as nx
import re

from tornado.process import fork_processes

from .calc import InputBuilder
from .util import *
from .core import *

class Atom():

    def __init__(self, coord:list = None, type:str = None, valence:int = None, index:int = None):
        self.coord = np.array(coord)
        self.type = type
        self.id = index
        self.mass = None
        self.atoms = None

        if self.coord is not None:
            self.x = self.coord[0]
            self.y = self.coord[1]
            self.z = self.coord[2]

class Fragment():

    def __init__(self):
        self.atoms = []
        # self.xyz = None
        # self.Mass = None


    @property
    def xyz(self):

        xyz_list = []

        for atom in self.atoms:
            xyz_list.append(atom.coord)

        return np.array(xyz_list)
    
    @property
    def Mass(self):

        mass_list = []
        
        for atom in self.atoms:
            mass_list.append(atom.mass)

        return np.array(mass_list)




    # def get_atoms(self):
    #     xyz_list = self.xyz
    #     type_list = self.type_list

    #     atom_list = []

    #     index = 0
    #     for xyz, type in zip(xyz_list, type_list):
    #         atom = Atom(coord=xyz, type=type, index=index)
    #         atom_list.append(atom)

    #     self.atoms = atom_list
    #     return atom_list

    # def get_xyz(self):
    #     xyz = []
    #     for atom in self.get_atoms():
    #         xyz.append(atom.coord)
    #     self.xyz = xyz

    # xyz = property(fget=get_xyz)

class State():

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @classmethod
    def from_file(cls, path, software):

        builder = StateBuilder(path=path, software=software)
        system =  builder.build()
        system.id   = path.split('/')[-2]
        return system

    @property
    def xyz(self):

        xyz_list = []

        for atom in self.atoms:
            xyz_list.append(atom.coord)

        return np.array(xyz_list)

    @property
    def Mass(self):

        mass_list = []

        for atom in self.atoms:
            mass_list.append(atom.mass)

        return np.array(mass_list)

    @property
    def mass(self):
        mass_list = self.Mass
        return np.sum(mass_list)

    @staticmethod
    def element_symbol(A):

        """ A dictionary for atomic number and atomic symbol
        :param A: either atomic number or atomic symbol for Hydrogen, Carbon, Nitrogen, Oxygen, Fluorine and Silicon
        :return: the corresponding atomic symbol or atomic number
        """

        periodic_table = {'1': 'H', '2': 'He',
                          '3': 'Li', '4': 'Be', '5': 'B', '6': 'C', '7': 'N', '8': 'O', '9': 'F', '10': 'Ne',
                          '11': 'Na', '12': 'Mg', '13': 'Al', '14': 'Si', '15': 'P', '16': 'S', '17': 'Cl', '18': 'Ar',
                          '19': 'K', '20': 'Ca', '35': 'Br', '47':'Ag', '53':'I'
                          }
        return periodic_table[A]

    def add_atoms(self, atom):
        self.atoms.append(atom)

    def remove_atoms(self, atom):
        self.atoms.remove(atom)

    def measure_internal(self, atom_list):
        return StateEditor.measure(atom_list=atom_list, state=self)

    def set_internal(self, atom_list, val):

        editor = StateEditor(self)

        if len(atom_list) == 2:
            editor.set_distance(atom_list=atom_list, new_distance=val)        
        elif len(atom_list) == 3:
            editor.set_angle(atom_list=atom_list, new_ang=val)
        elif len(atom_list) == 4:
            editor.set_dihedral(atom_list=atom_list, new_dih=val)

    def connectivity_matrix(self, distXX=1.65, distXH=1.15):

        """ Creates a connectivity matrix of the molecule. A connectivity matrix holds the information of which atoms are bonded and to what.

        :param distXX: The max distance between two atoms (not hydrogen) to be considered a bond
        :param distXH: The max distance between any atom and a hydrogen atom to be considered a bond
        """

        Nat = self.NAtoms
        self.conn_mat = np.zeros((Nat, Nat))

        for at1 in self.atoms:
            for at2 in self.atoms:

                dist = StateEditor.get_distance([at1,at2])

                if at1 == at2:
                    pass

                elif (at1.type == 'H' or at2.type == 'H') and dist < distXH:
                    self.conn_mat[at1.id, at2.id] = 1;
                    self.conn_mat[at2.id, at1.id] = 1
                elif (at1.type != 'H' and at2.type != 'H') and dist < distXX:
                    self.conn_mat[at1.id, at2.id] = 1;
                    self.conn_mat[at2.id, at1.id] = 1

        # Remove bifurcated Hs:
        for at1 in self.atoms:
            if at1.type == 'H' and np.sum(self.conn_mat[at1.id, :]) > 1:

                at2list = np.where(self.conn_mat[at1.id, :] == 1)
                at2list = at2list[0].tolist()

                at2dist = [round(StateEditor.get_distance([at1, self.atoms[at2x]]), 3) for at2x in at2list]
                for at, dist in zip(at2list, at2dist):
                    if self.atoms[at].type == 'H':
                        at2list.remove(at)
                        at2dist.remove(dist)

                at2 = at2list[at2dist.id(min(at2dist))]
                for at2x in at2list:
                    if at2x != at2:
                        print('remove', self.id, at2x, at1, at2)
                        self.conn_mat[at1.id, at2x] = 0;
                        self.conn_mat[at2x, at1.id] = 0

        graph = nx.from_numpy_array(self.conn_mat)

        self.Nmols = nx.number_connected_components(graph)
        self.graph = graph

    def system_split(self):

        g = self.graph
        components = [g.subgraph(c).copy() for c in nx.connected_components(g)]

        frags = []
        for comp in components:
            frag = Fragment()
            frag.graph = comp

            atom_indices = comp.nodes()
            for index in atom_indices:
                atom = self.atoms[index]
                frag.atoms.append(atom)

            frags.append(frag)

        self.mols = frags

    def show(self, width=600, height=600):

        import py3Dmol as p3D

        """ Displays a 3D rendering of the conformer using Py3Dmol

        :param width: the width of the display window
        :param height: the height of the display window
        """

        XYZ = "{0:3d}\n{1:s}\n".format(self.NAtoms, self.id)
        for at, xyz in zip(self.atoms, self.xyz):
            XYZ += "{0:3s}{1:10.3f}{2:10.3f}{3:10.3f}\n".format(at.type, xyz[0], xyz[1], xyz[2])
        xyzview = p3D.view(width=width, height=height)
        xyzview.addModel(XYZ, 'xyz')
        xyzview.setStyle({'stick': {}})
        xyzview.zoomTo()
        xyzview.show()

class Data:
    
    def __init__(self, **kwargs):
    
        self.__dict__.update(kwargs)

    def __repr__(self):
    
        return f"Data({self.__dict__})"
    
    @classmethod
    def from_file(cls, path, software, **kwargs):

        builder = DataBuilder(path=path, software=software, **kwargs)

        return builder.build()

    
class Space():

    def __init__(self, states:list = [], theory:dict = None, input_path:str = None, output_path:str = None):
        self.states = states

        if theory is None:
            theory = {
                'disp': True,
                'nprocs': 24,
                'mem': '60B',
                'method': 'PBE1PBE',
                'basis_set': '6-311G**',
                'jobtype': 'opfreq',
                'charge': 0,
                'multiplicity': 1
            }
        self.theory = theory
        self.input_path = input_path
        self.output_path = output_path

    @property
    def energies(self):
        energies = []

        for state in self.states:
            if hasattr(state, 'E'):
                energies.append(state.E)

        return energies

    @property
    def free_energies(self):

        energies = []

        for state in self.states:
            if hasattr(state, 'F'):
                energies.append(state.F)

        return energies

    @property
    def enthalpies(self):

        energies = []

        for state in self.states:
            if hasattr(state, 'H'):
                energies.append(state.H)

        return energies

    def to_file(self, software:str = 'gaussian'):
        path = self.output_path
        theory = self.theory

        builder = InputBuilder(path=path, theory=theory, software=software, space=self)
        builder.build(path=path, theory=theory, software=software, space=self)

    def sum(self, states:list, quant:str = 'E'):

        if isinstance(states, int):
            states_list = [state for state in self.states]
        else:
            states_list = states

        if quant not in ['E', 'F', 'H']:
            print('Error: Quantity not recognized')
            return None

        total = 0
        for state in states_list:
            if not hasattr(state, quant):
                print('Error: State does not have attribute', quant)
                return None

            val = getattr(state, quant)
            total += val

        return total
    
    @classmethod
    def from_dir(cls, path, software='gaussian'):

        dirs = [d for d in os.listdir(path) if os.path.isdir(f"{path}/{d}")]
        states = []

        for subdir in dirs:
            
            if software == 'gaussian':
                state = State.from_file(f"{path}/{subdir}/input.log", software='gaussian')
            # Include other software formats in the future.
            
            states.append(state)

        return Space(states)

    def diff(self, states=None, quant:str = 'E'):

        if states:
            if isinstance(states, list):
                
                if isinstance(states[0], int):
                    states_list = [self.states[n] for n in states]
                else:
                    states_list = states
            
        else:
            states_list = self.states

        if quant not in ['E', 'F', 'H']:
            raise ValueError(f"Error: Quantity {quant} not recognized!")
        
        for state in states_list:
            if not hasattr(state, quant):
                raise AttributeError(f"Error: State does not have attribute {quant}")
                
        diff_list = []
        # val_0 = getattr(states_list[0], quant)
        
        vals = [getattr(state, quant) for state in states_list]
        val_0 = np.min(vals)

        for state in states_list:
            val = getattr(state, quant) - val_0
            diff_list.append(val * 627.5095)

        return diff_list

    def add(self, state):

        if isinstance(state, list):
            for st in state:
                self.states.append(st)
        else:
            self.states.append(state)

    def remove(self, state):
        type = type(state)
        if type == list:
            for st in state:
                if type(st) != int:
                    self.states.remove(st)
                else:
                    self.states.pop(st)

        elif type == int:
            self.states.pop(state)
        else:
            self.states.remove(state)



    


