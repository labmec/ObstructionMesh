"""
Basic data structure with controlled attribute setting and print methods.

Created by Carlos Puga: 09/20/2025
"""
from dataclasses import dataclass, field
from typing import Any
from abc import ABCMeta

@dataclass
class TPZBasicDataStructure(metaclass=ABCMeta):
    fDeactivateAttr: bool = field(default=False)
    
    def DeactivateAttr(self) -> None:
        self.fDeactivateAttr = True

    def ActivateAttr(self) -> None:
        self.fDeactivateAttr = False

    def __setattr__(self, name: str, value: Any) -> None:
        if not self.fDeactivateAttr:
            super().__setattr__(name, value)

        else:
            if hasattr(self, name):
                return super().__setattr__(name, value)
            
            else:
                self.DebugStop(f"Cannot add new attribute '{name}' when attributes are deactivated.")
            
    def __str__(self):
        fields = ', '.join(f"{key}={value}" for key, value in self.__dict__.items())
        return f"{self.__class__.__name__}({fields})"
    
    #   ****************** 
    #        METHODS
    #   ******************  
    def DebugStop(self, message='') -> None:
        raise ValueError(message + ' YOUR CHANCE TO PUT A BREAK POINT HERE')