import vtk
import numpy as np
import sys
from dateutil import parser
import pyproj
from math import pi, floor, ceil, sqrt

# distance de la caméra en proportion du rayon de la terre
distanceFactor = 1.015

EARTH_RADIUS = 6371009

GLIDER_FILE_PATH = "vtkgps.txt"
MAP_FILE_PATH = "EarthEnv-DEM90_N60E010.bil"
TEXTURE_FILE_PATH = "glider_map.jpg"

MAP_SIZE_X = 6000
MAP_SIZE_Y = 6000
MAP_SIZE_Z = 1

#how to convert
coordinateSwedish = pyproj.Proj(init='epsg:3021')
coordinateGlobal = pyproj.Proj(init='epsg:4326')
def sweToGlo(x, y):
    return pyproj.transform(coordinateSwedish,coordinateGlobal, x, y)
## coordonées des 4 coins (HG = Haut Gauche, BD = Bas Droite)
xHG, yHG = 1349340, 7022573
xHD, yHD = 1371573, 7022967
xBG, yBG = 1349602, 7005969
xBD, yBD = 1371835, 7006362

MIN_LONG, MIN_LAT = sweToGlo(min(xHG, xBG), max(yHD, yHG))
MAX_LONG, MAX_LAT = sweToGlo(max(xHD, xBD), min(yBD, yBG))

MIN_Y = floor((MIN_LONG - 10) * MAP_SIZE_X/5)
MAX_Y = ceil((MAX_LONG - 10) * MAP_SIZE_X/5)
MIN_X = floor((MIN_LAT - 65) * MAP_SIZE_Y/-5)
MAX_X = ceil((MAX_LAT - 65) * MAP_SIZE_Y/-5)

MEAN_LONG = np.mean([MIN_LONG, MAX_LONG])
MEAN_LAT = np.mean([MIN_LAT, MAX_LAT])

MAP_REDUCED_SIZE_X = MAX_X - MIN_X
MAP_REDUCED_SIZE_Y = MAX_Y - MIN_Y

# transforme un angle en degrés vers des radians
def angleToRad(angle):
    return angle * pi / 180

# converts physical (x,y) to logical (l,m)
def XtoL(x,y):

    xbg, ybg = sweToGlo(xBG, yBG)
    xbd, ybd = sweToGlo(xBD, yBD)
    xhd, yhd = sweToGlo(xHD, yHD)
    xhg, yhg = sweToGlo(xHG, yHG)

    #create our polygon
    px = [xbg, xbd, xhd, xhg]
    py = [ybg, ybd, yhd, yhg]
    
    #compute coefficients
    A = [[1, 0, 0, 0], [1, 1, 0, 0], [1, 1, 1, 1],[1, 0, 1, 0]]
    AI = np.linalg.inv(A)
    a = np.dot(AI, px)
    b = np.dot(AI, py)

    #quadratic equation coeffs, aa*mm^2+bb*m+cc=0
    aa = a[3]*b[2] - a[2]*b[3]
    bb = a[3]*b[0] -a[0]*b[3] + a[1]*b[2] - a[2]*b[1] + x*b[3] - y*a[3]
    cc = a[1]*b[0] -a[0]*b[1] + x*b[1] - y*a[1]
 
    #compute m = (-b+sqrt(b^2-4ac))/(2a)
    det = sqrt(bb*bb - 4*aa*cc)
    m = (-bb+det)/(2*aa)
 
    #compute l
    l = (x-a[0]-a[2]*m)/(a[1]+a[3]*m)
    return (l, 1 - m)

gliderCoordinates = np.genfromtxt(GLIDER_FILE_PATH, dtype=[('x', 'i4'),('y', 'i4'), ('alt', 'f4'), ('date', 'U30')], usecols=(1, 2, 3, 4, 5), skip_header=1, names=('x', 'y', 'altitude', 'date'), encoding='utf-8')

mapData = np.fromfile(MAP_FILE_PATH, dtype=np.int16)

mapData = mapData.reshape(MAP_SIZE_X, MAP_SIZE_Y)

#création de la map
structuredGrid = vtk.vtkStructuredGrid()
structuredGrid.SetDimensions([MAP_REDUCED_SIZE_Y, MAP_REDUCED_SIZE_X, 1])

points = vtk.vtkPoints()
points.Allocate(MAP_REDUCED_SIZE_X * MAP_REDUCED_SIZE_Y)


colorsArray = vtk.vtkLookupTable()
colorsArray.SetRange(0, 1)
colorsArray.SetNumberOfTableValues(2)
colorsArray.SetTableValue(0, 1.0, 1.0, 1.0, 1.0)
colorsArray.SetTableValue(1, 0.0, 0.0, 0.0, 0.0)
colorsArray.Build()

#prise en compte de l'altitude
scalars = vtk.vtkFloatArray()
scalars.SetNumberOfComponents(2)

scalarsColor = vtk.vtkIntArray()
scalarsColor.SetNumberOfComponents(1)

for lat, y in zip(np.linspace(MIN_LAT, MAX_LAT, MAP_REDUCED_SIZE_X)[::-1], range(MIN_X, MAX_X)):
    for lon, x in zip(np.linspace(MIN_LONG, MAX_LONG, MAP_REDUCED_SIZE_Y), range(MIN_Y, MAX_Y)):
        alt = EARTH_RADIUS + mapData[y][x]
        points.InsertNextPoint(
            alt,
            angleToRad(lat),
            angleToRad(lon * 0.5)
        )
        
        scalars.InsertNextTuple(XtoL(lon, lat))
        xL, yL = XtoL(lon, lat)
        if(xL < 0 or xL > 1 or yL < 0 or yL > 1):
            scalarsColor.InsertNextValue(1)
        else:
            scalarsColor.InsertNextValue(0)
        
structuredGrid.SetPoints(points)
structuredGrid.GetPointData().SetTCoords(scalars)
structuredGrid.GetPointData().SetScalars(scalarsColor)

geometryFilter = vtk.vtkStructuredGridGeometryFilter()
geometryFilter.SetInputData(structuredGrid)


'''application d'une transformation convertissant les altitudes latitudes et longitudes
en coordonnées sur les axes orthogonaux'''

tf = vtk.vtkSphericalTransform()
transformFilter = vtk.vtkTransformPolyDataFilter()
transformFilter.SetTransform(tf)
transformFilter.SetInputConnection(geometryFilter.GetOutputPort())
transformFilter.Update()

mapMapper = vtk.vtkPolyDataMapper()
mapMapper.SetInputConnection(transformFilter.GetOutputPort())
mapMapper.ScalarVisibilityOn()
mapMapper.SetScalarModeToUsePointData()
mapMapper.SetColorModeToMapScalars()
mapMapper.SetLookupTable(colorsArray)

#mapping des points pour la texture
mappedPoints = vtk.vtkJPEGReader()
mappedPoints.SetFileName(TEXTURE_FILE_PATH)

#création de la texture
texture = vtk.vtkTexture()
texture.SetInputConnection(mappedPoints.GetOutputPort())
texture.InterpolateOn()
texture.RepeatOff()
texture.EdgeClampOn()

mapActor = vtk.vtkActor()
mapActor.SetMapper(mapMapper)
mapActor.SetTexture(texture)

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
camera.Roll(-90)
camera.SetFocalPoint(mapActor.GetCenter())
ren1.SetActiveCamera(camera)
ren1.ResetCameraClippingRange()

renWin.Render()

iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

style = vtk.vtkInteractorStyleTrackballCamera()
iren.SetInteractorStyle(style)

iren.Initialize()
iren.Start()

