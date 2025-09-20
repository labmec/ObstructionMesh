"""
Class to create several circular obstructions on 
the module's front face

Created by Carlos Puga: 01/15/2024
"""

#%% ****************** 
#   IMPORTED MODULES
#   ******************
import numpy as np
import gmsh

from src.TPZModuleTypology import TPZModuleTypology
from src.TPZGmshToolkit import TPZGmshToolkit

#%% ****************** 
#   CLASS DEFINITION
#   ******************
class TPZMultipleObstruction(TPZModuleTypology):
    """
    This class creates several circular obstructions in the 
    middle of the front (positive direction of z axis) face.
    
    It inherits a base creator of typologies (TPZModuleTypology)
    to generates the module body and insert the obstruction.

    Fields: 
        - fObstructionRadius: size of the obstruction radius
        - fObstructionDistance: distance from the center of the domain
        - fObstructionCX: x coordinate to place the obstruction
        - fObstructionCY: y coordinate to place the obstruction
    """
#   ****************** 
#      INITIALIZOR
#   ******************  
    def __init__(self, length:float, lc:float, radius:float, obstructionRadius:float, obstructionDistance:float) -> None:
        super().__init__(length=length, lc=lc, radius=radius)
        
        self.fObstructionRadius: float = obstructionRadius
        self.fObstructionDistance: float = obstructionDistance
        self.fObstructionCX: float = 0.
        self.fObstructionCY: float = 0.

        self.DeactivateAttr()

        self.__post_init__()

        return

    def __post_init__(self) -> None:
        self.CreateDomain()
        return

#   ****************** 
#        METHODS
#   ******************  
    def CheckTypology(self)->None:

        if (self.fObstructionRadius + self.fObstructionDistance) > self.fRadius:
            self.DebugStop('ERROR: obstruction radius not compatible with cylinder dimensions!')

        self.CreateCylinder()

        return

    def CreateDomain(self) -> None:
        """
        Generates the module with a circular obstruction on gmsh.
        """
        self.CheckTypology()

        # creating the obstruction on surface obstruction_face
        obstructions = self.CreateObstruction()

        # calculating the boolean difference between the domain and the obstruction faces  
        newSurfaces = gmsh.model.occ.fragment([(2, self.fObstructionSurface)], [(2, obs) for obs in obstructions])

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
        cx = self.fObstructionCX
        cy = self.fObstructionCY
        r = self.fObstructionRadius
        l = self.fLength
        lc = self.fLC

        pointCoords = [
            [cx, cy, l],
            [cx + r, cy, l],
            [cx, cy + r, l],
            [cx - r, cy, l],
            [cx, cy - r, l]
        ]

        return TPZGmshToolkit.CreatePoints(pointCoords, lc)

    def ObstructionArcs(self, points: list[int]) -> list[int]:
        """
        Returns the lines belonging to the obstruction
        """
        p1, p2, p3, p4, p5 = points

        arcPoints = [
            [p2, p1, p3],
            [p3, p1, p4],
            [p4, p1, p5],
            [p5, p1, p2]
        ]

        ob_arcs = TPZGmshToolkit.CreateCircleArcs(arcPoints)

        gmsh.model.occ.remove([(0, p1)])

        return ob_arcs

    def CreateObstruction(self) -> list[int]:
        """
        Returns the obstruction surface id
        """
        angles = [0,45,90,135,180,225,270,315]
        
        originX = self.fObstructionCX
        originY = self.fObstructionCY
        r = self.fObstructionDistance

        multipleObs = []

        centerPoints = self.ObstructionPoints()
        centerArcs = self.ObstructionArcs(centerPoints)
        centerCurves = gmsh.model.occ.addCurveLoop(centerArcs)        
        centerSurface = gmsh.model.occ.addPlaneSurface([centerCurves])

        multipleObs.append(centerSurface)

        for theta in angles:
            self.fObstructionCX = r*np.cos(np.deg2rad(theta)) + originX
            self.fObstructionCY = r*np.sin(np.deg2rad(theta)) + originY

            points = self.ObstructionPoints()
            arcs = self.ObstructionArcs(points) 
            curves = gmsh.model.occ.addCurveLoop(arcs)
            circleSurface = gmsh.model.occ.addPlaneSurface([curves])

            multipleObs.append(circleSurface)

        return multipleObs