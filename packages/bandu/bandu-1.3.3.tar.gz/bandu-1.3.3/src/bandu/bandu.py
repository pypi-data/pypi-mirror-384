import numpy as np
from typing import Generator
from copy import copy
from . import brillouin_zone as brlzn
from . import translate as trnslt
from . import wfk_class as wc

class BandU():
    def __init__(
        self, wfks:Generator, energy_level:float, width:float, grid:bool=True, fft:bool=True, norm:bool=True,
        sym:bool=True, low_mem:bool=False, plot:bool=True, real_imag_sep:bool=True
    )->None:
        '''
        BandU object with methods for finding states and computing BandU functions from states.

        Parameters
        ----------
        wfks : Generator
            An iterable generator of WFK objects with wavefunction coefficients, k-points, and eigenvalue attributes.
        energy_level : float
            The energy level of interest relative to the Fermi energy.
        width : float
            Defines how far above and below the energy_level is searched for states.
            Search is done width/2 above and below, so total states captured are within 'width' energy.
        grid : bool
            Determines whether or not wavefunction coefficients are converted to 3D numpy grid.
            Default converts to grid (True).
        fft : bool
            Determines whether or not wavefunction coefficients are Fourier transformed to real space.
            Default converts from reciprocal space to real space (True).
        norm : bool
            Determines whether or not wavefunction coefficients are normalized.
            Default normalizes coefficients (True)
        plot : bool
            Plots eigenvalues from principal component analysis.
            Default will save plot (True)
        low_mem : bool
            Run the program on a lower memory setting
            The low_mem tag will print plane wave cofficients to a Python pickle to read from disk later.
            Default does not run in low memory mode (False)

        Methods
        -------
        ToXSF
            Writes real and imaginary parts of BandU functions to XSF files
        '''
        self.grid:bool=grid
        self.fft:bool=fft
        self.norm:bool=norm
        self.sym:bool=sym
        self.low_mem:bool=low_mem
        self.found_states:int=0
        self.bandu_fxns:list[wc.WFK]=[]
        self.plot=plot
        # find all states within width
        self._FindStates(energy_level, width, wfks)
        print(f'{self.found_states} states found within specified energy range')
        # construct principal orbital components
        if real_imag_sep:
            principal_vals = self._RealImagPrnplComps()
        else:
            principal_vals = self._PrincipalComponents()
        # plot eigenvalues from PCA
        if plot:
            self._PlotEigs(principal_vals)
        # normalize bandu functions
        for i in range(self.found_states):
            self.bandu_fxns[i] = self.bandu_fxns[i].Normalize()
        # compute ratios
        if not real_imag_sep:
            omega_vals, omega_check = self._CheckOmega()
        else:
            omega_vals = 0
            omega_check = 0
        # write output file
        fermi = self.bandu_fxns[0].fermi_energy
        with open('eigenvalues.out', 'w') as f:
            print(f'Width: {width}, found states: {self.found_states}', file=f)
            print(f'Energy level: {energy_level+fermi}, Fermi energy: {fermi}', file=f)
            print(np.abs(principal_vals), file=f)   
            print('Omega Values', file=f)
            print(omega_vals, file=f)   
            print('Omega Check (value of 0 indicates Omega is at local extremum)', file=f)
            print(omega_check, file=f)
#---------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------ METHODS ------------------------------------------------------#
#---------------------------------------------------------------------------------------------------------------------#
    # method transforming reciprocal space wfks to real space
    def _FindStates(
        self, energy_level:float, width:float, wfks:Generator[wc.WFK,None,None]
    ):
        # loop through every state
        for state in wfks:
            # check if state has a band that crosses the width
            min_en = state.fermi_energy + energy_level - width/2
            max_en = state.fermi_energy + energy_level + width/2
            for i, band in enumerate(state.eigenvalues):
                if min_en <= band <= max_en:
                    self.found_states += 1
                    coeffs = copy(state)
                    coeffs.wfk_coeffs = coeffs.wfk_coeffs[i]
                    for wfk in self._Process(coeffs):
                        self.bandu_fxns.append(wfk)
        if self.bandu_fxns is []:
            raise ValueError(
            '''Identified 0 states within provided width.
            Action: Increase width or increase fineness of kpoint grid.
            ''')
    #-----------------------------------------------------------------------------------------------------------------#
    # method for processing planewave coefficient data from FindStates
    def _Process(
            self, state:wc.WFK
    )->Generator[wc.WFK,None,None]:
        funcs:list[wc.WFK] = []
        # generate symmetrically equivalent coefficients
        if self.sym:
            for sym_coeffs in state.SymWFKs(kpoint=state.kpoints):
                self.found_states += 1
                funcs.append(sym_coeffs)
            self.found_states -= 1
        else:
            # shift point back into Brillouin Zone as necessary
            rec_latt = state.Real2Reciprocal()
            shift = brlzn.BZ(rec_latt=rec_latt).GetShifts(state.kpoints)
            state.pw_indices += shift
            state.kpoints = state.kpoints.reshape((-1,3)) - shift
            funcs.append(state)
        # apply desired transformations
        for wfk in funcs:
            if self.grid:
                wfk = wfk.GridWFK()
            if self.fft:
                wfk = wfk.IFFT()
            if self.norm:
                wfk = wfk.Normalize()
            yield wfk
    #-----------------------------------------------------------------------------------------------------------------#
    # check if states along BZ edge have been collected
    # --not functional--
    def _CheckEdgeCase(
        self
    ):
        bz = brlzn.BZ(self.bandu_fxns[0].Real2Reciprocal())
        x = self.bandu_fxns[0].ngfftx
        y = self.bandu_fxns[0].ngffty
        z = self.bandu_fxns[0].ngfftz
        all_shifts:list[np.ndarray] = []
        wfk_to_shift:list[int] = []
        dupes:list[wc.WFK] = []
        for i, wfk in enumerate(self.bandu_fxns):
            # if point on edge, translate to find other periodic points
            edge_pts = bz._BZEdgePt(wfk.kpoints)
            print(wfk.kpoints)
            print(edge_pts)
            if len(edge_pts[edge_pts > 0]) > 0:
                shifts, _ = trnslt.TranslatePoints(np.zeros((1,3)), np.zeros(1), np.identity(3))
                shifts = shifts[edge_pts > 0].astype(int)
                all_shifts.append(shifts)
                wfk_to_shift.append(i)
        for i in wfk_to_shift:
            for shifts in all_shifts:
                for shift in shifts:
                    shifted_wfk = copy(self.bandu_fxns[i])
                    shifted_wfk = shifted_wfk.RemoveGrid()
                    shifted_wfk.pw_indices += shift
                    shifted_wfk = shifted_wfk.GridWFK()
                    shifted_wfk.wfk_coeffs = shifted_wfk.wfk_coeffs.reshape((1,x*y*z))
                    shifted_dupe = copy(self.bandu_fxns)
                    shifted_dupe[i] = shifted_wfk
                    dupes.extend(shifted_dupe)
                    self.duped_states += self.found_states
        self.bandu_fxns.extend(dupes)
    #-----------------------------------------------------------------------------------------------------------------#
    # find principal components
    def _PrincipalComponents(
        self
    )->np.ndarray:
        total_states = self.found_states
        # organize wfk coefficients 
        x = self.bandu_fxns[0].ngfftx
        y = self.bandu_fxns[0].ngffty
        z = self.bandu_fxns[0].ngfftz
        mat = np.zeros((total_states,x*y*z), dtype=complex)
        for i in range(total_states):
            mat[i,:] = self.bandu_fxns[i].wfk_coeffs.reshape((1,x*y*z))
        # compute overlap matrix
        print('Computing overlap matrix')
        overlap_mat = np.matmul(np.conj(mat), mat.T)
        # diagonlize matrix
        principal_vals, principal_vecs = np.linalg.eig(overlap_mat)
        principal_vecs = principal_vecs.T
        # organize eigenvectors and eigenvalues
        sorted_inds = np.flip(principal_vals.argsort())
        principal_vals = np.take(principal_vals, sorted_inds)
        principal_vecs = np.take(principal_vecs, sorted_inds, axis=0)
        mat = np.matmul(principal_vecs, mat)
        for i in range(total_states):
            self.bandu_fxns[i].wfk_coeffs = mat[i,:]
        return principal_vals 
    #-----------------------------------------------------------------------------------------------------------------#
    # find principal components with real and imaginary separated
    def _RealImagPrnplComps(
        self
    )->np.ndarray:
        x = self.bandu_fxns[0].ngfftx
        y = self.bandu_fxns[0].ngffty
        z = self.bandu_fxns[0].ngfftz
        mat = np.zeros((2*self.found_states,x*y*z), dtype=complex)
        for i in range(self.found_states):
            ind = 2*i
            real_coeffs = self.bandu_fxns[i].wfk_coeffs.real
            imag_coeffs = self.bandu_fxns[i].wfk_coeffs.imag
            mat[ind,:] = real_coeffs.reshape((1,x*y*z))
            mat[ind+1,:] = imag_coeffs.reshape((1,x*y*z))
        print('Computing overlap matrix')
        overlap_mat = np.matmul(np.conj(mat),mat.T)
        # diagonlize matrix
        principal_vals, principal_vecs = np.linalg.eig(overlap_mat)
        principal_vecs = principal_vecs.T
        # organize eigenvectors and eigenvalues
        sorted_inds = np.flip(principal_vals.argsort())
        principal_vals = np.take(principal_vals, sorted_inds)
        principal_vecs = np.take(principal_vecs, sorted_inds, axis=0)
        mat = np.matmul(principal_vecs, mat)
        for i in range(2*self.found_states):
            if i < self.found_states:
                self.bandu_fxns[i].wfk_coeffs = mat[i,:]
            else:
                new_coeffs = copy(self.bandu_fxns[0])
                new_coeffs.wfk_coeffs = mat[i,:]
                self.bandu_fxns.append(new_coeffs)
        self.found_states *= 2
        return principal_vals 
    #-----------------------------------------------------------------------------------------------------------------#
    # find ratio of real and imaginary components
    def _CheckOmega(
        self
    )->tuple[np.ndarray, np.ndarray]:
        total_states = self.found_states
        omega_vals = np.zeros((total_states, 3), dtype=float)
        vals = np.linspace(start=-0.01, stop=0.01, num=3)
        for i, val in enumerate(vals):
            for j in range(total_states):
                coeffs:np.ndarray = copy(self.bandu_fxns[j].wfk_coeffs)
                coeffs *= np.exp(1j*val*np.pi)
                omega = np.sum(coeffs.real*coeffs)/np.sum(coeffs.imag*coeffs)
                omega = np.abs(omega)
                omega_vals[j,i] = omega
        omega_diff1 = (omega_vals[:,1] - omega_vals[:,0])
        omega_diff2 = (omega_vals[:,2] - omega_vals[:,1])
        omega_check = np.sign(omega_diff1) + np.sign(omega_diff2)
        return omega_vals[:,1], omega_check
    #-----------------------------------------------------------------------------------------------------------------#
    # plot eigenvalues from PCA
    def _PlotEigs(
        self, eigvals:np.ndarray
    ):
        import matplotlib.pyplot as plt
        x = np.arange(self.found_states) + 1
        y = np.abs(eigvals.flatten())
        figsize = (12,6)
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot()
        ax.plot(
            x, 
            y, 
            color='black', 
            linestyle='-', 
            marker='o', 
            mfc='red', 
            markersize=8
        )
        ax.spines[['right','top']].set_visible(False)
        ax.tick_params(axis='both', labelsize=12)
        plt.xlim(1.0,len(y)+5.0)
        plt.ylim=(0,np.max(y))
        mod_val = round(self.found_states/5 - 0.5)
        plt.xticks(ticks=[val for val in range(0,len(y)+1) if val % mod_val == 0])
        plt.rcParams['font.family'] = 'Times New Roman'
        plt.savefig('bandu_eigenvalues.png',dpi=500)
    #-----------------------------------------------------------------------------------------------------------------#
    # make xsf of BandU functions
    def ToXSF(
        self, nums:list[int]=[], xsf_name:str='Principal_orbital_component'
    ):
        total_states = self.found_states
        if nums is []:
            nums = [1,total_states]
        else:
            # check if list has only 2 elements
            if len(nums) != 2:
                raise ValueError(f'nums should contain two values, {len(nums)} were received.')
            # check if function number is within defined range
            if nums[0] < 1:
                print('First element of nums cannot be lower than 1, changing to 1 now.')
                nums[0] = 1
            # update function number list if it exceeds maximum number of bandu functions
            if nums[1] > total_states:
                print(f'Printing up to max Band-U function number: {total_states}')
                nums[1] = total_states
            # check if lower limit is within defined range
            if nums[0] > nums[1]:
                nums[0] = nums[1]
        print(f'Writing XSF files for Band-U functions {nums[0]} through {nums[1]}.')
        # write xsf files
        x = self.bandu_fxns[0].ngfftx
        y = self.bandu_fxns[0].ngffty
        z = self.bandu_fxns[0].ngfftz
        for i in range(nums[0]-1, nums[1]):
            file_name = xsf_name + f'_{i+1}'
            wfk = copy(self.bandu_fxns[i])
            wfk.wfk_coeffs = wfk.wfk_coeffs.reshape((x,y,z))
            wfk = wfk.XSFFormat()
            wfk.WriteXSF(xsf_file=file_name)