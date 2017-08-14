import numpy as np
import numpy.ma as ma

x = np.array([1,2,3,-1,5])

# mx = ma.masked_array(x, mask=[0,0,0,1,0])
mx = ma.masked_equal(x, 5)

print (mx.mean())
