# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class UserItem(scrapy.Item):
    user_id = scrapy.Field()
    name = scrapy.Field()
    title = scrapy.Field()
    created_at = scrapy.Field()


class SearchRankingItem(scrapy.Item):
    word = scrapy.Field()
    point = scrapy.Field()
    gender = scrapy.Field()
    tallying_date = scrapy.Field()
    is_hot = scrapy.Field()
