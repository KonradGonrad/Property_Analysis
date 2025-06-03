import sys
sys.path.append('../')

from .settings_keys import SCRAPEOPS_API_KEY
from data.database_info import db_name, acc_name, password

# Scrapy settings for house_scrapper project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = "house_scrapper"

SPIDER_MODULES = ["house_scrapper.spiders"]
NEWSPIDER_MODULE = "house_scrapper.spiders"

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "house_scrapper (+http://www.yourdomain.com)"

SCRAPEOPS_API_KEY = SCRAPEOPS_API_KEY
SCRAPEOPS_NUM_RESULTS = 50
SCRAPEOPS_FAKE_BROWSER_HEADER_ENDPOINT = "http://headers.scrapeops.io/v1/browser-headers"
SCRAPEOPS_FAKE_BROWSER_HEADER_ENABLED = True

# Spider settings
SCRAP_WAIT_TIME = 5
SCRAP_SLEEP_TIME = 1

# Extra scrape things
SCRAP_HISTORY = False # In general I don't use this
SCRAP_NUMBER = True
SCRAP_DESCRIPTION = True
SCRAP_PHOTOS = False
SCRAP_STATS = True

SCRAP_ADD = any([SCRAP_DESCRIPTION,
                 SCRAP_STATS])

SCRAP_OTHER = any([SCRAP_HISTORY, 
                   SCRAP_NUMBER, 
                   SCRAP_DESCRIPTION, 
                   SCRAP_PHOTOS])


# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
DOWNLOAD_DELAY = 1
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
#COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "house_scrapper.middlewares.HouseScrapperSpiderMiddleware": 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
    "house_scrapper.middlewares.HouseScrapperDownloaderMiddleware": 543,
    # "house_scrapper.middlewares.SeleniumMiddleware": 200,
    "house_scrapper.middlewares.WebScraperFakeBrowserHeaders": 404,
}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}
TELNETCONSOLE_PORT = [6060, 6070]

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
   "house_scrapper.pipelines.HouseScrapperPipeline": 300,
   "house_scrapper.pipelines.ProcessToSQL": 400,
   "house_scrapper.pipelines.SaveToPostgreSQL": 500
}

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
#AUTOTHROTTLE_ENABLED = True
# The initial download delay
#AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
#AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
#AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"


# Custom settings
SAVE_PATH = 'appdata.json'

# DataBase Settings
DB_NAME = db_name
DB_USER = acc_name
DB_PASSWORD = password
DB_PORT = '5432'
DB_HOST = 'localhost'