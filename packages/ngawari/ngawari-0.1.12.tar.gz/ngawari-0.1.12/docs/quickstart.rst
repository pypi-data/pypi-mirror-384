Quick Start Guide
=================

This guide will help you get started with Ngawari quickly. We'll cover the basic concepts and show you how to perform common tasks.

Basic Concepts
--------------

Ngawari provides utilities for working with VTK data objects. Three primary modules are provided:

* **ftk**: Mathematical and utility functions
* **fIO**: File input/output operations
* **vtkfilters**: VTK filtering and processing functions

Getting Started
--------------

First, import Ngawari:

.. code-block:: python

   from ngawari import ftk, fIO, vtkfilters

Creating Basic Geometry
----------------------

Create a sphere:

.. code-block:: python

   # Create a sphere at origin with radius 1.0
   sphere = vtkfilters.buildSphereSource([0, 0, 0], radius=1.0)
   print(f"Sphere has {sphere.GetNumberOfPoints()} points")

Create a cylinder:

.. code-block:: python

   # Create a cylinder
   cylinder = vtkfilters.buildCylinderSource([0, 0, 0], radius=0.5, height=2.0)
   print(f"Cylinder has {cylinder.GetNumberOfPoints()} points")

Working with Arrays
------------------

Get points as a NumPy array:

.. code-block:: python

   # Get all points from the sphere
   points = vtkfilters.getPtsAsNumpy(sphere)
   print(f"Points shape: {points.shape}")  # (n_points, 3)

Add a scalar array:

.. code-block:: python

   # Create a scalar array based on x-coordinates
   x_coords = points[:, 0]
   vtkfilters.setArrayFromNumpy(sphere, x_coords, "x_coordinates", SET_SCALAR=True)

Add a vector array:

.. code-block:: python

   # Create a vector array (example: normalized position vectors)
   import numpy as np
   vectors = points / np.linalg.norm(points, axis=1, keepdims=True)
   vtkfilters.setArrayFromNumpy(sphere, vectors, "normals", SET_VECTOR=True)

Filtering Operations
-------------------

Apply smoothing:

.. code-block:: python

   # Smooth the sphere
   smoothed = vtkfilters.smoothTris(sphere, iterations=10)

Extract surface from volume data:

.. code-block:: python

   # If you have volume data, extract the surface
   surface = vtkfilters.filterExtractSurface(volume_data)

Clipping and Cutting
-------------------

Clip by plane:

.. code-block:: python

   # Clip the sphere with a plane
   plane_point = [0, 0, 0]
   plane_normal = [1, 0, 0]  # x-direction
   clipped = vtkfilters.clipDataByPlane(sphere, plane_point, plane_normal)

Clip by sphere:

.. code-block:: python

   # Clip with a sphere
   clip_center = [0.5, 0, 0]
   clip_radius = 0.3
   clipped = vtkfilters.getPolyDataClippedBySphere(sphere, clip_center, clip_radius)

File I/O
--------

Save data to VTK format - file extension is used for format. Supported formats are:

**Write**

- .vtp
- .vts
- .vtu
- .stl
- .vti
- .mhd
- .mha
- .nii

**Read**

- .vtp
- .vts
- .vtu
- .stl
- .vti
- .vtk
- .vtm
- .nrrd
- .mha
- .ply
- .nii
- .nii.gz
- .png
- .jpg / .jpeg
- .tif / .tiff

Also supports .pvd files for reading and writing - used for e.g. time series data.

.. code-block:: python

   # Save polydata
   fIO.writeVTKFile(sphere, "sphere.vtp")
   
   # Save image data
   fIO.writeVTKFile(image_data, "image.vti")

Load data from VTK format:

.. code-block:: python

   # Load polydata
   loaded_sphere = fIO.readVTKFile("sphere.vtp")
   
   # Load image data
   loaded_image = fIO.readVTKFile("image.vti")

Mathematical Operations
----------------------

Calculate distances:

.. code-block:: python

   # Distance between two points
   point1 = [0, 0, 0]
   point2 = [1, 1, 1]
   distance = ftk.distTwoPoints(point1, point2)

Vector operations:

.. code-block:: python

   # Normalize a vector
   vector = [1, 2, 3]
   normalized = ftk.normaliseArray(vector)
   

Complete Example
---------------

Here's a complete example that demonstrates several features:

.. code-block:: python


   from ngawari import ftk, fIO, vtkfilters
   import numpy as np
   
   # Create a simple sphere
   sphere = vtkfilters.buildSphereSource([0, 0, 0], radius=1.0)
   
   # Get points as numpy array
   points = vtkfilters.getPtsAsNumpy(sphere)
   
   # Add a scalar array
   vtkfilters.setArrayFromNumpy(sphere, points[:, 0], "x_coords", SET_SCALAR=True)
   
   # Apply a filter
   smoothed = vtkfilters.smoothTris(sphere, iterations=10)

   # Write to file
   fIO.writeVTKFile(smoothed, "smoothed_sphere.vtp")

   # Build image over sphere:
   image = vtkfilters.buildRawImageDataFromPolyData(smoothed, res=[0.1,0.1,0.1])

   # Add a scalar array to the image
   vtkfilters.setArrayFromNumpy(image, np.random.rand(image.GetNumberOfPoints()), "random_scalar", SET_SCALAR=True)

   # Null scalars outside sphere
   image_nulled = vtkfilters.filterNullOutsideSurface(image, smoothed)

   # Write to file
   fIO.writeVTKFile(image_nulled, "image_over_sphere.vti")

Next Steps
----------

Now that you have the basics, you can explore:

* :doc:`api/index` - Complete API reference
* :doc:`examples/index` - More detailed examples
* :doc:`contributing` - How to contribute to the project

For more advanced usage, check out the individual module documentation:

* :doc:`api/ftk` - Mathematical and utility functions
* :doc:`api/fIO` - File input/output operations
* :doc:`api/vtkfilters` - VTK filtering and processing functions 