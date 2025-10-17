from turtle import color

import matplotlib
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import colormaps
import copy
from math import log

import matplotlib as mpl
from matplotlib.ticker import NullFormatter
from matplotlib.ticker import FormatStrFormatter
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from matplotlib.ticker import FuncFormatter
from numpy.ma.extras import average

class Plot():
    """
    A class that creates plots from a numpy array.
    It can make reaction coordinate diagrams, RMSD and RMSF trajectory plots,
    Free energy plots, Scatter Plots, and SNFG Figures.
    """

    def __init__(self) :

        """
        Constructs a plot object.
        :param data: (array) a numpy array containing the data to be plotted.
        """

        config_dict = {
            'xrange': None,
            'yrange': None,
            'xtick': None,
            'ytick': None,
            'xlabel': None,
            'ylabel': None,
            'title': None,
            'font': None,
            'xextend': None,
            'yextend': None,
            'title fontsize': None,
            'axis fontsize': None,
            'tick fontsize': None,
        }

        self.config_dict = config_dict

        # RK: Just set some default colors for ease of use, adjust as needed. 
        self.set_colors(["#4856d1", "#f3a667", '#e31a1c', '#1f78b4', '#53546c'])

    def cmap(self, color_num: int = None, offset: float = 0, map: str = 'ice', reverse: bool = False) :
        """
        Generates and processes a colormap with optional offsetting logic.
        :param color_num: (int) Number of discrete colors.
        :param offset: (float) Fractional offset to shift the colormap.
        :param map: (str) Name of the colormap from the colormaps library.
        """
        # Check if the colormap exists in colormaps
        if not hasattr(colormaps, map):
            raise ValueError(f"Colormap '{map}' not found in colormaps library!")

        # Fetch colormap
        colors_obj = getattr(colormaps, map)

        if color_num is not None:
            color_num += 1
        # Ensure the colormap has an array of colors
        if not hasattr(colors_obj, 'colors'):
            raise ValueError(f"The selected colormap '{map}' does not have a valid 'colors' attribute!")

        colormap_colors = colors_obj.colors

        # Validating the shape of colormap_colors
        if len(colormap_colors[0]) != 3:
            raise ValueError(f"Expected RGB colors in the colormap, but got shape {np.array(colormap_colors).shape}.")

        # Applying offset manually

        if offset != 0:
            new_colors = []

            for color in colormap_colors:

                new_color = []
                for color_elm in color:
                    color_elm -= offset

                    if color_elm > 1:
                        color_elm = 1

                    if color_elm < 0:
                        color_elm = 0

                    new_color.append(color_elm)
                new_colors.append(new_color)

            colormap_colors = new_colors


        if reverse:
            colormap_colors = list(reversed(colormap_colors))

        # Discretize the colormap to the required number of colors
        if color_num is not None:
            discrete_colors = np.linspace(0, len(colormap_colors) - 1, color_num, dtype=int)
            self.colors = [colormap_colors[i] for i in discrete_colors]
        else:
            self.colors = colormap_colors.tolist()

    def savefig(self, filename='fig', format:str='png'):
        self.fig.savefig(f"{self.path}/{filename}.{format}", dpi=300, bbox_inches='tight')

    def set_colors(self, colors:list = None):
        self.colors = colors

    def set_config(self, conf:dict):
        old_conf = self.config_dict

        for key, value in old_conf.items():
            if key not in conf.keys():
                conf[key] = value

        self.config_dict = conf

    def set_axes(self, ax:matplotlib.pyplot.axes):
        from matplotlib import rc

        config_dict = self.config_dict

        for key, value in config_dict.items():

            if key == 'xrange' and value is not None:
                ax.set_xlim(value[0], value[1])
            if key == 'yrange' and value is not None:
                ax.set_ylim(value[0], value[1])
            if key == 'xticks' and value is not None:
                ax.set_xticks(value)
            if key == 'yticks' and value is not None:
                ax.set_yticks(value)
            if key == 'xlabel' and value is not None:
                ax.set_xlabel(value)
            if key == 'ylabel' and value is not None:
                ax.set_ylabel(value)
            if key == 'title' and value is not None:
                ax.set_title(value)
            if key == 'font' and value is not None:
                mpl.rcParams['font.sans-serif'] = value
                mpl.rcParams['font.family'] = "sans-serif"
            if key == 'axis fontsize' and value is not None:
                mpl.rcParams['axes.labelsize'] = value
            if key == 'title fontsize' and value is not None:
                ax.title.set_size(value)
            if key == 'tick fontsize' and value is not None:
                ax.tick_params(labelsize=value, axis='both')

    def trajectory(self, data_list, var_name = 'colvar', col = 1, average=None, title=None, hist=True, alpha=None, calc_qa=False, overlap=False):
      
        """ Plots MD trajectory with histogram. Takes in data for CP2K or Gromacs via Mol.
        :param data_list: (Mol / List) Either a Data object, or a list of Data objs if you want to overlay data. 
        :param var_name: (list) Name of the collective variable you are plotting on your y-axis.
        :param col: (int) Index of the column containing your colvar data, in the case that you have multiple.
        """
        if not isinstance(data_list, list):
            data_list = [data_list]

        self.path = data_list[0].path
        # CP2K default timestep unit is in fs, Gromacs is in ps:
        # We convert these to ps and nm respectively:
 
#         if mol_list[0].software == 'cp2k':
#             time_unit = 'ps'
 
#         elif mol_list[0].software == 'gromacs':
#             time_unit = self.time_unit
            
        fig, ax = plt.subplots(1,2, figsize=(11,3), gridspec_kw={'width_ratios': [3.5, 1]})
        
        i = 0
        
        if alpha == None:
            alpha = [0.8] * len(data_list)
            
        if average == None:
            average = [0] * len(data_list)
            
        elif not isinstance(average, list):
            average = [average] * len(data_list)
            
        for datum in data_list:

            residue = False
            
            if datum.time_unit == 'fs':
                time = (datum.data[:, 0] / 1000).tolist()  # fs -> ps for CP2K
                time_label = 'ps'
            
            elif datum.time_unit == 'ps':
                time = (datum.data[:, 0] / 1000).tolist()  # ps -> ns for GROMACS
                time_label = 'ns'
                
            elif datum.time_unit == 'ns':
                time = (datum.data[:, 0]).tolist() # if GROMACS already in ns don't convert
                time_label = 'ns'

            elif datum.time_unit == 'Residue':
                time = (datum.data[:, 0]).tolist() # if GROMACS in residue, also don't convert
                time_label = 'residue'
                residue = True

            colvar = datum.data[:, col].tolist()
 
            timestep = np.abs(time[0] - time[1])

            if not hasattr(self, 'colors'):
                self.cmap(color_num=len(data_list),offset=0,map='ice')
            
            color = self.colors
            
            if average[i] > 1:
                array_len =  len(colvar)
                # conv_kernel = np.ones(average[i])/array_len
                conv_kernel = np.ones(average[i])/average[i]
                colvar_conv = np.convolve(colvar, conv_kernel, mode='valid').tolist()
                time = time[:-1*average[i] + 1]

            if overlap == True:

                ax[0].plot(time, colvar_conv, linewidth=2, color=color[i], alpha=alpha[i])
                ax[0].plot(time,colvar[:(len(colvar_conv))],linewidth=0.8, color = color[i], alpha=alpha[i]*.3)
                ax[1].hist(colvar, bins='rice', orientation="horizontal", color=color[i], alpha=alpha[i])
            
            elif overlap == False and average[i] > 1:
                ax[0].plot(time,colvar_conv,linewidth=0.8, color=color[i], alpha=alpha[i])
                
            else:
                ax[0].plot(time,colvar,linewidth=0.8, color=color[i], alpha=alpha[i])
                ax[1].hist(colvar, bins='rice', orientation="horizontal", color=color[i], alpha=alpha[i], label=np.round(np.average(colvar)))
        
            if calc_qa == True:

                nbins = 50
                hist = np.histogram(colvar[500:], nbins, range=(min(colvar), max(colvar)))
                
                dmin = np.argmin(hist[0][15:23])+15
                bs = np.sum(hist[0][:dmin+1]) ; us = np.sum(hist[0][dmin+1:])

                if us == 0: Qa = 1000.0 ; boundary = 0.0
                
                else:
                    Qa =  float(bs)/float(us) ; boundary = float (dmin)/10
                    
                # ax[1].fill_between([0, ax[1].get_xlim()[1]], boundary, boundary+0.1, color='0.8')
                
                # Only annotate Qas if one trajectory is entered, otherwise print them.
                if len(data_list) == 1:
                    ax[1].axhline(y=boundary, color='gray', linestyle='-', alpha=0.5, linewidth=5)

                    textstr = r'$Q_a$={0:3.2f}'.format(Qa)
                    ax[1].text(0.55 * ax[1].get_xlim()[1], 0.95 * ax[1].get_ylim()[1], textstr, fontsize=14, verticalalignment='top')
                    
                else:
                    print(f"mol{i+1} Qa = {np.round(Qa, 3)}")

            #if len(data_list) == 1:
            #    ax[1].set_title(f"average = {np.round(np.average(colvar), 3)}", fontsize = 10)
 
            #else:
                
                #x= (np.round(np.average(colvar), 3))
                #ax[1].legend()
                #print(x)

            print(f"average = {np.round(np.average(colvar), 2)}") 
 
            i = i+1

        if not residue:
            ax[0].set_xlabel(f"time ({time_label}); stepsize = {timestep}{time_label}")
        
        else:
            ax[0].set_xlabel(f"{time_label}")

        ax[0].set_ylabel(var_name)
        
        if title != None:
            ax[0].set_title(f"{title}", fontsize = 10)
            
        if hist == False:
            fig.delaxes(ax[1])

        if not residue:
            xmax = ax[0].get_xlim()[1]
            xmax = xmax + 1     
            ax[0].set_xlim(0, xmax) 
        
        ax[1].set_xlabel('structures')
        
        self.set_axes(ax[0])
        
        # Hard code the y axis of the histogram to align with the trajectory:
        for key, value in self.config_dict.items():
            if key == 'yrange' and value is not None:
                ax[1].set_ylim(value[0], value[1])
                
        plt.tight_layout()
        self.fig = fig
        self.ax = ax

    def fes(self, data, cols=[1,2], temp=300, num_levels = 8, num_ticks = 8):

        """ Plots MD FES. Takes in data for CP2K or Gromacs via Mol.
        :param data: (Data) Class Data.
        :param cols: (int) Index of the 2 columns containing your colvar data, in the case that you have more than 2.
        """
        
        self.path = data.path
        Temp = temp ; R = 8.314 # J/K mol

        colvar1 = data.data[:, cols[0]]
        colvar2 = data.data[:, cols[1]]

        Hall, x_edges, y_edges = np.histogram2d(colvar1, colvar2, bins=72)

        Hall = - R * Temp * np.log(Hall)
        hmin = np.min(Hall)
        
        Hall_rel = 0.001*(Hall.T-hmin)

        vmin, vmax = 0, np.ceil(np.nanmax(Hall_rel[~np.isinf(Hall_rel)]))
        MHall = np.ma.masked_greater(Hall_rel, vmax)

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_aspect('equal', adjustable='box')

        # colors = self.colors
        # cmap = ListedColormap(colors)

        num_levels = num_levels
        plot = ax.contourf(x_edges[:-1], y_edges[:-1], MHall, cmap='Blues_r', zorder=1, levels=num_levels)
        # plot = ax.contourf(x_edges[:-1], y_edges[:-1], Hall.T, cmap=cmap, zorder=1, levels=num_levels)

        num_ticks = num_ticks
        x_ticks = np.linspace(x_edges[0], x_edges[-1], num_ticks)
        y_ticks = np.linspace(y_edges[0], y_edges[-1], num_ticks)
        ax.set_xticks(x_ticks)
        ax.set_yticks(y_ticks)
        ax.set_xticklabels([f"{tick:.1f}" for tick in x_ticks], fontsize=12)
        ax.set_yticklabels([f"{tick:.1f}" for tick in y_ticks], fontsize=12)

        cb_ticks = np.linspace(vmin, vmax, 6)
        cb = fig.colorbar(plot, ax=ax, ticks=cb_ticks, pad=0.05, shrink=0.78)
        cb.ax.set_yticklabels([f"{tick:.1f}" for tick in cb_ticks], fontsize=12)
        cb.set_label("\n Free energy [kJ]", fontsize=14)

        # Enable grid that aligns with ticks
        ax.grid(True, ls='--', zorder=10.0)

        # Axis labels and title
        ax.set_xlabel("colvar1", fontsize=14)
        ax.set_ylabel("colvar2", fontsize=14)

        # fig.tight_layout()
        
        self.fig = fig
        self.ax = ax

    def contour(self, xpm_data_list, limit = 16):
    
        """ Plots contour maps for a provided list of moles from xpm files.
        :param xpm_mols: (List) List of mol objects generated from xpm files.
        :param limit: (Int) The upper limit on your energy scale
        """
        
        self.path = xpm_data_list[0].path
        limit = limit
        
        Mat = []
        
        for xpm_data in xpm_data_list:
            M = xpm_data.data
            MM = np.ma.masked_greater(M, limit-1)
            Mat.append(MM)
        
#         if xpm_mol1 != None and xpm_mol2 != None and xpm_mol3 != None: 
#             M1 = xpm_mol1.data
#             M2 = xpm_mol2.data
#             M3 = xpm_mol3.data
#             MM1 = np.ma.masked_greater(M1, limit-1)
#             MM2 = np.ma.masked_greater(M2, limit-1) 
#             MM3 = np.ma.masked_greater(M3, limit-1) 
#             Mat = [MM1, MM2, MM3]

#         elif xpm_mol1 != None and xpm_mol2 != None:
#             M1 = xpm_mol1.data
#             M2 = xpm_mol2.data
#              #DiffM = M1-M2
#             MM1 = np.ma.masked_greater(M1, limit-1)
#             MM2 = np.ma.masked_greater(M2, limit-1)  
#             Mat = [MM1, MM2]

#         else:
#             raise ValueError("Give me a correct number of some chunky matrices")
        fig, axes = plt.subplots(1,len(Mat), figsize=(4*len(Mat) + (len(Mat)-1)*1,  4), sharex=True, sharey=True)
        # fig, axes = plt.subplots(1,len(Mat), figsize=(4*len(Mat) + 1.5, 4), sharex=True, sharey=True)
        
        color_bar = ['Blues_r']*len(Mat)
        color = self.colors
        color.reverse()
        cmap = ListedColormap(color)

        levels = np.linspace(0, limit, 9)  # 8 levels between 0 and limit

        for n, ax in enumerate(axes):
            ax.set_aspect('equal', adjustable='box')
            ax.grid(True, ls='--', zorder=10.0)

            # Set x-axis ticks and labels
            xmin, xmax = -180.0, 180.0
            xticks = np.linspace(xmin, xmax, 7)
            ax.set_xticks(np.linspace(0, 71, 7))
            ax.set_xticklabels(['{0:d}'.format(int(x)) for x in xticks], fontsize=12)
            ax.set_xlabel(r'$\phi$', fontsize=14)

            # Set y-axis ticks and labels
            ymin, ymax = -180.0, 180.0
            yticks = np.linspace(ymax, ymin, 7)[::-1]
            ax.set_yticks(np.linspace(0, 71, 7))
            ax.set_yticklabels(['{0:d}'.format(int(x)) for x in yticks], fontsize=12)

            if n == 0:
                ax.set_ylabel(r'$\psi$', fontsize=14)

            # Create the contourf plot with consistent levels
            plot = ax.contourf(Mat[n], levels=levels, cmap=cmap, zorder=1)

            # Add a color bar with consistent boundaries and ticks
            cb = fig.colorbar(plot, ax=ax, pad=0.025, aspect=20, ticks=levels)
            cb.set_ticklabels(["{0:3.1f}".format(x) for x in levels])

        fig.tight_layout()
        
        self.fig = fig
        self.ax = axes
    
    def foo_plot(self, data, SCR = None, w = 0.5):
        
        """ Not a bar plot. Mostly used for SCR stuff
        :param data: (Data) Data objects generated from csv files.
        :param SCR: (list) Specifies specific SCRs to plot from your data. Otherwise, default is to plot them all.
        :param w: (float) Width of the lines in the foo plot.
        """
        
        color = self.colors
        self.path = data.path

        if SCR == None:

            SCR = []
            for line in data.data[1:]:
                SCR.append(line.split()[0])

        SUG = data.data[0].split(); data_dict = {}

        for line in data.data[1:]:
            # Doctor Founder says not to transform the data, only plot the data:
            # data[line.split()[0]] = [log(float(i)*(float(i)+1)/C0,10) for i in line.split()[1:]]
            
            data_dict[line.split()[0]] = [float(i) for i in line.split()[1:]]

        fig, ax = plt.subplots(figsize=(8.0, 4.0))

        ax.tick_params(axis='both', which='both', bottom=True, top=False, labelbottom=True, right=False, left=False, labelleft=True, labelright=False)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.xaxis.set_tick_params(direction='out')

        x_pos = np.arange(len(SUG))
        xmax = len(SUG)
        
        ax.set_xlim(-1,xmax)
        
        ymin=0; ymax=np.round(max(val for sublist in data_dict.values() for val in sublist))
        ax.set_ylim(ymin, ymax+0.1)
        yticks=np.linspace(ymin,ymax,7)
        ax.set_yticks(yticks)
        # ax.set_yticklabels(yticks)

        ax.set_xticks(x_pos)
        ax.set_xticklabels(SUG)

        #ax.set_xlabel(r'time [ns]')
        for i in yticks:  ax.plot([-1,xmax], [i,i], '0.75', lw=0.5)
        
        ax.grid(axis='y', color='grey', linestyle='-', linewidth=0.5)

        for n, scr in enumerate(SCR):
            for i in range(len(SUG)):
                ax.plot([x_pos[i]-w/2, x_pos[i]+w/2], [data_dict[scr][i], data_dict[scr][i]], color = color[n], lw=2)

                #ax.bar ( x_pos[i], data[scr][i], align='center', color=color[n])

        plt.setp(ax.get_xticklabels(), rotation=45, ha="right", rotation_mode="anchor")
        
        self.set_axes(ax)

        fig.tight_layout()
        self.fig = fig
        self.ax = ax


    def scatter(self, data=None, headers=None, format:str ='.', figsize=(6,6)):

        """
        Generates a scatter plot from data
        """
        data_list = []
        if isinstance(data, list):
            for set in data:
                data_list.append(set.data)
        else:
            data = data.data
            data_list.append(data)
            
        if headers != None:
            desc = headers

        #x_extend = 0
        #y_extend = 0

        colors = self.colors if self.colors is not None else ['b', 'r', 'g', 'c', 'm', 'y', 'k']
        fig, ax = plt.subplots(1, 1, figsize=figsize)

        for i, data in enumerate(data_list):

            if data.ndim == 2:
                data_x = data[:, 0]
                data_ys = []
                row_len = len(data[0,:])
            else:
                data_x = data[0]
                data_ys = []
                row_len = len(data)

            nullfmt = NullFormatter()         # no labels

            #fig, ax = plt.subplots(1, figsize=figsize)

            for col in range(1, row_len):
                if data.ndim == 2:
                    data_y = data[:,col]
                    data_ys.append(data_y)
                else:
                    data_y = data[col]
                    data_ys.append(data_y)

                fit = np.polyfit(data_x, data_y, 1)
                val = np.polyval(fit, data_x)

                if headers is not None:
                    if len(data_list) == 1:
                        ax.scatter(data_x, data_y, marker=format, label=desc[col-1], color = colors[col-1])
                        ax.legend()
                    else:
                        ax.scatter(data_x, data_y, marker=format, label=desc[i], color=colors[i])
                        ax.legend()

                else:
                    if len(data_list) == 1:
                        ax.scatter(data_x, data_y, marker=format, color = colors[col-1])
                    else:
                        ax.scatter(data_x, data_y, marker=format, color = colors[i])

        ax.tick_params(axis='both', which='both', bottom=True, top=False, labelbottom=True, right=False, left=True, labelleft=True)
        for s in ['top', 'right']:
            ax.spines[s].set_visible(False)
        ax.xaxis.set_tick_params(direction='out')
        ax.yaxis.set_tick_params(direction='out')

        self.set_axes(ax)

        xmin, xmax = ax.get_xlim()[0], ax.get_xlim()[1]
        ymin, ymax = ax.get_ylim()[0], ax.get_ylim()[1]

        #if x_extend != 0.0 : 
        #    xmin -= x_extend ; xmax += x_extend
        #    ax.set_xlim(xmin, xmax)
        #    print(xmin, xmax)

        #if y_extend != 0.0: 
        #    ax.set_ylim(ymin-y_extend, ymax)

        #ax.plot([xmin, xmax], [ymin-y_extend, ymin-y_extend], 'k', lw=1)
        #ax.plot([xmin+ax_fit, xmin+ax_fit], [ymin ,ymax], 'k', lw=1)

        plt.tight_layout()
        self.fig = fig
        self.ax = ax

    def gaussian_broadening(self, state, broaden=1, resolution=1):

        """ Performs gaussian broadening on IR spectrum
        generates attribute self.IR - np.array with dimmension 4000/resolution consisting gaussian-boraden spectrum

        :param broaden: (float) gaussian broadening in wn-1
        :param resolution: (float) resolution of the spectrum (number of points for 1 wn) defaults is 1, needs to be fixed in plotting
        """

        IR = np.zeros((int(4000 / resolution) + 1,))
        X = np.linspace(0, 4000, int(4000 / resolution) + 1)
        for f, i in zip(state.Freq, state.Ints):  IR += i * np.exp(-0.5 * ((X - f) / int(broaden)) ** 2)
        state .IR = np.vstack((X, IR)).T  # tspec

    def ir(self, state, xmin = 900, xmax = 1700, normal_modes:bool = False):

        """ Plots the IR spectrum in xmin -- xmax range,
        x-axis is multiplied by scaling factor, everything
        is normalized to 1. If exp_data is specified,
        then the top panel is getting plotted too.
        Need to add output directory. Default name is self._id
        """

        import matplotlib.pyplot as plt
        from matplotlib.ticker import NullFormatter
        import math

        colors = self.colors
        background_colors = []

        for color in colors:
            color[0] += 0.25
            color[1] += 0.25
            color[2] += 0.25
            background_colors.append(color)

        fig, ax = plt.subplots(1, figsize=(math.ceil(10*(xmax-xmin)/(1500)),3))

        self.gaussian_broadening(state ,resolution=0.001,broaden=2)

        #left, width = 0.02, 0.98 ; bottom, height = 0.15, 0.8
        #ax  = [left, bottom, width, height ]
        #ax  = plt.axes(ax)
        exten = 20

        ax.tick_params(axis='both', which='both', bottom=True, top=False, labelbottom=True, right=False, left=False, labelleft=False)
        ax.spines['top'].set_visible(False) ; ax.spines['right'].set_visible(False) ; ax.spines['left'].set_visible(False)
        ax.xaxis.set_tick_params(direction='out')
        ax.yaxis.set_major_formatter(NullFormatter())
        ax.set_ylim(0,1.1)

        xticks = np.linspace(xmin,xmax,int((xmax-xmin+2*exten)/100)+1)
        ax.set_xticks(xticks)
        ax.set_xticklabels([int(x) for x in xticks], fontsize=10)
        ax.set_xlim(xmin-exten, xmax+exten+10)

        shift = 0.05
        incr = (state.IR[-1,0] - state.IR[0,0])/(len(state.IR)-1)
        scale_t  =  1/np.amax(state.IR[int(xmin/incr):int(xmax/incr)+100,1])

        Xsc = state.IR[:,0] ; IRsc = state.IR[:,1]*scale_t
        ir_theo = ax.plot(Xsc, IRsc+shift, color='k', linewidth=0.5)
        ax.fill_between(Xsc, np.linspace(shift, shift, len(IRsc)), IRsc+shift, color=background_colors[0], alpha=0.5)

        if normal_modes == True:
            for l in range(len(state.Freq)):
                 ax.plot([state.Freq[l], state.Freq[l]], [shift, state.Ints[l]*scale_t+shift], linewidth=2, color=colors[0])

        fig.tight_layout()
        current_path = os.getcwd()
        #output_path =  os.path.join(current_path, state.path, state._id+'.png')
        #print(output_path + state._id+'.png')

    def space(self, list_of_spaces, names=None, quant:str = 'E'):

        fig, ax = plt.subplots()

        n = 0

        for space in list_of_spaces:

            # if quant == 'E': data = space.energies
            # elif quant == 'F': data = space.free_energies
            # elif quant == 'H': data = space.enthalpies

            data = space.diff(quant=quant)

            if names == None:
                name = [str(n)] * len(data)
            else:
                name = names[n]

            ax.scatter(name, data, marker='_', linewidths=3, s=700)

            n = n + 1

        if n != 1:
            
            pad = 1 / (n - 1)
            ax.set_xmargin(pad)

        plt.ylabel(f"{quant} (Ha)")
        plt.xlabel('conformer id')

        self.set_axes(ax)
