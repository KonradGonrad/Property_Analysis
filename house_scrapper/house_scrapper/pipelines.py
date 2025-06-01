# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from .items import OtodomScrapperResult
from .settings import SCRAP_PHOTOS, SCRAP_DESCRIPTION, SCRAP_HISTORY, SCRAP_NUMBER, SCRAP_OTHER
from typing import List

class HouseScrapperPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        result = OtodomScrapperResult()

        if SCRAP_OTHER:
            if SCRAP_NUMBER:
                result['number'] = self.parse_generic(adapter.get('number'), 'number')

            if SCRAP_DESCRIPTION:
                result['description'] = self.parse_generic(adapter.get('description'), 'description')

            if SCRAP_HISTORY:
                result['history'] = self.parse_generic(adapter.get('history'), 'history')
                result['likes'] = self.parse_generic(adapter.get('likes'), 'likes')
                result['views'] = self.parse_generic(adapter.get('views'), 'views')

            if SCRAP_PHOTOS:
                result['num_photo'] = self.parse_generic(adapter.get('num_photo'), 'num_photo')

        # Generic values
        generic = ['listing_id', 'scraped_at', 'listing_type', 'price',
                   'floor', 'num_rooms', 'area', 'rent', 'deposit',
                   'elevator', 'building_year', 'link']
        
        for element_name in generic:
            element = adapter.get(element_name)
            result[element_name] = self.parse_generic(element, element_name)

        # category
        category = ['finish_level', 'heating', 'building_type', 
                    'building_material', 'windows_type']

        for element_name in category:
            element = adapter.get(element_name)
            result[element_name] = self.parse_category(element, element_name)

        # Category_lists
        category_list = ['additional', 'equipment', 'media', 'security']
        
        for element_name in category_list:
            element = adapter.get(element_name)
            result[element_name] = self.parse_category_list(element, element_name)

        # Location
        result['street'], result['estate'], result['district'], result['city'], result['province'] = self.parse_location(adapter.get('location'))
        
        return result

    @staticmethod
    def parse_generic(element, element_name: str):
        if element in ['brak informacji', None, 'brak']:
            return None
    
        if element_name in ['floor']:
            if element == '> 10': # Problematic case
                return int(10)
            return 0 if (first := element.split("/")[0]) == 'parter' else int(first)
        
        if element_name in ['listing_id', 'building_year', 'num_rooms', 'description', 'likes', 'views']:
            return int(element)
        
        if element_name in ['rent']:
            return float(element.split("zł/miesiąc")[0].replace(" ", "").replace(",", "."))

        if element_name in ['scraped_at', 'listing_type', 'link', 'number', 'history', 'active']:
            return element
        
        if element_name in ['area']:
            return float(element)
        
        if element_name in ['price', 'deposit']:
            return float(element.split("zł")[0].replace(" ", "").replace(",", "."))
        
        if element_name in ['num_photo']:
            return int(element[element.find('(')+1:element.find(")")])
        
        if element_name in ['elevator']:
            return True if element == 'tak' else False

    @staticmethod
    def parse_category(element: str, mapping_name: str):
        mappings = {
            'finish_level': {
                'do zamieszkania': 'ready_to_move_in',
                'do wykończenia': 'to_be_finished',
                'do remontu': 'to_renovate'
            },
            'heating': {
                'miejskie': 'district',
                'inne': 'other',
                'gazowe': 'gas',
                'elektryczne': 'electric',
                'kotłownia': 'boiler_room'
            },
            'building_type': {
                'blok': 'block',
                'kamienica': 'tenement_house',
                'apartamentowiec': 'apartment_building',
                'loft': 'loft',
                'dom wolnostojący': 'detached_house',
                'plomba': 'infill',
                'szeregowiec': 'terraced_house'
            },
            'building_material': {
                'cegła': 'brick',
                'wielka płyta': 'prefab',
                'pustak': 'hollow_block',
                'beton': 'concrete',
                'inny': 'other',
                'beton komórkowy': 'aerated_concrete',
                'silikat': 'silicate',
                'żelbet': 'reinforced_concrete'
            },
            'windows_type': {
                'plastikowe': 'plastic',
                'drewniane': 'wooden',
                'aluminiowe': 'aluminium'
            }
        }
        if element in ['brak informacji', None, 'brak']:
            return None
        mapping = mappings.get(mapping_name, {})
        return mapping.get(element.strip(), element.strip())

    @staticmethod
    def parse_category_list(element: List, mapping_name:str):
        mappings = {'equipment' : {
            'meble': 'furniture',
            'pralka': 'washing_machine',
            'zmywarka': 'dishwasher',
            'lodówka': 'fridge',
            'kuchenka': 'stove',
            'piekarnik': 'oven',
            'telewizor': 'tv',
            'klimatyzacja': 'air_conditioning',
            },
                    'additional': {
                'balkon': 'balcony',
                'garaż/miejsce parkingowe': 'garage',
                'pom. użytkowe': 'utility_room',
                'piwnica': 'basement',
                'oddzielna kuchnia': 'separate_kitchen',
                'ogródek': 'garden',
                'taras': 'patio',
                'Wynajmę również studentom': 'students_allowed',
                'tylko dla niepalących': 'non_smokers_only',
                'dwupoziomowe': 'duplex',
            },
                    'security': {"drzwi / okna antywłamaniowe": 'anti-burglary_doors_windows',
                                "domofon / wideofon": 'entry_phone',
                                "system alarmowy": 'alarm_system',
                                "rolety antywłamaniowe": "anti-burglary_blinds"},
                    'media': {'telewizja kablowa': 'tv',
                              'internet': 'internet',
                              'telefon': 'phone'}
            }
        if element in ['brak informacji', None, 'brak']:
            return None
        mapping = mappings.get(mapping_name, {})
        return [mapping.get(item.strip(), item.strip()) for item in element]

    @staticmethod    
    def parse_location(element: str):
        """
        Function return street, estate, district, city and province for location that have at least 4 
        """
        location_splitted = element.split(",")

        street = location_splitted[0] if len(location_splitted) in [5, 6] else None
        estate = location_splitted[-4] if len(location_splitted) in [4, 5, 6] else None
        district = location_splitted[-3]
        city = location_splitted[-2]
        province = location_splitted[-1]

        return street, estate, district, city, province

    @staticmethod
    def parse_history(element):
        """
        Have no idea actually what can i do with this, so I'll just leave this for now
        """
        pass

class SaveToPostgreSQL:
    def __init__(self):
        pass
