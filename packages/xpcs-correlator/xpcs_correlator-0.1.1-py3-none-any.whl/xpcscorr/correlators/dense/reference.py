import numpy as np

from xpcscorr.core.base import Results
from xpcscorr.correlators.dense.base import DenseCorrelator
from xpcscorr.core.utils import (mask_to_3d_bool_stack, 
                                 lin_bin , 
                                 lin_log_bin, 
                                 bin_centers,
                                 bin_centers_mixed,
                        )

class CorrelatorDenseReference(DenseCorrelator):
    '''
    Implementation of the dense correlator for reference.
    '''

    def __init__(self, frames, roimask, **kwargs):
        super().__init__(frames, roimask, **kwargs)

        self.ttcf_format = kwargs.get('ttcf_format', None)
        self.t1_t2_binning = kwargs.get('t1_t2_binning', None)
        self.age_binning = kwargs.get('age_binning', None)
        self.lag_binning = kwargs.get('lag_binning', None)
        self.extra_options = kwargs.get('extra_options', None)

        # ---Mask processing---
        self.roimask = mask_to_3d_bool_stack(self.roimask)

        if self.roimask.ndim == 2:
            self.roimask = self.roimask[np.newaxis, ...]

        self.mask_num = self.roimask.shape[0]
        
        # --- Results initialization ---
        self.results=Results(
                             roimask= self.roimask, 
                             ttcf_format=self.ttcf_format, 
                            )
        # --- Computation ---                     
        self._compute()


    def _compute(self):

        #1 setting all variables and conditions
        calculate_ttcf = bool(self.ttcf_format)
        calculate_g2_err = True #TODO as an option ?
        

        for i in range(self.roimask.shape[0]):
            self._workflow(self.frames, 
                            self.roimask[i], 
                            calculate_g2_err, 
                            calculate_ttcf,
                            i)

    def _workflow(self, frames, mask, calculate_g2_err, calculate_ttcf, calc_num):

        g2, g2_err, ttcf = self.correlate(frames, mask, calculate_g2_err, calculate_ttcf)

        # initialize result arrays for g2 and g2_err
        if self.results.g2 is None:
            self.results.g2=np.empty((self.mask_num,g2.size))
        
        if self.results.g2_err is None and g2_err is not None:
            self.results.g2_err=np.empty((self.mask_num,g2.size))
        
        # g2 calculation
        self.results.g2[calc_num] = g2
        # g2 error calculation
        if g2_err is not None and self.results.g2_err is not None:
            self.results.g2_err[calc_num] = g2_err

        # ttcf calculations
        if  calculate_ttcf:
            # ttcf in t1,t2 format with binning
            if self.ttcf_format == 't1,t2':
                if self.t1_t2_binning is not None:                        
                        ttcf, t1, t2 = self.bin_ttcf(ttcf, self.t1_t2_binning)
                        self._add_ttcf(ttcf, calc_num)
                        self.results.t1 = t1 
                        self.results.t2 = t2
                # ttcf in t1,t2 without binning
                elif ttcf is not None:
                    self._add_ttcf(ttcf, calc_num)
                    self.results.t1 = np.arange(frames.shape[0])
                    self.results.t2 = np.arange(frames.shape[0])
            # ttcf in age,lag with binning
            if self.ttcf_format == 'age,lag':
                ttcf, lag, age = self.bin_ttcf_age_lag(ttcf,self.age_binning, self.lag_binning)
                self._add_ttcf(ttcf, calc_num)
                self.results.lag = lag
                self.results.age = age

    # initialize or add ttcf to results
    def _add_ttcf(self, ttcf, calc_num):
        if self.results.ttcf is None:
            self.results.ttcf = np.empty((self.mask_num, ttcf.shape[0], ttcf.shape[1])) #TODO this can change datatype of ttcf to float64
        self.results.ttcf[calc_num] = ttcf

    @staticmethod
    def correlate(xpcs_data, mask, calculate_g2_err=False, calculate_ttcf=False):
        
        """
        Reference implementation of the dense correlator.

        n_tau - number of frames
        n_x - size of x axis of detector frame
        n_y - size of y axis of detector frame
        n_pix - number of pixels in the detector frame after masking

        Parameters
        ----------
        xpcs_data : np.ndarray
            The input data of shape (n_tau, n_x, n_y).
        mask : np.ndarray
            The mask of the input data of shape (n_x, n_y).
        calculate_g2_err : bool, optional
            If True, the error of g2 is calculated. The default is False.
        calculate_ttcf : bool, optional
            If True, the ttcf matrix is calculated. The default is False.
        Returns
        -------
        g2 : np.ndarray
            The g2 correlation function of shape (n_tau-1,).
        g2_err : np.ndarray
            The error of g2 correlation function of shape (n_tau-1,).
        ttcf : np.ndarray
            The ttcf matrix of shape (n_tau, n_tau).
        """
        
        g2_err = None
        ttcf= None
        ind = np.where(mask)  # selects indices where mask is True
        xpcs_data = np.array(xpcs_data[:, ind[0], ind[1]], np.float32)  # (n_tau, n_pix)
        meanmatr = np.mean(xpcs_data, axis=1)  # xpcs_data.sum(axis=-1).sum(axis=-1)/n_pix
        ltimes, lenmatr = np.shape(xpcs_data)  # n_tau, n_pix
        meanmatr.shape = 1, ltimes

        # Calculation of the numerator and denominator of ttcf matrix
        num = np.dot(xpcs_data, xpcs_data.T) / lenmatr
        denom = np.dot(meanmatr.T, meanmatr)
        
        #Calculation of the ttcf matrix
        if calculate_ttcf:
            ttcf = num / denom

        #Calculation of g2 correlation function    
        g2 = np.zeros(ltimes-1)

        if calculate_g2_err:
            g2_err = np.zeros_like(g2)

        for i in range(1,ltimes):  # was ltimes-1, so res[-1] was always 1 !
            dia_n = np.diag(num, k=i) 
            dia_d = np.diag(denom, k=i)
            g2[i-1] = np.sum(dia_n) / np.sum(dia_d)
            if g2_err is not None:
                g2_err[i-1] = np.std(dia_n / dia_d) / np.sqrt(len(dia_d)) 
        
        return g2, g2_err, ttcf

   

    @staticmethod
    def bin_ttcf(ttcf,t1_t2_binning):
        """
        Bin the ttcf matrix along t1 and t2 axes using linear binning.

        Parameters
        ----------
        ttcf : np.ndarray
            The ttcf matrix in t1,t2 coordinates.
        t1_t2_binning : int
            The number of linear bins for each axis (t1 and t2).

        Returns
        -------
        result : np.ndarray
            The binned ttcf matrix.
        t1 : np.ndarray
            The bin centers for the t1 axis.
        t2 : np.ndarray
            The bin centers for the t2 axis.
        """
        
        ttcf_shape=ttcf.shape
        x_ttcf, y_ttcf = np.indices(ttcf.shape, dtype=np.int32).reshape(2, -1)

        # Filter for upper triangle including diagonal (t1 >= t2)
        mask = x_ttcf >= y_ttcf
        x_ttcf_upper = x_ttcf[mask]
        y_ttcf_upper = y_ttcf[mask]
        ttcf_upper = ttcf.ravel()[mask]

        del ttcf # Memory savings 
        del x_ttcf
        del y_ttcf

        bin_edges_t1, _ = lin_bin(np.arange(ttcf_shape[0]), t1_t2_binning)
        bin_edges_t2 = bin_edges_t1
        intensities, _, _ = np.histogram2d(
            x_ttcf_upper, y_ttcf_upper, bins=[bin_edges_t1, bin_edges_t2], weights=ttcf_upper)
        counts, _, _ = np.histogram2d(
            x_ttcf_upper, y_ttcf_upper, bins=[bin_edges_t1, bin_edges_t2])

        # Normalize the binned intensities by the counts
        # Avoid division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            result = np.divide(intensities, counts)

        # Calculate bin centers
        t1 = bin_centers(bin_edges_t1)
        t2 = t1

        return result, t1, t2

    @staticmethod
    def bin_ttcf_age_lag(ttcf, age_binning, lag_binning):
        """
        Bins the ttcf matrix in t1,t2 coordinates into lag and age coordinates.
        The lag is defined as t2-t1 and the age is defined as (t1+t2)/2.

        Parameters
        ----------
        ttcf : np.ndarray
            The ttcf matrix in t1,t2 coordinates.
        age_binning : int
            The linear age binning factor.
        lag_binning : tuple(int, int)
            The lag binning factor (N,n_points), N is a decade, \
        
        Returns
        -------
        ttcf_binned_norm : np.ndarray
            The binned ttcf matrix in age, lag coordinates.
        lag : np.ndarray
            The lag coordinates.
        age : np.ndarray
            The age coordinates.
        """

        # Two arrays with t2 and t1 indices of ttcf
        t2, t1 = np.indices(ttcf.shape)

        # Compute lag and age
        lag = (t2 - t1)
        age = ((t1 + t2) / 2)
        
        # Compute bin edges for lag and age
        bins_lag, _ = lin_log_bin(lag[:, 0], lag_binning[0], lag_binning[1])
        bins_age, _ = lin_bin(np.diag(age), age_binning)

        # Select only indices corresponding to non-negative lag values
        ind = lag >= 0

        lag_selected = lag[ind]
        age_selected = age[ind]
        ttcf_selected = ttcf[ind]

        # Bin the data    
        bins = (bins_age, bins_lag)
        intensities, _, _ = np.histogram2d(age_selected, lag_selected, bins=bins, weights=ttcf_selected)
        counts, _, _ = np.histogram2d(age_selected, lag_selected, bins=bins)

        # Normalize the binned intensities by the counts
        # Avoid division by zero
        with np.errstate(divide='ignore', invalid='ignore'):
            ttcf_binned = np.divide(intensities, counts)
        
        # Calculate bin centers
        age = bin_centers(bins_age)
        lag = bin_centers_mixed(bins_lag, lag_binning[0])
        
        return ttcf_binned, lag, age

