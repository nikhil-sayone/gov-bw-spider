# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

# class GovBwItem(scrapy.Item):
#     def __setitem__(self, key, value):
#         self._values[key] = value
#         self.fields[key] = {}

class GovBwItem(scrapy.Item):
    
    url = scrapy.Field()
    department = scrapy.Field()
    section = scrapy.Field()
    title = scrapy.Field()
    contents = scrapy.Field()
    documents = scrapy.Field()