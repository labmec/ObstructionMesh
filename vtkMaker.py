"""
Just a simple example of how to create a mesh and 
export it to VTK. Internet says that we should use meshio for that, instead of 
gmsh built-in VTK exporter or VTK Python library.
"""
import gmsh 
import sys
import meshio

showModel = False # turn on to compare with paraview

# ----- Creating the mesh with Gmsh -----
gmsh.initialize()
gmsh.model.add("vtkMaker")

gmsh.option.setNumber('Geometry.SurfaceNumbers', 1)
gmsh.option.setNumber('Geometry.CurveNumbers', 1)

# Create a simple geometry (a box)
lc = 1e-2
gmsh.model.occ.addRectangle(0, 0, 0, 1, 1)

gmsh.model.occ.synchronize()

gmsh.model.mesh.generate(2)

# ----- adding some boundary conditions and material IDs -----
domain = gmsh.model.addPhysicalGroup(2, [1], name="Domain")
bcLeft = gmsh.model.addPhysicalGroup(1, [2], name="Left")
bcRight = gmsh.model.addPhysicalGroup(1, [4], name="Right")
bcUp = gmsh.model.addPhysicalGroup(1, [3], name="Up")
bcDown = gmsh.model.addPhysicalGroup(1, [1], name="Down")

gmsh.write("mesh.msh")

# ----- Exporting to VTK with meshio -----
mesh = meshio.read("mesh.msh")
meshio.write("mesh.vtk", mesh) # exporting the mesh as it is

# here I'm just rewriting what fields paraview will show
materialIDs = []
for i, cell in enumerate(mesh.cells):
    # only the material ID will be saved
    materialID = mesh.cell_data["gmsh:physical"][i]
    materialIDs.append(materialID)

mesh = meshio.Mesh(
    points=mesh.points,
    cells=mesh.cells,
    cell_data={"MaterialID": materialIDs}, # and here I'm replacing the field name
)

meshio.write("mesh_with_materials.vtk", mesh) # exporting the new mesh

if ('-nopopup' not in sys.argv) and showModel: 
    gmsh.fltk.run() 
