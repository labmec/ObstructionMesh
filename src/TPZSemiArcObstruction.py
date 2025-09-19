"""
Class to create obstruction with semi arcs on 
the module's front face

Created by Carlos Puga: 01/15/2024
"""

#%% ****************** 
#   IMPORTED MODULES
#   ******************
from typing import ClassVar
import numpy as np
import gmsh

from src.TPZModuleTypology import TPZModuleTypology
from src.TPZGmshToolkit import TPZGmshToolkit

#%% ****************** 
#   CLASS DEFINITION
#   ******************
class TPZSemiArcObstruction(TPZModuleTypology):
    """
    This class creates a obstruction with semi arcs in the 
    middle of the front (positive direction of z axis) face.
    
    It inherits a base creator of typologies (TPZModuleTypology)
    to generates the module body and insert the obstruction.

    Fields: 
        - fObstructionRadius: distance from the center of the module to the semi arcs
        - fObstructionCX: x coordinate to place the obstruction
        - fObstructionCY: y coordinate to place the obstruction
    """
#   ****************** 
#      INITIALIZOR
#   ******************  
    multiplicativeConstant:ClassVar = 1.2

    def __init__(self, length:float, lc:float, radius:float, obstructionRadius:float) -> None:
        super().__init__(length=length, lc=lc, radius=radius)

        self.fObstructionRadius: float = obstructionRadius
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
    def CheckTypology(self) -> None:
        """
        Checks whether the module is rectangular or circular 
        """
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
        newSurfaces = gmsh.model.occ.fragment([(2, self.fObstructionSurface)], [(2, obs) for obs in obstruction])

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
        cons = self.multiplicativeConstant

        dx = r * np.cos(np.deg2rad(60))
        dy = r * np.sin(np.deg2rad(60))

        pointsCoord = [
            [cx, cy, l],

            [cx + dx, cy + dy, l],
            [cx + cons * dx, cy + cons * dy, l],
            [cx - cons * dx, cy + cons * dy, l],
            [cx - dx, cy + dy, l],
            
            [cx + dx, cy - dy, l],
            [cx + cons * dx, cy - cons * dy, l],
            [cx - dx, cy - dy, l],
            [cx - cons * dx, cy - cons * dy, l]
        ]

        dx = r * np.cos(np.deg2rad(30))
        dy = r * np.sin(np.deg2rad(30))

        pointsCoord += [
            [cx + dx, cy + dy, l],
            [cx + cons * dx, cy + cons * dy, l],
            [cx + dx, cy - dy, l],
            [cx + cons * dx, cy - cons * dy, l],

            [cx - dx, cy + dy, l],
            [cx - cons * dx, cy + cons * dy, l],
            [cx - dx, cy - dy, l],
            [cx - cons * dx, cy - cons * dy, l]
        ]

        return TPZGmshToolkit.CreatePoints(pointsCoord, lc)

    def ObstructionArcs(self, points: list[int])->list[int]:
        """
        Returns the lines belonging to the obstruction
        """
        p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16, p17 = points

        linePoints = [
            [[p2, p3], [p3, p1, p4], [p4, p5], [p5, p1, p2]],
            [[p7, p6], [p6, p1, p8], [p8, p9], [p9, p1, p7]],
            [[p12, p13], [p13, p1, p11], [p11, p10], [p10, p1, p12]],
            [[p14, p15], [p15, p1, p17], [p17, p16], [p16, p1, p14]]
        ]

        obArcs = []
        for group in linePoints:
            g1, g2, g3, g4 = group
            
            arc = []
            arc.append(gmsh.model.occ.addLine(g1[0], g1[1]))
            arc.append(gmsh.model.occ.addCircleArc(g2[0], g2[1], g2[2]))
            arc.append(gmsh.model.occ.addLine(g3[0], g3[1]))
            arc.append(gmsh.model.occ.addCircleArc(g4[0], g4[1], g4[2]))

            obArcs.append(arc)

        gmsh.model.occ.remove([(0, p1)])

        return obArcs

    def CreateObstruction(self)->int:
        """
        Returns the obstruction surface id
        """
        obPoints = self.ObstructionPoints()
        obArcs = self.ObstructionArcs(obPoints)
        
        obstruction = []
        for arc in obArcs:
            curve = gmsh.model.occ.addCurveLoop(arc)
        
            obstructionSurface = gmsh.model.occ.addPlaneSurface([curve])
            obstruction.append(obstructionSurface)

        return obstruction
    
    def Move(self, dx:float, dy:float, dz:float):
        """
        Moves the module (dx, dy, dz)
        """
        gmsh.model.occ.translate([ (3, self.fVolumeID)], dx, dy, dz)
