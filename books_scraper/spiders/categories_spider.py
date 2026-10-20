"""Spider for discovering book categories."""

import scrapy

from books_scraper.category_utils import extract_categories


class CategoriesSpider(scrapy.Spider):
    """Discover category names and URLs from the website."""

    name = "categories"
    start_urls = ["https://books.toscrape.com/"]

    custom_settings = {
        "ITEM_PIPELINES": {},
        "FEEDS": {},
    }

    def parse(self, response):
        """Yield each discovered category."""
        categories = extract_categories(response, self.logger)

        if not categories:
            self.logger.warning(
                "No category links found on %s",
                response.url,
            )
            return

        self.logger.info(
            "Found %d category links on %s",
            len(categories),
            response.url,
        )

        for category in categories:
            yield {
                "category": category["name"],
                "category_url": category["url"],
            }
