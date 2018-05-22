import vtk
import numpy as np
import sys
from dateutil import parser

GLIDER_FILE_PATH = "vtkgps.txt"
MAP_FILE_PATH = "EarthEnv-DEM90_N60E010.bil"

MAP_SIZE_X = 6000
MAP_SIZE_Y = 6000

gliderCoordinates = np.genfromtxt(GLIDER_FILE_PATH, dtype=[('x', 'i4'),('y', 'i4'), ('alt', 'f4'), ('date', 'U30')], usecols=(1, 2, 3, 4, 5), skip_header=1, names=('x', 'y', 'altitude', 'date'), encoding='utf-8')

mapData = np.fromfile(MAP_FILE_PATH)
mapData.reshape(MAP_SIZE_X, MAP_SIZE_Y)

print(mapData)
print(gliderCoordinates[0])