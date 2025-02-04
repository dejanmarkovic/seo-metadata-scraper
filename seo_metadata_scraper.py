import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import random
from urllib.parse import urlparse
from typing import List, Dict

class WebsiteScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    def get_domain(self, url: str) -> str:
        """Extract domain from URL."""
        return urlparse(url).netloc
    
    def get_all_headings(self, soup: BeautifulSoup) -> Dict[str, List[str]]:
        """Extract all headings (h1-h6) from the page."""
        headings = {}
        for level in range(1, 7):
            tag = f'h{level}'
            elements = soup.find_all(tag)
            headings[tag] = [h.get_text(strip=True) for h in elements]
        return headings
    
    def get_meta_tags(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract meta tags from the page."""
        meta_tags = {
            'meta_title': None,
            'meta_description': None,
            'og_title': None,
            'og_description': None
        }
        
        # Get meta title (try different methods)
        meta_title = soup.find('meta', attrs={'name': 'title'})
        if meta_title:
            meta_tags['meta_title'] = meta_title.get('content', '').strip()
        
        # Get meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            meta_tags['meta_description'] = meta_desc.get('content', '').strip()
        
        # Get OpenGraph title and description as fallback
        og_title = soup.find('meta', attrs={'property': 'og:title'})
        if og_title:
            meta_tags['og_title'] = og_title.get('content', '').strip()
            
        og_desc = soup.find('meta', attrs={'property': 'og:description'})
        if og_desc:
            meta_tags['og_description'] = og_desc.get('content', '').strip()
        
        return meta_tags
    
    def scrape_metadata(self, url: str) -> Dict:
        """Scrape metadata from a single URL."""
        try:
            # Add random delay between requests (1-3 seconds)
            time.sleep(random.uniform(1, 3))
            
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Get all headings
            headings = self.get_all_headings(soup)
            
            # Get meta tags
            meta_tags = self.get_meta_tags(soup)
            
            # Basic metadata
            metadata = {
                'url': url,
                'domain': self.get_domain(url),
                'page_title': soup.title.string.strip() if soup.title else None,
                'meta_title': meta_tags['meta_title'] or meta_tags['og_title'],  # Use OG title as fallback
                'meta_description': meta_tags['meta_description'] or meta_tags['og_description'],  # Use OG description as fallback
                'og_title': meta_tags['og_title'],
                'og_description': meta_tags['og_description']
            }
            
            # Add heading counts and lists
            for tag, heading_list in headings.items():
                metadata[f'{tag}_count'] = len(heading_list)
                metadata[f'{tag}_text'] = ' | '.join(heading_list) if heading_list else ''
            
            return metadata
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            # Return empty data structure with error
            metadata = {
                'url': url,
                'domain': self.get_domain(url),
                'page_title': None,
                'meta_title': None,
                'meta_description': None,
                'og_title': None,
                'og_description': None,
                'error': str(e)
            }
            # Add empty heading data
            for level in range(1, 7):
                tag = f'h{level}'
                metadata[f'{tag}_count'] = 0
                metadata[f'{tag}_text'] = ''
            return metadata
    
    def scrape_urls(self, urls: List[str], output_file: str = 'website_metadata.csv') -> pd.DataFrame:
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
            'url', 'domain', 'page_title', 'meta_title', 'meta_description',
            'og_title', 'og_description'
        ]
        for level in range(1, 7):
            column_order.extend([f'h{level}_count', f'h{level}_text'])
        if 'error' in df.columns:
            column_order.append('error')
        
        df = df[column_order]
        
        # Save to CSV
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"\nResults saved to {output_file}")
        
        # Print summary
        print("\nScraping Summary:")
        print(f"Total URLs processed: {len(df)}")
        print(f"Successful scrapes: {len(df[df.get('error').isna()])}")
        print(f"Failed scrapes: {len(df[df.get('error').notna()])}")
        
        # Print heading statistics
        print("\nHeading Statistics:")
        for level in range(1, 7):
            total_headings = df[f'h{level}_count'].sum()
            urls_with_headings = len(df[df[f'h{level}_count'] > 0])
            print(f"h{level}: {total_headings} headings found across {urls_with_headings} URLs")
        
        return df

# Example usage
if __name__ == "__main__":
    # List of URLs to scrape
    urls_to_scrape = [
        "https://example1.com",
        "https://example2.com",
        "https://example3.com"
    ]
    
    # Initialize and run scraper
    scraper = WebsiteScraper()
    results_df = scraper.scrape_urls(urls_to_scrape)