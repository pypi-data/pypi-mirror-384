import numpy as np

def mask_to_3d_bool_stack(mask: np.ndarray) -> np.ndarray:
    """
    Converts various mask formats to a 3D boolean stack.
    
    Parameters
    ----------
    mask : np.ndarray
        Input mask in one of the supported formats:
        - 2D mask with 0/1 or False/True
        - 2D mask with integer labels (each label is a mask index)
        - 3D mask with 0/1 or False/True
        - 3D mask with integer values (nonzero = True)
    
    Returns
    -------
    np.ndarray
        3D boolean array of shape (n_masks, height, width)
    """
    mask = np.asarray(mask)
    if mask.ndim == 2:
        if mask.dtype == bool or np.array_equal(np.unique(mask), [0, 1]) or np.array_equal(np.unique(mask), [0]):
            # 2D binary mask: single mask
            return mask[None, ...].astype(bool)
        else:
            # 2D integer mask: each unique nonzero value is a mask index
            labels = np.unique(mask)
            labels = labels[labels != 0]  # Exclude zero label
            if len(labels) == 0:
                # Only zeros: return a single all-False mask
                return np.zeros((1,) + mask.shape, dtype=bool)
            stack = np.zeros((len(labels),) + mask.shape, dtype=bool)
            for i, label in enumerate(labels):
                stack[i] = (mask == label)
            return stack
    elif mask.ndim == 3:
        # 3D mask: treat each slice as a mask
        return mask.astype(bool)
    else:
        raise ValueError("Mask must be 2D or 3D numpy array")

def lin_log_bin(x, N, n_log_bins) -> tuple[np.ndarray, np.ndarray]:
    """
    Create hybrid linear-logarithmic binning for the linear x input data \
    with a linear part from 0 to N and a logarithmic part from N to the maximum.
    The logarithmic part is divided into n_log_bins bins.
    The linear part is divided into 10**N bins.

    Parameters
    ----------
    x : np.ndarray
        Input of x coordinates.
    N : int
        The log10 decade from which logarithmic binning should start.
    n_log_bins : int
        Number of logarithmic equally distributed bins.

    Returns
    -------
    bin_edges : np.ndarray
        The edges of the bins.
    binned_indices : np.ndarray
        The indices of the bins for each element in x.
    """

    N_max = np.log10(np.max(x))
    if N_max < N:
        N_max = N

    bin_edges = np.concatenate((
        #Here -0.5 was requested by Yuri.
        np.arange(0,10**N)-0.5,  # the linear part, bins are centered around integers
        np.logspace(N, N_max, num=n_log_bins) # the logarithmic part
    ))

    bin_edges[-1] = np.max(x) # ensure the last bin edge is exactly the max of x

    binned_indices = np.digitize(x, bin_edges, right=True) 
    binned_indices = binned_indices[(binned_indices > 0) &
                                    (binned_indices < len(bin_edges))]
    
    return bin_edges, binned_indices


def bin_centers_mixed(bins_lag, N):
    """
    Compute bin centers for hybrid linear-logarithmic bins.
    The linear part is from 0 to 10**N and the logarithmic part is
    from 10**N to the maximum.
    
    Parameters
    ----------
    bins_lag : np.ndarray
        The edges of the bins.
    N : int
        The log10 decade from which logarithmic binning starts.
    
    Returns
    -------
    centers : np.ndarray
        The centers of the bins.
    """

    split_idx = np.searchsorted(bins_lag, 10**N)
    centers = np.empty(len(bins_lag) - 1)
    # Linear part
    centers[:split_idx] = 0.5 * (bins_lag[1:split_idx+1] + bins_lag[:split_idx])
    # Log part
    centers[split_idx:] = np.sqrt(bins_lag[split_idx+1:] * bins_lag[split_idx:-1])
    return centers


def lin_bin(x, N) -> tuple[np.ndarray, np.ndarray]:
    """
    Create linear binning for the linear x input data.
    The linear part is divided into N bins.

    Parameters
    ----------
    x : np.ndarray
        Input of x coordinates.
    N : int
        The number of bins.

    Returns
    -------
    bin_edges : np.ndarray
        The edges of the bins.
    binned_indices : np.ndarray
        The indices of the bins for each element in x.
    """
    
    bin_edges = np.linspace(0, np.max(x), N+1)
    binned_indices = np.digitize(x, bin_edges, right=True)
    binned_indices = binned_indices[(binned_indices > 0) &
                                    (binned_indices < len(bin_edges))]

    return bin_edges, binned_indices

def bin_centers(bins):
    """
    Compute bin centers from bin edges.
    
    Parameters
    ----------
    bins : np.ndarray
        The edges of the bins.
    
    Returns
    -------
    centers : np.ndarray
        The centers of the bins.
    """
    return 0.5 * (bins[1:] + bins[:-1])


def bins_calc_tccf_t1_t2_chunk(t1_t2_binning, global_ttcf_size, rows_start, rows_end, cols_start, cols_end):
        """
        Bin the chunk ttcf matrix according to the provided t1_t2_binning.
        
        Parameters
        ----------
        ttcf : np.ndarray
            The chunk ttcf matrix to be binned.
        global_ttcf_size : int
            The axis size of the full ttcf matrix - equal to the number of frames.
        t1_t2_binning : int
            The number of linear bins for each axis (t1 and t2).
        
        Returns
        -------
        local_bin_t1 : np.ndarray
            The bin edges for t1 in the chunk.
        local_bin_t2 : np.ndarray
            The bin edges for t2 in the chunk.
        bin_t1_start : int
            The starting index of the t1 bins in the global bin array.
        bin_t1_end : int
            The ending index of the t1 bins in the global bin array.
        bin_t2_start : int
            The starting index of the t2 bins in the global bin array.
        bin_t2_end : int
            The ending index of the t2 bins in the global bin array.
        """

        global_bin_t1, _ = lin_bin(np.arange(global_ttcf_size), t1_t2_binning)
        global_bin_t2 = global_bin_t1


        # Row bins
        bin_t2_start = np.searchsorted(global_bin_t2, rows_start, side='right') - 1
        bin_t2_end   = np.searchsorted(global_bin_t2, rows_end-1, side='right')
        # Column bins
        bin_t1_start = np.searchsorted(global_bin_t1, cols_start, side='right') - 1
        bin_t1_end   = np.searchsorted(global_bin_t1, cols_end-1, side='right')

        # Clamp indices
        bin_t1_start = max(bin_t1_start, 0)
        bin_t1_end = min(bin_t1_end, len(global_bin_t1)-1)
        bin_t2_start = max(bin_t2_start, 0)
        bin_t2_end = min(bin_t2_end, len(global_bin_t2)-1)

        # Local bins for the chunk
        local_bin_t1 = global_bin_t1[bin_t1_start:bin_t1_end+1]
        local_bin_t2 = global_bin_t2[bin_t2_start:bin_t2_end+1]
        
        return local_bin_t1, local_bin_t2, bin_t1_start, bin_t1_end, bin_t2_start, bin_t2_end


def bins_calc_tccf_age_lag_chunk(age_binning, lag_binning, global_ttcf_size, rows_start, rows_end, cols_start, cols_end):
    """
    Calculate bin edges for age and lag values for a chunk.
    The age is (t1 + t2)/2 and lag is (t2 - t1).
    
    For lag values, we need to consider the actual range of lag values in the chunk,
    including negative lags for the lower triangle.

    Parameters
    ----------
    age_binning : int
        Number of linear bins for age.
    lag_binning : tuple(int, int)
        Tuple specifying (linear part end decade, number of log bins) for lag.
    global_ttcf_size : int
        The axis size of the full ttcf matrix - equal to the number of frames.
    rows_start : int
        Starting index of the chunk rows (t2).
    rows_end : int
        Ending index of the chunk rows (t2).
    cols_start : int
        Starting index of the chunk columns (t1).
    cols_end : int
        Ending index of the chunk columns (t1).

    Returns
    -------
    local_bin_lag : np.ndarray
        The bin edges for lag in the chunk.
    local_bin_age : np.ndarray
        The bin edges for age in the chunk.
    bin_lag_start : int
        The starting index of the lag bins in the global bin array.
    bin_lag_end : int
        The ending index of the lag bins in the global bin array.
    bin_age_start : int
        The starting index of the age bins in the global bin array.
    bin_age_end : int
        The ending index of the age bins in the global bin array.
    """
    # For age binning, we can continue with linear binning
    global_age_bins, _ = lin_bin(np.arange(global_ttcf_size), age_binning)
    
    # For lag binning, we need to consider the actual range of lag values
    # Maximum lag value would be the difference between max and min frame indices
    max_lag_value = global_ttcf_size - 1
    
    # Create lag bins using lin_log_bin (linear from 0 to 10^lag_binning[0], 
    # then log-spaced with lag_binning[1] bins)
    global_lag_bins, _ = lin_log_bin(np.arange(max_lag_value + 1), lag_binning[0], lag_binning[1])
    
    # Check if this chunk spans the diagonal
    is_diagonal_chunk = rows_start <= cols_end and cols_start <= rows_end
    
    if is_diagonal_chunk:
        # This chunk includes both positive and negative lags
        min_lag = 0  # Include the diagonal (zero lag)
        max_lag = max(rows_end - cols_start - 1, cols_end - rows_start - 1)
    else:
        # Handle purely upper or lower triangle
        if rows_start > cols_end:
            # Upper triangle (positive lags)
            min_lag = rows_start - cols_end
            max_lag = rows_end - cols_start - 1
        else:
            # Lower triangle (negative lags)
            min_lag = 0  # We'll convert to positive later
            max_lag = cols_end - rows_start
    
    # Find bin indices that cover this range
    bin_lag_start = np.searchsorted(global_lag_bins, min_lag, side='right') - 1
    bin_lag_end = np.searchsorted(global_lag_bins, max_lag, side='right')
    
    # For age bins, use the original approach
    bin_age_start = np.searchsorted(global_age_bins, (cols_start + rows_start)/2, side='right') - 1
    bin_age_end = np.searchsorted(global_age_bins, (cols_end + rows_end)/2, side='right')
    
    # Clamp indices
    bin_age_start = max(bin_age_start, 0)
    bin_age_end = min(bin_age_end, len(global_age_bins)-1)
    bin_lag_start = max(bin_lag_start, 0)
    bin_lag_end = min(bin_lag_end, len(global_lag_bins)-1)
    
    # Local bins for the chunk
    local_bin_lag = global_lag_bins[bin_lag_start:bin_lag_end+1]
    local_bin_age = global_age_bins[bin_age_start:bin_age_end+1]
    
    # Ensure we always have at least 2 bin edges
    if len(local_bin_lag) < 2:
        local_bin_lag = np.array([0, max_lag + 1])
        bin_lag_start = 0
        bin_lag_end = 1
        
    if len(local_bin_age) < 2:
        local_bin_age = np.array([cols_start, rows_end])
        bin_age_start = 0
        bin_age_end = 1
    
    return local_bin_lag, local_bin_age, bin_lag_start, bin_lag_end, bin_age_start, bin_age_end
   

def simulate_decorrelating_frames(n_frames, X, Y, noise_level=1.0):
    """
    Simulate a stack of frames that decorrelate over time.
    Each frame is generated by adding random noise to the previous frame.

    Parameters
    ----------
    n_frames : int
        Number of frames to simulate.
    X : int
        Width of each frame.
    Y : int
        Height of each frame.
    noise_level : float
        The level of noise to add to each frame.

    Returns
    -------
    frames : np.ndarray
        The simulated stack of frames.
    """
    # Start with a random initial frame
    frames = np.zeros((n_frames, X, Y), dtype=np.float32)
    frames[0] = np.random.poisson(40, (X, Y))
    for i in range(1, n_frames):
        # Each frame is the previous frame plus random noise (decorrelation)
        frames[i] = frames[i-1] + np.random.normal(0, noise_level * i, (X, Y))
    return frames


