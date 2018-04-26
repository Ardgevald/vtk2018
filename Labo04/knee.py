import vtk
reader = vtk.vtkSLCReader()
reader.SetFileName("vw_knee.slc")
reader.Update()

imageData = reader.GetOutput()

surface = vtk.vtkMarchingCubes()
surface.SetInputData(imageData)
# surface.SetValue(40, 80)
surface.SetValue(5, 20)
surface.Update()

'''
resample = vtk.vtkImageResample()
resample.SetInputData(skinSurface.GetOutput())
resample.SetDimensionality(3)
resample.SetMagnificationFactors(0.5, 0.5, 0.5)
'''

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(surface.GetOutputPort())

actor = vtk.vtkActor()
actor.SetMapper(mapper)
actor.GetProperty().SetPointSize(3)

# Setup rendering
renderer = vtk.vtkRenderer()
renderer.AddActor(actor)
renderer.SetBackground(1, 1, 1)
renderer.ResetCamera()

renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)

renderWindowInteractor = vtk.vtkRenderWindowInteractor()

renderWindowInteractor.SetRenderWindow(renderWindow)
renderWindowInteractor.Initialize()
renderWindowInteractor.Start()
