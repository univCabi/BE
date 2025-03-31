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
    
    def get_buildings_with_floors(self, building_name, floor_list):
        """
        건물명과 층 리스트를 받아 해당 건물의 존재하는 층 정보를 반환
        """
        buildings_qs = buildings.objects.filter(
            name=building_name,
            floor__in=floor_list
        )
        
        if not buildings_qs.exists():
            raise BuildingNotFoundException()
            
        # 요청한 층 중 실제 존재하는 층만 필터링
        existing_floors = set(buildings_qs.values_list('floor', flat=True))
        non_existing_floors = set(floor_list) - existing_floors

        if non_existing_floors:
            raise BuildingNotFoundException(building=building_name, floor=non_existing_floors.pop())
        
        return buildings_qs