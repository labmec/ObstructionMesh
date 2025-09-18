"""
Class to create a simple circular obstruction on 
the module's front face

Created by Carlos Puga: 01/13/2024
"""

#%% ****************** 
#   IMPORTED MODULES
#   ******************
import gmsh

from src.TPZModuleTypology import TPZModuleTypology
from src.TPZGmshToolkit import TPZGmshToolkit

#%% ****************** 
#   CLASS DEFINITION
#   ******************
class TPZSimpleObstruction(TPZModuleTypology):
    """
    This class creates a simple circular obstruction in the 
    middle of the front (positive direction of z axis) face.
    
    It inherits a base creator of typologies (TPZModuleTypology)
    to generates the module body and insert the obstruction.

    Fields: 
        - obstruction_radius: size of the obstrcution radius
        - obstruction_cx: x coordinate to place the obstruction
        - obstruction_cy: y coordinate to place the obstruction
        - id: obstruction volume's identification (provided by the class itself)
    """
#   ****************** 
#      INITIALIZER
#   ******************  
    def __init__(self, length:float, lc:float, radius:float, obstructionRadius:float) -> None: 
        super().__init__(length=length, lc=lc, radius=radius)

        self.fObstructionRadius: float = obstructionRadius
        self.fObstructionSurface:int = -1
        self.fObstructionCX:float = -1.
        self.fObstructionCY:float = -1.

        self.DeactivateAttr()

        self.__post_init__()

        return

    def __post_init__(self) -> None:
        self.CreateDomain()
        
        return

#   ****************** 
#        METHODS
#   ******************  
    def CheckTypology(self) -> None:
        """
        Checks whether the module's typology and geometry 
        """
        self.fObstructionCX = 0
        self.fObstructionCY = 0

        if self.fObstructionRadius > self.fRadius:
            self.DebugStop('ERROR: obstruction radius not compatible with cylinder dimensions!')

        self.CreateCylinder()

        return

    def CreateDomain(self) -> None:
        """
        Generates the module with a circular obstruction on gmsh.
        """
        self.CheckTypology()

        # creating the obstruction on surface obstruction_face
        obstruction = self.CreateObstruction()

        # calculating the boolean difference between the domain and the obstruction faces  
        newSurfaces = gmsh.model.occ.fragment([(2, self.fObstructionSurface)], [(2, obstruction)])

        self.fObstructionSurface = obstruction
        domainSurfaces = self.fSurfaces + [surface[1] for surface in newSurfaces[0]]

        # creating the module volume
        surfaceLoop = gmsh.model.occ.addSurfaceLoop(domainSurfaces)
        self.fVolumeID = gmsh.model.occ.addVolume([surfaceLoop])

        return

#   ****************** 
#        OBSTRUCTION
#   ******************  
    def ObstructionPoints(self) -> list[int]:
        """
        Returns the points belonging to the obstruction
        """
        cx, cy = self.fObstructionCX, self.fObstructionCY
        r = self.fObstructionRadius
        l = self.fLength
        lc = self.fLC

        points_coord = [
            [cx, cy, l],
            [cx + r, cy, l],
            [cx, cy + r, l],
            [cx - r, cy, l],
            [cx, cy - r, l]
        ]

        return TPZGmshToolkit.CreatePoints(points_coord, lc)

    def ObstructionArcs(self, p1:int, p2:int, p3:int, p4:int, p5:int) -> tuple[int]:
        """
        Returns the lines belonging to the obstruction
        """
        arcPoints = [
            [p2, p1, p3],
            [p3, p1, p4],
            [p4, p1, p5],
            [p5, p1, p2]
        ]

        obArcs = TPZGmshToolkit.CreateCircleArcs(arcPoints)

        gmsh.model.occ.remove([(0, p1)]) # center of obstruction circle

        return obArcs

    def CreateObstruction(self) -> int:
        """
        Returns the obstruction surface id
        """
        obPoints = self.ObstructionPoints()
        obArc = self.ObstructionArcs(*obPoints)

        c1 = gmsh.model.occ.addCurveLoop(obArc)
        
        obstructionSurface = gmsh.model.occ.addPlaneSurface([c1])

        return obstructionSurface
    
    def Move(self, dx:float, dy:float, dz:float):
        """
        Moves the module (dx, dy, dz)
        """
        gmsh.model.occ.translate([ (3, self.fVolumeID)], dx, dy, dz)

        return