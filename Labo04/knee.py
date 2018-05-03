# coding: utf-8

import vtk

def newRenderer(actors):
    renderer = vtk.vtkRenderer()
    for actor in actors:
        renderer.AddActor(actor)
    renderer.SetBackground(1, 1, 1)
    #renderer.ResetCamera()
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
boneSurface.Update()

# utulise le volume pour en faire une isosurface pour la peau
skinSurface = vtk.vtkMarchingCubes()
skinSurface.SetInputData(imageData)
skinSurface.SetValue(5, 20)
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
boneActor.GetProperty().SetColor(250, 0, 0)
boneActor.GetProperty().SetAmbient(0.4)

skinActor = vtk.vtkActor()
skinActor.SetMapper(skinMapper)
skinActor.GetProperty().SetPointSize(3)
skinActor.GetProperty().SetColor(0.5, 0, 0)
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

# mise en place des rendus et des acteurs
ringRenderer = newRenderer({skinActor, boneActor, actorGrillage})
transparentRenderer = newRenderer({skinActor, boneActor, actorGrillage})
normalRenderernderer = newRenderer({skinActor, boneActor, actorGrillage})
proximityRenderer = newRenderer({skinActor, boneActor, actorGrillage})

# découpe la fenêtre pour placer les différents rendus
ringRenderer.SetViewport(0.0, 0.5, 0.5, 1.0)
transparentRenderer.SetViewport(0.5, 0.5, 1.0, 1.0)
normalRenderernderer.SetViewport(0.0, 0.0, 0.5, 0.5)
proximityRenderer.SetViewport(0.5, 0.0, 1.0, 0.5)

# création de la fenêtre d'affichage
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(ringRenderer)
renderWindow.AddRenderer(transparentRenderer)
renderWindow.AddRenderer(normalRenderernderer)
renderWindow.AddRenderer(proximityRenderer)

# paramètre l'interaction avec la fenêtre
renderWindowInteractor = vtk.vtkRenderWindowInteractor()

# lancement de l'affichage
renderWindowInteractor.SetRenderWindow(renderWindow)
renderWindowInteractor.Initialize()
renderWindowInteractor.Start()
