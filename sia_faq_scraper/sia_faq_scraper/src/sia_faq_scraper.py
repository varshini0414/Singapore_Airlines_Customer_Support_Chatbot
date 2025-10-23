"""
Lightweight scraper for Singapore Airlines FAQs.
Saves results to JSON and CSV.
"""
from __future__ import annotations
import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict
from typing import List, Optional
import time
import json
import csv
import logging
import pathlib

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

BASE_URL = "https://www.singaporeair.com"
FAQ_ROOT = "https://www.singaporeair.com/en_UK/us/faq/"  # main FAQ landing. Source: public site. :contentReference[oaicite:1]{index=1}

HEADERS = {
    "User-Agent": "sia-faq-scraper/1.0 (+https://example.com/)",
}

REQUEST_DELAY = 0.5  # polite rate limit


@dataclass
class FAQItem:
    category: str
    question: str
    answer_html: str
    source_url: str


class SIAFaqScraper:
    def __init__(self, session: Optional[requests.Session] = None, delay: float = REQUEST_DELAY):
        self.session = session or requests.Session()
        self.session.headers.update(HEADERS)
        self.delay = delay

    def fetch(self, url: str) -> str:
        logging.info("GET %s", url)
        r = self.session.get(url, timeout=20)
        r.raise_for_status()
        time.sleep(self.delay)
        return r.text

    def list_category_links(self, landing_html: str) -> List[tuple[str, str]]:
        """Return list of (category_name, url)."""
        soup = BeautifulSoup(landing_html, "html.parser")
        # category blocks usually are links under the FAQ page. Keep selector flexible.
        links = []
        for a in soup.select("a[href]"):
            href = a.get("href", "")
            text = a.get_text(strip=True)
            if "/faq/" in href and text:
                full = href if href.startswith("http") else BASE_URL + href
                links.append((text, full))
        # dedupe preserving order
        seen = set()
        out = []
        for name, url in links:
            if url not in seen:
                seen.add(url)
                out.append((name, url))
        logging.info("Found %d category links", len(out))
        return out

    def parse_faq_page(self, category: str, html: str, url: str) -> List[FAQItem]:
        soup = BeautifulSoup(html, "html.parser")
        faqs = []
        # The site uses headings and Q/A blocks. Try multiple fallback selectors.
        # Primary: elements with class containing 'faq' or structural patterns.
        # Search for question-like headings then the next sibling(s) as answers.
        question_selectors = [
            ".faq-question", "h2", "h3", ".ng-binding", ".question", ".article h3"
        ]
        # naive approach: find headings and get nearby paragraph text
        for h in soup.find_all(["h2", "h3"]):
            q = h.get_text(strip=True)
            if not q:
                continue
            # collect answer paragraphs until next heading
            answer_parts = []
            for sib in h.find_next_siblings():
                if sib.name and sib.name.startswith("h"):
                    break
                answer_parts.append(str(sib))
            answer_html = "\n".join(answer_parts).strip()
            if not answer_html:
                # try the element next to heading
                nxt = h.find_next()
                answer_html = str(nxt) if nxt else ""
            faqs.append(FAQItem(category=category, question=q, answer_html=answer_html, source_url=url))
        # Fallback: find explicit Q/A blocks
        if not faqs:
            for qa in soup.select(".faq, .question-answer, .faq-item"):
                q_el = qa.select_one(".question, .faq-title, h3")
                a_el = qa.select_one(".answer, .faq-answer, p")
                if q_el and a_el:
                    faqs.append(FAQItem(category=category, question=q_el.get_text(strip=True),
                                        answer_html=str(a_el), source_url=url))
        logging.info("Parsed %d faqs from %s", len(faqs), url)
        return faqs

    def scrape(self) -> List[FAQItem]:
        landing = self.fetch(FAQ_ROOT)
        categories = self.list_category_links(landing)
        all_faqs: List[FAQItem] = []
        # If categories is empty, treat landing page as a category
        if not categories:
            logging.info("No category links found. Parsing landing as single page.")
            all_faqs.extend(self.parse_faq_page("General", landing, FAQ_ROOT))
            return all_faqs
        for name, url in categories:
            logging.info("Scraping category: %s", name)
            try:
                html = self.fetch(url)
            except Exception as e:
                logging.warning("Failed to fetch %s: %s", url, e)
                continue
            faqs = self.parse_faq_page(name, html, url)
            all_faqs.extend(faqs)
        return all_faqs


def save_json(items: List[FAQItem], outpath: str = "sia_faqs.json"):
    data = [asdict(i) for i in items]
    p = pathlib.Path(outpath)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logging.info("Saved %d faqs to %s", len(items), outpath)


def save_csv(items: List[FAQItem], outpath: str = "sia_faqs.csv"):
    p = pathlib.Path(outpath)
    with p.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["category", "question", "answer_html", "source_url"])
        for it in items:
            writer.writerow([it.category, it.question, it.answer_html, it.source_url])
    logging.info("Saved %d faqs to %s", len(items), outpath)


if __name__ == "__main__":
    scraper = SIAFaqScraper()
    items = scraper.scrape()
    save_json(items)
    save_csv(items)
    print(f"Done. Scraped {len(items)} FAQ items.")
