"""
Class to create a module without obstructions

Created by Carlos Puga: 01/13/2024
"""
#%% ****************** 
#   IMPORTED MODULES
#   ******************
import gmsh

from src.TPZModuleTypology import TPZModuleTypology

#%% ****************** 
#   CLASS DEFINITION
#   ******************
class TPZNoObstruction(TPZModuleTypology):
    """
    This class creates a module without obstrucitons
    
    It inherits a base creator of typologies (TPZModuleTypology)
    to generates the module body and insert the obstruction.

    Fields: 
        - length: module length
        - lc: mesh size (gmsh requirement)
    """
#   ****************** 
#      INITIALIZOR
#   ******************  
    def __init__(self, length:float, lc:float, radius:float) -> None:
        super().__init__(length=length, lc=lc, radius=radius)

        self.__post_init__()

        return

    def __post_init__(self) -> None:
        self.CreateDomain()
        return

#   ****************** 
#        METHODS
#   ******************  
    def CreateDomain(self) -> None:
        """
        Generates the module with a circular obstruction on gmsh.
        """
        self.CreateCylinder()

        domainSurfaces = self.fSurfaces + [self.fObstructionSurface]

        # creating the module volume
        surfaceLoop = gmsh.model.occ.addSurfaceLoop(domainSurfaces)
        self.fVolumeID = gmsh.model.occ.addVolume([surfaceLoop])

        return