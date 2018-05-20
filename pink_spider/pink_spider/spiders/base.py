# -*- coding: utf-8 -*-
import os
import re
import scrapy
from scrapy.exceptions import CloseSpider


class BaseSpider(scrapy.spiders.CrawlSpider):
    name = "base"
    crawl_url = ""

    def start_requests(self):
        url = "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index"
        return [
            scrapy.Request(url=url, callback=self.get_post_key)
        ]

    def get_post_key(self, response):
        post_key = re.search(r'name="post_key" value="(\w+)"', response.text).group(1)
        url = "https://accounts.pixiv.net/login"
        data = {
            "pixiv_id": os.environ.get('PIXIV_ID', ''),
            "password": os.environ.get('PIXIV_PASSWORD', ''),
            "source": "pc",
            "lang": "ja",
            "return_to": "https://www.pixiv.net/",
            "post_key": post_key,
        }
        if not all([data["pixiv_id"], data["password"]]):
            raise CloseSpider("Pixiv ID or Password is empty.")
        return scrapy.FormRequest(url=url, formdata=data, callback=self.crawl)

    def crawl(self, response):
        if response.url == 'https://accounts.pixiv.net/login':
            raise CloseSpider("Login failed.Please check Pixiv ID and Password.")
        yield scrapy.Request(self.crawl_url, callback=self.parse)

    def parse(self, response):
        print(response.text)


class FollowingSpider(BaseSpider):
    name = "following"
    crawl_url = "https://www.pixiv.net/bookmark.php?type=user&rest=show"
