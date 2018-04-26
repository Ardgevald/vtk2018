import vtk
import numpy as np
import random
import os
import sys

videoFileName = "cube.avi"

input = [ [[3, 2, 2], [2, 2, 5], [5, 5, 5]], 
          [[3, 0, 4], [3, 0, 4], [3, 1, 4]],
          [[6, 0, 4], [6, 6, 6], [1, 1, 1]]]
colors = [(0, 0, 1), (0, 1, 0), (0, 1, 1), (1, 0, 0), (1, 0, 1), (1, 1, 0), (1, 1, 1)]

actorsOrder = [5, 2, 3, 0, 4, 6, 1]
actors = []

appendFilters = []
for i in range(7):
  appendFilters.append(vtk.vtkAppendPolyData())
  
for i in range(3):
  for j in range(3):
    for k in range(3):
      cube = vtk.vtkCubeSource()
      cube.SetXLength(1.0)
      cube.SetYLength(1.0)
      cube.SetZLength(1.0)
      cube.SetCenter(i, j, k)
      obj = appendFilters[input[i][j][k]]
      obj.AddInputConnection(cube.GetOutputPort())

ren1 = vtk.vtkRenderer()

for i in range(7):
  cubeMapper = vtk.vtkPolyDataMapper()
  cubeMapper.SetInputConnection(appendFilters[i].GetOutputPort())
  cubeActor = vtk.vtkActor()
  cubeActor.SetMapper(cubeMapper)
  cubeActor.GetProperty().SetColor(colors[i])
  actors.append(cubeActor)
  ren1.AddActor(cubeActor)

# caméra
camera = vtk.vtkCamera()
camera.SetPosition(10, 10, 15)
camera.SetFocalPoint(-2, 0, 0)

ren1.SetActiveCamera(camera)
ren1.SetBackground(0.1, 0.2, 0.4)

# fenêtre de rendu
renWin = vtk.vtkRenderWindow()
renWin.OffScreenRenderingOn()
renWin.AddRenderer(ren1)
renWin.SetSize(800, 600)

# filtre pour obtenir une image depuis le rendu
w2i = vtk.vtkWindowToImageFilter()
w2i.SetInput(renWin)

# writer pour générer une vidéo
writer = vtk.vtkAVIWriter()
writer.SetInputConnection(w2i.GetOutputPort())
writer.SetFileName(videoFileName)
writer.SetRate(140)
writer.Start()

renWin.Start()

renWin.Render()

print("beginning vidéo")
for index in actorsOrder:
  transform = vtk.vtkTransform()
  for i in range(200):
    #Export a single frame
    renWin.Render()
    w2i.Modified()
    writer.Write()

    transform.Translate(-0.02, 0, 0)
    actors[index].SetUserMatrix(transform.GetMatrix())
    

#Finish movie
print("\nEnd of video")
writer.End()
