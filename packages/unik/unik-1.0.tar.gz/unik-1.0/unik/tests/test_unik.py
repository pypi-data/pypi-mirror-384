"""
Tests for the unik package.
"""
import pytest
import numpy as np

from .. import Unique

def test_unique():
    """
    Test ``Unique`` helper
    """
    
    data = [1,1,1,2,2,9]
    
    for d in [data, np.array(data)]:
        un = Unique(d, verbose=False)
        
        # Unique values
        assert(len(un.values) == 3)
        assert(np.allclose(un.values, [1,2,9]))
        
        # Array indices
        assert(np.allclose(un.indices, [0, 0, 0, 1, 1, 2]))
        
        # Missing key 
        assert(un[-1].sum() == 0)
        
        # Existing key
        assert(un[1].sum() == 3)
        
        # __iter__ and __get__ methods
        for (v, vs) in un:
            #print(v)
            assert(np.allclose(un.array[un[v]], v))
            assert(np.allclose(un[v], vs))
            assert(np.allclose(un.array[vs], v))

