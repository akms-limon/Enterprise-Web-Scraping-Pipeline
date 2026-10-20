import math
import re
import sqlite3
from pathlib import Path

from itemadapter import ItemAdapter
from scrapy.exceptions import DropItem
from books_scraper.items import BooksScraperItem


class BooksScraperPipeline:
    """Validate, normalize, and store scraped books in SQLite."""

    required_fields = tuple(BooksScraperItem.fields)

    @classmethod
    def from_crawler(cls, crawler):
        """Create the pipeline with access to the active crawler."""
        pipeline = cls()
        pipeline.crawler = crawler
        return pipeline

    def open_spider(self):
        """Open the database and prepare the books table."""
        database_path = Path("output/books.db")
        database_path.parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(database_path)
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                price REAL NOT NULL,
                availability BOOLEAN NOT NULL,
                product_url TEXT NOT NULL,
                image_url TEXT NOT NULL,
                category TEXT NOT NULL
            )
            """
        )
        self.connection.execute("DELETE FROM books")
        self.connection.commit()

        self.crawler.spider.logger.info(
            "SQLite database ready: %s", database_path
        )

    def process_item(self, item):
        """Validate, normalize, and save one book."""
        adapter = ItemAdapter(item)

        for field in self.required_fields:
            value = adapter.get(field)
            if value is None or not str(value).strip():
                raise DropItem(f"Missing required field: {field}")

        for field in ("title", "product_url", "image_url", "category"):
            adapter[field] = " ".join(str(adapter[field]).split())

        raw_price = str(adapter["price"]).strip()
        normalized_price = re.sub(r"[^\d.]", "", raw_price)

        if not normalized_price or normalized_price.count(".") > 1:
            raise DropItem(f"Invalid price: {raw_price}")

        try:
            price = float(normalized_price)
        except ValueError as error:
            raise DropItem(f"Invalid price: {raw_price}") from error

        if not math.isfinite(price) or price < 0:
            raise DropItem(f"Invalid price: {raw_price}")

        adapter["price"] = price

        availability = " ".join(str(adapter["availability"]).split())
        adapter["availability"] = availability.startswith("In stock")

        self.connection.execute(
            """
            INSERT INTO books (
                title, price, availability, product_url, image_url, category
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                adapter["title"],
                adapter["price"],
                adapter["availability"],
                adapter["product_url"],
                adapter["image_url"],
                adapter["category"],
            ),
        )

        return item

    def close_spider(self):
        """Commit pending records and close the database connection."""
        if hasattr(self, "connection"):
            self.connection.commit()
            self.connection.close()
            self.crawler.spider.logger.info(
                "SQLite database connection closed."
            )
