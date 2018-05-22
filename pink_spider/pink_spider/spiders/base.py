# -*- coding: utf-8 -*-
import logging
import os
import re
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
from ..items import FollowingItem

logger = logging.getLogger(__name__)


class BaseSpider(CrawlSpider):
    name = "base"
    crawl_url = ""

    def start_requests(self):
        url = "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index"
        return [scrapy.Request(url=url, callback=self.login_parse)]

    def login_parse(self, response):
        post_key = re.search(r'name="post_key" value="(\w+)"', response.text).group(1)
        url = "https://accounts.pixiv.net/login"
        data = {
            "pixiv_id": os.environ.get("PIXIV_ID", ""),
            "password": os.environ.get("PIXIV_PASSWORD", ""),
            "source": "pc",
            "lang": "ja",
            "return_to": "https://www.pixiv.net/",
            "post_key": post_key,
        }
        if not all([data["pixiv_id"], data["password"]]):
            raise CloseSpider("Pixiv ID or Password is empty.")
        return scrapy.FormRequest(url=url, formdata=data, callback=self.after_login)

    def after_login(self, response):
        if response.url == "https://accounts.pixiv.net/login":
            raise CloseSpider("Login failed.Please check Pixiv ID and Password.")
        for url in self.start_urls:
            yield scrapy.Request(url)


class FollowingSpider(BaseSpider):
    name = "following"
    allowed_domains = ["pixiv.net"]
    start_urls = ["https://www.pixiv.net/bookmark.php?type=user&rest=show"]
    rules = (
        Rule(LinkExtractor("/member.php\?id=\d+$"), follow=True, callback="parse_page"),
        Rule(
            LinkExtractor("/member_illust.php\?mode=medium&illust_id=\d+$"),
            callback="parse_items",
        ),
        Rule(LinkExtractor("\?type=user&rest=show&p=\d+$"), follow=True),
    )

    def parse_start_url(self, response):
        return self.parse_page(response)

    def parse_page(self, response):
        user_name = response.css("a.user-name::text").extract_first()
        item = FollowingItem(name=user_name)
        logger.info(f"Artist: {user_name}")
        return item

    def parse_items(self, response):
        if response.url != "https://www.pixiv.net/bookmark.php?type=user&rest=show":
            title = response.css("title::text").extract_first()
            if not title:
                title = "No Title"
            m = re.search(r'"createDate":"\d+-\d+-\d+', response.text)
            if m:
                created_at = m.group()[-10:]
            else:
                created_at = "No Date"
            logger.info(f"{created_at}:{title}")
        return
