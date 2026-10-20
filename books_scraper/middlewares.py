from scrapy import signals


class BooksScraperSpiderMiddleware:
    """Provide hooks for processing spider inputs, outputs, and exceptions."""

    @classmethod
    def from_crawler(cls, crawler):
        """Create the middleware and connect its spider-opened signal."""
        middleware = cls()
        crawler.signals.connect(
            middleware.spider_opened,
            signal=signals.spider_opened,
        )
        return middleware

    def process_spider_input(self, response, spider):
        """Allow a response to continue to the spider unchanged."""
        return None

    def process_spider_output(self, response, result, spider):
        """Pass the spider's requests and items through unchanged."""
        yield from result

    def process_spider_exception(self, response, exception, spider):
        """Leave spider exceptions for other middleware to handle."""
        return None

    async def process_start(self, start):
        """Pass the spider's initial requests and items through unchanged."""
        async for item_or_request in start:
            yield item_or_request

    def spider_opened(self, spider):
        """Log when the spider starts."""
        spider.logger.info("Spider opened: %s", spider.name)


class BooksScraperDownloaderMiddleware:
    """Provide hooks for processing downloader requests and responses."""

    @classmethod
    def from_crawler(cls, crawler):
        """Create the middleware and connect its spider-opened signal."""
        middleware = cls()
        crawler.signals.connect(
            middleware.spider_opened,
            signal=signals.spider_opened,
        )
        return middleware

    def process_request(self, request, spider):
        """Allow a request to continue to the downloader unchanged."""
        return None

    def process_response(self, request, response, spider):
        """Return the downloaded response unchanged."""
        return response

    def process_exception(self, request, exception, spider):
        """Leave download exceptions for other middleware to handle."""
        return None

    def spider_opened(self, spider):
        """Log when the spider starts."""
        spider.logger.info("Spider opened: %s", spider.name)
