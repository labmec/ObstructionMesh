"""
This class uses all modules created to generate a single and unified mesh, AKA, the model. 
Some methods are also present in the TPZGmshToolkit class, but they are more specific to this application.

Created by Carlos Puga: 09/20/2025
"""
#%% ******************
#   IMPORTED MODULES
#   ******************
import gmsh 
import sys

from src.TPZSimpleObstruction import TPZSimpleObstruction
from src.TPZGmshToolkit import TPZGmshToolkit
from src.TPZBasicDataStructure import TPZBasicDataStructure

#%% ******************
#   CLASS DEFINITION
#   ******************
class TPZModel(TPZBasicDataStructure):
    def __init__(self, modules:list) -> None:
        super().__init__()

        # it can be, in fact, any kind of obstruction. I just need the method to recognize the object attributes
        self.fModules: list[TPZSimpleObstruction] = modules  
        self.fTotalLength: float = -1.0
        self.fEntities: dict = {}

        self.DeactivateAttr()

        self.__post_init__()

        return
    
    def __post_init__(self) -> None:
        """
        Post-initialization method to compute the total length of the model.
        """
        self.fTotalLength = sum(module.fLength for module in self.fModules)
        return
    
    def BuildModel(self) -> None:
        """
        Build the model by assembling the specified modules.
        """
        # first we translate each module to its correct position
        currentZ = self.fModules[0].fLength
        for module in self.fModules[1:]:
            gmsh.model.occ.translate([(3, module.fVolumeID)], 0, 0, currentZ)
            
            currentZ += module.fLength

        gmsh.model.occ.removeAllDuplicates()
        gmsh.model.occ.synchronize()

        return
    
    def DistanceToOrigin(self, x, y, z, planeXY=False) -> float:
        """
        Calculate the distance from a point to the origin.
        3D distance by default, or 2D distance on the XY plane if plane

        Inputs:
        ------
        x, y, z : float
            Coordinates of the point.
        planeXY : bool
            If True, calculate distance on the XY plane.

        Returns:
        --------
        float
            Distance to the origin.
        """
        if planeXY:
            return (x ** 2 + y ** 2) ** 0.5
    
        return (x ** 2 + y ** 2 + z ** 2) ** 0.5

    def FindMidPoint(self, coords:list) -> tuple[float]:
        """
        Find the midpoint of a surface given its coordinates.
        Inputs:
        -------
        surfaceCoords : list of tuples
            List of (x, y, z) coordinates of the surface points.
        Returns:
        --------
        tuple
            (x, y, z) coordinates of the midpoint.
        """
        x = y = z = 0.0

        for c in coords:
            x += c[0]
            y += c[1]
            z += c[2]

        sz = len(coords)

        return (x/sz, y/sz, z/sz)

    def ExtractEntities(self) -> None:
        """
        Find and store all geometric entities in the model.
        """
        tol = 1e-6
        radius = self.fModules[0].fRadius  # all modules need to have the same radius

        volumes = gmsh.model.getEntities(dim=3)
        volumes = [v[1] for v in volumes]

        self.fEntities = {"volumes": []}

        for v in volumes:
            volumes = {"id": v, "surfaces": []}

            lastVolumeSurfaces = [s["id"] for s in self.fEntities["volumes"][-1]["surfaces"]] if self.fEntities["volumes"] else []

            volumeSurfaces = gmsh.model.getBoundary([(3, v)], oriented=False, recursive=False)
            volumeSurfaces = [s[1] for s in volumeSurfaces if s[1] not in lastVolumeSurfaces]

            for s in volumeSurfaces:
                surface = {"id": s, "isOrifice": False, "pMidDistance": 0.0, "pMid": []}
                
                surfacePoints = gmsh.model.getBoundary([(2, s)], oriented=False, recursive=True)
                surfacePoints = [p[1] for p in surfacePoints]

                pointDistanceOnPlaneXY = [self.DistanceToOrigin(*gmsh.model.getValue(0, p, []), planeXY=True) for p in surfacePoints]

                if all(distance < radius for distance in pointDistanceOnPlaneXY):
                    surface["isOrifice"] = True
                    volumes["surfaces"].append(surface)

                    continue # no need to calculate mid point for orifice surfaces

                elif any(distance < radius for distance in pointDistanceOnPlaneXY):
                    surfacePoints = [p for p, dist in zip(surfacePoints, pointDistanceOnPlaneXY) if abs(dist - radius) < tol]

                pointCoords = [gmsh.model.getValue(0, p, []) for p in surfacePoints] # initialize with first point

                surface["pMid"] = self.FindMidPoint(pointCoords)
                surface["pMidDistance"] = self.DistanceToOrigin(*surface["pMid"])

                volumes["surfaces"].append(surface)

            self.fEntities["volumes"].append(volumes)

        return 
    
    def GetModelConfiguration(self) -> tuple[list[int], list[int], list[int], list[int], list[int], list[int]]:
        """
        Get the configuration of the model, classifying surfaces into different categories.

        Returns:
        --------
        tuple
            (domains, inletSurface, outletSurface, obstructionSurfaces, wallSurfaces, orificeSurfaces)
        """
        domains = []
        inletSurface = []
        outletSurface = []
        obstructionSurfaces = []
        wallSurfaces = []
        orificeSurfaces = []

        for v in self.fEntities["volumes"]:
            domains.append(v["id"])

            for surface in v["surfaces"]: 

                if surface["isOrifice"]:
                    orificeSurfaces.append(surface["id"])
                    continue

                match  surface["pMid"]:
                    case [0, 0, 0]:
                        inletSurface.append(surface["id"])

                    case [0, 0, z] if z == self.fTotalLength:
                        outletSurface.append(surface["id"])

                    case [0, 0, z]:
                        obstructionSurfaces.append(surface["id"])

                    case _:
                        wallSurfaces.append(surface["id"])

        if not domains:
            self.DebugStop("No volumes found")

        if not inletSurface:
            self.DebugStop("Inlet surface not found")
        elif len(inletSurface) > 1:
            self.DebugStop("Multiple inlet surfaces found")

        if not outletSurface:
            self.DebugStop("Outlet surface not found")
        elif len(outletSurface) > 1:
            self.DebugStop("Multiple outlet surfaces found")

        if not wallSurfaces:
            self.DebugStop("Wall surfaces not found")

        return (domains, inletSurface, outletSurface, obstructionSurfaces, wallSurfaces, orificeSurfaces)
    
    def CreatePhysicalGroups(self, physicalGroups:list[dict]) -> None:
        """
        Create physical groups in the model based on the provided configuration.

        Inputs:
        -------
        physicalGroups : dict
            Dictionary with keys as group names and values as lists of entity IDs.
            Each list element must have: ["entityDim", "entityTags", "MaterialID"] as mandatory keys. 
            The key "name" is optional.
        """
        keys = ["entityDim", "entityTags", "MaterialID"]
        if not all(all(key in phGr for key in keys) for phGr in physicalGroups):
            self.DebugStop(f"Physical groups must contain the following keys: {keys}")

        for phGr in physicalGroups:
            gmsh.model.addPhysicalGroup(phGr["entityDim"], phGr["entityTags"], phGr["MaterialID"], name=phGr["name"])

        return
    
    def Show(self) -> None:
        """
        Display the model using Gmsh's GUI.
        """
        gmsh.model.occ.synchronize()

        if '-nopopup' not in sys.argv:
            gmsh.fltk.run() 

        return
    
    def CreateConstantField(self, entitiesTags:list[int], meshSize:float, bigNumber:float = 1e12) -> int:
        """
        Defines the mesh constant field in a surface.

        Inputs:
        -------
        entitiesTags : list of int
            List of entity tags where the field will be applied.
        meshSize : float
            Desired mesh size at the specified entities.
        bigNumber : float
            A large number to represent "infinity" for mesh size away from the entities.

        Returns:
        --------
        int
            ID of the created field.
        """
        fieldOperator = gmsh.model.mesh.field 

        fieldID = fieldOperator.add("Constant")
        fieldOperator.set_number(fieldID, "IncludeBoundary", 1)
        fieldOperator.set_numbers(fieldID, "SurfacesList", entitiesTags)
        fieldOperator.set_number(fieldID, "VIn", meshSize)
        fieldOperator.set_number(fieldID, "VOut", bigNumber)

        gmsh.option.setNumber("Mesh.MeshSizeExtendFromBoundary", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromPoints", 0)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)

        return fieldID
    
    def SetMinimumMeshSize(self, fieldsID) -> None:
        """
        Sets the mesh size using the minimum value of each field provided.

        Inputs:
        -------
        fieldsID : list of int
            List of field IDs to be considered for mesh size determination.
        """
        minMeshSizeField = gmsh.model.mesh.field.add("Min")
        gmsh.model.mesh.field.setNumbers(minMeshSizeField, "FieldsList", fieldsID)
        gmsh.model.mesh.field.setAsBackgroundMesh(minMeshSizeField)

        return