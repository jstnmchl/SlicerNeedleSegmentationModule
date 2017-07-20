cmake_minimum_required(VERSION 2.8.9)

project(StaticNeedleSegmentation)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/StaticNeedleSegmentation")
set(EXTENSION_CATEGORY "Examples")
set(EXTENSION_CONTRIBUTORS "Justin Michael (Robarts Research Institute), Lori Gardi (Robarts Research Institute)")
set(EXTENSION_DESCRIPTION "This is an example of a simple extension")
set(EXTENSION_ICONURL "http://www.example.com/Slicer/Extensions/StaticNeedleSegmentation.png")
set(EXTENSION_SCREENSHOTURLS "http://www.example.com/Slicer/Extensions/StaticNeedleSegmentation/Screenshots/1.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(StaticNeedleSegmentation)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
