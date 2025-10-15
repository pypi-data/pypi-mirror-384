import pytest
import numpy as np
import h5py

from xpcscorr import correlator_dense_chunked, correlator_dense_reference
from xpcscorr.core.utils import mask_to_3d_bool_stack
from xpcscorr.correlators.dense.chunked import ChunkWorker, Chunks                                   


def make_data():
    n_frames=200
    size_frame=100

    data = np.random.poisson(10, (n_frames, size_frame, size_frame))

    
    #Some mask
    mask = np.ones((100,100), dtype=np.int8)
    mask[0:50, :] = 1
    mask[50:, :] = 2
    
    return data, mask

@pytest.fixture
def data_np_array():
    return make_data()
    

@pytest.fixture
def data_hdf5(tmp_path):

    data, mask = make_data()
    # write to temporary h5 file
    h5_path = tmp_path / "matrix3d.h5"
    with h5py.File(h5_path, "w") as f:
        f.create_dataset("det_frames", data=data, compression=None)

    # read dataset back 
    f=h5py.File(h5_path, "r")
    data_from_h5 = f["det_frames"]

    return data_from_h5, mask

@pytest.fixture(params=["data_np_array", "data_hdf5"])
def data_type(request):
    return request.getfixturevalue(request.param)

@pytest.fixture(params=[None,'local']) # None, local, slurm - as params
def dask_cluster_type(request):
    return request.param

#@pytest.mark.parametrize("dask_cluster_type", [None, "local","slurm"])
def test_compare_to_reference(data_type, dask_cluster_type):
    data, mask = data_type

    extra_options={'chunks_N':3,
                   'chunks_dtype':np.float32,
                   'dask_cluster_type': dask_cluster_type}

    result_ref = correlator_dense_reference(np.array(data), mask, ttcf_format='t1,t2')
    result_chunk = correlator_dense_chunked(data, mask, ttcf_format='t1,t2', extra_options=extra_options)
    
    for i in range(mask.max()):
        assert np.allclose(result_ref.g2[i], result_chunk.g2[i])
        assert np.allclose(result_ref.g2_err[i], result_chunk.g2_err[i])
        assert np.allclose(np.triu(result_ref.ttcf[i]),np.triu(result_chunk.ttcf[i]))
        assert np.allclose(result_ref.t1, result_chunk.t1)
        assert np.allclose(result_ref.t2, result_chunk.t2)


def test_compare_to_reference_binned_t1_t2(data_type, dask_cluster_type):
    data, mask = data_type

    extra_options={'chunks_N':3,
                   'chunks_dtype':np.float32,
                   'dask_cluster_type': dask_cluster_type}
    
    result_ref = correlator_dense_reference(np.array(data), mask, ttcf_format='t1,t2',t1_t2_binning=5)
    result_chunk = correlator_dense_chunked(data, mask, ttcf_format='t1,t2',t1_t2_binning=5,
                                             extra_options=extra_options)
    
    for i in range(mask.max()):
        assert np.allclose(result_ref.g2[i], result_chunk.g2[i])
        assert np.allclose(result_ref.g2_err[i], result_chunk.g2_err[i])
        assert np.allclose(result_ref.ttcf[i], result_chunk.ttcf[i], equal_nan=True)
        assert np.allclose(result_ref.t1, result_chunk.t1)
        assert np.allclose(result_ref.t2, result_chunk.t2)


def test_compare_to_reference_binned_age_lag(data_type, dask_cluster_type):
    data, mask = data_type

    extra_options={'chunks_N':3,
                   'chunks_dtype':np.float32,
                   'dask_cluster_type': dask_cluster_type}
    
    result_ref = correlator_dense_reference(np.array(data), mask, ttcf_format='age,lag',age_binning=5, lag_binning=(2,3))
    result_chunk = correlator_dense_chunked(data, mask, ttcf_format='age,lag',age_binning=5, lag_binning=(2,3), 
                                            extra_options=extra_options)
    for i in range(mask.max()):
        assert np.allclose(result_ref.g2[i], result_chunk.g2[i])
        assert np.allclose(result_ref.g2_err[i], result_chunk.g2_err[i])
        assert np.allclose(result_ref.ttcf[i], result_chunk.ttcf[i],equal_nan=True)
        assert np.allclose(result_ref.age, result_chunk.age)
        assert np.allclose(result_ref.lag, result_chunk.lag)
                                       
def test_chunk_worker_load_data_h5_and_ram(data_hdf5):
    """
    Test if the ChunkWorker loads the same data from h5 and from ram.
    """
    
    data_h5_metadata, roimask = data_hdf5
    data_ram=np.array(data_h5_metadata)

    chunks= Chunks(data_ram.shape[0],3)
     
     # ---Mask processing---
    roimask = mask_to_3d_bool_stack(roimask)

    chunks= Chunks(data_ram.shape[0],3)

    for k in range(len(chunks.chunks)):
        for i in range(roimask.shape[0]):
            
            ind_y, ind_x = np.where(roimask[i])
            data_ram_masked = (data_ram[chunks.chunks[k]['row_start']:chunks.chunks[k]['row_end'], ind_y, ind_x],
                            data_ram[chunks.chunks[k]['col_start']:chunks.chunks[k]['col_end'], ind_y, ind_x])

            worker_h5=ChunkWorker(roimask, chunks.chunks, np.float32, data_ram.shape)
            worker_ram=ChunkWorker(roimask, chunks.chunks, np.float32, data_ram.shape)
        
            chunk_data_ram=worker_ram._load_chunk_data(data_ram_masked, i, k)
            chunk_data_h5=worker_h5._load_chunk_data((data_h5_metadata.file.filename, data_h5_metadata.name),i, k)

            assert np.allclose(chunk_data_h5[0], chunk_data_ram[0])
            assert np.allclose(chunk_data_h5[1], chunk_data_ram[1])
