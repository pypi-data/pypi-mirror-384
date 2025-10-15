import numpy as np
from typing import Union, Optional

class Results:
    r'''
    The Results class is a container for the results \
    of the correlation analysis. It holds the computed 
    correlation results and metadata.
    '''

    def __init__(self, 
            g2: Optional[np.ndarray] = None,
            roimask: Optional[np.ndarray] = None,
            g2_err: Optional[np.ndarray] = None,
            ttcf_format: Optional[str] = None, 
            ttcf: Optional[np.ndarray] = None,
            t1: Optional[np.ndarray] = None,
            t2: Optional[np.ndarray] = None,
            lag: Optional[np.ndarray] = None,
            age: Optional[np.ndarray] = None,
            **kwargs):
    
        self.g2 = None if g2 is None else g2
        self.roimask = np.array([]) if roimask is None else roimask
        self.g2_err = None if g2_err is None else g2_err
        self.ttcf_format = ttcf_format
        self.ttcf = None if ttcf is None else ttcf
        self.t1 = None if t1 is None else t1
        self.t2 = None if t2 is None else t2
        self.lag = None if lag is None else lag
        self.age = None if age is None else age
        self.extra = kwargs




