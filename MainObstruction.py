"""
This script is a new version of how to create pipe modules with obstructions
"""
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
from src.TPZModel import TPZModel
from src.TPZVtkGenerator import TPZVtkGenerator


#%% ****************** 
#     MAIN FUNCTION
#   ******************
def main()->None:
    """
    Main function
    """
    outputFile = "Example101"

    mm = 1e-3
    cm = 10 * mm

    # "Input for module generation"
    lc = 1e-2
    length = 50 * cm
    radius = 4.5 * cm

    # "Input for obstruction generation"
    obstructionDiameter = 1 * cm

    TPZGmshToolkit.Begin()

    TPZGmshToolkit.TurnOnLabels('surface', 'volume')
    TPZGmshToolkit.TurnOnRepresentation('surfaces')
    
    TPZGmshToolkit.TurnOnNormals()

    # "Input for mesh generation"
    meshDim = 3
    meshSize = 5 * cm

    # "Creating the obstructions"
    modules = [
        TPZSimpleObstruction(length=length, lc=lc, radius=radius, obstructionRadius=obstructionDiameter / 2),
        TPZCrossObstruction(length=length, lc=lc, radius=radius, obstructionWidth=1 * cm, obstructionHeight=1 * cm),
        TPZRandomObstruction(length=length, lc=lc, radius=radius, obstructionRadius=obstructionDiameter / 2, nObstructions=5),
        TPZMultipleObstruction(length=length, lc=lc, radius=radius, obstructionRadius=obstructionDiameter / 2, obstructionDistance=1.5 * cm),
        TPZSemiArcObstruction(length=length, lc=lc, radius=radius, obstructionRadius=obstructionDiameter / 2),
        TPZNoObstruction(length=length, lc=lc, radius=radius)
    ]
    
    # building the model
    model = TPZModel(modules)
    model.BuildModel()

    model.ExtractEntities()

    # getting the model configuration (which surface is which)
    domains, inletSurface, outletSurface, obstructionSurfaces, wallSurfaces, orificeSurfaces = model.GetModelConfiguration()

    # creating physical groups (domain and boundary conditions)
    model.CreatePhysicalGroups([
        {"entityDim":3, "entityTags":domains, "name":"Domain", "MaterialID":1},
        {"entityDim":2, "entityTags":inletSurface, "name":"PressIn", "MaterialID":2},
        {"entityDim":2, "entityTags":outletSurface, "name":"PressOut", "MaterialID":3},
        {"entityDim":2, "entityTags":wallSurfaces + inletSurface + outletSurface, "name":"NoSlip", "MaterialID":4},
        {"entityDim":2, "entityTags":wallSurfaces, "name":"NoPenetration", "MaterialID":5},
        {"entityDim":2, "entityTags":obstructionSurfaces, "name":"Obstruction", "MaterialID":100},
        {"entityDim":2, "entityTags":orificeSurfaces, "name":"Orifice", "MaterialID":200}
    ])

    model.Show()

    field1 = model.CreateConstantField(entitiesTags=wallSurfaces + inletSurface + outletSurface + obstructionSurfaces, meshSize=meshSize)
    field2 = model.CreateConstantField(entitiesTags=orificeSurfaces, meshSize=meshSize/10)

    model.SetMinimumMeshSize([field1, field2])

    TPZGmshToolkit.CreateMesh(meshDim)

    TPZGmshToolkit.WriteMeshFiles(outputFile, ".msh")

    TPZGmshToolkit.End()

    vtk = TPZVtkGenerator()
    vtk.Do(outputFile, f"{outputFile}.msh", ["MaterialID"])

    print(f"All done! Files {outputFile}.msh and {outputFile}.vtk created.")

    return

if __name__ == '__main__':
    main()