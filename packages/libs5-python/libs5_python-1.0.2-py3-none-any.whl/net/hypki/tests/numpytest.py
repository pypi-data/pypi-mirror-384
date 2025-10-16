'''
Created on 21-06-2013

@author: ahypki
'''

import numpy as np
import scipy.signal

a = np.zeros(100)
a[0] = 1
a[1] = 2
a[2] = 3
a[3] = 4
a[4] = 3
a[5] = 1
a[6] = 0
a[7] = -1
a[8] = 2
a[9] = 3
a[10] = 2
a[11] = 1
print(a)
res = scipy.signal.argrelmax(a)
print(res)

b = np.zeros(100)
b[0] = 1
b[1] = 2
b[2] = 1
b[3] = 2
bb = np.trim_zeros(b)
print(bb.mean())
print(bb.std())