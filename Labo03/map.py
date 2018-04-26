import vtk
import sys
import numpy as np
from math import pi

# distance de la caméra en proportion du rayon de la terre
distanceFactor = 1.085

# permet de changer entre une représentation discrète
# des couleurs
DISCRETE = False

# si le niveau de la mer atteint la hauteur indiquée
OVERFLOW = False
OVERFLOW_HEIGHT = 270

EARTH_RADIUS = 6371009

# longitudes et latitudes min et max de l'extrait de la carte
MIN_LONG = 5.0
MAX_LONG = 7.5
MIN_LAT = 45.0
MAX_LAT = 47.5

MEAN_LONG = np.mean([MIN_LONG, MAX_LONG])
MEAN_LAT = np.mean([MIN_LAT, MAX_LAT])


# transforme un angle en degrés vers des radians
def angleToRad(angle):
    return angle * pi / 180


# on récupère le nom du fichier à traiter
if len(sys.argv) < 2:
    print("Missing argument : data filename")
    sys.exit()

# on récupère les altitudes (la première ligne est ignorée)
arrayAltitudes = np.loadtxt(sys.argv[1], dtype=int, skiprows=1, ndmin=2)
maxAltitude = np.amax(arrayAltitudes)
minAltitude = np.amin(arrayAltitudes)
xSize, ySize = arrayAltitudes.shape
zSize = 1

'''
On utilise une structuredGrid pour représenter nos données
car elle nous permet de représenter nos données spacialement selon un plan
dont la topologie est bien définie (nombre de points en largeur et en longueur)

Elle nous permet de mettre les points à des hauteurs variable, mais il y a
un seul point pour des coordonées x et y. La topologie est simplement définie
par les dimensions
'''
structuredGrid = vtk.vtkStructuredGrid()
structuredGrid.SetDimensions([xSize, ySize, zSize])

'''
Les couleurs ont été choisies pour afficher du vert
en plaine tirant sur le blanc en passant par le jaune
'''
colorsArray = vtk.vtkLookupTable()
colorsArray.SetRange(minAltitude, maxAltitude)
colorsArray.SetValueRange(0.4, 1)
colorsArray.SetHueRange(0.3, 0)
colorsArray.SetSaturationRange(0.8, 0)
colorsArray.SetNanColor(1, 1, 1, 1)
colorsArray.SetScaleToLog10()
colorsArray.SetBelowRangeColor(0, 0, 1, 1)
colorsArray.SetUseBelowRangeColor(True)
if DISCRETE:
    colorsArray.SetNumberOfTableValues(7)
colorsArray.Build()

# liste des points de la structuredGrid
points = vtk.vtkPoints()
points.Allocate(xSize * ySize)

# Scalars pour garder les altitudes tel quel en tant qu'attribut pour la coloration
scalars = vtk.vtkIntArray()
scalars.SetNumberOfComponents(1)

# les points ont comme coordonnées de départ, l'altitude, longitude et latitude
for lon, y in zip(np.arange(MIN_LONG, MAX_LONG, (MAX_LONG - MIN_LONG) / xSize), range(ySize)):
    for lat, x in zip(np.arange(MIN_LAT, MAX_LAT, (MAX_LAT - MIN_LAT) / ySize), range(xSize)):

        if OVERFLOW:
            arrayAltitudes[y][x] = max(arrayAltitudes[y][x], OVERFLOW_HEIGHT)

        alt = EARTH_RADIUS + arrayAltitudes[y][x]

        points.InsertNextPoint(
            alt,
            angleToRad(lat),
            angleToRad(lon)
        )

LIMIT_FLAT = 5  # nombre de points adjacents pour considérer que c'est plat

precedentValues = arrayAltitudes[0][:LIMIT_FLAT]  # moins que 5 on commence a avoir trop de plats détéctés
y = 0
similars = False
lastValue = 0
counter = LIMIT_FLAT

vtk.vtkSpheri

# parcours la liste des points pour vérifier si c'est plat
for y in range(len(precedentValues), xSize * ySize):
    currentValue = arrayAltitudes[y % xSize][y // xSize]
    if not similars:
        similars = True
        # on considère plat si les len(precedentValues) précédentes valeurs sont identiques
        for x in precedentValues:
            if x != currentValue:
                similars = False
                break
        # une valeur ancienne peut définitivement être coloriée
        if counter >= len(precedentValues) and not similars:
            scalars.InsertNextValue(arrayAltitudes[y % xSize][y // xSize])
        # on a trouvé une ligne plate on colorie les ancienne valeur
        elif similars:
            counter = 0
            for x in range(len(precedentValues)):
                scalars.InsertNextValue(arrayAltitudes[(y - x) % xSize][(y - x) // xSize])
        counter += 1
    # on a trouvé une ligne suffisement longue pour considérer ça comme plat
    else:
        # on colorie en bleu tant qu'on trouve des valeurs identiques
        if lastValue == currentValue:
            scalars.InsertNextValue(1)
        # fin de la ligne plate on arrête de colorier en bleu
        else:
            similars = False
            scalars.InsertNextValue(arrayAltitudes[y % xSize][y // xSize])
    lastValue = currentValue
    precedentValues[y % len(precedentValues)] = currentValue

structuredGrid.SetPoints(points)
structuredGrid.GetPointData().SetScalars(scalars)

geometryFilter = vtk.vtkStructuredGridGeometryFilter()
geometryFilter.SetInputData(structuredGrid)

'''
application d'une transformation convertissant les altitudes latitudes et longitudes
en coordonnées sur les axes orthogonaux
'''
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
mapMapper.SetLookupTable(colorsArray)
mapMapper.SetScalarRange(OVERFLOW_HEIGHT if OVERFLOW else minAltitude, maxAltitude)

mapActor = vtk.vtkActor()
mapActor.SetMapper(mapMapper)

# légende pour la lookupTable
scalarBar = vtk.vtkScalarBarActor()
scalarBar.SetLookupTable(colorsArray)
scalarBar.SetTitle("Altitudes")
scalarBar.SetLabelFormat("%4.0f")
scalarBar.SetNumberOfLabels(8)
scalarBar.SetDrawBelowRangeSwatch(True)
scalarBar.SetVerticalTitleSeparation(30)
scalarBar.SetBelowRangeAnnotation("Water")

ren1 = vtk.vtkRenderer()
ren1.AddActor(mapActor)
ren1.AddActor2D(scalarBar)
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

# obtention de l'image

overflowText = "WithOverflow" if OVERFLOW else ""
tableTypeText = "Discrete" if DISCRETE else "Continuous"
filename = "{0}{1}.png".format(overflowText, tableTypeText)

w2i = vtk.vtkWindowToImageFilter()
w2i.SetInput(renWin)
w2i.Update()

writer = vtk.vtkPNGWriter()
writer.SetFileName(filename)
writer.SetInputConnection(w2i.GetOutputPort())
writer.Write()

iren = vtk.vtkRenderWindowInteractor()
iren.SetRenderWindow(renWin)

style = vtk.vtkInteractorStyleTrackballCamera()
iren.SetInteractorStyle(style)

iren.Initialize()
iren.Start()
