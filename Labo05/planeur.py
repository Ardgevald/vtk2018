import vtk
import numpy as np
import sys
from dateutil import parser
import pyproj
from math import pi

GLIDER_FILE_PATH = "vtkgps.txt"
MAP_FILE_PATH = "EarthEnv-DEM90_N60E010.bil"

MAP_SIZE_X = 3000
MAP_SIZE_Y = 3000
MAP_SIZE_Z = 1

MIN_LONG = 5.0
MAX_LONG = 7.5
MIN_LAT = 45.0
MAX_LAT = 47.5

# transforme un angle en degrés vers des radians
def angleToRad(angle):
    return angle * pi / 180

#how to convert
coordinateSwedish = pyproj.Proj(init='epsg:3021')
coordinateGlobal = pyproj.Proj(init='epsg:4326')
xHG, yHG = 1349340, 7022573
xHD, yHD = 1371573, 7022967
xBG, yBG = 1349602, 7005969
xBD, yBD = 1371835, 7006362
print(pyproj.transform(coordinateSwedish,coordinateGlobal,1349340,7022573))
print(pyproj.transform(coordinateSwedish,coordinateGlobal,1371573,7022967))
print(pyproj.transform(coordinateSwedish,coordinateGlobal,1349602,7005969))
print(pyproj.transform(coordinateSwedish,coordinateGlobal,1371835,7006362))

gliderCoordinates = np.genfromtxt(GLIDER_FILE_PATH, dtype=[('x', 'i4'),('y', 'i4'), ('alt', 'f4'), ('date', 'U30')], usecols=(1, 2, 3, 4, 5), skip_header=1, names=('x', 'y', 'altitude', 'date'), encoding='utf-8')

mapData = np.fromfile(MAP_FILE_PATH)

print(mapData)
print(gliderCoordinates[0])
mapData.reshape(MAP_SIZE_X, MAP_SIZE_Y)

vecfunc = np.vectorize(pyproj.transform) #Convert python function to vector function
result=vecfunc([3,2,1],[4,8,2])


#création de la map
structuredGrid = vtk.vtkStructuredGrid()
structuredGrid.SetDimensions([MAP_SIZE_X, MAP_SIZE_Y, 1])

points = vtk.vtkPoints()
points.Allocate(MAP_SIZE_X * MAP_SIZE_Y)

#prise en compte de l'altitude
scalars = vtk.vtkIntArray()
scalars.SetNumberOfComponents(1)

for x in range(0, MAP_SIZE_X):
    vectorUnityLatX = (xHD - xHG) * (x / MAP_SIZE_X) + (xBD - xBG) * ((MAP_SIZE_X - x) / MAP_SIZE_X)
    vectorUnityLatY = (yHD - yHG) * (x / MAP_SIZE_X) + (yBD - yBG) * ((MAP_SIZE_X - x) / MAP_SIZE_X)
    for y in range(0, MAP_SIZE_Y):
        vectorUnityLonX = (xBG - xHG) * (y / MAP_SIZE_Y) + (xBD - xBG) * ((MAP_SIZE_Y - y) / MAP_SIZE_Y)
        vectorUnityLonY = (yBD - yHD) * (y / MAP_SIZE_Y) + (yBD - yBG) * ((MAP_SIZE_Y - y) / MAP_SIZE_Y)

        latSwedish = x * vectorUnityLatX + y * vectorUnityLonX
        lonSwedish = x * vectorUnityLatY + y * vectorUnityLonY
        latGlobal, lonGlobal = pyproj.transform(coordinateSwedish,coordinateGlobal,latSwedish,lonSwedish)

        alt = mapData[y][x]

        points.InsertNextPoint(
            alt,
            angleToRad(latGlobal),
            angleToRad(lonGlobal)
        )