# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from .settings import SCRAP_PHOTOS, SCRAP_DESCRIPTION, SCRAP_HISTORY, SCRAP_NUMBER, SCRAP_OTHER
from typing import List
from house_scrapper.items import *
import psycopg2
from data.queries import ListingQuerries

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

class ProcessToSQL:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        listing_id = adapter.get('listing_id')
        scraped_at = adapter.get('scraped_at')

        #SQL Tables
        db_tables = DbTablesItem()

        # === Listing - main table ===
        db_tables['listing'] = ListingsItem(
            listing_id = listing_id,
            listing_type = adapter.get('listing_type'),
            len_description = adapter.get('description'),
            num_photo = adapter.get('num_photo'),
            active = adapter.get('active'),
            link = adapter.get('link'),
            phone_number = adapter.get('number')
        )

        # === Listing Multi columns ===
        # [listing_media, listing_additional, listing_security, listing_equipment]
        db_tables['listing_equipment'] = ListingEquipmentItem(
            listing_id = listing_id,
            value = adapter.get('equipment')
        )
        db_tables['listing_security'] = ListingSecurityItem(
            listing_id = listing_id,
            value = adapter.get('security')
        )
        db_tables['listing_additional'] = ListingAdditionalItem(
            listing_id = listing_id,
            value = adapter.get('additional')
        )
        db_tables['listing_media'] = ListingMediaItem(
            listing_id = listing_id,
            value = adapter.get('media')
        )

        # === Listing Features ===
        db_tables['listing_features'] = ListingsFeaturesItem(
            listing_id = listing_id,
            floor = adapter.get('floor'),
            num_rooms = adapter.get('num_rooms'),
            area = adapter.get('area'),
            elevator = adapter.get('elevator')
        )

        # === Statistic table ===
        db_tables['listing_stats'] = ListingStatsItem(
            listing_id = listing_id,
            scraped_at = scraped_at,
            views = adapter.get('views'),
            likes = adapter.get('likes')
        )

        # === Location table ===
        db_tables['location'] = LocationItem(
            listing_id = listing_id,
            street = adapter.get('street'),
            estate = adapter.get('estate'),
            district = adapter.get('district'),
            city = adapter.get('city'),
            province = adapter.get('province')
        )

        # === Price History table ===
        db_tables['price_history'] = PriceHistoryItem(
            listing_id = listing_id,
            scraped_at = scraped_at,
            price = adapter.get('price'),
            rent = adapter.get('rent'),
            deposit = adapter.get('deposit')
        )

        #=== Building Features table ===
        db_tables['building_features'] = BuildingFeaturesItem(
            listing_id = listing_id,
            building_material = adapter.get('building_material'),
            building_type = adapter.get('building_type'),
            building_year = adapter.get('building_year'),
            finish_level = adapter.get('finish_level'),
            heating = adapter.get('heating'),
            windows_type = adapter.get('windows_type')
        )

        return db_tables

class SaveToPostgreSQL:
    def __init__(self, db_settings):
        self.db_settings = db_settings
        self.conn = None
        self.cur = None

    @classmethod
    def from_crawler(cls, crawler):
        db_settings = {
            'host': crawler.settings.get('DB_HOST'),
            'port': crawler.settings.get('DB_PORT'),
            'user': crawler.settings.get('DB_USER'),
            'dbname': crawler.settings.get('DB_NAME'),
            'password': crawler.settings.get('DB_PASSWORD')
        }
        return cls(db_settings)

    def open_spider(self, spider):
        self.conn = psycopg2.connect(**self.db_settings) # ** - unpacking the dict contents
        self.cur = self.conn.cursor() 

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        list_keys = ['listing_additional', 'listing_media', 'listing_security', 'listing_equipment']
        for key, value in adapter.items():
            if key in list_keys:
                query, params = ListingQuerries.insert_list_values(table_name=key, values=value, column_name='value')
                self.cur.executemany(query, params)
            else:
                query, params = ListingQuerries.insert(key=key, values=value)
                self.cur.execute(query, params)
            self.conn.commit()

        return item


    def close_spider(self, spider):
        self.cur.close()
        self.conn.close()
        