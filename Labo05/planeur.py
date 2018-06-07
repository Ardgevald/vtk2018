import vtk
import numpy as np
import sys
from datetime import datetime
import pyproj
from math import pi, floor, ceil, sqrt

'''
Dans notre résultat, la carte et le glider ont une différence d'angle de 90°. Cela
provient certainement de la carte, car les coordonnées glider sont directement affichées
via leurs coordonnées. Nous n'avons pas réussi à tourner la carte avec ce que nous
avons fait.
De plus, la carte et le glider étaient écrasés sur une des dimensions (peut-être 
à cause du même souci de map), on a alors divisé par un facteur sur l'autre dimension
pour obtenir une carte plus agréable à regarder.
'''


# distance de la caméra en proportion du rayon de la terre
distanceFactor = 1.006

# adapte la carte pour un meilleur rendu
LON_ADAPT = 0.5

EARTH_RADIUS = 6371009

# chemin des fichiers à traiter
GLIDER_FILE_PATH = "vtkgps.txt"
MAP_FILE_PATH = "EarthEnv-DEM90_N60E010.bil"
TEXTURE_FILE_PATH = "glider_map.jpg"

# taille de la carte initiale
MAP_SIZE_X = 6000
MAP_SIZE_Y = 6000
MAP_SIZE_Z = 1

# convertisseur de coordonées selon la norme Suédoise vers la globale (longitude lattitude)
coordinateSwedish = pyproj.Proj(init='epsg:3021')
coordinateGlobal = pyproj.Proj(init='epsg:4326')

def sweToGlo(x, y):
    return pyproj.transform(coordinateSwedish, coordinateGlobal, x, y)


# coordonées des 4 coins (HG = Haut Gauche, BD = Bas Droite)
xHG, yHG = 1349340, 7022573
xHD, yHD = 1371573, 7022967
xBG, yBG = 1349602, 7005969
xBD, yBD = 1371835, 7006362

# Limites dans chaque direction dans les deux normes
MIN_LONG_SWE, MIN_LAT_SWE = min(xHG, xBG), max(yHD, yHG)
MAX_LONG_SWE, MAX_LAT_SWE = max(xHD, xBD), min(yBD, yBG)

MIN_LONG, MIN_LAT = sweToGlo(MIN_LONG_SWE, MIN_LAT_SWE)
MAX_LONG, MAX_LAT = sweToGlo(MAX_LONG_SWE, MAX_LAT_SWE)

# Limites en coordonnées x, y, entre 0 et 6000
MIN_X = floor((MIN_LONG - 10) * MAP_SIZE_X/5)
MAX_X = ceil((MAX_LONG - 10) * MAP_SIZE_X/5)
MIN_Y = floor((MIN_LAT - 65) * MAP_SIZE_Y/-5)
MAX_Y = ceil((MAX_LAT - 65) * MAP_SIZE_Y/-5)

# moyenne des longitudes et lattitudes pour la caméra
MEAN_LONG = np.mean([MIN_LONG, MAX_LONG])
MEAN_LAT = np.mean([MIN_LAT, MAX_LAT])

# nombre de points du sous-ensemble
MAP_REDUCED_SIZE_Y = MAX_Y - MIN_Y
MAP_REDUCED_SIZE_X = MAX_X - MIN_X

# transforme un angle en degrés vers des radians
def angleToRad(angle):
    return angle * pi / 180

# méthode de conversion reprise et adaptée en python et au problème
# https://www.particleincell.com/2012/quad-interpolation/
# converts physical (x,y) to logical (l,m)
def XtoL(x, y):

    # create our polygon
    px = [xHG, xHD, xBD, xBG]
    py = [yBD, yBG, yHG, yHD]

    # compute coefficients
    A = [[1, 0, 0, 0], [1, 1, 0, 0], [1, 1, 1, 1], [1, 0, 1, 0]]
    AI = np.linalg.inv(A)
    a = np.dot(AI, px)
    b = np.dot(AI, py)

    # quadratic equation coeffs, aa*mm^2+bb*m+cc=0
    aa = a[3]*b[2] - a[2]*b[3]
    bb = a[3]*b[0] - a[0]*b[3] + a[1]*b[2] - a[2]*b[1] + x*b[3] - y*a[3]
    cc = a[1]*b[0] - a[0]*b[1] + x*b[1] - y*a[1]

    # compute m = (-b+sqrt(b^2-4ac))/(2a)
    det = sqrt(bb*bb - 4*aa*cc)
    m = (-bb+det)/(2*aa)

    # compute l
    l = (x-a[0]-a[2]*m)/(a[1]+a[3]*m)
    return (l, 1 - m)

# récupèration des données du glider
gliderCoordinates = np.genfromtxt(GLIDER_FILE_PATH, dtype=[('x', 'i4'), ('y', 'i4'), ('alt', 'f4'), ('date', 'U30')], usecols=(
    1, 2, 3, 4, 5), skip_header=1, names=('x', 'y', 'altitude', 'date'), encoding='utf-8')

# récupération des données de la carte
mapData = np.fromfile(MAP_FILE_PATH, dtype=np.int16)

mapData = mapData.reshape(MAP_SIZE_X, MAP_SIZE_Y)

# création de la carte
structuredGrid = vtk.vtkStructuredGrid()
structuredGrid.SetDimensions([MAP_REDUCED_SIZE_Y, MAP_REDUCED_SIZE_X, 1])

points = vtk.vtkPoints()
points.Allocate(MAP_REDUCED_SIZE_Y * MAP_REDUCED_SIZE_X)

# valeurs pour l'application de la texture
scalars = vtk.vtkFloatArray()
scalars.SetNumberOfComponents(2)

# parcours des données et création des points
for lon, x in zip(np.linspace(MIN_LONG_SWE, MAX_LONG_SWE, MAP_REDUCED_SIZE_X), range(MIN_X, MAX_X)):
    for lat, y in zip(np.linspace(MIN_LAT_SWE, MAX_LAT_SWE, MAP_REDUCED_SIZE_Y)[::-1], range(MIN_Y, MAX_Y)):
        alt = EARTH_RADIUS + mapData[y][x]

        newLon, newLat = sweToGlo(lon, lat)

        points.InsertNextPoint(
            alt,
            angleToRad(newLat),
            angleToRad(newLon * LON_ADAPT)
        )

        scalars.InsertNextTuple(XtoL(lon, lat))

structuredGrid.SetPoints(points)
structuredGrid.GetPointData().SetTCoords(scalars)

geometryFilter = vtk.vtkStructuredGridGeometryFilter()
geometryFilter.SetInputData(structuredGrid)

# création des gliders
pointsGlider = vtk.vtkPoints()
pointsGlider.Allocate(len(gliderCoordinates))

speedArray = vtk.vtkFloatArray()
speedArray.SetNumberOfComponents(1)

# parcours des données pour générer les points avec vitesse verticale
first = True
previousDate = 0
previousAlt = 0
previousLon = 0
previousLat = 0
cpt = 0
for lon, lat, alt, date in gliderCoordinates:
    alt = EARTH_RADIUS + alt
    newLon, newLat = sweToGlo(lon, lat)
    newDate = datetime.strptime(date, '%m/%y/%d_%H:%M:%S')

    pointsGlider.InsertNextPoint(
        alt,
        angleToRad(newLat),
        angleToRad(newLon * LON_ADAPT)
    )

    if not first:
        time = (newDate - previousDate).total_seconds()
        speedArray.InsertNextValue(
            (alt - previousAlt)/time
        )
    else:
        speedArray.InsertNextValue(1)
        origin = [alt, angleToRad(newLat), angleToRad(newLon)]

    previousDate = newDate
    previousAlt = alt
    previousLon = lon
    previousLat = lat
    first = False
    cpt = cpt + 1

# polyline finale
polyLine = vtk.vtkPolyLine()
polyLine.GetPointIds().SetNumberOfIds(len(gliderCoordinates))
for i in range(len(gliderCoordinates)):
    polyLine.GetPointIds().SetId(i, i)

cells = vtk.vtkCellArray()
cells.InsertNextCell(polyLine)

# Création d'un polydata pour y ajouter la polyline, les points et les vitesses
polyData = vtk.vtkPolyData()
polyData.SetPoints(pointsGlider)
polyData.GetPointData().SetScalars(speedArray)
polyData.SetLines(cells)

# transformation d'altitude lattitude longitude en coordonnées x, y, z
tf = vtk.vtkSphericalTransform()
transformFilter = vtk.vtkTransformPolyDataFilter()
transformFilter.SetTransform(tf)
transformFilter.SetInputData(polyData)
transformFilter.Update()

# obtention des points pour en prendre un sous ensemble
# de manière à éviter les valeurs atypiques dans la
# lookuptable
array = []
for i in range(len(gliderCoordinates)):
    array.append(speedArray.GetValue(i))

array.sort()
minRange = array[floor(len(gliderCoordinates) * 0.1)]
maxRange = array[floor(len(gliderCoordinates) * 0.9)]

# table des couleurs
lookupColor = vtk.vtkLookupTable()
lookupColor.SetRange(minRange, maxRange)
lookupColor.SetNumberOfTableValues(4)
lookupColor.SetTableValue(0, [0.0, 0.0, 1.0, 1.0])
lookupColor.SetTableValue(1, [0.0, 0.7, 1.0, 1.0])
lookupColor.SetTableValue(2, [1.0, 0.7, 0.0, 1.0])
lookupColor.SetTableValue(3, [1.0, 0.0, 0.0, 1.0])
lookupColor.SetNanColor(0, 0, 0, 1)
lookupColor.Build()

# filtre pour afficher un tube au lieu de la polyline
tubeFilter = vtk.vtkTubeFilter()
tubeFilter.SetInputConnection(transformFilter.GetOutputPort())
tubeFilter.SetRadius(40)

# Mapper du polyline
polylineMapper = vtk.vtkPolyDataMapper()
polylineMapper.SetInputConnection(tubeFilter.GetOutputPort())
polylineMapper.ScalarVisibilityOn()
polylineMapper.SetLookupTable(lookupColor)
polylineMapper.SetScalarRange(minRange, maxRange)
polylineMapper.SetColorModeToMapScalars()

polylineActor = vtk.vtkActor()
polylineActor.SetMapper(polylineMapper)

'''application d'une transformation convertissant les altitudes latitudes et longitudes
en coordonnées sur les axes orthogonaux'''

transformFilter2 = vtk.vtkTransformPolyDataFilter()
transformFilter2.SetTransform(tf)
transformFilter2.SetInputConnection(geometryFilter.GetOutputPort())
transformFilter2.Update()

mapMapper = vtk.vtkPolyDataMapper()
mapMapper.SetInputConnection(transformFilter2.GetOutputPort())

# mapping des points pour la texture
mappedPoints = vtk.vtkJPEGReader()
mappedPoints.SetFileName(TEXTURE_FILE_PATH)
mappedPoints.Update()
imageData = mappedPoints.GetOutput()
imageX, imageY, imageZ = imageData.GetDimensions()

# masque transparent 
transparentMask = vtk.vtkImageData()
transparentMask.SetExtent(imageData.GetExtent())
transparentMask.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)

for x in range(imageX):
    for y in range(imageY):
        if x == 0 or y == 0 or x == imageX - 1 or y == imageY - 1:
            transparentMask.SetScalarComponentFromFloat(x, y, 0, 0, 0)
        else:
            transparentMask.SetScalarComponentFromFloat(x, y, 0, 0, 255)

appendComponent = vtk.vtkImageAppendComponents()
appendComponent.AddInputConnection(mappedPoints.GetOutputPort())
appendComponent.AddInputData(transparentMask)

# création de la texture
texture = vtk.vtkTexture()
texture.SetInputConnection(appendComponent.GetOutputPort())
texture.InterpolateOn()
texture.RepeatOff()

mapActor = vtk.vtkActor()
mapActor.SetMapper(mapMapper)
mapActor.SetTexture(texture)

# légende pour la lookupTable
scalarBar = vtk.vtkScalarBarActor()
scalarBar.SetLookupTable(lookupColor)
scalarBar.SetTitle("Vertical Speed")
scalarBar.SetLabelFormat("%4.0f")
scalarBar.SetVerticalTitleSeparation(30)

ren1 = vtk.vtkRenderer()
ren1.AddActor(mapActor)
ren1.AddActor(polylineActor)
ren1.AddActor(scalarBar)
ren1.SetBackground(0.1, 0.2, 0.4)
ren1.SetUseFXAA(True)

renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren1)
renWin.SetSize(800, 600)

renWin.Render()

# caméra posée au dessus du centre de la carte
cameraPosIn = [distanceFactor * EARTH_RADIUS,
               angleToRad(MEAN_LAT), angleToRad(MEAN_LONG * LON_ADAPT)]
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
