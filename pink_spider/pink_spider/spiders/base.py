# -*- coding: utf-8 -*-
import datetime
import logging
import os
import re
from bs4 import BeautifulSoup
import scrapy
from scrapy.spiders import Spider, CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
from ..items import UserItem, SearchRankingItem

logger = logging.getLogger(__name__)


class UserSpider(CrawlSpider):
    name = "user"
    pre_login_url = "https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index"
    login_url = "https://accounts.pixiv.net/login"

    def start_requests(self):
        return [scrapy.Request(url=self.pre_login_url, callback=self.login_parse)]

    def login_parse(self, response):
        post_key = re.search(r'name="post_key" value="(\w+)"', response.text).group(1)
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
        return scrapy.FormRequest(
            url=self.login_url, formdata=data, callback=self.after_login
        )

    def after_login(self, response):
        if response.url == self.login_url:
            raise CloseSpider("Login failed.Please check Pixiv ID and Password.")
        for url in self.start_urls:
            yield scrapy.Request(url)


class FollowingSpider(UserSpider):
    name = "following"
    allowed_domains = ["pixiv.net"]
    start_urls = ["https://www.pixiv.net/bookmark.php?type=user&rest=show"]
    rules = (
        Rule(LinkExtractor("/member.php\?id=\d+$"), follow=True),
        Rule(LinkExtractor("\?type=user&rest=show&p=\d+$"), follow=True),
        Rule(
            LinkExtractor("/member_illust.php\?mode=medium&illust_id=\d+$"),
            callback="parse_items",
        ),
    )

    def parse_start_url(self, response):
        return self.parse_items(response)

    def parse_items(self, response):

        if response.url != self.start_urls[0]:
            # Since there are cases where a work link other than the user himself,
            # such as "image response", is displayed, this is excluded.
            if 'isFollowed":true' not in response.text:
                return

            item = UserItem()

            user_id_match = re.search(r'userId":"\d+', response.text)
            if user_id_match:
                _, user_id = user_id_match.group().split(":")
                user_id = user_id[1:]
            else:
                user_id = ""

            title = response.css("title::text").extract_first()
            if not title:
                title = ""

            if title:
                name = title.split("/")[1].split("」のイラスト")[0][1:]
            else:
                name = ""

            created_at_match = re.search(r'"createDate":"\d+-\d+-\d+', response.text)
            if created_at_match:
                created_at = created_at_match.group()[-10:]
            else:
                created_at = ""

            item["user_id"] = user_id
            item["name"] = name
            item["title"] = title
            item["created_at"] = created_at
            return item


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
