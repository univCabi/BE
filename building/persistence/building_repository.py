from building.models import buildings
from building.exceptions import BuildingNotFoundException

class BuildingRepository :
    def get_building(self, building : str, floor : int):
        building = buildings.objects.filter(
            name=building,
            floor=floor).first()

        if not building:
            raise BuildingNotFoundException(building=building, floor=floor)
        return building