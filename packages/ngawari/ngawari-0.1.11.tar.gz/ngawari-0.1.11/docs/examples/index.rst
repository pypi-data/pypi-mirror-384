Examples
========

This section contains practical examples demonstrating how to use Ngawari for common tasks.

Basic Geometry Example
---------------------

.. code-block:: python

   from ngawari import ftk, fIO, vtkfilters
   import numpy as np
   
   # Create a sphere
   sphere = vtkfilters.buildSphereSource([0, 0, 0], radius=1.0)
   
   # Get points and add scalar data based on distance from origin
   points = vtkfilters.getPtsAsNumpy(sphere)
   distances = np.linalg.norm(points, axis=1)
   vtkfilters.setArrayFromNumpy(sphere, distances, "distance", SET_SCALAR=True)
   
   # Apply smoothing
   smoothed = vtkfilters.smoothTris(sphere, iterations=10)
   
   # Save the result
   fIO.writeVTKFile(smoothed, "smoothed_sphere.vtp")
   
   print(f"Created sphere with {smoothed.GetNumberOfPoints()} points")

Clipping Example
---------------

.. code-block:: python

   from ngawari import ftk, fIO, vtkfilters
   
   # Load or create some data
   sphere = vtkfilters.buildSphereSource([0, 0, 0], radius=1.0)
   
   # Clip with a plane
   plane_point = [0.5, 0, 0]
   plane_normal = [1, 0, 0]  # x-direction
   clipped = vtkfilters.clipDataByPlane(sphere, plane_point, plane_normal)
   
   # Clip with a sphere
   clip_center = [0.3, 0, 0]
   clip_radius = 0.4
   final_result = vtkfilters.getPolyDataClippedBySphere(clipped, clip_center, clip_radius)
   
   # Save result
   fIO.writeVTKFile(final_result, "clipped_sphere.vtp")
   
   print(f"Clipped sphere has {final_result.GetNumberOfPoints()} points")

Image Data Example
-----------------

.. code-block:: python

   from ngawari import ftk, fIO, vtkfilters
   import numpy as np
   
   # Create a simple image data
   dims = [50, 50, 50]
   spacing = [0.1, 0.1, 0.1]
   origin = [0, 0, 0]
   
   image_data = vtkfilters.buildRawImageData(dims, spacing, origin)
   
   # Create some scalar data (example: distance from center)
   points = vtkfilters.getPtsAsNumpy(image_data)
   center = np.array([2.5, 2.5, 2.5])  # Center of the image
   distances = np.linalg.norm(points - center, axis=1)
   
   # Add the data to the image
   vtkfilters.setArrayFromNumpy(image_data, distances, "distance_from_center", SET_SCALAR=True)
   
   # Apply median filtering
   filtered = vtkfilters.filterVtiMedian(image_data, filterKernalSize=3)
   
   # Save the result
   fIO.writeVTKFile(filtered, "filtered_image.vti")
   
   print(f"Created image data with {filtered.GetNumberOfPoints()} points")

Mathematical Operations Example
------------------------------

.. code-block:: python

   from ngawari import ftk, fIO, vtkfilters
   import numpy as np
   
   # Create some test points
   points = np.array([
       [0, 0, 0],
       [1, 0, 0],
       [0, 1, 0],
       [1, 1, 0]
   ])
   
   # Calculate distances between points
   for i in range(len(points)):
       for j in range(i+1, len(points)):
           dist = ftk.distTwoPoints(points[i], points[j])
           print(f"Distance between point {i} and {j}: {dist:.3f}")
   
   # Normalize vectors
   vectors = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
   normalized = ftk.normaliseArray(vectors)
   print("Normalized vectors:")
   print(normalized)
   
   # Calculate angles between vectors
   angle = ftk.angleBetween2Vec(vectors[0], vectors[1])
   print(f"Angle between first two vectors: {angle:.3f} radians")

File I/O Example
---------------

.. code-block:: python

   from ngawari import ftk, fIO, vtkfilters
   
   # Create some geometry
   sphere = vtkfilters.buildSphereSource([0, 0, 0], radius=1.0)
   cylinder = vtkfilters.buildCylinderSource([2, 0, 0], radius=0.5, height=2.0)
   
   # Save individual files
   fIO.writeVTKFile(sphere, "sphere.vtp")
   fIO.writeVTKFile(cylinder, "cylinder.vtp")
   
   # Load them back
   loaded_sphere = fIO.readVTKFile("sphere.vtp")
   loaded_cylinder = fIO.readVTKFile("cylinder.vtp")
   
   print(f"Loaded sphere has {loaded_sphere.GetNumberOfPoints()} points")
   print(f"Loaded cylinder has {loaded_cylinder.GetNumberOfPoints()} points")
   
   # Create a PVD file for time series data
   time_data = {
       0.0: sphere,
       1.0: cylinder
   }
   
   fIO.writeVTK_PVD_Dict(time_data, ".", "example", ".vtp")
   print("Created PVD file for time series data") 