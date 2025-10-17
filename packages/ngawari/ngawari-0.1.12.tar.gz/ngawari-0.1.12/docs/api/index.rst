API Reference
=============

This section contains the complete API reference for Ngawari. The library is organized into three main modules:

Core Modules
------------

.. toctree::
   :maxdepth: 2

   ftk
   fIO
   vtkfilters

Module Overview
---------------

ftk - Mathematical and Utility Functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``ftk`` module provides mathematical utilities and helper functions for working with vectors, matrices, and geometric operations.

Key features:
* Vector and matrix operations
* Geometric calculations
* Point and line utilities
* Mathematical transformations

fIO - File Input/Output
~~~~~~~~~~~~~~~~~~~~~~~

The ``fIO`` module handles reading and writing VTK file formats and other data formats.

Key features:
* VTK file format support (VTP, VTI, VTS, VTU)
* Other format support (STL, OBJ, PLY)
* Data conversion utilities
* Batch processing capabilities

vtkfilters - VTK Filtering and Processing
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``vtkfilters`` module provides comprehensive VTK filtering and processing operations.

Key features:
* VTK data object utilities
* Array management and conversion
* Geometry creation and manipulation
* Clipping and cutting operations
* Surface and volume processing
* Connected region analysis

Usage Examples
--------------

Basic Import
~~~~~~~~~~~

.. code-block:: python

   import ngawari as ng
   
   # Or import specific modules
   from ngawari import ftk, fIO, vtkfilters

Common Patterns
~~~~~~~~~~~~~~~

.. code-block:: python

   # Load data
   data = ng.loadVTP("mesh.vtp")
   
   # Process data
   processed = ng.smoothTris(data, iterations=10)
   
   # Save result
   ng.saveVTP(processed, "smoothed_mesh.vtp")

For detailed information about each module, click on the links above or use the navigation menu. 