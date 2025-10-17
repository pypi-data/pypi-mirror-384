Contributing to Ngawari
=======================

Thank you for your interest in contributing to Ngawari! This document provides guidelines for contributing to the project.

Getting Started
--------------

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
3. **Create a feature branch** for your changes
4. **Make your changes** following the guidelines below
5. **Test your changes** thoroughly
6. **Submit a pull request**

Development Setup
----------------

Install the development dependencies:

.. code-block:: bash

   git clone https://github.com/your-username/ngawari.git
   cd ngawari
   pip install -e .[docs]

Code Style
----------

Ngawari follows PEP 8 style guidelines with some exceptions:

* Line length: 120 characters maximum
* Use descriptive variable names
* Add type hints where appropriate
* Include docstrings for all public functions

Example:

.. code-block:: python

   def calculate_distance(point_a: np.ndarray, point_b: np.ndarray) -> float:
       """
       Calculate the Euclidean distance between two points.
       
       Args:
           point_a: First point as numpy array
           point_b: Second point as numpy array
           
       Returns:
           float: Distance between the points
       """
       return np.linalg.norm(point_b - point_a)


Testing
-------

Write tests for new functionality:

.. code-block:: python

   def test_calculate_distance():
       """Test distance calculation function."""
       point_a = np.array([0, 0, 0])
       point_b = np.array([1, 1, 1])
       expected = np.sqrt(3)
       result = calculate_distance(point_a, point_b)
       assert np.isclose(result, expected)

Run tests:

.. code-block:: bash

   python -m pytest ngawari/tests/

Building Documentation
---------------------

To build the documentation locally:

.. code-block:: bash

   cd docs
   make html

The documentation will be built in `docs/_build/html/`.

Pull Request Guidelines
----------------------

1. **Keep changes focused** - One feature or bug fix per PR
2. **Write clear commit messages** - Use present tense and be descriptive
3. **Update documentation** - Add or update docstrings and examples
4. **Add tests** - Include tests for new functionality
5. **Check the build** - Ensure all tests pass and documentation builds

Example commit message:

.. code-block:: text

   Add function to calculate surface area of polydata

   - Implement calculatePolyDataArea function
   - Add comprehensive docstring with examples
   - Include unit tests for various input types
   - Update API documentation

Issue Reporting
--------------

When reporting issues, please include:

* Python version
* Ngawari version
* VTK version
* Operating system
* Minimal code example to reproduce the issue
* Expected vs actual behavior

Example:

.. code-block:: text

   **Environment:**
   - Python 3.9.7
   - Ngawari 0.1.7
   - VTK 9.3.0
   - Ubuntu 20.04
   
   **Issue:**
   Function X returns incorrect results when input is Y.
   
   **Minimal Example:**
   ```python
   from ngawari import ftk, fIO, vtkfilters
   result = ftk.some_function(input_data)
   print(result)  # Expected: A, Got: B
   ```

Getting Help
-----------

* **GitHub Issues**: For bug reports and feature requests
* **GitHub Discussions**: For questions and general discussion
* **Documentation**: Check the API reference and examples

Thank you for contributing to Ngawari! 