import scrapy

class CategoriesSpider(scrapy.Spider):
    """Discover book category links from the Books to Scrape homepage."""

    name = "categories"

    start_urls = ["https://books.toscrape.com/"]

    def parse(self, response):
        """Extract category names and absolute URLs from the sidebar."""

        category_links = response.css(".side_categories ul ul li a")

        if not category_links:
            self.logger.warning(
                "No category links found on %s",
                response.url,
            )
            return

        self.logger.info(
            "Found %d category links on %s",
            len(category_links),
            response.url,
        )

        for link in category_links:
            category_name = link.css("::text").get()

            if not category_name:
                self.logger.warning(
                    "Skipping a category link with no text on %s",
                    response.url,
                )
                continue

            category_name = category_name.strip()
            category_url = response.urljoin(link.attrib["href"])

            self.logger.debug(
                "Discovered category: %s",
                category_name,
            )

            yield {
                "category": category_name,
                "category_url": category_url,
            }