import ast
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.pyplot as plt
import numpy as np
import matplotlib

def cmap_fromLut(fname): # converts a .lut file given its path to a LinearSegmentedColormap
    # locate control points number for each color [blue,green,red] and store data
    control_points = []
    data = []
    with open(fname, "r") as f:
        for line in f:
            data.append(line.strip())
            if 'Number of Control Points' in line:
                split = line.split(':')
                control_points.append(int(split[1].strip()))
    # locate the
    location = []
    n=0
    for i in data:
        if 'Info' in i:
            location.append(n)
        n+=1
    # separate and store the control points
    points_B = data[location[0]+2:location[0]+2+control_points[0]]
    points_G = data[location[1]+2:location[1]+2+control_points[1]]
    points_R = data[location[2]+2:location[2]+2+control_points[2]]

    def convert(list): # to convert from string to array format
        A = []
        for i in list:
            A.append(ast.literal_eval(i.split(':')[1].strip()))
        A = np.array(A)
        sorted_indices = np.argsort(A[:,0])
        arr = A[sorted_indices]
        return arr

    points_B = convert(points_B)
    points_G = convert(points_G)
    points_R = convert(points_R)
    #invert the color map to match the original
    points_B[:,1] = 255-points_B[:,1]
    points_G[:,1] = 255-points_G[:,1]
    points_R[:,1] = 255-points_R[:,1]

    # Create the colormap
    cmap_lut = LinearSegmentedColormap('lut_colormap', {
        'red':   [(x/255.0, y/255.0, y/255.0) for x, y in points_R],
        'green': [(x/255.0, y/255.0, y/255.0) for x, y in points_G],
        'blue':  [(x/255.0, y/255.0, y/255.0) for x, y in points_B]
    })
    return cmap_lut


def export_colormap(colormap, filename):
    cmaplist = [colormap(i) for i in range(0,colormap.N,4)]
    colormap = matplotlib.colors.LinearSegmentedColormap.from_list('mcm',cmaplist, colormap.N/4)

    with open(filename, 'w') as file:
        file.write("WSxM file copyright UAM\n")
        file.write("New Format Palette. 2001\n")
        file.write("Image header size: 1143\n\n")
        
        def write_color_points(color_name, color_points):
            file.write(f"[{color_name} Info]\n")
            for i, point in enumerate(color_points):
                file.write(f"    Control Point {i}: ({int(point[0]*255)} , {255-int(point[1]*255)})\n")
            file.write(f"    Number of Control Points: {len(color_points)}\n\n")
        
        write_color_points("Blue", colormap._segmentdata['blue'])
        write_color_points("Green", colormap._segmentdata['green'])
        write_color_points("Red", colormap._segmentdata['red'])
        
        file.write("[Palette Generation Settings]\n")
        file.write("    Derivate Mode for the last blue Point: Automatic\n")
        file.write("    Derivate Mode for the last green Point: Automatic\n")
        file.write("    Derivate Mode for the last red Point: Automatic\n")
        file.write("    Is there a particular palette index colored?: No\n")
        file.write("    Smooth Blue: No\n")
        file.write("    Smooth Green: No\n")
        file.write("    Smooth Red: No\n\n")
        
        file.write("[Header end]")

def lut_cmap():
    lut_cmap = cmap_fromLut('examples/Julio.lut')
    return lut_cmap