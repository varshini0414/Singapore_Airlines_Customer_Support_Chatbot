from .utils import default_session, rate_limited
from .parser import parse_faq_page, extract_category_links
from typing import List
from .parser import FAQItem

FAQ_ROOT = "https://www.singaporeair.com/en_UK/us/faq/"

class SIAFaqScraper:
    def __init__(self, session=None, delay=0.5):
        self.session = session or default_session()
        self.delay = delay

    @rate_limited
    def fetch(self, url: str) -> str:
        return self.session.get(url, timeout=20).text

    def scrape(self) -> List[FAQItem]:
        landing = self.fetch(FAQ_ROOT)
        categories = extract_category_links(landing)
        results = []
        if not categories:
            results.extend(parse_faq_page("General", landing, FAQ_ROOT))
            return results
        for name, url in categories:
            html = self.fetch(url)
            results.extend(parse_faq_page(name, html, url))
        return results
