import sys
import os
import shutil
from .core import *

class InputBuilder():

    def __init__(self, path:str = None, theory:dict = None, software:str = 'gaussian', space = None):
        self.path = path
        self.theory = theory
        self.software = software
        self.space = space

    @staticmethod
    def element_number(A):

        periodic_table = {'H': 1, 'He': 2,
                          'Li': 3, 'Be': 4, 'B': 5, 'C': 6, 'N': 7, 'O': 8, 'F': 9, 'Ne': 10,
                          'Na': 11, 'Mg': 12, 'Al': 13, 'Si': 14, 'P': 15, 'S': 16, 'Cl': 17, 'Ar': 18,
                          'K': 19, 'Ca': 20, 'Br': 35, 'Ag': 47, 'I': 53}

        return periodic_table[A]

    def gaussian(self):
        space = self.space
        theory = self.theory
        names = self.names

        if names is not None:
            for i in range(space.states):
                space.states[i].id = names[i]

        for state in space.states:
            if theory['disp'] in [True, 'EmpiricalDispersion=GD3BJ', 'GD3BJ']:
                theory['disp'] = 'EmpiricalDispersion=GD3BJ'
            elif theory['disp'] in ['EmpiricalDispersion=GD3', 'GD3']:
                theory['disp'] = 'EmpiricalDispersion=GD3'
            else:
                theory['disp'] = ' '


            input_dir = os.path.join(self.path,state.id)
            if not os.path.isdir(input_dir):
                os.mkdir(input_dir)
            input_file = os.path.join(input_dir,'input.com')

            f = open(input_file, 'w')
            f.write('%nproc=' + str(theory['nprocs']) + '\n')
            f.write('%mem=' + theory['mem'] + '\n')
            if 'other_options' in theory.keys():
                f.write(' '.join(['#P', theory['method'], theory['basis_set'], theory['jobtype'], theory['other_options'],
                              theory['disp'], '\n']))
            else:
                f.write(
                    ' '.join(['#P', theory['method'], theory['basis_set'], theory['jobtype'],
                              theory['disp'], '\n']))
            f.write('\n')
            f.write(state.id + '\n')
            f.write('\n ')
            f.write(str(theory['charge']) + ' ' + str(theory['multiplicity']) + '\n')
            for at, xyz in zip(state.atoms, state.xyz):
                line = '{0:5s} {1:10.3f} {2:10.3f} {3:10.3f}\n'.format(at.type, xyz[0], xyz[1], xyz[2])
                f.write(line)
            f.write(' ')

            if 'extra' in theory.keys():
                if theory['extra'] == None:
                    f.close()
                else:
                    f.write('\n')
                    f.write(theory['extra'] + '\n')
                    f.write(' ')
                f.close()
            else:
                f.close()

    def fhiaims(self):
        space = self.space
        theory = self.theory

        for state in space:

            if not os.path.isdir(os.path.join(self.path, state.id)):
                os.mkdir(os.path.join(self.path, state.id))

            control_file = os.path.join(self.path, state.id, 'control.in')
            geom_file = os.path.join(self.path, state.id, '/geometry.in')

            c = open(control_file, 'w')
            c.write('xc ' + str(theory['xc']) + '\n')
            c.write(theory['disp'] + '\n')
            c.write('charge ' + str(theory['charge']) + '\n')
            c.write(theory['jobtype'] + '\n')
            c.write(theory['convergence_options'] + '\n')
            c.write('density_update_method ' + theory['density_update_method'] + '\n')
            c.write('check_cpu_consistency ' + theory['check_cpu_consistency'] + '\n')
            diff_atoms = set([atom.type for atom in state.atoms])

            for at in diff_atoms:
                EN = "{0:02d}".format(InputBuilder.element_number(at))
                with open('/exports/apps/fhi-aims.210226/species_defaults/' + theory[
                    'basis_set'] + '/' + EN + '_' + at + '_default', 'r') as light:
                    for line in light.readlines():
                        c.write(line)
            c.close()

            g = open(geom_file, 'w')
            for n, at, xyz in zip(range(state.NAtoms), state.atoms, state.xyz):
                if n in theory['extra']:
                    freeze = 'constrain_relaxation .true.'
                else:
                    freeze = ''
                line = 'atom      {0:10.3f} {1:10.3f} {2:10.3f} {3:3s}{4:s}\n'.format(xyz[0], xyz[1], xyz[2], at,
                                                                                      freeze)
                g.write(line)
            g.close()

    def xyz(self):
        space = self.space
        for state in space:

            input_dir = os.path.join(self.path,state.id)
            if not os.path.isdir(input_dir):
                os.mkdir(input_dir)
            input_file = os.path.join(input_dir,'geometry.xyz')

            f = open(input_file, 'w')
            f.write('{0:3d}\n'.format(state.NAtoms))
            f.write(f'{state.id}\n')
            for at, xyz in zip(state.atoms, state.xyz):
                line = '{0:5s} {1:10.3f} {2:10.3f} {3:10.3f}\n'.format(at.type, xyz[0], xyz[1], xyz[2])
                f.write(line)
            f.close()

    def build(self, space, theory, software, path, names:list = None):
        self.space = space
        self.theory = theory
        self.software = software
        self.path = path
        self.names = names

        if software == 'gaussian':
            self.gaussian()
        elif software == 'fhiaims':
            self.fhiaims()
        elif software == 'xyz':
            self.xyz()