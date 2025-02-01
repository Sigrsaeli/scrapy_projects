import scrapy
from ..items import HomeProjectItem


class MerchantpointSpider(scrapy.Spider):
    name = "merchantpoint"
    allowed_domains = ["merchantpoint.ru"]
    start_urls = ["https://merchantpoint.ru"]

    def parse(self, response):
        return scrapy.Request(url=response.xpath("//a[text()='Бренды']/@href").get(), callback=self.parse_brands)

    def parse_brands(self, response):
        hrefs = response.xpath("//tbody/tr/td/a/@href").getall()
        descriptions = response.xpath("//tbody/tr/td[3]/text()").getall()
        for link, description in zip(hrefs, descriptions):
            if description == '':
                continue
            else:
                yield scrapy.Request(url=response.urljoin(link), callback=self.brand)
        # Переход на следующую страницу
        next_page = response.xpath("//a[text()='Вперед →']/@href").get()
        if next_page:
            yield response.follow(next_page, callback=self.parse_brands)

    def brand(self, response):
        item = HomeProjectItem()

        # Извлекаем данные из первой страницы
        item["org_name"] = response.xpath("//h1[@class='h2']/text()").get()
        item["org_description"] = response.xpath("//p[@class='form-text text-muted']/following-sibling::p/text()").get()
        item["source_url"] = response.xpath("//b[text()='Сайт']/following-sibling::a/@href").get()

        # Находим ссылки на дополнительные данные
        points_table = response.xpath("//tbody[@class='searchable']/tr/td/a/@href").get()
        
        if points_table:
            url = response.urljoin(points_table)
            # Передаём item в meta
            yield scrapy.Request(url=url, callback=self.parse_addInfo, meta={"item": item})
        else:
            yield item  # Если ссылок нет, сразу отдаём item
    
    def parse_addInfo(self, response):
         # Получаем переданный item
        item = response.meta["item"]

        # Извлекаем данные со второй страницы
        merchant_name = response.xpath("//p[b[text()='MerchantName']]/text()").get()
        item["merchant_name"] = merchant_name.replace(" — ", "").strip() if merchant_name else None

        mcc = response.xpath("//p[b[text()='MCC код']]/a/text()").get()
        item["mcc"] = mcc.strip() if mcc else None

        address = response.xpath("//p[b[text()='Адрес торговой точки']]/text()").get()
        item["address"] = address.replace(" — ", "").strip() if address else None

        coordinates = response.xpath("//p[b[text()='Геокоординаты']]/text()").get()
        item["geo_coordinates"] = coordinates.replace(" — ", "").strip() if coordinates else None

        yield item  # Отправляем полностью заполненный Item