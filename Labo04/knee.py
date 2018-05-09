# coding: utf-8

import vtk
from math import pi
import os.path

KNEE_COLOR_FILE = "colorationBone.vtk"

WRITE_FILE = False

def newRenderer(actors):
    renderer = vtk.vtkRenderer()
    for actor in actors:
        renderer.AddActor(actor)
    renderer.SetBackground(1, 1, 1)
    renderer.ResetCamera()
    return renderer

# on lit les données depuis le fichier pour créer un ensemble structuré de points (volume)
reader = vtk.vtkSLCReader()
reader.SetFileName("vw_knee.slc")
reader.Update()

imageData = reader.GetOutput()

# utulise le volume pour en faire une isosurface pour l'os
boneSurface = vtk.vtkMarchingCubes()
boneSurface.SetInputData(imageData)
boneSurface.SetValue(40, 80)
boneSurface.ComputeScalarsOff()
boneSurface.Update()

# utulise le volume pour en faire une isosurface pour la peau
skinSurface = vtk.vtkMarchingCubes()
skinSurface.SetInputData(imageData)
skinSurface.SetValue(4, 21)
skinSurface.ComputeScalarsOff()
skinSurface.Update()

'''
resample = vtk.vtkImageResample()
resample.SetInputData(skinSurface.GetOutput())
resample.SetDimensionality(3)
resample.SetMagnificationFactors(0.5, 0.5, 0.5)
'''

# création des mappers
boneMapper = vtk.vtkPolyDataMapper()
boneMapper.SetInputConnection(boneSurface.GetOutputPort())

skinMapper = vtk.vtkPolyDataMapper()
skinMapper.SetInputConnection(skinSurface.GetOutputPort())

# création des acteurs
boneActor = vtk.vtkActor()
boneActor.SetMapper(boneMapper)
boneActor.GetProperty().SetPointSize(3)
boneActor.GetProperty().SetColor(0.9, 0.9, 0.9)
boneActor.GetProperty().SetAmbient(0.4)

skinActor = vtk.vtkActor()
skinActor.SetMapper(skinMapper)
skinActor.GetProperty().SetPointSize(3)
skinActor.GetProperty().SetColor(0.8, 0.3, 0.3)
skinActor.GetProperty().SetAmbient(0.4)

# calcul de la taille du cube en fonction des limites de la peau
bounds = skinMapper.GetBounds()
xLength = bounds[1] - bounds[0]
yLength = bounds[3] - bounds[2]
zLength = bounds[5] - bounds[4]
xCenter = (xLength / 2) + bounds[0]
yCenter = (yLength / 2) + bounds[2]
zCenter = (zLength / 2) + bounds[4]

# création du cube qui fait office de grillage
grillage = vtk.vtkCubeSource()

grillage.SetXLength(xLength)
grillage.SetYLength(yLength)
grillage.SetZLength(zLength)
grillage.SetCenter(xCenter, yCenter, zCenter)

grillageFilter = vtk.vtkOutlineFilter()
grillageFilter.SetInputConnection(grillage.GetOutputPort())

mapperGrillage = vtk.vtkPolyDataMapper()
mapperGrillage.SetInputConnection(grillageFilter.GetOutputPort())

actorGrillage = vtk.vtkActor()
actorGrillage.SetMapper(mapperGrillage)
actorGrillage.GetProperty().SetColor(0,0,0)

# création des anneaux
NUMBER_OF_RING = 19
WIDTH_OF_RING = 1

plane = vtk.vtkPlane()
plane.SetOrigin(0, 0, 0)
plane.SetNormal(0, 0, 1)

cutter = vtk.vtkCutter()
cutter.SetCutFunction(plane)
cutter.SetInputConnection(skinSurface.GetOutputPort())
cutter.GenerateValues(NUMBER_OF_RING, [0, zLength])
cutter.Update()

stripper = vtk.vtkStripper()
stripper.SetInputConnection(cutter.GetOutputPort())

tubeFilter = vtk.vtkTubeFilter()
tubeFilter.SetInputConnection(stripper.GetOutputPort())
tubeFilter.SetRadius(WIDTH_OF_RING)

cutterMapper = vtk.vtkPolyDataMapper()
cutterMapper.SetInputConnection(tubeFilter.GetOutputPort())

planeActor = vtk.vtkActor()
planeActor.GetProperty().SetColor(0.8, 0.3, 0.3)
planeActor.GetProperty().SetLineWidth(WIDTH_OF_RING)
planeActor.SetMapper(cutterMapper)

# création de la sphère sous forme d'acteur
sphereSource = vtk.vtkSphereSource()
sphereSource.SetRadius(50)
sphereSource.SetCenter(xCenter, yCenter - 60, zCenter)

mapperSphere = vtk.vtkPolyDataMapper()
mapperSphere.SetInputConnection(sphereSource.GetOutputPort())

actorSphere = vtk.vtkActor()
actorSphere.SetMapper(mapperSphere)
actorSphere.GetProperty().SetOpacity(0.1)

# clipping de la peau par une sphère
sphere = vtk.vtkSphere()
sphere.SetRadius(50)
sphere.SetCenter(xCenter, yCenter - 60, zCenter)

clip = vtk.vtkClipPolyData()
clip.SetInputConnection(skinSurface.GetOutputPort())
clip.SetClipFunction(sphere)
clip.InsideOutOff()
clip.GenerateClippedOutputOn()

clipMapper = vtk.vtkPolyDataMapper()
clipMapper.SetInputConnection(clip.GetOutputPort())
clipMapper.ScalarVisibilityOff()

clippedSkinActor = vtk.vtkActor()
clippedSkinActor.SetMapper(clipMapper)
clippedSkinActor.GetProperty().SetColor(0.8, 0.3, 0.3)

# ajout de la transparence sur la peau clippée (uniquement à l'avant)
frontProp = vtk.vtkProperty()
frontProp.SetOpacity(0.4)
frontProp.SetColor(0.3, 0.8, 0.3)
frontProp.BackfaceCullingOff()
frontProp.FrontfaceCullingOff()

backProp = vtk.vtkProperty()
backProp.SetOpacity(0.99)
backProp.SetColor(0.3, 0.3, 0.8)
backProp.BackfaceCullingOn()
backProp.FrontfaceCullingOn()

clipTransparentMapper = vtk.vtkPolyDataMapper()
clipTransparentMapper.SetInputConnection(clip.GetOutputPort())
clipTransparentMapper.ScalarVisibilityOff()

clippedTransparentSkinActor = vtk.vtkActor()
clippedTransparentSkinActor.SetMapper(clipTransparentMapper)
clippedTransparentSkinActor.SetProperty(frontProp)
clippedTransparentSkinActor.SetBackfaceProperty(backProp)

# coloration de l'os selon la distance à la peau
if os.path.isfile(KNEE_COLOR_FILE) or not(WRITE_FILE):
    vtkReader = vtk.vtkPolyDataReader()
    vtkReader = reader.SetFileName(KNEE_COLOR_FILE)
    boneFilter = reader
else: 
    boneFilter = vtk.vtkDistancePolyDataFilter()
    boneFilter.SetInputConnection(0, boneSurface.GetOutputPort())
    boneFilter.SetInputConnection(1, skinSurface.GetOutputPort())
    boneFilter.Update()
    

vtkWriter = vtk.vtkPolyDataWriter()
vtkWriter.SetInputConnection(boneFilter.GetOutputPort())
vtkWriter.SetFileName(KNEE_COLOR_FILE)
vtkWriter.Write()

distanceMapper = vtk.vtkPolyDataMapper()
distanceMapper.SetInputConnection(boneFilter.GetOutputPort() )
distanceMapper.SetScalarRange(boneFilter.GetOutput().GetPointData().GetScalars().GetRange()[0], boneFilter.GetOutput().GetPointData().GetScalars().GetRange()[1])

coloredBoneActor = vtk.vtkActor()
coloredBoneActor.SetMapper(distanceMapper)

# mise en place des rendus et des acteurs
ringRenderer = newRenderer({planeActor, boneActor, actorGrillage})
transparentRenderer = newRenderer({clippedTransparentSkinActor, boneActor, actorGrillage, actorSphere})
normalRenderernderer = newRenderer({clippedSkinActor, boneActor, actorGrillage, actorSphere})
#proximityRenderer = newRenderer({coloredBoneActor, actorGrillage})
proximityRenderer = vtk.vtkRenderer()
# découpe la fenêtre pour placer les différents rendus
ringRenderer.SetViewport(0.0, 0.5, 0.5, 1.0)
transparentRenderer.SetViewport(0.5, 0.5, 1.0, 1.0)
normalRenderernderer.SetViewport(0.0, 0.0, 0.5, 0.5)
proximityRenderer.SetViewport(0.5, 0.0, 1.0, 0.5)

# same camera for each renderer for sync
camera = vtk.vtkCamera()
camera.SetPosition(xCenter + xLength * 0.01, yCenter - yLength * 3, zCenter)
camera.SetFocalPoint(xCenter, yCenter, zCenter)
camera.Roll(90)
ringRenderer.SetActiveCamera(camera)
transparentRenderer.SetActiveCamera(camera)
normalRenderernderer.SetActiveCamera(camera)
proximityRenderer.SetActiveCamera(camera)

# création de la fenêtre d'affichage
renderWindow = vtk.vtkRenderWindow()
renderWindow.SetSize(800, 600)
renderWindow.AddRenderer(ringRenderer)
renderWindow.AddRenderer(transparentRenderer)
renderWindow.AddRenderer(normalRenderernderer)
renderWindow.AddRenderer(proximityRenderer)

# paramètre l'interaction avec la fenêtre
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetLightFollowCamera(True)

# lancement de l'affichage
renderWindowInteractor.SetRenderWindow(renderWindow)
renderWindowInteractor.Initialize()
renderWindowInteractor.Start()
