"""Shared helpers for extracting book categories."""

def extract_categories(response, logger):
    """Return valid category names and absolute URLs from a response."""
    categories = []

    for link in response.css(".side_categories ul ul li a"):
        name = link.css("::text").get()
        href = link.attrib.get("href")

        if not name or not href:
            logger.warning("Skipping an incomplete category link.")
            continue

        categories.append({
            "name": name.strip(),
            "url": response.urljoin(href),
        })

    return categories
