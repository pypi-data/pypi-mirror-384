##### imports ######
import matplotlib.pyplot as plt
import sys
sys.path.append("src")
import converter as conv


##### code #######

# colormap from matplotlib
cmap = plt.cm.magma


# export the map in .lut format
conv.export_colormap(cmap, 'out/output_colormap.lut')
