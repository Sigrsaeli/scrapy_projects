from collections.abc import Iterable

import scrapy
from parsel import Selector
from playwright.async_api import Page
from scrapy import Request
from scrapy.http import Response

from final_project.items import FinalProjectItem
from final_project.pipelines import PhotoDownloaderPipeline

def should_abort_request(request):
    return "yandex" in request.url or "ya" in request.url or "google" in request.url or "smi2" in request.url


class KpNewsSpider(scrapy.Spider):
    name = "kp_news"
    allowed_domains = ["kp.ru"]
    required_articles_count = 500
    total_scanned_articles = 0

    custom_settings = {
        "CONCURRENT_REQUESTS":3,
        "PLAYWRIGHT_ABORT_REQUEST": should_abort_request,
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": False},
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "ITEM_PIPELINES":{"final_project.pipelines.MongoPipeline":100},
        "MONGO_DB":"kp_ru",
        "MONGO_USER":"exprnc",
        "MONGO_PASSWORD":"1234",
        "MONGO_DB_COLLECTION":"kp_articles",
        "CLOSESPIDER_ITEMCOUNT": 500
    }

    def start_requests(self) -> Iterable[Request]:
        yield scrapy.Request(
            url="https://www.kp.ru/online/",
            meta={"playwright": True, "playwright_include_page": True},
        )

    async def parse(self, response: Response):
        page: Page = response.meta["playwright_page"]

        item = FinalProjectItem()

        while self.total_scanned_articles < self.required_articles_count:
            page_selector = Selector(await page.content())
            articles = page_selector.xpath("//a[@class='sc-1tputnk-2 drlShK']/@href").getall()
            articles = articles[-25:]
            for article in articles:
                item["source_url"] = response.urljoin(article)
                yield scrapy.Request(url=response.urljoin(article), callback=self.parse_article, meta={"item":item})
            await page.locator(selector="//button[@class='sc-abxysl-0 cdgmSL']").click(position={"x": 176, "y": 26.5})
            await page.wait_for_timeout(10000)
            self.total_scanned_articles += len(articles)
            print(self.total_scanned_articles)
            del articles
        await page.close()

    async def parse_article(self, response: Response):
        item = response.meta["item"]
        item["title"] = response.xpath("//h1[@class='sc-j7em19-3 eyeguj']/text()").getall()
        item["description"] = response.xpath("//div[@class='sc-j7em19-4 nFVxV']/text()").get()
        item["article_text"] = response.xpath("//div[@data-gtm-el='content-body']/text()").getall()
        item["publication_datetime"] = response.xpath("//span[@class='sc-j7em19-1 dtkLMY']/text()").get()
        item["header_photo_url"] = response.xpath("//img[@class='sc-foxktb-1 cYprnQ']/@src").get()
        item["header_photo_base64"] = PhotoDownloaderPipeline(35)
        item["keywords"] = response.xpath("//a[@class='sc-1vxg2pp-0 cXMtmu']/text()").getall()
        item["author"] = response.xpath("//span[@class='sc-1jl27nw-1 bmkpOs']/text()").get()

        yield item
