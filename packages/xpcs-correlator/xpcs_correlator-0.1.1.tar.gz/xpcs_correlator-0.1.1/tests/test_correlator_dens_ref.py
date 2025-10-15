import pytest
import numpy as np

from xpcscorr import correlator_dense_reference
                                                  
@pytest.fixture
def create_data():
    
    n_frames=1000
    size_frame=100

    data = np.random.poisson(1000, (n_frames, size_frame, size_frame))

    #Some mask
    mask = np.ones((100,100), dtype=np.int8)
    mask[20:80, 20:80] = 1
    mask[0:10, 90:100] = 2
    
    return data, mask

def test_correlator_dense_reference(create_data):
    data, mask = create_data
    result = correlator_dense_reference(data, mask)
    
    assert result.g2.shape == (2, data.shape[0]-1)
    assert result.g2_err.shape == (2, data.shape[0]-1)
    assert result.ttcf is None


def test_correlator_dense_reference_t1_t2(create_data):
    data, mask = create_data
    result = correlator_dense_reference(data, mask, ttcf_format='t1,t2')
    
    assert result.g2.shape == (2, data.shape[0]-1)
    assert result.g2_err.shape == (2, data.shape[0]-1)
    assert result.ttcf.shape == (2, data.shape[0], data.shape[0])

def test_correlator_dense_reference_binned_t1_t2(create_data):
    data, mask = create_data
    
    ttcf_format = 't1,t2'
    t1_t2_binning = 100  # 100 linear bins

    result = correlator_dense_reference(data, mask, 
                                        ttcf_format=ttcf_format, 
                                        t1_t2_binning=t1_t2_binning)
    
    assert result.ttcf[0].shape == (t1_t2_binning, t1_t2_binning)
    assert result.t1.shape[0] == t1_t2_binning
    assert result.t2.shape[0] == t1_t2_binning
    assert result.g2.shape == (2, data.shape[0]-1)
    assert result.g2_err.shape == (2, data.shape[0]-1)


def test_correlator_dense_reference_binned_age_lag(create_data):
    data, mask = create_data

    lag_binning = (2, 5)  # linear to 10, then 5 bins 
    age_binning = 50      # 50 linear bins

    result= correlator_dense_reference(data, mask, 
                                       ttcf_format='age,lag', 
                                       age_binning=age_binning, 
                                       lag_binning=lag_binning)

    assert result.ttcf.shape == (2, age_binning, 10**lag_binning[0]-1+lag_binning[1])
    assert result.age.shape == (age_binning,)
    assert result.lag.shape == (10**lag_binning[0]-1+lag_binning[1],)
    assert result.g2.shape == (2, data.shape[0]-1)
    assert result.g2_err.shape == (2, data.shape[0]-1)
    
