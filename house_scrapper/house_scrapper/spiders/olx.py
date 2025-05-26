import scrapy


class OlxSpider(scrapy.Spider):
    name = "olx"
    allowed_domains = ["olx.pl"]
    start_urls = ["https://olx.pl"]


    def parse(self, response):
        driver = response.meta.get('driver')
        print(driver)
        pass
