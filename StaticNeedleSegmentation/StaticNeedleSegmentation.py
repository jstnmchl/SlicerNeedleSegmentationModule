import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import subprocess
import numpy

#
# StaticNeedleSegmentation
#

class StaticNeedleSegmentation(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "StaticNeedleSegmentation" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This is an example of scripted loadable module bundled in an extension.
    It performs a simple thresholding on the input volume and optionally captures a screenshot.
    """
    self.parent.acknowledgementText = """
    This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
    and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# StaticNeedleSegmentationWidget
#

class StaticNeedleSegmentationWidget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # input volume selector
    #
    self.imageSelector = slicer.qMRMLNodeComboBox()
    self.imageSelector.nodeTypes = ["vtkMRMLScalarVolumeNode"]
    self.imageSelector.selectNodeUponCreation = True
    self.imageSelector.addEnabled = False
    self.imageSelector.removeEnabled = False
    self.imageSelector.noneEnabled = False
    self.imageSelector.showHidden = False
    self.imageSelector.showChildNodeTypes = False
    self.imageSelector.setMRMLScene( slicer.mrmlScene )
    self.imageSelector.setToolTip( "Select the image to be segmented." )
    parametersFormLayout.addRow("Image: ", self.imageSelector)

    #
    # input seed selector
    #
    self.seedSelector = slicer.qMRMLNodeComboBox()
    self.seedSelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
    self.seedSelector.selectNodeUponCreation = True
    self.seedSelector.addEnabled = True
    self.seedSelector.removeEnabled = False
    self.seedSelector.noneEnabled = False
    self.seedSelector.showHidden = False
    self.seedSelector.showChildNodeTypes = False
    self.seedSelector.setMRMLScene( slicer.mrmlScene )
    self.seedSelector.setToolTip( "Select a single seed point along the needle shaft." )
    parametersFormLayout.addRow("Seed Point: ", self.seedSelector)

    #
    # output points selector
    #
    self.outputSelector = slicer.qMRMLNodeComboBox()
    self.outputSelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
    self.outputSelector.selectNodeUponCreation = True
    self.outputSelector.addEnabled = True
    self.outputSelector.removeEnabled = True
    self.outputSelector.noneEnabled = True
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = False
    self.outputSelector.setMRMLScene( slicer.mrmlScene )
    self.outputSelector.setToolTip( "Select the markups fiducial where the output will be returned." )
    parametersFormLayout.addRow("Output Points: ", self.outputSelector)

    #
    # check box to trigger taking screen shots for later use in tutorials
    #
    self.enableScreenshotsFlagCheckBox = qt.QCheckBox()
    self.enableScreenshotsFlagCheckBox.checked = 0
    self.enableScreenshotsFlagCheckBox.setToolTip("If checked, take screen shots for tutorials. Use Save Data to write them to disk.")
    parametersFormLayout.addRow("Enable Screenshots", self.enableScreenshotsFlagCheckBox)


    #
    # Apply Button
    #
    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = False
    parametersFormLayout.addRow(self.applyButton)

    #
    # Advanced Area
    #
    advancedCollapsibleButton = ctk.ctkCollapsibleButton()
    advancedCollapsibleButton.text = "Advanced"
    self.layout.addWidget(advancedCollapsibleButton)

    # Layout within the dummy collapsible button
    advancedFormLayout = qt.QFormLayout(advancedCollapsibleButton)

    #
    # Manual Segmentation points selector
    #
    self.manSegPointsSelector = slicer.qMRMLNodeComboBox()
    self.manSegPointsSelector.nodeTypes = ["vtkMRMLMarkupsFiducialNode"]
    self.manSegPointsSelector.selectNodeUponCreation = True
    self.manSegPointsSelector.addEnabled = True
    self.manSegPointsSelector.removeEnabled = True
    self.manSegPointsSelector.noneEnabled = True
    self.manSegPointsSelector.showHidden = False
    self.manSegPointsSelector.showChildNodeTypes = False
    self.manSegPointsSelector.setMRMLScene( slicer.mrmlScene )
    self.manSegPointsSelector.setToolTip( "Select the markups fiducial containing the manually selected tip." )
    advancedFormLayout.addRow("Manual Tip: ", self.manSegPointsSelector)

    self.numToAddSliderWidget = ctk.ctkSliderWidget()
    self.numToAddSliderWidget.singleStep = 5.0
    self.numToAddSliderWidget.minimum = 0.0
    self.numToAddSliderWidget.maximum = 90.0
    self.numToAddSliderWidget.value = 45.0
    self.numToAddSliderWidget.toolTip = "Input the expected insertion angle relative to the A-P axis."
    advancedFormLayout.addRow("Expected Insertion Angle: ", self.numToAddSliderWidget)

    #
    # check box to select if models of segmentations should be generated
    #
    self.enableNeedleModelsFlagCheckBox = qt.QCheckBox()
    self.enableNeedleModelsFlagCheckBox.checked = 1
    self.enableNeedleModelsFlagCheckBox.setToolTip("If checked, models are generated from points defining segmentations.")
    advancedFormLayout.addRow("Generate Needle Models", self.enableNeedleModelsFlagCheckBox)

    # connections
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.imageSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.seedSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.outputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)
    self.manSegPointsSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onSelect)

    # Add vertical spacer
    self.layout.addStretch(1)

    # Refresh Apply button state
    self.onSelect()

  def cleanup(self):
    pass

  def onSelect(self):
    self.applyButton.enabled = self.imageSelector.currentNode() and self.seedSelector.currentNode() and self.outputSelector.currentNode()

  def onApplyButton(self):
    logic = StaticNeedleSegmentationLogic()
    enableScreenshotsFlag = self.enableScreenshotsFlagCheckBox.checked
    enableNeedleModelsFlag = self.enableNeedleModelsFlagCheckBox.checked
    logic.run(self.imageSelector.currentNode(), self.seedSelector.currentNode(),
              self.outputSelector.currentNode(), self.manSegPointsSelector.currentNode(),
              self.numToAddSliderWidget.value, enableNeedleModelsFlag, enableScreenshotsFlag, )

#
# StaticNeedleSegmentationLogic
#

class StaticNeedleSegmentationLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def hasImageData(self,volumeNode):
    """This is an example logic method that
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      logging.debug('hasImageData failed: no volume node')
      return False
    if volumeNode.GetImageData() is None:
      logging.debug('hasImageData failed: no image data in volume node')
      return False
    return True

  def isValidInputOutputData(self, inputVolumeNode, outputVolumeNode):
    """Validates if the output is not the same as input
    """
    if not inputVolumeNode:
      logging.debug('isValidInputOutputData failed: no input volume node defined')
      return False
    if not outputVolumeNode:
      logging.debug('isValidInputOutputData failed: no output volume node defined')
      return False
    if inputVolumeNode.GetID()==outputVolumeNode.GetID():
      logging.debug('isValidInputOutputData failed: input and output volume is the same. Create a new volume for output to avoid this error.')
      return False
    return True

  def takeScreenshot(self,name,description,type=-1):
    # show the message even if not taking a screen shot
    slicer.util.delayDisplay('Take screenshot: '+description+'.\nResult is available in the Annotations module.', 3000)

    lm = slicer.app.layoutManager()
    # switch on the type to get the requested window
    widget = 0
    if type == slicer.qMRMLScreenShotDialog.FullLayout:
      # full layout
      widget = lm.viewport()
    elif type == slicer.qMRMLScreenShotDialog.ThreeD:
      # just the 3D window
      widget = lm.threeDWidget(0).threeDView()
    elif type == slicer.qMRMLScreenShotDialog.Red:
      # red slice window
      widget = lm.sliceWidget("Red")
    elif type == slicer.qMRMLScreenShotDialog.Yellow:
      # yellow slice window
      widget = lm.sliceWidget("Yellow")
    elif type == slicer.qMRMLScreenShotDialog.Green:
      # green slice window
      widget = lm.sliceWidget("Green")
    else:
      # default to using the full window
      widget = slicer.util.mainWindow()
      # reset the type so that the node is set correctly
      type = slicer.qMRMLScreenShotDialog.FullLayout

    # grab and convert to vtk image data
    qpixMap = qt.QPixmap().grabWidget(widget)
    qimage = qpixMap.toImage()
    imageData = vtk.vtkImageData()
    slicer.qMRMLUtils().qImageToVtkImageData(qimage,imageData)

    annotationLogic = slicer.modules.annotations.logic()
    annotationLogic.CreateSnapShot(name, description, type, 1, imageData)

  def compareToManualSeg(self, tip, tail , manSegPoints, insertAngle):
    # print("One day I'll be a real function! Please write me Jessica!!")
    # get manually selected point
    manualTip = [0.0, 0.0, 0.0]
    manSegPoints.GetNthFiducialPosition(0, manualTip)
    # manualTipString = "{0:.10} {1:.10} {2:.10}".format(manualTip[0], manualTip[1], manualTip[2])
    # print("manual tip: " + manualTipString)

    # calculate the distance between needle tips
    tipError = numpy.sqrt((tip[0]-manualTip[0])**2 + (tip[1]-manualTip[1])**2 + (tip[2]-manualTip[2])**2)
    tipErrorString = "{0:.10}".format(tipError)
    print("Tip error is " + tipErrorString + " mm.")

    # calculate the directional vectors for the algorithm and manual segmentations
    algoVector = [a - b for a, b in zip(tip, tail)]
    manualVector = [a - b for a, b in zip(manualTip, tail)]

    # normalize the vectors
    algoLength = numpy.sqrt(algoVector[0]**2 + algoVector[1]**2 + algoVector[2]**2)
    manualLength = numpy.sqrt(manualVector[0] ** 2 + manualVector[1] ** 2 + manualVector[2] ** 2)
    algoVector = [a / algoLength for a in algoVector]
    manualVector = [a / manualLength for a in manualVector]

    # calculate the dot product and compute the trajectory difference
    dotProduct = numpy.dot(algoVector, manualVector)
    trajError = numpy.arccos(dotProduct)
    trajError = numpy.degrees(trajError)
    trajErrorString = "{0:.10}".format(trajError)
    print("Trajectory error is " + trajErrorString + " degrees.")

    # calculate the active tip error
    algoActTip = [a * 10 for a in algoVector]
    algoActTip = [a - b for a,b in zip(tip, algoActTip)]
    manualActTip = [a * 10 for a in manualVector]
    manualActTip = [a - b for a,b in zip(tip, manualActTip)]
    actTipError = numpy.sqrt((algoActTip[0] - manualActTip[0]) ** 2 + (algoActTip[1] - manualActTip[1]) ** 2 + (algoActTip[2] - manualActTip[2]) ** 2)
    actTipErrorString = "{0:.10}".format(actTipError)
    print("Active tip error is " + actTipErrorString + " mm.")

    # calculate the difference from expected insertion angle
    insertString = "{0:.10}".format(insertAngle)
    print("Expected insertion angle is " + insertString + " degrees.")

    # calculate insertion angle of algorithmically segmented needle
    dotProduct = -1 * algoVector[1]
    algoAngle = numpy.arccos(dotProduct)
    algoAngle = numpy.degrees(algoAngle)
    algoAngleString = "{0:.10}".format(algoAngle)
    print("Segmented insertion angle is " + algoAngleString + " degrees.")

    # calculate insertion angle error
    angleDiff = numpy.absolute(insertAngle - algoAngle)
    angleDiffString = "{0:.10}".format(angleDiff)
    print("Insertion angle difference is " + angleDiffString + " degrees.")

    # check if a metrics table has already been created
    if not slicer.util.getNode('Metrics'):
      tableNode = slicer.vtkMRMLTableNode()
      tableNode.SetName('Metrics')
      col = tableNode.AddColumn()
      col.SetName('Tip Difference (mm)')
      col = tableNode.AddColumn()
      col.SetName('Active Tip Difference (mm)')
      col = tableNode.AddColumn()
      col.SetName('Trajectory Difference (deg)')
      col = tableNode.AddColumn()
      col.SetName('Segmented Insertion Angle (deg)')
      col = tableNode.AddColumn()
      col.SetName('Insertion Angle Difference (deg)')
      slicer.mrmlScene.AddNode(tableNode)
    else:
      tableNode = slicer.util.getNode('Metrics')

    # populates a table with the metrics values
    tableNode.AddEmptyRow()
    row = tableNode.GetNumberOfRows() - 1
    tableNode.SetCellText(row, 0, tipErrorString)
    tableNode.SetCellText(row, 1, actTipErrorString)
    tableNode.SetCellText(row, 2, trajErrorString)
    tableNode.SetCellText(row, 3, algoAngleString)
    tableNode.SetCellText(row, 4, angleDiffString)

  def run(self, inputVolume, inputSeedFiducial, outputPoints, manSegPoints, insertAngle, enableNeedleModels,enableScreenshots=0):
    """
    Run the actual algorithm
    """

    # if not self.isValidInputOutputData(inputVolume, outputVolume):
    #   slicer.util.errorDisplay('Input volume is the same as output volume. Choose a different output volume.')
    #   return False

    logging.info('Processing started')
    print(enableNeedleModels)
    #Hard coded parameters for passing between slicer and executable through files on disk
    inputImageFileName = 'inputImage.mha'
    outputResultsFileName = 'segmentationOutput.txt'
    exeName = 'StaticNeedleTestBed'

    dir_path = os.path.dirname(os.path.realpath(__file__)) #directory script is running from

    #Write input image to disk

    imgData = vtk.vtkImageData()
    imgData.DeepCopy(inputVolume.GetImageData())
    imgData.SetSpacing(inputVolume.GetSpacing())
    imgData.SetOrigin(inputVolume.GetOrigin())

    writer = vtk.vtkMetaImageWriter()
    writer.SetFileName(os.path.join(dir_path,inputImageFileName))
    writer.SetInputData(imgData)
    writer.Write()


    inputImageFullPath = os.path.join(dir_path, inputImageFileName)
    #print(dir_path)
    # storageNode = inputVolume.CreateDefaultStorageNode()
    # storageNode.SetFileName(inputImageFullPath)
    # inputVolume.AddAndObserveStorageNodeID(storageNode.GetID())
    # storageNode.WriteData(inputVolume)
    print('Image successfully written to ' + inputImageFullPath)

    #Get seed point
    seedPoint = [0.0, 0.0, 0.0]
    ##FIRST CHECK ONLY ONE POINT IN MARKUPS FIDUCIAL
    inputSeedFiducial.GetNthFiducialPosition(0, seedPoint)
    #convert from LPS to RAS
    seedPoint[0] = -1*seedPoint[0]
    seedPoint[1] = -1 * seedPoint[1]
    #lpsToRas = vtk.vtkMatrix4x4()
    #lpsToRas = vtk.vtkMatrix4x4()
    #lpsToRas.SetElement(0, 0, -1)
    #lpsToRas.SetElement(1, 1, -1)

    #Call needle segmentation algorithm
    exeFullPath = os.path.join(dir_path,exeName)
    seedPointString = "{0:.10} {1:.10} {2:.10}".format(seedPoint[0], seedPoint[1], seedPoint[2])
    commandLineCall = exeFullPath + " " + inputImageFullPath + " " + seedPointString
    outputFromExe = subprocess.check_output(commandLineCall )
    #  'C:\\1-Projects\\StaticNeedleTestBed_VS_2013\\x64\\Release\\StaticNeedleTestBed C:\\1-Projects\\StaticNeedleTestBed_VS_2013\\x64\\Release\\LeftAngle45med.mha 91.6299 27.8934 66.8955')


    #print("Input image full path: " + inputImageFullPath)
    print("Command line call: " + commandLineCall)
    print("Output from exe: " + outputFromExe)
    print("seed point: " + seedPointString)

    #Pass results of algorithm to output markups fiducial
    outputPoints.RemoveAllMarkups()
    outputFromExe_floats = map(float, outputFromExe.split())
    tip = outputFromExe_floats[:3]
    tip[0] = -1*tip[0]
    tip[1] = -1*tip[1]
    tail = outputFromExe_floats[3:6]
    tail[0] = -1*tail[0]
    tail[1] = -1*tail[1]

    outputPoints.AddFiducialFromArray(tip)
    outputPoints.AddFiducialFromArray(tail)

    #Compare algorithm results to manually selected fiducials
    ####
    #Check whether or not a manually selected tip has been input
    if manSegPoints.GetNumberOfFiducials() == 0:
      print('No manually selected tip.')
    else:
      self.compareToManualSeg(tip, tail, manSegPoints, insertAngle)
    ####

    #Extrapolate points on needle to extent of image volume


    #Generate model of needle from points (radius of 1mm)


    # Capture screenshot
    if enableScreenshots:
      self.takeScreenshot('StaticNeedleSegmentationTest-Start','MyScreenshot',-1)

    logging.info('Processing completed')

    return True


class StaticNeedleSegmentationTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_StaticNeedleSegmentation1()

  def test_StaticNeedleSegmentation1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = StaticNeedleSegmentationLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')
