import copy, logging, os ,sys

from typing import Optional, Union
from time import time

import numpy as np
import h5py, hdf5plugin

from dask.distributed import Client, as_completed

from xpcscorr.core.base import Results
from xpcscorr.correlators.dense.base import DenseCorrelator, Chunks
from xpcscorr.core.utils import (mask_to_3d_bool_stack, 
                                 lin_bin , 
                                 lin_log_bin, 
                                 bin_centers,
                                 bin_centers_mixed,
                                 bins_calc_tccf_t1_t2_chunk,
                                 bins_calc_tccf_age_lag_chunk,                                     
                                 )



python_executable = sys.executable

from xpcscorr import logger


class ChunkWorker:
    """
    Worker class to calculate a chunk of the correlation matrix.
    """

    def __init__(self,
                roimask: np.ndarray,
                chunk_metadata: dict,
                chunks_dtype: np.dtype,
                frames_shape: tuple,
                t1_t2_binning: Optional[int]=None,
                age_binning: Optional[int]=None,
                lag_binning: Optional[Union[int, tuple]]=None,
                ):

        self.roimask = roimask
        self.chunk_metadata = chunk_metadata
        self.chunks_dtype = chunks_dtype
        self.frames_shape = frames_shape
        self.t1_t2_binning = t1_t2_binning
        self.age_binning = age_binning
        self.lag_binning = lag_binning

    # This need to be "pure" function for Dask to be able to serialize it !!!
    def __call__(self, frames, roimask_n, chunk_ID):
        """
        Here we process one chunk of data, for given roimask_num and chunk_ID

        Parameters
        ----------
        frames: tuple (h5py file name, dataset name) or tuple of two np.ndarray
            The frames should be :
                - tuple (h5_path, dset_name)
                - or tuple (np.ndarray, np.ndarray) with two data chunks (already masked and flattened) 
                with selected rows and columns corresponding to each chunk.
        roimask_n: int
            The index of the ROI mask to use.
        frames: tuple
            The frames data like two np.ndarray already masked (data_ch1, data_ch2) 
            or (h5_path, dset_name)
        """
       
        # --- Set the number of threads for BLAS libraries if environment variable is set ---
        import threadpoolctl 
        
        #Here we set the ny=umber of threads for BLAS libraries, when using local Dask cluster
        if 'XPCS_BLAS_THREADS' in os.environ:
            threadpoolctl.threadpool_limits(int(os.environ.get("XPCS_BLAS_THREADS", 1)))
        
        logger.info("Numpy mutlithreading BLAS configuration:")
        logger.info(threadpoolctl.threadpool_info())
        
        # --- Process the chunk ---
        logger.info("Processing chunk ID %d for mask %d", chunk_ID, roimask_n)
        # _load_chunk_data
        data_ch1, data_ch2 = self._load_chunk_data(frames, roimask_n, chunk_ID)
        logger.info("Loaded data for chunks with data shapes: %s, %s", data_ch1.shape, data_ch2.shape)
        
        # _calculate_chunk_nom_denom
        logger.info("Calculating nom and denom for chunk ID %d, mask %d", chunk_ID, roimask_n)
        nom, denom = self._calculate_chunk_nom_denom(data_ch1,data_ch2)
        logger.info("Calculated nom and denom with shapes: %s, %s", nom.shape, denom.shape)
        
        # _calculate_chunk_ttcf
        logger.info("Calculating ttcf for chunk ID %d, mask %d", chunk_ID, roimask_n)
        ttcf=nom/denom # normal chunk
        if len(set(self.chunk_metadata[chunk_ID]['coordinates'])) == 1:  # if diagonal chunk
            with np.errstate(divide='ignore', invalid='ignore'):
                ttcf= np.triu(ttcf)  # take only upper part, including main diagonal
        logger.info("Calculated ttcf with shape (only upper triangle): %s", ttcf.shape)

        # _calculate_g2_diagonals_size_mean_std_of_chunk
        logger.info("Calculating g2 diagonals statistics for chunk ID %d, mask %d", chunk_ID, roimask_n)
        res_chunk = self._calculate_g2_diagonals_size_mean_std_of_chunk(ttcf, nom, denom, chunk_ID)
        logger.info("Calculated g2 diagonals statistics for chunk ID %d, mask %d", chunk_ID, roimask_n)

        # _bin_tccf_t1_t2_chunk
        logger.info("Binning ttcf for chunk ID %d, mask %d", chunk_ID, roimask_n)
        if self.t1_t2_binning is not None:
            
            local_bin_t1, local_bin_t2, bin_t1_start, bin_t1_end, bin_t2_start, bin_t2_end = \
            bins_calc_tccf_t1_t2_chunk(t1_t2_binning=self.t1_t2_binning,
                                                            global_ttcf_size=self.frames_shape[0],
                                                            rows_start=self.chunk_metadata[chunk_ID]['row_start'],
                                                            rows_end=self.chunk_metadata[chunk_ID]['row_end'],
                                                            cols_start=self.chunk_metadata[chunk_ID]['col_start'],
                                                            cols_end=self.chunk_metadata[chunk_ID]['col_end'],
                                                            )
            intensities, counts = self._bin_tccf_t1_t2_chunk(ttcf, local_bin_t1, local_bin_t2, chunk_ID)
            ttcf = (intensities, counts)
            logger.info("Binned lineary, t1,t2 ttcf for chunk ID %d, mask %d", chunk_ID, roimask_n)
        
        elif self.age_binning is not None and self.lag_binning is not None:
            local_bin_lag, local_bin_age, bin_lag_start, bin_lag_end, bin_age_start, bin_age_end = \
            bins_calc_tccf_age_lag_chunk(age_binning=self.age_binning,
                                            lag_binning=self.lag_binning,
                                            global_ttcf_size=self.frames_shape[0],
                                            rows_start=self.chunk_metadata[chunk_ID]['row_start'],
                                            rows_end=self.chunk_metadata[chunk_ID]['row_end'],
                                            cols_start=self.chunk_metadata[chunk_ID]['col_start'],
                                            cols_end=self.chunk_metadata[chunk_ID]['col_end'],
                                            )
            intensities, counts = self._bin_ttcf_age_lag_chunk(ttcf, local_bin_age, local_bin_lag, chunk_ID)
            ttcf = (intensities, counts)
            logger.info("Binned lin/lin+log, age, lag ttcf for chunk ID %d, mask %d", chunk_ID, roimask_n)

        return res_chunk, ttcf

    def _load_chunk_data(self, frames, roimask_n, chunk_ID):
        """
        Load the chunk data from the hdf5 dataset or tuple of two np.ndarray.
        The data from ndarrays should be already masked.
        """

        row_start = self.chunk_metadata[chunk_ID]['row_start']
        row_end = self.chunk_metadata[chunk_ID]['row_end']
        col_start = self.chunk_metadata[chunk_ID]['col_start']
        col_end = self.chunk_metadata[chunk_ID]['col_end']

        # TODO: add support if the chunk coordinates equal (0,0) etc. -diagonal chunk 
        # In this case we can load only one part of frames
        # and use it for both parts of correlation calculation
        if isinstance(frames, tuple) and isinstance(frames[0], str):
            with h5py.File(frames[0], 'r') as f:
                dataset = f[frames[1]]

                ind_y, ind_x = np.where(self.roimask[roimask_n])  # selects indices where mask is True

                # Load the chunk data from the hdf5 dataset
                # This is done by iterating over the frames in the chunk
                # and selecting only the pixels in the mask
                # This is done to avoid loading the entire hdf5 dataset into memory
                data_ch1 = np.empty((row_end - row_start, ind_x.size), dtype=self.chunks_dtype)

                for i, row_data in enumerate(dataset[row_start:row_end]):  # type: ignore
                    data_ch1[i, :] = row_data[ind_y, ind_x]  # type: ignore
                
                data_ch2 = np.empty((col_end - col_start, ind_x.size), dtype=self.chunks_dtype)

                for i, col_data in enumerate(dataset[col_start:col_end]):  # type: ignore
                    data_ch2[i, :] = col_data[ind_y, ind_x]  # type: ignore

        elif isinstance(frames, tuple) and isinstance(frames[0], np.ndarray):
            #The frames is a numpy array. Already the loaded data should be masked 3D array
            data_ch1 = frames[0].astype(self.chunks_dtype)  # type: ignore
            data_ch2 = frames[1].astype(self.chunks_dtype)  # type: ignore
        
        else:
            raise ValueError(
                "frames should be either tuple of two str (h5_path, dset_name) or (np.ndarray, np.ndarray)"
            )

        # Load the chunk data from the main data array
        return data_ch1.astype(self.chunks_dtype), data_ch2.astype(self.chunks_dtype)
    
    @staticmethod
    def _calculate_chunk_nom_denom(data_ch1, data_ch2):
        """
        Calculate the nominator and denominator for the chunk.
        """

        nom = np.matmul(data_ch1, data_ch2.T) / data_ch1.shape[1]
        mean_matrix_ch1 = np.mean(data_ch1, axis=1)
        mean_matrix_ch2 = np.mean(data_ch2, axis=1)
       
        denom= np.outer(mean_matrix_ch1, mean_matrix_ch2)

        return nom, denom
    
    def _calculate_g2_diagonals_size_mean_std_of_chunk(self, ttcf, nom, denom , chunkID):
        """
        Calculate statistics for each diagonal of the chunk's ttcf matrix:
        size, mean, std, sum_nom, sum_denom
        """
        
        if len(set(self.chunk_metadata[chunkID]['coordinates'])) == 1:
            diagonals_offset = np.arange(0, ttcf.shape[0])
        else:
            diagonals_offset = np.arange(-ttcf.shape[0]+1, ttcf.shape[1])  
        
        # TODO be carreful with this, dtype should be defined?, now its float64
        res_diag = [np.empty(len(diagonals_offset)) for _ in range(5)] # size, mean, std, sum_nom, sum_denom
        
        for i, diag_n in enumerate(diagonals_offset):

            diag_size= np.diagonal(ttcf, offset=diag_n).size
            diag_mean= np.mean(np.diagonal(ttcf, offset=diag_n))
            diag_std_ttcf= np.std(np.diagonal(ttcf, offset=diag_n))
            diag_sum_nom= np.sum(np.diagonal(nom, offset=diag_n))
            diag_sum_denom= np.sum(np.diagonal(denom, offset=diag_n))
            
            res_diag[0][i] = diag_size #TODO Check data type here is possible that number is upcasted to float64
            res_diag[1][i] = diag_mean
            res_diag[2][i] = diag_std_ttcf
            res_diag[3][i] = diag_sum_nom
            res_diag[4][i] = diag_sum_denom
            
        return res_diag

    def _bin_tccf_t1_t2_chunk(self, ttcf, local_bin_t1, local_bin_t2, chunk_ID):
        """
        Bin the ttcf for t1,t2 format for the chunk.
        Uses np.bincount for a 'faster' binning.
        """


        # t1_offset and t2_offset are used to map the local indices to global time indices
        t1_offset = self.chunk_metadata[chunk_ID]['col_start'].astype(np.int32)
        t2_offset = self.chunk_metadata[chunk_ID]['row_start'].astype(np.int32)

        # Pre-compute bin mappings for all possible time values in this chunk
        t1_range = np.arange(t1_offset, t1_offset + ttcf.shape[1], dtype=np.int32)
        t2_range = np.arange(t2_offset, t2_offset + ttcf.shape[0], dtype=np.int32)

        # Pre-compute bin indices for all possible time values
        # -1 because searchsorted returns the index where the element should be inserted
        # to maintain order, so we need to subtract 1 to get the correct bin index
        # Clip to ensure indices are within valid range
        bin_map_t1 = np.clip(np.searchsorted(local_bin_t1, t1_range, side='right') - 1, 
                            0, len(local_bin_t1) - 2, dtype=np.int32)
        bin_map_t2 = np.clip(np.searchsorted(local_bin_t2, t2_range, side='right') - 1, 
                            0, len(local_bin_t2) - 2, dtype=np.int32)
        
        # Check if this is a diagonal chunk (triangular matrix)
        is_diagonal_chunk = len(set(self.chunk_metadata[chunk_ID]['coordinates'])) == 1
        
        if is_diagonal_chunk:
            # For diagonal chunks, only consider upper triangular elements
            t2, t1 = np.indices(ttcf.shape, dtype=np.int32)
            t2 += t2_offset
            t1 += t1_offset
            mask = t1 >= t2
            
            values = ttcf[mask]
            t1_coords = t1[mask]
            t2_coords = t2[mask]
            
            # Use pre-computed mappings for fast lookup
            indices_t1 = bin_map_t1[t1_coords - t1_offset]
            indices_t2 = bin_map_t2[t2_coords - t2_offset]
        else:
            # For non-diagonal chunks, we can use a more efficient approach
            values = ttcf.ravel()
            
            # Create bin indices directly without generating coordinates
            row_indices = np.repeat(np.arange(ttcf.shape[0],dtype=np.int32), ttcf.shape[1])
            col_indices = np.tile(np.arange(ttcf.shape[1],dtype=np.int32), ttcf.shape[0])
            
            # Use pre-computed mappings
            indices_t1 = bin_map_t1[col_indices]
            indices_t2 = bin_map_t2[row_indices]
        
        # Calculate bin indices
        bin_indices = indices_t1 * (len(local_bin_t2) - 1) + indices_t2
        
        # Calculate intensities and counts
        minlength = (len(local_bin_t1) - 1) * (len(local_bin_t2) - 1)
        shape = (len(local_bin_t1) - 1, len(local_bin_t2) - 1)
        
        intensities = np.bincount(bin_indices, weights=values, minlength=minlength).reshape(shape)
        counts = np.bincount(bin_indices, minlength=minlength).reshape(shape)
        
        return intensities, counts

    def _bin_ttcf_age_lag_chunk(self, ttcf, local_bin_age, local_bin_lag, chunk_ID):
        """
        Bin the ttcf for age,lag format for the chunk.
        Uses np.bincount for a 'faster' binning.
        """
        
        local_bin_lag=local_bin_lag.astype(np.float64)
        local_bin_age=local_bin_age.astype(np.float64)
        # Get chunk offsets
        t2_offset = self.chunk_metadata[chunk_ID]['row_start'].astype(np.int32)
        t1_offset = self.chunk_metadata[chunk_ID]['col_start'].astype(np.int32)

        # Check if this is a diagonal chunk
        is_diagonal_chunk = len(set(self.chunk_metadata[chunk_ID]['coordinates'])) == 1
        
        if is_diagonal_chunk:
            # For diagonal chunks, generate full coordinate arrays
            t2, t1 = np.indices(ttcf.shape, np.dtype(np.int32))
            t2 += t2_offset
            t1 += t1_offset
            
            # Calculate age and lag
            lag = t2 - t1
            age = np.add(t1,t2, dtype=np.float32) / np.float32(2)
            # Filter for valid points (where lag <= 0)
            mask = lag <= 0
            lag_coords = lag[mask] * -1  # Convert to positive values
            age_coords = age[mask]
            values = ttcf[mask]
        else:
            # For non-diagonal chunks, create coordinate arrays more efficiently
            rows, cols = ttcf.shape
            
            # Create coordinate arrays for this chunk
            row_indices = np.repeat(np.arange(rows, dtype=np.int32), cols)
            col_indices = np.tile(np.arange(cols,dtype=np.int32), rows)
            
            # Convert to global coordinates
            t2_coords = row_indices + t2_offset
            t1_coords = col_indices + t1_offset
            
            # Calculate age and lag for all points
            lag = t2_coords - t1_coords
            age = np.add(t1_coords, t2_coords, dtype=np.float32) / np.float32(2)
            
            # Filter for valid points (where lag <= 0)
            mask = lag <= 0
            lag_coords = lag[mask] * -1  # Convert to positive values
            age_coords = age[mask]
            values = ttcf.ravel()[mask]
        
        # Since age = (t1 + t2)/2 where t1,t2 are integers, age can only be integers or half-integers
        # Calculate min/max, ensure they capture the full integer/half-integer range
        min_age = np.floor(np.min(age_coords) * 2) / 2
        max_age = np.ceil(np.max(age_coords) * 2) / 2
        
        # Create array of all possible age values (integers and half-integers)
        # Multiply by 2, use arange with integers, then divide by 2
        possible_ages = np.arange((min_age * 2), (max_age * 2) + 1 ,dtype=np.float32) / 2
        
        # Pre-compute bin indices for these exact values
        bin_map_age = np.clip(np.searchsorted(local_bin_age, possible_ages, side='right') - 1, 
                            0, len(local_bin_age) - 2,dtype=np.int32)
        
        # Convert age to an index into the pre-computed bins
        # Scale to integers by multiplying by 2, then offset to start from 0
        age_indices = bin_map_age[(age_coords * 2 - min_age * 2).astype(np.int32)]
        
        # For lag values, use direct binning
        lag_indices = np.clip(np.searchsorted(local_bin_lag, lag_coords, side='right') - 1, 
                            0, len(local_bin_lag) - 2, dtype=np.int32)
        
        # Calculate bin indices
        bin_indices = age_indices * (len(local_bin_lag) - 1) + lag_indices
        
        # Calculate intensities and counts using bincount
        minlength = (len(local_bin_age) - 1) * (len(local_bin_lag) - 1)
        shape = (len(local_bin_age) - 1, len(local_bin_lag) - 1)
        
        intensities = np.bincount(bin_indices, weights=values, minlength=minlength).reshape(shape)
        counts = np.bincount(bin_indices, minlength=minlength).reshape(shape)
        
        return intensities, counts

class CorrelatorDenseChunked(DenseCorrelator):
    """
    Implementation of the dense correlator calculated in chunks.
    This is useful when the frames data is too large to fit into memory.
    The frames data can be provided as a tuple of two numpy arrays or as an hdf5 dataset.
    The chunks are selected to cover the triangle of the correlation matrix which is symmetric.

    Parameters
    ----------
    extra_options: dict, optional
        Extra options for the correlator. 
        
        Example for the local dask cluster with 4 chunks::
            
            extra_options = {
                'chunks_N': 4,
                'chunks_dtype': np.float32,
                'dask_cluster_type': 'local',
                'dask_local_n_workers': 2,
                'dask_local_blas_threads': 2,
            }
        
        The following options are available:
        
        **General options**:
        
        * chunks_N: int, optional
            Number of chunks to divide the data into. Default is 1.
        * chunks_dtype: np.dtype, optional
            Data type for the chunks. Default is np.float32.
        * dask_cluster_type: str, optional
            Type of dask cluster to use. Options are 'local', 'slurm' or None.
            Default is None, which means no dask is used and the computation is done in a single process.
        
        **Local dask cluster options**:
        
        * dask_local_n_workers: int, optional
            Number of workers for the local dask cluster. Default is 1.
        * dask_local_blas_threads: int, optional
            Number of threads for BLAS libraries for each local dask worker. Default is 1.
            Basically this is number of CPU cores per worker.

        **SLURM dask cluster options**:
        
        * dask_cluster_queue: str, optional
            Partition name for the slurm dask cluster. Default is 'low' for ESRF slurm cluster.
        * dask_cluster_walltime: str, optional
            Walltime for the slurm dask cluster. Default is '02:00:00'.
        * dask_slurm_workers: int, optional
            Number of workers for the slurm dask cluster. Default is 10.
        * dask_slurm_processes_per_worker: int, optional
            Number of processes per worker for the slurm dask cluster. Default is 1.
        * dask_slurm_cores_per_worker: int, optional
            Number of CPU cores per worker for the slurm dask cluster. Default is 8.
        * dask_slurm_memory_per_worker: str, optional
            Memory per worker for the slurm dask cluster. Default is '50GB'.
    """

    def __init__(self, frames, roimask, **kwargs):
        super().__init__(frames, roimask, **kwargs)

        self.ttcf_format = kwargs.get('ttcf_format', None)
        self.t1_t2_binning = kwargs.get('t1_t2_binning', None)
        self.age_binning = kwargs.get('age_binning', None)
        self.lag_binning = kwargs.get('lag_binning', None)
        self.extra_options = kwargs.get('extra_options', None)

        # --- Load extra options with defaults  ---
        defaults = dict(
            chunks_N = 1,
            chunks_dtype = np.float32,
            dask_cluster_type = None,  # 'local' or 'slurm' or None- if None no dask is used
            dask_local_n_workers = 1,
            dask_local_blas_threads = 1,
            dask_cluster_queue = 'low',
            dask_cluster_walltime = '02:00:00',
            dask_slurm_workers = 10,
            dask_slurm_processes_per_worker = 1,
            dask_slurm_cores_per_worker = 8,
            dask_slurm_memory_per_worker = '50GB',
        )
        opts = defaults.copy()
        if isinstance(self.extra_options, dict):
            opts.update(self.extra_options)

        # assign attributes from merged options
        self.chunks_N = int(opts['chunks_N'])
        
        self.chunks_dtype = opts['chunks_dtype']
        self.dask_cluster_type = opts['dask_cluster_type']

        self.dask_local_n_workers = int(opts['dask_local_n_workers'])
        self.dask_local_blas_threads = int(opts['dask_local_blas_threads'])

        self.dask_cluster_queue = opts['dask_cluster_queue']
        self.dask_cluster_walltime = opts['dask_cluster_walltime']
        self.dask_slurm_workers = int(opts['dask_slurm_workers'])
        self.dask_slurm_processes_per_worker = int(opts['dask_slurm_processes_per_worker'])
        self.dask_slurm_cores_per_worker = int(opts['dask_slurm_cores_per_worker'])
        self.dask_slurm_memory_per_worker = opts['dask_slurm_memory_per_worker']
  
        # --- Frames data processing ---
        if isinstance(frames, np.ndarray):
            self._frames_h5=None
            self.frames=frames
            self.frames_shape=self.frames.shape
        elif isinstance(frames, h5py.Dataset):
            self._frames_h5=(frames.file.filename, 
                             frames.name)
            self.frames_shape=frames.shape
            frames.file.close()
        
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
        
        start=time()
        logger.info(f"Starting computation... {time()-start:.2f} s")
        logger.info(f"Data shape: {self.frames_shape}, mask shape: {self.roimask.shape}, chunks_N: {self.chunks_N}")
        
        #--- setting all variables and conditions ---
        calculate_ttcf = bool(self.ttcf_format)
        calculate_g2_err = True #TODO as an option ?
        
        # --- calculate ttcf t1,t2 or age,lag axes from bins ---
        self._calculate_ttcf_axes()

        # --- initializing chunks ---
        self.chunks= Chunks(self.frames_shape[0],self.chunks_N) 

        #--- calculating chunks ID to process ---
        chunks_ID_to_process=self.chunks.snake_chunks #if we doing parallel we dont care about order ? or maybe we do for better memory managment at some point?

        # --- initialize per-mask results ---
        for i_chk_ID in chunks_ID_to_process:
            self.chunks.chunks[i_chk_ID]['results_by_mask']={}
            for i_mask_num in range(self.mask_num):
                self.chunks.chunks[i_chk_ID]['results_by_mask'][i_mask_num]= {
                    'diagonal_stats':None,
                    'ttcf': None,
                }

        # ---  initializing global result arrays for g2, g2_err and ttcf ---
        self.results.g2 = np.zeros((self.mask_num, self.frames_shape[0]-1), dtype=np.float64) 
        self.results.g2_err = np.zeros((self.mask_num, self.frames_shape[0]-1), dtype=np.float64)
        
        if self.ttcf_format == 't1,t2':
            if self.t1_t2_binning is None:
                self.results.ttcf = np.zeros((self.mask_num, self.frames_shape[0], self.frames_shape[0]), dtype=self.chunks_dtype) # TODO: accumulation also in float64 ?
            elif self.t1_t2_binning is not None:
                self.results.ttcf = np.zeros((self.mask_num, self.t1_t2_binning, self.t1_t2_binning), dtype=self.chunks_dtype)
        elif self.ttcf_format == 'age,lag':
            self.results.ttcf  = np.zeros((self.mask_num, self.age_binning, 10**self.lag_binning[0]-1+self.lag_binning[1]), dtype=self.chunks_dtype)

        # Here goes  methods which allow to proces chunks in parallel on a cluster (using Dask)
        # or  locally in sequence. Basically the parallel processing is done by submitting
        #  all jobs at once (all masks chunks) to Dask cluster and then collecting the results. 
        # The local processing is done by simply calling the worker function.
        worker=ChunkWorker(self.roimask, 
                           copy.deepcopy(self.chunks.chunks), 
                           self.chunks_dtype,
                           self.frames_shape, 
                           self.t1_t2_binning,
                           self.age_binning,
                           self.lag_binning)
        
        # --- Dask cluster setup ---
        if self.dask_cluster_type is not None:
            self._dask_cluster_setup()
            logger.info(f"Dask SLURM cluster started and scaled {time()-start:.2f} s")
        else:
            logger.info(f"Processing locally without Dask {time()-start:.2f} s")
        
        all_futures = {} #Format: {(mask_k, chunk_i): future}
        future_to_key = {} 

        # --- Main loop over masks and chunks ---
        for k in range(self.mask_num):
            logger.info(f"Start processing mask {k}/{self.mask_num-1} {time()-start:.2f} s")
            
            #Processing chunks in parallel
            for i in chunks_ID_to_process:
    
                logger.info(f"Processing mask {k}/{self.mask_num-1}, chunk ID {i}, {self.chunks.chunks[i]['coordinates']} {time()-start:.2f} s")

                # If frames are hdf5 dataset
                if self._frames_h5 is not None:

                    data_for_worker=copy.deepcopy(self._frames_h5)

                    # Processing locally without Dask
                    if self.dask_cluster_type is None: 
                        self.chunks.chunks[i]['results_by_mask'][k]['diagonal_stats'], self.chunks.chunks[i]['results_by_mask'][k]['ttcf'] = worker(data_for_worker, k, i)
                
                # If frames are numpy array
                elif isinstance(self.frames, np.ndarray):

                    ind_y, ind_x = np.where(self.roimask[k])

                    chunk_1_data = self.frames[self.chunks.chunks[i]['row_start']:self.chunks.chunks[i]['row_end'], ind_y, ind_x]
                    chunk_2_data = self.frames[self.chunks.chunks[i]['col_start']:self.chunks.chunks[i]['col_end'], ind_y, ind_x]
                    
                    data_for_worker = (chunk_1_data, chunk_2_data)

                    #Processing locally without Dask
                    if self.dask_cluster_type is None: 
                        self.chunks.chunks[i]['results_by_mask'][k]['diagonal_stats'], self.chunks.chunks[i]['results_by_mask'][k]['ttcf'] = worker(data_for_worker, k, i)

                # Submitting jobs to Dask cluster
                if self.dask_cluster_type is not None:
                    future = self._dask_client.submit(worker, data_for_worker, k, i)
                    all_futures[(k, i)] = future
                    future_to_key[future] = (k, i)

        # --- Collecting results from Dask cluster ---
        if self.dask_cluster_type is not None:
            logger.info(f"Collecting results from Dask {time()-start:.2f} s")
            
            for future_finished, result in as_completed(all_futures.values(), with_results=True):
                mask_k, chunk_i = future_to_key[future_finished]
            
                diagonal_stats, ttcf_results = result
                self.chunks.chunks[chunk_i]['results_by_mask'][mask_k]['diagonal_stats'] = diagonal_stats
                self.chunks.chunks[chunk_i]['results_by_mask'][mask_k]['ttcf'] = ttcf_results

                # remove forward mapping to free references
                all_futures.pop((mask_k, chunk_i), None)

                logger.info(f"Collected result for mask {mask_k}/{self.mask_num-1}, chunk ID {chunk_i}")

        # --- Accumulating results from chunks to global results ---
        for n  in range(self.mask_num):
            logger.info(f"Accumulating results from chunks ... {time()-start:.2f} s")
            g2, g2_err = self._calculate_global_g2_and_g2_err(n)
            logger.info(f"Finished calculating g2 and g2_err {time()-start:.2f} s")
            self.results.g2[n]= g2[1:]  # removing g2[0] 
            self.results.g2_err[n]= g2_err[1:]  # removing g2_err[0]
                
            if self.ttcf_format is not None:
                self._calculate_global_ttcf(n) #type: ignore
                logger.info(f"Finished accumulating ttcf {time()-start:.2f} s")
            logger.info(f"Finished mask {n}/{self.mask_num-1} in {time()-start:.2f} s")

        if self.dask_cluster_type is not None:
            self._dask_client.close()
            self._dask_cluster.close()
            logger.info(f"Dask cluster closed {time()-start:.2f} s")
        
        logger.info(f"Computation finished in {time()-start:.2f} s")

   
    # --- Methods for calculating global results from chunks --- #
    def _calculate_global_g2_and_g2_err(self, mask_k):
        """
        Calculate global g2 and g2_err from chunk diagonal statistics.
        """

        # This corresponds to the number of main plus upper diagonals of main ttcf
        diagonal_contributions = [[] for _ in range(self.frames_shape[0])]  # One list per diagonal index
        
        # Accumulate results from all chunks
        for chunkID in self.chunks.snake_chunks:
            
            chunk_results = self.chunks.chunks[chunkID]['results_by_mask'][mask_k]
            diagonal_stats = chunk_results['diagonal_stats']

            offset_min=self.chunks.chunks[chunkID]['diag_offset_min']
            offset_max=self.chunks.chunks[chunkID]['diag_offset_max']
                        
            if len(set(self.chunks.chunks[chunkID]['coordinates'])) == 1:

                ind=np.arange(0, offset_max+1)
                offset=0
            else:

                ind=np.arange(offset_min, offset_max+1)
                offset=offset_min

            for i in ind:
                diagonal_contributions[i].append((
                    diagonal_stats[0][i-offset],
                    diagonal_stats[1][i-offset],
                    diagonal_stats[2][i-offset],
                    diagonal_stats[3][i-offset],
                    diagonal_stats[4][i-offset],
                ))
        
        g2=np.zeros(len(diagonal_contributions))
        g2_err=np.zeros(len(diagonal_contributions))

        for i, contrib in enumerate(diagonal_contributions):
            # Calculate g2 using sum of numerators and denominators
            sum_nom = np.sum([k[3] for k in contrib])  # Collect sum_nom values
            sum_denom = np.sum([k[4] for k in contrib])  # Collect sum_denom values
            g2[i] = sum_nom / sum_denom  # Proper g2 calculation
            
            # Calculate g2_err using combined standard deviation and normalize by sqrt of total elements
            contrib_size_mean_std = [k[0:3] for k in contrib]
            g2_err[i], total_elements = self._calculate_std_from_processed_chunks_diagonals(contrib_size_mean_std) 
            g2_err[i] /= np.sqrt(total_elements)  # Standard error reduction
        
        return g2, g2_err

    def _calculate_global_ttcf(self, mask_num):
        """
        Calculate global ttcf from chunk ttcf results.
        """
        
        global_ttcf=self.results.ttcf[mask_num]

        if self.ttcf_format == 't1,t2' and self.t1_t2_binning is not None or self.ttcf_format == 'age,lag':
            # Initialize global intensities and counts arrays
            global_intensities = np.zeros_like(global_ttcf)
            global_counts = np.zeros_like(global_ttcf)
      
        for chunkID in self.chunks.snake_chunks:
           
            if self.ttcf_format == 't1,t2':
                if self.t1_t2_binning is None:
                    global_ttcf[self.chunks.chunks[chunkID]['row_start']:self.chunks.chunks[chunkID]['row_end'],
                                self.chunks.chunks[chunkID]['col_start']:self.chunks.chunks[chunkID]['col_end']] += self.chunks.chunks[chunkID]['results_by_mask'][mask_num]['ttcf']

                elif self.t1_t2_binning is not None:
                
                    local_bin_t1, local_bin_t2, bin_t1_start, bin_t1_end, bin_t2_start, bin_t2_end = \
                    bins_calc_tccf_t1_t2_chunk(self.t1_t2_binning, self.frames_shape[0], 
                                            self.chunks.chunks[chunkID]['row_start'], 
                                            self.chunks.chunks[chunkID]['row_end'], 
                                            self.chunks.chunks[chunkID]['col_start'], 
                                            self.chunks.chunks[chunkID]['col_end'])

                    intensities, counts = self.chunks.chunks[chunkID]['results_by_mask'][mask_num]['ttcf']

                    global_intensities[bin_t1_start:bin_t1_end, bin_t2_start:bin_t2_end] += intensities
                    global_counts[bin_t1_start:bin_t1_end, bin_t2_start:bin_t2_end] += counts
        
            if self.ttcf_format == 'age,lag':

                local_bin_lag, local_bin_age, bin_lag_start, bin_lag_end, bin_age_start, bin_age_end = \
                bins_calc_tccf_age_lag_chunk(self.age_binning, self.lag_binning, self.frames_shape[0], 
                                        self.chunks.chunks[chunkID]['row_start'], 
                                        self.chunks.chunks[chunkID]['row_end'], 
                                        self.chunks.chunks[chunkID]['col_start'], 
                                        self.chunks.chunks[chunkID]['col_end'])
                intensities, counts = self.chunks.chunks[chunkID]['results_by_mask'][mask_num]['ttcf']

                global_intensities[bin_age_start:bin_age_end, bin_lag_start:bin_lag_end] += intensities
                global_counts[bin_age_start:bin_age_end, bin_lag_start:bin_lag_end] += counts

        if self.t1_t2_binning is not None or self.ttcf_format == 'age,lag':
            with np.errstate(divide='ignore', invalid='ignore'):
                global_ttcf[:] = np.divide(global_intensities, global_counts)

        return global_ttcf

    # This is Chan's method for combining standard deviations
    # https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Parallel_algorithm
    @staticmethod
    def _calculate_std_from_processed_chunks_diagonals(chunks_diagonals_processed):
        """
        Calculates the overall mean and standard deviation from data split into chunks.
        Using Chen method for combining standard deviations.
        """
        total_elements = np.sum([r[0] for r in chunks_diagonals_processed])
        # Weighted mean
        overall_mean = np.sum([r[0] * r[1] for r in chunks_diagonals_processed]) / total_elements
        # Variance: sum of within-chunk variances + variance between chunk means
        variance = (
            np.sum([r[0] * (r[2]**2 + (r[1] - overall_mean)**2) for r in chunks_diagonals_processed]) / total_elements
        )
        overall_std = np.sqrt(variance)
        return overall_std, total_elements
    
    def _calculate_ttcf_axes(self):
        """
        Calculate the ttcf axes based on the provided binning."""
    
        if self.ttcf_format is None or (self.ttcf_format == 't1,t2' and self.t1_t2_binning is None):
            self.results.t1 = np.arange(self.frames_shape[0], dtype=np.int32)
            self.results.t2 = self.results.t1

        elif self.ttcf_format == 't1,t2' and self.t1_t2_binning is not None:
            bin_edges_t1, _ = lin_bin(np.arange(self.frames_shape[0]), self.t1_t2_binning)
            self.results.t1 = bin_centers(bin_edges_t1)
            self.results.t2 = self.results.t1
        
        elif self.ttcf_format == 'age,lag':

            t = np.arange(self.frames_shape[0], dtype=np.int32)

            age,_ = lin_bin(t,self.age_binning)
            lag, _=lin_log_bin(t,self.lag_binning[0],self.lag_binning[1])

            age_centers=bin_centers(age)
            lag_centers=bin_centers_mixed(lag,self.lag_binning[0])

            self.results.age = age_centers
            self.results.lag = lag_centers

    
    
    def _dask_cluster_setup(self):
        """
        Setup Dask cluster, slurm or local, based on the provided configuration.
        """
        logger.info(f"Setting up Dask cluster : {self.dask_cluster_type}")
        cluster_type = self.dask_cluster_type  # 'local' or 'slurm' or 'other'
        # TODO for the local cluster  system variables for BLAS threading should set inside the function making calculations
        if cluster_type == 'local':
            from dask.distributed import LocalCluster
            self._dask_cluster=LocalCluster(n_workers=self.dask_local_n_workers, 
                                            threads_per_worker=1,
                                            processes=True,
                                            env= {'XPCS_BLAS_THREADS': str(self.dask_local_blas_threads),
                                                })
            logger.info(f"Local Dask cluster with {self.dask_local_n_workers} workers and {self.dask_local_blas_threads} BLAS threads per worker started.")

        if cluster_type == 'slurm':
            from dask_jobqueue import SLURMCluster
            self._dask_cluster = SLURMCluster(
                queue=self.dask_cluster_queue,  # Specify SLURM partition/queue
                cores=self.dask_slurm_cores_per_worker,  # CPU cores per job - match your OMP_NUM_THREADS
                memory=self.dask_slurm_memory_per_worker,    # Memory per job
                processes=self.dask_slurm_processes_per_worker, # One Dask worker per SLURM job
                walltime=self.dask_cluster_walltime,  # Job time limit
                log_directory="./dask-worker-logs",
                python=python_executable,  # Use your current Python interpreter from env
                job_script_prologue=[
                    #"source /home/esrf/jankowsk/miniforge3/etc/profile.d/conda.sh",
                    #"conda activate cuda_12_2",
                    f"export OMP_NUM_THREADS={self.dask_slurm_cores_per_worker}",
                    f"export MKL_NUM_THREADS={self.dask_slurm_cores_per_worker}",
                    f"export OPENBLAS_NUM_THREADS={self.dask_slurm_cores_per_worker}"
                ],
                worker_extra_args=['--nthreads', '1']  # Ensure each worker uses a single thread!!! Important for BLAS
            )                                
            self._dask_cluster.scale(self.dask_slurm_workers)  # Adjust number of workers as needed
            logger.info(f"SLURM Dask cluster with {self.dask_slurm_workers} workers, CPUs per worker {self.dask_slurm_cores_per_worker} started.")
        self._dask_client = Client(self._dask_cluster)
        print("Dashboard:", self._dask_client.dashboard_link)
        logger.info("Dashboard: %s", self._dask_client.dashboard_link)


