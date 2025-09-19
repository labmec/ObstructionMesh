"""
Class to create a cross obstruction on 
the module's front face

Created by Carlos Puga: 01/15/2024
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
class TPZCrossObstruction(TPZModuleTypology):
    """
    This class creates a cross obstruction in the 
    middle of the outlet face.
    
    It inherits a base creator of typologies (TPZModuleTypology)
    to generates the module body and insert the obstruction.

    Fields: 
        - fObstructionWidth: obstruction width
        - fObstructionHeight: obstruction height
        - fRadius: cross curved edge's radius 
        - fObstructionCX: x coordinate to place the obstruction
        - fObstructionCY: y coordinate to place the obstruction
        - fCrossTipRadius: radius of the cross tips

    """
#   ****************** 
#      INITIALIZOR
#   ******************  
    def __init__(self, length:float, lc:float, radius:float, obstructionWidth:float=0.5, obstructionHeight:float=0.5) -> None:
        super().__init__(length=length, lc=lc, radius=radius)

        self.fObstructionWidth: float = obstructionWidth
        self.fObstructionHeight: float = obstructionHeight
        self.fRadius: float = radius
        self.fCrossTipRadius: float = 0.1*obstructionWidth
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
        if (self.fObstructionWidth + self.fCrossTipRadius) > self.fRadius or (self.fObstructionHeight + self.fCrossTipRadius) > self.fRadius:
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
        dx, dy = self.fObstructionWidth, self.fObstructionHeight
        l = self.fLength
        r = self.fCrossTipRadius
        lc = self.fLC

        pointCoords = [
            [cx + dx, cy, l],
            [cx + dx, cy - r, l],
            [cx + dx + r, cy, l],
            [cx + dx, cy + r, l],

            [cx, cy + dy, l],
            [cx + r, cy + dy, l],
            [cx, cy + dy + r, l],
            [cx - r, cy + dy, l],

            [cx - dx, cy, l],
            [cx - dx, cy + r, l],
            [cx - dx - r, cy, l],
            [cx - dx, cy - r, l],

            [cx, cy - dy, l],
            [cx - r, cy - dy, l],
            [cx, cy - dy - r, l],
            [cx + r, cy - dy, l],

            [cx + r, cy + r, l],
            [cx - r, cy + r, l],
            [cx - r, cy - r, l],
            [cx + r, cy - r, l]
        ]

        return TPZGmshToolkit.CreatePoints(pointCoords, lc)

    def ObstructionArcs(self, points:list[int]) -> list[int]:
        """
        Returns the lines belonging to the obstruction
        """
        p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16, p17, p18, p19, p20 = points

        points = [
            {"arcs": [[p2, p1, p3], [p3, p1, p4]], 
             "lines": [[p4, p17], [p17, p6]]},

            {"arcs":[[p6, p5, p7], [p7, p5, p8]],
             "lines": [[p8, p18], [p18, p10]]},

            {"arcs": [[p10, p9, p11], [p11, p9, p12]],
             "lines": [[p12, p19], [p19, p14]]},

            {"arcs": [[p14, p13, p15], [p15, p13, p16]],
             "lines": [[p16, p20], [p20, p2]]} 
        ]

        obsLines = []
        for group in points:
            gpArcs = group["arcs"]
            gpLines = group["lines"]

            a = TPZGmshToolkit.CreateCircleArcs(gpArcs)
            l = TPZGmshToolkit.CreateLines(gpLines)
            
            obsLines += a
            obsLines += l

        gmsh.model.occ.remove([(0, p1)])
        gmsh.model.occ.remove([(0, p5)])
        gmsh.model.occ.remove([(0, p9)])
        gmsh.model.occ.remove([(0, p13)])

        return obsLines

    def CreateObstruction(self) -> int:
        """
        Returns the obstruction surface id
        """
        points = self.ObstructionPoints()
        curves = self.ObstructionArcs(points)        
        c1 = gmsh.model.occ.addCurveLoop(curves)
        
        return gmsh.model.occ.addPlaneSurface([c1])
    
    def Move(self, dx:float, dy:float, dz:float) -> None:
        """
        Moves the module (dx, dy, dz)
        """
        gmsh.model.occ.translate([ (3,self.fVolumeID)], dx, dy, dz)
        return