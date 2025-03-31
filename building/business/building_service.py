
from building.persistence.building_repository import BuildingRepository

building_repository = BuildingRepository()

class BuildingService:

    def get_building(self, building : str, floor : int):
        return building_repository.get_building(building, floor)

    def get_buildings_with_floors(self, building_name, floor_list):
        return building_repository.get_buildings_with_floors(building_name, floor_list)