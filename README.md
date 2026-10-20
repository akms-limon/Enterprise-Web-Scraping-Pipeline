# Enterprise Web Scraping Pipeline

A modular Scrapy application that collects book data from [Books to Scrape](https://books.toscrape.com/index.html), processes it through an item pipeline, exports it in multiple formats, and stores it in SQLite. The application can run locally or inside Docker and supports deployment and execution through Scrapyd.

## Features

- Dynamically discovers book categories from the website.
- Randomly selects 5–10 categories per crawl, depending on how many are available.
- Follows category pagination to collect available books.
- Randomly selects up to five books per selected category.
- Extracts titles, prices, availability, product URLs, image URLs, and category names.
- Normalizes text, converts prices to numeric values, and converts availability to a boolean.
- Exports records to JSON, CSV, and XML through Scrapy Feed Exports.
- Stores processed records in SQLite through a Scrapy item pipeline.
- Uses Docker to package the application and Scrapyd.
- Supports remote spider scheduling through the Scrapyd HTTP API.

## Tech Stack

- Python 3.12+
- Scrapy
- SQLite
- Docker
- Scrapyd
- JSON, CSV, and XML

## Requirements

For local execution:

- Python 3.12 or newer
- pip
- Internet access to reach Books to Scrape

For containerized execution:

- Docker Engine
- A terminal with `curl`

## Installation

Clone the repository and enter the project directory:

```bash
git clone https://github.com/akms-limon/Enterprise-Web-Scraping-Pipeline.git
cd Enterprise-Web-Scraping-Pipeline
```

Create and activate a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install the project dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Check the available spiders:

```bash
scrapy list
```

The project provides the `books` and `categories` spiders.

## Running the Spider Locally

Run the main spider:

```bash
scrapy crawl books
```

The spider discovers categories dynamically, selects a random subset, crawls their pagination, and yields up to five randomly selected books per category.

The output directory is created automatically when needed. The main spider writes the following files:

- `output/books.json`
- `output/books.csv`
- `output/books.xml`
- `output/books.db`

The export formats are configured through `FEEDS` in `books_scraper/settings.py`. Existing feed files are overwritten by a new crawl.

To run the category-discovery spider separately:

```bash
scrapy crawl categories
```

## Output Data

Each book record contains these fields:

| Field | Description |
|---|---|
| `title` | Book title |
| `price` | Numeric price |
| `availability` | Boolean availability value |
| `product_url` | Absolute URL of the book details page |
| `image_url` | Absolute URL of the book cover image |
| `category` | Discovered category name |

### JSON

`output/books.json` stores the records as a JSON array.

### CSV

`output/books.csv` stores the records as rows with column headers.

### XML

`output/books.xml` stores the records in XML format using Scrapy's XML feed exporter.

## Data Processing and Database

The `BooksScraperPipeline` processes each item before it is stored.

The pipeline:

1. Checks that all required fields are present.
2. Normalizes whitespace in text fields.
3. Removes currency symbols and other non-numeric price characters.
4. Converts valid prices to numeric floating-point values.
5. Converts availability to a boolean: values beginning with `In stock` become `true`; other availability values become `false`.
6. Inserts the processed record into SQLite.

The SQLite database is stored at `output/books.db`. Its `books` table contains the six required data fields and an internal auto-incrementing ID.

The database is cleared when a new spider run opens the pipeline, so each run stores the current crawl's selected records rather than accumulating records from previous runs.

JSON, CSV, XML, and SQLite are generated from the same processed items. The record counts and normalized contents can be compared to verify consistency.

## Docker Setup

Build the image:

```bash
docker build -t books-scraper .
```

Run Scrapyd in a container:

```bash
docker run -d \
  --name books-scrapyd \
  -p 6800:6800 \
  -v "$PWD/output:/app/output" \
  books-scraper
```

The volume mount maps the local `output` directory to `/app/output` inside the container so generated files are available on the host.

Check that Scrapyd is ready:

```bash
curl http://localhost:6800/daemonstatus.json
```

A healthy server returns JSON containing `"status": "ok"`.

To inspect the running container:

```bash
docker ps --filter "name=books-scrapyd"
docker logs books-scrapyd
```

To stop the container:

```bash
docker stop books-scrapyd
```

To remove it when it is no longer needed:

```bash
docker rm books-scrapyd
```

## Scrapyd Deployment

The project includes a `deploy:local` target in `scrapy.cfg` pointing to `http://localhost:6800/`.

Make sure the virtual environment is active, the required dependencies are installed, and the Scrapyd container is running.

Deploy the project:

```bash
scrapyd-deploy local
```

A successful deployment returns a response with `"status": "ok"` and the deployed project version.

Check the deployed project:

```bash
curl "http://localhost:6800/listprojects.json"
```

List the spiders available to the deployed project:

```bash
curl "http://localhost:6800/listspiders.json?project=books_scraper"
```

## Running a Spider Through the Scrapyd API

Schedule the main spider:

```bash
curl -X POST "http://localhost:6800/schedule.json" \
  -d project=books_scraper \
  -d spider=books
```

A successful response includes a job ID. Use that ID to find the job in the job listing:

```bash
curl "http://localhost:6800/listjobs.json?project=books_scraper"
```

A completed job appears in the `finished` list. Running jobs appear in `running`, and jobs waiting to start appear in `pending`.

Scrapyd logs can be accessed using the `log_url` returned by the job listing. For example:

```bash
curl "http://localhost:6800/logs/books_scraper/books/<JOB_ID>.log"
```

Replace `<JOB_ID>` with the actual job ID.

## Architecture

```text
Books to Scrape
      |
      v
BooksSpider
      |
      +--> Discover categories dynamically
      |
      +--> Randomly select categories
      |
      +--> Crawl category pagination
      |
      +--> Select up to five books per category
      |
      v
Scrapy Items
      |
      v
BooksScraperPipeline
      |
      +--> Validate required fields
      +--> Normalize text and price
      +--> Normalize availability
      +--> Insert into SQLite
      |
      +--> Scrapy Feed Exports
                |
                +--> books.json
                +--> books.csv
                +--> books.xml

Docker container
      |
      +--> Scrapyd
              |
              +--> Deploy project
              +--> Schedule spider through HTTP API
```

## Folder Structure

```text
Enterprise-Web-Scraping-Pipeline/
├── books_scraper/
│   ├── __init__.py
│   ├── items.py
│   ├── middlewares.py
│   ├── pipelines.py
│   ├── settings.py
│   └── spiders/
│       ├── books_spider.py
│       └── categories_spider.py
├── output/
│   ├── books.json
│   ├── books.csv
│   ├── books.xml
│   └── books.db
├── .dockerignore
├── .gitignore
├── Dockerfile
├── pyproject.toml
├── requirements.txt
├── scrapy.cfg
├── scrapyd.conf
├── setup.py
└── README.md
```

Generated output files may be excluded from version control by `.gitignore`.

## Design Decisions

- **Dynamic discovery:** Category names and URLs are extracted from the website instead of being hardcoded.
- **Pagination:** The spider follows each category's next-page link until no further page is available.
- **Random sampling:** Categories and books are selected randomly on each run. This makes the resulting dataset vary between crawls.
- **Pipeline processing:** Validation and normalization are centralized in the item pipeline instead of duplicated in spider callbacks.
- **Feed exports:** Scrapy's built-in feed exporters generate JSON, CSV, and XML from processed items.
- **SQLite:** SQLite provides persistent storage without requiring a separate database server.
- **Docker and Scrapyd:** Docker packages the runtime, while Scrapyd provides an HTTP API for deploying and scheduling spiders.
- **Output persistence:** A Docker bind mount makes the container's output directory available on the host.

## Known Limitations

- The target website is an educational scraping site; its structure and availability may change.
- Category and book selection is random, so consecutive runs may produce different records.
- Some categories contain fewer than five books. The spider collects all available books from those categories rather than inventing records.
- Prices are represented as floating-point numbers. This is adequate for this scraping exercise but decimal arithmetic may be preferable for financial applications.
- Availability is stored as a boolean, so the original availability wording is not retained.
- The application requires network access to the target website.
- The SQLite database is reset at the start of a run. Previous crawl results should be backed up before a new run if they need to be retained.
- Scrapyd is exposed on port `6800` for local use. A production deployment should restrict access and apply appropriate network security.

## Verification

The main spider has been executed locally and through Scrapyd. Record counts can vary because category and book selection is random. In a verified Scrapyd run, JSON, CSV, XML, and SQLite each contained 36 records, and all four record counts matched. A separate local run produced 39 records. Required fields were present in the local JSON output, and the output counts matched across JSON, CSV, XML, and SQLite.

To repeat the checks, run the spider and compare the generated output files and SQLite records.

