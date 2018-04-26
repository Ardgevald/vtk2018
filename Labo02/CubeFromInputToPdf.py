# Ce programme s'utilise avec en argument le nom du fichier qui contient les informations
# sur le cube, avec un cube par ligne, représenté par des nombres ordonnés de 1 à 7 séparés par des espaces
# Exemple :
#   3 3 1 3 2 2 2 2 1 .....
#
# Le second argument est facultatif et représente le nombre de cubes que l'on veut traiter
# Avec le fichier de résultats en entrée que j'ai reçu, je l'ai appelé comme suit :
# python CubeFromInputToPdf.py resultatForme.txt 1000
#
# Il y avait beaucoup trop de solutions pour faire le traitement en un temps raisonnable, alors
# j'ai pris les 1000 premiers cubes comme échantillon
#
# Nécessite fpdf pour fonctionner (pip install fpdf)

import vtk
import numpy as np
import sys
import os
from fpdf import FPDF
import datetime

cubeSize = 3

# couleurs des pièces utilisée
colors = [(1, 0.5, 0), (0, 0, 1), (0, 0.8, 0), (0, 1, 1), (1, 0, 0), (1, 0, 1), (1, 1, 0)]

# fonction utilisant un cube dans un tableau en trois dimensions représenté par ses pièces
# et un nom de fichier
def cubeSolutionToImage(input, filename):
  actors = []
  appendFilters = []
  renderers = []

  for i in range(7):
    appendFilters.append(vtk.vtkAppendPolyData())

  nbPieces = 0

  # on génère les cubes et on les ajoute aux polyData des pieces
  for i in range(cubeSize):
    for j in range(cubeSize):
      for k in range(cubeSize):
        cube = vtk.vtkCubeSource()
        cube.SetXLength(1.0)
        cube.SetYLength(1.0)
        cube.SetZLength(1.0)
        cube.SetCenter(i - 1, j - 1, k - 1)
        obj = appendFilters[input[i, j, k]]
        nbPieces = max(nbPieces, input[i, j, k] + 1)
        obj.AddInputConnection(cube.GetOutputPort())

  # cube outline
  cubeFrame = vtk.vtkCubeSource()
  cubeFrame.SetXLength(cubeSize + 0.1)
  cubeFrame.SetYLength(cubeSize + 0.1)
  cubeFrame.SetZLength(cubeSize + 0.1)
  cubeFrame.SetCenter(0, 0, 0)
  cubeFrameMapper = vtk.vtkPolyDataMapper()
  cubeFrameMapper.SetInputConnection(cubeFrame.GetOutputPort())
  outline = vtk.vtkOutlineFilter()
  outline.SetInputConnection(cubeFrame.GetOutputPort())
  mapper2 = vtk.vtkPolyDataMapper()
  mapper2.SetInputConnection(outline.GetOutputPort())
  cubeFrameActor = vtk.vtkActor()
  cubeFrameActor.SetMapper(mapper2)
  cubeFrameActor.GetProperty().SetColor((0, 0, 0))

  # camera
  camera = vtk.vtkCamera()
  camera.SetPosition(8, 8, 8)

  # lumiere directionnelle
  light = vtk.vtkLight()
  light.SetLightTypeToSceneLight()
  light.SetPosition(2, 5, 10)

  # 7 renderers, un pour chaque etape
  for i in range(7):
    renderer = vtk.vtkRenderer()
    renderer.SetActiveCamera(camera)
    renderer.SetBackground(1, 1, 1)

    renderer.AddLight(light)

    renderer.SetUseFXAA(True)
    renderers.append(renderer)

    cubeMapper = vtk.vtkPolyDataMapper()
    cubeMapper.SetInputConnection(appendFilters[i].GetOutputPort())
    cubeActor = vtk.vtkActor()
    cubeActor.SetMapper(cubeMapper)
    cubeActor.GetProperty().SetColor(colors[i])
    cubeActor.GetProperty().SetAmbient(0.4)
    actors.append(cubeActor)

    for a in actors:
      renderer.AddActor(a)

  # rendering offscreen car non nécessaire
  renWin = vtk.vtkRenderWindow()
  renWin.OffScreenRenderingOn()
  renWin.SetSize(600, 900)

  r = 4
  c = 2

  for i in reversed(range(r - 1)):
    for j in range(c):
      index = c * (r - i - 2) + j
      renderers[index].SetViewport(j/c, i/r, (j+1)/c, (i+1)/r)
      renderers[index].AddActor(cubeFrameActor)

  renderers[6].SetViewport(0, 0.75, 1, 1)

  for r in renderers:
    renWin.AddRenderer(r)

  renWin.Render()

  w2i = vtk.vtkWindowToImageFilter()
  w2i.SetInput(renWin)
  w2i.Update()

  writer = vtk.vtkPNGWriter()
  writer.SetFileName(filename)
  writer.SetInputConnection(w2i.GetOutputPort())
  writer.Write()

# obtention du fichier représentant les cubes ligne par ligne
if(len(sys.argv) < 2):
  print("Missing file name argument")
else:
  inputFileLines = list(open(sys.argv[1]))

  tempImageNameFormat = 'solution{}.png'
  pdf = FPDF()

  # obtention de la limite du nombre de cubes si présent
  if(len(sys.argv) < 3):
    maxNbValues = len(inputFileLines)
  else:
    maxNbValues = min(len(inputFileLines), int(sys.argv[2]))

  n = 0
  for cube in inputFileLines[:maxNbValues]:
    n += 1
    input = np.zeros((cubeSize, cubeSize, cubeSize), np.int8)
    cubeValues = cube.split(" ")

    for i in range(cubeSize):
      for j in range(cubeSize):
        for k in range(cubeSize):
          input[i][j][k] = int(cubeValues[i*cubeSize*cubeSize + k*cubeSize + j]) - 1

    tempImageName = tempImageNameFormat.format(n)

    cubeSolutionToImage(input, tempImageName)

    pdf.add_page()
    pdf.image(tempImageName, 0, 0)
    print(tempImageName + " is done")
    os.remove(tempImageName)

  outputFile = "solutions{}.pdf".format(datetime.datetime.now().strftime("%Y%m%d%H%M%S"))
  print("saving pdf file, can take some time...")
  pdf.output(outputFile, "F")

