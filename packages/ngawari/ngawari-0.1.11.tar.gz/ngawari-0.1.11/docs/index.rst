Welcome to Ngawari's documentation!
====================================

.. image:: https://img.shields.io/pypi/v/ngawari.svg
   :target: https://pypi.org/project/ngawari/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/ngawari.svg
   :target: https://pypi.org/project/ngawari/
   :alt: Python versions

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://github.com/fraser29/ngawari/blob/main/LICENSE
   :alt: License

**Ngawari** is a simple and functional toolkit for working with data in VTK (Visualization Toolkit). 
It provides a comprehensive set of utilities for VTK data manipulation, filtering, and processing.

Key Features
------------

* **VTK Data Utilities**: Functions for working with VTK data objects (vtkImageData, vtkPolyData, vtkStructuredGrid)
* **Array Management**: Easy conversion between VTK arrays and NumPy arrays
* **Filtering Operations**: Comprehensive set of VTK filters and operations
* **Geometry Tools**: Utilities for building and manipulating geometric objects
* **File I/O**: Simplified reading and writing of VTK file formats
* **Mathematical Operations**: Vector and matrix operations optimized for VTK data

Quick Start
-----------

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

Installation
------------

.. code-block:: bash

   pip install ngawari

For development installation with documentation dependencies:

.. code-block:: bash

   pip install ngawari[docs]

Documentation Structure
----------------------

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   api/index
   examples/index
   contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search` 