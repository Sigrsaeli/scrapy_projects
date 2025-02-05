import scrapy
from scrapy.spiders import SitemapSpider
from .. items import HomeProject2Item

class ChgorodSpider(scrapy.Spider):
    name = "chGorod"
    allowed_domains = ["chitai-gorod.ru"]
    start_urls = ["https://chitai-gorod.ru/sitemap.xml"]
    #sitemap_rules = [
        #("/categories1.xml", "parse"),
        #("/books/", "parse_categories"),

    #]
    custom_settings = {
        #"DOWNLOAD_DELAY":3,
        #"CONCURRENT_REQUESTS":2,
        "ITEM_PIPELINES":{"home_project2.pipelines.MongoPipeline":100},
        "MONGO_DB":"chitai_gorod",
        "MONGO_USER":"exprnc",
        "MONGO_PASSWORD":"1234",
        "MONGO_DB_COLLECTION":"books_chitai_gorod"
    }

    def parse(self, response):
        response.selector.remove_namespaces()
    
        # Получаем все ссылки из тега <loc>
        links = response.xpath("//loc/text()").getall()

        # Фильтруем ссылки по ключевому слову "categories1"
        categories_link = [link for link in links if "categories1" in link]
        
        return scrapy.Request(url=categories_link[0], callback=self.parse_categories)


    def parse_categories(self, response):
        headers = {"Authorization":"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Mzg2MjI0MjYsImlhdCI6MTczODQ1NDQyNiwiaXNzIjoiL2FwaS92MS9hdXRoL2Fub255bW91cyIsInN1YiI6IjZhNDE3YzkwMzY0N2UxYjlkOTliMzlmNTY5MTkxNjVkNTAyY2ViNWUzZjljNjYyMDY1MDRhMjYxN2MzNGU3Y2EiLCJ0eXBlIjoxMH0.93sLjJsyr4HFqHZKrReVMGLbAfbTBP5qU1KPuvS8jkk"}
        response.selector.remove_namespaces()

        links = response.xpath("//loc/text()").getall()

        # Фильтруем ссылки по ключевому слову "books"
        books_categories = [link for link in links if "books" in link]

        for category in books_categories:
            yield scrapy.Request(url=category, callback=self.parse_categoryPage, headers=headers)


    def parse_categoryPage(self, response):
        item = HomeProject2Item()

        books_links = response.xpath("//a[@class='product-card__picture product-card__row']/@href").getall()

        for link in books_links:
            item["source_url"] = self.allowed_domains[0]+link
            yield scrapy.Request(url=response.urljoin(link), callback=self.parse_bookCard, meta={"item":item})

        next_page = response.xpath("//a[@class='pagination__button']/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_categoryPage)


    def parse_bookCard(self, response):
        item = response.meta["item"]
        item["title"] = response.xpath("//h1[@itemprop='name']/text()").get().strip()
        item["author"] = response.xpath("//a[@class='product-info-authors__author']/text()").get().strip()
        full_description = response.xpath("//div[@class='detail-description__text']/text()").getall()
        full_description = " ".join([text.strip() for text in full_description if text.strip()])
        item["description"] = full_description
        price_currency = response.xpath("//span[@itemprop='price']/text()").get().strip().split()
        item["price_amount"] = price_currency[0]
        item["price_currency"] = price_currency[1]
        item["rating_value"] =  response.xpath("//meta[@itemprop='ratingValue']/@content").get()
        item["rating_count"] = response.xpath("//meta[@itemprop='reviewCount']/@content").get()
        item["publication_year"] = response.xpath("//span[@itemprop='datePublished']/text()").get().strip()
        item["isbn"] = response.xpath("//span[@itemprop='isbn']/text()").get().strip()
        item["publisher"] = response.xpath("//a[@itemprop='publisher']/text()").get().strip()
        item["book_cover"] = response.xpath("//img[@class='product-info-gallery__poster']/@src").get()
        yield item

