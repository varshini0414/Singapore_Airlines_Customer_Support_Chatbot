# tests/test_parser.py
import pytest
from sia_faq_scraper.parser import extract_category_links, parse_faq_page, FAQItem

SAMPLE_LANDING_HTML = """
<html><body>
  <nav>
    <a href="/en_UK/us/faq/baggage/">Baggage</a>
    <a href="/en_UK/us/faq/check-in/">Check-in</a>
    <a href="https://www.singaporeair.com/en_UK/us/faq/special-assistance/">Special Assistance</a>
  </nav>
</body></html>
"""

SAMPLE_HEADING_FAQ_HTML = """
<html><body>
  <h2>Can I carry liquids?</h2>
  <p>Yes. Liquids must be in containers of 100ml or less.</p>
  <h2>Do I need a visa?</h2>
  <p>Visa requirements depend on nationality.</p>
</body></html>
"""

SAMPLE_BLOCK_FAQ_HTML = """
<html><body>
  <div class="faq-item">
    <div class="faq-title">How many bags can I check in?</div>
    <div class="faq-answer"><p>Allowance varies by fare and route.</p></div>
  </div>
  <div class="faq-item">
    <h3 class="question">What is excess baggage?</h3>
    <div class="answer"><p>Charges apply for overweight or extra pieces.</p></div>
  </div>
</body></html>
"""

SAMPLE_TABLE_FAQ_HTML = """
<html><body>
  <table>
    <tr><th>Question</th><th>Answer</th></tr>
    <tr><td>When can I check-in?</td><td>Online check-in opens 48 hours before departure.</td></tr>
    <tr><td>Can I change my booking?</td><td>Changes depend on fare rules.</td></tr>
  </table>
</body></html>
"""

def test_extract_category_links_returns_absolute_urls_and_names():
    links = extract_category_links(SAMPLE_LANDING_HTML)
    assert isinstance(links, list)
    assert len(links) == 3
    names = [n for n, _ in links]
    urls = [u for _, u in links]
    assert "Baggage" in names
    assert any(u.startswith("https://") for u in urls)

def test_parse_faq_page_parses_headings():
    faqs = parse_faq_page("General", SAMPLE_HEADING_FAQ_HTML, "https://site/faq")
    assert isinstance(faqs, list)
    assert len(faqs) == 2
    q_texts = [f.question for f in faqs]
    assert "Can I carry liquids?" in q_texts
    assert any("100ml" in f.answer_html for f in faqs)

def test_parse_faq_page_parses_block_items():
    faqs = parse_faq_page("Baggage", SAMPLE_BLOCK_FAQ_HTML, "https://site/faq/baggage")
    assert len(faqs) == 2
    assert any("How many bags" in f.question for f in faqs)
    assert any("excess baggage" in f.answer_html.lower() for f in faqs)

def test_parse_faq_page_parses_table_rows():
    faqs = parse_faq_page("Table", SAMPLE_TABLE_FAQ_HTML, "https://site/faq/table")
    assert len(faqs) == 2
    expected_qs = {"When can I check-in?", "Can I change my booking?"}
    assert set(f.question for f in faqs) == expected_qs

def test_faqitem_dataclass_fields():
    item = FAQItem(category="C", question="Q", answer_html="<p>A</p>", source_url="u")
    assert item.category == "C"
    assert item.question == "Q"
    assert "<p>A</p>" in item.answer_html
    assert item.source_url == "u"
