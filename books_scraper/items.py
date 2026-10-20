import scrapy


class BooksScraperItem(scrapy.Item):
    """Represent a scraped book and its required fields."""

    title = scrapy.Field()
    price = scrapy.Field()
    availability = scrapy.Field()
    product_url = scrapy.Field()
    image_url = scrapy.Field()
    category = scrapy.Field()
