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
    custom_settings = {'FEEDS': {
         'apps_data.json'   :   {'format':'json', 'overwrite': True}, # File to save destination
    }}
    idx = 1
    next = None

    def start_requests(self): # Start for different links, there I used that to differentiate the rent and the sale market in Lodz
        start_urls = [("https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/lodzkie/lodz/lodz/lodz?ownerTypeSingleSelect=ALL&viewType=listing", "rent"), # Otodom appartments for rent
                      ("https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/lodzkie/lodz/lodz/lodz?viewType=listing", "sale")
        ]

        for url, listing_type in start_urls:
            yield SeleniumRequest(url = url,
                                  callback = self.parse,
                                  meta = {"listing_type": listing_type},
                                  wait_time=1)

    def parse(self, response):
        driver = response.meta.get('driver') # Download the driver
        next_page = None # Next_page if exists, needed to secure the option, when in the try block won't work
        listing_type = response.meta.get('listing_type') # Take the type of listing given in meta

        if driver is None: # If there is no driver found
            print("Driver is None. Initializing one.") # Print out the message
            driver = webdriver.Chrome() # Initialize the driver with Chrome driver
            driver.get(response.url) # Pass to the driver page link
        
        try: # Next try to:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # Scroll down with js script on the website

            WebDriverWait(driver, 2).until( # let driver wait for 2 seconds until
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="navigation"]')) # There will appear the navbar on the bottom
            )
            try: # Set the next_page using JSON data - first attempt 
                json_data = response.xpath('//script[@type="application/json"]').get() # Get the script data
                data = json.loads(json_data) # Load that script data into json

                page_number = data.get("page_nb") # Number of page
                self.total_pages = data.get("page_count") # Total number of pages

                next_page = response.url + f"&page={page_number + 1}"
            except Exception as e: # If cannot find the Json data, then do this
                print("Json data not found.", e)

                try:
                    navbar = driver.find_element(By.CSS_SELECTOR, 'div[role="navigation"]') # Locate navbar
                    driver.execute_script("arguments[0].scrollIntoView();", navbar) # Scroll to navbar

                    self.next = navbar.find_element(By.CSS_SELECTOR, 'div > ul li[title="Go to next Page"]') # Locate button in li to take next page
                except Exception as e:
                    print("Not found next page", e)
                
                # If I'm not wrong I could possibly put the statements below into try method to look more profensional, but it works

                if self.next is not None: # If found the next page 
                    next_page = response.url + f"&page={self.idx + 1}" # Method with indexing
                    self.idx += 1
                else:
                    next_page = None
                    
        except Exception as e:
            print("Navbar not found.", e) # Exception error


        apartments = response.css('div[data-cy="search.listing.organic"] > span + ul > li') # Appartments list
        for apartment in apartments: 
            relative_url = apartment.css('article > section > div + div > a::attr(href)').get() # Realative url to open the apartments
            
            if relative_url: # If there are relative url
                # apartment_url = "https://" + self.allowed_domains[0] + relative_url # Creating the each apartment url
                apartment_url = urljoin("https://www.otodom.pl", relative_url)
                yield SeleniumRequest(wait_time=2, # wait 2 seconds before scraping
                                      callback = self.parse_apartment, # Use parse_apartment function and return the output
                                      url = apartment_url,
                                      meta={'listing_type': listing_type}) # Use apartment_url as the link to follow
                
        if next_page is not None: # If there are another page, then parse that page with SeleniumRequest
            yield SeleniumRequest(url = next_page,
                                  callback=self.parse,
                                  wait_time=1,
                                  meta={'driver': driver, 'listing_type': listing_type})
                
    def parse_apartment(self, response):
        Data = OtodomScrapperItem() # Container for data scraped from the Website
        listing_type = response.meta.get('listing_type')

        Data['link'] = response.url
        Data['listing_type'] = listing_type
        Data['price'] = response.css('div[data-sentry-element="MainPriceWrapper"] > strong::text').get() # Getting the price from JSON data
        
        elements = response.css('div[data-sentry-element="StyledListContainer"] div[data-sentry-element="ItemGridContainer"]') # Elements data containers
        num_elements = len(elements) # number of elements

        special_data = ["Informacje dodatkowe", "Wyposażenie", "Media"] # Special data, where are few elements in the same row
        for index in range(num_elements):  # For each element 
            element_name = elements[index].css('p:nth-of-type(1)::text').get() # Takes the name of the element scraped
            element_value = elements[index].css('p + p::text').get() if element_name not in special_data else elements[index].css('p + p > span::text').getall() # Gets the value or all values from element

            if OtodomScrapperItemsFilter.element_bool(element_name): # If element name in elements list that are scraped
                Data[OtodomScrapperItemsFilter.element_name(element_name)] = element_value # If so, assign data to the Data element

        yield Data # Return scrapped data