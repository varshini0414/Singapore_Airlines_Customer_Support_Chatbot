from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class FAQItem:
    category: str
    question: str
    answer_html: str
    source_url: str


def extract_category_links(html: str) -> List[Tuple[str, str]]:
    """
    Extracts FAQ category names and URLs from the landing page.
    Returns a list of tuples: (category_name, category_url)
    """
    soup = BeautifulSoup(html, "html.parser")
    links = []
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        text = a.get_text(strip=True)
        if "/faq/" in href and text:
            # handle both absolute and relative links
            if not href.startswith("http"):
                href = "https://www.singaporeair.com" + href
            links.append((text, href))

    # Deduplicate while preserving order
    seen = set()
    clean_links = []
    for name, url in links:
        if url not in seen:
            seen.add(url)
            clean_links.append((name, url))
    return clean_links


def parse_faq_page(category: str, html: str, url: str) -> List[FAQItem]:
    """
    Parses an individual FAQ page and extracts all question-answer pairs.
    Tries multiple patterns because FAQ layouts can vary.
    """
    soup = BeautifulSoup(html, "html.parser")
    faqs: List[FAQItem] = []

    # Try common Q/A patterns
    question_selectors = [
        "h2", "h3", ".faq-question", ".question", ".faq-title"
    ]
    answer_selectors = [
        "p", ".faq-answer", ".answer", ".faq-content"
    ]

    # Method 1: Find headings and extract paragraphs until next heading
    for h in soup.find_all(["h2", "h3"]):
        q = h.get_text(strip=True)
        if not q:
            continue
        answer_parts = []
        for sib in h.find_next_siblings():
            if sib.name and sib.name in ["h2", "h3"]:
                break
            if sib.name:
                answer_parts.append(str(sib))
        if answer_parts:
            answer_html = "\n".join(answer_parts)
            faqs.append(FAQItem(category, q, answer_html, url))

    # Method 2: Explicit question-answer blocks
    if not faqs:
        for block in soup.select(".faq, .faq-item, .question-answer"):
            q_el = block.select_one(".question, .faq-question, .faq-title, h3")
            a_el = block.select_one(".answer, .faq-answer, p")
            if q_el and a_el:
                faqs.append(
                    FAQItem(
                        category=category,
                        question=q_el.get_text(strip=True),
                        answer_html=str(a_el),
                        source_url=url,
                    )
                )

    # Method 3: fallback — table or accordion format
    if not faqs:
        for row in soup.select("table tr"):
            cells = row.find_all(["td", "th"])
            if len(cells) >= 2:
                q = cells[0].get_text(strip=True)
                a = cells[1].decode_contents()
                if q and a:
                    faqs.append(FAQItem(category, q, a, url))

    return faqs
