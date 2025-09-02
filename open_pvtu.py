from paraview.simple import *
import glob
from os.path import abspath

files = [abspath(p) for p in glob.glob(r"vis_out\job_vis_psf.*.pvtu")]

vis_render = XMLPartitionedUnstructuredGridReader(registrationName='job_result', FileName=files)
renderView = GetActiveViewOrCreate('RenderView')
Show(vis_render, renderView, 'UnstructuredGridRepresentation'); Hide(vis_render, renderView)

time = AnnotateGlobalData(registrationName='time display', Input=vis_render)
time.SelectArrays = 'TOTALTIME'
time.Prefix = 'TIME: '
time.Format = '%7.5g'
time.Suffix = '[s]'
timeDisplay = Show(time, renderView, 'TextSourceRepresentation')
timeDisplay.FontSize = 32
timeDisplay.Color = [1.0, 1.0, 1.0]

ex_sol = Threshold(registrationName='ExtractSOLID', Input=vis_render)

ex_sol.Scalars = ['CELLS', 'Mesh_Type']
ex_sol.LowerThreshold = 341.0; ex_sol.UpperThreshold = 362.0

convertMB = ProgrammableFilter(registrationName='ConvertMultiBlock', Input=ex_sol)

convertMB.OutputDataSetType = 'vtkMultiblockDataSet'
convertMB.Script = """from paraview.vtk.util.numpy_support import vtk_to_numpy
import vtk
import numpy as np
from os.path import isfile

input0 = inputs[0].VTKObject

material_array = input0.GetCellData().GetArray("MATERIAL_ID")
if material_array is None:
  raise RuntimeError("MATELIAL_ID is NOT FOUND")

material_ids = vtk_to_numpy(material_array)
unique_ids = np.unique(material_ids)

if isfile(\'parts.txt\'):
  f = open(\'parts.txt\'); parts = f.read().split(\',\'); f.close()
  if not len(parts) == len(unique_ids): names = range(len(unique_ids))
  else: names = parts
else: names = range(len(unique_ids))

for i, mid in enumerate(unique_ids):
  cell_ids = np.where(material_ids == mid)[0]

  id_list = vtk.vtkIdList()
  for cid in cell_ids:
    id_list.InsertNextId(int(cid))

  extractor = vtk.vtkExtractCells()
  extractor.SetInputData(input0)
  extractor.SetCellList(id_list)
  extractor.Update()

  block_data = extractor.GetOutput()

  output.SetBlock(i, block_data)
  output.GetMetaData(i).Set(vtk.vtkCompositeDataSet.NAME(), f"{names[i]}")

fd = input0.GetFieldData()
if fd and fd.GetArray("TOTALTIME"):
  output.GetInformation().Set(vtk.vtkDataObject.DATA_TIME_STEP(), fd.GetArray("TOTALTIME").GetValue(0))
"""
convertMB.CopyArrays = 1
Show(convertMB, renderView, 'UnstructuredGridRepresentation'); Hide(convertMB, renderView)

warpByVector = WarpByVector(registrationName='job_deformed', Input=convertMB)
warpByVector.Vectors = ['POINTS', 'DISPLACEMENT']
warpByVector.ScaleFactor = 1.0
def_Display = Show(warpByVector, renderView, 'UnstructuredGridRepresentation')
renderView.Update()

renderView.Update()

animationScene = GetAnimationScene()
animationScene.UpdateAnimationUsingDataTimeSteps()
animationScene.GoToLast()

ColorBy(def_Display, ('POINTS', 'NodalMISES'))
def_Display.SetScalarBarVisibility(renderView, True)
renderView.Update()

Render()