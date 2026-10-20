
import re

from itemadapter import ItemAdapter


class BooksScraperPipeline:
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        for field_name in ("title", "product_url", "image_url", "category"):
            value = adapter.get(field_name)

            if isinstance(value, str):
                adapter[field_name] = " ".join(value.split())

        price = adapter.get("price")

        if price is not None:
            normalized_price = re.sub(r"[^\d.]", "", str(price))
            adapter["price"] = float(normalized_price)

        availability = adapter.get("availability", "")
        adapter["availability"] = str(availability).strip().startswith("In stock")

        return item
