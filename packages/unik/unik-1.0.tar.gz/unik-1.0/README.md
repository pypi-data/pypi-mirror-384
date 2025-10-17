# unik

Provide functionality for working with selections of unique items in lists / arrays

## Installation

You can install unik using pip:

```bash
pip install unik
```

## Usage

```python
>>> import numpy as np
>>> from unik import Unique

>>> items = [1, 2, 2, 2, 3, 1, 4, 3]
>>> un = Unique(items, verbose=True)
   N  value     
====  ==========
   2           1
   3           2
   2           3
   1           4
  
>>> print(un.info(sort_counts=True))
   N  value     
====  ==========
   1           4
   2           1
   2           3
   3           2

>>> items = np.array(['apples', 'apples', 'oranges', 'apples', 'grapes'])
>>> un = Unique(items, verbose=True)
   N  value     
====  ==========
   3  apples    
   1  grapes    
   1  oranges   

>>> print(np.array(un.values)[un.counts > 1])
['apples']

>>> another_array = np.array(['tree', 'tree', 'tree', 'tree', 'vine'])
>>> for i in un.unique_index():
>>>     print(f'{items[i]} grow on a {another_array[i]}')
apples grow on a tree
grapes grow on a vine
oranges grow on a tree

# __get__ builtin returns boolean array
>>> print(un['apples'])
[ True  True False  True False]

>>> print(items[~un['apples']])
['oranges' 'grapes']

>>> print(another_array[~un['apples']])
['tree' 'vine']

```

## License

MIT License - see LICENSE file for details
