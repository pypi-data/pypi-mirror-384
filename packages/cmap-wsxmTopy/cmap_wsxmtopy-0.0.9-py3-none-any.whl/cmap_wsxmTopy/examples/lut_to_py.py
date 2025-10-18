
##### imports ######
import matplotlib.pyplot as plt
import sys
import numpy as np
sys.path.append("src")
import cmap_wsxmTopy.cmap_wsxmTopy.src.converter as conv


##### code #######


### path of the .lut file, here one example provided in the example folder
fname  = 'examples/Julio.lut'

### convert the colormap

cmap_lut = conv.cmap_fromLut(fname)

# Test the converted colormap
plt.figure()
data = np.random.rand(10, 10)  # Example data
plt.imshow(data, cmap=cmap_lut)
plt.colorbar()
plt.show()