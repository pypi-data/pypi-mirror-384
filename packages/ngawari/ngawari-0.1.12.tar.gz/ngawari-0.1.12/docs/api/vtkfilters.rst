vtkfilters - VTK Filtering and Processing
=========================================

.. automodule:: ngawari.vtkfilters
   :members:
   :undoc-members:
   :show-inheritance:

Data Type Checkers
-----------------

.. autofunction:: ngawari.vtkfilters.isVTI
.. autofunction:: ngawari.vtkfilters.isVTP
.. autofunction:: ngawari.vtkfilters.isVTS

Array Operations
---------------

.. autofunction:: ngawari.vtkfilters.getArrayNames
.. autofunction:: ngawari.vtkfilters.getArray
.. autofunction:: ngawari.vtkfilters.getArrayAsNumpy
.. autofunction:: ngawari.vtkfilters.setArrayFromNumpy
.. autofunction:: ngawari.vtkfilters.delArray
.. autofunction:: ngawari.vtkfilters.renameArray

Geometry Creation
----------------

.. autofunction:: ngawari.vtkfilters.buildSphereSource
.. autofunction:: ngawari.vtkfilters.buildCylinderSource
.. autofunction:: ngawari.vtkfilters.buildCubeSource
.. autofunction:: ngawari.vtkfilters.buildPlaneSource
.. autofunction:: ngawari.vtkfilters.buildPolyLineFromXYZ
.. autofunction:: ngawari.vtkfilters.buildPolydataFromXYZ

Filtering Operations
-------------------

.. autofunction:: ngawari.vtkfilters.contourFilter
.. autofunction:: ngawari.vtkfilters.cleanData
.. autofunction:: ngawari.vtkfilters.filterBoolean
.. autofunction:: ngawari.vtkfilters.tubeFilter
.. autofunction:: ngawari.vtkfilters.filterVtpSpline
.. autofunction:: ngawari.vtkfilters.filterTransformPolyData
.. autofunction:: ngawari.vtkfilters.smoothTris
.. autofunction:: ngawari.vtkfilters.smoothTris_SINC
.. autofunction:: ngawari.vtkfilters.filterExtractSurface
.. autofunction:: ngawari.vtkfilters.filterTriangulate

Clipping and Cutting
-------------------

.. autofunction:: ngawari.vtkfilters.clipDataByPlane
.. autofunction:: ngawari.vtkfilters.getPolyDataClippedBySphere
.. autofunction:: ngawari.vtkfilters.getPolyDataClippedByBox
.. autofunction:: ngawari.vtkfilters.clippedByScalar

Image Data Operations
--------------------

.. autofunction:: ngawari.vtkfilters.buildRawImageData
.. autofunction:: ngawari.vtkfilters.filterFlipImageData
.. autofunction:: ngawari.vtkfilters.filterVtiMedian
.. autofunction:: ngawari.vtkfilters.filterResampleToImage
.. autofunction:: ngawari.vtkfilters.filterResliceImage

Surface Operations
-----------------

.. autofunction:: ngawari.vtkfilters.filterGetPointsInsideSurface
.. autofunction:: ngawari.vtkfilters.filterGetEnclosedPts
.. autofunction:: ngawari.vtkfilters.filterSurfaceToImageStencil
.. autofunction:: ngawari.vtkfilters.filterMaskImageBySurface

Data Conversion
--------------

.. autofunction:: ngawari.vtkfilters.vtiToVts
.. autofunction:: ngawari.vtkfilters.vtsToVti
.. autofunction:: ngawari.vtkfilters.pointToCellData
.. autofunction:: ngawari.vtkfilters.cellToPointData

Utility Functions
----------------

.. autofunction:: ngawari.vtkfilters.getPtsAsNumpy
.. autofunction:: ngawari.vtkfilters.getOutline
.. autofunction:: ngawari.vtkfilters.getMaximumBounds
.. autofunction:: ngawari.vtkfilters.copyPolyData
.. autofunction:: ngawari.vtkfilters.copyData 