"""
This script is a new version of how to create pipe modules with obstructions
"""
#%% ****************** 
#   IMPORTED MODULES
#   ******************
import gmsh

#%% ****************** 
#   IMPORTED CLASSES
#   ******************
from src.TPZGmshToolkit import TPZGmshToolkit
from src.TPZNoObstruction import TPZNoObstruction
from src.TPZSimpleObstruction import TPZSimpleObstruction
from src.TPZCrossObstruction import TPZCrossObstruction
from src.TPZRandomObstruction import TPZRandomObstruction
from src.TPZMultipleObstruction import TPZMultipleObstruction
from src.TPZSemiArcObstruction import TPZSemiArcObstruction
from src.TPZVtkGenerator import TPZVtkGenerator


#%% ****************** 
#     MAIN FUNCTION
#   ******************
def main()->None:
    """
    Main function
    """
    mm = 1e-3
    cm = mm*10

    # "Input for module generation"
    length = 50*cm
    radius = 4.5*cm

    lc = 1e-2

    # "Input for obstruction generation"
    obstructionDiameter = 1*cm
    
    TPZGmshToolkit.Begin()

    TPZGmshToolkit.TurnOnLabels('surface', 'volume')
    TPZGmshToolkit.TurnOnRepresentation('surfaces')
    
    TPZGmshToolkit.TurnOnNormals()
    # TPZMeshModeling.TurnOnTangents()

    # "Input for mesh generation"
    meshDim = 3

    # "Creating the obstructions"
    modules = [
        TPZSimpleObstruction(length=length, lc=lc, radius=radius, obstructionRadius=obstructionDiameter/2),
        TPZCrossObstruction(length=length, lc=lc, radius=radius, obstructionWidth=1*cm, obstructionHeight=1*cm),
        TPZRandomObstruction(length=length, lc=lc, radius=radius, obstructionRadius=obstructionDiameter/2, nObstructions=5),
        TPZMultipleObstruction(length=length, lc=lc, radius=radius, obstructionRadius=obstructionDiameter/2, obstructionDistance=1.5*cm),
        TPZSemiArcObstruction(length=length, lc=lc, radius=radius, obstructionRadius=obstructionDiameter/2),
        TPZNoObstruction(length=length, lc=lc, radius=radius)
    ]
    
    #todo Create the Class TPZModelToolkit and include the method "BuildModel"
    "Moving them to the right place"
    for i, module in enumerate(modules):
        module.Move(0, 0, length*i)
    
    # "Joining them all in one"
    gmsh.model.occ.removeAllDuplicates()
    #todo unitl here

    #todo add the testObs methods (latest version)
    # physical_group = [
    #     [(3, [i + 1 for i, _ in enumerate(modules) ]), 1, "Domain"],
    #     [(2, [1]), 2, "PressIn"],
    #     [(2, [12]), 3, "PressOut"],
    #     [(2, [2, 3, 4, 5, 8, 9, 10, 11, 1 , 12]), 4, "NoSlip"],
    #     [(2, [2, 3, 4, 5, 8, 9, 10, 11]), 5, "NoPenetration"],
    #     [(2, [6]), 100, "Obstruction"],
    #     [(2, [7]), 101, "Orifice"],
    # ]

    # "Creating the elements"
    TPZGmshToolkit.Synchronize()
    TPZGmshToolkit.ShowModel()

    # TPZGmshToolkit.CreatePhysicalGroup(physical_group)

    #todo add the mesh refinement too
    # gmsh.model.mesh.field.add("Cylinder", 1)
    # gmsh.model.mesh.field.setNumber(1, "Radius", 1.2*obstructionDiameter/2)
    # gmsh.model.mesh.field.setNumber(1, "VIn", 0.05*lc)
    # gmsh.model.mesh.field.setNumber(1, "VOut", lc)
    # gmsh.model.mesh.field.setNumber(1, "XAxis", 0)
    # gmsh.model.mesh.field.setNumber(1, "XCenter", 0)
    # gmsh.model.mesh.field.setNumber(1, "YAxis", 0)
    # gmsh.model.mesh.field.setNumber(1, "YCenter", 0)
    # gmsh.model.mesh.field.setNumber(1, "ZAxis", 1)
    # gmsh.model.mesh.field.setNumber(1, "ZCenter", length)
    # gmsh.model.mesh.field.setAsBackgroundMesh(1)

    #* this is supposed to be working already
    # TPZGmshToolkit.CreateMesh(meshDim)

    # TPZGmshToolkit.WriteMeshFiles(fileName, ".msh")

    # TPZGmshToolkit.End()

    # vtk = TPZVtkGenerator()
    # vtk.Do(fileName, fileName+".msh", ["MaterialID"])

if __name__ == '__main__':
    main()