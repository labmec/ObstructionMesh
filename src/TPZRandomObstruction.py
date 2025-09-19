"""
Class to create random circular obstructions on 
the module's front face

Created by Carlos Puga: 01/15/2024
"""

#%% ****************** 
#   IMPORTED MODULES
#   ******************
import gmsh
import random
import numpy as np
from datetime import datetime

from src.TPZModuleTypology import TPZModuleTypology
from src.TPZGmshToolkit import TPZGmshToolkit

#%% ****************** 
#   CLASS DEFINITION
#   ******************
class TPZRandomObstruction(TPZModuleTypology):
    """
    This class creates a random circular obstructions in the 
    middle of the front (positive direction of z axis) face.
    
    It inherits a base creator of typologies (TPZModuleTypology)
    to generates the module body and insert the obstruction.

    Fields: 
        - fObstructionRadius: size of the obstruction radius
        - fNumberOfObstructions: maximum number of obstructions
        - fObstructionCX: x coordinate to place the obstruction
        - fObstructionCY: y coordinate to place the obstruction
    """
#   ****************** 
#      INITIALIZOR
#   ******************  
    def __init__(self, length: float, lc: float, radius: float, obstructionRadius: float, nObstructions: int, seed: int = None) -> None:
        super().__init__(length=length, lc=lc, radius=radius)

        self.fObstructionRadius = obstructionRadius
        self.fNumberOfObstructions = nObstructions
        self.fSeed = seed
        self.fObstructionCX = 0.0
        self.fObstructionCY = 0.0

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

    def EuclideanDistance(self, xa: float, ya: float, xb: float, yb: float)->float:
        """
        Returns the euclidean distance between the points (xa, ya) and (xb, yb)
        """
        Xa = np.array([xa, ya])
        Xb = np.array([xb, yb])

        return np.linalg.norm(Xa - Xb)

    def GetObstructionDomain(self) -> list[float]:
        """
        Returns the domain range in which the obstructions can be inserted
        """
        return [.85*(self.fRadius - self.fObstructionRadius)] * 2

    def NoOverlappingCircles(self):
        """
        Returns a list containing the (x,y) coordinates of 'n_samples' random circles, with no overlapping between them. The range of the coordinates is within the ['domainX' x 'domainY'] values and the circles have radius = 'radius'. In case of cylindrical domains, it is also verified whether the coordinates fit the domain or not.

        Return: circleList
        """
        counter = 0
        circleList = []

        domX, domY = self.GetObstructionDomain()

        random.seed(self.fSeed) if self.fSeed is not None else random.seed(datetime.now().timestamp())

        while len(circleList) < self.fNumberOfObstructions and counter < 1000:
            counter += 1

            xMult = (-1) ** random.randint(0, 1)
            yMult = (-1) ** random.randint(0, 1)

            x = (xMult) * random.uniform(0, domX)
            y = (yMult) * random.uniform(0, domY)

            if not any((Xcenter, Ycenter) for Xcenter, Ycenter in circleList if self.EuclideanDistance(x, y, Xcenter, Ycenter) < 2.5 * self.fObstructionRadius):
                if (x) ** 2 + (y) ** 2 < (.75 * self.fRadius) ** 2: circleList.append((x, y))

        return circleList

#   ****************** 
#        OBSTRUCTION
#   ******************  
    def ObstructionPoints(self)->tuple[int]:
        """
        Returns the points belonging to the obstruction
        """
        cx, cy = self.fObstructionCX, self.fObstructionCY
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

    def ObstructionArcs(self, points: list[int])->tuple[int]:
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

        obArcs = TPZGmshToolkit.CreateCircleArcs(arcPoints)

        gmsh.model.occ.remove([(0, p1)])

        return obArcs

    def CreateObstruction(self)->int:
        """
        Returns the obstruction surface id
        """
        originX = self.fObstructionCX
        originY = self.fObstructionCY
        
        obstruction_coordinates = self.NoOverlappingCircles()

        obstructions = []

        for coordinates in obstruction_coordinates:
            dx, dy = coordinates

            self.fObstructionCX = originX + dx
            self.fObstructionCY = originY + dy

            obPoints = self.ObstructionPoints()
            obArc = self.ObstructionArcs(obPoints)
            
            curve = gmsh.model.occ.addCurveLoop(obArc)
            
            obstructionSurface = gmsh.model.occ.addPlaneSurface([curve])

            obstructions.append(obstructionSurface)

        return obstructions
    
    def Move(self, dx:float, dy:float, dz:float):
        """
        Moves the module (dx, dy, dz)
        """
        gmsh.model.occ.translate([ (3,self.fVolumeID)], dx, dy, dz)