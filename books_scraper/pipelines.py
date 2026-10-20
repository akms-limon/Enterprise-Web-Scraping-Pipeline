
import re
import sqlite3
from pathlib import Path

from itemadapter import ItemAdapter


class BooksScraperPipeline:
    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        pipeline.crawler = crawler
        return pipeline

    def open_spider(self):
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
        self.connection.commit()

        self.connection.execute("DELETE FROM books")
        self.connection.commit()

        self.crawler.spider.logger.info(
            "SQLite database is ready: %s",
            database_path,
        )

    def process_item(self, item):
        adapter = ItemAdapter(item)

        for field_name in ("title", "product_url", "image_url", "category"):
            value = adapter.get(field_name)

            if isinstance(value, str):
                adapter[field_name] = " ".join(value.split())

        price = adapter.get("price")

        if price is not None:
            normalized_price = re.sub(r"[^\d.]", "", str(price))

            if not normalized_price:
                raise ValueError("Invalid book price")

            adapter["price"] = float(normalized_price)

        availability = adapter.get("availability", "")
        adapter["availability"] = (
            str(availability).strip().startswith("In stock")
        )

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
        self.connection.commit()

        return item

    def close_spider(self):
        self.connection.close()
        self.crawler.spider.logger.info("SQLite database connection closed.")
