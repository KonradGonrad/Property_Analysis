import scrapy


class OtodomSpider(scrapy.Spider):
    name = "otodom"
    allowed_domains = ["otodom.pl"]
    start_urls = ["https://otodom.pl"]

    def parse(self, response):
        pass
