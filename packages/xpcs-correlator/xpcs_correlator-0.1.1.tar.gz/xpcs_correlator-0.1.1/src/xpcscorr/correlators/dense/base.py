import os
import time
import inspect

from typing import Optional
import numpy as np
from xpcscorr.core.base import Results

# Base class for all dense correlators
class DenseCorrelator:

    def __init__(self,
                frames, 
                roimask, 
                ttcf_format,
                t1_t2_binning, 
                age_binning,
                lag_binning,
                extra_options
                ):

        self.frames = frames
        self.roimask = roimask
        self.ttcf_format = ttcf_format
        self.t1_t2_binning = t1_t2_binning
        self.age_binning = age_binning
        self.lag_binning = lag_binning
        self.extra_options = extra_options

        self._types_verification()
        
    #TODO Make types checking during runtime- to finish
    def _types_verification(self):
        pass
    
    #Return results of the computation
    def _compute(self):
        pass

def _create_correlator_function(correlator_class):
    """
    Factory function that creates a correlator function using 
    the specified correlator class.
    
    Parameters
    ----------
    correlator_class : class
        The correlator class to use for calculation.
        
    Returns
    -------
    function
        A function that processes frames using the specified correlator class.
    """

    def correlator_dense(frames : np.ndarray,
                        roimask: np.ndarray,
                        ttcf_format : Optional[str] = None,
                        t1_t2_binning : Optional[int] = None,
                        age_binning : Optional[int] = None,
                        lag_binning : Optional[tuple] = None,
                        extra_options : Optional[dict] = None,
                        ) -> Results:
        
        correlator = correlator_class(frames, 
                                    roimask, 
                                    ttcf_format=ttcf_format,
                                    t1_t2_binning=t1_t2_binning, 
                                    age_binning=age_binning,
                                    lag_binning=lag_binning,
                                    extra_options=extra_options)
        
        return correlator.results
    
    # Define the function docstring in NumPy style
    correlator_dense.__doc__ = f"""
This correlator computes the two time correlation function (ttcf) 
and the one-time correlation function (g2) with errors (g2_err)  
for a given set of detectors frames. It allows to compute the ttcf in 
two different formats: t1,t2 or age,lag. The ttcf can be binned 
in both coordinate system using a standard linear binning t1, t2 axis 
and a hybrid linear-logarithmic binning scheme for the lag, and linear for
age axis. 

Parameters
----------
frames : np.ndarray
    The frames data in dense format or types uint8, uint16, and uint32.
roimask : np.ndarray
    The region of interest mask corresponding to different q-bins.
ttcf_format : str, optional
    The format of the ttcf. The default is None. Can be 't1,t2' or 'age,lag' 
    where age is defined as (t1+t2)/2 and lag is defined as t2-t1.
t1_t2_binning : int, optional
    The t1,t2 number of linear bins for each axis. The default is None.
age_binning : int, optional
    The number of age linear bins. The default is None.
lag_binning : tuple, optional
    The lag binning factor (N,n_points), N is a decade, 
    n_points is a number of bins for logarithmic part defining bins, 
    i.e., range(N*10) + logspace(N, …, n_points)
extra_options : dict, optional
    Extra options for the correlator.

Returns
-------
Results
    An object with the following attributes:
    
    - ttcf_format : str
      The format of the ttcf, can be None, "t1,t2", or "age,lag"
    - ttcf : np.ndarray or None
      Shape (qbin, t1, t2) or (qbin, age, lag)
    - g2 : np.ndarray
      Shape (qbin, lag)
    - g2_err : np.ndarray or None
      Shape (qbin, lag)
    - lag : np.ndarray or None
      None if ttcf_format is None
    - age : np.ndarray or None
      None if ttcf_format is None
    - t1 : np.ndarray or None
      The t1 coordinates
    - t2 : np.ndarray or None
      The t2 coordinates
    - roimask : np.ndarray
      Boolean array
"""

    # Append class-specific docstring if available
    class_doc = getattr(correlator_class, '__doc__', '') or ''
    if class_doc:
        class_doc = inspect.cleandoc(class_doc)
        correlator_dense.__doc__ += f"\n\nNotes\n-----\n{class_doc}"

    return correlator_dense


class Chunks:
    def __init__(self, frames_N,
                        chunks_N,
                        ):
        
        '''
        Class to handle chunking of the correlation matrix.
        
        Parameters
        ----------
        frames_N : int
            Number of frames in the 3D dataset. It is first dimension of 
            the frames array. The ttcf matrix size is frames_N x frames_N.
        chunks_N : int
            Number of chunks of ttcf matrix. The chunks size is defined as
            frames_N / chunks_N.
        '''

        self.frames_N = frames_N
        self.chunks_N = chunks_N

        # dictionary to store chunks information
        self.chunks={}

        # Calculate chunk indices and sizes
        self._get_chunk_indices()
        
        # Get chunks ID in snake order (zig-zag path in upper triangle)
        self.snake_chunks= self._select_snake_chunks()
    
    def _get_chunk_indices(self):
        """
        Calculate and store chunk info in self.chunks dictionary.
        Uses numpy for more elegant array operations.
        """
        # Get row and column indices
        row_indices = self._split_indices(self.frames_N, self.chunks_N)
        col_indices = self._split_indices(self.frames_N, self.chunks_N)
        
        # Build chunks dictionary using dictionary comprehension
        self.chunks = {
            row_chunk * self.chunks_N + col_chunk: {
                'coordinates': (row_chunk, col_chunk),
                'row_start': row_start,
                'row_end': row_end,
                'col_start': col_start,
                'col_end': col_end,
                'chunk_size': (row_end-row_start, col_end-col_start),
                'chunk_elements': (row_end-row_start)*(col_end-col_start),
                # Add diagonal information
                # The range of diagonals in the chunks represented as
                # the global matrix (chunked matrix not the chunk) diagonal offsets
                'diag_offset_min': col_start - row_end + 1,  # Most negative diagonal
                'diag_offset_max': col_end - row_start - 1,  # Most positive diagonal
            }
            for row_chunk, (row_start, row_end) in enumerate(row_indices)
            for col_chunk, (col_start, col_end) in enumerate(col_indices)
        }
        
        # Calculate the number of diagonals for each chunk
        for chunk_id, info in self.chunks.items():
            info['diag_N'] = info['diag_offset_max'] - info['diag_offset_min'] + 1

    def _split_indices(self, N, n_chunks):
        """
        Get (start, end) indices for splitting N into n_chunks.
        Distributes remainder to first chunks.
        """
        # Calculate base chunk size and remainder
        base_size = N // n_chunks
        remainder = N % n_chunks
        
        # Create array of endpoints
        endpoints = np.cumsum(
            [base_size + (1 if i < remainder else 0) for i in range(n_chunks)]
        )
        
        # Create pairs of (start, end)
        starts = np.append(0, endpoints[:-1])
        return list(zip(starts, endpoints))

    def _select_upper_triangle_chunks(self):
        """
        Select only chunks that cover the upper triangle of the matrix.
        Returns a list of chunk IDs that are in the upper triangle.
        """
        upper_triangle_chunks = []
        for chunk_id, info in self.chunks.items():
            row_chunk, col_chunk = info['coordinates']
            if col_chunk >= row_chunk:
                upper_triangle_chunks.append(chunk_id)
        return upper_triangle_chunks

    @staticmethod
    def _upper_triangle_snake(N):
        """
        Generate a zig-zag path for the upper triangle of an NxN matrix:
        - Start at (0,0), move right to (0,N-1)
        - Drop to (1,N-1), move left to (1,1)
        - Drop diagonally to (2,2), move right to (2,N-1)
        - Continue this pattern...
        Returns a list of (i, j) tuples (0-based indexing).
        """
        return [
            (i, j if i % 2 == 0 else N - 1 - (j - i))
            for i in range(N)
            for j in range(i, N)
        ]
    
    def animate_upper_triangle_snake(self,N, delay=0.3):
        """
        Animate the custom zig-zag path in the terminal.
        Parameters
        ----------
        N : int
            Number of chunks (matrix size NxN).
        delay : float, optional
            Delay between steps in seconds. The default is 0.3.
        Returns
        -------
        None.
        """
        
        path = self._upper_triangle_snake(N)
        path_elements = N * (N + 1) // 2
        matrix = [['.' for _ in range(N)] for _ in range(N)]

        for step, (i, j) in enumerate(path):
            os.system('clear')
            display = [row[:] for row in matrix]
            display[i][j] = 'X'
            print(f"Step {step+1}/{path_elements}: (i={i}, j={j})")
            for row in display:
                print(' '.join(row))
            print('-' * (2*N))
            time.sleep(delay)

    
    def _select_snake_chunks(self):
        N = self.chunks_N
        coord_to_id = {info['coordinates']: chunk_id for chunk_id, info in self.chunks.items()}
        return [coord_to_id[coord] for coord in self._upper_triangle_snake(N) if coord in coord_to_id]

    def map_chunk_diagonal_to_matrix(self, chunk_id, k):
        """
        Maps the k-th diagonal of a chunk to the corresponding 
        n-th diagonal in the overall chunked matrix.
        
        Parameters
        ----------
        chunk_id : int
            The ID of the chunk.
        k : int
            The local diagonal number within the chunk.
            0 is the main diagonal of the chunk.
            Positive values are above the main diagonal.
            Negative values are below the main diagonal.
            
        Returns
        -------
        int
            The corresponding diagonal number in the overall matrix.
        """
        if chunk_id not in self.chunks:
            raise ValueError(f"Chunk ID {chunk_id} not found")
        
        chunk_info = self.chunks[chunk_id]
        
        # Check if k is within the valid range for this chunk
        if k < chunk_info['diag_offset_min'] or k > chunk_info['diag_offset_max']:
            raise ValueError(
                f"Diagonal {k} is outside the range of diagonals in chunk {chunk_id}. "
                f"Valid range: [{chunk_info['diag_offset_min']}, {chunk_info['diag_offset_max']}]"
            )
        
        # Calculate the global matrix diagonal
        # The offset between chunk coordinates and matrix coordinates is (col_start - row_start)
        row_start = chunk_info['row_start']
        col_start = chunk_info['col_start']
        
        return k + (col_start - row_start)