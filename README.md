# SlicerNeedleSegmentationModule
Module to wrap around existing needle segmentation algorithm that allows inputs to algorithm to be selected from GUI in Slicer

Module is built around an algorithm designed to segment a needle out of a 3D ultrasound image. Module takes an input image and seed point for the segmentation, makes a command line call to trigger the segmentation algorithm (compiled .exe) and then retrieves and displays the result in 3D Slicer.
Segmentation algorithm is not included puiblically but module offers example of using 3D Slicer with commandline calls to other programs.
