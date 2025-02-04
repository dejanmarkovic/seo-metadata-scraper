"""
SEO Metadata Scraper - A Python tool that extracts essential SEO elements including meta tags, headings, 
and OpenGraph data from websites for competitive analysis and content optimization.

The SEO Metadata Scraper is a robust Python utility designed for digital marketers and SEO professionals 
to analyze website content at scale. It systematically extracts crucial SEO elements including meta titles, 
meta descriptions, heading hierarchies (H1-H6), and OpenGraph metadata from any list of URLs. Built with 
respect for server resources through rate limiting and proper headers, this tool enables efficient competitive 
analysis, content auditing, and SEO optimization by exporting all extracted data into an organized CSV format.
"""

import random
import time
from typing import Dict, List
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup


class WebsiteScraper:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        return urlparse(url).netloc

    def get_all_headings(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract all headings (h1-h6) from the page."""
        headings = {}
        for level in range(1, 7):
            tag = f"h{level}"
            elements = soup.find_all(tag)
            headings[tag] = [h.get_text(strip=True) for h in elements]
        return headings

    def get_meta_tags(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract meta tags from the page."""
        meta_tags = {
            "meta_title": None,
            "meta_description": None,
            "og_title": None,
            "og_description": None,
        }

        # Get meta title (try different methods)
        meta_title = soup.find("meta", attrs={"name": "title"})
        if meta_title:
            meta_tags["meta_title"] = meta_title.get("content", "").strip()

        # Get meta description
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            meta_tags["meta_description"] = meta_desc.get("content", "").strip()

        # Get OpenGraph title and description as fallback
        og_title = soup.find("meta", attrs={"property": "og:title"})
        if og_title:
            meta_tags["og_title"] = og_title.get("content", "").strip()

        og_desc = soup.find("meta", attrs={"property": "og:description"})
        if og_desc:
            meta_tags["og_description"] = og_desc.get("content", "").strip()

        return meta_tags

    def scrape_metadata(self, url: str) -> Dict:
        """Scrape metadata from a single URL."""
        try:
            # Add random delay between requests (1-3 seconds)
            time.sleep(random.uniform(1, 3))

            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(
                response.content.decode("utf-8", "replace"), "html.parser"
            )

            # Get all headings
            headings = self.get_all_headings(soup)

            # Get meta tags
            meta_tags = self.get_meta_tags(soup)

            # Basic metadata
            metadata = {
                "url": url,
                "domain": self.get_domain(url),
                "page_title": (
                    soup.title.string.replace("\xa0", " ").strip()
                    if soup.title
                    else None
                ),
                "meta_title": meta_tags["meta_title"]
                or meta_tags["og_title"],  # Use OG title as fallback
                "meta_description": meta_tags["meta_description"]
                or meta_tags["og_description"],  # Use OG description as fallback
                "og_title": meta_tags["og_title"],
                "og_description": meta_tags["og_description"],
                "error": None,  # Explicitly set error to None for successful scrapes
            }

            # Add heading counts and lists
            for tag, heading_list in headings.items():
                metadata[f"{tag}_count"] = len(heading_list)
                metadata[f"{tag}_text"] = (
                    " | ".join([h.replace("\xa0", " ").strip() for h in heading_list])
                    if heading_list
                    else ""
                )

            return metadata

        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            # Return empty data structure with error
            metadata = {
                "url": url,
                "domain": self.get_domain(url),
                "page_title": None,
                "meta_title": None,
                "meta_description": None,
                "og_title": None,
                "og_description": None,
                "error": str(e),  # Store the error message
            }
            # Add empty heading data
            for level in range(1, 7):
                tag = f"h{level}"
                metadata[f"{tag}_count"] = 0
                metadata[f"{tag}_text"] = ""
            return metadata

    def scrape_urls(
        self, urls: List[str], output_file: str = "website_metadata.csv"
    ) -> pd.DataFrame:
        """Scrape metadata from multiple URLs and save to CSV."""
        results = []
        total_urls = len(urls)

        for i, url in enumerate(urls, 1):
            print(f"Scraping [{i}/{total_urls}]: {url}")
            metadata = self.scrape_metadata(url)
            results.append(metadata)

        # Convert results to DataFrame
        df = pd.DataFrame(results)

        # Reorder columns for better readability
        column_order = [
            "url",
            "domain",
            "page_title",
            "meta_title",
            "meta_description",
            "og_title",
            "og_description",
        ]
        for level in range(1, 7):
            column_order.extend([f"h{level}_count", f"h{level}_text"])
        column_order.append("error")  # Always include error column

        df = df[column_order]

        # Save to CSV
        df.to_csv(output_file, index=False, encoding="utf-8")
        print(f"\nResults saved to {output_file}")

        # Print summary
        print("\nScraping Summary:")
        print(f"Total URLs processed: {len(df)}")
        successful_scrapes = len(df[df["error"].isna()])
        failed_scrapes = len(df[df["error"].notna()])
        print(f"Successful scrapes: {successful_scrapes}")
        print(f"Failed scrapes: {failed_scrapes}")

        if successful_scrapes > 0:
            # Print heading statistics only for successful scrapes
            print("\nHeading Statistics:")
            for level in range(1, 7):
                total_headings = df[df["error"].isna()][f"h{level}_count"].sum()
                urls_with_headings = len(
                    df[(df["error"].isna()) & (df[f"h{level}_count"] > 0)]
                )
                print(
                    f"h{level}: {total_headings} headings found across {urls_with_headings} URLs"
                )

        return df


# Example usage
if __name__ == "__main__":
    # List of URLs to scrape
    urls_to_scrape = [
        "https://yoursite.com/",
        "https://yoursite.com/",
    ]

    # Initialize and run scraper
    scraper = WebsiteScraper()
    results_df = scraper.scrape_urls(urls_to_scrape)
