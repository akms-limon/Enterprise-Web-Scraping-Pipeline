# Enterprise Web Scraping Pipeline

## Project Overview

A Scrapy-based application that scrapes book data from [Books to Scrape](https://books.toscrape.com/), processes it, exports it in JSON, CSV, and XML formats, and stores records in SQLite. Docker and Scrapyd support containerized execution and spider deployment.

## Features

- Dynamically discovers book categories and URLs.
- Randomly selects 5–10 categories per crawl.
- Follows category pagination.
- Selects up to five random books per category.
- Extracts six required book fields.
- Validates and normalizes scraped data.
- Converts prices to numeric values and availability to Boolean.
- Exports data to JSON, CSV, and XML.
- Stores processed records in SQLite.
- Supports Docker and Scrapyd deployment.
- Provides an HTTP API for scheduling spiders.

## Tech Stack

- Python 3.12+
- Scrapy
- SQLite
- Docker
- Scrapyd

## Installation Guide

**Clone the repository**

```
git clone https://github.com/akms-limon/Enterprise-Web-Scraping-Pipeline.git
cd Enterprise-Web-Scraping-Pipeline
````

Create a virtual environment and install dependencies

```
uv sync
```

Verify the installation

```
uv run scrapy list
```

Expected output:

```
books
categories
```

## Running the Spider

Run the main spider

```
uv run scrapy crawl books
```

The spider discovers categories, selects categories randomly, follows pagination, selects books, processes records, and writes the output files.

Run the category-discovery spider

```
uv run scrapy crawl categories
```

To save discovered categories separately:

```
uv run scrapy crawl categories -O /tmp/categories.json
```

The category spider disables the main book pipeline and configured feeds to prevent category records from entering the book database or overwriting book exports.

## Docker Setup Guide

Prerequisites

Install Docker Engine and ensure the Docker daemon is running.

Build the image

Run from the repository root:

```
docker build -t books-scraper .
```

Start the container

```
mkdir -p output

docker run -d \
  --name books-scrapyd \
  -p 6800:6800 \
  -v "$PWD/output:/app/output" \
  books-scraper
```

The volume mount keeps generated files and the SQLite database accessible on the host.

Check the service

```
curl http://localhost:6800/daemonstatus.json
```

A successful response contains `"status": "ok"`.

Check container status and logs

```
docker ps --filter "name=books-scrapyd"
docker logs books-scrapyd
```

Stop and remove the container

```
docker stop books-scrapyd
docker rm books-scrapyd
```

The host's mounted `output/` directory remains available after container removal.

## Scrapyd Deployment Guide

Scrapyd provides an HTTP API for deploying and scheduling Scrapy spiders.

The local deployment target is configured in `scrapy.cfg`:

```
[settings]
default = books_scraper.settings

[deploy:local]
url = http://localhost:6800/
project = books_scraper
```

Start Scrapyd

Ensure the Docker container is running and Scrapyd is accessible at `http://localhost:6800/`.

Deploy the project

With the required dependencies, including Scrapyd Client, installed locally:

```
uv run scrapyd-deploy local
```

Verify deployment

List deployed projects:

```
curl "http://localhost:6800/listprojects.json"
```

List the deployed spiders:

```
curl "http://localhost:6800/listspiders.json?project=books_scraper"
```

The project should list `books` and `categories`.

Schedule a spider

```
curl -X POST "http://localhost:6800/schedule.json" \
  -d project=books_scraper \
  -d spider=books
```

The response includes a job ID.

Check job status

```
curl "http://localhost:6800/listjobs.json?project=books_scraper"
```

Jobs are grouped into `pending`, `running`, and `finished`.

View a job log

Replace `<JOB_ID>` with the returned ID:

```
curl "http://localhost:6800/logs/books_scraper/books/<JOB_ID>.log"
```

## Output Format Description

The main spider generates these files in `output/`:

| File         | Format | Description                  |
| ------------ | ------ | ---------------------------- |
| `books.json` | JSON   | Book records as a JSON array |
| `books.csv`  | CSV    | Records with column headers  |
| `books.xml`  | XML    | Book records in XML format   |
| `books.db`   | SQLite | Processed database records   |

Each book record contains six fields:

| Field          | Description               |
| -------------- | ------------------------- |
| `title`        | Book title                |
| `price`        | Numeric price             |
| `availability` | Boolean stock status      |
| `product_url`  | Absolute product page URL |
| `image_url`    | Absolute image URL        |
| `category`     | Category name             |

The main spider overwrites the JSON, CSV, and XML files on each run.

## Database Configuration

The `BooksScraperPipeline` in `books_scraper/pipelines.py` processes items and stores them in SQLite.

Database details

- Path: `output/books.db`
- Table: `books`
- Columns: Six required fields plus an auto-incrementing `id`

Pipeline processing

- Validates required fields.
- Removes unnecessary whitespace.
- Removes currency symbols and converts prices to numeric values.
- Converts availability to `True` for values beginning with `In stock`; other values become `False`.
- Inserts records using parameterized SQL.
- Commits changes and closes the connection when the spider finishes.

The database table is cleared when a new spider run opens the pipeline. The same processed items are passed to the feed exporters and database pipeline.

Check the database record count

```
uv run python -c "import sqlite3; db=sqlite3.connect('output/books.db'); print(db.execute('SELECT COUNT(*) FROM books').fetchone()[0]); db.close()"
```

## Architecture Diagram (Text or Image)

```
            Books to Scrape
                   |
                   v
               BooksSpider
                   |
                   v
         Dynamic Category Discovery
                   |
                   v
          Random Category Selection
                   |
                   v
         Category Pagination Crawl
                   |
                   v
           Random Book Selection
                   |
                   v
            BooksScraperItem
                   |
                   v
          BooksScraperPipeline
                   |
         +---------+---------+
         |         |         |
         v         v         v
       SQLite     JSON      CSV
                   +------> XML


                 Docker
                   |
                   v
                 Scrapyd
                   |
         +---------+---------+
         |         |         |
         v         v         v
       Deploy   Schedule   Monitor
       Spiders    Jobs     Job Status
```

## Folder Structure

```
Enterprise-Web-Scraping-Pipeline/
├── books_scraper/
│   ├── __init__.py
│   ├── category_utils.py
│   ├── items.py
│   ├── middlewares.py
│   ├── pipelines.py
│   ├── settings.py
│   └── spiders/
│       ├── __init__.py
│       ├── books_spider.py
│       └── categories_spider.py
├── .dockerignore
├── .gitignore
├── Dockerfile
├── pyproject.toml
├── requirements.txt
├── scrapy.cfg
├── scrapyd.conf
├── setup.py
├── uv.lock
└── README.md
```

The `output/` directory and generated data files are created at runtime and excluded from Git tracking.

## Design Decisions

- Dynamic discovery: Extracts category names and URLs from the website.
- Shared helper: `category_utils.py` avoids duplicated category extraction logic.
- Pagination: Follows category pages to collect available books.
- Random sampling: Produces different datasets across runs.
- Item pipeline: Separates data validation and normalization from scraping callbacks.
- SQLite: Provides local storage without a separate database service.
- Feed exports: Uses Scrapy's built-in JSON, CSV, and XML exporters.
- Docker and Scrapyd: Support containerized execution and API-based scheduling.

## Known Limitations

- Results depend on website availability and structure.
- Random selection can produce different results on each run.
- Categories with fewer than five books produce fewer records.
- Prices are stored as floating-point values.
- Availability is stored as a Boolean rather than the original text.
- The database is cleared when a new spider run starts.
- Scrapyd's exposed port should be protected in production.