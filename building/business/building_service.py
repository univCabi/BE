
from building.persistence.building_repository import BuildingRepository

building_repository = BuildingRepository()

class BuildingService:

    def get_building(self, building : str, floor : int):
        return building_repository.get_building(building, floor)

    #def get_buildings(self):
    #    return self.building_repository.get_buildings()

    #def add_building(self, building):
    #    return self.building_repository.add_building(building)

    #def update_building(self, building):
    #    return self.building_repository.update_building(building)

    #def delete_building(self, building_id):
    #    return self.building_repository.delete_building(building_id)