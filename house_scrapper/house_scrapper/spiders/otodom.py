import scrapy
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from scrapy_selenium import SeleniumRequest
from house_scrapper.items import OtodomScrapperItem, OtodomScrapperItemsFilter
import json
from urllib.parse import urljoin

class OtodomSpider(scrapy.Spider):
    name = "otodom"
    allowed_domains = ["otodom.pl"]
    start_urls = ["https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/cala-polska"]
    custom_settings = {'FEEDS': {
         'apps_data.json'   :   {'format':'json', 'overwrite': True}, # File to save destination
    }}

    def parse(self, response):
        driver = response.meta.get('driver') # Download the driver

        if driver is None: # If there is no driver found
            print("Driver is None. Initializing one.") # Print out the message
            driver = webdriver.Chrome() # Initialize the driver with Chrome driver
            driver.get(response.url) # Pass to the driver page link
        
        # try: # Next try to:
        #     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # Scroll down with js script on the website

        #     WebDriverWait(driver, 2).until( # let driver wait for 2 seconds until
        #         EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="navigation"]')) # There will appear the navbar on the bottom
        #     )
        #     navbar = driver.find_element(By.CSS_SELECTOR, 'div[role="navigation"]') # Navbar location, if there is no navbar then execption
        #     json_data = response.xpath('//script[@type="application/json"]').get() # Get the script data
        #     data = json.loads(json_data) # Load that script data into json

        #     page_number = data.get("page_nb") # Number of page
        #     total_pages = data.get("page_count") # Total number of pages

        #     next_page = None if page_number == total_pages else self.start_urls[0] + f"?page={page_number + 1}"

        # except NoSuchElementException as e:
        #     print("Navbar not found.", e) # Exception error


        apartments = response.css('div[data-cy="search.listing.organic"] > span + ul > li') # Appartments list
        for apartment in apartments: 
            relative_url = apartment.css('article > section > div + div > a::attr(href)').get() # Realative url to open the apartments
            
            if relative_url: # If there are relative url
                # apartment_url = "https://" + self.allowed_domains[0] + relative_url # Creating the each apartment url
                apartment_url = urljoin("https://www.otodom.pl", relative_url)
                yield SeleniumRequest(wait_time=2, # wait 2 seconds before scraping
                                      callback = self.parse_apartment, # Use parse_apartment function and return the output
                                      url = apartment_url) # Use apartment_url as the link to follow
                
    def parse_apartment(self, response):
        Data = OtodomScrapperItem() # Container for data scraped from the Website

        Data['price'] = response.css('div[data-sentry-element="MainPriceWrapper"] > strong::text').get() # Getting the price from JSON data
        
        elements = response.css('div[data-sentry-element="StyledListContainer"] div[data-sentry-element="ItemGridContainer"]') # Elements data containers
        num_elements = len(elements) # number of elements

        special_data = ["Informacje dodatkowe", "Wyposażenie", "Media"] # Special data, where are few elements in the same row
        for index in range(num_elements):  # For each element 
            element_name = elements[index].css('p:nth-of-type(1)::text').get() # Takes the name of the element scraped
            element_value = elements[index].css('p + p::text').get() if element_name not in special_data else elements[index].css('p + p > span::text').getall() # Gets the value or all values from element

            if OtodomScrapperItemsFilter.element_bool(element_name): # If element name in elements list that are scraped
                Data[OtodomScrapperItemsFilter.element_name(element_name)] = element_value # If so, assign data to the Data element

        yield Data