import matmalib.core as matmacore
import math
import numpy as np
import re
from scipy.linalg import expm

class StateEditor:

    def __init__(self, state):

        self.state = state

    @staticmethod
    def get_distance(atom_list, state=None):

        """ Finds the distance between two atoms
        :param at1: (list) a list of xyz coordinates of atom1
        :param at2: (list) a list of xyz coordinates of atom2
        :return: (float) the distance between 2 atoms
        """

        from .core import Atom

        # If at1 or at2 are integers, extract these values from the supplied state.
        if len(atom_list) != 2: print(f"Warning! {len(atom_list)} atoms specified for function get_distance, expected 2.")

        if all(isinstance(at, int) for at in atom_list) and state != None:
            at1 = state.atoms[atom_list[0]]
            at2 = state.atoms[atom_list[1]]

        elif all(isinstance(at, Atom) for at in atom_list):
            at1 = atom_list[0]
            at2 = atom_list[1]

        else:
            raise ValueError('Error: Specify all Atoms, or all integers for atom list!')

        dist = 0
        for dim in range(3):
            dist += (at1.coord[dim]-at2.coord[dim])**2

        return math.sqrt(dist)

    @staticmethod
    def adjacent_atoms(conn_mat, at):

        """returns all adjacent atoms to a specific atom in a conformation
        :param conn_mat: the connectivity matrix
        :param at: index of the selected atom
        :return: indices of all atoms adjacent to the selected atom
        """

        return np.nonzero(conn_mat[at,:])[0]
    
    @staticmethod
    def get_angle(atom_list, state=None):

        """Calculate an angle between three atoms:
        angle = acos(dot(X,Y)/(norm(X)*norm(Y)))
        :param list_of_atoms: (list) list of 3 atoms
        :param conf: a conformer object
        :return angle, axor: returns angle in degrees and axis of rotation of the angle
        """

        from .core import Atom

        if len(atom_list) != 3: print(f"Warning! {len(atom_list)} atoms specified for function get_distance, expected 3.")

        if all(isinstance(at, int) for at in atom_list) and state != None:
            at1 = state.atoms[atom_list[0]]
            at2 = state.atoms[atom_list[1]]
            at3 = state.atoms[atom_list[2]]

        elif all(isinstance(at, Atom) for at in atom_list):
            at1 = atom_list[0]
            at2 = atom_list[1]
            at3 = atom_list[2]

        else:
            raise ValueError('Error: Specify all Atoms, or all integers for atom list!')

        r1 = [x-y for x,y in zip(at1.coord,at2.coord)]
        r2 = [x-y for x,y in zip(at3.coord,at2.coord)]

        norm1 = StateEditor.get_distance([at1,at2])
        norm2 = StateEditor.get_distance([at2,at3])

        norm = norm1*norm2
        dot = np.dot(r1,r2)/norm
        angle = math.acos(dot)
        axor = np.cross(r1,r2)

        return angle*180/np.pi, axor
    
    @staticmethod
    def get_dihedral(atom_list, state= None, ax:bool = False):

        from .core import Atom

        if len(atom_list) != 4: print(f"Warning! {len(atom_list)} atoms specified for function get_distance, expected 4.")

        if all(isinstance(at, int) for at in atom_list) and state != None:
            at1 = state.atoms[atom_list[0]]
            at2 = state.atoms[atom_list[1]]
            at3 = state.atoms[atom_list[2]]
            at4 = state.atoms[atom_list[3]]

        elif all(isinstance(at, Atom) for at in atom_list):
            at1 = atom_list[0]
            at2 = atom_list[1]
            at3 = atom_list[2]
            at4 = atom_list[3]

        else:
            raise ValueError('Error: Specify all Atoms, or all integers for atom list!')

        r1 = [x-y for x,y in zip(at1.coord,at2.coord)]
        r2 = [x-y for x,y in zip(at2.coord,at3.coord)]
        r3 = [x-y for x,y in zip(at3.coord,at4.coord)]

        p1 = np.cross(r1,r2)
        p2 = np.cross(r2,r3)

        axor = np.cross(p1,p2)

        norm_p1 = np.sqrt(np.sum(p1**2))
        norm_p2 = np.sqrt(np.sum(p2**2))

        norm = norm_p1*norm_p2
        dot = np.clip(np.dot(p1,p2)/norm,-0.999999999,0.999999999)
        angle = math.acos(dot)

        ppoint = -np.dot(p1,at1.coord)
        dpoint = np.dot(p1,at4.coord) + ppoint/norm_p1


        if not ax:
            if dpoint >= 0:
                return -(angle*180/np.pi)
            else:
                return angle*180/np.pi

        if ax:
            if dpoint >= 0:
                return -(angle * 180 / np.pi), axor
            else:
                return angle * 180 / np.pi, axor
            
    @staticmethod
    def measure(atom_list, state=None):

        if len(atom_list) == 2:
            return StateEditor.get_distance(atom_list, state=state)
        elif len(atom_list) == 3:
            return StateEditor.get_angle(atom_list, state=state)
        elif len(atom_list) == 4:
            return StateEditor.get_dihedral(atom_list, state=state)

    @staticmethod
    def determine_carried_atoms(state, atom_list):

        import networkx as nx
        from .core import Atom

        """Find all atoms necessary to be carried over during rotation
        of an atom
        :param at1: (list) the xyz coordinates of an atom
        :param at2: (list) the xyz coordinates of another atom
        :param conn_matt: the connectivity matrix of a conformer
        """
        #   1. Zero the connections in connectivity matrix
        # tmp_conn = np.copy(conf.conn_mat)

        if len(atom_list) != 2: print(f"Warning! {len(atom_list)} atoms specified for function get_distance, expected 2.")

        if all(isinstance(at, int) for at in atom_list) and state != None:
            at1 = state.atoms[atom_list[0]]
            at2 = state.atoms[atom_list[1]]

        elif all(isinstance(at, Atom) for at in atom_list):
            at1 = atom_list[0]
            at2 = atom_list[1]

        else:
            raise ValueError('Error: Specify all Atoms, or all integers for atom list!')

        coord1 = at1.coord
        coord2 = at2.coord

        broke_bond = False
        if state.conn_mat[at1.id, at2.id] == 1 or state.conn_mat[at2.id, at1.id] == 1:
            StateEditor.disconnect_atoms(state, at1.id, at2.id)
            broke_bond = True

        # cm = state.graph # This doesn't work.
        cm = nx.graph.Graph(state.conn_mat)

        if nx.is_connected(cm):
            print("Matrix still connected")
            return

        #   2. Determine the connected atoms:
        for subgraph in nx.connected_components(cm):
            if at2.id in subgraph:
                # print('subgraph:',subgraph)
                carried_atoms = [state.atoms[at] for at in subgraph]
        if broke_bond: StateEditor.connect_atoms(state, at1.id, at2.id)

        return carried_atoms
    
    @staticmethod
    def connect_atoms(state, at1:int, at2:int):

        """Connects two atoms in the conn_mat
        :param conf: conf object that has associated conn_mat
        :return: None
        """

        state.conn_mat[at1, at2] = 1
        state.conn_mat[at2, at1] = 1

    @staticmethod
    def disconnect_atoms(state, at1:int, at2:int):

        """Disconnects two atoms in the conn_mat
        :param conf: conf object that has associated conn_mat
        :return: None                                            
        """

        state.conn_mat[at1, at2] = 0
        state.conn_mat[at2, at1] = 0

    def set_distance(self, atom_list, new_distance):

        """Set a new distance between two atoms
        :param list_of_atoms: (list) list of two atoms
        :param new_distance: value of bond distance to be set
        """

        if len(atom_list) != 2 or not all(isinstance(at, int) for at in atom_list):
            raise ValueError("The position needs to be defined by 2 integers")

        at1 = self.state.atoms[atom_list[0]]
        at2 = self.state.atoms[atom_list[1]]

        # Identify displacement vector:
        
        displacement_vector = at2.coord - at1.coord
        norm_vector = np.sqrt(np.sum(displacement_vector**2))
        normalized_vector = displacement_vector / norm_vector
        
        old_distance = StateEditor.get_distance([at1, at2], state=self.state)
        translation = normalized_vector * (new_distance - old_distance)
        
        carried_atoms = StateEditor.determine_carried_atoms(self.state, [at1.id, at2.id])

        for at in carried_atoms:

            self.state.atoms[at.id].coord += translation

        #return xyz

    def set_angle(self, atom_list, new_ang):

        """Set a new angle between three atoms
        :param list_of_atoms: (list) list of three atoms
        :param new_ang: value of dihedral angle (in degrees) to be set
        """

        if len(atom_list) != 3 or not all(isinstance(at, int) for at in atom_list):
            raise ValueError("The position needs to be defined by 3 integers")

        at1 = self.state.atoms[atom_list[0]]
        at2 = self.state.atoms[atom_list[1]]
        at3 = self.state.atoms[atom_list[2]]

        #   Determine the axis of rotation:

        old_ang, axor = StateEditor.get_angle([at1, at2, at3], state=self.state)
        norm_axor = np.sqrt(np.sum(axor**2))
        normalized_axor = axor/norm_axor

        #   Each carried_atom is rotated by euler-rodrigues formula:
        #   Also, I move the midpoint of the bond to the mid atom
        #   the rotation step and then move the atom back.

        rot_angle = np.pi*(new_ang - old_ang)/180.
        translation = at2.coord

        #apply rotations to at3.
        rot = expm(np.cross(np.eye(3), normalized_axor*(rot_angle)))
        carried_atoms = StateEditor.determine_carried_atoms(self.state, [at2.id, at3.id])
        
        for at in carried_atoms:
        
            at.coord = np.dot(rot, at.coord-translation)
            at.coord = at.coord+translation
        
    def set_dihedral(self, atom_list, new_dih, incr = False,  axis_pos = "bond", threshold = 0.1):

        """Set a new dihedral angle between two planes defined by
        atoms first and last three atoms of the supplied list.
        :param list_of_atoms: (list) list of four atoms
        :param new_dih: (float) value of dihedral angle (in degrees) to be set
        :incr: (bool) whether the new_dih should be treated as incremental value to current dih
        :axis_pos: whether to set the axor along the central bond, or the terminal bond in the list of 4 atoms
        :returns: xyz modified numpy array with new atoms positions
        """
        #print("atoms of the planes:", list_of_atoms) #It's very poetic

        if len(atom_list) != 4 or not all(isinstance(at, int) for at in atom_list):
            raise ValueError("The position needs to be defined by 4 integers")

        at1 = self.state.atoms[atom_list[0]]
        at2 = self.state.atoms[atom_list[1]]
        at3 = self.state.atoms[atom_list[2]]
        at4 = self.state.atoms[atom_list[3]]
        
        #xyz = copy.copy(conf.xyz)
        # xyz = self.mol.xyz

        #   Determine the axis of rotation:
        # old_dih, axor = StateEditor.get_dihedral(self.state, [at1, at2, at3, at4])
        old_dih, axor = StateEditor.get_dihedral([at1, at2, at3, at4], ax=True)

        #if incr == True:
        #    print("current dihedral:",old_dih,"increm dihedral:",new_dih)
        #else:
        #    print("current dihedral:",old_dih,"target dihedral:",new_dih)
        try:
            norm_axor = np.sqrt(np.sum(axor**2))
            normalized_axor = axor/norm_axor

        except RuntimeWarning:
            print(axor, norm_axor, normalized_axor)
            print(at1, at2, at3, at4)
            print(axis_pos, incr)

        if incr == True: new_dih = old_dih + new_dih

        #(get it between -180. - 180.0
        if   new_dih >=  180.0 : new_dih -= 360.0
        elif new_dih <= -180.0 : new_dih += 360.0

        if abs(new_dih - old_dih) < threshold: return

        if old_dih >= 0.0 :
            if ( 180.0 - threshold) < new_dih:  new_dih = 180.0 - threshold
            rot_angle = new_dih - old_dih
            rot_angle = np.pi*(rot_angle)/180.
        else:
            if (-180.0 + threshold) > new_dih:  new_dih= -180.0 + threshold
            rot_angle = new_dih - old_dih
            rot_angle = -np.pi*(rot_angle)/180.

        #   Each carried_atom is rotated by Euler-Rodrigues formula:
        #   Reverse if the angle is less than zero, so it rotates in
        #   right direction.
        #   Also, I move the midpoint of the bond to the center for
        #   the rotation step and then move the atom back.

        rot = expm(np.cross(np.eye(3), normalized_axor*rot_angle))

        if axis_pos == "bond":
            translation = (at2.coord+at3.coord)/2
            carried_atoms = StateEditor.determine_carried_atoms(self.state, [at2.id, at3.id])

        elif axis_pos == "term":
            translation = np.array([x for x in at4.coord])
            #Determine which atoms should be dragged along with the bond:
            carried_atoms = StateEditor.determine_carried_atoms(self.state, [at3.id, at4.id])
            carried_atoms.remove(at4)

        for at in carried_atoms:
            #print("atom #:", at)
            #print("original xyz:", xyz[at, :])
            at.coord = np.dot(rot, at.coord-translation)
            at.coord = at.coord+translation
            #print("new xyz:", xyz[at, :])

            #dih, axor = measure_dihedral(conf, [at1, at2, at3, at4])
            #print("new dihedral:", dih, "\n")


class StateBuilder:

    def __init__(self, path, software):
        self.path = path
        self.software = software

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

    def gaussian(self):

        """
        Parses log files from Gaussian 16 and appends information inside the log file to the mol object.

        """
        flags = {'freq_flag': False, 'nmr_flag': False, 'opt_flag': False, 'jcoup_flag': False, 'normal_mode': False,
                 'read_geom': False}
        job_type = None

        # temprorary variables to hold the data
        freq = []
        ints = []
        vibs = []
        geom = []
        atoms = []
        nmr = []
        self.NAtoms = None

        for line in open(self.path, 'r').readlines():

            if not job_type and re.search('^ #', line):

                if "opt" in line:
                    if "freq" in line:
                        job_type = 'optfreq'
                    else:
                        job_type = 'opt'
                elif "freq" in line:
                    if "opt" in line:
                        job_type = 'optfreq'
                    else:
                        job_type = 'freq'
                        flags["freq_flag"] = True
                elif "nmr" in line:
                    job_type = 'nmr'
                else:
                    job_type = 'sp'

            if self.NAtoms is None and re.search('^ NAtoms=', line):
                self.NAtoms = int(line.split()[1])

            if job_type == 'optfreq' or job_type == "freq":

                if flags['freq_flag'] == False and re.search('Normal termination', line): flags['freq_flag'] = True
                # We skip the opt part of optfreq job, all info is in the freq part

                if flags['freq_flag'] == True:

                    if re.search('SCF Done', line):
                        self.E = float(line.split()[4])
                    elif re.search('Sum of electronic and zero-point Energies', line):
                        self.Ezpe = float(line.split()[6])
                    elif re.search('Sum of electronic and thermal Enthalpies', line):
                        self.H = float(line.split()[6])
                    elif re.search('Sum of electronic and thermal Free Energies', line):
                        self.F = float(line.split()[7])

                    elif re.search('Coordinates', line) and len(geom) == 0:
                        flags['read_geom'] = True

                    elif flags['read_geom'] == True and re.search(r'^\s*.\d', line):
                        geom.append([float(x) for x in line.split()[3:6]])
                        coord = [float(x) for x in line.split()[3:6]]
                        type = StateBuilder.element_symbol(line.split()[1])
                        atom = matmacore.Atom(coord, type)
                        atoms.append(atom)
                        if int(line.split()[0]) == self.NAtoms:
                            flags['read_geom'] = False

                    elif re.search(' Deg. of freedom', line):
                        self.NVibs = int(line.split()[3])

                    elif re.search('^ Frequencies', line):
                        freq_line = line.strip()
                        for f in freq_line.split()[2:5]: freq.append(float(f))
                        flags['normal_mode'] = False

                    elif re.search('^ IR Inten', line):
                        ir_line = line.strip()
                        for i in ir_line.split()[3:6]: ints.append(float(i))

                    elif re.search('^  Atom  AN', line):
                        flags['normal_mode'] = True  # locating normal modes of a frequency
                        mode_1 = []
                        mode_2 = []
                        mode_3 = []
                        # continue

                    elif flags['normal_mode'] == True and re.search(r'^\s*\d*\s*.\d*', line) and len(line.split()) > 3:
                        mode_1.append([float(x) for x in line.split()[2:5]])
                        mode_2.append([float(x) for x in line.split()[5:8]])
                        mode_3.append([float(x) for x in line.split()[8:11]])

                    elif flags['normal_mode'] == True:
                        flags['normal_mode'] = False
                        for m in [mode_1, mode_2, mode_3]: vibs.append(np.array(m))

            elif job_type == 'opt':

                if re.search('SCF Done', line): E = float(line.split()[4])
                if re.search('Optimization completed.', line):
                    self.E = E;
                    flags['opt_flag'] = True
                if flags['opt_flag'] == True:
                    if re.search('Standard orientation:', line):
                        flags['read_geom'] = True

                    elif flags['read_geom'] == True and re.search(r'^\s*.\d', line):
                        geom.append([float(x) for x in line.split()[3:6]])
                        coord = [float(x) for x in line.split()[3:6]]
                        type = StateBuilder.element_symbol(line.split()[1])
                        atom = matmacore.Atom(coord, type)
                        atoms.append(atom)
                        if int(line.split()[0]) == self.NAtoms:
                            flags['read_geom'] = False

            elif job_type == 'nmr':

                if re.search('SCF Done', line):
                    self.E = float(line.split()[4])
                elif re.search('Coordinates', line) and len(geom) == 0:
                    flags['read_geom'] = True

                elif flags['read_geom'] == True and re.search(r'^\s*.\d', line):
                    geom.append([float(x) for x in line.split()[3:6]])
                    coord = [float(x) for x in line.split()[3:6]]
                    type = StateBuilder.element_symbol(line.split()[1])
                    atom = matmacore.Atom(coord, type)
                    atoms.append(atom)
                    if int(line.split()[0]) == self.NAtoms:
                        flags['read_geom'] = False

                elif re.search('Total nuclear spin-spin coupling J', line):
                    spin = [[] for i in range(self.NAtoms)]
                    flags['jcoup_flag'] = True

                elif flags['jcoup_flag'] == True and re.search(r'-?\d\.\d+[Dd][+\-]\d\d?', line):
                    for x in line.split()[1:]:
                        spin[int(line.split()[0]) - 1].append(float(x.replace('D', 'E')))

                elif flags['jcoup_flag'] == True and re.search('End of Minotr F.D. properties file', line):
                    flags['jcoup_flag'] = False

            elif job_type == 'sp':

                if re.search('SCF Done', line):
                    self.E = float(line.split()[4])
                elif re.search('Standard orientation:', line):
                    flags['read_geom'] = True
                elif flags['read_geom'] == True and re.search(r'^\s*.\d', line):
                    geom.append([float(x) for x in line.split()[3:6]])
                    coord = [float(x) for x in line.split()[3:6]]
                    type = StateBuilder.element_symbol(line.split()[1])
                    atom = matmacore.Atom(coord, type)
                    atoms.append(atom)
                    if int(line.split()[0]) == self.NAtoms:
                        flags['read_geom'] = False

        # postprocessing:
        if job_type == 'freq' or job_type == 'optfreq':
            self.Freq = np.array(freq)
            self.Ints = np.array(ints)
            self.Vibs = np.zeros((self.NVibs, self.NAtoms, 3))
            for i in range(self.NVibs): self.Vibs[i, :, :] = vibs[i]

        if job_type == 'nmr':
            for at in spin:
                while len(at) < self.NAtoms: at.append(0)
            self.nmr = np.tril(spin)

        for i, atom in enumerate(atoms):
            atoms[i].id = i

        self.atoms = atoms

    def cp2k_geom(self):

        """ Parses information from CP2K. Right now only works for AIMD Trajectories, plan to implement opt compatability later.
        """

        with open(self.path, 'r') as geom:
            first_line = geom.readline()
            NAtoms = int(first_line.split()[0])

            raw_coords = geom.readlines()[-NAtoms:]

            coords = np.array([line.split()[1:] for line in raw_coords], dtype=float)
            types = np.array([line.split()[0] for line in raw_coords])

            geom.close()

        index = 0
        atoms = []
        for coord, type in zip(coords, types):
            atom = matmacore.Atom(coord, type, index)
            atoms.append(atom)
            index += 1

        self.NAtoms = NAtoms
        self.atoms = atoms

    def orca(self):

        """ Parses information from ORCA input.log file
        """

        with open(self.path, "r") as f:
            for line in f:
                if "Geometry Optimization Run" in line:
                    output_file = "input.orca.xyz"

                    with open("/".join([self.path, output_file]), "r") as f2:
                        first_line = f2.readline()
                        Natoms = int(first_line.split()[0])

                        second_line = f2.readlines()[0:1]
                        energy = np.array([i.split()[-1] for i in second_line], dtype=float)

                        raw_coords = f2.readlines()[-Natoms:]

                        coords = np.array([line.split()[1:] for line in raw_coords], dtype=float)
                        types = np.array([line.split()[0] for line in raw_coords])

                    self.Natoms = Natoms
                    self.xyz = coords
                    self.type_list = atoms

                    index = 0
                    atoms = []
                    for coord, type in zip(coords, types):
                        atom = matmacore.Atom(coord, type, index)
                        atoms.append(atom)
                        index += 1

                    self.atoms = atoms

                    self.E = energy

                elif "Single Point Calculation" and "FINAL SINGLE POINT ENERGY" in line:
                    # print(line.split()[-1])
                    job_type = "sp"
                    energy = np.array(line.split()[-1], dtype=float)
                    self.E = energy
                    return self

                else:
                    print("Unable to read ORCA log file")

    def build(self):

        from .core import State

        if self.software == 'cp2k': self.cp2k_geom()
        elif self.software == 'gaussian': self.gaussian()
        elif self.software == 'orca': self.orca()
        else: raise ValueError(f"Unsupported software: {self.software}")
        state = State(**self.__dict__)
        state.connectivity_matrix()
        state.system_split()
        return state
    
class DataBuilder:

    def __init__(self, path, software, **kwargs):

        self.path = path
        self.software = software

        for k, v in kwargs.items():
            setattr(self, k, v)

    def cp2k_md(self, colvar=None, timestep=None):

        from .core import State
        from .core import Atom

        self.time_unit = 'fs'  # Default unit in CP2K

        if re.search('.xyz', self.path):
            # Reads colvars straight from the xyz file. Requires specification of timestep and colvar coordinate.
            
            colvar = getattr(self, 'colvar', None) if colvar is None else colvar
            timestep = getattr(self, 'timestep', None) if timestep is None else timestep

            if colvar == None:
                raise ValueError('Error: Specify the atoms for your collective variables.')

            if timestep == None:
                raise ValueError('Error: Specify timestep for reading CP2K trajectories.')

            with open(self.path, 'r') as geom:
                line_1 = geom.readline()
                self.Natoms = int(line_1.split()[0])

                line_cnt = self.Natoms + 2
                line_num = 1
                conf_array = []
                conf_raw_coord = []

                for line in geom:

                    for col in colvar:
                        if line_num % line_cnt == (col+2) % line_cnt:
                            conf_raw_coord.append(line.split())

                    if len(conf_raw_coord) == len(colvar):
                        conf_array.append(conf_raw_coord)
                        conf_raw_coord = []

                    line_num += 1

            conf_array = np.array(conf_array)
            mol_space = []
            colvar_data = []

            for conf in conf_array:
                index = 0
                state = State()
                atoms = []

                for row in conf:
                    type = row[0]
                    xyz = [float(i) for i in row[1:]]

                    atom = Atom(coord=xyz, type=type, index=index)
                    atoms.append(atom)

                    index +=1

                state.atoms = atoms
                mol_space.append(state)

                col_data = StateEditor.measure(atoms)
                colvar_data.append(col_data)

            time = [i / (1 / timestep) for i in range(len(colvar_data))]

            data = np.array(list(zip(time, colvar_data)))
            self.data = data

        elif re.search('.metadynLog', self.path):
            # Reads colvars from the metadynLog file.

            data = np.loadtxt(self.path)

            self.time_unit = 'fs'
            self.data = data
    
    def gromacs(self):
        """ Parses information from gromacs *.xvg file
        """

        # I don't use Gromacs enough to know how the output looks like. Right now, I am just reading the .xvg file:

        if re.search('.xvg', self.path):

            with open(self.path, 'r') as f:
                i = 0
                for line in f.readlines():
                    if re.search('#', line) or re.search('@', line):
                        i = i + 1

                    if re.search('xaxis', line):
                        time_unit = line.split()[-1].strip('()"')
                        self.time_unit = time_unit
                f.close()

            data = np.loadtxt(self.path, skiprows=i)

            self.data = data

        if re.search('.xpm', self.path):

            f = open(self.path, 'r')
            pattern = None;
            matrix_lett = [];
            matrix_dict = {}
            grid = None
            for line in f.readlines():

                if re.search(r'(\d\s\d\b)', line) and grid is None:
                    grid = int(line.split()[1])
                    pattern = grid * '[A-Z]'

                if pattern and re.search(pattern, line):
                    replL1 = line.replace('",', '')
                    replL2 = line.replace('"', '')
                    matrix_lett.append('\n'.join(replL2.split()))

                if re.search('((".*")[0-9])', line):
                    replL1 = line.replace('"', ' ')
                    letters, energy = values = str(replL1.split()[0]), float(replL1.split()[4])
                    matrix_dict.update(dict.fromkeys(letters, energy))

            matrix = np.zeros([grid, grid])
            for i in range(grid):
                for j in range(grid):
                    matrix[grid - i - 1, j] = matrix_dict[matrix_lett[i][j]]

            self.data = matrix

    def csv(self, skiprows=0, dtype=float, delimiter: str = ','):
        """
        Parses a csv file and appends the data to the mol object

        :param file: (string) File containing the csv data.
        :param skiprows: (int) Number of rows to skip
        :param dtype: (type) Data type
        :param delimiter: (str) Delimiter
        """

        skiprows = getattr(self, 'skiprows', skiprows)
        dtype = getattr(self, 'dtype', dtype)
        delimiter = getattr(self, 'delimiter', delimiter)

        self.data = np.loadtxt(self.path, skiprows=skiprows, dtype=dtype, delimiter=delimiter)

    def build(self):

        from .core import Data

        if self.software == 'cp2k': self.cp2k_md()
        elif self.software == 'gromacs': self.gromacs()
        elif self.software == 'csv': self.csv()
        else: raise ValueError(f"Unsupported software: {self.software}")

        return Data(**self.__dict__)