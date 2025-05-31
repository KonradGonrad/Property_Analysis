import scrapy
from ..settings import SCRAP_PHOTOS, SCRAP_DESCRIPTION, SCRAP_HISTORY, SCRAP_NUMBER, SCRAP_OTHER, SCRAP_WAIT_TIME
from ..settings_keys import email, password
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium import webdriver
from scrapy_selenium import SeleniumRequest
from scrapy.http import HtmlResponse
from house_scrapper.items import OtodomScrapperItem, OtodomScrapperItemsFilter
import json
import time
from urllib.parse import urljoin

class OtodomSpider(scrapy.Spider):
    name = "otodom"
    allowed_domains = ["otodom.pl"]
    custom_settings = {'FEEDS': {
         'apps_data_5.json'   :   {'format':'json', 'overwrite': True}, # File to save destination
    }}

    def start_requests(self): # Start for different links, there I used that to differentiate the rent and the sale market in Lodz
        start_urls = [("https://www.otodom.pl/pl/wyniki/wynajem/mieszkanie/lodzkie/lodz/lodz/lodz?ownerTypeSingleSelect=ALL&viewType=listing", "rent"), # Otodom appartments for rent
                    #   ("https://www.otodom.pl/pl/wyniki/sprzedaz/mieszkanie/lodzkie/lodz/lodz/lodz?viewType=listing", "sale") 
        ]
        self.idx = 1
        self.next = None

        for url, listing_type in start_urls:
            yield SeleniumRequest(url = url,
                                  callback = self.parse,
                                  meta = {"listing_type": listing_type, 'start_url': url},
                                  wait_time=SCRAP_WAIT_TIME)

    def parse(self, response):
        # options = webdriver.ChromeOptions()
        # options.add_argument("--headless") # Cannot use that, because the site is aware of --headless argument and dont load js
        start_url = response.meta.get('start_url')
        driver = response.meta.get('driver') # Download the driver
        next_page = None # Next_page if exists, needed to secure the option, when in the try block won't work
        listing_type = response.meta.get('listing_type') # Take the type of listing given in meta

        # Initializing the driver for selenium
        if driver is None: # If there is no driver found
            print("Driver is None. Initializing one.") # Print out the message
            driver = webdriver.Chrome() # Initialize the driver with Chrome driver
            driver.get(response.url) # Pass to the driver page link
        
        try: # Next try to:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # Scroll down with js script on the website

            WebDriverWait(driver, SCRAP_WAIT_TIME).until( # let driver wait for 2 seconds until
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
                    next_page = start_url + f"&page={self.idx + 1}" # Method with indexing
                    self.idx += 1
                else:
                    next_page = None  

        except Exception as e:
            print("Navbar not found.", e) # Exception error
        driver.close()

        # Scraping listings
        apartments = response.css('div[data-cy="search.listing.organic"] > span + ul > li') # Appartments list
        for apartment in apartments: 
            relative_url = apartment.css('article > section > div + div > a::attr(href)').get() # Realative url to open the apartments
            
            if relative_url: # If there are relative url
                # apartment_url = "https://" + self.allowed_domains[0] + relative_url # Creating the each apartment url
                apartment_url = urljoin("https://www.otodom.pl", relative_url)
                yield SeleniumRequest(wait_time=SCRAP_WAIT_TIME, # wait 2 seconds before scraping
                                      callback = self.parse_apartment, # Use parse_apartment function and return the output
                                      url = apartment_url,
                                      meta={'listing_type': listing_type, 'driver': driver}) # Use apartment_url as the link to follow
        
        # print("Page done", response.url)
        
        if next_page is not None: # If there are another page, then parse that page with SeleniumRequest
            yield SeleniumRequest(url = next_page,
                                  callback=self.parse,
                                  wait_time=SCRAP_WAIT_TIME,
                                  meta={'listing_type': listing_type, 'start_url': start_url})
        print("Scraping finished")
                
    def parse_apartment(self, response):
        Data = OtodomScrapperItem() # Container for data scraped from the Website
        listing_type = response.meta.get('listing_type')

        Data['scraped_at'] = time.strftime("%Y-%m-%d")
        Data['link'] = response.url
        Data['listing_type'] = listing_type
        Data['price'] = response.css('div[data-sentry-element="MainPriceWrapper"] > strong::text').get() # Getting the price from JSON data
        Data['listing_id'] = response.css('div[data-sentry-component="AdDescriptionBase"] > div:nth-of-type(3) p::text')[-1].get()
        Data['location'] =  response.css('div[data-sentry-component="AdHeaderBase"] a::text').get() # Need to be parsed

        elements = response.css('div[data-sentry-element="StyledListContainer"] div[data-sentry-element="ItemGridContainer"]') # Elements data containers
        num_elements = len(elements) # number of elements

        # Scraping appartment info section
        special_data = ["Informacje dodatkowe", "Wyposażenie", "Media", "Zabezpieczenia"] # Special data, where are few elements in the same row
        
        for index in range(num_elements):  # For each element 
            element_name = elements[index].css('p:nth-of-type(1)::text').get().strip() # Takes the name of the element scraped
            childs = [element.root.tag for element in elements[index].css('*')]

            if element_name in special_data:
                if len(childs) > 3:
                    element_value = elements[index].css('p + p > span::text').getall()
                else:
                    element_value = elements[index].css('p + p::text').getall()
            else:
                element_value = elements[index].css('p + p::text').get()

            if OtodomScrapperItemsFilter.element_bool(element_name): # If element name in elements list that are scraped
                Data[OtodomScrapperItemsFilter.element_name(element_name)] = element_value # If so, assign data to the Data element

        # Scraping other extras
        if SCRAP_OTHER:

            try:
                driver = webdriver.Chrome() # Initialize the driver with Chrome driver
                driver.get(response.url) # Pass to the driver page link

                time.sleep(0.5) # Waiting for page to load

                # Doesn't work corectly
                # try: # Trying to close the cookie bar
                #     cookie_button = driver.find_element(By.CSS_SELECTOR, "button#onetrust-accept-btn-handler")
                #     cookie_button.click()
                #     time.sleep(0.5)
                # except NoSuchElementException as e:
                #     print("Cookie button not found", e)
                # except Exception as e:
                #     print("Cookie error", e)

                try:
                    cookie_button = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, "button#onetrust-accept-btn-handler"))
                    )
                    cookie_button.click()
                    time.sleep(0.5)
                except TimeoutException:
                    print("Cookie button not found (timeout)")
                except NoSuchElementException:
                    print("Cookie button not found (no such element)")
                except Exception as e:
                    print("Cookie error", e)

                time.sleep(1)

                try: 
                    survey_buttons = driver.find_elements(By.CSS_SELECTOR, '.laq-layout__actions--decline')

                    if survey_buttons:
                        try:
                            survey_buttons[0].click()
                            print("Survey closed")
                        except Exception as e:
                            print(f"Survey button found but couldn't click: {e}")
                    else:
                        print("No survey found")
                except Exception as e:
                    print("error survey", e)

                if SCRAP_PHOTOS:
                    try: 
                        gallery_buttons = driver.find_elements(By.CSS_SELECTOR, 'div[data-cy="mosaic-gallery-main-view"] > button')
                        gallery_num = gallery_buttons[-1].find_element(By.CSS_SELECTOR, 'div').text
                        Data['num_photo'] = gallery_num
                    except NoSuchElementException:
                        Data['num_photo'] = None
                        print(f"No div found inside last gallery button on page {response.url}")
                    except Exception as e:
                        Data['num_photo'] = None
                        print("Not found gallery", e)

                time.sleep(0.5)

                if SCRAP_NUMBER:
                    try:
                        number_button = driver.find_element(By.CSS_SELECTOR, 'div[data-sentry-component="SellerInfo"] button[data-sentry-component="getPhoneButton"]')
                        number_button.click()
                        time.sleep(0.5) # Waiting for laod
                        number = driver.find_element(By.CSS_SELECTOR, 'div[data-sentry-element="PhoneNumberWrapper"] span').text

                        Data['number'] = number
                    except NoSuchElementException:
                        Data['number'] = None
                        print(f"No number found on page {response.url}")

                    except Exception as e:
                        Data['number'] = None
                        print("Number [Error]", e)

                time.sleep(0.5)

                if SCRAP_DESCRIPTION:
                    try:
                        description_section = driver.find_element(By.CSS_SELECTOR, 'div[data-sentry-component="AdDescriptionBase"]')
                        driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", description_section)

                        try:
                            
                            expand_button = description_section.find_element(By.XPATH, './/span[text()="Pokaż więcej"]/ancestor::button')
                            expand_button.click()
                            time.sleep(1)  
                        except Exception as e:
                            print("Nie znaleziono lub nie można kliknąć przycisku 'Pokaż więcej':", e)

                        description = driver.find_element(By.CSS_SELECTOR, 'div[data-sentry-component="AdDescriptionBase"] > div[data-sentry-element="DescriptionWrapper"] > span')

                        Data['description'] = len(description.text.split())

                    except:
                        Data['description'] = None
                        print("Description not found")
        
            except Exception as e:
                print("Driver not created")
            finally:
                driver.close()

            
            
            if SCRAP_HISTORY:
                    
                    try:
                        login_button = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="ad.page.history.login-button"]'))
                        )
                        login_button.click()

                        WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.ID, "username"))
                        )

                        driver.find_element(By.ID, "username").send_keys(f"{email}")
                        driver.find_element(By.ID, "password").send_keys(f"{password}")

                        login_button = driver.find_element(By.CSS_SELECTOR, 'button[data-testid="login-submit-button"]')
                        login_button.click()

                        WebDriverWait(driver, 10).until(
                            EC.url_contains("otodom.pl") 
                        )

                        print("Logged in")
                    except:
                        pass

                    time.sleep(3)

                    element = WebDriverWait(driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-sentry-component="AdHistoryBase"]'))
                        )
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                    try:
                        history_section = WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-sentry-component="AdHistoryBase"]'))
                            )

                            # Pobieramy wszystkie pasujące elementy do wskazanej ścieżki
                        data_elements = driver.find_elements(By.CSS_SELECTOR,
                                'div[data-sentry-component="AdHistoryBase"] > div[data-sentry-element="Row"] + div > div > div > div'
                            )
                        actions = []
                        element = data_elements[-1]
                        try:
                            date = element.find_element(By.CSS_SELECTOR, 'p').text
                            actions.append(date)
                        except Exception as e:
                            print('Element error', e)

                        Data['history'] = actions
                    except NoSuchElementException as e:
                        print("Blad", e)

            if SCRAP_DESCRIPTION:
                pass


        yield Data # Return scrapped data