from paraview.simple import *
import glob
from os.path import abspath

files = [abspath(p) for p in glob.glob(r"vis_out\job_vis_psf.*.pvtu")]

vis_render = XMLPartitionedUnstructuredGridReader(registrationName='job_result', FileName=files)
renderView = GetActiveViewOrCreate('RenderView')
res_Display = Show(vis_render, renderView, 'UnstructuredGridRepresentation')

warpByVector = WarpByVector(registrationName='job_deformed', Input=vis_render)
warpByVector.Vectors = ['POINTS', 'DISPLACEMENT']
warpByVector.ScaleFactor = 1.0
def_Display = Show(warpByVector, renderView, 'UnstructuredGridRepresentation')
renderView.Update()

Hide(vis_render, renderView)
renderView.Update()

animationScene = GetAnimationScene()
animationScene.UpdateAnimationUsingDataTimeSteps()
animationScene.GoToLast()

ColorBy(def_Display, ('POINTS', 'NodalMISES'))
def_Display.SetScalarBarVisibility(renderView, True)
renderView.Update()

time = AnnotateGlobalData(registrationName='time display', Input=vis_render)
time.SelectArrays = 'TOTALTIME'
time.Prefix = 'TIME: '
time.Format = '%7.5g'
time.Suffix = '[s]'
timeDisplay = Show(time, renderView, 'TextSourceRepresentation')
timeDisplay.FontSize = 32
timeDisplay.Color = [1.0, 1.0, 1.0]

Render()