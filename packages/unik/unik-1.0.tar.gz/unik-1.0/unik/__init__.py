"""
unik - Helper for unique entries in lists / arrays

A simple utility to work with unique elements in lists and arrays.
"""
import numpy as np

from .version import __version__

class Unique(object):
    def __init__(self, array, verbose=True, **kwargs):
        """
        Helper for unique items in an array

        Parameters
        ----------
        array : array-like
            Data to parse, generally strings but can be anything that can
            be parsed by `numpy.unique`

        verbose : bool
            Print info on initialization

        Attributes
        ----------
        dim : int
            ``size`` of input ``array``

        values : list
            Unique elements of ``array``

        indices : list
            Integer list length of ``array`` with the indices of ``values``
            for each element

        counts : list
            Counts of each element of ``values``


        Methods
        -------
        __get__(key)
            Return a `bool` array where entries of ``array`` match the
            specified ``key``

        __iter__
            Iterator over ``values``

        """
        if isinstance(array, list):
            self.array = np.array(array)
        else:
            self.array = array

        _ = np.unique(self.array, return_counts=True, return_inverse=True)
        self.dim = self.array.size
        self.zeros = np.zeros(self.array.shape, dtype=bool)

        self.values = [l for l in _[0]]
        self.indices = _[1]
        self.counts = _[2]

        if verbose:
            print(self.info(**kwargs))

    @property
    def N(self):
        """
        Number of unique ``values``
        """
        return len(self.values)

    def info(self, sort_counts=0, **kwargs):
        """
        Print a summary

        Parameters
        ----------
        sort_counts : int, optional
            Sort the counts in ascending order if `sort_counts` is non-zero.
            Default is 0.

        """
        lines = [
            f'{"N":>4}  {"value":10}',
            "====  ==========",
        ]
        
        if sort_counts:
            so = np.argsort(self.counts)[:: int(sort_counts)]
        else:
            so = np.arange(self.N)

        for i in so:
            v, c = self.values[i], self.counts[i]
            lines.append(f"{c:>4}  {v:10}")
        
        return "\n".join(lines)

    def count(self, key):
        """
        Get occurrences count of a particular ``value``.

        Parameters
        ----------
        key : object
            The value to count occurrences of.

        Returns
        -------
        count : int
            The number of occurrences of the specified value.

        """
        if key in self.values:
            ix = self.values.index(key)
            return self.counts[ix]
        else:
            return 0
    
    
    @property
    def list_indices(self):
        """
        Build list of lists of indices that each unique value
        """

        inds = [[] for i in range(self.N)]
        so = np.argsort(self.indices)

        for i, ii in zip(so, self.indices[so]):
            inds[ii].append(i)

        # Sort the sublists
        for i in range(self.N):
            if self.counts[i] > 1:
                inds[i].sort()

        return inds
    
        
    def unique_index(self, index=0):
        """
        Return array of indices of the parent array that makes
        a unique output array

        Parameters
        ----------
        index : int, optional
            The index of the value to return. Default is 0.

        Returns
        -------
        uix : list
            List of unique indices

        """
        uix = [ind[index] for ind in self.list_indices]

        return uix
    

    def __iter__(self):
        """
        Iterable over `values` attribute

        Returns a tuple of the value and the boolean selection array for that
        value.
        """
        i = 0
        while i < self.N:
            vi = self.values[i]
            yield (vi, self[vi])
            i += 1

    def __getitem__(self, key):
        if key in self.values:
            ix = self.values.index(key)
            test = self.indices == ix
            return test
        else:
            return self.zeros

    def __len__(self):
        return self.N

__all__ = ['Unique']
