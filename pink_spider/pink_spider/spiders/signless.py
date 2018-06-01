# -*- coding: utf-8 -*-
import datetime

from bs4 import BeautifulSoup
from scrapy.spiders import Spider

from ..items import SearchRankingItem


class SearchRankingSpider(Spider):
    name = "search_ranking"
    start_urls = ["https://www.pixiv.net/idea/"]

    def parse(self, response):
        today = datetime.date.today()
        soup = BeautifulSoup(response.text, "html.parser")
        for gender in ("male", "female"):
            ranking_words = soup.select(f"#{gender}-ranking .word")
            ranking_points = soup.select(f"#{gender}-ranking .point")
            for (word_obj, point_obj) in zip(ranking_words, ranking_points):
                word = word_obj.text
                if point_obj.text.startswith("Hot"):
                    point = point_obj.text[3:-2]
                    is_hot = "true"
                else:
                    point = point_obj.text[:-2]
                    is_hot = "false"
                item = SearchRankingItem()
                item["word"] = word
                item["point"] = point
                item["gender"] = gender
                item["tallying_date"] = today
                item["is_hot"] = is_hot
                yield item
