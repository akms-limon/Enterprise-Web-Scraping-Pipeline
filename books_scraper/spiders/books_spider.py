
import random

import scrapy

from books_scraper.category_utils import extract_categories
from books_scraper.items import BooksScraperItem


class BooksSpider(scrapy.Spider):
    """Discover categories and scrape randomly selected books."""

    name = "books"
    start_urls = ["https://books.toscrape.com/index.html"]

    def parse(self, response):
        """Discover categories and select between five and ten."""
        categories = extract_categories(response, self.logger)

        if not categories:
            self.logger.error("No categories found on %s", response.url)
            return

        category_count = random.randint(
            min(5, len(categories)),
            min(10, len(categories)),
        )
        selected_categories = random.sample(categories, category_count)

        self.logger.info(
            "Discovered %d categories; selected %d.",
            len(categories),
            len(selected_categories),
        )

        for category in selected_categories:
            self.logger.info("Selected category: %s", category["name"])

            yield response.follow(
                category["url"],
                callback=self.parse_category,
                cb_kwargs={
                    "category_name": category["name"],
                    "collected_books": [],
                },
            )

    def parse_category(self, response, category_name, collected_books):
        """Collect every page, then select up to five books."""
        for book in response.css("article.product_pod"):
            title = book.css("h3 a::attr(title)").get()
            price = book.css(".price_color::text").get()
            availability = " ".join(
                book.css(".availability::text").getall()
            ).strip()
            product_url = book.css("h3 a::attr(href)").get()
            image_url = book.css(".image_container img::attr(src)").get()

            if not all((
                title,
                price,
                availability,
                product_url,
                image_url,
            )):
                self.logger.warning(
                    "Skipping incomplete book on %s",
                    response.url,
                )
                continue

            collected_books.append({
                "title": title.strip(),
                "price": price.strip(),
                "availability": availability,
                "product_url": response.urljoin(product_url),
                "image_url": response.urljoin(image_url),
                "category": category_name,
            })

        next_page = response.css("li.next a::attr(href)").get()

        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse_category,
                cb_kwargs={
                    "category_name": category_name,
                    "collected_books": collected_books,
                },
            )
            return

        selected_books = random.sample(
            collected_books,
            min(5, len(collected_books)),
        )

        self.logger.info(
            "Selected %d books from '%s' (%d collected).",
            len(selected_books),
            category_name,
            len(collected_books),
        )

        for book in selected_books:
            yield BooksScraperItem(**book)
