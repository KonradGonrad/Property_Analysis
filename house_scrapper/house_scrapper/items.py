# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class OtodomScrapperItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    link = scrapy.Field() # For checking if everything is scraped corectlly
    listing_id = scrapy.Field() # int
    location = scrapy.Field() # Need to be changed in pipelines
    scraped_at = scrapy.Field()

    # Extra
    number = scrapy.Field()
    history = scrapy.Field()
    description = scrapy.Field()
    num_photo = scrapy.Field()
    views = scrapy.Field()
    likes = scrapy.Field()

    listing_type = scrapy.Field()
    price = scrapy.Field() # int
    area = scrapy.Field() # float
    num_rooms = scrapy.Field() # int
    heating = scrapy.Field() # Bool
    floor = scrapy.Field() # int ?
    finish_level = scrapy.Field() # few points, list of elements
    rent = scrapy.Field() # int
    deposit = scrapy.Field() # int 
    additional = scrapy.Field() # Few points, list of elements
    elevator = scrapy.Field() # Bool
    building_type = scrapy.Field() # Few points, list of elements
    building_material = scrapy.Field() # Few points, list of elements
    windows_type = scrapy.Field() # Few points, list of elements
    equipment = scrapy.Field() # Few points, list of elements
    security = scrapy.Field() # Few points, list of elements
    media = scrapy.Field() # Few points, list of elements
    building_year = scrapy.Field()

class OtodomScrapperResult(scrapy.Item):
    # generic values
    listing_id = scrapy.Field() 
    scraped_at = scrapy.Field() 
    listing_type = scrapy.Field() 
    price = scrapy.Field() 
    floor = scrapy.Field()
    num_rooms = scrapy.Field()
    area = scrapy.Field() 
    rent = scrapy.Field()
    deposit = scrapy.Field()
    elevator = scrapy.Field()
    building_year = scrapy.Field()
    link = scrapy.Field()

    # category values
        # Sigle values
    finish_level = scrapy.Field() # single
    heating = scrapy.Field() # single
    building_type = scrapy.Field() # single
    building_material = scrapy.Field() # single
    windows_type = scrapy.Field() # single
        # Mutli values
    additional = scrapy.Field() # mult
    equipment = scrapy.Field() # multi 
    media = scrapy.Field() # mutli
    security = scrapy.Field() # multi

    #location
    street = scrapy.Field()
    estate = scrapy.Field()
    district = scrapy.Field()
    city = scrapy.Field()
    state = scrapy.Field()

    # Extra
    description = scrapy.Field()
    num_photo = scrapy.Field()
    number = scrapy.Field()
    history = scrapy.Field()
    views = scrapy.Field()
    likes = scrapy.Field()

class OtodomScrapperItemsFilter:
    def element_name(name):
        elements = {"Powierzchnia": "area",
                    "Liczba pokoi": "num_rooms",
                    "Ogrzewanie": "heating",
                    "Piętro": "floor",
                    "Stan wykończenia": "finish_level",
                    "Czynsz": "rent",
                    "Kaucja": "deposit",
                    "Informacje dodatkowe": "additional",
                    "Winda": "elevator",
                    "Rodzaj zabudowy": "building_type",
                    "Materiał budynku": "building_material",
                    "Okna": "windows_type",
                    "Wyposażenie": "equipment",
                    "Zabezpieczenia": "security",
                    "Media": "media",
                    "Rok budowy": "building_year"}

        return elements[name]
    
    def element_bool(name):
        elements = ["Powierzchnia", "Liczba pokoi", "Ogrzewanie", "Piętro", "Stan wykończenia",
                    "Czynsz", "Kaucja", "Informacje dodatkowe", "Winda", "Rodzaj zabudowy",
                    "Materiał budynku", "Okna", "Wyposażenie", "Zabezpieczenia", "Media", "Rok budowy"]
        return name in elements

