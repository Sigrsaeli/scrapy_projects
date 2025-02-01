# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class HomeProjectItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    merchant_name = scrapy.Field()
    mcc = scrapy.Field()
    address = scrapy.Field()
    geo_coordinates = scrapy.Field()
    org_name = scrapy.Field()
    org_description = scrapy.Field()
    source_url = scrapy.Field()
