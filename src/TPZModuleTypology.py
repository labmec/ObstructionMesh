"""
Class to create modules of length 'size'

Created by Carlos Puga: 01/13/2024
"""
#%% ****************** 
#   IMPORTED MODULES
#   ******************
import gmsh

from src.TPZGmshToolkit import TPZGmshToolkit
from src.TPZBasicDataStructure import TPZBasicDataStructure

#%% ****************** 
#   CLASS DEFINITION
#   ******************
class TPZModuleTypology(TPZBasicDataStructure):
    """
    Base class used to generate the module in which 
    the obstruction will be inserted. Every module is 
    created in the origin of cartesian plan

    Fields:
        - length: module length
        - lc: mesh size (gmsh requirement)
        - points: module's points (class provides it)
        - lines: module's lines (class provides it)
        - curves: module's curve loops (class provides it)
        - surfaces: module's surfaces, expcept by the one on which
         the obstruction will be inserted (class provides it)
        - obstructionSurface: module's surface on which the obstruction 
        will be inserted
        - volumeID: module's volume identification (provided by the class itself)
    """
#   ****************** 
#      INITIALIZOR
#   ******************  
    def __init__(self, length: float, lc: float, radius:float) -> None:
            self.fLength = length
            self.fLC = lc
            self.fRadius = radius
            self.fPoints = []
            self.fArcs = []
            self.fCurves = []
            self.fSurfaces = []
            self.fObstructionSurface = -1
            self.fVolumeID = -1

            return 


#   ****************** 
#        METHODS
#   ******************  
    def DebugStop(self, message='') -> None:
        raise ValueError(message + ' YOUR CHANCE TO PUT A BREAK POINT HERE')

#   ****************** 
#       CYLINDER
#   ******************  
    def CylinderPoints(self) -> None:   
        """
        Creates the points of the cylinder inlet surface
        """
        radius = self.fRadius

        pointsCoords = [
            [0, 0, 0],
            [radius, 0, 0],
            [0, radius, 0],
            [-radius, 0, 0],
            [0, -radius, 0],

        ]

        self.fPoints = TPZGmshToolkit.CreatePoints(pointsCoords, self.fLC)

        return 

    def CylinderArcs(self) -> None:
        """
        Creates the arcs of the cylinder inlet surface
        """
        p1, p2, p3, p4, p5 = self.fPoints

        linePoints = [
            [p2, p1, p3],
            [p3, p1, p4],
            [p4, p1, p5],
            [p5, p1, p2],
        ]

        self.fArcs = TPZGmshToolkit.CreateCircleArcs(linePoints)

        gmsh.model.occ.remove([(0, p1)]) # center of the back circle

        return 

    def CylinderCurves(self) -> None:
        """
        Creates the cylinder inlet surface curve loop
        """
        self.fCurves.append(gmsh.model.occ.addCurveLoop(self.fArcs))

        return 

    def CylinderSurfaces(self) -> None:
        """
        Creates the cylinder surfaces
        """
        back = gmsh.model.occ.addPlaneSurface(self.fCurves)
        
        front = gmsh.model.occ.copy([(2, back)])[0][1]
        gmsh.model.occ.translate([(2, front)], 0, 0, self.fLength)

        contour = gmsh.model.occ.addThruSections([back, front], makeSolid=False)

        self.fSurfaces = [back] + [c[1] for c in contour]
        self.fObstructionSurface = front

        return 


    def CreateCylinder(self)->None:
        """
        Create a cylinder with 'radius'
        """
        self.CylinderPoints()
        self.CylinderArcs()
        self.CylinderCurves()
        self.CylinderSurfaces()
