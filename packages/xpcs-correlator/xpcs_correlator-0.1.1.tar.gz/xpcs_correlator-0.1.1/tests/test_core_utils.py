import numpy as np
from xpcscorr.core.utils import (mask_to_3d_bool_stack,
                                 lin_bin,
                                 lin_log_bin,
                                 )

def test_mask_to_3d_bool_stack():
    # 2D binary mask (0/1)
    mask_2d_bin = np.array([[0, 1, 0],
                            [1, 0, 1],
                            [0, 1, 0]])
    out = mask_to_3d_bool_stack(mask_2d_bin)
    assert out.shape == (1, 3, 3)
    assert np.array_equal(out[0], mask_2d_bin.astype(bool))

    # 2D binary mask (all zeros)
    mask_2d_zero = np.zeros((3, 3), dtype=int)
    out = mask_to_3d_bool_stack(mask_2d_zero)
    assert out.shape == (1, 3, 3)
    assert np.all(out == False)

    # 2D boolean mask
    mask_2d_bool = np.array([[True, False, True],
                             [False, True, False],
                             [True, False, True]])
    out = mask_to_3d_bool_stack(mask_2d_bool)
    assert out.shape == (1, 3, 3)
    assert np.array_equal(out[0], mask_2d_bool)

    # 2D integer mask (labels)
    mask_2d_labels = np.array([[0, 2, 1],
                               [1, 2, 0],
                               [2, 1, 0]])
    out = mask_to_3d_bool_stack(mask_2d_labels)
    assert out.shape == (2, 3, 3)  # labels 1 and 2
    assert np.array_equal(out[0], mask_2d_labels == 1)
    assert np.array_equal(out[1], mask_2d_labels == 2)

    # 3D binary mask
    mask_3d_bin = np.zeros((3, 3, 3), dtype=int)
    mask_3d_bin[0, 0, 0] = 1
    mask_3d_bin[1, 1, 1] = 1
    mask_3d_bin[2, 2, 2] = 1
    out = mask_to_3d_bool_stack(mask_3d_bin)
    assert out.shape == (3, 3, 3)
    assert out[0, 0, 0] == True
    assert out[1, 1, 1] == True
    assert out[2, 2, 2] == True
    assert np.sum(out) == 3

    # 3D boolean mask
    mask_3d_bool = np.zeros((3, 3, 3), dtype=bool)
    mask_3d_bool[0, 1, 2] = True
    mask_3d_bool[1, 2, 0] = True
    mask_3d_bool[2, 0, 1] = True
    out = mask_to_3d_bool_stack(mask_3d_bool)
    assert out.shape == (3, 3, 3)
    assert out[0, 1, 2] == True
    assert out[1, 2, 0] == True
    assert out[2, 0, 1] == True
    assert np.sum(out) == 3

    print("All mask_to_3d_bool_stack tests passed.")


def test_lin_bin():

    x_points = np.arange(1,101)
    x_edges = lin_bin(x_points, 10)
    
    assert len(x_edges[0]) == 11
    assert len(x_edges[1]) == len(x_points)
    assert np.allclose(x_edges[0], np.linspace(0,100,11))
    assert np.allclose(x_edges[1], np.repeat(np.arange(1, 11), 10))

def test_lin_log_bin():

    x_points = np.arange(0,1001)
    x_edges, x_indices = lin_log_bin(x_points, 1,3)

    assert x_edges.size == 13
    linear_part=np.arange(-0.5, 9, 1)
    log_part=np.array([10,100,1000])
    assert np.array_equal(x_edges, np.concatenate([linear_part, log_part]))