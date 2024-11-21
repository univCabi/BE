from dataclasses import dataclass

@dataclass
class CabinetFloorInputDTO:
    building: str
    floor: int