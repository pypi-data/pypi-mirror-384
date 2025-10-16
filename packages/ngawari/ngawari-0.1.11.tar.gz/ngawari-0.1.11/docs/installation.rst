Installation Guide
==================

Requirements
------------

Ngawari requires Python 3.9 or higher and the following dependencies:

* `numpy <https://numpy.org/>`_ - For numerical operations
* `vtk <https://vtk.org/>`_ (>=9.3.0) - The Visualization Toolkit
* `scipy <https://scipy.org/>`_ - For scientific computing

Installation Methods
-------------------

From PyPI (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~

The easiest way to install Ngawari is using pip:

.. code-block:: bash

   pip install ngawari

From Source
~~~~~~~~~~~

To install from the source code:

.. code-block:: bash

   git clone https://github.com/fraser29/ngawari.git
   cd ngawari
   pip install -e .

Development Installation
~~~~~~~~~~~~~~~~~~~~~~~~

For development work, install with documentation dependencies:

.. code-block:: bash

   pip install -e .[docs]

This will install additional packages needed for building documentation:

* `sphinx <https://www.sphinx-doc.org/>`_ - Documentation generator
* `sphinx-rtd-theme <https://sphinx-rtd-theme.readthedocs.io/>`_ - Read the Docs theme
* `sphinx-autodoc-typehints <https://github.com/agronholm/sphinx-autodoc-typehints>`_ - Type hints support
* `myst-parser <https://myst-parser.readthedocs.io/>`_ - Markdown support

Verifying Installation
----------------------

After installation, you can verify that Ngawari is working correctly:

.. code-block:: python

   from ngawari import ftk, fIO, vtkfilters
   
   # Create a simple test
   sphere = vtkfilters.buildSphereSource([0, 0, 0], radius=1.0)
   print(f"Sphere created with {sphere.GetNumberOfPoints()} points")
   
   # Test array operations
   points = vtkfilters.getPtsAsNumpy(sphere)
   print(f"Points shape: {points.shape}")


Version Compatibility
~~~~~~~~~~~~~~~~~~~~

Ngawari is tested with:
* Python 3.9, 3.10, 3.11
* VTK 9.3.0 and later
* NumPy 1.21 and later
* SciPy 1.7 and later

If you encounter compatibility issues, please check the `GitHub issues <https://github.com/fraser29/ngawari/issues>`_ or create a new one. 