import vtk
import numpy as np
import sys
from dateutil import parser
import pyproj
from math import pi, floor, ceil

# distance de la caméra en proportion du rayon de la terre
distanceFactor = 1.015

EARTH_RADIUS = 6371009

GLIDER_FILE_PATH = "vtkgps.txt"
MAP_FILE_PATH = "EarthEnv-DEM90_N60E010.bil"

MAP_SIZE_X = 6000
MAP_SIZE_Y = 6000
MAP_SIZE_Z = 1

#how to convert
coordinateSwedish = pyproj.Proj(init='epsg:3021')
coordinateGlobal = pyproj.Proj(init='epsg:4326')

## coordonées des 4 coins (HG = Haut Gauche, BD = Bas Droite)
xHG, yHG = 1349340, 7022573
print(pyproj.transform(coordinateSwedish,coordinateGlobal,xHG, yHG))
xHD, yHD = 1371573, 7022967
xBG, yBG = 1349602, 7005969
xBD, yBD = 1371835, 7006362
print(pyproj.transform(coordinateSwedish,coordinateGlobal,xBD, yBD))

MIN_LONG, MIN_LAT = pyproj.transform(coordinateSwedish,coordinateGlobal,min(xHG, xBG), max(yHD, yHG))
MAX_LONG, MAX_LAT = pyproj.transform(coordinateSwedish,coordinateGlobal, max(xHD, xBD), min(yBD, yBG))

MIN_X = floor((MIN_LONG - 10) * MAP_SIZE_X/5)
MAX_X = ceil((MAX_LONG - 10) * MAP_SIZE_X/5)
MIN_Y = floor((MIN_LAT - 65) * MAP_SIZE_Y/-5)
MAX_Y = ceil((MAX_LAT - 65) * MAP_SIZE_Y/-5)

MEAN_LONG = np.mean([MIN_LONG, MAX_LONG])
MEAN_LAT = np.mean([MIN_LAT, MAX_LAT])

MAP_REDUCED_SIZE_X = MAX_X - MIN_X
MAP_REDUCED_SIZE_Y = MAX_Y - MIN_Y

print(MAP_REDUCED_SIZE_X)
print(MAP_REDUCED_SIZE_Y)

# transforme un angle en degrés vers des radians
def angleToRad(angle):
    return angle * pi / 180

gliderCoordinates = np.genfromtxt(GLIDER_FILE_PATH, dtype=[('x', 'i4'),('y', 'i4'), ('alt', 'f4'), ('date', 'U30')], usecols=(1, 2, 3, 4, 5), skip_header=1, names=('x', 'y', 'altitude', 'date'), encoding='utf-8')

mapData = np.fromfile(MAP_FILE_PATH, dtype=np.int16)

mapData = mapData.reshape(MAP_SIZE_X, MAP_SIZE_Y)

#création de la map
structuredGrid = vtk.vtkStructuredGrid()
structuredGrid.SetDimensions([MAP_REDUCED_SIZE_Y, MAP_REDUCED_SIZE_X, 1])

points = vtk.vtkPoints()
points.Allocate(MAP_REDUCED_SIZE_X * MAP_REDUCED_SIZE_Y)


#prise en compte de l'altitude
scalars = vtk.vtkIntArray()
scalars.SetNumberOfComponents(1)

print(MIN_Y)
print(MIN_LONG)
print(MAX_Y)
print(MAX_LONG)
print(MIN_X)
print(MIN_LAT)
print(MAX_X)
print(MAX_LAT)



vectorUnityLonX = (xBG - xHG) / MAP_SIZE_Y
vectorUnityLonY = (yBD - yHD) / MAP_SIZE_Y

print(np.linspace(MIN_LONG, MAX_LONG, MAP_REDUCED_SIZE_X), range(MIN_Y, MAX_Y))


for lon, y in zip(np.linspace(MIN_LONG, MAX_LONG, MAP_REDUCED_SIZE_X), range(MIN_X, MAX_X)):
    for lat, x in zip(np.linspace(MIN_LAT, MAX_LAT, MAP_REDUCED_SIZE_Y), range(MIN_Y, MAX_Y)):
        if x == MIN_X and y == MIN_Y:
            print('min')
            print(lon)
            print(MIN_LONG)
            print(MIN_LAT)

        if x == MAX_X - 1 and y == MAX_Y - 1:
            print('max')
            print(lon)
            print(MAX_LONG)
            print(MAX_LAT)
        alt = EARTH_RADIUS + mapData[y][x]
        points.InsertNextPoint(
            alt,
            angleToRad(lat),
            angleToRad(lon)
        )
        scalars.InsertNextValue(mapData[y][x])
        
structuredGrid.SetPoints(points)
structuredGrid.GetPointData().SetScalars(scalars)

geometryFilter = vtk.vtkStructuredGridGeometryFilter()
geometryFilter.SetInputData(structuredGrid)


'''application d'une transformation convertissant les altitudes latitudes et longitudes
en coordonnées sur les axes orthogonaux'''

tf = vtk.vtkSphericalTransform()
transformFilter = vtk.vtkTransformPolyDataFilter()
transformFilter.SetTransform(tf)
transformFilter.SetInputConnection(geometryFilter.GetOutputPort())
transformFilter.Update()

# mapper sur lequel on met la lookup table pour la coloration
mapMapper = vtk.vtkPolyDataMapper()
mapMapper.SetInputConnection(transformFilter.GetOutputPort())
mapMapper.ScalarVisibilityOn()
mapMapper.SetScalarModeToUsePointData()
mapMapper.SetColorModeToMapScalars()

mapActor = vtk.vtkActor()
mapActor.SetMapper(mapMapper)

ren1 = vtk.vtkRenderer()
ren1.AddActor(mapActor)
ren1.SetBackground(0.1, 0.2, 0.4)

renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren1)
renWin.SetSize(800, 600)

renWin.Render()

# caméra posée au dessus du centre de la carte
cameraPosIn = [distanceFactor * EARTH_RADIUS, angleToRad(MEAN_LAT), angleToRad(MEAN_LONG)]
cameraPosOut = [0, 0, 0]
tf.TransformPoint(cameraPosIn, cameraPosOut)

camera = vtk.vtkCamera()
camera.SetPosition(cameraPosOut)
camera.SetFocalPoint(mapActor.GetCenter())
camera.Roll(-90)
ren1.SetActiveCamera(camera)
ren1.ResetCameraClippingRange()

renWin.Render()

iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

style = vtk.vtkInteractorStyleTrackballCamera()
iren.SetInteractorStyle(style)

iren.Initialize()
iren.Start()

