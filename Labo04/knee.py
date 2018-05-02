import vtk

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

skinActor = vtk.vtkActor()
skinActor.SetMapper(skinMapper)
skinActor.GetProperty().SetPointSize(3)

# mise en place du rendu et des acteurs
ringRenderer = newRenderer({skinActor, boneActor})
transparentRenderer = newRenderer({skinActor, boneActor})
normalRenderernderer = newRenderer({skinActor, boneActor})
proximityRenderer = newRenderer({skinActor, boneActor})

# création de la fenêtre de rendu
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(ringRenderer)
renderWindow.AddRenderer(transparentRenderer)
renderWindow.AddRenderer(normalRenderernderer)
renderWindow.AddRenderer(proximityRenderer)

# découpe la fenêtre pour placer les différents rendus
ringRenderer.SetViewport(0.0, 0.5, 0.5, 1.0)
transparentRenderer.SetViewport(0.5, 0.5, 1.0, 1.0)
normalRenderernderer.SetViewport(0.0, 0.0, 0.5, 0.5)
proximityRenderer.SetViewport(0.5, 0.0, 1.0, 0.5)

# paramètre l'interaction avec la fenêtre
renderWindowInteractor = vtk.vtkRenderWindowInteractor()

# lancement de l'affichage
renderWindowInteractor.SetRenderWindow(renderWindow)
renderWindowInteractor.Initialize()
renderWindowInteractor.Start()
