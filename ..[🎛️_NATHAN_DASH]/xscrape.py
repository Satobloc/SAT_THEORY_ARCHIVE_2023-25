# arxiv_keyword_scan.py

import arxiv
import csv
from datetime import datetime

KEYWORDS = [
    "holonomy",
    "torsion",
    "cobordism",
    "neutrino photon",
    "fermion boson",
    "emergent spacetime",
]

CATEGORIES = [
    "gr-qc",
    "hep-th",
    "hep-ph",
    "quant-ph",
    "astro-ph.CO",
]

MAX_RESULTS_PER_QUERY = 50
OUTPUT_FILE = "arxiv_keyword_results.csv"


def build_query(keyword, categories=None):
    # Search all fields for the keyword, then constrain by category.
    keyword_query = f'all:"{keyword}"'

    if categories:
        category_query = " OR ".join(f"cat:{cat}" for cat in categories)
        return f'({keyword_query}) AND ({category_query})'

    return keyword_query


def main():
    client = arxiv.Client(
        page_size=100,
        delay_seconds=3,
        num_retries=3
    )

    rows = []

    for keyword in KEYWORDS:
        query = build_query(keyword, CATEGORIES)

        search = arxiv.Search(
            query=query,
            max_results=MAX_RESULTS_PER_QUERY,
            sort_by=arxiv.SortCriterion.SubmittedDate,
            sort_order=arxiv.SortOrder.Descending
        )

        print(f"Searching: {keyword}")

        for result in client.results(search):
            rows.append({
                "keyword": keyword,
                "title": result.title,
                "authors": ", ".join(author.name for author in result.authors),
                "published": result.published.date().isoformat(),
                "updated": result.updated.date().isoformat(),
                "categories": ", ".join(result.categories),
                "primary_category": result.primary_category,
                "abstract": " ".join(result.summary.split()),
                "arxiv_url": result.entry_id,
                "pdf_url": result.pdf_url,
            })

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "keyword",
                "title",
                "authors",
                "published",
                "updated",
                "categories",
                "primary_category",
                "abstract",
                "arxiv_url",
                "pdf_url",
            ]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nSaved {len(rows)} results to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
